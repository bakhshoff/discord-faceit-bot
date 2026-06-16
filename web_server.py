from flask import Flask, jsonify, render_template
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "bot_database.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "web_leaderboard", "templates")

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/leaderboard")
def api_leaderboard():
    return jsonify(get_players())


def run_web_server():
    port = int(os.environ.get("WEB_PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
