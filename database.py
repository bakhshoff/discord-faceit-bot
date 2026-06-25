import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "."), "bot_database.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=4000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def init_db():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            discord_id INTEGER PRIMARY KEY,
            so2_nick TEXT NOT NULL,
            so2_id TEXT NOT NULL,
            elo INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(players)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if "coins" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN coins INTEGER DEFAULT 0")
    if "active_banner" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN active_banner TEXT DEFAULT NULL")
    if "active_frame" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN active_frame TEXT DEFAULT NULL")
    if "zm_balance" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN zm_balance INTEGER DEFAULT 0")
    if "ai_memory" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN ai_memory TEXT DEFAULT NULL")
    if "kills" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN kills INTEGER DEFAULT 0")
    if "assists" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN assists INTEGER DEFAULT 0")
    if "deaths" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN deaths INTEGER DEFAULT 0")

    # ── Seasons ──────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_number INTEGER UNIQUE NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS season_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            season_id INTEGER NOT NULL,
            elo_start INTEGER DEFAULT 0,
            elo_gained INTEGER DEFAULT 0,
            kills INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            UNIQUE(discord_id, season_id)
        )
    """)

    # ── Active match lock ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_match (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            match_number INTEGER DEFAULT NULL,
            status TEXT DEFAULT NULL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO active_match (id) VALUES (1)")

    # ── Scan results ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_number INTEGER NOT NULL,
            scan_data TEXT NOT NULL,
            winner_team TEXT DEFAULT NULL,
            confirmed INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)

    # ── Daily tasks ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            kill_target INTEGER DEFAULT 0,
            assist_target INTEGER DEFAULT 0,
            reward_coins INTEGER NOT NULL,
            active INTEGER DEFAULT 1,
            expires_at INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            started_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            kills_progress INTEGER DEFAULT 0,
            assists_progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            UNIQUE(discord_id, task_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            acquired_at INTEGER NOT NULL,
            UNIQUE(discord_id, item_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_counter (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_number INTEGER DEFAULT 0
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO match_counter (id, last_number) VALUES (1, 0)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mukafat TEXT NOT NULL,
            end_unix INTEGER NOT NULL,
            winner_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            finished INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_type TEXT NOT NULL,
            played_at INTEGER NOT NULL,
            match_number INTEGER,
            winner_ids TEXT NOT NULL,
            loser_ids TEXT NOT NULL,
            winner_elo_before TEXT,
            winner_elo_after TEXT,
            loser_elo_before TEXT,
            loser_elo_after TEXT
        )
    """)

    # ===== STANDOFF MARKET / SKIN cÉ™dvÉ™llÉ™ri =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            image_url TEXT,
            active INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skin_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            skin_id INTEGER NOT NULL,
            skin_name TEXT NOT NULL,
            price_paid INTEGER NOT NULL,
            image_url TEXT,
            acquired_at INTEGER NOT NULL,
            delivered INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            change INTEGER NOT NULL,
            reason TEXT NOT NULL,
            log_type TEXT NOT NULL,
            balance_after INTEGER,
            created_at INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_boosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            boost_type TEXT NOT NULL,
            multiplier REAL NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)

    # Tez-tez istifadÉ™ edilÉ™n sorÄŸular Ã¼Ã§Ã¼n indekslÉ™r
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_elo       ON players(elo DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_id        ON players(discord_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user    ON inventory(discord_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_coin_logs_user    ON coin_logs(discord_id, created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(discord_id, created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_boosts_user       ON active_boosts(discord_id, expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skin_inv_user     ON skin_inventory(discord_id, acquired_at DESC)")

    conn.commit()
    conn.close()


def get_next_match_number():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE match_counter SET last_number = last_number + 1 WHERE id = 1")
    cursor.execute("SELECT last_number FROM match_counter WHERE id = 1")
    number = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return number

def register_player(discord_id, so2_nick, so2_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO players (discord_id, so2_nick, so2_id) VALUES (?, ?, ?)",
        (discord_id, so2_nick, so2_id)
    )
    conn.commit()
    conn.close()
    return True

def get_player(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_team_elo(winner_ids, loser_ids):
    """
    winner_ids, loser_ids: discord_id siyahÄ±larÄ± (hÉ™r komandada bir neÃ§É™ oyunÃ§u)
    KomandanÄ±n orta ELO-suna gÃ¶rÉ™ hesablanÄ±r, hÉ™r oyunÃ§u fÉ™rdi yenilÉ™nir.
    """
    conn = _get_conn()
    cursor = conn.cursor()

    def fetch_all(ids):
        result = []
        for discord_id in ids:
            cursor.execute("SELECT discord_id, so2_nick, elo, wins, losses FROM players WHERE discord_id = ?", (discord_id,))
            row = cursor.fetchone()
            if row:
                result.append(row)
        return result

    winners = fetch_all(winner_ids)
    losers = fetch_all(loser_ids)

    if not winners or not losers:
        conn.close()
        return None

    winner_avg_elo = sum(p[2] for p in winners) / len(winners)
    loser_avg_elo = sum(p[2] for p in losers) / len(losers)

    K = 32
    expected_winner = 1 / (1 + 10 ** ((loser_avg_elo - winner_avg_elo) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_avg_elo - loser_avg_elo) / 400))

    elo_change_winner = round(K * (1 - expected_winner))
    elo_change_loser = round(K * (0 - expected_loser))

    results = {"winners": [], "losers": []}

    for discord_id, nick, elo, wins, losses in winners:
        new_elo = elo + apply_elo_modifiers(discord_id, elo_change_winner)
        cursor.execute(
            "UPDATE players SET elo = ?, wins = ? WHERE discord_id = ?",
            (new_elo, wins + 1, discord_id)
        )
        results["winners"].append({"discord_id": discord_id, "nick": nick, "old_elo": elo, "new_elo": new_elo})

    for discord_id, nick, elo, wins, losses in losers:
        new_elo = elo + apply_elo_modifiers(discord_id, elo_change_loser)
        cursor.execute(
            "UPDATE players SET elo = ?, losses = ? WHERE discord_id = ?",
            (new_elo, losses + 1, discord_id)
        )
        results["losers"].append({"discord_id": discord_id, "nick": nick, "old_elo": elo, "new_elo": new_elo})

    conn.commit()
    conn.close()
    return results


def update_elo(winner_id, loser_id):
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT elo, wins, losses FROM players WHERE discord_id = ?", (winner_id,))
    winner = cursor.fetchone()
    cursor.execute("SELECT elo, wins, losses FROM players WHERE discord_id = ?", (loser_id,))
    loser = cursor.fetchone()

    if not winner or not loser:
        conn.close()
        return None

    winner_elo, winner_wins, winner_losses = winner
    loser_elo, loser_wins, loser_losses = loser

    K = 32
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_elo - loser_elo) / 400))

    elo_change_w = round(K * (1 - expected_winner))
    elo_change_l = round(K * (0 - expected_loser))
    elo_change_w = apply_elo_modifiers(winner_id, elo_change_w)
    elo_change_l = apply_elo_modifiers(loser_id, elo_change_l)
    new_winner_elo = winner_elo + elo_change_w
    new_loser_elo = loser_elo + elo_change_l

    cursor.execute(
        "UPDATE players SET elo = ?, wins = ? WHERE discord_id = ?",
        (new_winner_elo, winner_wins + 1, winner_id)
    )
    cursor.execute(
        "UPDATE players SET elo = ?, losses = ? WHERE discord_id = ?",
        (new_loser_elo, loser_losses + 1, loser_id)
    )
    conn.commit()
    conn.close()

    return {
        "winner_old_elo": winner_elo, "winner_new_elo": new_winner_elo,
        "loser_old_elo": loser_elo, "loser_new_elo": new_loser_elo
    }

def get_all_players(limit=500):
    """discord_id ilə birlikdə bütün oyunçuları qaytarır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, so2_nick, so2_id, elo FROM players ORDER BY elo DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "nick": r[1], "so2_id": r[2], "elo": r[3]} for r in rows]


def get_leaderboard(limit=20):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT so2_nick, so2_id, elo, wins, losses, active_banner FROM players ORDER BY elo DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


queue_list = []  # YaddaÅŸda saxlanÄ±lan mÃ¼vÉ™qqÉ™ti nÃ¶vbÉ™

def add_to_queue(discord_id, nick, elo, so2_id=""):
    for p in queue_list:
        if p["discord_id"] == discord_id:
            return False
    queue_list.append({"discord_id": discord_id, "nick": nick, "elo": elo, "so2_id": so2_id})
    return True

def remove_from_queue(discord_id):
    global queue_list
    before = len(queue_list)
    queue_list = [p for p in queue_list if p["discord_id"] != discord_id]
    return len(queue_list) < before

def queue_size():
    return len(queue_list)


def get_queue_list():
    return list(queue_list)

def clear_queue():
    global queue_list
    queue_list = []

def is_in_queue(discord_id):
    return any(p["discord_id"] == discord_id for p in queue_list)

def pop_10_and_balance():
    global queue_list
    if len(queue_list) < 10:
        return None
    import random
    players = queue_list[:10]
    queue_list = queue_list[10:]

    players_sorted = sorted(players, key=lambda p: p["elo"], reverse=True)
    team_a, team_b = [], []
    for i, p in enumerate(players_sorted):
        if i % 4 in (0, 3):
            team_a.append(p)
        else:
            team_b.append(p)

    random.shuffle(team_a)
    random.shuffle(team_b)

    captain_a = max(team_a, key=lambda p: p["elo"])
    captain_b = max(team_b, key=lambda p: p["elo"])

    return team_a, team_b, captain_a, captain_b


def create_giveaway(mukafat, end_unix, winner_id, channel_id, message_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO giveaways (mukafat, end_unix, winner_id, channel_id, message_id, finished) VALUES (?, ?, ?, ?, ?, 0)",
        (mukafat, end_unix, winner_id, channel_id, message_id)
    )
    conn.commit()
    giveaway_id = cursor.lastrowid
    conn.close()
    return giveaway_id


def get_due_giveaways(current_unix):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, mukafat, winner_id, channel_id, message_id FROM giveaways WHERE finished = 0 AND end_unix <= ?",
        (current_unix,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_giveaway_finished(giveaway_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE giveaways SET finished = 1 WHERE id = ?", (giveaway_id,))
    conn.commit()
    conn.close()


def add_coins(discord_id, amount):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET coins = coins + ? WHERE discord_id = ?", (amount, discord_id))
    conn.commit()
    cursor.execute("SELECT coins FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_coins(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def spend_coins(discord_id, amount):
    """Balans kifayÉ™tdirsÉ™ coin Ã§Ä±xÄ±r vÉ™ True qaytarÄ±r, yoxdursa False qaytarÄ±r."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] < amount:
        conn.close()
        return False
    cursor.execute("UPDATE players SET coins = coins - ? WHERE discord_id = ?", (amount, discord_id))
    conn.commit()
    conn.close()
    return True


def get_inventory(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM inventory WHERE discord_id = ?", (discord_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def owns_item(discord_id, item_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM inventory WHERE discord_id = ? AND item_id = ?", (discord_id, item_id))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def add_to_inventory(discord_id, item_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO inventory (discord_id, item_id, acquired_at) VALUES (?, ?, ?)",
            (discord_id, item_id, int(time.time()))
        )
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def set_active_banner(discord_id, item_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET active_banner = ? WHERE discord_id = ?", (item_id, discord_id))
    conn.commit()
    conn.close()


def get_active_banner(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT active_banner FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_active_frame(discord_id, item_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET active_frame = ? WHERE discord_id = ?", (item_id, discord_id))
    conn.commit()
    conn.close()


def get_active_frame(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT active_frame FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def record_match_history(match_type, winner_ids, loser_ids, winner_elo_before, winner_elo_after,
                          loser_elo_before, loser_elo_after, match_number=None):
    """
    match_type: "1v1" veya "5v5"
    winner_ids, loser_ids: discord_id siyahÄ±sÄ± (1v1 Ã¼Ã§Ã¼n tÉ™k elementli)
    winner_elo_before/after, loser_elo_before/after: hÉ™r oyunÃ§unun ELO-su, ids ilÉ™ eyni sÄ±rada
    """
    import json as _json
    import time as _time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO match_history
           (match_type, played_at, match_number, winner_ids, loser_ids,
            winner_elo_before, winner_elo_after, loser_elo_before, loser_elo_after)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_type, int(_time.time()), match_number,
         _json.dumps(winner_ids), _json.dumps(loser_ids),
         _json.dumps(winner_elo_before), _json.dumps(winner_elo_after),
         _json.dumps(loser_elo_before), _json.dumps(loser_elo_after))
    )
    conn.commit()
    conn.close()


def get_player_match_history(discord_id, limit=10):
    """VerilmiÅŸ oyunÃ§unun iÅŸtirak etdiyi son matÃ§larÄ± qaytarÄ±r (É™n yenidÉ™n kÃ¶hnÉ™yÉ™)."""
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM match_history ORDER BY played_at DESC")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        (mid, match_type, played_at, match_number, winner_ids_json, loser_ids_json,
         w_before_json, w_after_json, l_before_json, l_after_json) = row
        winner_ids = _json.loads(winner_ids_json)
        loser_ids = _json.loads(loser_ids_json)

        if discord_id in winner_ids:
            idx = winner_ids.index(discord_id)
            elo_before = _json.loads(w_before_json)[idx]
            elo_after = _json.loads(w_after_json)[idx]
            won = True
        elif discord_id in loser_ids:
            idx = loser_ids.index(discord_id)
            elo_before = _json.loads(l_before_json)[idx]
            elo_after = _json.loads(l_after_json)[idx]
            won = False
        else:
            continue

        results.append({
            "match_type": match_type,
            "played_at": played_at,
            "match_number": match_number,
            "won": won,
            "elo_before": elo_before,
            "elo_after": elo_after,
            "elo_change": elo_after - elo_before,
        })

        if len(results) >= limit:
            break

    return results


def get_total_match_count():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM match_history")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def admin_set_player_field(discord_id, field, value):
    """
    Admin panel Ã¼Ã§Ã¼n: bir oyunÃ§unun tÉ™k bir sahÉ™sini dÉ™yiÅŸir.
    field: 'so2_nick', 'so2_id', 'elo', 'coins', 'wins', 'losses'
    """
    allowed_fields = {"so2_nick", "so2_id", "elo", "coins", "zm_balance", "wins", "losses",
                      "kills", "assists", "deaths"}
    if field not in allowed_fields:
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()
    conn.close()
    return True


# ==================== STANDOFF MARKET / SKIN SISTEMI ====================

def add_skin(name, price, image_url=None):
    """MaÄŸazaya yeni skin É™lavÉ™ edir. YaradÄ±lan skin id-sini qaytarÄ±r."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO skins (name, price, image_url, active, created_at) VALUES (?, ?, ?, 1, ?)",
        (name, price, image_url, int(time.time()))
    )
    conn.commit()
    skin_id = cursor.lastrowid
    conn.close()
    return skin_id


def get_active_skins():
    """MaÄŸazada satÄ±ÅŸda olan (active=1) skinlÉ™ri qaytarÄ±r."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url FROM skins WHERE active = 1 ORDER BY price ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "price": r[2], "image_url": r[3]} for r in rows]


def get_skin_by_id(skin_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url, active FROM skins WHERE id = ?", (skin_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "price": row[2], "image_url": row[3], "active": row[4]}


def remove_skin(skin_id):
    """Skini maÄŸazadan gÃ¶tÃ¼rÃ¼r (active=0). TarixÃ§É™ Ã¼Ã§Ã¼n silmir, deaktiv edir."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE skins SET active = 0 WHERE id = ?", (skin_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def add_skin_to_inventory(discord_id, skin_id, skin_name, price_paid, image_url=None):
    """AlÄ±nan skini oyunÃ§unun skin envanterinÉ™ É™lavÉ™ edir (hÉ™r alÄ±ÅŸ ayrÄ± sÉ™tir)."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO skin_inventory (discord_id, skin_id, skin_name, price_paid, image_url, acquired_at, delivered)
           VALUES (?, ?, ?, ?, ?, ?, 0)""",
        (discord_id, skin_id, skin_name, price_paid, image_url, int(time.time()))
    )
    conn.commit()
    inv_id = cursor.lastrowid
    conn.close()
    return inv_id


def get_skin_inventory(discord_id, only_undelivered=False):
    """OyunÃ§unun skin envanterini qaytarÄ±r. only_undelivered=True olsa yalnÄ±z tÉ™hvil verilmÉ™yÉ™nlÉ™ri."""
    conn = _get_conn()
    cursor = conn.cursor()
    if only_undelivered:
        cursor.execute(
            "SELECT id, skin_id, skin_name, price_paid, image_url, acquired_at, delivered FROM skin_inventory WHERE discord_id = ? AND delivered = 0 ORDER BY acquired_at DESC",
            (discord_id,)
        )
    else:
        cursor.execute(
            "SELECT id, skin_id, skin_name, price_paid, image_url, acquired_at, delivered FROM skin_inventory WHERE discord_id = ? ORDER BY acquired_at DESC",
            (discord_id,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "skin_id": r[1], "skin_name": r[2], "price_paid": r[3],
         "image_url": r[4], "acquired_at": r[5], "delivered": r[6]}
        for r in rows
    ]


def get_skin_inventory_entry(inv_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, discord_id, skin_id, skin_name, price_paid, image_url, acquired_at, delivered FROM skin_inventory WHERE id = ?",
        (inv_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "discord_id": row[1], "skin_id": row[2], "skin_name": row[3],
            "price_paid": row[4], "image_url": row[5], "acquired_at": row[6], "delivered": row[7]}


def remove_skin_from_inventory(inv_id):
    """Admin manuel olaraq oyunÃ§unun envanterindÉ™n bir skini silir (oyunda tÉ™hvil verildikdÉ™)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skin_inventory WHERE id = ?", (inv_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def add_coin_log(discord_id, change, reason, log_type, balance_after=None):
    """
    Coin hÉ™rÉ™kÉ™tini loga yazÄ±r.
    change: mÃ¼sbÉ™t (qazanma) vÉ™ ya mÉ™nfi (xÉ™rclÉ™mÉ™) say
    reason: izah mÉ™tni (mÉ™s: "Skin alÄ±ÅŸÄ±: AK-47 Redline")
    log_type: "earn" vÉ™ ya "spend"
    """
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coin_logs (discord_id, change, reason, log_type, balance_after, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (discord_id, change, reason, log_type, balance_after, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_coin_logs(discord_id, log_type=None, limit=15):
    """
    OyunÃ§unun coin loglarÄ±nÄ± qaytarÄ±r (É™n yenidÉ™n kÃ¶hnÉ™yÉ™).
    log_type: None (hamÄ±sÄ±), "earn" (qazanma), "spend" (xÉ™rclÉ™mÉ™)
    """
    conn = _get_conn()
    cursor = conn.cursor()
    if log_type in ("earn", "spend"):
        cursor.execute(
            "SELECT change, reason, log_type, balance_after, created_at FROM coin_logs WHERE discord_id = ? AND log_type = ? ORDER BY created_at DESC LIMIT ?",
            (discord_id, log_type, limit)
        )
    else:
        cursor.execute(
            "SELECT change, reason, log_type, balance_after, created_at FROM coin_logs WHERE discord_id = ? ORDER BY created_at DESC LIMIT ?",
            (discord_id, limit)
        )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"change": r[0], "reason": r[1], "log_type": r[2], "balance_after": r[3], "created_at": r[4]}
        for r in rows
    ]


def get_zm_balance(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT zm_balance FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def add_zm(discord_id, amount):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET zm_balance = zm_balance + ? WHERE discord_id = ?", (amount, discord_id))
    conn.commit()
    cursor.execute("SELECT zm_balance FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def spend_zm(discord_id, amount):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT zm_balance FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] < amount:
        conn.close()
        return False
    cursor.execute("UPDATE players SET zm_balance = zm_balance - ? WHERE discord_id = ?", (amount, discord_id))
    conn.commit()
    conn.close()
    return True


def exchange_coins_to_azn(discord_id, coins_per_pack=250, azn_per_pack=0.5):
    """250 coin Ã§evirir, 0.5 AZN É™lavÉ™ edir. (success, new_coins, new_zm) qaytarÄ±r."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT coins, zm_balance FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] < coins_per_pack:
        conn.close()
        return False, 0, 0
    new_coins = row[0] - coins_per_pack
    new_zm = round(float(row[1] or 0) + azn_per_pack, 2)
    cursor.execute("UPDATE players SET coins = ?, zm_balance = ? WHERE discord_id = ?",
                   (new_coins, new_zm, discord_id))
    conn.commit()
    conn.close()
    return True, new_coins, new_zm


def apply_elo_modifiers(discord_id, elo_change):
    if elo_change > 0:
        for bt in ("boost_100", "boost_50"):
            b = get_active_boost(discord_id, bt)
            if b:
                return round(elo_change * b["multiplier"])
    elif elo_change < 0:
        if get_active_boost(discord_id, "protection"):
            return 0
    return elo_change


def add_boost(discord_id, boost_type, multiplier, duration_seconds):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("SELECT id, expires_at FROM active_boosts WHERE discord_id = ? AND boost_type = ?", (discord_id, boost_type))
    existing = cursor.fetchone()
    if existing:
        new_expires = max(existing[1], now) + duration_seconds
        cursor.execute("UPDATE active_boosts SET expires_at = ?, multiplier = ? WHERE id = ?", (new_expires, multiplier, existing[0]))
    else:
        cursor.execute("INSERT INTO active_boosts (discord_id, boost_type, multiplier, expires_at) VALUES (?, ?, ?, ?)",
                      (discord_id, boost_type, multiplier, now + duration_seconds))
    conn.commit()
    conn.close()


def get_active_boost(discord_id, boost_type):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, multiplier, expires_at FROM active_boosts WHERE discord_id = ? AND boost_type = ? AND expires_at > ?",
        (discord_id, boost_type, int(time.time()))
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "multiplier": row[1], "expires_at": row[2]}


def get_all_active_boosts(discord_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT boost_type, multiplier, expires_at FROM active_boosts WHERE discord_id = ? AND expires_at > ? ORDER BY boost_type",
        (discord_id, int(time.time()))
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"boost_type": r[0], "multiplier": r[1], "expires_at": r[2]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# KILLS / ASSISTS / DEATHS
# ═══════════════════════════════════════════════════════════════════════════════

def add_combat_stats(discord_id, kills=0, assists=0, deaths=0):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE players SET kills=kills+?, assists=assists+?, deaths=deaths+? WHERE discord_id=?",
        (kills, assists, deaths, discord_id)
    )
    conn.commit()
    conn.close()


def get_combat_stats(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT kills, assists, deaths FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return {"kills": row[0], "assists": row[1], "deaths": row[2]} if row else {"kills": 0, "assists": 0, "deaths": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# SEASON SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

def get_or_create_current_season():
    import datetime as dt
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, season_number, start_date, end_date FROM seasons WHERE status='active' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        conn.close()
        return {"id": row[0], "season_number": row[1], "start_date": row[2], "end_date": row[3]}
    # Yeni sezon yarat
    now = dt.date.today()
    # Ayın 1-i başlayır, ayın son günü bitir
    start = now.replace(day=1).isoformat()
    if now.month == 12:
        end = now.replace(year=now.year+1, month=1, day=1).isoformat()
    else:
        end = now.replace(month=now.month+1, day=1).isoformat()
    cursor.execute("SELECT COALESCE(MAX(season_number),0)+1 FROM seasons")
    season_num = cursor.fetchone()[0]
    cursor.execute("INSERT INTO seasons (season_number, start_date, end_date, status) VALUES (?,?,?,'active')",
                   (season_num, start, end))
    conn.commit()
    sid = cursor.lastrowid
    conn.close()
    return {"id": sid, "season_number": season_num, "start_date": start, "end_date": end}


def get_season_by_number(season_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, season_number, start_date, end_date, status FROM seasons WHERE season_number=?", (season_number,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "season_number": row[1], "start_date": row[2], "end_date": row[3], "status": row[4]}


def add_season_stat(discord_id, season_id, kills=0, assists=0, deaths=0, wins=0, losses=0, elo_gained=0, elo_start=0):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO season_stats (discord_id, season_id, elo_start, elo_gained, kills, assists, deaths, wins, losses)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(discord_id, season_id) DO UPDATE SET
            elo_gained=elo_gained+excluded.elo_gained,
            kills=kills+excluded.kills,
            assists=assists+excluded.assists,
            deaths=deaths+excluded.deaths,
            wins=wins+excluded.wins,
            losses=losses+excluded.losses
    """, (discord_id, season_id, elo_start, elo_gained, kills, assists, deaths, wins, losses))
    conn.commit()
    conn.close()


def get_season_stat(discord_id, season_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT elo_start,elo_gained,kills,assists,deaths,wins,losses FROM season_stats WHERE discord_id=? AND season_id=?",
                   (discord_id, season_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"elo_start": 0, "elo_gained": 0, "kills": 0, "assists": 0, "deaths": 0, "wins": 0, "losses": 0}
    return {"elo_start": row[0], "elo_gained": row[1], "kills": row[2], "assists": row[3],
            "deaths": row[4], "wins": row[5], "losses": row[6]}


def get_season_leaderboard(season_id, limit=20):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.so2_nick, p.so2_id, ss.elo_gained, ss.kills, ss.assists, ss.deaths, ss.wins, ss.losses, p.discord_id
        FROM season_stats ss
        JOIN players p ON p.discord_id = ss.discord_id
        WHERE ss.season_id=?
        ORDER BY ss.elo_gained DESC LIMIT ?
    """, (season_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def close_season(season_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE seasons SET status='completed' WHERE id=?", (season_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# AKTİV MATÇ KİLİDİ
# ═══════════════════════════════════════════════════════════════════════════════

def set_active_match(match_number, team_a_json=None, team_b_json=None,
                     log_message_id=None, log_channel_id=None, selected_map=None):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(active_match)")
    cols = [r[1] for r in cursor.fetchall()]
    for col, default in [("team_a","NULL"),("team_b","NULL"),
                         ("log_message_id","NULL"),("log_channel_id","NULL"),
                         ("selected_map","NULL")]:
        if col not in cols:
            cursor.execute(f"ALTER TABLE active_match ADD COLUMN {col} TEXT DEFAULT {default}")
    cursor.execute(
        "UPDATE active_match SET match_number=?, status='active', "
        "team_a=?, team_b=?, log_message_id=?, log_channel_id=?, selected_map=? WHERE id=1",
        (match_number, team_a_json, team_b_json,
         str(log_message_id) if log_message_id else None,
         str(log_channel_id) if log_channel_id else None,
         selected_map)
    )
    conn.commit()
    conn.close()


def clear_active_match():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE active_match SET match_number=NULL, status=NULL, "
        "team_a=NULL, team_b=NULL, log_message_id=NULL, log_channel_id=NULL, selected_map=NULL WHERE id=1"
    )
    conn.commit()
    conn.close()


def get_active_match():
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(active_match)")
    cols = [r[1] for r in cursor.fetchall()]
    extra = "team_a" in cols
    if extra:
        cursor.execute("SELECT match_number, status, team_a, team_b, log_message_id, log_channel_id, selected_map FROM active_match WHERE id=1")
    else:
        cursor.execute("SELECT match_number, status FROM active_match WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    if not row or row[1] is None:
        return None
    result = {"match_number": row[0], "status": row[1],
              "team_a": [], "team_b": [],
              "log_message_id": None, "log_channel_id": None, "selected_map": None}
    if extra and len(row) >= 7:
        result["team_a"]         = _json.loads(row[2]) if row[2] else []
        result["team_b"]         = _json.loads(row[3]) if row[3] else []
        result["log_message_id"] = int(row[4]) if row[4] else None
        result["log_channel_id"] = int(row[5]) if row[5] else None
        result["selected_map"]   = row[6]
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN NƏTİCƏLƏRİ
# ═══════════════════════════════════════════════════════════════════════════════

def save_scan_result(match_number, scan_data_json, winner_team=None):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scan_results WHERE match_number=? AND confirmed=0", (match_number,))
    cursor.execute(
        "INSERT INTO scan_results (match_number, scan_data, winner_team, confirmed, created_at) VALUES (?,?,?,0,?)",
        (match_number, scan_data_json, winner_team, int(time.time()))
    )
    conn.commit()
    rid = cursor.lastrowid
    conn.close()
    return rid


def get_scan_result(match_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, scan_data, winner_team, confirmed FROM scan_results WHERE match_number=? ORDER BY id DESC LIMIT 1",
                   (match_number,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "scan_data": row[1], "winner_team": row[2], "confirmed": row[3]}


def confirm_scan(scan_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE scan_results SET confirmed=1 WHERE id=?", (scan_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK TAPŞIRIQLAR
# ═══════════════════════════════════════════════════════════════════════════════

def refresh_daily_tasks():
    """Vaxtı keçmiş tapşırıqları silir, 3 aktiv tapşırıq olmasını təmin edir."""
    import time, random as rnd
    TASK_POOL = [
        ("24 saat ərzində 35 kill əldə et",    35, 0,  80),
        ("24 saat ərzində 20 kill əldə et",    20, 0,  45),
        ("24 saat ərzində 10 asist et",          0, 10, 35),
        ("24 saat ərzində 50 kill əldə et",    50, 0, 120),
        ("24 saat ərzində 30 kill + 5 asist",  30, 5,  90),
        ("24 saat ərzində 15 kill + 10 asist", 15, 10, 65),
        ("24 saat ərzində 25 kill əldə et",    25, 0,  55),
        ("24 saat ərzində 40 kill əldə et",    40, 0, 100),
        ("24 saat ərzində 8 asist et",           0, 8,  30),
        ("24 saat ərzində 45 kill + 3 asist",  45, 3, 110),
    ]
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("DELETE FROM daily_tasks WHERE expires_at <= ?", (now,))
    cursor.execute("SELECT COUNT(*) FROM daily_tasks WHERE active=1 AND expires_at > ?", (now,))
    count = cursor.fetchone()[0]
    needed = 3 - count
    exp = now + 86400
    for _ in range(needed):
        desc, kt, at, rc = rnd.choice(TASK_POOL)
        cursor.execute("INSERT INTO daily_tasks (description, kill_target, assist_target, reward_coins, active, expires_at) VALUES (?,?,?,?,1,?)",
                       (desc, kt, at, rc, exp))
    conn.commit()
    conn.close()


def get_active_daily_tasks():
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, kill_target, assist_target, reward_coins, expires_at FROM daily_tasks WHERE active=1 AND expires_at > ? ORDER BY id LIMIT 3",
                   (int(time.time()),))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "description": r[1], "kill_target": r[2], "assist_target": r[3],
             "reward_coins": r[4], "expires_at": r[5]} for r in rows]


def get_player_active_task(discord_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pt.id, pt.task_id, dt.description, dt.kill_target, dt.assist_target, dt.reward_coins,
               pt.kills_progress, pt.assists_progress, pt.expires_at, pt.completed, pt.failed
        FROM player_tasks pt
        JOIN daily_tasks dt ON dt.id = pt.task_id
        WHERE pt.discord_id=? AND pt.completed=0 AND pt.failed=0 AND pt.expires_at > ?
        ORDER BY pt.id DESC LIMIT 1
    """, (discord_id, int(time.time())))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "task_id": row[1], "description": row[2], "kill_target": row[3],
            "assist_target": row[4], "reward_coins": row[5], "kills_progress": row[6],
            "assists_progress": row[7], "expires_at": row[8], "completed": row[9], "failed": row[10]}


def assign_task_to_player(discord_id, task_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    exp = now + 86400
    try:
        cursor.execute("INSERT INTO player_tasks (discord_id, task_id, started_at, expires_at) VALUES (?,?,?,?)",
                       (discord_id, task_id, now, exp))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def update_task_progress(discord_id, kills=0, assists=0):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE player_tasks SET kills_progress=kills_progress+?, assists_progress=assists_progress+?
        WHERE discord_id=? AND completed=0 AND failed=0 AND expires_at > ?
    """, (kills, assists, discord_id, int(time.time())))
    conn.commit()
    # Check completion
    cursor.execute("""
        SELECT pt.id, pt.kills_progress, pt.assists_progress, dt.kill_target, dt.assist_target, dt.reward_coins
        FROM player_tasks pt JOIN daily_tasks dt ON dt.id=pt.task_id
        WHERE pt.discord_id=? AND pt.completed=0 AND pt.failed=0 AND pt.expires_at > ?
    """, (discord_id, int(time.time())))
    row = cursor.fetchone()
    completed = False
    reward = 0
    if row:
        pt_id, kp, ap, kt, at, rc = row
        if kp >= kt and ap >= at:
            cursor.execute("UPDATE player_tasks SET completed=1 WHERE id=?", (pt_id,))
            conn.commit()
            completed = True
            reward = rc
    conn.close()
    return completed, reward


def fail_expired_tasks():
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE player_tasks SET failed=1 WHERE completed=0 AND failed=0 AND expires_at <= ?",
                   (int(time.time()),))
    conn.commit()
    conn.close()
