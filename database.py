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
    if "active_theme" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN active_theme TEXT DEFAULT NULL")
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
    if "created_at" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN created_at INTEGER DEFAULT NULL")
    if "last_match_at" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN last_match_at INTEGER DEFAULT NULL")
    if "active_title_id" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN active_title_id TEXT DEFAULT NULL")
    if "boost50_cards" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN boost50_cards INTEGER DEFAULT 0")
    if "boost100_cards" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN boost100_cards INTEGER DEFAULT 0")
    if "protect_cards" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN protect_cards INTEGER DEFAULT 0")
    if "dm_notifications" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN dm_notifications INTEGER DEFAULT 1")
    if "last_comeback_bonus_at" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN last_comeback_bonus_at INTEGER DEFAULT 0")
    if "loss_streak" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN loss_streak INTEGER DEFAULT 0")
    if "nick_change_used" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN nick_change_used INTEGER DEFAULT 0")
    if "target_elo" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN target_elo INTEGER DEFAULT NULL")
    if "birthday_month" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN birthday_month INTEGER DEFAULT NULL")
    if "birthday_day" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN birthday_day INTEGER DEFAULT NULL")
    if "last_birthday_announced_year" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN last_birthday_announced_year INTEGER DEFAULT NULL")
    if "task_streak" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN task_streak INTEGER DEFAULT 0")
    if "last_perfect_task_day" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN last_perfect_task_day TEXT DEFAULT NULL")
    if "last_profile_surprise_day" not in existing_columns:
        cursor.execute("ALTER TABLE players ADD COLUMN last_profile_surprise_day TEXT DEFAULT NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            send_at INTEGER NOT NULL,
            created_by INTEGER,
            sent INTEGER DEFAULT 0
        )
    """)

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

    # ── Bot Meta (kiçik key-value saxlama, restart-lar arası) ───────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # ── İcma Hədəfləri (aylıq) ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_goals (
            month_key    TEXT PRIMARY KEY,
            target       INTEGER NOT NULL,
            reward_coins INTEGER NOT NULL,
            rewarded     INTEGER DEFAULT 0
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

    # ── Silinmiş qeydiyyat arxivi (bax: archive_and_delete_player) — avtomatik təmizləmə
    # "qeydiyyatlar səbəbsiz silinir" insidentindən sonra bərpa imkanı üçün əlavə edildi.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deleted_players_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            so2_nick TEXT,
            so2_id TEXT,
            coins INTEGER,
            zm_balance INTEGER,
            deleted_at INTEGER NOT NULL,
            deleted_reason TEXT
        )
    """)

    # ── İki-mərhələli avtomatik təmizləmə (bax: process_pending_cleanup) — namizəd bir
    # oyunçu İLK dəfə görünəndə dərhal silinmir, yalnız ƏN AZ 24 saat sonra HƏLƏ DƏ
    # namizəddirsə həqiqətən silinir.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_player_cleanup (
            discord_id INTEGER PRIMARY KEY,
            flagged_at INTEGER NOT NULL
        )
    """)

    # ── Mağaza (store_catalog_seed.json-dan toplu doldurulur — bax: seed_store_catalog) ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            is_digital INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL,
            code TEXT,
            name TEXT NOT NULL,
            price_azn REAL NOT NULL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            image_path TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(store_products)")
    if "image_path" not in [r[1] for r in cursor.fetchall()]:
        cursor.execute("ALTER TABLE store_products ADD COLUMN image_path TEXT")

    # ── Mystery Box (sayt, Discord login ilə) — bax: open_mystery_box ──────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS box_openings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            nick TEXT,
            item_key TEXT NOT NULL,
            item_label TEXT NOT NULL,
            opened_at INTEGER NOT NULL
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

    # ── Quest zəncirləri ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quest_chains (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            steps TEXT NOT NULL,
            reward_coins INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_quest_progress (
            discord_id INTEGER NOT NULL,
            chain_id TEXT NOT NULL,
            current_step INTEGER DEFAULT 0,
            step_progress INTEGER DEFAULT 0,
            completed_at INTEGER DEFAULT NULL,
            PRIMARY KEY (discord_id, chain_id)
        )
    """)

    # ── Günün Ortaq Çağırışı ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_challenges (
            date_key TEXT PRIMARY KEY,
            challenge_type TEXT NOT NULL,
            target INTEGER NOT NULL,
            reward_coins INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_challenge_claims (
            date_key TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            PRIMARY KEY (date_key, discord_id)
        )
    """)

    # ── Fərdi ləqəblər (Custom Titles) ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS titles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            title_id TEXT NOT NULL,
            earned_at INTEGER NOT NULL,
            UNIQUE(discord_id, title_id)
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

    # ── Seasons ──────────────────────────────────────────────────────────────
    # 5v5 dəstəyi üçün `mode` sütunu əlavə olunur — season_number artıq mode-a görə
    # AYRI say qatarı olduğundan UNIQUE constraint (season_number, mode) cütünə keçir.
    # SQLite constraint dəyişikliyini ALTER TABLE ilə etmədiyi üçün cədvəl köçürülür,
    # `id` dəyərləri (season_stats.season_id istinadları) TOXUNULMADAN saxlanılır.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_number INTEGER UNIQUE NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)
    cursor.execute("PRAGMA table_info(seasons)")
    if "mode" not in [r[1] for r in cursor.fetchall()]:
        cursor.execute("ALTER TABLE seasons RENAME TO seasons_old")
        cursor.execute("""
            CREATE TABLE seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_number INTEGER NOT NULL,
                mode TEXT NOT NULL DEFAULT '2v2',
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                UNIQUE(season_number, mode)
            )
        """)
        cursor.execute("""
            INSERT INTO seasons (id, season_number, mode, start_date, end_date, status)
            SELECT id, season_number, '2v2', start_date, end_date, status FROM seasons_old
        """)
        cursor.execute("DROP TABLE seasons_old")

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
    cursor.execute("PRAGMA table_info(season_stats)")
    if "mode" not in [r[1] for r in cursor.fetchall()]:
        cursor.execute("ALTER TABLE season_stats ADD COLUMN mode TEXT NOT NULL DEFAULT '2v2'")

    # ── 5v5 paralel sistemi — ayrıca rəqabət statistikası cədvəli ─────────────
    # Kimlik/iqtisadiyyat (nick, so2_id, coins, inventory, achievements, battle pass)
    # `players`-də PAYLAŞILMIŞ qalır — yalnız ELO/W-L/K-A-D/streak ayrılır.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players_5v5 (
            discord_id INTEGER PRIMARY KEY,
            elo INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            kills INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            win_streak INTEGER DEFAULT 0,
            loss_streak INTEGER DEFAULT 0,
            peak_elo INTEGER DEFAULT 1000,
            max_streak INTEGER DEFAULT 0,
            created_at INTEGER
        )
    """)
    cursor.execute("PRAGMA table_info(players_5v5)")
    _p5v5_cols = [r[1] for r in cursor.fetchall()]
    if "last_match_at" not in _p5v5_cols:
        cursor.execute("ALTER TABLE players_5v5 ADD COLUMN last_match_at INTEGER DEFAULT NULL")
    if "last_decay_at" not in _p5v5_cols:
        cursor.execute("ALTER TABLE players_5v5 ADD COLUMN last_decay_at INTEGER DEFAULT NULL")
    if "decay_warning_sent_at" not in _p5v5_cols:
        cursor.execute("ALTER TABLE players_5v5 ADD COLUMN decay_warning_sent_at INTEGER DEFAULT NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchmaking_queue_5v5 (
            discord_id INTEGER PRIMARY KEY,
            nick TEXT NOT NULL,
            so2_id TEXT,
            elo INTEGER NOT NULL,
            joined_at INTEGER NOT NULL
        )
    """)

    # ── Active match lock ─────────────────────────────────────────────────────
    # Köhnə tək-sətirlik "active_match" sxemi (id sütunu ilə) aşkarlanarsa,
    # paralel-matç dəstəyi üçün çox-sətirli sxemə keçid (transient state,
    # tarixi data itkisi yoxdur — yalnız o an "gözləmədə" olan matçın
    # vəziyyəti sıfırlanır). Cədvəl heç olmayıbsa bu yoxlama sadəcə keçilir.
    cursor.execute("PRAGMA table_info(active_match)")
    if "id" in [r[1] for r in cursor.fetchall()]:
        cursor.execute("DROP TABLE active_match")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_match (
            match_number   INTEGER PRIMARY KEY,
            team_a         TEXT,
            team_b         TEXT,
            log_message_id TEXT,
            log_channel_id TEXT,
            thread_id      TEXT,
            selected_map   TEXT,
            created_at     INTEGER,
            captain_a_id   INTEGER,
            captain_b_id   INTEGER,
            team_a_ready   INTEGER DEFAULT 0,
            team_b_ready   INTEGER DEFAULT 0,
            is_golden      INTEGER DEFAULT 0,
            is_lightning   INTEGER DEFAULT 0,
            voice_a_id     TEXT,
            voice_b_id     TEXT,
            map_vetoed     TEXT DEFAULT '[]',
            veto_a_used    INTEGER DEFAULT 0,
            veto_b_used    INTEGER DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(active_match)")
    _am_cols = [r[1] for r in cursor.fetchall()]
    if "map_vetoed" not in _am_cols:
        cursor.execute("ALTER TABLE active_match ADD COLUMN map_vetoed TEXT DEFAULT '[]'")
    if "veto_a_used" not in _am_cols:
        cursor.execute("ALTER TABLE active_match ADD COLUMN veto_a_used INTEGER DEFAULT 0")
    if "veto_b_used" not in _am_cols:
        cursor.execute("ALTER TABLE active_match ADD COLUMN veto_b_used INTEGER DEFAULT 0")
    if "mode" not in _am_cols:
        cursor.execute("ALTER TABLE active_match ADD COLUMN mode TEXT NOT NULL DEFAULT '2v2'")

    # ── Ümumi söhbət XP / aktivlik ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_activity (
            discord_id  INTEGER PRIMARY KEY,
            weekly_xp   INTEGER DEFAULT 0,
            total_xp    INTEGER DEFAULT 0,
            last_xp_at  INTEGER DEFAULT 0
        )
    """)

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
        CREATE TABLE IF NOT EXISTS matchmaking_queue (
            discord_id INTEGER PRIMARY KEY,
            nick TEXT NOT NULL,
            so2_id TEXT,
            elo INTEGER NOT NULL,
            joined_at INTEGER NOT NULL
        )
    """)
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
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            channel_id INTEGER,
            ticket_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at INTEGER,
            closed_at INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS duo_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            member_id INTEGER,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            reminder_7d INTEGER DEFAULT 0,
            reminder_3d INTEGER DEFAULT 0,
            reminder_1d INTEGER DEFAULT 0,
            reminder_1h INTEGER DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(duo_teams)")
    if "channel_id" not in [r[1] for r in cursor.fetchall()]:
        cursor.execute("ALTER TABLE duo_teams ADD COLUMN channel_id INTEGER DEFAULT NULL")

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
    cursor.execute("PRAGMA table_info(match_history)")
    _match_history_cols = [r[1] for r in cursor.fetchall()]
    if "map" not in _match_history_cols:
        cursor.execute("ALTER TABLE match_history ADD COLUMN map TEXT DEFAULT NULL")
    for _col in ("winner_kills", "winner_assists", "winner_deaths", "loser_kills", "loser_assists", "loser_deaths"):
        if _col not in _match_history_cols:
            cursor.execute(f"ALTER TABLE match_history ADD COLUMN {_col} TEXT DEFAULT NULL")
    if "season_id" not in _match_history_cols:
        cursor.execute("ALTER TABLE match_history ADD COLUMN season_id INTEGER DEFAULT NULL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_claims (
            discord_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_claim_at INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_task_progress (
            discord_id INTEGER NOT NULL,
            date_key TEXT NOT NULL,
            play_progress INTEGER DEFAULT 0,
            win_progress INTEGER DEFAULT 0,
            kill_progress INTEGER DEFAULT 0,
            claimed_play INTEGER DEFAULT 0,
            claimed_win INTEGER DEFAULT 0,
            claimed_kill INTEGER DEFAULT 0,
            PRIMARY KEY (discord_id, date_key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_capsule_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            unlock_at INTEGER NOT NULL,
            opened INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anniversary_greetings (
            discord_id INTEGER NOT NULL,
            year_number INTEGER NOT NULL,
            greeted_at INTEGER NOT NULL,
            UNIQUE(discord_id, year_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teammate_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rater_id INTEGER NOT NULL,
            rated_id INTEGER NOT NULL,
            match_number INTEGER NOT NULL,
            stars INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            UNIQUE(rater_id, rated_id, match_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS squads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            wins_together INTEGER DEFAULT 0
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

    # ── Hərraclar (Auction House) ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            starting_bid INTEGER NOT NULL,
            current_bid INTEGER NOT NULL,
            current_bidder_id INTEGER,
            end_unix INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            finished INTEGER DEFAULT 0
        )
    """)

    # ── Battle Pass Sezon Arxivi ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bp_season_archive (
            season_name TEXT PRIMARY KEY,
            archived_at INTEGER NOT NULL,
            top_players TEXT NOT NULL,
            total_participants INTEGER NOT NULL
        )
    """)

    # ── Səs kanalı fəallığı (Ən Sosial reytinqi) ───────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_time (
            discord_id    INTEGER PRIMARY KEY,
            total_seconds INTEGER DEFAULT 0
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

RESETTABLE_PLAYER_TABLES = [
    "players", "daily_logins", "personal_records", "elo_history", "warnings",
    "player_achievements", "player_quest_progress", "daily_challenge_claims",
    "player_titles", "match_predictions", "season_stats", "scan_results",
    "player_tasks", "chat_history", "inventory", "match_history", "squads",
    "skin_inventory", "coin_logs", "active_boosts",
    "referral_invites", "referrals", "active_match",
    "players_5v5", "matchmaking_queue_5v5", "matchmaking_queue", "chat_activity",
    "seasons",
]


def reset_all_player_data():
    """DİQQƏT: geri qaytarıla bilməz. Bütün qeydiyyatlı oyunçuları, matç tarixçəsini,
    coin/AZN balanslarını, nailiyyətləri, inventarı (banner/skin/ELO kartları daxil) və
    mükafat tarixçəsini həmişəlik silir, matç nömrələnməsini sıfırlayır. Kataloq/konfiqurasiya
    cədvəlləri (achievements/quest_chains/titles/skins tərifləri, bot_meta, admin_logs,
    giveaways, daily_tasks kataloqu) TOXUNULMAZ qalır."""
    conn = _get_conn()
    cursor = conn.cursor()
    for table in RESETTABLE_PLAYER_TABLES:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError:
            pass
    cursor.execute("UPDATE match_counter SET last_number = 0 WHERE id = 1")
    conn.commit()
    conn.close()


def register_player(discord_id, so2_nick, so2_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO players (discord_id, so2_nick, so2_id, created_at) VALUES (?, ?, ?, ?)",
        (discord_id, so2_nick, so2_id, int(time.time()))
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


def set_target_elo(discord_id, target_elo):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET target_elo = ? WHERE discord_id = ?", (target_elo, discord_id))
    conn.commit()
    conn.close()


def get_target_elo(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT target_elo FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_birthday(discord_id, month, day):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE players SET birthday_month = ?, birthday_day = ? WHERE discord_id = ?",
        (month, day, discord_id)
    )
    conn.commit()
    conn.close()


def get_birthday(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT birthday_month, birthday_day FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or row[0] is None:
        return None
    return {"month": row[0], "day": row[1]}


def get_todays_birthday_players(month, day, year):
    """Doğum günü bu gün olan VƏ bu il hələ təbrik edilməmiş oyunçuları qaytarır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, so2_nick FROM players WHERE birthday_month=? AND birthday_day=? "
        "AND (last_birthday_announced_year IS NULL OR last_birthday_announced_year != ?)",
        (month, day, year)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "nick": r[1]} for r in rows]


def mark_birthday_announced(discord_id, year):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET last_birthday_announced_year = ? WHERE discord_id = ?", (year, discord_id))
    conn.commit()
    conn.close()


def set_profile_theme(discord_id, theme_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET active_theme = ? WHERE discord_id = ?", (theme_id, discord_id))
    conn.commit()
    conn.close()


def get_profile_theme(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT active_theme FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def create_scheduled_announcement(channel_id, content, send_at, created_by):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scheduled_announcements (channel_id, content, send_at, created_by, sent) "
        "VALUES (?, ?, ?, ?, 0)",
        (channel_id, content, send_at, created_by)
    )
    conn.commit()
    ann_id = cursor.lastrowid
    conn.close()
    return ann_id


def get_due_scheduled_announcements():
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, channel_id, content FROM scheduled_announcements WHERE sent=0 AND send_at <= ?",
        (int(time.time()),)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "channel_id": r[1], "content": r[2]} for r in rows]


def mark_announcement_sent(ann_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE scheduled_announcements SET sent=1 WHERE id=?", (ann_id,))
    conn.commit()
    conn.close()


def get_server_health_stats():
    """Admin panelindəki Server Sağlamlığı görünüşü üçün sürətli KPI-lar."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    now = int(time.time())
    today_start = now - (now % 86400)
    week_start = now - 7 * 86400
    cursor.execute("SELECT COUNT(*) FROM match_history WHERE played_at >= ?", (today_start,))
    matches_today = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM match_history WHERE played_at >= ?", (week_start,))
    matches_week = cursor.fetchone()[0]
    conn.close()
    return {"total_players": total_players, "matches_today": matches_today, "matches_week": matches_week}


def export_all_players_rows():
    """Admin "Data Export" üçün: hər oyunçunun kimlik + iqtisadiyyat + 5v5 statistikası, CSV-yə
    hazır sətirlər (dict) kimi."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.discord_id, p.so2_nick, p.so2_id, p.coins, p.zm_balance,
               COALESCE(p5.elo, 1000), COALESCE(p5.wins, 0), COALESCE(p5.losses, 0),
               COALESCE(p5.kills, 0), COALESCE(p5.assists, 0), COALESCE(p5.deaths, 0),
               COALESCE(p5.peak_elo, 1000)
        FROM players p
        LEFT JOIN players_5v5 p5 ON p5.discord_id = p.discord_id
        ORDER BY COALESCE(p5.elo, 1000) DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "discord_id": r[0], "nick": r[1], "so2_id": r[2], "coins": r[3], "zm_balance": r[4],
            "elo": r[5], "wins": r[6], "losses": r[7], "kills": r[8], "assists": r[9], "deaths": r[10],
            "peak_elo": r[11],
        }
        for r in rows
    ]


def get_players_needing_decay_warning(warn_after_days, decay_at_days):
    """`warn_after_days` ilə `decay_at_days` arasında qeyri-aktiv olan (hələ decay BAŞLAMAYAN,
    amma tezliklə başlayacaq) oyunçuları qaytarır — bax: inactivity_elo_decay_loop-dakı
    əvvəlcədən xəbərdarlıq addımı. Hər oyunçuya yalnız BİR dəfə xəbərdarlıq göndərilir."""
    import time
    now = int(time.time())
    warn_cutoff = now - warn_after_days * 86400
    decay_cutoff = now - decay_at_days * 86400
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id FROM players_5v5 WHERE last_match_at IS NOT NULL "
        "AND last_match_at < ? AND last_match_at >= ? "
        "AND (decay_warning_sent_at IS NULL OR decay_warning_sent_at < last_match_at)",
        (warn_cutoff, decay_cutoff)
    )
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def mark_decay_warning_sent(discord_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE players_5v5 SET decay_warning_sent_at = ? WHERE discord_id = ?",
        (int(time.time()), discord_id)
    )
    conn.commit()
    conn.close()



def get_inactive_unplayed_players(cutoff_ts):
    """Qeydiyyatdan (created_at) bəri cutoff_ts-dən çox vaxt keçmiş, amma heç bir 5v5 matçı
    oynamamış oyunçuları qaytarır. DİQQƏT: əvvəllər `players.last_match_at`-a baxırdı — o sütun
    2v2 sisteminin qalığıdır və 5v5-ə keçdikdən sonra HEÇ VAXT yazılmır (bax: update_team_elo_5v5,
    `players_5v5.last_match_at`-a yazır), ona görə HƏR gün, 3+ gün əvvəl qeydiyyatdan keçmiş
    HƏR oyunçu (minlərlə real, aktiv 5v5 oyunçusu daxil) "heç oynamayıb" sayılıb silinirdi. İndi
    əsl 5v5 fəallığına (players_5v5.last_match_at) baxır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.discord_id, p.so2_nick FROM players p "
        "LEFT JOIN players_5v5 p5 ON p5.discord_id = p.discord_id "
        "WHERE p.created_at IS NOT NULL AND p.created_at < ? "
        "AND (p5.discord_id IS NULL OR p5.last_match_at IS NULL)",
        (cutoff_ts,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "nick": r[1]} for r in rows]


def delete_player(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE discord_id = ?", (discord_id,))
    conn.commit()
    conn.close()


def archive_and_delete_player(discord_id, reason):
    """`delete_player`-in təhlükəsiz versiyası — sətri silmədən ƏVVƏL `deleted_players_archive`-ə
    köçürür ki, admin paneldən (bax: get_recent_deleted_players/restore_deleted_player) bərpa
    oluna bilsin. Qeydiyyat silmə insidentindən sonra əlavə edildi."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT so2_nick, so2_id, coins, zm_balance FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "INSERT INTO deleted_players_archive "
            "(discord_id, so2_nick, so2_id, coins, zm_balance, deleted_at, deleted_reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (discord_id, row[0], row[1], row[2], row[3], int(time.time()), reason)
        )
    cursor.execute("DELETE FROM players WHERE discord_id=?", (discord_id,))
    conn.commit()
    conn.close()


def get_recent_deleted_players(limit=30):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, discord_id, so2_nick, so2_id, coins, zm_balance, deleted_at, deleted_reason "
        "FROM deleted_players_archive ORDER BY deleted_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "discord_id": r[1], "nick": r[2], "so2_id": r[3],
         "coins": r[4], "zm_balance": r[5], "deleted_at": r[6], "reason": r[7]}
        for r in rows
    ]


def restore_deleted_player(archive_id):
    """Arxiv sətrini `players`-ə geri qaytarır (coin/AZN balansı daxil). Oyunçu artıq (başqa
    cür) qeydiyyatdan keçibsə üzərinə yazmır, False qaytarır."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, so2_nick, so2_id, coins, zm_balance FROM deleted_players_archive WHERE id=?",
        (archive_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    discord_id, nick, so2_id, coins, zm_balance = row
    cursor.execute("SELECT 1 FROM players WHERE discord_id=?", (discord_id,))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO players (discord_id, so2_nick, so2_id, coins, zm_balance, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (discord_id, nick, so2_id, coins or 0, zm_balance or 0, int(time.time()))
    )
    cursor.execute("DELETE FROM deleted_players_archive WHERE id=?", (archive_id,))
    conn.commit()
    conn.close()
    return True


def process_pending_cleanup(candidate_ids, now_ts, grace_seconds=86400):
    """Gündəlik avtomatik qeydiyyat təmizləməsi üçün iki-mərhələli təhlükəsizlik: bir oyunçu
    İLK dəfə namizəd olanda sadəcə QEYD edilir (dərhal silinmir) — YALNIZ ən az `grace_seconds`
    (defolt 24 saat) sonra HƏLƏ DƏ namizəddirsə, bu funksiya onu "bu gün silinməli" siyahısına
    qaytarır. Aralıqda aktivləşən (namizəd siyahısından çıxan) oyunçular avtomatik təmizlənir.
    Qeydiyyat silmə insidentindən sonra əlavə edildi."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id, flagged_at FROM pending_player_cleanup")
    pending = {r[0]: r[1] for r in cursor.fetchall()}

    candidate_set = set(candidate_ids)
    to_delete = []
    newly_flagged = []
    for did in candidate_set:
        if did in pending:
            if now_ts - pending[did] >= grace_seconds:
                to_delete.append(did)
        else:
            cursor.execute(
                "INSERT INTO pending_player_cleanup (discord_id, flagged_at) VALUES (?, ?)",
                (did, now_ts)
            )
            newly_flagged.append(did)

    for did in list(pending.keys()):
        if did not in candidate_set:
            cursor.execute("DELETE FROM pending_player_cleanup WHERE discord_id=?", (did,))

    for did in to_delete:
        cursor.execute("DELETE FROM pending_player_cleanup WHERE discord_id=?", (did,))

    conn.commit()
    conn.close()
    return {"to_delete": to_delete, "newly_flagged": newly_flagged}


def maybe_grant_profile_surprise(discord_id, date_key, chance=0.05, min_coin=5, max_coin=20):
    """Gündə İLK `/profile` açılışında kiçik ehtimalla (defolt 5%) sürpriz coin bonusu verir.
    Bu gün artıq yoxlanılıbsa (bonus düşsə də düşməsə də) bir daha yoxlamır, None qaytarır."""
    import random as _random
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT last_profile_surprise_day FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if row and row[0] == date_key:
        conn.close()
        return None
    cursor.execute("UPDATE players SET last_profile_surprise_day=? WHERE discord_id=?", (date_key, discord_id))
    amount = None
    if _random.random() < chance:
        amount = _random.randint(min_coin, max_coin)
        cursor.execute("UPDATE players SET coins = coins + ? WHERE discord_id=?", (amount, discord_id))
    conn.commit()
    conn.close()
    return amount


# ═══════════════════════════════════════════════════════════════════════════════
# MAĞAZA — gaming aksessuarlar (2E kataloqu) + rəqəmsal məhsullar (bax: web_leaderboard/store_catalog_seed.json)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_store_catalog(json_path):
    """`store_catalog_seed.json`-dan kateqoriya/məhsulları bir dəfəlik doldurur (bax: bot.py-dəki
    on_ready-də meta-bayraqla qorunan çağırış). Artıq mövcud olan kateqoriya/məhsul kodlarını
    YENİDƏN yaratmır (idempotent) — təkrar çağırılsa belə dublikat yaratmaz."""
    import json as _json
    with open(json_path, "r", encoding="utf-8") as f:
        categories = _json.load(f)

    conn = _get_conn()
    cursor = conn.cursor()
    added_categories = 0
    added_products = 0
    for cat in categories:
        cursor.execute("SELECT 1 FROM store_categories WHERE id=?", (cat["id"],))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO store_categories (id, name, sort_order, is_digital) VALUES (?, ?, ?, ?)",
                (cat["id"], cat["name"], cat.get("sort_order", 0), cat.get("is_digital", 0))
            )
            added_categories += 1
        for p in cat.get("products", []):
            cursor.execute(
                "SELECT 1 FROM store_products WHERE category_id=? AND code=?",
                (cat["id"], p.get("code"))
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                "INSERT INTO store_products (category_id, code, name, price_azn, stock, active) "
                "VALUES (?, ?, ?, ?, ?, 1)",
                (cat["id"], p.get("code"), p["name"], p.get("price_azn", 0), p.get("stock", 0))
            )
            added_products += 1
    conn.commit()
    conn.close()
    return {"categories": added_categories, "products": added_products}


def get_store_categories():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT c.id, c.name, c.sort_order, c.is_digital, COUNT(p.id) "
        "FROM store_categories c LEFT JOIN store_products p ON p.category_id = c.id AND p.active=1 "
        "GROUP BY c.id ORDER BY c.sort_order ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "sort_order": r[2], "is_digital": bool(r[3]), "product_count": r[4]}
        for r in rows
    ]


def get_store_products(category_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, code, name, price_azn, stock, active, image_path FROM store_products "
        "WHERE category_id=? AND active=1 ORDER BY name ASC",
        (category_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "code": r[1], "name": r[2], "price_azn": r[3], "stock": r[4],
         "active": bool(r[5]), "image_path": r[6]}
        for r in rows
    ]


def set_store_product_active(product_id, active):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE store_products SET active=? WHERE id=?", (1 if active else 0, product_id))
    conn.commit()
    conn.close()


def set_store_stock(product_id, stock):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE store_products SET stock=? WHERE id=?", (stock, product_id))
    conn.commit()
    conn.close()


def add_store_product(category_id, name, price_azn, code=None, stock=0, image_path=None):
    """Mağazaya əl ilə tək-tək məhsul əlavə etmək üçün (bax: /profile → ... yox, admin/Claude
    tərəfindən məhsul şəkli+məlumatı verildikcə çağırılır — toplu seed deyil)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM store_categories WHERE id=?", (category_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError(f"Naməlum kateqoriya: {category_id}")
    cursor.execute(
        "INSERT INTO store_products (category_id, code, name, price_azn, stock, active, image_path) "
        "VALUES (?, ?, ?, ?, ?, 1, ?)",
        (category_id, code, name, price_azn, stock, image_path)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id


def update_store_product(product_id, **fields):
    """`fields`: name/price_azn/code/stock/image_path/active sahələrindən istənilənini yeniləyir."""
    allowed = {"name", "price_azn", "code", "stock", "image_path", "active"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    conn = _get_conn()
    cursor = conn.cursor()
    cols = ", ".join(f"{k}=?" for k in sets)
    cursor.execute(f"UPDATE store_products SET {cols} WHERE id=?", (*sets.values(), product_id))
    conn.commit()
    conn.close()


def delete_store_product(product_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM store_products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def clear_store_products():
    """Bütün mağaza məhsullarını silir, kateqoriyaları (şablon strukturu) saxlayır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM store_products")
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


def get_all_store_products_admin():
    """Admin/idarəetmə üçün — `active` statusundan asılı olmayaraq BÜTÜN məhsulları qaytarır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.id, p.category_id, c.name, p.code, p.name, p.price_azn, p.stock, p.active, p.image_path "
        "FROM store_products p JOIN store_categories c ON c.id = p.category_id "
        "ORDER BY c.sort_order ASC, p.name ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "category_id": r[1], "category_name": r[2], "code": r[3], "name": r[4],
         "price_azn": r[5], "stock": r[6], "active": bool(r[7]), "image_path": r[8]}
        for r in rows
    ]



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




# Sıra artıq SQLite-da (matchmaking_queue) saxlanılır, in-memory Python siyahısında YOX.
# Səbəb: Railway deploy zamanı köhnə/yeni konteyner bir neçə saniyə paralel işləyə bilir —
# hər ikisi eyni Discord gateway hadisələrini alır. In-memory siyahı prosesə məxsus olduğu
# üçün hər iki proses eyni 4 nəfəri MÜSTƏQİL görüb HƏR İKİSİ öz matçını yaradırdı (dublikat
# matç bug-ının kök səbəbi). SQLite ilə bütün proseslər EYNİ, paylaşılan vəziyyəti görür və
# pop_4_and_balance() BEGIN IMMEDIATE ilə atomik işləyir ki iki proses eyni 4 nəfəri paralel
# "götürə" bilməsin.
















# ═══════════════════════════════════════════════════════════════════════════════
# PARALEL 5v5 SİSTEMİ — ayrıca sıra/ELO/statistika, `players` cədvəlinə TOXUNMUR.
# Kimlik/iqtisadiyyat (nick, so2_id, coins, inventory, achievements, battle pass)
# `players`-də PAYLAŞILMIŞ qalır, yalnız rəqabət statistikası `players_5v5`-dədir.
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_5v5_stats_row(discord_id):
    """Oyunçu ilk dəfə 5v5 sırasına qoşulanda `players_5v5`-də sətir yaradır (yoxdursa)."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM players_5v5 WHERE discord_id=?", (discord_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO players_5v5 (discord_id, elo, peak_elo, created_at) VALUES (?, 1000, 1000, ?)",
            (discord_id, int(time.time()))
        )
        conn.commit()
    conn.close()


def get_player_5v5(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, elo, wins, losses, kills, assists, deaths, win_streak, "
        "loss_streak, peak_elo, max_streak, created_at, last_match_at FROM players_5v5 WHERE discord_id=?",
        (discord_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "discord_id": row[0], "elo": row[1], "wins": row[2], "losses": row[3],
        "kills": row[4], "assists": row[5], "deaths": row[6], "win_streak": row[7],
        "loss_streak": row[8], "peak_elo": row[9], "max_streak": row[10], "created_at": row[11],
        "last_match_at": row[12],
    }


def get_player_stats_dict_5v5(discord_id):
    """`get_player_stats_dict`-in 5v5 analoqu — nick/so2_id/coins `players`-dən, rəqabət
    statistikası `players_5v5`-dən götürülüb eyni dict formatına gətirilir (kart generatorları
    ilə tam uyğun — bax: generate_stats_card)."""
    player = get_player(discord_id)
    stats5 = get_player_5v5(discord_id)
    if not player or not stats5:
        return None
    matches = stats5["wins"] + stats5["losses"]
    win_rate = round((stats5["wins"] / matches) * 100, 1) if matches > 0 else 0.0
    kd = round(stats5["kills"] / max(stats5["deaths"], 1), 2)
    return {
        "discord_id": discord_id, "nick": player[1], "so2_id": player[2],
        "elo": stats5["elo"], "wins": stats5["wins"], "losses": stats5["losses"],
        "matches": matches, "win_rate": win_rate,
        "kills": stats5["kills"], "assists": stats5["assists"], "deaths": stats5["deaths"], "kd": kd,
        "win_streak": stats5["win_streak"], "max_streak": stats5["max_streak"],
        "coins": get_coins(discord_id),
    }


def update_team_elo_5v5(winner_ids, loser_ids, elo_multiplier=1):
    """`update_team_elo`-nun `players_5v5` üzərində işləyən analoqu — eyni K=32 komanda-orta-ELO
    düsturu, eyni `apply_elo_modifiers` (ELO kartları PAYLAŞILMIŞ iqtisadiyyat üzvüdür)."""
    import time
    for discord_id in winner_ids + loser_ids:
        ensure_5v5_stats_row(discord_id)

    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())

    def fetch_all(ids):
        result = []
        for discord_id in ids:
            cursor.execute("SELECT discord_id, elo, wins, losses FROM players_5v5 WHERE discord_id = ?", (discord_id,))
            row = cursor.fetchone()
            if row:
                result.append(row)
        return result

    winners = fetch_all(winner_ids)
    losers = fetch_all(loser_ids)
    if not winners or not losers:
        conn.close()
        return None

    winner_avg_elo = sum(p[1] for p in winners) / len(winners)
    loser_avg_elo = sum(p[1] for p in losers) / len(losers)

    K = 32
    expected_winner = 1 / (1 + 10 ** ((loser_avg_elo - winner_avg_elo) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_avg_elo - loser_avg_elo) / 400))
    elo_change_winner = round(K * (1 - expected_winner)) * elo_multiplier
    elo_change_loser = round(K * (0 - expected_loser)) * elo_multiplier

    results = {"winners": [], "losers": []}
    for discord_id, elo, wins, losses in winners:
        new_elo = elo + apply_elo_modifiers(discord_id, elo_change_winner, cursor=cursor)
        peak_elo = max(new_elo, cursor.execute(
            "SELECT peak_elo FROM players_5v5 WHERE discord_id=?", (discord_id,)
        ).fetchone()[0])
        cursor.execute(
            "UPDATE players_5v5 SET elo=?, wins=?, peak_elo=?, last_match_at=? WHERE discord_id=?",
            (new_elo, wins + 1, peak_elo, now, discord_id)
        )
        results["winners"].append({"discord_id": discord_id, "old_elo": elo, "new_elo": new_elo})

    for discord_id, elo, wins, losses in losers:
        new_elo = elo + apply_elo_modifiers(discord_id, elo_change_loser, cursor=cursor)
        cursor.execute(
            "UPDATE players_5v5 SET elo=?, losses=?, last_match_at=? WHERE discord_id=?",
            (new_elo, losses + 1, now, discord_id)
        )
        results["losers"].append({"discord_id": discord_id, "old_elo": elo, "new_elo": new_elo})

    conn.commit()
    conn.close()
    return results


def apply_inactivity_elo_decay(inactive_days=14, decay_interval_days=7, decay_amount=10, floor_elo=1000):
    """Liderlik lövhəsini real-aktiv oyunçularla göstərmək üçün: `inactive_days`+ gündür 5v5
    oynamayan oyunçuların ELO-su hər `decay_interval_days` gündə bir `decay_amount` azalır,
    `floor_elo`-dan (başlanğıc ELO) aşağı düşmür. Yalnız real (sıfırdan böyük) dəyişikliyi olan
    oyunçuları `{discord_id, old_elo, new_elo}` siyahısı kimi qaytarır (çağıran tərəf rol/DM
    sinxronlaşdırması üçün istifadə edir)."""
    import time
    now = int(time.time())
    inactive_cutoff = now - inactive_days * 86400
    decay_cutoff = now - decay_interval_days * 86400

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_id, elo FROM players_5v5 WHERE last_match_at IS NOT NULL AND last_match_at < ? "
        "AND elo > ? AND (last_decay_at IS NULL OR last_decay_at < ?)",
        (inactive_cutoff, floor_elo, decay_cutoff)
    )
    rows = cursor.fetchall()

    decayed = []
    for discord_id, elo in rows:
        new_elo = max(floor_elo, elo - decay_amount)
        cursor.execute(
            "UPDATE players_5v5 SET elo=?, last_decay_at=? WHERE discord_id=?",
            (new_elo, now, discord_id)
        )
        if new_elo != elo:
            decayed.append({"discord_id": discord_id, "old_elo": elo, "new_elo": new_elo})

    conn.commit()
    conn.close()
    return decayed


def update_streak_5v5(discord_id, won: bool):
    ensure_5v5_stats_row(discord_id)
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT win_streak, max_streak, loss_streak FROM players_5v5 WHERE discord_id=?", (discord_id,))
    streak, max_s, loss_streak = cursor.fetchone()
    if won:
        streak += 1
        max_s = max(max_s, streak)
        loss_streak = 0
    else:
        streak = 0
        loss_streak += 1
    cursor.execute("UPDATE players_5v5 SET win_streak=?, max_streak=?, loss_streak=? WHERE discord_id=?",
                   (streak, max_s, loss_streak, discord_id))
    conn.commit(); conn.close()
    return streak, max_s




def add_to_queue_5v5(discord_id, nick, elo, so2_id=""):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO matchmaking_queue_5v5 (discord_id, nick, so2_id, elo, joined_at) VALUES (?, ?, ?, ?, ?)",
            (discord_id, nick, so2_id, elo, int(time.time()))
        )
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        added = False
    conn.close()
    return added


def remove_from_queue_5v5(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matchmaking_queue_5v5 WHERE discord_id = ?", (discord_id,))
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def queue_size_5v5():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM matchmaking_queue_5v5")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_queue_list_5v5():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id, nick, elo, so2_id, joined_at FROM matchmaking_queue_5v5 ORDER BY joined_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "nick": r[1], "elo": r[2], "so2_id": r[3], "joined_at": r[4]} for r in rows]


def clear_queue_5v5():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matchmaking_queue_5v5")
    conn.commit()
    conn.close()


def is_in_queue_5v5(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM matchmaking_queue_5v5 WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def _balance_5v5_teams(players, locked_pairs=None):
    """10 oyunçunu ELO-ya görə ən balanslaşdırılmış 2x5 komandaya bölür — mümkün bütün
    C(10,5)=252 bölgü arasında komandaların ümumi ELO fərqini minimuma endirəni tapır.
    Bərabər (ən balanslaşdırılmış) bölgülər arasında təsadüfi seçim edilir ki, eyni ELO
    profilində hər dəfə eyni qruplaşma təkrarlanmasın.

    locked_pairs: [(discord_id_a, discord_id_b), ...] — bu cütlər (aktiv duo komanda
    üzvləri) HƏMİŞƏ eyni tərəfdə saxlanılır. Heç bir bölgü bütün cütləri eyni anda təmin
    etmirsə (nadir hal — komanda ölçüsü 5 tək ədəd olduğu üçün, məs. 5 üst-üstə düşməyən
    cüt eyni hovuzda olanda riyazi mümkünsüz ola bilər), məhdudiyyət görməzdən gəlinir."""
    import random
    from itertools import combinations

    id_to_index = {p["discord_id"]: i for i, p in enumerate(players)}

    def _respects_pairs(combo_set):
        if not locked_pairs:
            return True
        for a_id, b_id in locked_pairs:
            a_idx, b_idx = id_to_index.get(a_id), id_to_index.get(b_id)
            if a_idx is None or b_idx is None:
                continue
            if (a_idx in combo_set) != (b_idx in combo_set):
                return False
        return True

    total_elo = sum(p["elo"] for p in players)

    def _find_best(enforce_pairs):
        best_diff = None
        best_splits = []
        for combo in combinations(range(len(players)), 5):
            combo_set = set(combo)
            if enforce_pairs and not _respects_pairs(combo_set):
                continue
            team_a_elo = sum(players[i]["elo"] for i in combo)
            diff = abs(team_a_elo - (total_elo - team_a_elo))
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_splits = [combo]
            elif diff == best_diff:
                best_splits.append(combo)
        return best_splits

    best_splits = _find_best(enforce_pairs=True)
    if not best_splits:
        best_splits = _find_best(enforce_pairs=False)

    chosen = set(random.choice(best_splits))
    team_a = [players[i] for i in range(len(players)) if i in chosen]
    team_b = [players[i] for i in range(len(players)) if i not in chosen]
    return team_a, team_b


def _get_locked_team_pairs_for_players(players):
    """Verilən oyunçu hovuzunun İÇİNDƏ hər iki üzvü eyni anda olan aktiv duo komandaların
    (owner_id, member_id) cütlərini qaytarır — bax: _balance_5v5_teams."""
    ids_in_pool = {p["discord_id"] for p in players}
    pairs = []
    for t in get_active_duo_teams():
        if t["member_id"] is not None and t["owner_id"] in ids_in_pool and t["member_id"] in ids_in_pool:
            pairs.append((t["owner_id"], t["member_id"]))
    return pairs


def pop_10_and_balance():
    """Sıradan ən əvvəl qoşulan 10 nəfəri ATOMİK götürüb ELO-ya görə balanslaşdırılmış iki
    5-nəfərlik komandaya bölür (bax: _balance_5v5_teams)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            "SELECT discord_id, nick, elo, so2_id FROM matchmaking_queue_5v5 ORDER BY joined_at ASC LIMIT 10"
        )
        rows = cursor.fetchall()
        if len(rows) < 10:
            cursor.execute("ROLLBACK")
            conn.close()
            return None
        ids = [r[0] for r in rows]
        cursor.executemany("DELETE FROM matchmaking_queue_5v5 WHERE discord_id = ?", [(i,) for i in ids])
        cursor.execute("COMMIT")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        conn.close()
        return None
    conn.close()

    players = [{"discord_id": r[0], "nick": r[1], "elo": r[2], "so2_id": r[3]} for r in rows]
    locked_pairs = _get_locked_team_pairs_for_players(players)
    team_a, team_b = _balance_5v5_teams(players, locked_pairs)

    captain_a = max(team_a, key=lambda p: p["elo"])
    captain_b = max(team_b, key=lambda p: p["elo"])

    return team_a, team_b, captain_a, captain_b


def set_player_5v5_elo(discord_id, new_elo):
    """Matç ləğvi ELO cəzası kimi bir-başa yazma hallar üçün (bax: admin_set_player_field-in
    2v2 analoqu, CancelMatchView5v5)."""
    ensure_5v5_stats_row(discord_id)
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE players_5v5 SET elo=? WHERE discord_id=?", (new_elo, discord_id))
    conn.commit()
    conn.close()


def get_all_players_5v5(limit=1000):
    """5v5 oynamış (players_5v5-də sətri olan) bütün oyunçuları qaytarır — rol-sinxronizasiyası
    üçün (bax: /rank_rollari_qur)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id, elo FROM players_5v5 ORDER BY elo DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "elo": r[1]} for r in rows]


def get_leaderboard_5v5(limit=20):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.so2_nick, p.so2_id, p5.elo, p5.wins, p5.losses, p.active_banner, p5.kills, p5.deaths
        FROM players_5v5 p5
        JOIN players p ON p.discord_id = p5.discord_id
        ORDER BY p5.elo DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_leaderboard_5v5_alltime(limit=20):
    """Sezon sıfırlamalarından toxunulmaz qalan `peak_elo`-ya əsaslanan ümumi
    (bütün-zamanların) leaderboard — sezon leaderboard-undan fərqli olaraq sıfırlanmır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.so2_nick, p.so2_id, p5.peak_elo, p5.wins, p5.losses, p.active_banner, p5.kills, p5.deaths
        FROM players_5v5 p5
        JOIN players p ON p.discord_id = p5.discord_id
        ORDER BY p5.peak_elo DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


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


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

def create_ticket(discord_id, channel_id, ticket_type):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tickets (discord_id, channel_id, ticket_type, status, created_at) VALUES (?, ?, ?, 'open', ?)",
        (discord_id, channel_id, ticket_type, int(time.time()))
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def get_open_ticket(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, discord_id, channel_id, ticket_type, status, created_at FROM tickets "
        "WHERE discord_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
        (discord_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "discord_id": row[1], "channel_id": row[2], "ticket_type": row[3],
            "status": row[4], "created_at": row[5]}


def get_ticket_by_channel(channel_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, discord_id, channel_id, ticket_type, status, created_at FROM tickets WHERE channel_id = ?",
        (channel_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "discord_id": row[1], "channel_id": row[2], "ticket_type": row[3],
            "status": row[4], "created_at": row[5]}


def close_ticket(ticket_id):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET status = 'closed', closed_at = ? WHERE id = ?",
        (int(time.time()), ticket_id)
    )
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DUO TEAM — müddətli (10/30 gün), max 2 nəfər, 1 oyunçu max 1 komandada
# ═══════════════════════════════════════════════════════════════════════════════

_TEAM_REMINDER_COLUMNS = {"reminder_7d", "reminder_3d", "reminder_1d", "reminder_1h"}


def is_in_duo_team(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    import time
    now = int(time.time())
    cursor.execute(
        "SELECT 1 FROM duo_teams WHERE status='active' AND expires_at > ? AND (owner_id=? OR member_id=?)",
        (now, discord_id, discord_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def create_duo_team(owner_id, duration_days):
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    expires_at = now + duration_days * 86400
    cursor.execute(
        "INSERT INTO duo_teams (owner_id, member_id, created_at, expires_at, status) VALUES (?, NULL, ?, ?, 'active')",
        (owner_id, now, expires_at)
    )
    conn.commit()
    team_id = cursor.lastrowid
    conn.close()
    return team_id


def _row_to_team(row):
    return {
        "id": row[0], "owner_id": row[1], "member_id": row[2], "created_at": row[3],
        "expires_at": row[4], "status": row[5], "channel_id": row[6] if len(row) > 6 else None,
    }


def set_team_channel(team_id, channel_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE duo_teams SET channel_id=? WHERE id=?", (channel_id, team_id))
    conn.commit()
    conn.close()


def get_duo_team_for_player(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    import time
    now = int(time.time())
    cursor.execute(
        "SELECT id, owner_id, member_id, created_at, expires_at, status, channel_id FROM duo_teams "
        "WHERE status='active' AND expires_at > ? AND (owner_id=? OR member_id=?)",
        (now, discord_id, discord_id)
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_team(row) if row else None


def get_duo_team(team_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, owner_id, member_id, created_at, expires_at, status, channel_id FROM duo_teams WHERE id=?",
        (team_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_team(row) if row else None


def join_duo_team(team_id, member_id):
    """Komandaya yalnız boş yer varsa (member_id hələ NULL-dursa) üzv əlavə edir."""
    conn = _get_conn()
    cursor = conn.cursor()
    import time
    now = int(time.time())
    cursor.execute("SELECT member_id FROM duo_teams WHERE id=? AND status='active' AND expires_at > ?", (team_id, now))
    row = cursor.fetchone()
    if not row or row[0] is not None:
        conn.close()
        return False
    cursor.execute("UPDATE duo_teams SET member_id=? WHERE id=?", (member_id, team_id))
    conn.commit()
    conn.close()
    return True


def disband_duo_team(team_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE duo_teams SET status='expired' WHERE id=?", (team_id,))
    conn.commit()
    conn.close()


def get_active_duo_teams():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, owner_id, member_id, created_at, expires_at, status, "
        "reminder_7d, reminder_3d, reminder_1d, reminder_1h, channel_id FROM duo_teams WHERE status='active'"
    )
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = _row_to_team((r[0], r[1], r[2], r[3], r[4], r[5], r[10]))
        d.update({"reminder_7d": r[6], "reminder_3d": r[7], "reminder_1d": r[8], "reminder_1h": r[9]})
        result.append(d)
    return result


def mark_team_reminder_sent(team_id, reminder_column):
    if reminder_column not in _TEAM_REMINDER_COLUMNS:
        raise ValueError(f"Keçərsiz reminder sütunu: {reminder_column}")
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE duo_teams SET {reminder_column}=1 WHERE id=?", (team_id,))
    conn.commit()
    conn.close()


def expire_due_teams():
    """Vaxtı keçmiş aktiv komandaları 'expired' statusuna keçirir, bildiriş üçün siyahısını qaytarır."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    now = int(time.time())
    cursor.execute("SELECT id, owner_id, member_id, channel_id FROM duo_teams WHERE status='active' AND expires_at <= ?", (now,))
    rows = cursor.fetchall()
    cursor.execute("UPDATE duo_teams SET status='expired' WHERE status='active' AND expires_at <= ?", (now,))
    conn.commit()
    conn.close()
    return [{"id": r[0], "owner_id": r[1], "member_id": r[2], "channel_id": r[3]} for r in rows]


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


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK MÜKAFAT — ardıcıl gün bonusu (streak) + gündəlik çarx (random bonus)
# ═══════════════════════════════════════════════════════════════════════════════

DAILY_WHEEL_OUTCOMES = [
    # (çəki, növ, min, max) — yalnız coin (bax: istifadəçi tələbi, ELO kartları/AZN çıxarıldı)
    (50, "coins", 5, 15),
    (25, "coins", 20, 40),
]


def get_daily_claim_status(discord_id):
    """Oyunçunun gündəlik mükafatı bu gün artıq götürüb-götürmədiyini və cari seriyasını qaytarır."""
    import datetime
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT streak, last_claim_at FROM daily_claims WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or row[1] is None:
        return {"streak": row[0] if row else 0, "can_claim": True}
    last_date = datetime.datetime.utcfromtimestamp(row[1]).date()
    today = datetime.datetime.utcnow().date()
    return {"streak": row[0], "can_claim": last_date != today}


def claim_daily_reward(discord_id):
    """Gündəlik giriş mükafatını götürür: ardıcıl gün sayına görə artan əsas bonus (streak,
    max 100 coin) + gündəlik çarx fırlatması (random bonus — coin/ELO kartı/AZN). Gündə yalnız
    bir dəfə işləyir (UTC tarixinə görə). Artıq götürülübsə {"already_claimed": True} qaytarır.
    Bir gün buraxılırsa seriya sıfırlanır (1-dən başlayır)."""
    import time
    import datetime
    import random as _random

    now = int(time.time())
    today = datetime.datetime.utcfromtimestamp(now).date()

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT streak, last_claim_at FROM daily_claims WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    streak, last_claim_at = row if row else (0, None)

    if last_claim_at is not None:
        last_date = datetime.datetime.utcfromtimestamp(last_claim_at).date()
        if last_date == today:
            conn.close()
            return {"already_claimed": True, "streak": streak}
        new_streak = streak + 1 if (today - last_date).days == 1 else 1
    else:
        new_streak = 1

    streak_bonus = min(10 + (new_streak - 1) * 5, 100)
    weights = [o[0] for o in DAILY_WHEEL_OUTCOMES]
    _, kind, lo, hi = _random.choices(DAILY_WHEEL_OUTCOMES, weights=weights, k=1)[0]

    result = {"already_claimed": False, "streak": new_streak, "streak_bonus": streak_bonus,
              "wheel_kind": kind, "wheel_amount": 0}
    coin_total = streak_bonus
    if kind == "coins":
        amount = _random.randint(lo, hi)
        coin_total += amount
        result["wheel_amount"] = amount
    elif kind in ("boost_card", "protect_card"):
        result["wheel_amount"] = 1
    elif kind == "azn":
        result["wheel_amount"] = hi

    if coin_total:
        cursor.execute("UPDATE players SET coins = coins + ? WHERE discord_id=?", (coin_total, discord_id))
    if kind == "boost_card":
        cursor.execute("UPDATE players SET boost50_cards = boost50_cards + 1 WHERE discord_id=?", (discord_id,))
    elif kind == "protect_card":
        cursor.execute("UPDATE players SET protect_cards = protect_cards + 1 WHERE discord_id=?", (discord_id,))
    elif kind == "azn":
        cursor.execute("UPDATE players SET zm_balance = zm_balance + ? WHERE discord_id=?", (result["wheel_amount"], discord_id))

    if row:
        cursor.execute("UPDATE daily_claims SET streak=?, last_claim_at=? WHERE discord_id=?", (new_streak, now, discord_id))
    else:
        cursor.execute("INSERT INTO daily_claims (discord_id, streak, last_claim_at) VALUES (?, ?, ?)", (discord_id, new_streak, now))

    cursor.execute("SELECT coins, zm_balance FROM players WHERE discord_id=?", (discord_id,))
    bal_row = cursor.fetchone()
    result["coin_total"] = coin_total
    result["new_coin_balance"] = bal_row[0] if bal_row else None
    result["new_azn_balance"] = bal_row[1] if bal_row else None

    conn.commit()
    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK TAPŞIRIQLAR — 3 sabit tapşırıq, hər gün (UTC tarixinə görə) sıfırlanır
# ═══════════════════════════════════════════════════════════════════════════════

def get_daily_task_progress(discord_id, date_key):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT play_progress, win_progress, kill_progress, claimed_play, claimed_win, claimed_kill "
        "FROM daily_task_progress WHERE discord_id=? AND date_key=?",
        (discord_id, date_key)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"play": 0, "win": 0, "kill": 0, "claimed_play": False, "claimed_win": False, "claimed_kill": False}
    return {
        "play": row[0], "win": row[1], "kill": row[2],
        "claimed_play": bool(row[3]), "claimed_win": bool(row[4]), "claimed_kill": bool(row[5]),
    }


def advance_daily_task(discord_id, date_key, won, kills):
    """Hər 5v5 matçdan sonra çağırılır — gündəlik tapşırıq tərəqqisini artırır (upsert)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO daily_task_progress (discord_id, date_key, play_progress, win_progress, kill_progress) "
        "VALUES (?, ?, 1, ?, ?) "
        "ON CONFLICT(discord_id, date_key) DO UPDATE SET "
        "play_progress = play_progress + 1, "
        "win_progress = win_progress + excluded.win_progress, "
        "kill_progress = kill_progress + excluded.kill_progress",
        (discord_id, date_key, 1 if won else 0, kills)
    )
    conn.commit()
    conn.close()


def claim_daily_task(discord_id, date_key, task_id):
    """`task_id`: 'play'|'win'|'kill'. Artıq claim edilibsə (və ya sütun adı etibarsızdırsa)
    False qaytarır — idempotentdir."""
    if task_id not in ("play", "win", "kill"):
        return False
    col = f"claimed_{task_id}"
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE daily_task_progress SET {col}=1 WHERE discord_id=? AND date_key=? AND {col}=0",
        (discord_id, date_key)
    )
    conn.commit()
    ok = cursor.rowcount > 0
    conn.close()
    return ok


def record_perfect_task_day(discord_id, date_key):
    """Oyunçu eyni gündə HƏR 3 gündəlik tapşırığı claim edəndə çağırılır (bax: bot.py-dəki
    DailyTasksClaimView) — ardıcıl "mükəmməl gün" seriyasını yeniləyir, yeni seriya ədədini
    qaytarır. Bir gün buraxılırsa seriya 1-dən yenidən başlayır."""
    import datetime as _dt
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT task_streak, last_perfect_task_day FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    streak, last_day = (row[0] or 0, row[1]) if row else (0, None)

    if last_day == date_key:
        conn.close()
        return streak

    today = _dt.datetime.strptime(date_key, "%Y-%m-%d").date()
    if last_day:
        last = _dt.datetime.strptime(last_day, "%Y-%m-%d").date()
        new_streak = streak + 1 if (today - last).days == 1 else 1
    else:
        new_streak = 1

    cursor.execute(
        "UPDATE players SET task_streak=?, last_perfect_task_day=? WHERE discord_id=?",
        (new_streak, date_key, discord_id)
    )
    conn.commit()
    conn.close()
    return new_streak


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET — kosmetik inventar (banner/çərçivə, coin) + ELO kartları (AZN)
# ═══════════════════════════════════════════════════════════════════════════════

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
    cursor.execute(
        "INSERT OR IGNORE INTO inventory (discord_id, item_id, acquired_at) VALUES (?, ?, ?)",
        (discord_id, item_id, int(time.time()))
    )
    conn.commit()
    conn.close()


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
    """Balans kifayətdirsə AZN çıxır və True qaytarır, yoxdursa False qaytarır."""
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


def add_boost_cards(discord_id, card_type, qty):
    """card_type: 'boost50', 'boost100', 'protect' (bax: _BOOST_CARD_COLS)."""
    col = _BOOST_CARD_COLS[card_type]
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {col} = {col} + ? WHERE discord_id = ?", (qty, discord_id))
    conn.commit()
    conn.close()


def get_boost_card_counts(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT boost50_cards, boost100_cards, protect_cards FROM players WHERE discord_id = ?",
        (discord_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"boost50": 0, "boost100": 0, "protect": 0}
    return {"boost50": row[0], "boost100": row[1], "protect": row[2]}


# ═══════════════════════════════════════════════════════════════════════════════
# MYSTERY BOX — saytda Discord girişi ilə açılan qutu (100 coin), ELO Boost/Qoruma
# kartları verir. Kartlar mövcud boost50/protect iqtisadiyyatına düşür — bax:
# apply_elo_modifiers/consume_boost_card (bot.py-da ƏLAVƏ dəyişiklik lazım deyil,
# matçda AVTOMATİK istifadə olunur).
# ═══════════════════════════════════════════════════════════════════════════════

BOX_COST_COINS = 100

MYSTERY_BOX_ITEMS = [
    # ELO kartları — card_type: players cədvəlindəki boost50_cards/protect_cards sütunlarına
    # düşür, matçda AVTOMATİK istifadə olunur (bax: apply_elo_modifiers).
    {"key": "boost_1", "label": "1x ELO Boost", "icon": "⚡", "color": "#8d8794",
     "kind": "card", "card_type": "boost50", "qty": 1, "weight": 20},
    {"key": "boost_2", "label": "2x ELO Boost", "icon": "⚡", "color": "#5fd07a",
     "kind": "card", "card_type": "boost50", "qty": 2, "weight": 12},
    {"key": "boost_3", "label": "3x ELO Boost", "icon": "⚡", "color": "#50a0dc",
     "kind": "card", "card_type": "boost50", "qty": 3, "weight": 7},
    {"key": "boost_5", "label": "5x ELO Boost", "icon": "⚡", "color": "#b89cf0",
     "kind": "card", "card_type": "boost50", "qty": 5, "weight": 3},
    {"key": "shield_1", "label": "ELO Qoruma Kartı", "icon": "🛡️", "color": "#f0b429",
     "kind": "card", "card_type": "protect", "qty": 1, "weight": 2},

    # Coin — balans birbaşa artırılır.
    {"key": "coins_20", "label": "20 Coin", "icon": "🪙", "color": "#8d8794",
     "kind": "coins", "amount": 20, "weight": 25},
    {"key": "coins_50", "label": "50 Coin", "icon": "🪙", "color": "#5fd07a",
     "kind": "coins", "amount": 50, "weight": 15},
    {"key": "coins_100", "label": "100 Coin", "icon": "🪙", "color": "#f0b429",
     "kind": "coins", "amount": 100, "weight": 8},

    # Qutuya İSTİSNA kosmetikalar — Market-də satılmır, yalnız bu qutudan düşür
    # (bax: bot.py-dəki BOX_EXCLUSIVE_BANNERS/BOX_EXCLUSIVE_FRAMES).
    {"key": "cosmetic_banner", "label": "Mystery Banner", "icon": "🖼️", "color": "#50a0dc",
     "kind": "cosmetic", "item_type": "banner", "item_id": "banner_box_exclusive", "weight": 4},
    {"key": "cosmetic_banner_gif", "label": "Mystery Banner (GIF)", "icon": "🎬", "color": "#8a5ce6",
     "kind": "cosmetic", "item_type": "banner", "item_id": "banner_box_exclusive_gif", "weight": 2},
    {"key": "cosmetic_frame", "label": "Mystery Çərçivə", "icon": "💍", "color": "#f0b429",
     "kind": "cosmetic", "item_type": "frame", "item_id": "frame_box_exclusive", "weight": 1.5},
    {"key": "cosmetic_frame_gif", "label": "Mystery Çərçivə (GIF)", "icon": "✨", "color": "#d6453d",
     "kind": "cosmetic", "item_type": "frame", "item_id": "frame_box_exclusive_gif", "weight": 0.5},
]


def get_box_odds():
    total = sum(i["weight"] for i in MYSTERY_BOX_ITEMS)
    return [
        {**i, "pct": round(i["weight"] / total * 100, 1)}
        for i in MYSTERY_BOX_ITEMS
    ]


def open_mystery_box(discord_id, nick, cost=BOX_COST_COINS):
    """100 coin xərcləyib çəkiyə görə random mükafat verir. Kifayət qədər coin yoxdursa
    {"error": "insufficient_coins", "balance": N} qaytarır. Coin xərci `add_coin_log`
    vasitəsilə qeyd olunur ki, Discord `/profile` coin tarixçəsində də görünsün."""
    import time
    import random as _random

    if not spend_coins(discord_id, cost):
        return {"error": "insufficient_coins", "balance": get_coins(discord_id)}

    weights = [i["weight"] for i in MYSTERY_BOX_ITEMS]
    item = _random.choices(MYSTERY_BOX_ITEMS, weights=weights, k=1)[0]

    net_change = -cost
    if item["kind"] == "card":
        add_boost_cards(discord_id, item["card_type"], item["qty"])
    elif item["kind"] == "coins":
        add_coins(discord_id, item["amount"])
        net_change += item["amount"]
    elif item["kind"] == "cosmetic":
        add_to_inventory(discord_id, item["item_id"])

    new_balance = get_coins(discord_id)
    log_type = "earn" if net_change > 0 else "spend"
    add_coin_log(discord_id, net_change, f"🎁 Mystery Box: {item['label']}", log_type, new_balance)

    now = int(time.time())
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO box_openings (discord_id, nick, item_key, item_label, opened_at) VALUES (?, ?, ?, ?, ?)",
        (discord_id, nick, item["key"], item["label"], now)
    )
    conn.commit()
    conn.close()

    return {"error": None, "item": item, "balance": new_balance}


def get_recent_box_openings(limit=12):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nick, item_key, item_label, opened_at FROM box_openings ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"nick": r[0], "item_key": r[1], "item_label": r[2], "opened_at": r[3]}
        for r in rows
    ]




















def record_match_history(match_type, winner_ids, loser_ids, winner_elo_before, winner_elo_after,
                          loser_elo_before, loser_elo_after, match_number=None, map_name=None,
                          winner_kills=None, winner_assists=None, winner_deaths=None,
                          loser_kills=None, loser_assists=None, loser_deaths=None, season_id=None):
    """
    match_type: "1v1" veya "5v5"
    winner_ids, loser_ids: discord_id siyahÄ±sÄ± (1v1 Ã¼Ã§Ã¼n tÉ™k elementli)
    winner_elo_before/after, loser_elo_before/after: hÉ™r oyunÃ§unun ELO-su, ids ilÉ™ eyni sÄ±rada
    winner_kills/assists/deaths, loser_kills/assists/deaths: (optional) hər oyunçunun bu matçdakı
    K/A/D-si, ids ilə eyni sırada — scan təsdiqlənməyibsə None qalır (bax: get_player_match_history,
    ELO/K-D trend qrafiki üçün istifadə olunur).
    season_id: matçın aid olduğu sezon — bax: delete_match_and_revert/revert edilən admin alətləri,
    bunsuz season_stats-ı HƏDƏF matçla sinxron saxlamaq mümkün deyil (bax: "sezon ilə ümumi
    leaderboard fərqlidir" insidenti).
    """
    import json as _json
    import time as _time

    def _dump(values):
        return _json.dumps(values) if values is not None else None

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO match_history
           (match_type, played_at, match_number, winner_ids, loser_ids,
            winner_elo_before, winner_elo_after, loser_elo_before, loser_elo_after, map,
            winner_kills, winner_assists, winner_deaths, loser_kills, loser_assists, loser_deaths,
            season_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_type, int(_time.time()), match_number,
         _json.dumps(winner_ids), _json.dumps(loser_ids),
         _json.dumps(winner_elo_before), _json.dumps(winner_elo_after),
         _json.dumps(loser_elo_before), _json.dumps(loser_elo_after), map_name,
         _dump(winner_kills), _dump(winner_assists), _dump(winner_deaths),
         _dump(loser_kills), _dump(loser_assists), _dump(loser_deaths), season_id)
    )
    conn.commit()
    conn.close()


def get_weekly_elo_gainers(since_ts, limit=3, match_type="5v5"):
    """Verilən vaxtdan (unix timestamp) bəri `match_type` matçlarında hər oyunçunun cəmi ELO
    artımını hesablayır, ən çox artıranları sıralı qaytarır: [{discord_id, nick, elo_gained}, ...]
    (0 və ya mənfi nəticəli oyunçular siyahıya düşmür)."""
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT winner_ids, winner_elo_before, winner_elo_after, loser_ids, loser_elo_before, loser_elo_after "
        "FROM match_history WHERE match_type = ? AND played_at >= ?",
        (match_type, since_ts)
    )
    rows = cursor.fetchall()
    conn.close()

    gains = {}
    for w_ids, w_before, w_after, l_ids, l_before, l_after in rows:
        for did, before, after in zip(_json.loads(w_ids), _json.loads(w_before), _json.loads(w_after)):
            gains[did] = gains.get(did, 0) + (after - before)
        for did, before, after in zip(_json.loads(l_ids), _json.loads(l_before), _json.loads(l_after)):
            gains[did] = gains.get(did, 0) + (after - before)

    top = sorted(gains.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    result = []
    for discord_id, gained in top:
        if gained <= 0:
            continue
        p = get_player(discord_id)
        nick = p[1] if p else str(discord_id)
        result.append({"discord_id": discord_id, "nick": nick, "elo_gained": gained})
    return result


def get_map_stats(discord_id):
    """Oyunçunun hər xəritədə qələbə/məğlubiyyət sayını qaytarır: {map: {wins, losses}}."""
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT map, winner_ids, loser_ids FROM match_history WHERE map IS NOT NULL")
    stats = {}
    for map_name, winner_ids_json, loser_ids_json in cursor.fetchall():
        winner_ids = _json.loads(winner_ids_json)
        loser_ids = _json.loads(loser_ids_json)
        if discord_id in winner_ids:
            entry = stats.setdefault(map_name, {"wins": 0, "losses": 0})
            entry["wins"] += 1
        elif discord_id in loser_ids:
            entry = stats.setdefault(map_name, {"wins": 0, "losses": 0})
            entry["losses"] += 1
    conn.close()
    return stats




# ═══════════════════════════════════════════════════════════════════════════════
# SQUAD (SABİT DUO) SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

















def get_player_match_history(discord_id, limit=10):
    """VerilmiÅŸ oyunÃ§unun iÅŸtirak etdiyi son matÃ§larÄ± qaytarÄ±r (É™n yenidÉ™n kÃ¶hnÉ™yÉ™)."""
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, match_type, played_at, match_number, winner_ids, loser_ids, "
        "winner_elo_before, winner_elo_after, loser_elo_before, loser_elo_after, "
        "winner_kills, winner_assists, winner_deaths, loser_kills, loser_assists, loser_deaths "
        "FROM match_history ORDER BY played_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    def _load(json_str):
        return _json.loads(json_str) if json_str else None

    results = []
    for row in rows:
        (mid, match_type, played_at, match_number, winner_ids_json, loser_ids_json,
         w_before_json, w_after_json, l_before_json, l_after_json,
         w_kills_json, w_assists_json, w_deaths_json, l_kills_json, l_assists_json, l_deaths_json) = row
        winner_ids = _json.loads(winner_ids_json)
        loser_ids = _json.loads(loser_ids_json)

        if discord_id in winner_ids:
            idx = winner_ids.index(discord_id)
            elo_before = _json.loads(w_before_json)[idx]
            elo_after = _json.loads(w_after_json)[idx]
            won = True
            kills_list, assists_list, deaths_list = _load(w_kills_json), _load(w_assists_json), _load(w_deaths_json)
        elif discord_id in loser_ids:
            idx = loser_ids.index(discord_id)
            elo_before = _json.loads(l_before_json)[idx]
            elo_after = _json.loads(l_after_json)[idx]
            won = False
            kills_list, assists_list, deaths_list = _load(l_kills_json), _load(l_assists_json), _load(l_deaths_json)
        else:
            continue

        results.append({
            "match_type": match_type,
            "played_at": played_at,
            "match_number": match_number,
            "won": won,
            "kills": kills_list[idx] if kills_list else None,
            "assists": assists_list[idx] if assists_list else None,
            "deaths": deaths_list[idx] if deaths_list else None,
            "elo_before": elo_before,
            "elo_after": elo_after,
            "elo_change": elo_after - elo_before,
        })

        if len(results) >= limit:
            break

    return results




def admin_set_player_field(discord_id, field, value):
    """
    Admin panel üçün: bir oyunçunun kimlik/valyuta sahəsini dəyişir (players cədvəli).
    field: 'so2_nick', 'so2_id', 'coins', 'zm_balance'. ELO/wins/losses/kills/assists/deaths
    üçün bax: admin_set_player_field_5v5 (bu sahələr artıq players_5v5-də saxlanılır).
    """
    allowed_fields = {"so2_nick", "so2_id", "coins", "zm_balance"}
    if field not in allowed_fields:
        return False
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE players SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()
    conn.close()
    return True


def admin_set_player_field_5v5(discord_id, field, value):
    """Admin panel üçün: bir oyunçunun 5v5 statistika sahəsini (players_5v5) dəyişir."""
    allowed_fields = {"elo", "wins", "losses", "kills", "assists", "deaths"}
    if field not in allowed_fields:
        return False
    ensure_5v5_stats_row(discord_id)
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE players_5v5 SET {field} = ? WHERE discord_id = ?", (value, discord_id))
    conn.commit()
    conn.close()
    return True


def get_player_stats_dict(discord_id):
    """generate_stats_card-ın gözlədiyi player_data formatında tam statistika."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT so2_nick, so2_id, elo, wins, losses, kills, assists, deaths, "
        "win_streak, max_streak, coins, zm_balance FROM players WHERE discord_id=?",
        (discord_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "nick": row[0], "so2_id": row[1], "elo": row[2], "wins": row[3], "losses": row[4],
        "kills": row[5], "assists": row[6], "deaths": row[7],
        "win_streak": row[8], "max_streak": row[9], "coins": row[10], "zm_balance": row[11]
    }


def get_recent_matches(limit=15):
    """Son matçları admin siyahısı üçün qaytarır (oyunçu nickləri ilə)."""
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT match_number, match_type, played_at, winner_ids, loser_ids, map "
        "FROM match_history ORDER BY played_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()

    results = []
    for match_number, match_type, played_at, winner_ids_json, loser_ids_json, map_name in rows:
        winner_ids = _json.loads(winner_ids_json)
        loser_ids = _json.loads(loser_ids_json)

        def _nicks(ids):
            names = []
            for did in ids:
                cursor.execute("SELECT so2_nick FROM players WHERE discord_id=?", (did,))
                r = cursor.fetchone()
                names.append(r[0] if r else str(did))
            return names

        results.append({
            "match_number": match_number, "match_type": match_type, "played_at": played_at,
            "winner_nicks": _nicks(winner_ids), "loser_nicks": _nicks(loser_ids), "map": map_name
        })

    conn.close()
    return results




def get_match_by_number(match_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, match_type, played_at, match_number, winner_ids, loser_ids, "
        "winner_elo_before, winner_elo_after, loser_elo_before, loser_elo_after, "
        "winner_kills, winner_assists, winner_deaths, loser_kills, loser_assists, loser_deaths, "
        "season_id "
        "FROM match_history WHERE match_number=? ORDER BY id DESC LIMIT 1",
        (match_number,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    import json as _json

    def _load(v):
        return _json.loads(v) if v is not None else None

    return {
        "id": row[0], "match_type": row[1], "played_at": row[2], "match_number": row[3],
        "winner_ids": _json.loads(row[4]), "loser_ids": _json.loads(row[5]),
        "winner_elo_before": _json.loads(row[6]), "winner_elo_after": _json.loads(row[7]),
        "loser_elo_before": _json.loads(row[8]), "loser_elo_after": _json.loads(row[9]),
        "winner_kills": _load(row[10]), "winner_assists": _load(row[11]), "winner_deaths": _load(row[12]),
        "loser_kills": _load(row[13]), "loser_assists": _load(row[14]), "loser_deaths": _load(row[15]),
        "season_id": row[16],
    }


def delete_match_and_revert(match_number):
    """
    Matçı silir, hər oyunçunun ELO-sunu elo_before-a qaytarır, wins/losses-i 1
    azaldır, VƏ matçın aid olduğu sezonun season_stats-ını da geri alır (bax:
    "sezon leaderboard ümumi ilə fərqlidir" insidenti — əvvəllər bura toxunulmurdu,
    silinən/dəyişdirilən matçlar sezon rəqəmlərində əbədi qalırdı). Köhnə (bu dəyişiklikdən
    əvvəlki) matçlarda season_id yoxdur — həmin halda season_stats toxunulmadan keçilir.
    Coin/kill-assist-death/nailiyyət (lifetime) dəyişiklikləri geri alınmır.
    Təsirlənən oyunçuların siyahısını qaytarır, tapılmasa None.
    `match_type`-a görə düzgün cədvələ (5v5 -> players_5v5, köhnə 2v2 tarixi
    qeydlər -> players) yazır ki, leaderboard/rank rolu ilə uyğunsuzluq yaranmasın.
    """
    match = get_match_by_number(match_number)
    if not match:
        return None

    table = "players_5v5" if match["match_type"] == "5v5" else "players"

    conn = _get_conn()
    cursor = conn.cursor()
    affected = []

    def _nick_for(did):
        cursor.execute("SELECT so2_nick FROM players WHERE discord_id=?", (did,))
        row = cursor.fetchone()
        return row[0] if row else str(did)

    if match["season_id"] is not None:
        w_kills = match["winner_kills"] or [0] * len(match["winner_ids"])
        w_assists = match["winner_assists"] or [0] * len(match["winner_ids"])
        w_deaths = match["winner_deaths"] or [0] * len(match["winner_ids"])
        for did, before, after, k, a, d in zip(
            match["winner_ids"], match["winner_elo_before"], match["winner_elo_after"], w_kills, w_assists, w_deaths
        ):
            add_season_stat(did, match["season_id"], kills=-k, assists=-a, deaths=-d, wins=-1,
                             elo_gained=-(after - before), mode=match["match_type"], cursor=cursor)

        l_kills = match["loser_kills"] or [0] * len(match["loser_ids"])
        l_assists = match["loser_assists"] or [0] * len(match["loser_ids"])
        l_deaths = match["loser_deaths"] or [0] * len(match["loser_ids"])
        for did, before, after, k, a, d in zip(
            match["loser_ids"], match["loser_elo_before"], match["loser_elo_after"], l_kills, l_assists, l_deaths
        ):
            add_season_stat(did, match["season_id"], kills=-k, assists=-a, deaths=-d, losses=-1,
                             elo_gained=-(after - before), mode=match["match_type"], cursor=cursor)

    for did, elo_before in zip(match["winner_ids"], match["winner_elo_before"]):
        cursor.execute(f"SELECT elo FROM {table} WHERE discord_id=?", (did,))
        row = cursor.fetchone()
        if not row:
            continue
        old_elo = row[0]
        cursor.execute(
            f"UPDATE {table} SET elo=?, wins=MAX(wins-1,0) WHERE discord_id=?",
            (elo_before, did)
        )
        affected.append({"discord_id": did, "nick": _nick_for(did), "old_elo": old_elo, "new_elo": elo_before})

    for did, elo_before in zip(match["loser_ids"], match["loser_elo_before"]):
        cursor.execute(f"SELECT elo FROM {table} WHERE discord_id=?", (did,))
        row = cursor.fetchone()
        if not row:
            continue
        old_elo = row[0]
        cursor.execute(
            f"UPDATE {table} SET elo=?, losses=MAX(losses-1,0) WHERE discord_id=?",
            (elo_before, did)
        )
        affected.append({"discord_id": did, "nick": _nick_for(did), "old_elo": old_elo, "new_elo": elo_before})

    cursor.execute("DELETE FROM match_history WHERE id=?", (match["id"],))
    cursor.execute("DELETE FROM scan_results WHERE match_number=?", (match_number,))
    conn.commit()
    conn.close()
    return affected


# ==================== STANDOFF MARKET / SKIN SISTEMI ====================

















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


def get_match_coin_total(discord_id, match_number):
    """Bu oyunçuya həmin matçla bağlı (reason='Matç No{X} ...') yazılmış bütün coin
    log-larının cəmini qaytarır — nəticə düzəlişində köhnə mükafatı geri almaq üçün."""
    conn = _get_conn()
    cursor = conn.cursor()
    pattern = f"Matç No{match_number} %"
    cursor.execute(
        "SELECT COALESCE(SUM(change),0) FROM coin_logs WHERE discord_id=? AND reason LIKE ?",
        (discord_id, pattern)
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


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










_BOOST_CARD_COLS = {"boost50": "boost50_cards", "boost100": "boost100_cards", "protect": "protect_cards"}






def consume_boost_card(discord_id, card_type, cursor=None):
    """Bir kart varsa 1 ədəd azaldıb True qaytarır, yoxdursa False.
    cursor verilsə (artıq açıq bir transaction daxilində çağırılırsa) YENİ connection
    AÇMIR — eyni cursor üzərində işləyir. Bu, update_team_elo/update_elo öz transaction-u
    açıq ikən nested-connection SQLite "database is locked" bug-ının qarşısını alır."""
    col = _BOOST_CARD_COLS[card_type]
    own_conn = None
    if cursor is None:
        own_conn = _get_conn()
        cursor = own_conn.cursor()
    cursor.execute(f"SELECT {col} FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        if own_conn:
            own_conn.close()
        return False
    cursor.execute(f"UPDATE players SET {col} = {col} - 1 WHERE discord_id = ?", (discord_id,))
    if own_conn:
        own_conn.commit()
        own_conn.close()
    return True


def apply_elo_modifiers(discord_id, elo_change, cursor=None):
    """cursor verilsə (bax: consume_boost_card qeydi) eyni transaction üzərində işləyir."""
    own_conn = None
    if cursor is None:
        own_conn = _get_conn()
        cursor = own_conn.cursor()
    try:
        if elo_change > 0:
            for bt in ("boost_100", "boost_50"):
                b = get_active_boost(discord_id, bt, cursor=cursor)
                if b:
                    return round(elo_change * b["multiplier"])
            # Marketdən alınan, dövrü/vaxt-əsaslı olmayan, tək-istifadəlik kartlar
            if consume_boost_card(discord_id, "boost100", cursor=cursor):
                return round(elo_change * 2.0)
            if consume_boost_card(discord_id, "boost50", cursor=cursor):
                return round(elo_change * 1.5)
        elif elo_change < 0:
            if get_active_boost(discord_id, "protection", cursor=cursor):
                return 0
            if consume_boost_card(discord_id, "protect", cursor=cursor):
                return 0
        return elo_change
    finally:
        if own_conn:
            own_conn.commit()
            own_conn.close()




def get_active_boost(discord_id, boost_type, cursor=None):
    import time
    own_conn = None
    if cursor is None:
        own_conn = _get_conn()
        cursor = own_conn.cursor()
    cursor.execute(
        "SELECT id, multiplier, expires_at FROM active_boosts WHERE discord_id = ? AND boost_type = ? AND expires_at > ?",
        (discord_id, boost_type, int(time.time()))
    )
    row = cursor.fetchone()
    if own_conn:
        own_conn.close()
    if not row:
        return None
    return {"id": row[0], "multiplier": row[1], "expires_at": row[2]}




# ═══════════════════════════════════════════════════════════════════════════════
# KILLS / ASSISTS / DEATHS
# ═══════════════════════════════════════════════════════════════════════════════

def add_combat_stats(discord_id, kills=0, assists=0, deaths=0):
    """5v5 matçdan sonra çağırılır (bax: MatchResultView5v5._finish) — ona görə `players_5v5`-ə
    yazır. (Əvvəllər səhvən `players`-ə yazırdı — /profile, website və `players_5v5`-dən oxuyan
    hər yer bunu HEÇ görmürdü; bax: migrate_combat_stats_to_5v5 bu köhnə datanı bərpa edir.)"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE players_5v5 SET kills=kills+?, assists=assists+?, deaths=deaths+? WHERE discord_id=?",
        (kills, assists, deaths, discord_id)
    )
    conn.commit()
    conn.close()


def get_combat_stats(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT kills, assists, deaths FROM players_5v5 WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return {"kills": row[0], "assists": row[1], "deaths": row[2]} if row else {"kills": 0, "assists": 0, "deaths": 0}


def migrate_combat_stats_to_5v5():
    """Birdəfəlik miqrasiya: `add_combat_stats`-ın əvvəlki (səhv) hədəfi olan köhnə
    `players.kills/assists/deaths` sayğaclarını `players_5v5`-ə köçürür ki, indiyə qədər
    oynanılmış bütün matçların K/A/D-si /profile və saytda görünsün. Qeyd: `players.kills/
    assists/deaths` tarixən həm 2v2, həm 5v5 matçları eyni sayğacda toplayırdı (2v2 silinənə
    qədər) — bu ayrıla bilmədiyi üçün köçürülən rəqəm bəzi köhnə hesablarda əsl 5v5 K/A/D-dən
    bir qədər yüksək ola bilər, amma mövcud ən yaxşı məlumatdır (0-dan qat-qat dəqiqdir).
    Təsirlənən sətir sayını qaytarır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE players_5v5
        SET kills = (SELECT kills FROM players WHERE players.discord_id = players_5v5.discord_id),
            assists = (SELECT assists FROM players WHERE players.discord_id = players_5v5.discord_id),
            deaths = (SELECT deaths FROM players WHERE players.discord_id = players_5v5.discord_id)
        WHERE EXISTS (SELECT 1 FROM players WHERE players.discord_id = players_5v5.discord_id)
          AND kills = 0 AND assists = 0 AND deaths = 0
    """)
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


# ═══════════════════════════════════════════════════════════════════════════════
# SEASON SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

def get_or_create_current_season(mode="2v2"):
    """`mode`-a görə ayrıca sezon-nömrə qatarı saxlayır (2v2 və 5v5 paralel, müstəqil
    #1-dən başlayan sezon tarixçələridir)."""
    import datetime as dt
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, season_number, start_date, end_date FROM seasons WHERE status='active' AND mode=? ORDER BY id DESC LIMIT 1",
        (mode,)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return {"id": row[0], "season_number": row[1], "start_date": row[2], "end_date": row[3], "mode": mode}
    # Yeni sezon yarat
    now = dt.date.today()
    # Ayın 1-i başlayır, ayın son günü bitir
    start = now.replace(day=1).isoformat()
    if now.month == 12:
        end = now.replace(year=now.year+1, month=1, day=1).isoformat()
    else:
        end = now.replace(month=now.month+1, day=1).isoformat()
    cursor.execute("SELECT COALESCE(MAX(season_number),0)+1 FROM seasons WHERE mode=?", (mode,))
    season_num = cursor.fetchone()[0]
    cursor.execute("INSERT INTO seasons (season_number, mode, start_date, end_date, status) VALUES (?,?,?,?,'active')",
                   (season_num, mode, start, end))
    conn.commit()
    sid = cursor.lastrowid
    conn.close()
    return {"id": sid, "season_number": season_num, "start_date": start, "end_date": end, "mode": mode}


def get_season_by_number(season_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, season_number, start_date, end_date, status FROM seasons WHERE season_number=?", (season_number,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "season_number": row[1], "start_date": row[2], "end_date": row[3], "status": row[4]}


def add_season_stat(discord_id, season_id, kills=0, assists=0, deaths=0, wins=0, losses=0, elo_gained=0,
                     elo_start=0, mode="2v2", cursor=None):
    """cursor verilsə (bax: delete_match_and_revert) YENİ connection AÇMIR, eyni transaction
    üzərində işləyir — açıq bir yazı transaction-u davam edərkən ayrı connection ilə UPDATE
    cəhdi SQLite-da kilidlənməyə səbəb ola bilər (bax: consume_boost_card-dakı eyni qeyd).
    Mənfi dəyərlər vermək (kills=-k, wins=-1 və.s) əvvəlki əlavəni DÜZGÜN geri qaytarır,
    çünki toplama additiv işləyir."""
    own_conn = None
    if cursor is None:
        own_conn = _get_conn()
        cursor = own_conn.cursor()
    cursor.execute("""
        INSERT INTO season_stats (discord_id, season_id, mode, elo_start, elo_gained, kills, assists, deaths, wins, losses)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(discord_id, season_id) DO UPDATE SET
            elo_gained=elo_gained+excluded.elo_gained,
            kills=kills+excluded.kills,
            assists=assists+excluded.assists,
            deaths=deaths+excluded.deaths,
            wins=wins+excluded.wins,
            losses=losses+excluded.losses
    """, (discord_id, season_id, mode, elo_start, elo_gained, kills, assists, deaths, wins, losses))
    if own_conn:
        own_conn.commit()
        own_conn.close()


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


def backfill_season_from_lifetime(season_id, mode="5v5"):
    """Sezon statistikasını players_5v5-dəki ÖMÜRLÜK (lifetime) rəqəmlərlə TAM uyğunlaşdırır.
    Sezon 1 serverin İLK sezonu olduğu üçün (ondan əvvəl heç bir sezon yoxdur), ümumi və sezon
    leaderboard-ların eyni şeyi göstərməsi məntiqlidir — bax: "ikisi fərqlidir" sualı. Hər
    oyunçunun season_stats sətrini ƏLAVƏ ETMİR, DİRECT ƏVƏZ EDİR (idempotent — neçə dəfə
    işə salınsa da nəticə eynidir). elo_gained = cari elo - 1000 (standart başlanğıc ELO)."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT discord_id, elo, wins, losses, kills, assists, deaths FROM players_5v5")
    rows = cursor.fetchall()
    for discord_id, elo, wins, losses, kills, assists, deaths in rows:
        cursor.execute("""
            INSERT INTO season_stats (discord_id, season_id, mode, elo_start, elo_gained, kills, assists, deaths, wins, losses)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(discord_id, season_id) DO UPDATE SET
                mode=excluded.mode, elo_start=excluded.elo_start, elo_gained=excluded.elo_gained,
                kills=excluded.kills, assists=excluded.assists, deaths=excluded.deaths,
                wins=excluded.wins, losses=excluded.losses
        """, (discord_id, season_id, mode, 1000, elo - 1000, kills, assists, deaths, wins, losses))
    conn.commit()
    conn.close()
    return len(rows)






def close_season(season_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE seasons SET status='completed' WHERE id=?", (season_id,))
    conn.commit()
    conn.close()


def reset_all_players_for_new_season(mode="2v2", base_elo=1000):
    """Yeni sezon başlayanda oyunçuların RƏQABƏT statistikasını sıfırlayır:
    ELO, wins, losses, kills, assists, deaths, win_streak, loss_streak. Karyera
    rekordları (peak_elo, max_streak, created_at və s.) TOXUNULMAZ qalır — bunlar
    sezonlar arası davam edən lifetime nailiyyətlərdir, season_stats cədvəli isə
    (add_season_stat vasitəsilə artıq hər matçda ayrıca yazılır) bu sıfırlamadan
    asılı olmadan hər sezonun tam tarixçəsini saxlayır. `mode="5v5"` olanda YALNIZ
    `players_5v5` cədvəli sıfırlanır — 2v2 statistikasına TOXUNULMUR."""
    table = "players_5v5" if mode == "5v5" else "players"
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table} SET elo=?, wins=0, losses=0, kills=0, assists=0, deaths=0, "
        "win_streak=0, loss_streak=0",
        (base_elo,)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


def get_completed_seasons(mode="2v2"):
    """Bağlanmış (keçmiş) sezonların siyahısını qaytarır — "zaman kapsulu" veb funksiyası üçün."""
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute(
        "SELECT id, season_number, start_date, end_date FROM seasons "
        "WHERE status='completed' AND mode=? ORDER BY season_number DESC",
        (mode,)
    )
    rows = cursor.fetchall(); conn.close()
    return [{"id": r[0], "season_number": r[1], "start_date": r[2], "end_date": r[3]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# AKTİV MATÇ KİLİDİ
# ═══════════════════════════════════════════════════════════════════════════════

_ACTIVE_MATCH_COLS = (
    "match_number, team_a, team_b, log_message_id, log_channel_id, thread_id, "
    "selected_map, created_at, captain_a_id, captain_b_id, team_a_ready, team_b_ready, "
    "is_golden, is_lightning, voice_a_id, voice_b_id, map_vetoed, veto_a_used, veto_b_used, mode"
)


def _row_to_active_match(row):
    import json as _json
    if not row:
        return None
    return {
        "match_number": row[0],
        "team_a": _json.loads(row[1]) if row[1] else [],
        "team_b": _json.loads(row[2]) if row[2] else [],
        "log_message_id": int(row[3]) if row[3] else None,
        "log_channel_id": int(row[4]) if row[4] else None,
        "thread_id": int(row[5]) if row[5] else None,
        "selected_map": row[6],
        "created_at": row[7],
        "captain_a_id": row[8],
        "captain_b_id": row[9],
        "team_a_ready": bool(row[10]),
        "team_b_ready": bool(row[11]),
        "is_golden": bool(row[12]),
        "is_lightning": bool(row[13]),
        "voice_a_id": int(row[14]) if row[14] else None,
        "voice_b_id": int(row[15]) if row[15] else None,
        "map_vetoed": _json.loads(row[16]) if len(row) > 16 and row[16] else [],
        "veto_a_used": bool(row[17]) if len(row) > 17 else False,
        "veto_b_used": bool(row[18]) if len(row) > 18 else False,
        "mode": row[19] if len(row) > 19 and row[19] else "2v2",
    }


def veto_map(match_number, is_team_a, new_map):
    """Kapitanın xəritə veto/reroll haqqını istifadə edir — o komandanın veto haqqını
    işarələyir, köhnə xəritəni vetolanmışlar siyahısına əlavə edir, yeni xəritəni təyin edir."""
    import json as _json
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute("SELECT selected_map, map_vetoed FROM active_match WHERE match_number=?", (match_number,))
    row = cursor.fetchone()
    if not row:
        conn.close(); return None
    old_map, vetoed_json = row
    vetoed = _json.loads(vetoed_json) if vetoed_json else []
    if old_map and old_map not in vetoed:
        vetoed.append(old_map)
    col = "veto_a_used" if is_team_a else "veto_b_used"
    cursor.execute(
        f"UPDATE active_match SET selected_map=?, map_vetoed=?, {col}=1 WHERE match_number=?",
        (new_map, _json.dumps(vetoed), match_number)
    )
    conn.commit(); conn.close()
    return new_map


def set_active_match(match_number, team_a_json=None, team_b_json=None,
                     log_message_id=None, log_channel_id=None, selected_map=None,
                     captain_a_id=None, captain_b_id=None, is_golden=False, is_lightning=False,
                     mode="2v2"):
    """Yeni aktiv matç sətri yaradır (paralel matçlar dəstəklənir — hər biri öz sətri).
    `mode` 2v2/5v5 matçlarının eyni cədvəldə qarışmadan yaşamasını təmin edir."""
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO active_match (match_number, team_a, team_b, log_message_id, log_channel_id, "
        "selected_map, created_at, captain_a_id, captain_b_id, team_a_ready, team_b_ready, "
        "is_golden, is_lightning, mode) VALUES (?,?,?,?,?,?,?,?,?,0,0,?,?,?)",
        (match_number, team_a_json, team_b_json,
         str(log_message_id) if log_message_id else None,
         str(log_channel_id) if log_channel_id else None,
         selected_map, int(time.time()), captain_a_id, captain_b_id,
         int(bool(is_golden)), int(bool(is_lightning)), mode)
    )
    conn.commit()
    conn.close()


def set_active_match_message(match_number, message_id, channel_id, thread_id=None):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE active_match SET log_message_id=?, log_channel_id=?, thread_id=? WHERE match_number=?",
        (str(message_id), str(channel_id), str(thread_id) if thread_id else None, match_number)
    )
    conn.commit()
    conn.close()


def set_active_match_voice(match_number, voice_a_id, voice_b_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE active_match SET voice_a_id=?, voice_b_id=? WHERE match_number=?",
        (str(voice_a_id) if voice_a_id else None, str(voice_b_id) if voice_b_id else None, match_number)
    )
    conn.commit()
    conn.close()


def set_match_ready(match_number, is_team_a: bool):
    conn   = _get_conn()
    cursor = conn.cursor()
    col = "team_a_ready" if is_team_a else "team_b_ready"
    cursor.execute(f"UPDATE active_match SET {col}=1 WHERE match_number=?", (match_number,))
    conn.commit()
    conn.close()


def clear_active_match(match_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_match WHERE match_number=?", (match_number,))
    conn.commit()
    conn.close()


def get_active_match(match_number):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {_ACTIVE_MATCH_COLS} FROM active_match WHERE match_number=?", (match_number,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_active_match(row)


def get_active_match_by_message_id(message_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {_ACTIVE_MATCH_COLS} FROM active_match WHERE log_message_id=?", (str(message_id),))
    row = cursor.fetchone()
    conn.close()
    return _row_to_active_match(row)


def get_all_active_matches():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {_ACTIVE_MATCH_COLS} FROM active_match")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_active_match(r) for r in rows]


def count_active_matches(mode=None):
    conn = _get_conn()
    cursor = conn.cursor()
    if mode is None:
        cursor.execute("SELECT COUNT(*) FROM active_match")
    else:
        cursor.execute("SELECT COUNT(*) FROM active_match WHERE mode=?", (mode,))
    n = cursor.fetchone()[0]
    conn.close()
    return n


def is_player_in_active_match(discord_id):
    import json as _json
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT team_a, team_b FROM active_match")
    rows = cursor.fetchall()
    conn.close()
    for team_a_json, team_b_json in rows:
        team_a = _json.loads(team_a_json) if team_a_json else []
        team_b = _json.loads(team_b_json) if team_b_json else []
        ids = {p["discord_id"] for p in team_a} | {p["discord_id"] for p in team_b}
        if discord_id in ids:
            return True
    return False


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



def get_current_win_streak(discord_id):
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT win_streak FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0




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











def is_banned(discord_id):
    """FACEIT (matchmaking) ban statusu — `banned_until` keçmişdirsə (müvəqqəti ban bitibsə)
    avtomatik `False` qaytarır, amma sətri özü sıfırlamır (bax: set_player_banned, ban qalıcı
    olmayanda sonrakı `set_player_banned(..., False)` çağırışı ilə təmizlənir)."""
    import time
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned, banned_until FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return False
    banned_until = row[1]
    if banned_until and banned_until > 0 and banned_until < int(time.time()):
        return False
    return True


def set_player_banned(discord_id, banned, until_ts=None):
    """FACEIT (matchmaking) ban təyin edir/qaldırır. `until_ts` verilməsə qalıcı ban olur."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE players SET is_banned=?, banned_until=? WHERE discord_id=?",
        (1 if banned else 0, until_ts or 0, discord_id)
    )
    conn.commit()
    conn.close()


def get_ban_info(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned, banned_until FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"is_banned": False, "banned_until": None}
    return {"is_banned": bool(row[0]), "banned_until": row[1] or None}


def add_warning(discord_id, reason, staff_id):
    """`staff_id` parametri `warnings.admin_id` sütununa yazılır — pre-existing cədvəl bu adı
    istifadə edir (bax: init_db-dəki "── Warnings ──" bölməsi)."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO warnings (discord_id, reason, admin_id, created_at) VALUES (?, ?, ?, ?)",
        (discord_id, reason, staff_id, int(time.time()))
    )
    conn.commit()
    conn.close()


def get_warnings(discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, reason, admin_id, created_at FROM warnings WHERE discord_id=? ORDER BY created_at DESC",
        (discord_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "reason": r[1], "staff_id": r[2], "created_at": r[3]} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# NAİLİYYƏTLƏR
# ═══════════════════════════════════════════════════════════════════════════════



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


def award_achievement(discord_id, achievement_id):
    """Oyunçuya nişan verir (idempotent — `player_achievements`-dəki UNIQUE(discord_id,
    achievement_id) sayəsində eyni nişan iki dəfə verilmir). Yeni veriləndə `True`, artıq
    var idisə `False` qaytarır (profil panelində "yeni nişan!" bildirişi üçün)."""
    import time
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO player_achievements (discord_id, achievement_id, earned_at) VALUES (?, ?, ?)",
        (discord_id, achievement_id, int(time.time()))
    )
    conn.commit()
    newly_awarded = cursor.rowcount > 0
    conn.close()
    return newly_awarded








def create_time_capsule_letter(discord_id, message, unlock_at):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO time_capsule_letters (discord_id, message, unlock_at, opened, created_at) VALUES (?,?,?,0,?)",
        (discord_id, message, unlock_at, int(__import__("time").time()))
    )
    conn.commit()
    letter_id = cursor.lastrowid
    conn.close()
    return letter_id


def get_time_capsule_letters(discord_id):
    """Oyunçunun bütün vaxt kapsulu məktublarını qaytarır (açıq/gözləyən/hazır)."""
    now = int(__import__("time").time())
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, message, unlock_at, opened FROM time_capsule_letters WHERE discord_id=? ORDER BY unlock_at ASC",
        (discord_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "message": r[1], "unlock_at": r[2], "opened": bool(r[3]), "ready": r[2] <= now and not r[3]}
        for r in rows
    ]


def mark_time_capsule_letter_opened(letter_id, discord_id):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE time_capsule_letters SET opened=1 WHERE id=? AND discord_id=? AND unlock_at<=?",
        (letter_id, discord_id, int(__import__("time").time()))
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_all_achievements():
    conn   = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, icon FROM achievements ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "icon": r[3]} for r in rows]




# ═══════════════════════════════════════════════════════════════════════════════
# FƏRDİ LƏQƏBLƏR (CUSTOM TITLES)
# ═══════════════════════════════════════════════════════════════════════════════









# ═══════════════════════════════════════════════════════════════════════════════
# QUEST ZƏNCİRLƏRİ
# ═══════════════════════════════════════════════════════════════════════════════












# ═══════════════════════════════════════════════════════════════════════════════
# ELO TARİXÇƏSİ + PİK ELO
# ═══════════════════════════════════════════════════════════════════════════════







# ═══════════════════════════════════════════════════════════════════════════════
# COİN TRANSFER
# ═══════════════════════════════════════════════════════════════════════════════



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


def get_daily_stats(day_start_ts, day_end_ts):
    conn   = _get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM match_history WHERE played_at >= ? AND played_at < ?",
        (day_start_ts, day_end_ts)
    )
    match_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM players WHERE created_at >= ? AND created_at < ?",
        (day_start_ts, day_end_ts)
    )
    new_players = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(k), 0) FROM (
            SELECT SUM(CAST(json_each.value AS INTEGER)) as k
            FROM scan_results sr, json_each(json_extract(sr.scan_data, '$[*].kills'))
            WHERE sr.confirmed=1 AND sr.created_at >= ? AND sr.created_at < ?
        )
    """, (day_start_ts, day_end_ts))
    try:
        total_kills = cursor.fetchone()[0] or 0
    except Exception:
        total_kills = 0

    cursor.execute("""
        SELECT p.so2_nick, COUNT(*) as cnt
        FROM match_history mh
        JOIN players p ON (mh.winner_ids LIKE '%'||p.discord_id||'%'
                        OR mh.loser_ids  LIKE '%'||p.discord_id||'%')
        WHERE mh.played_at >= ? AND mh.played_at < ?
        GROUP BY p.discord_id ORDER BY cnt DESC LIMIT 1
    """, (day_start_ts, day_end_ts))
    row = cursor.fetchone()
    top_player = (row[0], row[1]) if row else None

    conn.close()
    return {
        "match_count": match_count,
        "new_players": new_players,
        "total_kills": total_kills,
        "top_player": top_player,
    }








def get_meta(key, default=None):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_meta WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_meta(key, value):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bot_meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def get_player_count():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM players")
    n = cursor.fetchone()[0]
    conn.close()
    return n


def get_total_match_count():
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM match_history")
    n = cursor.fetchone()[0]
    conn.close()
    return n


















# ═══════════════════════════════════════════════════════════════════════════════
# ŞƏXSİ REKORDLAR
# ═══════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════
# MÜVVƏQƏTİ BAN
# ═══════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK GİRİŞ BONUSU
# ═══════════════════════════════════════════════════════════════════════════════






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




# ═══════════════════════════════════════════════════════════════════════════════
# MARKET ENDİRİM
# ═══════════════════════════════════════════════════════════════════════════════









# ═══════════════════════════════════════════════════════════════════════════════
# REFERRAL (DAVET) SiSTEMi
# ═══════════════════════════════════════════════════════════════════════════════

REFERRAL_REWARD_REG     = 200      # Qeydiyyat üçün coin
REFERRAL_REWARD_3MATCH  = 500      # 3 matç üçün coin
REFERRAL_BANNER_ID      = "banner_ambassador"   # 10 matç üçün xüsusi banner





















# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — BİLDİRİŞ TERCİHLƏRİ (Push DM / Həftəlik Xülasə)
# ═══════════════════════════════════════════════════════════════════════════════







# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — ŞÜBHƏLİ FƏALİYYƏT AŞKARLANMASI
# ═══════════════════════════════════════════════════════════════════════════════

SUSPICIOUS_COIN_GAIN_THRESHOLD = 400   # tək bir log yazısında bu qədər (və ya çox) coin qazancı
SUSPICIOUS_WINDOW_SECONDS = 3600       # bu vaxt aralığında
SUSPICIOUS_WINDOW_GAIN_THRESHOLD = 800 # cəmi bu qədər (və ya çox) coin qazanılırsa


def check_suspicious_activity(since_ts):
    """since_ts-dən bəri şübhəli coin qazanc naxışlarını aşkarlayır (admin bildirişi üçün).
    Qaytarır: [{"discord_id", "nick", "total_gain", "log_count"}]"""
    conn = _get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT discord_id, SUM(change), COUNT(*), MAX(change) FROM coin_logs "
        "WHERE created_at >= ? AND change > 0 GROUP BY discord_id",
        (since_ts,)
    )
    rows = cur.fetchall()
    flagged = []
    for discord_id, total_gain, log_count, max_single in rows:
        if max_single >= SUSPICIOUS_COIN_GAIN_THRESHOLD or total_gain >= SUSPICIOUS_WINDOW_GAIN_THRESHOLD:
            cur.execute("SELECT so2_nick FROM players WHERE discord_id=?", (discord_id,))
            nrow = cur.fetchone()
            flagged.append({
                "discord_id": discord_id, "nick": nrow[0] if nrow else "?",
                "total_gain": total_gain, "log_count": log_count, "max_single": max_single
            })
    conn.close()
    return flagged


# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — HƏRRACLAR (Auction House)
# ═══════════════════════════════════════════════════════════════════════════════














def get_activity_heatmap_grid(discord_id, days=90):
    """Son `days` gündə oyunçunun matçlarının həftənin günü × saat üzrə paylanması (AZ vaxtı).
    Qaytarır: 7x24 grid (sətir=weekday 0..6, sütun=saat 0..23), hər hüceyrə matç sayı."""
    import time, datetime as _dt
    since = int(time.time()) - days * 86400
    conn = _get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT played_at FROM match_history WHERE played_at >= ? AND "
        "(winner_ids LIKE ? OR loser_ids LIKE ?)",
        (since, f"%{discord_id}%", f"%{discord_id}%")
    )
    rows = cur.fetchall()
    conn.close()
    grid = [[0] * 24 for _ in range(7)]
    for (played_at,) in rows:
        az_dt = _dt.datetime.utcfromtimestamp(played_at) + _dt.timedelta(hours=4)
        grid[az_dt.weekday()][az_dt.hour] += 1
    return grid


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






def get_lang(discord_id: int) -> str:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("SELECT lang FROM players WHERE discord_id=?", (discord_id,))
    row = cur.fetchone(); conn.close()
    return (row[0] or 'az') if row else 'az'


def set_lang(discord_id: int, lang: str):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE players SET lang=? WHERE discord_id=?", (lang, discord_id))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — HƏFTƏLİK ŞƏXSİ XÜLASƏ (DM)
# ═══════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 3 — SƏS KANALI FƏALLIĞI (Ən Sosial reytinqi)
# ═══════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 4 — VEB: KOMANDA YOLDAŞI ŞƏBƏKƏSİ, MILESTONE, RISING STAR, RÜTBƏ BÖLGÜSÜ
# ═══════════════════════════════════════════════════════════════════════════════

def get_teammate_network(discord_id, limit=8):
    """Oyunçunun ən çox EYNİ KOMANDADA birlikdə oynadığı digər oyunçuları qaytarır:
    [{"discord_id", "nick", "games_together", "wins_together"}, ...] (ən çoxdan azına)."""
    import json as _json
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute("SELECT winner_ids, loser_ids FROM match_history")
    rows = cursor.fetchall()
    tally = {}
    for winner_json, loser_json in rows:
        for side_json, won in ((winner_json, True), (loser_json, False)):
            ids = _json.loads(side_json or "[]")
            if discord_id not in ids:
                continue
            for mate_id in ids:
                if mate_id == discord_id:
                    continue
                entry = tally.setdefault(mate_id, {"games": 0, "wins": 0})
                entry["games"] += 1
                if won:
                    entry["wins"] += 1
    candidates = []
    for mate_id, rec in tally.items():
        cursor.execute("SELECT so2_nick FROM players WHERE discord_id=?", (mate_id,))
        nrow = cursor.fetchone()
        candidates.append({
            "discord_id": mate_id, "nick": nrow[0] if nrow else "?",
            "games_together": rec["games"], "wins_together": rec["wins"]
        })
    conn.close()
    candidates.sort(key=lambda c: c["games_together"], reverse=True)
    return candidates[:limit]


def get_player_milestones(discord_id):
    """Etibarlı, artıq izlənilən sahələrdən (created_at/peak_elo/max_streak) və
    match_history-dən dərəcə (milestone) siyahısı qurur — ayrıca tarixi cədvələ
    ehtiyac yoxdur."""
    import json as _json
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute("SELECT created_at, peak_elo, max_streak FROM players WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    created_at, peak_elo, max_streak = row

    cursor.execute(
        "SELECT played_at, winner_ids, loser_ids FROM match_history WHERE "
        "winner_ids LIKE ? OR loser_ids LIKE ? ORDER BY played_at ASC",
        (f"%{discord_id}%", f"%{discord_id}%")
    )
    rows = cursor.fetchall()
    conn.close()

    first_match_at = None
    first_win_at = None
    for played_at, winner_json, loser_json in rows:
        winner_ids = _json.loads(winner_json or "[]")
        loser_ids = _json.loads(loser_json or "[]")
        if discord_id not in winner_ids and discord_id not in loser_ids:
            continue
        if first_match_at is None:
            first_match_at = played_at
        if discord_id in winner_ids and first_win_at is None:
            first_win_at = played_at
        if first_match_at is not None and first_win_at is not None:
            break

    return {
        "created_at": created_at, "first_match_at": first_match_at, "first_win_at": first_win_at,
        "peak_elo": peak_elo, "max_streak": max_streak,
    }


def get_player_momentum(discord_id):
    """Son 24 saatdakı NET ELO sürəti ("isti seriya" indeksi üçün) və oyunçunun
    tarixi orta qazanc/itki dəyərləri (What-If simulyatoru üçün) — eyni
    match_history keçidindən hər ikisi hesablanır, ayrıca sorğu lazım deyil."""
    import time as _time
    matches = get_player_match_history(discord_id, limit=300)
    if not matches:
        return None

    now = int(_time.time())
    cutoff_24h = now - 86400
    net_change_24h = 0
    match_count_24h = 0
    win_deltas = []
    loss_deltas = []
    for m in matches:
        if m["played_at"] >= cutoff_24h:
            net_change_24h += m["elo_change"]
            match_count_24h += 1
        if m["won"]:
            win_deltas.append(m["elo_change"])
        else:
            loss_deltas.append(m["elo_change"])

    avg_win_gain = round(sum(win_deltas) / len(win_deltas), 1) if win_deltas else 25.0
    avg_loss_amount = round(sum(loss_deltas) / len(loss_deltas), 1) if loss_deltas else -20.0
    heat_pct = max(0, min(100, round((net_change_24h / 150) * 100)))

    return {
        "net_change_24h": net_change_24h,
        "match_count_24h": match_count_24h,
        "heat_pct": heat_pct,
        "avg_win_gain": avg_win_gain,
        "avg_loss_amount": avg_loss_amount,
        "sample_size": len(matches),
    }


def get_rising_star(days=1):
    """Son `days` gündə ən çox NET ELO qazanan oyunçunu qaytarır (match_history-dəki
    hər matçın before/after ELO-suna əsasən) — {"discord_id","nick","elo_gain"} və ya None."""
    import time, json as _json
    since = int(time.time()) - days * 86400
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute(
        "SELECT winner_ids, loser_ids, winner_elo_before, winner_elo_after, "
        "loser_elo_before, loser_elo_after FROM match_history WHERE played_at >= ?",
        (since,)
    )
    rows = cursor.fetchall()
    gains = {}
    for winner_json, loser_json, w_before, w_after, l_before, l_after in rows:
        for ids_json, before_json, after_json in (
            (winner_json, w_before, w_after), (loser_json, l_before, l_after)
        ):
            ids = _json.loads(ids_json or "[]")
            before_list = _json.loads(before_json or "[]")
            after_list = _json.loads(after_json or "[]")
            for i, did in enumerate(ids):
                if i < len(before_list) and i < len(after_list):
                    gains[did] = gains.get(did, 0) + (after_list[i] - before_list[i])
    if not gains:
        conn.close()
        return None
    top_id, top_gain = max(gains.items(), key=lambda kv: kv[1])
    cursor.execute("SELECT so2_nick FROM players WHERE discord_id=?", (top_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or top_gain <= 0:
        return None
    return {"discord_id": top_id, "nick": row[0], "elo_gain": top_gain}


def get_rank_distribution():
    """Bütün qeydiyyatlı oyunçuların rütbə üzrə paylanmasını qaytarır: [{"name","color","count"}, ...]."""
    from visual_cards import RANKS
    conn = _get_conn(); cursor = conn.cursor()
    cursor.execute("SELECT elo FROM players")
    elos = [r[0] for r in cursor.fetchall()]
    conn.close()
    counts = {r[2]: 0 for r in RANKS}
    for elo in elos:
        for lo, hi, name, color, emoji in RANKS:
            if lo <= elo < hi:
                counts[name] += 1
                break
    return [{"name": r[2], "color": list(r[3]), "count": counts[r[2]]} for r in RANKS]




# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN ANALİTİKA PANELİ (mövcud /admin?key= veb dashboard-u üçün trend funksiyaları)
# ═══════════════════════════════════════════════════════════════════════════════

def get_economy_trend(days=30):
    """Son `days` gündə gündəlik qazanılan/xərclənən/net coin cəmləri (tarixə görə artan sıra).
    {"labels": [...], "earned": [...], "spent": [...], "net": [...]}"""
    import time, datetime as dt
    conn = _get_conn(); cur = conn.cursor()
    start = int(time.time()) - days * 86400
    cur.execute("SELECT created_at, change FROM coin_logs WHERE created_at >= ?", (start,))
    rows = cur.fetchall()
    conn.close()
    buckets = {}
    for ts, change in rows:
        day = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        b = buckets.setdefault(day, {"earned": 0, "spent": 0})
        if change > 0:
            b["earned"] += change
        else:
            b["spent"] += -change
    labels = sorted(buckets.keys())
    earned = [buckets[d]["earned"] for d in labels]
    spent = [buckets[d]["spent"] for d in labels]
    return {"labels": labels, "earned": earned, "spent": spent,
            "net": [e - s for e, s in zip(earned, spent)]}


def get_growth_stats(days=30):
    """Gündəlik yeni qeydiyyat sayı + o gün matç oynayan, qeydiyyatı bu pəncərədən ƏVVƏL
    olan ("geri dönən") unikal oyunçu sayı. {"labels":[...], "new_players":[...], "returning":[...]}"""
    import time, datetime as dt, json as _json
    conn = _get_conn(); cur = conn.cursor()
    start = int(time.time()) - days * 86400
    cur.execute("SELECT discord_id, created_at FROM players WHERE created_at >= ?", (start,))
    reg_rows = cur.fetchall()
    cur.execute("SELECT played_at, winner_ids, loser_ids FROM match_history WHERE played_at >= ?", (start,))
    match_rows = cur.fetchall()
    cur.execute("SELECT discord_id, created_at FROM players")
    all_created = dict(cur.fetchall())
    conn.close()

    new_by_day = {}
    for did, ts in reg_rows:
        day = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        new_by_day[day] = new_by_day.get(day, 0) + 1

    returning_by_day = {}
    for ts, winner_ids, loser_ids in match_rows:
        day = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        ids = _json.loads(winner_ids or "[]") + _json.loads(loser_ids or "[]")
        seen = returning_by_day.setdefault(day, set())
        for did in ids:
            created = all_created.get(int(did))
            if created is not None and created < start:
                seen.add(int(did))

    labels = sorted(set(new_by_day) | set(returning_by_day))
    return {
        "labels": labels,
        "new_players": [new_by_day.get(d, 0) for d in labels],
        "returning": [len(returning_by_day.get(d, set())) for d in labels],
    }


def get_match_volume_trend(days=30):
    """Gündəlik matç sayı seriyası, 2v2/5v5 ayrılıqda. {"labels":[...], "matches_2v2":[...], "matches_5v5":[...]}"""
    import time, datetime as dt
    conn = _get_conn(); cur = conn.cursor()
    start = int(time.time()) - days * 86400
    cur.execute("SELECT played_at, match_type FROM match_history WHERE played_at >= ?", (start,))
    rows = cur.fetchall()
    conn.close()
    by_day = {}
    for ts, mtype in rows:
        day = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        b = by_day.setdefault(day, {"2v2": 0, "5v5": 0})
        b["5v5" if mtype == "5v5" else "2v2"] += 1
    labels = sorted(by_day.keys())
    return {
        "labels": labels,
        "matches_2v2": [by_day[d]["2v2"] for d in labels],
        "matches_5v5": [by_day[d]["5v5"] for d in labels],
    }


def get_moderation_summary(days=30):
    """Aqreqat moderasiya statistikası: admin əməliyyat sayı, şübhəli coin-qazanc
    bayraqları (bax: check_suspicious_activity). Şikayət (reports) sistemi ləğv edilib —
    həmin sahələr həmişə 0 qaytarır (geriyə uyğunluq üçün saxlanılır)."""
    import time
    conn = _get_conn(); cur = conn.cursor()
    start = int(time.time()) - days * 86400
    cur.execute("SELECT COUNT(*) FROM admin_logs WHERE created_at >= ?", (start,))
    admin_actions = cur.fetchone()[0]
    conn.close()
    flagged = check_suspicious_activity(start)
    return {
        "total_reports": 0,
        "open_reports": 0,
        "admin_actions": admin_actions,
        "suspicious_flags": len(flagged),
        "suspicious_players": flagged[:10],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ÜMUMI SÖHBƏT XP / HƏFTƏLİK AKTİVLİK LÖVHƏSİ
# ═══════════════════════════════════════════════════════════════════════════════

CHAT_XP_PER_MESSAGE = 5
CHAT_XP_COOLDOWN_SECONDS = 30  # spam-la XP fermalaşdırmanın qarşısını almaq üçün


def add_chat_xp(discord_id, amount=CHAT_XP_PER_MESSAGE, cooldown_seconds=CHAT_XP_COOLDOWN_SECONDS):
    """Cooldown bitibsə XP verir və True qaytarır; hələ cooldown-dadırsa heç nə etmir,
    False qaytarır (spam-la XP fermalaşdırmanın qarşısını almaq üçün)."""
    import time
    now = int(time.time())
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT last_xp_at FROM chat_activity WHERE discord_id=?", (discord_id,))
    row = cursor.fetchone()
    if row and now - row[0] < cooldown_seconds:
        conn.close()
        return False
    if row:
        cursor.execute(
            "UPDATE chat_activity SET weekly_xp = weekly_xp + ?, total_xp = total_xp + ?, last_xp_at = ? "
            "WHERE discord_id = ?",
            (amount, amount, now, discord_id)
        )
    else:
        cursor.execute(
            "INSERT INTO chat_activity (discord_id, weekly_xp, total_xp, last_xp_at) VALUES (?,?,?,?)",
            (discord_id, amount, amount, now)
        )
    conn.commit()
    conn.close()
    return True


def get_chat_leaderboard(limit=10):
    """Cari həftənin XP-sinə görə sıralanmış aktivlik lövhəsi. [{"discord_id","nick","weekly_xp"}, ...]"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ca.discord_id, p.so2_nick, ca.weekly_xp FROM chat_activity ca "
        "JOIN players p ON p.discord_id = ca.discord_id "
        "WHERE ca.weekly_xp > 0 ORDER BY ca.weekly_xp DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"discord_id": r[0], "nick": r[1], "weekly_xp": r[2]} for r in rows]


def get_top_chat_activity():
    """Bu həftənin ən aktiv üzvünü qaytarır (yoxdursa None) — Bazar elanı üçün."""
    top = get_chat_leaderboard(limit=1)
    return top[0] if top else None


def reset_weekly_chat_xp():
    """Hər Bazar gecəsi elandan sonra çağırılır — həftəlik sayğacı sıfırlayır, `total_xp`
    (bütün-zamanlar) toxunulmaz qalır."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_activity SET weekly_xp = 0")
    conn.commit()
    conn.close()

