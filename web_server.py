from flask import Flask, jsonify, render_template, request, abort
import sqlite3
import os
import time
import uuid
import database
from visual_cards import get_rank

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "bot_database.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "web_leaderboard", "templates")
ADMIN_DASHBOARD_TOKEN = os.environ.get("ADMIN_DASHBOARD_TOKEN", "")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# ── Canlı baxanlar sayğacı ────────────────────────────────────────────────────
# Sadə heartbeat-əsaslı izləmə: hər səhifə ~12 saniyədə bir /api/heartbeat çağırır,
# server son 30 saniyədə "səs vermiş" unikal session-ları sayır. DB-siz, yaddaşda —
# bot restart olsa sıfırlanır (canlı göstərici üçün məqbul, tarixi məlumat deyil).
_VIEWER_TIMEOUT_SECONDS = 30
_active_viewers = {}


def get_players():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT so2_nick, so2_id, elo, wins, losses FROM players ORDER BY elo DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    players = []
    for i, (nick, so2_id, elo, wins, losses) in enumerate(rows, start=1):
        matches = wins + losses
        win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0
        players.append({
            "rank": i,
            "nick": nick,
            "so2_id": so2_id,
            "elo": elo,
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate
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
    return {
        "discord_id": discord_id, "nick": nick, "so2_id": so2_id, "elo": elo,
        "wins": wins, "losses": losses, "matches": matches, "win_rate": win_rate,
        "kills": stats.get("kills", 0), "assists": stats.get("assists", 0), "deaths": stats.get("deaths", 0),
        "rank_name": rank_name, "rank_color": list(rank_color), "rank_emoji": rank_emoji,
    }


@app.route("/u/<int:discord_id>")
def public_profile(discord_id):
    profile = _profile_dict(discord_id)
    if not profile:
        abort(404)
    return render_template("profile_public.html", **profile)


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
