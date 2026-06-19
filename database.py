import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "."), "bot_database.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
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

    # ===== STANDOFF MARKET / SKIN cədvəlləri =====
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

    conn.commit()
    conn.close()


def get_next_match_number():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE match_counter SET last_number = last_number + 1 WHERE id = 1")
    cursor.execute("SELECT last_number FROM match_counter WHERE id = 1")
    number = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return number

def register_player(discord_id, so2_nick, so2_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_team_elo(winner_ids, loser_ids):
    """
    winner_ids, loser_ids: discord_id siyahıları (hər komandada bir neçə oyunçu)
    Komandanın orta ELO-suna görə hesablanır, hər oyunçu fərdi yenilənir.
    """
    conn = sqlite3.connect(DB_PATH)
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
        new_elo = elo + elo_change_winner
        cursor.execute(
            "UPDATE players SET elo = ?, wins = ? WHERE discord_id = ?",
            (new_elo, wins + 1, discord_id)
        )
        results["winners"].append({"discord_id": discord_id, "nick": nick, "old_elo": elo, "new_elo": new_elo})

    for discord_id, nick, elo, wins, losses in losers:
        new_elo = elo + elo_change_loser
        cursor.execute(
            "UPDATE players SET elo = ?, losses = ? WHERE discord_id = ?",
            (new_elo, losses + 1, discord_id)
        )
        results["losers"].append({"discord_id": discord_id, "nick": nick, "old_elo": elo, "new_elo": new_elo})

    conn.commit()
    conn.close()
    return results


def update_elo(winner_id, loser_id):
    conn = sqlite3.connect(DB_PATH)
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

    new_winner_elo = round(winner_elo + K * (1 - expected_winner))
    new_loser_elo = round(loser_elo + K * (0 - expected_loser))

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

def get_leaderboard(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT so2_nick, so2_id, elo, wins, losses FROM players ORDER BY elo DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


queue_list = []  # Yaddaşda saxlanılan müvəqqəti növbə

def add_to_queue(discord_id, nick, elo):
    for p in queue_list:
        if p["discord_id"] == discord_id:
            return False
    queue_list.append({"discord_id": discord_id, "nick": nick, "elo": elo})
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, mukafat, winner_id, channel_id, message_id FROM giveaways WHERE finished = 0 AND end_unix <= ?",
        (current_unix,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_giveaway_finished(giveaway_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE giveaways SET finished = 1 WHERE id = ?", (giveaway_id,))
    conn.commit()
    conn.close()


def add_coins(discord_id, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET coins = coins + ? WHERE discord_id = ?", (amount, discord_id))
    conn.commit()
    cursor.execute("SELECT coins FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_coins(discord_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def spend_coins(discord_id, amount):
    """Balans kifayətdirsə coin çıxır və True qaytarır, yoxdursa False qaytarır."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM inventory WHERE discord_id = ?", (discord_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def owns_item(discord_id, item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM inventory WHERE discord_id = ? AND item_id = ?", (discord_id, item_id))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def add_to_inventory(discord_id, item_id):
    import time
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET active_banner = ? WHERE discord_id = ?", (item_id, discord_id))
    conn.commit()
    conn.close()


def get_active_banner(discord_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT active_banner FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def record_match_history(match_type, winner_ids, loser_ids, winner_elo_before, winner_elo_after,
                          loser_elo_before, loser_elo_after, match_number=None):
    """
    match_type: "1v1" veya "5v5"
    winner_ids, loser_ids: discord_id siyahısı (1v1 üçün tək elementli)
    winner_elo_before/after, loser_elo_before/after: hər oyunçunun ELO-su, ids ilə eyni sırada
    """
    import json as _json
    import time as _time
    conn = sqlite3.connect(DB_PATH)
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
    """Verilmiş oyunçunun iştirak etdiyi son matçları qaytarır (ən yenidən köhnəyə)."""
    import json as _json
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM match_history")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def admin_set_player_field(discord_id, field, value):
    """
    Admin panel üçün: bir oyunçunun tək bir sahəsini dəyişir.
    field: 'so2_nick', 'so2_id', 'elo', 'coins', 'wins', 'losses'
    """
    allowed_fields = {"so2_nick", "so2_id", "elo", "coins", "wins", "losses"}
    if field not in allowed_fields:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()
    conn.close()
    return True


# ==================== STANDOFF MARKET / SKIN SISTEMI ====================

def add_skin(name, price, image_url=None):
    """Mağazaya yeni skin əlavə edir. Yaradılan skin id-sini qaytarır."""
    import time
    conn = sqlite3.connect(DB_PATH)
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
    """Mağazada satışda olan (active=1) skinləri qaytarır."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url FROM skins WHERE active = 1 ORDER BY price ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "price": r[2], "image_url": r[3]} for r in rows]


def get_skin_by_id(skin_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_url, active FROM skins WHERE id = ?", (skin_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "price": row[2], "image_url": row[3], "active": row[4]}


def remove_skin(skin_id):
    """Skini mağazadan götürür (active=0). Tarixçə üçün silmir, deaktiv edir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE skins SET active = 0 WHERE id = ?", (skin_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def add_skin_to_inventory(discord_id, skin_id, skin_name, price_paid, image_url=None):
    """Alınan skini oyunçunun skin envanterinə əlavə edir (hər alış ayrı sətir)."""
    import time
    conn = sqlite3.connect(DB_PATH)
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
    """Oyunçunun skin envanterini qaytarır. only_undelivered=True olsa yalnız təhvil verilməyənləri."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    """Admin manuel olaraq oyunçunun envanterindən bir skini silir (oyunda təhvil verildikdə)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skin_inventory WHERE id = ?", (inv_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def add_coin_log(discord_id, change, reason, log_type, balance_after=None):
    """
    Coin hərəkətini loga yazır.
    change: müsbət (qazanma) və ya mənfi (xərcləmə) say
    reason: izah mətni (məs: "Skin alışı: AK-47 Redline")
    log_type: "earn" və ya "spend"
    """
    import time
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coin_logs (discord_id, change, reason, log_type, balance_after, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (discord_id, change, reason, log_type, balance_after, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_coin_logs(discord_id, log_type=None, limit=15):
    """
    Oyunçunun coin loglarını qaytarır (ən yenidən köhnəyə).
    log_type: None (hamısı), "earn" (qazanma), "spend" (xərcləmə)
    """
    conn = sqlite3.connect(DB_PATH)
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
