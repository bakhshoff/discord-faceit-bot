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
    if "win_streak" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN win_streak INTEGER DEFAULT 0")
    if "max_streak" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN max_streak INTEGER DEFAULT 0")
    if "is_banned" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN is_banned INTEGER DEFAULT 0")
    if "peak_elo" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN peak_elo INTEGER DEFAULT 1000")
    if "banned_until" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN banned_until INTEGER DEFAULT 0")
    if "lang" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN lang TEXT DEFAULT 'az'")

    # ── Daily Login ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logins (
            discord_id   INTEGER PRIMARY KEY,
            last_login   INTEGER DEFAULT 0,
            login_streak INTEGER DEFAULT 0
        )
    """)

    # ── Admin Logs ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            action     TEXT    NOT NULL,
            target_id  INTEGER NOT NULL,
            field      TEXT,
            old_val    TEXT,
            new_val    TEXT,
            reason     TEXT,
            admin_id   INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    # ── Market Discounts ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_discounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     TEXT    NOT NULL,
            item_type   TEXT    NOT NULL DEFAULT 'market',
            discount    INTEGER NOT NULL,
            expires_at  INTEGER NOT NULL,
            created_at  INTEGER NOT NULL
        )
    """)

    # ── Personal Records ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_records (
            discord_id   INTEGER PRIMARY KEY,
            best_kills   INTEGER DEFAULT 0,
            best_assists INTEGER DEFAULT 0,
            best_deaths  INTEGER DEFAULT 0,
            best_kd      REAL    DEFAULT 0,
            best_match   INTEGER DEFAULT NULL,
            updated_at   INTEGER DEFAULT 0
        )
    """)

    # ── ELO History ───────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS elo_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            elo INTEGER NOT NULL,
            recorded_at INTEGER NOT NULL
        )
    """)

    # ── Warnings ─────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            admin_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    # ── Achievements ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            earned_at INTEGER NOT NULL,
            UNIQUE(discord_id, achievement_id)
        )
    """)

    # ── Match predictions ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_number INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            predicted_team TEXT NOT NULL,
            bet_coins INTEGER NOT NULL,
            result TEXT DEFAULT NULL,
            paid INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            UNIQUE(match_number, discord_id)
        )
    """)

    # Achievements seed data
    _seed_achievements(cursor)

    # Battle Pass
    init_battle_pass(cursor)

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
        "SELECT so2_nick, so2_id, elo, wins, losses, active_banner, kills, deaths FROM players ORDER BY elo DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


queue_list = []      # Müvəqqəti növbə

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

    players    = queue_list[:10]
    queue_list = queue_list[10:]

    # Saf ELO balansı — yüksəkdən aşağıya sırala, snake draft
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
    """Vaxtı keçmiş tapşırıqları silir, 3 unikal aktiv tapşırıq yaradır."""
    import time, random as rnd
    TASK_POOL = [
        ("35 kill əldə et",          35, 0,  80),
        ("20 kill əldə et",          20, 0,  45),
        ("10 asist et",               0, 10, 35),
        ("50 kill əldə et",          50, 0, 120),
        ("30 kill + 5 asist",        30, 5,  90),
        ("15 kill + 10 asist",       15, 10, 65),
        ("25 kill əldə et",          25, 0,  55),
        ("40 kill əldə et",          40, 0, 100),
        ("8 asist et",                0, 8,  30),
        ("45 kill + 3 asist",        45, 3, 110),
        ("10 kill + 8 asist",        10, 8,  60),
        ("60 kill əldə et",          60, 0, 150),
        ("5 asist et",                0, 5,  25),
        ("20 kill + 5 asist",        20, 5,  70),
        ("12 asist et",               0, 12, 45),
    ]
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("DELETE FROM daily_tasks WHERE expires_at <= ?", (now,))

    # Hal-hazırda aktiv olan tapşırıqların açıqlamasını al (təkrar olmasın)
    cursor.execute("SELECT description FROM daily_tasks WHERE active=1 AND expires_at > ?", (now,))
    existing_descs = {r[0] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM daily_tasks WHERE active=1 AND expires_at > ?", (now,))
    count  = cursor.fetchone()[0]
    needed = 3 - count

    # Mövcud olanlardan fərqli tapşırıqları seç
    available = [t for t in TASK_POOL if t[0] not in existing_descs]
    if len(available) < needed:
        available = TASK_POOL  # Çatmasa bütün pooldan seç

    chosen = rnd.sample(available, min(needed, len(available)))
    exp    = now + 86400
    for desc, kt, at, rc in chosen:
        cursor.execute(
            "INSERT INTO daily_tasks (description, kill_target, assist_target, reward_coins, active, expires_at) VALUES (?,?,?,?,1,?)",
            (desc, kt, at, rc, exp)
        )
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


def _seed_achievements(cursor):
    ACHIEVEMENTS = [
        ("first_match",   "İlk Matç",        "İlk matçını oynadın",                "🎮"),
        ("win_10",        "10 Qələbə",        "10 matç qazandın",                   "🏆"),
        ("win_50",        "50 Qələbə",        "50 matç qazandın",                   "👑"),
        ("kill_50",       "50 Kill",          "Cəmi 50 kill etdin",                 "🔫"),
        ("kill_100",      "100 Kill",         "Cəmi 100 kill etdin",                "💀"),
        ("kill_500",      "500 Kill",         "Cəmi 500 kill etdin",                "🎯"),
        ("mvp_3",         "Üçlü MVP",         "3 dəfə MVP seçildin",                "⭐"),
        ("mvp_10",        "MVP Ustası",       "10 dəfə MVP seçildin",               "🌟"),
        ("streak_3",      "Seriya 3",         "3 qələbə sıraı",                     "🔥"),
        ("streak_5",      "Seriya 5",         "5 qələbə sıraı",                     "💥"),
        ("streak_10",     "Seriya 10",        "10 qələbə sıraı",                    "⚡"),
        ("kd_2",          "KD 2.0+",          "K/D nisbətin 2.0-ı keçdi",           "🗡️"),
        ("task_10",       "Tapşırıq Qəhrəmanı","10 günlük tapşırıq tamamladın",     "🎯"),
        ("elo_1200",      "Elite Oyunçu",     "1200 ELO-ya çatdın",                 "💎"),
        ("elo_1500",      "Master",           "1500 ELO-ya çatdın",                 "👑"),
    ]
    for ach_id, name, desc, icon in ACHIEVEMENTS:
        cursor.execute(
            "INSERT OR IGNORE INTO achievements (id, name, description, icon) VALUES (?,?,?,?)",
            (ach_id, name, desc, icon)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# WIN STREAK
# ═══════════════════════════════════════════════════════════════════════════════

def update_streak(discord_id, won: bool):
    """Qələbədə streak artır, məğlubiyyətdə sıfırlanır. (streak, max_streak) qaytarır."""
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT win_streak, max_streak FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if not row:
        conn.close(); return 0, 0
    streak, max_s = row
    if won:
        streak += 1
        max_s = max(max_s, streak)
    else:
        streak = 0
    cursor.execute("UPDATE players SET win_streak=?, max_streak=? WHERE discord_id=?",
                   (streak, max_s, discord_id))
    conn.commit(); conn.close()
    return streak, max_s


def get_streak_bonus(streak: int) -> tuple:
    """(bonus_coins, bonus_elo) qaytarır."""
    if streak >= 10: return 20, 5
    if streak >= 7:  return 15, 3
    if streak >= 5:  return 10, 2
    if streak >= 3:  return 5,  1
    return 0, 0


# ═══════════════════════════════════════════════════════════════════════════════
# XƏBƏRDARLIQ / BAN
# ═══════════════════════════════════════════════════════════════════════════════

def add_warning(discord_id, reason, admin_id):
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO warnings (discord_id, reason, admin_id, created_at) VALUES (?,?,?,?)",
                   (discord_id, reason, admin_id, int(time.time())))
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM warnings WHERE discord_id=?", (discord_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_warnings(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, reason, admin_id, created_at FROM warnings WHERE discord_id=? ORDER BY created_at DESC",
                   (discord_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "reason": r[1], "admin_id": r[2], "created_at": r[3]} for r in rows]


def clear_warnings(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warnings WHERE discord_id=?", (discord_id,))
    conn.commit(); conn.close()


def ban_player(discord_id, reason, admin_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET is_banned=1 WHERE discord_id=?", (discord_id,))
    conn.commit(); conn.close()
    add_warning(discord_id, f"[BAN] {reason}", admin_id)


def unban_player(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET is_banned=0 WHERE discord_id=?", (discord_id,))
    conn.commit(); conn.close()


def is_banned(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0])


# ═══════════════════════════════════════════════════════════════════════════════
# NAİLİYYƏTLƏR
# ═══════════════════════════════════════════════════════════════════════════════

def check_and_grant_achievements(discord_id) -> list:
    """Yeni qazanılan nailiyyətləri qaytarır."""
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT wins, kills, win_streak, max_streak, elo FROM players WHERE discord_id=?",
        (discord_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close(); return []
    wins, kills, streak, max_s, elo = row

    cursor.execute("SELECT achievement_id FROM player_achievements WHERE discord_id=?", (discord_id,))
    owned = {r[0] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM player_tasks WHERE discord_id=? AND completed=1", (discord_id,))
    tasks_done = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scan_results sr "
                   "JOIN match_history mh ON mh.match_number=sr.match_number "
                   "WHERE sr.confirmed=1", ())
    # MVP sayı ayrıca coin log-dan bax
    cursor.execute("SELECT COUNT(*) FROM coin_logs WHERE discord_id=? AND reason='MVP mükafatı'",
                   (discord_id,))
    mvp_count = cursor.fetchone()[0]

    kd_val = 0.0
    cursor.execute("SELECT kills, deaths FROM players WHERE discord_id=?", (discord_id,))
    kd_row = cursor.fetchone()
    if kd_row:
        kd_val = kd_row[0] / max(kd_row[1], 1)

    candidates = {
        "first_match": wins >= 1,
        "win_10":      wins >= 10,
        "win_50":      wins >= 50,
        "kill_50":     kills >= 50,
        "kill_100":    kills >= 100,
        "kill_500":    kills >= 500,
        "mvp_3":       mvp_count >= 3,
        "mvp_10":      mvp_count >= 10,
        "streak_3":    max_s >= 3,
        "streak_5":    max_s >= 5,
        "streak_10":   max_s >= 10,
        "kd_2":        kd_val >= 2.0,
        "task_10":     tasks_done >= 10,
        "elo_1200":    elo >= 1200,
        "elo_1500":    elo >= 1500,
    }

    now = int(time.time())
    new_ones = []
    for ach_id, condition in candidates.items():
        if condition and ach_id not in owned:
            cursor.execute(
                "INSERT OR IGNORE INTO player_achievements (discord_id, achievement_id, earned_at) VALUES (?,?,?)",
                (discord_id, ach_id, now)
            )
            if cursor.rowcount:
                cursor.execute("SELECT name, icon FROM achievements WHERE id=?", (ach_id,))
                ach = cursor.fetchone()
                if ach:
                    new_ones.append({"id": ach_id, "name": ach[0], "icon": ach[1]})

    conn.commit(); conn.close()
    return new_ones


def get_player_achievements(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""SELECT a.id, a.name, a.description, a.icon, pa.earned_at
                      FROM player_achievements pa
                      JOIN achievements a ON a.id=pa.achievement_id
                      WHERE pa.discord_id=? ORDER BY pa.earned_at DESC""", (discord_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "icon": r[3], "earned_at": r[4]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# MATÇ MƏRCİ (PREDICTION)
# ═══════════════════════════════════════════════════════════════════════════════

def place_prediction(discord_id, match_number, predicted_team, bet_coins):
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] < bet_coins:
        conn.close(); return False, "Kifayət qədər coin yoxdur."
    cursor.execute("SELECT id FROM match_predictions WHERE match_number=? AND discord_id=?",
                   (match_number, discord_id))
    if cursor.fetchone():
        conn.close(); return False, "Artıq mərc etmisiniz."
    cursor.execute("UPDATE players SET coins=coins-? WHERE discord_id=?", (bet_coins, discord_id))
    cursor.execute(
        "INSERT INTO match_predictions (match_number, discord_id, predicted_team, bet_coins, created_at) VALUES (?,?,?,?,?)",
        (match_number, discord_id, predicted_team, bet_coins, int(time.time()))
    )
    conn.commit(); conn.close()
    return True, "Mərc qəbul edildi."


def resolve_predictions(match_number, winner_label):
    """Qalib labeli 'Komanda A' / 'Komanda B'. Düz tapanlar 2x qazanır."""
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, discord_id, predicted_team, bet_coins FROM match_predictions WHERE match_number=? AND paid=0",
        (match_number,)
    )
    preds = cursor.fetchall()
    winners = []
    for pred_id, did, pred_team, bet in preds:
        won = pred_team == winner_label
        result = "win" if won else "loss"
        cursor.execute("UPDATE match_predictions SET result=?, paid=1 WHERE id=?", (result, pred_id))
        if won:
            payout = bet * 2
            cursor.execute("UPDATE players SET coins=coins+? WHERE discord_id=?", (payout, did))
            winners.append({"discord_id": did, "bet": bet, "payout": payout})
    conn.commit(); conn.close()
    return winners


def get_predictions(match_number):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, predicted_team, bet_coins, result FROM match_predictions WHERE match_number=?",
        (match_number,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "team": r[1], "bet": r[2], "result": r[3]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# ELO TARİXÇƏSİ + PİK ELO
# ═══════════════════════════════════════════════════════════════════════════════

def record_elo_history(discord_id: int, elo: int):
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO elo_history (discord_id, elo, recorded_at) VALUES (?,?,?)",
                   (discord_id, elo, int(time.time())))
    cursor.execute("UPDATE players SET peak_elo=MAX(peak_elo, ?) WHERE discord_id=?", (elo, discord_id))
    conn.commit(); conn.close()


def get_elo_history(discord_id: int, limit=30):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT elo, recorded_at FROM elo_history WHERE discord_id=? ORDER BY recorded_at DESC LIMIT ?",
                   (discord_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return list(reversed(rows))  # köhnədən yeniyə


def get_peak_elo(discord_id: int):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT peak_elo FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 1000


# ═══════════════════════════════════════════════════════════════════════════════
# COİN TRANSFER
# ═══════════════════════════════════════════════════════════════════════════════

def transfer_coins(from_id: int, to_id: int, amount: int, commission_pct: float = 0.20):
    """Coin köçürmə. Göndərən amount ödəyir, alan (1-commission)*amount alır."""
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE discord_id=?", (from_id,))
    row = cursor.fetchone()
    if not row or row[0] < amount:
        conn.close(); return False, "Kifayət qədər coin yoxdur.", 0, 0
    commission   = int(amount * commission_pct)
    receiver_amt = amount - commission
    cursor.execute("UPDATE players SET coins=coins-? WHERE discord_id=?", (amount, from_id))
    cursor.execute("UPDATE players SET coins=coins+? WHERE discord_id=?", (receiver_amt, to_id))
    conn.commit(); conn.close()
    return True, "OK", commission, receiver_amt


# ═══════════════════════════════════════════════════════════════════════════════
# FƏALİYYƏT PANELİ
# ═══════════════════════════════════════════════════════════════════════════════

def get_activity_stats(days=7):
    import time
    since  = int(time.time()) - days * 86400
    conn   = _get_conn()
    cursor = conn.cursor()

    # Matç sayı
    cursor.execute("SELECT COUNT(*) FROM match_history WHERE played_at >= ?", (since,))
    match_count = cursor.fetchone()[0]

    # Aktiv oyunçular (matçlara iştirak etmiş)
    cursor.execute("""
        SELECT p.so2_nick, COUNT(*) as cnt
        FROM match_history mh
        JOIN players p ON (mh.winner_ids LIKE '%'||p.discord_id||'%'
                        OR mh.loser_ids  LIKE '%'||p.discord_id||'%')
        WHERE mh.played_at >= ?
        GROUP BY p.discord_id ORDER BY cnt DESC LIMIT 5
    """, (since,))
    top_active = cursor.fetchall()

    # Ümumi kills bu dövrdə
    cursor.execute("""
        SELECT COALESCE(SUM(k), 0) FROM (
            SELECT SUM(CAST(json_each.value AS INTEGER)) as k
            FROM scan_results sr, json_each(json_extract(sr.scan_data, '$[*].kills'))
            WHERE sr.confirmed=1 AND sr.created_at >= ?
        )
    """, (since,))
    try:
        total_kills = cursor.fetchone()[0] or 0
    except Exception:
        total_kills = 0

    # Qeydiyyat sayı
    cursor.execute("SELECT COUNT(*) FROM players WHERE rowid IN (SELECT rowid FROM players ORDER BY rowid DESC LIMIT 1000)")
    player_count = cursor.fetchone()[0]

    conn.close()
    return {
        "days": days,
        "match_count": match_count,
        "top_active": top_active,
        "total_kills": total_kills,
        "player_count": player_count,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ŞƏXSİ REKORDLAR
# ═══════════════════════════════════════════════════════════════════════════════

def update_personal_record(discord_id: int, kills: int, assists: int, deaths: int, match_number: int):
    import time
    kd   = round(kills / max(deaths, 1), 2)
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT best_kills, best_kd FROM personal_records WHERE discord_id=?", (discord_id,))
    row  = cur.fetchone()
    now  = int(time.time())
    if not row:
        cur.execute(
            "INSERT INTO personal_records (discord_id,best_kills,best_assists,best_deaths,best_kd,best_match,updated_at) VALUES (?,?,?,?,?,?,?)",
            (discord_id, kills, assists, deaths, kd, match_number, now)
        )
    else:
        upd = {}
        if kills   > row[0]: upd["best_kills"]   = kills
        if kd      > row[1]: upd["best_kd"]      = kd; upd["best_match"] = match_number
        if assists > 0:       upd["best_assists"] = max(assists, 0)
        if upd:
            sets = ", ".join(f"{k}=?" for k in upd)
            cur.execute(f"UPDATE personal_records SET {sets}, updated_at=? WHERE discord_id=?",
                        list(upd.values()) + [now, discord_id])
    conn.commit(); conn.close()


def get_personal_record(discord_id: int) -> dict:
    conn = _get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT best_kills,best_assists,best_deaths,best_kd,best_match FROM personal_records WHERE discord_id=?",
                (discord_id,))
    row  = cur.fetchone()
    conn.close()
    if not row:
        return {"best_kills": 0, "best_assists": 0, "best_deaths": 0, "best_kd": 0.0, "best_match": None}
    return {"best_kills": row[0], "best_assists": row[1], "best_deaths": row[2],
            "best_kd": row[3], "best_match": row[4]}


# ═══════════════════════════════════════════════════════════════════════════════
# MÜVVƏQƏTİ BAN
# ═══════════════════════════════════════════════════════════════════════════════

def temp_ban(discord_id: int, duration_seconds: int, reason: str, admin_id: int):
    import time
    until = int(time.time()) + duration_seconds
    conn  = _get_conn()
    cur   = conn.cursor()
    cur.execute("UPDATE players SET is_banned=1, banned_until=? WHERE discord_id=?", (until, discord_id))
    conn.commit(); conn.close()
    add_warning(discord_id, f"[TEMP BAN {duration_seconds//3600}s] {reason}", admin_id)
    return until


def check_and_lift_bans():
    import time
    conn = _get_conn()
    cur  = conn.cursor()
    now  = int(time.time())
    cur.execute(
        "UPDATE players SET is_banned=0, banned_until=0 WHERE is_banned=1 AND banned_until > 0 AND banned_until <= ?",
        (now,)
    )
    lifted = cur.rowcount
    conn.commit(); conn.close()
    return lifted


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK GİRİŞ BONUSU
# ═══════════════════════════════════════════════════════════════════════════════

def check_daily_login(discord_id: int) -> tuple:
    """Gündəlik giriş yoxlar. (coins_earned, streak, is_new) qaytarır."""
    import time, datetime as _dt
    conn   = _get_conn()
    cursor = conn.cursor()
    now    = int(time.time())
    today  = _dt.datetime.utcnow().date()

    cursor.execute("SELECT last_login, login_streak FROM daily_logins WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()

    if not row:
        # İlk giriş
        coins = 10
        cursor.execute("INSERT INTO daily_logins (discord_id, last_login, login_streak) VALUES (?,?,1)",
                       (discord_id, now))
        conn.commit(); conn.close()
        return coins, 1, True

    last_ts, streak = row
    last_date = _dt.datetime.utcfromtimestamp(last_ts).date()

    if last_date == today:
        conn.close(); return 0, streak, False  # Bu gün artıq alınıb

    if (today - last_date).days == 1:
        streak += 1   # Ardıcıl
    else:
        streak = 1    # Sıra kəsildi

    # Streak bonusu
    if   streak >= 30: coins = 50
    elif streak >= 14: coins = 35
    elif streak >= 7:  coins = 25
    elif streak >= 3:  coins = 15
    else:              coins = 10

    cursor.execute("UPDATE daily_logins SET last_login=?, login_streak=? WHERE discord_id=?",
                   (now, streak, discord_id))
    conn.commit(); conn.close()
    return coins, streak, True


# ═══════════════════════════════════════════════════════════════════════════════
# MİLESTONE MÜKAFATLARI
# ═══════════════════════════════════════════════════════════════════════════════

MILESTONES = {10: 50, 25: 100, 50: 200, 100: 500, 250: 1000, 500: 2000}

def check_milestones(discord_id: int, total_matches: int) -> list:
    """Keçilmiş milestone-ları tapıb coin verir. [{matches, coins}, ...] qaytarır."""
    conn   = _get_conn()
    cursor = conn.cursor()
    # Artıq verilmiş milestone-ları yoxla (coin_logs-dan)
    cursor.execute(
        "SELECT reason FROM coin_logs WHERE discord_id=? AND reason LIKE 'Milestone:%'",
        (discord_id,)
    )
    already = {r[0] for r in cursor.fetchall()}
    earned  = []
    for ms, reward in MILESTONES.items():
        label = f"Milestone:{ms}"
        if total_matches >= ms and label not in already:
            cursor.execute("UPDATE players SET coins=coins+? WHERE discord_id=?", (reward, discord_id))
            cursor.execute(
                "INSERT INTO coin_logs (discord_id,change,reason,log_type,balance_after,created_at) "
                "SELECT ?,?,?,?,coins,? FROM players WHERE discord_id=?",
                (discord_id, reward, label, "earn", __import__("time").time(), discord_id)
            )
            earned.append({"matches": ms, "coins": reward})
    conn.commit(); conn.close()
    return earned


# ═══════════════════════════════════════════════════════════════════════════════
# ADMİN LOGLARI
# ═══════════════════════════════════════════════════════════════════════════════

def log_admin_action(action, target_id, field, old_val, new_val, reason, admin_id):
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO admin_logs (action,target_id,field,old_val,new_val,reason,admin_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (action, target_id, field, str(old_val), str(new_val), reason, admin_id, int(time.time()))
    )
    conn.commit(); conn.close()


def get_admin_logs(target_id, limit=10):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT action,field,old_val,new_val,reason,admin_id,created_at FROM admin_logs "
        "WHERE target_id=? ORDER BY created_at DESC LIMIT ?",
        (target_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"action": r[0], "field": r[1], "old": r[2], "new": r[3],
             "reason": r[4], "admin_id": r[5], "created_at": r[6]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET ENDİRİM
# ═══════════════════════════════════════════════════════════════════════════════

def set_discount(item_id: str, item_type: str, discount_pct: int, hours: int):
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    now    = int(time.time())
    cursor.execute("DELETE FROM market_discounts WHERE item_id=?", (item_id,))
    cursor.execute(
        "INSERT INTO market_discounts (item_id,item_type,discount,expires_at,created_at) VALUES (?,?,?,?,?)",
        (item_id, item_type, discount_pct, now + hours*3600, now)
    )
    conn.commit(); conn.close()


def get_discount(item_id: str) -> int:
    """Aktiv endirimi qaytarır (%), yoxdursa 0."""
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discount FROM market_discounts WHERE item_id=? AND expires_at > ?",
        (item_id, int(time.time()))
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_all_discounts() -> list:
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT item_id, item_type, discount, expires_at FROM market_discounts WHERE expires_at > ? ORDER BY created_at DESC",
        (int(time.time()),)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"item_id": r[0], "item_type": r[1], "discount": r[2], "expires_at": r[3]} for r in rows]


def clear_expired_discounts():
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM market_discounts WHERE expires_at <= ?", (int(time.time()),))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# BATTLE PASS SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

# Season 1 konfiqurasiyası
BP_SEASON_ID   = 1
BP_PRICE_AZN   = 7
BP_MAX_LEVEL   = 30
BP_XP_PER_LEVEL= 500

BP_LEVEL_REWARDS = {
    1:  {"type": "coins",  "value": 50,   "label": "50 coin"},
    2:  {"type": "coins",  "value": 25,   "label": "25 coin"},
    3:  {"type": "coins",  "value": 25,   "label": "25 coin"},
    4:  {"type": "coins",  "value": 25,   "label": "25 coin"},
    5:  {"type": "coins",  "value": 200,  "label": "200 coin"},
    6:  {"type": "coins",  "value": 50,   "label": "50 coin"},
    7:  {"type": "coins",  "value": 50,   "label": "50 coin"},
    8:  {"type": "coins",  "value": 50,   "label": "50 coin"},
    9:  {"type": "coins",  "value": 50,   "label": "50 coin"},
    10: {"type": "banner", "value": "bp1_banner", "label": "S1 Banner"},
    11: {"type": "coins",  "value": 75,   "label": "75 coin"},
    12: {"type": "coins",  "value": 75,   "label": "75 coin"},
    13: {"type": "coins",  "value": 75,   "label": "75 coin"},
    14: {"type": "coins",  "value": 75,   "label": "75 coin"},
    15: {"type": "boost",  "value": "boost_50_1d", "label": "50% ELO Boost"},
    16: {"type": "coins",  "value": 100,  "label": "100 coin"},
    17: {"type": "coins",  "value": 100,  "label": "100 coin"},
    18: {"type": "coins",  "value": 100,  "label": "100 coin"},
    19: {"type": "coins",  "value": 100,  "label": "100 coin"},
    20: {"type": "frame",  "value": "bp1_frame",  "label": "S1 Frame"},
    21: {"type": "coins",  "value": 150,  "label": "150 coin"},
    22: {"type": "coins",  "value": 150,  "label": "150 coin"},
    23: {"type": "coins",  "value": 150,  "label": "150 coin"},
    24: {"type": "coins",  "value": 150,  "label": "150 coin"},
    25: {"type": "coins",  "value": 1000, "label": "1000 coin"},
    26: {"type": "coins",  "value": 200,  "label": "200 coin"},
    27: {"type": "coins",  "value": 200,  "label": "200 coin"},
    28: {"type": "coins",  "value": 200,  "label": "200 coin"},
    29: {"type": "coins",  "value": 200,  "label": "200 coin"},
    30: {"type": "skin",   "value": "AWM | Boom", "label": "AWM | Boom SKIN"},
}

BP_MISSIONS_SEED = [
    # (id, type, target, xp, description, mission_type)
    # Daily
    (1,  "kills",   5,  150, "5 kill et",               "daily"),
    (2,  "matches", 1,  100, "1 matc oyna",              "daily"),
    (3,  "mvp",     1,  200, "MVP ol",                   "daily"),
    # Weekly
    (4,  "kills",   20, 500, "20 kill et",               "weekly"),
    (5,  "wins",    3,  600, "3 qelebeni qazan",         "weekly"),
    (6,  "assists", 10, 400, "10 asist et",              "weekly"),
    # Seasonal
    (7,  "matches", 10, 1000,"10 matc oyna",             "seasonal"),
    (8,  "kills",   50, 1500,"50 kill et",               "seasonal"),
    (9,  "mvp",     5,  2000,"5 defe MVP ol",            "seasonal"),
    (10, "wins",    15, 2500,"15 qelebeni qazan",        "seasonal"),
]


def init_battle_pass(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battle_pass (
            discord_id   INTEGER NOT NULL,
            season_id    INTEGER NOT NULL,
            level        INTEGER DEFAULT 0,
            xp           INTEGER DEFAULT 0,
            purchased_at INTEGER NOT NULL,
            claimed_levels TEXT DEFAULT '[]',
            is_premium   INTEGER DEFAULT 0,
            PRIMARY KEY (discord_id, season_id)
        )
    """)
    # Migration: köhnə cədvəllərdə is_premium olmaya bilər
    cursor.execute("PRAGMA table_info(battle_pass)")
    bp_cols = [r[1] for r in cursor.fetchall()]
    if "is_premium" not in bp_cols:
        cursor.execute("ALTER TABLE battle_pass ADD COLUMN is_premium INTEGER DEFAULT 0")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bp_missions (
            id           INTEGER PRIMARY KEY,
            season_id    INTEGER NOT NULL,
            type         TEXT NOT NULL,
            target       INTEGER NOT NULL,
            xp_reward    INTEGER NOT NULL,
            description  TEXT NOT NULL,
            mission_type TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_bp_missions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id  INTEGER NOT NULL,
            mission_id  INTEGER NOT NULL,
            season_id   INTEGER NOT NULL,
            progress    INTEGER DEFAULT 0,
            completed   INTEGER DEFAULT 0,
            assigned_at INTEGER NOT NULL,
            UNIQUE(discord_id, mission_id, season_id)
        )
    """)
    # Seed missions
    for mid, mtype, target, xp, desc, mcat in BP_MISSIONS_SEED:
        cursor.execute(
            "INSERT OR IGNORE INTO bp_missions (id,season_id,type,target,xp_reward,description,mission_type) VALUES (?,?,?,?,?,?,?)",
            (mid, BP_SEASON_ID, mtype, target, xp, desc, mcat)
        )


def ensure_free_pass(discord_id: int):
    """Hər oyunçu üçün FREE pass avtomatik yaradılır."""
    import time, json
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT OR IGNORE INTO battle_pass (discord_id,season_id,level,xp,purchased_at,claimed_levels,is_premium) VALUES (?,?,0,0,?,?,0)",
            (discord_id, BP_SEASON_ID, int(time.time()), json.dumps([]))
        )
        conn.commit()
    conn.close()


def buy_battle_pass(discord_id: int) -> tuple:
    """Premium pass alır. (success, msg) qaytarır."""
    import time, json
    ensure_free_pass(discord_id)
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT zm_balance FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] < BP_PRICE_AZN:
        conn.close(); return False, f"Kifayet qeder AZN yoxdur. Lazim: {BP_PRICE_AZN} AZN"
    cursor.execute("SELECT is_premium FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    pr = cursor.fetchone()
    if pr and pr[0] == 1:
        conn.close(); return False, "Artiq Premium Pass sahibisiniz!"
    cursor.execute("UPDATE players SET zm_balance=zm_balance-? WHERE discord_id=?",
                   (BP_PRICE_AZN, discord_id))
    cursor.execute("UPDATE battle_pass SET is_premium=1 WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    conn.commit(); conn.close()
    return True, "Premium Pass ugurla alindi!"


def has_battle_pass(discord_id: int) -> bool:
    """Free və ya premium pass var?"""
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    ok = cursor.fetchone() is not None
    conn.close(); return ok


def is_premium_pass(discord_id: int) -> bool:
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_premium FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0])


def get_pass_data(discord_id: int) -> dict:
    import json
    ensure_free_pass(discord_id)
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT level,xp,claimed_levels,is_premium FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"level": 0, "xp": 0, "claimed": [], "is_premium": False}
    return {"level": row[0], "xp": row[1], "claimed": json.loads(row[2] or "[]"),
            "is_premium": bool(row[3])}


def add_bp_xp(discord_id: int, xp: int) -> dict:
    """XP əlavə edir. Hər oyunçu üçün işləyir (free + premium)."""
    import json
    ensure_free_pass(discord_id)  # Free pass avtomatik yaradılır
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT level,xp,claimed_levels FROM battle_pass WHERE discord_id=? AND season_id=?",
                   (discord_id, BP_SEASON_ID))
    row = cursor.fetchone()
    if not row:
        conn.close(); return {}

    level, cur_xp, claimed_json = row
    claimed = json.loads(claimed_json or "[]")
    cur_xp += xp
    new_rewards = []

    # Level up
    while level < BP_MAX_LEVEL and cur_xp >= BP_XP_PER_LEVEL:
        cur_xp -= BP_XP_PER_LEVEL
        level  += 1
        if level not in claimed:
            reward = BP_LEVEL_REWARDS.get(level)
            if reward:
                new_rewards.append({"level": level, **reward})
                # Coini ver
                if reward["type"] == "coins":
                    cursor.execute("UPDATE players SET coins=coins+? WHERE discord_id=?",
                                   (reward["value"], discord_id))
            claimed.append(level)

    cursor.execute("UPDATE battle_pass SET level=?,xp=?,claimed_levels=? WHERE discord_id=? AND season_id=?",
                   (level, cur_xp, json.dumps(claimed), discord_id, BP_SEASON_ID))
    conn.commit(); conn.close()
    return {"new_level": level, "new_xp": cur_xp, "rewards": new_rewards}


def get_active_bp_missions(discord_id: int) -> list:
    import time, json
    conn   = _get_conn()
    cursor = conn.cursor()
    now    = int(time.time())
    today  = now - (now % 86400)

    # Günlük missiyaları assign et
    cursor.execute(
        "SELECT COUNT(*) FROM player_bp_missions WHERE discord_id=? AND season_id=? AND completed=0 "
        "AND assigned_at >= ? AND mission_id IN (SELECT id FROM bp_missions WHERE mission_type='daily')",
        (discord_id, BP_SEASON_ID, today)
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "SELECT id FROM bp_missions WHERE season_id=? AND mission_type='daily' ORDER BY RANDOM() LIMIT 3",
            (BP_SEASON_ID,)
        )
        for (mid,) in cursor.fetchall():
            cursor.execute(
                "INSERT OR IGNORE INTO player_bp_missions (discord_id,mission_id,season_id,assigned_at) VALUES (?,?,?,?)",
                (discord_id, mid, BP_SEASON_ID, now)
            )
        conn.commit()

    # Sezonluq missiyaları da assign et
    cursor.execute(
        "SELECT id FROM bp_missions WHERE season_id=? AND mission_type='seasonal'",
        (BP_SEASON_ID,)
    )
    for (mid,) in cursor.fetchall():
        cursor.execute(
            "INSERT OR IGNORE INTO player_bp_missions (discord_id,mission_id,season_id,assigned_at) VALUES (?,?,?,?)",
            (discord_id, mid, BP_SEASON_ID, now)
        )
    conn.commit()

    # Aktiv missiyaları qaytar
    cursor.execute("""
        SELECT pm.id, bm.description, bm.type, bm.target, bm.xp_reward, bm.mission_type,
               pm.progress, pm.completed
        FROM player_bp_missions pm
        JOIN bp_missions bm ON bm.id=pm.mission_id
        WHERE pm.discord_id=? AND pm.season_id=?
        ORDER BY pm.completed ASC, bm.mission_type DESC
        LIMIT 8
    """, (discord_id, BP_SEASON_ID))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "desc": r[1], "type": r[2], "target": r[3], "xp": r[4],
             "cat": r[5], "progress": r[6], "completed": bool(r[7])} for r in rows]


def update_bp_mission(discord_id: int, mission_type: str, amount: int = 1) -> int:
    """Missiya tipinə görə progressi yenilər. Qazanılan XP-ni qaytarır."""
    if not has_battle_pass(discord_id):
        return 0
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pm.id, bm.target, bm.xp_reward, pm.progress
        FROM player_bp_missions pm
        JOIN bp_missions bm ON bm.id=pm.mission_id
        WHERE pm.discord_id=? AND pm.season_id=? AND bm.type=? AND pm.completed=0
    """, (discord_id, BP_SEASON_ID, mission_type))
    rows   = cursor.fetchall()
    total_xp = 0
    for pm_id, target, xp_reward, progress in rows:
        new_prog = min(progress + amount, target)
        completed = 1 if new_prog >= target else 0
        cursor.execute("UPDATE player_bp_missions SET progress=?,completed=? WHERE id=?",
                       (new_prog, completed, pm_id))
        if completed and progress < target:
            total_xp += xp_reward
    conn.commit(); conn.close()
    return total_xp


# ═══════════════════════════════════════════════════════════════════════════════
# FƏALİYYƏT — SAATLAR
# ═══════════════════════════════════════════════════════════════════════════════

def get_hourly_activity(days=7) -> dict:
    """Saat üzrə matç paylanması {hour: count}."""
    import time as _t, datetime as _dt
    since  = int(_t.time()) - days * 86400
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT played_at FROM match_history WHERE played_at >= ?", (since,))
    rows   = cursor.fetchall()
    conn.close()
    counts = {}
    for (ts,) in rows:
        h = (_dt.datetime.utcfromtimestamp(ts) + _dt.timedelta(hours=4)).hour
        counts[h] = counts.get(h, 0) + 1
    return counts


def fail_expired_tasks():
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE player_tasks SET failed=1 WHERE completed=0 AND failed=0 AND expires_at <= ?",
                   (int(time.time()),))
    conn.commit()
    conn.close()


def full_reset():
    """Bazadakı hər şeyi silir. Hamı yenidən qeydiyyatdan keçməlidir."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Bütün cədvəlləri sil
    for table in ("players", "match_history", "season_stats", "seasons",
                  "scan_results", "player_tasks", "daily_tasks",
                  "coin_logs", "active_boosts", "chat_history",
                  "inventory", "skin_inventory", "skins", "giveaways",
                  "warnings", "player_achievements", "match_predictions"):
        cursor.execute(f"DELETE FROM {table}")

    # Matç sayacını sıfırla
    cursor.execute("UPDATE match_counter SET last_number = 0 WHERE id = 1")

    # Aktiv matçı sıfırla (yalnız mövcud sütunları yenilə)
    cursor.execute("PRAGMA table_info(active_match)")
    am_cols = {r[1] for r in cursor.fetchall()}
    extra = ", ".join(f"{c}=NULL" for c in
                      ("team_a","team_b","log_message_id","log_channel_id","selected_map")
                      if c in am_cols)
    sql = "UPDATE active_match SET match_number=NULL, status=NULL"
    if extra:
        sql += ", " + extra
    sql += " WHERE id=1"
    cursor.execute(sql)

    conn.commit()
    conn.close()


def get_lang(discord_id: int) -> str:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("SELECT lang FROM players WHERE discord_id=?", (discord_id,))
    row = cur.fetchone(); conn.close()
    return (row[0] or 'az') if row else 'az'


def set_lang(discord_id: int, lang: str):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE players SET lang=? WHERE discord_id=?", (lang, discord_id))
    conn.commit(); conn.close()


def claim_bp_rewards(discord_id: int, levels_to_claim: list) -> dict:
    """
    Seçilmiş levellərin mükafatlarını tələb edir.
    Yalnız oyunçunun çatdığı levelə qədər, hələ tələb edilməmiş levelləri işlər.
    Qaytarır: {claimed: [level,...], coins_earned: int, items_earned: [...]}
    """
    import json
    pd = get_pass_data(discord_id)
    max_level   = pd["level"]
    already     = set(pd["claimed"])
    is_premium  = pd["is_premium"]

    newly_claimed = []
    coins_earned  = 0
    items_earned  = []

    for lv in levels_to_claim:
        if lv > max_level or lv in already:
            continue
        # FREE mükafat
        free_r = BP_LEVEL_REWARDS.get(lv, {}).get("free")
        if free_r:
            if free_r.get("type") == "coins":
                coins_earned += free_r.get("amount", 0)
            else:
                items_earned.append({"level": lv, "track": "free", "label": free_r.get("label","")})
        # PREMIUM mükafat (yalnız premium oyunçulara)
        if is_premium:
            prem_r = BP_LEVEL_REWARDS.get(lv, {}).get("premium")
            if prem_r:
                if prem_r.get("type") == "coins":
                    coins_earned += prem_r.get("amount", 0)
                else:
                    items_earned.append({"level": lv, "track": "premium", "label": prem_r.get("label","")})
        newly_claimed.append(lv)

    if not newly_claimed:
        return {"claimed": [], "coins_earned": 0, "items_earned": []}

    # DB yenilə
    new_claimed = list(already | set(newly_claimed))
    conn = _get_conn(); cur = conn.cursor()
    if coins_earned > 0:
        cur.execute("UPDATE players SET coins=coins+? WHERE discord_id=?", (coins_earned, discord_id))
    cur.execute("UPDATE battle_pass SET claimed_levels=? WHERE discord_id=? AND season_id=?",
                (json.dumps(new_claimed), discord_id, BP_SEASON_ID))
    conn.commit(); conn.close()

    return {"claimed": newly_claimed, "coins_earned": coins_earned, "items_earned": items_earned}


def get_unclaimed_bp_levels(discord_id: int) -> list:
    """Oyunçunun çatdığı amma hələ tələb etmədiyi levelləri qaytarır."""
    pd = get_pass_data(discord_id)
    claimed = set(pd["claimed"])
    return [lv for lv in range(1, pd["level"] + 1) if lv not in claimed]
