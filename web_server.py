from flask import Flask, jsonify, render_template, request, abort
import sqlite3
import os
import database
from visual_cards import get_rank

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "bot_database.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "web_leaderboard", "templates")
ADMIN_DASHBOARD_TOKEN = os.environ.get("ADMIN_DASHBOARD_TOKEN", "")

app = Flask(__name__, template_folder=TEMPLATE_DIR)


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


@app.route("/u/<int:discord_id>")
def public_profile(discord_id):
    player = database.get_player(discord_id)
    if not player:
        abort(404)

    _, nick, so2_id, elo, wins, losses = player[:6]
    stats = database.get_player_stats_dict(discord_id) or {}
    matches = wins + losses
    win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0
    rank_name, rank_color, rank_emoji = get_rank(elo)

    return render_template(
        "profile_public.html",
        nick=nick, so2_id=so2_id, elo=elo, wins=wins, losses=losses,
        matches=matches, win_rate=win_rate,
        kills=stats.get("kills", 0), assists=stats.get("assists", 0), deaths=stats.get("deaths", 0),
        rank_name=rank_name, rank_color=rank_color, rank_emoji=rank_emoji
    )


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
