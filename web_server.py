from flask import Flask, jsonify, render_template, request, abort
import sqlite3
import os
import time
import uuid
import database
from visual_cards import get_rank, RANKS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "bot_database.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "web_leaderboard", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "web_leaderboard", "static")
ADMIN_DASHBOARD_TOKEN = os.environ.get("ADMIN_DASHBOARD_TOKEN", "")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# ── Canlı baxanlar sayğacı ────────────────────────────────────────────────────
# Sadə heartbeat-əsaslı izləmə: hər səhifə ~12 saniyədə bir /api/heartbeat çağırır,
# server son 30 saniyədə "səs vermiş" unikal session-ları sayır. DB-siz, yaddaşda —
# bot restart olsa sıfırlanır (canlı göstərici üçün məqbul, tarixi məlumat deyil).
_VIEWER_TIMEOUT_SECONDS = 30
_active_viewers = {}

# ── Axtarış sayğacı ("məni kimsə axtaranda") ──────────────────────────────────
# Yaddaşda, gün-üzrə sıfırlanan sadə sayğac: {(date_str, so2_id): count}. DB-siz —
# bot restart olsa günün sayı sıfırlanır (məqbul, canlı statistika üçündür).
_search_counts = {}

# ── Profil emoji reaksiyaları ("Emoji Reaksiya Buludu") ───────────────────────
# Yaddaşda, qısa ömürlü: {discord_id: [{"id", "emoji", "ts"}, ...]}. DB-siz —
# canlı, keçici effekt üçündür, tarixi məlumat saxlamağa ehtiyac yoxdur.
_profile_reactions = {}
_reaction_counter = 0

# ── Bayram günləri (bot.py-dəki HOLIDAY_DATES ilə EYNİ təqvim — bot.py birbaşa
# import oluna bilmir, çünki modul səviyyəsində bot.run() çağırır) ────────────
HOLIDAY_DATES = {
    (1, 1):   "Yeni İl",
    (3, 20):  "Novruz Bayramı",
    (3, 21):  "Novruz Bayramı",
    (5, 28):  "Respublika Günü",
    (10, 18): "Müstəqillik Günü",
}


def get_players():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, so2_nick, so2_id, elo, wins, losses FROM players ORDER BY elo DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    players = []
    for i, (discord_id, nick, so2_id, elo, wins, losses) in enumerate(rows, start=1):
        matches = wins + losses
        win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0
        rank_name, rank_color, rank_emoji = get_rank(elo)
        players.append({
            "rank": i,
            "discord_id": discord_id,
            "nick": nick,
            "so2_id": so2_id,
            "elo": elo,
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "rank_name": rank_name,
            "rank_color": list(rank_color),
        })
    return players


def get_total_matches():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM match_history")
        row = cursor.fetchone()
        result = row[0] if row else 0
    except sqlite3.OperationalError:
        result = 0
    conn.close()
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "Zenith's Academy",
        "short_name": "Zenith",
        "description": "Standoff 2 FACEIT 2v2 leaderboard və profil paneli",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0a0d",
        "theme_color": "#8a5ce6",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    })


@app.route("/offline")
def offline_page():
    return render_template("offline.html")


@app.route("/sw.js")
def service_worker():
    js = (
        "const CACHE = 'zenith-v2';\n"
        "const OFFLINE_URL = '/offline';\n"
        "self.addEventListener('install', e => {\n"
        "  self.skipWaiting();\n"
        "  e.waitUntil(caches.open(CACHE).then(c => c.add(OFFLINE_URL)));\n"
        "});\n"
        "self.addEventListener('activate', e => self.clients.claim());\n"
        "self.addEventListener('fetch', e => {\n"
        "  if (e.request.method !== 'GET') return;\n"
        "  if (e.request.mode === 'navigate') {\n"
        "    e.respondWith(fetch(e.request).catch(() => caches.match(OFFLINE_URL)));\n"
        "    return;\n"
        "  }\n"
        "  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));\n"
        "});\n"
    )
    return app.response_class(js, mimetype="application/javascript")


@app.route("/api/leaderboard")
def api_leaderboard():
    return jsonify({
        "players": get_players(),
        "total_matches": get_total_matches()
    })


def _profile_dict(discord_id):
    player = database.get_player(discord_id)
    if not player:
        return None
    _, nick, so2_id, elo, wins, losses = player[:6]
    stats = database.get_player_stats_dict(discord_id) or {}
    matches = wins + losses
    win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0
    rank_name, rank_color, rank_emoji = get_rank(elo)

    next_rank_name = None
    elo_to_next = 0
    tier_progress_pct = 100
    for i, (lo, hi, name, color, emoji) in enumerate(RANKS):
        if lo <= elo < hi:
            tier_progress_pct = round(((elo - lo) / max(hi - lo, 1)) * 100, 1) if hi < 9999 else 100
            if i + 1 < len(RANKS):
                next_rank_name = RANKS[i + 1][2]
                elo_to_next = hi - elo
            break

    today_key = time.strftime("%Y-%m-%d")
    search_count_today = _search_counts.get((today_key, str(so2_id)), 0)

    return {
        "discord_id": discord_id, "nick": nick, "so2_id": so2_id, "elo": elo,
        "wins": wins, "losses": losses, "matches": matches, "win_rate": win_rate,
        "kills": stats.get("kills", 0), "assists": stats.get("assists", 0), "deaths": stats.get("deaths", 0),
        "rank_name": rank_name, "rank_color": list(rank_color), "rank_emoji": rank_emoji,
        "next_rank_name": next_rank_name, "elo_to_next": elo_to_next, "tier_progress_pct": tier_progress_pct,
        "search_count_today": search_count_today,
    }


@app.route("/u/<int:discord_id>")
def public_profile(discord_id):
    profile = _profile_dict(discord_id)
    if not profile:
        abort(404)
    return render_template("profile_public.html", **profile)


@app.route("/embed/<int:discord_id>")
def embed_profile(discord_id):
    profile = _profile_dict(discord_id)
    if not profile:
        abort(404)
    return render_template("profile_embed.html", **profile)


@app.route("/api/profile/<int:discord_id>")
def api_profile(discord_id):
    profile = _profile_dict(discord_id)
    if not profile:
        abort(404)
    return jsonify(profile)


@app.route("/api/profile/<int:discord_id>/history")
def api_profile_history(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    history = list(reversed(database.get_player_match_history(discord_id, limit=30)))
    return jsonify([{"match_number": h["match_number"], "elo_after": h["elo_after"]} for h in history])


@app.route("/api/profile/<int:discord_id>/maps")
def api_profile_maps(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    stats = database.get_map_stats(discord_id)
    result = []
    for map_name, s in stats.items():
        matches = s["wins"] + s["losses"]
        win_rate = round((s["wins"] / matches) * 100, 1) if matches else 0.0
        result.append({"map": map_name, "wins": s["wins"], "losses": s["losses"], "matches": matches, "win_rate": win_rate})
    return jsonify(result)


@app.route("/api/profile/<int:discord_id>/heatmap")
def api_profile_heatmap(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    return jsonify(database.get_activity_heatmap_grid(discord_id))


@app.route("/api/seasons")
def api_seasons():
    return jsonify(database.get_completed_seasons())


@app.route("/api/season/<int:season_id>")
def api_season_leaderboard(season_id):
    rows = database.get_season_leaderboard(season_id, limit=10)
    return jsonify([
        {"nick": r[0], "so2_id": r[1], "elo_gained": r[2], "kills": r[3], "assists": r[4],
         "deaths": r[5], "wins": r[6], "losses": r[7], "discord_id": r[8]}
        for r in rows
    ])


@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    session_id = request.json.get("session_id") if request.is_json else None
    if not session_id:
        session_id = str(uuid.uuid4())
    now = time.time()
    _active_viewers[session_id] = now
    stale = [sid for sid, ts in _active_viewers.items() if now - ts > _VIEWER_TIMEOUT_SECONDS]
    for sid in stale:
        del _active_viewers[sid]
    return jsonify({"session_id": session_id, "viewers": len(_active_viewers)})


@app.route("/api/profile/<int:discord_id>/network")
def api_profile_network(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    return jsonify(database.get_teammate_network(discord_id))


@app.route("/api/profile/<int:discord_id>/milestones")
def api_profile_milestones(discord_id):
    milestones = database.get_player_milestones(discord_id)
    if milestones is None:
        abort(404)
    return jsonify(milestones)


@app.route("/api/profile/<int:discord_id>/momentum")
def api_profile_momentum(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    momentum = database.get_player_momentum(discord_id)
    return jsonify(momentum or {
        "net_change_24h": 0, "match_count_24h": 0, "heat_pct": 0,
        "avg_win_gain": 25.0, "avg_loss_amount": -20.0, "sample_size": 0,
    })


ALLOWED_REACTION_EMOJIS = {"🔥", "👏", "😮", "💪", "🏆", "❤️"}


@app.route("/api/profile/<int:discord_id>/react", methods=["POST"])
def api_profile_react(discord_id):
    global _reaction_counter
    emoji = (request.json or {}).get("emoji") if request.is_json else None
    if emoji not in ALLOWED_REACTION_EMOJIS:
        return jsonify({"ok": False}), 400
    now = time.time()
    _reaction_counter += 1
    entry = {"id": _reaction_counter, "emoji": emoji, "ts": now}
    bucket = _profile_reactions.setdefault(discord_id, [])
    bucket.append(entry)
    cutoff = now - 15
    _profile_reactions[discord_id] = [r for r in bucket if r["ts"] > cutoff]
    return jsonify({"ok": True, "id": entry["id"]})


@app.route("/api/profile/<int:discord_id>/reactions")
def api_profile_reactions(discord_id):
    since_id = request.args.get("since", 0, type=int)
    bucket = _profile_reactions.get(discord_id, [])
    fresh = [r for r in bucket if r["id"] > since_id]
    return jsonify(fresh)


@app.route("/api/active_matches")
def api_active_matches():
    matches = database.get_all_active_matches()
    result = []
    for m in matches:
        team_a_nicks = []
        for pid in m["team_a"]:
            p = database.get_player(pid)
            if p:
                team_a_nicks.append(p[1])
        team_b_nicks = []
        for pid in m["team_b"]:
            p = database.get_player(pid)
            if p:
                team_b_nicks.append(p[1])
        result.append({
            "match_number": m["match_number"],
            "team_a": team_a_nicks,
            "team_b": team_b_nicks,
            "selected_map": m["selected_map"],
            "created_at": m["created_at"],
            "is_golden": m["is_golden"],
            "is_lightning": m["is_lightning"],
        })
    return jsonify(result)


@app.route("/api/profile/<int:discord_id>/achievements")
def api_profile_achievements(discord_id):
    if not database.get_player(discord_id):
        abort(404)
    earned = database.get_player_achievements(discord_id)
    earned_ids = {a["id"] for a in earned}
    all_ach = database.get_all_achievements()
    locked = [a for a in all_ach if a["id"] not in earned_ids]
    return jsonify({"earned": earned, "locked": locked})


@app.route("/api/recent_matches")
def api_recent_matches():
    return jsonify(database.get_recent_matches(limit=15))


@app.route("/api/rising_star")
def api_rising_star():
    daily = database.get_rising_star(days=1)
    weekly = database.get_rising_star(days=7)
    return jsonify({"daily": daily, "weekly": weekly})


@app.route("/api/rank_distribution")
def api_rank_distribution():
    return jsonify(database.get_rank_distribution())


@app.route("/api/holiday")
def api_holiday():
    import datetime as _dt
    now = _dt.datetime.utcnow() + _dt.timedelta(hours=4)
    name = HOLIDAY_DATES.get((now.month, now.day))
    return jsonify({"is_holiday": name is not None, "name": name})


@app.route("/api/track_search", methods=["POST"])
def api_track_search():
    so2_id = (request.json or {}).get("so2_id") if request.is_json else None
    if not so2_id:
        return jsonify({"ok": False}), 400
    today_key = time.strftime("%Y-%m-%d")
    key = (today_key, str(so2_id))
    _search_counts[key] = _search_counts.get(key, 0) + 1
    # köhnə günlərin qeydlərini təmizlə (yaddaş sızmasının qarşısını almaq üçün)
    stale = [k for k in _search_counts if k[0] != today_key]
    for k in stale:
        del _search_counts[k]
    return jsonify({"ok": True})


@app.route("/compare/<int:id1>/<int:id2>")
def compare_profiles(id1, id2):
    p1 = _profile_dict(id1)
    p2 = _profile_dict(id2)
    if not p1 or not p2:
        abort(404)
    return render_template("compare.html", p1=p1, p2=p2)


@app.route("/admin")
def admin_dashboard():
    if not ADMIN_DASHBOARD_TOKEN or request.args.get("key") != ADMIN_DASHBOARD_TOKEN:
        abort(403)

    stats = database.get_activity_stats(days=7)
    hourly = database.get_hourly_activity(days=7)
    matches = database.get_recent_matches(limit=20)
    players = get_players()

    return render_template(
        "admin.html",
        stats=stats, hourly=hourly, matches=matches,
        players=players, total_matches=get_total_matches()
    )


def run_web_server():
    port = int(os.environ.get("WEB_PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
