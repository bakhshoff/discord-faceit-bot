import sys
import io
import re

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import datetime
import random
import asyncio
import threading
from dotenv import load_dotenv
from database import (
    init_db, register_player, get_player,
    get_next_match_number,
    create_giveaway, get_due_giveaways, mark_giveaway_finished,
    set_active_match, clear_active_match, get_active_match, veto_map,
    set_active_match_message, set_match_ready,
    get_active_match_by_message_id, get_all_active_matches, count_active_matches,
    is_player_in_active_match, set_active_match_voice,
    add_combat_stats, get_combat_stats, record_match_history,
    save_scan_result, get_scan_result, confirm_scan,
    add_coins, get_coins,
    add_coin_log, get_coin_logs,
    get_streak_bonus,
    get_player_stats_dict, get_player_match_history,
    get_recent_matches, get_match_by_number, delete_match_and_revert, get_match_coin_total,
    admin_set_player_field, admin_set_player_field_5v5, log_admin_action, is_banned,
    get_map_stats, get_all_players,
    get_activity_stats, get_hourly_activity,
    get_daily_stats,
    get_meta, set_meta,
    get_player_count, get_total_match_count,
    get_lang, set_lang,
    get_inactive_unplayed_players, delete_player,
    reset_all_player_data,
    get_or_create_current_season, add_season_stat,
    get_season_stat, get_season_leaderboard, close_season,
    get_completed_seasons, reset_all_players_for_new_season,
    ensure_5v5_stats_row, get_player_5v5, get_player_stats_dict_5v5, update_team_elo_5v5,
    set_player_5v5_elo,
    update_streak_5v5, add_to_queue_5v5, remove_from_queue_5v5,
    queue_size_5v5, get_queue_list_5v5, clear_queue_5v5, pop_10_and_balance,
    get_leaderboard_5v5, get_leaderboard_5v5_alltime, get_all_players_5v5,
    check_suspicious_activity,
    add_chat_xp, get_chat_leaderboard, get_top_chat_activity, reset_weekly_chat_xp,
    create_ticket, get_open_ticket, get_ticket_by_channel, close_ticket,
)
from i18n import t, LANG_NAMES
from ai_chat import generate_daily_news, generate_personal_coach_report
import standoff2_news
from leaderboard_image import generate_leaderboard_image
from web_server import run_web_server
from profile_card import generate_profile_card
from match_card import generate_match_card
from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
from rules_card import generate_rules_card, generate_register_banner
from scan_system import ocr_scoreboard, match_to_registered, apply_defaults_for_missing
from visual_cards import (
    generate_coin_logs_card,
    generate_stats_card, generate_match_history_card,
    generate_map_stats_card,
    generate_activity_card, generate_elo_chart_card,
    generate_announcement_card, generate_chat_activity_card,
    RANKS, get_rank
)
import requests

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DATA_DIR = os.environ.get("DATA_DIR")
if DATA_DIR and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

if os.environ.get("RESET_DB_ON_BOOT") == "1":
    for _reset_fname in ("bot_database.db", "backup.json"):
        _reset_path = os.path.join(DATA_DIR or ".", _reset_fname)
        if os.path.exists(_reset_path):
            os.remove(_reset_path)
            print(f"[RESET] {_reset_path} silindi.", flush=True)

if os.environ.get("DIAGNOSE_KD") == "1":
    import sqlite3 as _sqlite3
    import json as _json_diag
    _dbp = os.path.join(DATA_DIR or ".", "bot_database.db")
    _c = _sqlite3.connect(_dbp)
    _cur = _c.cursor()
    _cur.execute("SELECT COUNT(*), COALESCE(SUM(kills),0), COALESCE(SUM(assists),0), COALESCE(SUM(deaths),0) FROM players")
    _p_count, _sum_k, _sum_a, _sum_d = _cur.fetchone()
    print(f"[DIAGNOSE] players={_p_count} sum_kills={_sum_k} sum_assists={_sum_a} sum_deaths={_sum_d}", flush=True)
    _cur.execute("SELECT COUNT(*) FROM match_history")
    print(f"[DIAGNOSE] match_history rows={_cur.fetchone()[0]}", flush=True)
    _cur.execute("SELECT COUNT(*), COALESCE(SUM(confirmed),0) FROM scan_results")
    _sr_total, _sr_confirmed = _cur.fetchone()
    print(f"[DIAGNOSE] scan_results total={_sr_total} confirmed={_sr_confirmed}", flush=True)
    _cur.execute("SELECT match_number, scan_data FROM scan_results WHERE confirmed=1 ORDER BY match_number")
    _recoverable = {}
    for _mn, _sd in _cur.fetchall():
        try:
            _parsed = _json_diag.loads(_sd)
        except Exception:
            continue
        for _k, _s in _parsed.items():
            try:
                _did = int(_k)
            except ValueError:
                continue
            r = _recoverable.setdefault(_did, [0, 0, 0])
            r[0] += _s.get("kills", 0)
            r[1] += _s.get("assists", 0)
            r[2] += _s.get("deaths", 0)
    print(f"[DIAGNOSE] recoverable_players_from_confirmed_scans={len(_recoverable)}", flush=True)
    for _did, (_k, _a, _d) in list(_recoverable.items())[:30]:
        _cur.execute("SELECT so2_nick, kills, assists, deaths FROM players WHERE discord_id=?", (_did,))
        _row = _cur.fetchone()
        print(f"[DIAGNOSE] player={_did} nick={_row[0] if _row else '?'} "
              f"current_kad=({_row[1] if _row else '?'},{_row[2] if _row else '?'},{_row[3] if _row else '?'}) "
              f"recoverable_kad=({_k},{_a},{_d})", flush=True)
    _c.close()

LOG_CHANNEL_ID = 1500790545172267028
LOG_CHANNEL_ID_5V5 = None
LOBBY_VOICE_ID = 1529228399464288456
PUBLIC_WEB_URL = os.environ.get("PUBLIC_WEB_URL", "https://discord-faceit-bot-production.up.railway.app")

MAX_PARALLEL_MATCHES = 2

SOCIAL_CHANNEL_ID = None
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@nextlevelaze",
    "tiktok": "https://www.tiktok.com/@nextlevelaz",
    "discord": "https://discord.gg/nextlevelaz",
    "shop": "https://zenithshop.up.railway.app/",
}

CATEGORY_ANNOUNCEMENTS_NAME = "📢 ANNOUNCEMENTS"
CATEGORY_GENERAL_NAME = "💬 COMMUNITY"
CATEGORY_5V5_NAME = "🎯 FACEIT 5V5"
CATEGORY_STAFF_NAME = "🛡️ STAFF"

MEMBER_ROLE_NAME = "NLA Member"

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

LOGO_PATH = "logo.jpg"
NEXTLEVELAZ_LOGO_PATH = "1fd03444-818d-4271-b35f-62fd17745199.jpg"
INACTIVE_REGISTRATION_DAYS = 3
AUDIT_LOG_CHANNEL_ID = None
STANDOFF2_NEWS_CHANNEL_ID = None
MATCH_HISTORY_CHANNEL_ID = None
SEASON_REWARD_CHANNEL_ID = None
JOIN_LEAVE_LOG_CHANNEL_ID = None

# ── Xəritə Veto ──────────────────────────────────────────────────────────────
MAP_VETO_MAX_REROLLS_PER_CAPTAIN = 1

GREEN_ACCENT = (95, 208, 122)
ACCENT_VIOLET = (138, 92, 230)
RED_ACCENT = (214, 69, 61)

# Matchmaking üçün açıq saatlar (Azərbaycan vaxtı, UTC+4)
QUEUE_OPEN_HOUR = 20   # 20:00
QUEUE_CLOSE_HOUR = 2   # 02:00

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


STAFF_ROLE_NAMES = {"founder", "admin"}


def _normalize_role_name(name: str) -> str:
    return re.sub(r"^[^a-zA-Z]+", "", name).strip().lower()


def is_staff(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    return any(_normalize_role_name(r.name) in STAFF_ROLE_NAMES
               for r in getattr(interaction.user, "roles", []))


def staff_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        return is_staff(interaction)
    return app_commands.check(predicate)


RANK_ROLE_NAMES_5V5 = {r[2] for r in RANKS}


async def _sync_rank_role_5v5(guild, discord_id, elo):
    """Oyunçunun ELO-suna uyğun rütbə rolunu təyin edir, köhnə rütbə rolunu çıxarır."""
    if not guild:
        return
    member = guild.get_member(discord_id)
    if not member:
        try:
            member = await guild.fetch_member(discord_id)
        except (discord.NotFound, discord.HTTPException):
            return
    rank_name, _color, _emoji = get_rank(elo)
    target_role = discord.utils.get(guild.roles, name=rank_name)
    if not target_role:
        return

    to_remove = [r for r in member.roles if r.name in RANK_ROLE_NAMES_5V5 and r.id != target_role.id]
    try:
        if to_remove:
            await member.remove_roles(*to_remove, reason="Rütbə yeniləndi")
        if target_role not in member.roles:
            await member.add_roles(target_role, reason="Rütbə yeniləndi")
    except discord.Forbidden:
        pass


async def _get_log_channel():
    """bot.get_channel keş boşluğu (məs. restart-dan dərhal sonra) səbəbindən None
    qaytarsa belə, fetch_channel ilə API-dən birbaşa çəkməyə çalışır — kritik
    bildirişlərin (matç hazır, gündəlik hesabat və s.) səssizcə itməməsi üçün."""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(LOG_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        print(f"[LOG_CHANNEL] Kanal tapılmadı: {LOG_CHANNEL_ID}", flush=True)
        return None


async def _get_log_channel_5v5():
    """`_get_log_channel`-in 5v5 analoqu — 5v5 matç nəticə düymələri bu kanala göndərilir."""
    if not LOG_CHANNEL_ID_5V5:
        return None
    channel = bot.get_channel(LOG_CHANNEL_ID_5V5)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(LOG_CHANNEL_ID_5V5)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_social_channel():
    channel = bot.get_channel(SOCIAL_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(SOCIAL_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        print(f"[SOCIAL_CHANNEL] Kanal tapılmadı: {SOCIAL_CHANNEL_ID}", flush=True)
        return None


async def _get_audit_log_channel():
    if not AUDIT_LOG_CHANNEL_ID:
        return None
    channel = bot.get_channel(AUDIT_LOG_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(AUDIT_LOG_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_standoff2_news_channel():
    if not STANDOFF2_NEWS_CHANNEL_ID:
        return None
    channel = bot.get_channel(STANDOFF2_NEWS_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(STANDOFF2_NEWS_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_match_history_channel():
    if not MATCH_HISTORY_CHANNEL_ID:
        return None
    channel = bot.get_channel(MATCH_HISTORY_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(MATCH_HISTORY_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_season_reward_channel():
    if not SEASON_REWARD_CHANNEL_ID:
        return None
    channel = bot.get_channel(SEASON_REWARD_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(SEASON_REWARD_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_join_leave_log_channel():
    if not JOIN_LEAVE_LOG_CHANNEL_ID:
        return None
    channel = bot.get_channel(JOIN_LEAVE_LOG_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(JOIN_LEAVE_LOG_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _post_audit_log(action, target_id, field, old_val, new_val, reason, admin_id):
    """log_admin_action ilə EYNİ anda çağırılır — DB-yə yazılan admin əməliyyatını canlı
    olaraq audit-log kanalına da göndərir. Kanal qurulmayıbsa sakitcə heç nə etmir."""
    channel = await _get_audit_log_channel()
    if not channel:
        return
    embed = discord.Embed(
        title=f"🛡️ Admin əməliyyatı: {action}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Admin", value=f"<@{admin_id}>", inline=True)
    if target_id:
        embed.add_field(name="Hədəf", value=f"<@{target_id}>", inline=True)
    if field:
        embed.add_field(name="Sahə", value=str(field), inline=True)
    if old_val is not None or new_val is not None:
        embed.add_field(name="Dəyişiklik", value=f"`{old_val}` → `{new_val}`", inline=False)
    if reason:
        embed.add_field(name="Səbəb", value=str(reason), inline=False)
    embed.timestamp = datetime.datetime.utcnow()
    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# KARYERA YOLU — Aylıq ELO Sezonları
# ═══════════════════════════════════════════════════════════════════════════════

_last_season_rotation_month = None


REWARDS_5V5_TOP3 = [3000, 2000, 1000]  # sezon sonu Top-3 Gold mükafatı


async def _rotate_season_for_mode(mode, rewards, lb_channel_id, channel_name_prefix):
    """Sezonu bağlayır, Top-3-ə Gold mükafatı verir, bunu xüsusi sezon-mükafat kanalında
    elan edir, statistikanı sıfırlayır, yeni sezon açır və leaderboard kanalının adını yeniləyir."""
    current = get_or_create_current_season(mode)
    leaderboard = get_season_leaderboard(current["id"], limit=3)
    mode_label = "5v5" if mode == "5v5" else "2v2"
    icon = "🎯" if mode == "5v5" else "🛤️"
    if leaderboard:
        lines = []
        for i, (nick, so2_id, elo_gained, kills, assists, deaths, wins, losses, discord_id) in enumerate(leaderboard):
            reward = rewards[i] if i < len(rewards) else 0
            if reward:
                new_bal = add_coins(discord_id, reward)
                add_coin_log(discord_id, reward, f"{mode_label} Sezon #{current['season_number']} Top-{i+1} mükafatı", "earn", new_bal)
            lines.append(f"**#{i+1}** {nick} — {'+' if elo_gained >= 0 else ''}{elo_gained} ELO ({wins}Q/{losses}M)"
                         + (f" 🎁 +{reward} Gold" if reward else ""))
        channel = await _get_season_reward_channel() or await _get_log_channel_5v5()
        if channel:
            progress_msg = await channel.send(f"⏳ {mode_label} sezonu yekunlaşdırılır...\n`░░░░░░░░░░░░░░░░░░░░` 0%")
            await _progress_step(progress_msg, 1, 3, "Mükafatlar hesablanır...")
            await asyncio.sleep(1.0)
            await _progress_step(progress_msg, 2, 3, "Bütün oyunçuların statistikası sıfırlanır...")
            await asyncio.sleep(1.0)
            await _progress_step(progress_msg, 3, 3, "Yeni sezon başlayır!")
            embed = discord.Embed(
                title=f"{icon} {mode_label} Sezon #{current['season_number']} başa çatdı!",
                description="\n".join(lines),
                color=discord.Color.from_rgb(138, 92, 230)
            )
            embed.set_footer(text=f"Bütün {mode_label} oyunçularının ELO/statistikası sıfırlandı — yeni sezon başladı.")
            await channel.send(embed=embed)
    close_season(current["id"])
    reset_all_players_for_new_season(mode=mode)
    new_season = get_or_create_current_season(mode)

    if lb_channel_id is not None:
        channel = bot.get_channel(lb_channel_id)
        if channel is not None:
            try:
                await channel.edit(name=f"{channel_name_prefix}-{new_season['season_number']}")
            except discord.Forbidden:
                pass


@tasks.loop(minutes=30)
async def season_rotation_loop():
    """Ayın 1-ində (AZ vaxtı ilə) 5v5 sezonunu bağlayıb yeni sezon açır — öz mükafat
    cədvəli və öz statistika cədvəli ilə (bax: _rotate_season_for_mode, reset_all_players_for_new_season).
    30 dəqiqəlik interval (bax: weekly_mvp_loop-dakı eyni izah) bot-un son restart vaxtından
    asılı olmadan ayın 1-i başlayan kimi tezliklə aşkarlanmasını təmin edir. Bayraq DB-də
    (get_meta/set_meta) saxlanılır — YALNIZ yaddaşda saxlansaydı, ayın 1-ində bot bir neçə dəfə
    restart olduqda (deploy və s.) hər restart eyni günü YENİDƏN rotasiya edərdi (sezon nömrəsi
    lazımsız yerə bir neçə dəfə artardı)."""
    global _last_season_rotation_month
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)  # AZ vaxtı
    if now.day != 1:
        return
    month_key = now.strftime("%Y-%m")
    if _last_season_rotation_month == month_key:
        return
    if get_meta("last_season_rotation_month") == month_key:
        _last_season_rotation_month = month_key
        return
    _last_season_rotation_month = month_key
    set_meta("last_season_rotation_month", month_key)

    await _rotate_season_for_mode("5v5", REWARDS_5V5_TOP3, leaderboard_channel_id_5v5, "leaderboard-5v5-sezon")


# ═══════════════════════════════════════════════════════════════════════════════
# STANDOFF 2 RƏSMİ YENİLİK XƏBƏRLƏRİ (help.standoff2.com izləmə)
# ═══════════════════════════════════════════════════════════════════════════════

STANDOFF2_NEWS_SEEN_META_KEY = "standoff2_seen_article_ids"


@tasks.loop(hours=6)
async def standoff2_news_loop():
    """help.standoff2.com/en-dəki 'Updates Description' bölməsini yoxlayır, yeni
    yenilik məqaləsi görünəndə tam mətnini çəkib AI ilə Azərbaycan dilinə çevirir və
    kanala göndərir. Sayt strukturu dəyişsə/əlçatan olmasa belə sakitcə keçib növbəti
    dövrdə yenidən cəhd edir — bot funksionallığına təsir etmir."""
    channel = await _get_standoff2_news_channel()
    if not channel:
        return
    try:
        articles = await asyncio.to_thread(standoff2_news.get_latest_update_articles, 5)
    except Exception as e:
        print(f"[STANDOFF2_NEWS] Kolleksiya səhifəsi çəkilə bilmədi: {e}", flush=True)
        return
    if not articles:
        return

    seen_raw = get_meta(STANDOFF2_NEWS_SEEN_META_KEY)
    if seen_raw is None:
        # İlk dəfə işə düşür — mövcud məqalələri "görülmüş" kimi işarələ, KEÇMİŞ elanları
        # göndərmə (yalnız BUNDAN SONRA çıxan yeniliklər elan olunacaq).
        set_meta(STANDOFF2_NEWS_SEEN_META_KEY, json.dumps([a["id"] for a in articles]))
        return

    try:
        seen_ids = set(json.loads(seen_raw))
    except (TypeError, ValueError):
        seen_ids = set()

    new_articles = [a for a in articles if a["id"] not in seen_ids]
    if not new_articles:
        return

    for article in reversed(new_articles):  # köhnədən yeniyə doğru elan et
        try:
            title, text = await asyncio.to_thread(standoff2_news.fetch_article_text, article["url"])
            summary = await asyncio.to_thread(standoff2_news.summarize_article_az, title, text)
        except Exception as e:
            print(f"[STANDOFF2_NEWS] Məqalə çəkilə bilmədi ({article['url']}): {e}", flush=True)
            continue
        if not summary:
            continue
        embed = discord.Embed(
            title=f"🎮 {title}",
            description=summary,
            color=discord.Color.from_rgb(138, 92, 230),
            url=article["url"]
        )
        embed.set_footer(text="Mənbə: help.standoff2.com — Nextlevelaz avtomatik tərcümə")
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as e:
            print(f"[STANDOFF2_NEWS] Kanala göndərilə bilmədi: {e}", flush=True)
        seen_ids.add(article["id"])

    set_meta(STANDOFF2_NEWS_SEEN_META_KEY, json.dumps(list(seen_ids)))


# ═══════════════════════════════════════════════════════════════════════════════
# ŞÜBHƏLİ FƏALİYYƏT XƏBƏRDARLIĞI
# ═══════════════════════════════════════════════════════════════════════════════

@tasks.loop(hours=1)
async def suspicious_activity_loop():
    since_ts = int((datetime.datetime.utcnow() - datetime.timedelta(hours=1)).timestamp())
    flagged = check_suspicious_activity(since_ts)
    if not flagged:
        return
    channel = await _get_audit_log_channel()
    if not channel:
        return
    embed = discord.Embed(
        title="⚠️ Şübhəli fəaliyyət aşkarlandı",
        description="Son 1 saatda qeyri-adi coin qazancı olan oyunçular:",
        color=discord.Color.red()
    )
    for f in flagged[:10]:
        embed.add_field(
            name=f["nick"],
            value=f"Cəmi qazanc: **{f['total_gain']}** coin ({f['log_count']} əməliyyat, ən böyüyü {f['max_single']})",
            inline=False
        )
    await channel.send(embed=embed)




def is_queue_open():
    return True
    az_time = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    hour = az_time.hour
    if QUEUE_OPEN_HOUR > QUEUE_CLOSE_HOUR:
        return hour >= QUEUE_OPEN_HOUR or hour < QUEUE_CLOSE_HOUR
    return QUEUE_OPEN_HOUR <= hour < QUEUE_CLOSE_HOUR


leaderboard_channel_id_5v5 = None
leaderboard_message_id_5v5 = None
queue_status_channel_id_5v5 = None
queue_status_message_id_5v5 = None


LEADERBOARD_IMAGE_PATH_5V5 = "leaderboard_5v5.png"


async def _update_live_board_message_5v5(change_note=None):
    """`_update_live_board_message`-in 5v5 analoqu."""
    if leaderboard_channel_id_5v5 is None or leaderboard_message_id_5v5 is None:
        return
    channel = bot.get_channel(leaderboard_channel_id_5v5)
    if channel is None:
        return
    rows = get_leaderboard_5v5(10)
    if not rows:
        return
    lines = [f"{i+1}. **{r[0]}** — {r[2]} ELO ({r[3]}Q/{r[4]}M)" for i, r in enumerate(rows)]
    content = (
        "🎯 **Nextlevelaz FACEIT 5v5 Leaderboard** — hər 60 saniyədə avtomatik yenilənir "
        "(bu şəkil Top-20-ni göstərir).\n"
        f"🌐 Bütün oyunçuların tam, axtarışlı siyahısı üçün vebsaytımıza baxın: {PUBLIC_WEB_URL}\n\n"
        "📊 **Top 10 (canlı):**\n" + "\n".join(lines)
    )
    if change_note:
        content += f"\n\n🔄 {change_note}"
    content += f"\n\n🕒 Son yeniləmə: <t:{int(datetime.datetime.utcnow().timestamp())}:R>"
    try:
        message = await channel.fetch_message(leaderboard_message_id_5v5)
        await message.edit(content=content)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


@tasks.loop(seconds=60)
async def refresh_leaderboard_5v5():
    global leaderboard_message_id_5v5
    if leaderboard_channel_id_5v5 is None or leaderboard_message_id_5v5 is None:
        return
    channel = bot.get_channel(leaderboard_channel_id_5v5)
    if channel is None:
        return
    rows = get_leaderboard_5v5(20)
    generate_leaderboard_image(rows, LEADERBOARD_IMAGE_PATH_5V5)
    try:
        message = await channel.fetch_message(leaderboard_message_id_5v5)
        await message.edit(attachments=[discord.File(LEADERBOARD_IMAGE_PATH_5V5, filename="leaderboard_5v5.png")])
    except discord.NotFound:
        pass


@tasks.loop(seconds=30)
async def check_giveaways():
    now_unix = int(datetime.datetime.utcnow().timestamp())
    due = get_due_giveaways(now_unix)
    for giveaway_id, mukafat, winner_id, channel_id, message_id in due:
        mark_giveaway_finished(giveaway_id)
        channel = bot.get_channel(channel_id)
        if channel is None:
            continue
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            continue

        guild = channel.guild
        actual_winner_id = winner_id

        if winner_id == 0:
            reactors = []
            for reaction in message.reactions:
                if str(reaction.emoji) != "🎉":
                    continue
                async for user in reaction.users():
                    if not user.bot:
                        reactors.append(user.id)
                break
            if not reactors:
                no_winner_embed = discord.Embed(
                    title="🎉 GIVEAWAY BİTDİ 🎉",
                    description=f"**Mükafat:** {mukafat}\n\n❌ Heç kim 🎉 reaksiyası vermədi, qalib təyin olunmadı.",
                    color=discord.Color.red()
                )
                no_winner_embed.set_footer(text="Nextlevelaz")
                try:
                    await message.edit(embed=no_winner_embed)
                except discord.HTTPException:
                    pass
                continue
            actual_winner_id = random.choice(reactors)

        winner_member = guild.get_member(actual_winner_id) if guild else None
        winner_mention = winner_member.mention if winner_member else f"<@{actual_winner_id}>"

        final_embed = discord.Embed(
            title="🎉 GIVEAWAY BİTDİ 🎉",
            description=f"**Mükafat:** {mukafat}\n\n🏆 Qalib: {winner_mention}\n\nTəbriklər!",
            color=discord.Color.green()
        )
        final_embed.set_footer(text="Nextlevelaz")
        try:
            await message.edit(embed=final_embed)
        except discord.HTTPException:
            pass
        await channel.send(f"🎉 Təbriklər {winner_mention}! Sən **{mukafat}** qazandın!")


STUCK_MATCH_THRESHOLD_SECONDS = 600
_warned_match_numbers = set()


@tasks.loop(seconds=120)
async def check_stuck_matches():
    active_matches = get_all_active_matches()
    active_numbers = {m["match_number"] for m in active_matches}
    _warned_match_numbers.intersection_update(active_numbers)

    for active in active_matches:
        if not active.get("created_at"):
            continue
        match_number = active["match_number"]
        age = int(datetime.datetime.utcnow().timestamp()) - active["created_at"]
        if age < STUCK_MATCH_THRESHOLD_SECONDS or match_number in _warned_match_numbers:
            continue

        _warned_match_numbers.add(match_number)
        log_channel = await _get_log_channel()
        if not log_channel:
            continue
        minutes = age // 60
        embed = discord.Embed(
            title=f"⚠️ Matç No{match_number} {minutes} dəqiqədir davam edir",
            description=(
                "Hazır olma/nəticə mərhələsində asılı qalıb ola bilər.\n"
                f"`/admin_matc_netice matc_no:{match_number}` ilə nəticə düymələrini yenidən göstərə bilərsiniz."
            ),
            color=discord.Color.red()
        )
        await log_channel.send(embed=embed)


@tasks.loop(time=datetime.time(hour=20, minute=0, tzinfo=datetime.timezone.utc))
async def daily_report_loop():
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    ended_az_date = now_utc.date()
    new_az_date = ended_az_date + datetime.timedelta(days=1)

    # ── Günlük hesabat (bitən AZ günü üçün) ──────────────────────────────────
    date_str = str(ended_az_date)
    if get_meta("last_daily_report_date") != date_str:
        set_meta("last_daily_report_date", date_str)
        day_end_ts = int(now_utc.timestamp())
        day_start_ts = day_end_ts - 86400
        stats = get_daily_stats(day_start_ts, day_end_ts)

        # ── Qeydiyyatdan 3+ gün keçib, heç bir matç oynamayanları təmizlə ────
        inactive_cutoff_ts = day_end_ts - INACTIVE_REGISTRATION_DAYS * 86400
        inactive_players = get_inactive_unplayed_players(inactive_cutoff_ts)
        for p in inactive_players:
            delete_player(p["discord_id"])

        log_channel = await _get_log_channel()
        if log_channel:
            embed = discord.Embed(
                title=f"📋 Günlük hesabat — {ended_az_date.strftime('%d.%m.%Y')}",
                color=discord.Color.blurple()
            )
            embed.add_field(name="🎮 Matç sayı", value=str(stats["match_count"]), inline=True)
            embed.add_field(name="🆕 Yeni qeydiyyat", value=str(stats["new_players"]), inline=True)
            embed.add_field(name="💥 Ümumi kill", value=str(stats["total_kills"]), inline=True)
            if stats["top_player"]:
                embed.add_field(
                    name="🔥 Günün ən aktiv oyunçusu",
                    value=f"{stats['top_player'][0]} ({stats['top_player'][1]} matç)",
                    inline=False
                )
            if inactive_players:
                embed.add_field(
                    name="🗑️ Qeydiyyat təmizliyi",
                    value=(
                        f"{len(inactive_players)} oyunçu qeydiyyatdan {INACTIVE_REGISTRATION_DAYS} gün "
                        f"keçməsinə baxmayaraq heç bir matç oynamadığı üçün qeydiyyatı silindi "
                        f"(istəsə yenidən qeydiyyatdan keçə bilər)"
                    ),
                    inline=False
                )
            await log_channel.send(embed=embed)

            news_text = await asyncio.to_thread(generate_daily_news, stats)
            if news_text:
                news_embed = discord.Embed(
                    title="📰 Nextlevelaz Xəbərləri",
                    description=news_text,
                    color=discord.Color.from_rgb(138, 92, 230)
                )
                news_embed.set_footer(text="Nextlevelaz")
                await log_channel.send(embed=news_embed)


_status_index = 0


@tasks.loop(minutes=5)
async def rotate_status_loop():
    global _status_index
    texts = [
        f"👀 {get_player_count()} qeydiyyatlı oyunçu",
        f"🎮 {get_total_match_count()} matç oynanılıb",
    ]

    text = texts[_status_index % len(texts)]
    _status_index += 1
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=text))
    except Exception:
        pass


class SocialLinksView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="YouTube", emoji="▶️", style=discord.ButtonStyle.link, url=SOCIAL_LINKS["youtube"]))
        self.add_item(discord.ui.Button(label="TikTok", emoji="🎵", style=discord.ButtonStyle.link, url=SOCIAL_LINKS["tiktok"]))
        self.add_item(discord.ui.Button(label="Discord", emoji="💬", style=discord.ButtonStyle.link, url=SOCIAL_LINKS["discord"]))
        self.add_item(discord.ui.Button(label="NextlevelazShop", emoji="🛒", style=discord.ButtonStyle.link, url=SOCIAL_LINKS["shop"]))


SOCIAL_REMINDER_TEXTS = [
    "Nextlevelaz icmasının bir hissəsi olduğunuz üçün təşəkkürlər! Bizi sosial mediada da izləyin ki, "
    "turnir elanlarını, canlı yayımları və xüsusi endirimləri qaçırmayasınız.",
    "Bilirdinizmi? Bizim YouTube və TikTok hesablarımızda ən gözəl anlar, matç xülasələri və məsləhətlər paylaşılır. "
    "Bir kliklə izləyin, geridə qalmayın!",
    "NextlevelazShop-da xüsusi əşyalar sizi gözləyir! Aşağıdakı düymələrdən bizim bütün platformalarımıza baş çəkə bilərsiniz.",
]
_social_index = 0


@tasks.loop(minutes=60)
async def social_reminder_loop():
    global _social_index
    channel = bot.get_channel(SOCIAL_CHANNEL_ID)
    if not channel:
        try:
            channel = await bot.fetch_channel(SOCIAL_CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            print(f"[SOCIAL] Kanal tapılmadı: {SOCIAL_CHANNEL_ID}", flush=True)
            return

    try:
        last_messages = [msg async for msg in channel.history(limit=1)]
    except discord.HTTPException:
        return
    if last_messages and last_messages[0].author.id == bot.user.id:
        return

    text = SOCIAL_REMINDER_TEXTS[_social_index % len(SOCIAL_REMINDER_TEXTS)]
    _social_index += 1

    embed = discord.Embed(
        title="📢 Nextlevelaz — Bizi izləyin!",
        description=text,
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.add_field(name="▶️ YouTube", value=SOCIAL_LINKS["youtube"], inline=False)
    embed.add_field(name="🎵 TikTok", value=SOCIAL_LINKS["tiktok"], inline=False)
    embed.add_field(name="💬 Discord", value=SOCIAL_LINKS["discord"], inline=False)
    embed.add_field(name="🛒 NextlevelazShop", value=SOCIAL_LINKS["shop"], inline=False)
    embed.set_footer(text="Nextlevelaz")
    if os.path.exists(LOGO_PATH):
        try:
            file = discord.File(LOGO_PATH, filename="logo.jpg")
            embed.set_thumbnail(url="attachment://logo.jpg")
            await channel.send(embed=embed, view=SocialLinksView(), file=file)
            return
        except Exception:
            pass
    await channel.send(embed=embed, view=SocialLinksView())


class RegisterModal(discord.ui.Modal, title="FACEIT Qeydiyyat"):
    so2_id = discord.ui.TextInput(
        label="Standoff 2 ID",
        placeholder="Məsələn: 123456789",
        required=True,
        max_length=50
    )
    nick = discord.ui.TextInput(
        label="Faceit adı / oyundakı ad",
        placeholder="Oyundakı adınızı yazın",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        success = register_player(interaction.user.id, str(self.nick), str(self.so2_id))
        if success:
            ensure_5v5_stats_row(interaction.user.id)
            embed = discord.Embed(
                title="✅ Qeydiyyat tamamlandı!",
                description=f"**Nick:** {self.nick}\n**ID:** {self.so2_id}\n**Başlanğıc ELO:** 1000",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Siz artıq qeydiyyatdan keçmisiniz! `/profile` ilə baxa bilərsiniz.",
                ephemeral=True
            )


class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Qeydiyyat", style=discord.ButtonStyle.success, emoji="✅", custom_id="reg_open")
    async def open_register(self, interaction: discord.Interaction, button: discord.ui.Button):
        if get_meta("registration_open") == "0":
            await interaction.response.send_message("❌ Qeydiyyat hazırda bağlıdır.", ephemeral=True)
            return
        existing = get_player(interaction.user.id)
        if existing:
            await interaction.response.send_message(
                "⚠️ Siz artıq qeydiyyatdan keçmisiniz! `/profile` ilə baxa bilərsiniz.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(RegisterModal())


async def _progress_step(message, step, total, label):
    """Uzun proseslərdə (full_setup, sezon rotasiyası) saxta 'yüklənmə' effekti —
    mesaj ardıcıl redaktə olunaraq vizual irəliləyiş zolağı göstərir."""
    if not message:
        return
    filled = round(step / total * 20)
    bar = "▓" * filled + "░" * (20 - filled)
    pct = round(step / total * 100)
    try:
        await message.edit(content=f"⏳ {label}\n`{bar}` {pct}%")
    except discord.HTTPException:
        pass


def _build_match_status_embed(active):
    """Matç kartının yanında göstərilən 'canlı status' embedi — komanda hazırlığı,
    xəritə və səs kanalı vəziyyəti dəyişdikcə yenidən redaktə olunur (bax:
    TeamReadyView._set_ready/_veto, _start_one_match)."""
    embed = discord.Embed(
        title=f"📋 Matç No{active['match_number']} — Canlı Status",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🔵 Komanda A", value="✅ Hazırdır" if active["team_a_ready"] else "⏳ Gözlənilir", inline=True)
    embed.add_field(name="🔴 Komanda B", value="✅ Hazırdır" if active["team_b_ready"] else "⏳ Gözlənilir", inline=True)
    embed.add_field(name="🗺️ Xəritə", value=active["selected_map"] or "?", inline=True)
    voice_ready = bool(active.get("voice_a_id")) and bool(active.get("voice_b_id"))
    embed.add_field(name="🎙️ Səs kanalları", value="✅ Hazır" if voice_ready else "⏳ Hazırlanır", inline=True)
    return embed


class TeamReadyView5v5(discord.ui.View):
    """`TeamReadyView`-in 5v5 analoqu — 10 oyunçu-info düyməsi (5+5, hər komanda öz sırasında),
    ready/veto/ləğv düymələri Discord-un 5-sıra limitinə tam sığacaq şəkildə yerləşdirilib."""

    def __init__(self, team_a=None, team_b=None):
        super().__init__(timeout=None)
        for row_idx, team in enumerate((team_a or [], team_b or [])):
            for i, p in enumerate(team[:5]):
                slot = row_idx * 5 + i
                btn = discord.ui.Button(
                    label=p["nick"][:80], style=discord.ButtonStyle.secondary,
                    custom_id=f"player_info_5v5_{slot}", row=row_idx
                )
                btn.callback = self._make_player_info_callback(slot)
                self.add_item(btn)

    def _make_player_info_callback(self, slot: int):
        async def _callback(interaction: discord.Interaction):
            active = await self._get_active_for_message(interaction)
            if not active:
                return
            roster = active["team_a"] + active["team_b"]
            if slot >= len(roster):
                await interaction.response.send_message("❌ Bu slot boşdur.", ephemeral=True)
                return
            target_id = roster[slot]["discord_id"]
            if not get_player(target_id):
                await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
                return
            stats5 = get_player_stats_dict_5v5(target_id)
            if not stats5:
                await interaction.response.send_message("❌ Bu oyunçunun hələ 5v5 statistikası yoxdur.", ephemeral=True)
                return
            card_path = os.path.join(DATA_DIR or ".", f"stats_5v5_{target_id}.png")
            await interaction.response.defer(ephemeral=True)
            achievements = []
            await asyncio.to_thread(generate_stats_card, stats5, achievements, card_path)
            await interaction.followup.send(file=discord.File(card_path, filename="stats_5v5.png"), ephemeral=True)
        return _callback

    async def _get_active_for_message(self, interaction: discord.Interaction):
        active = get_active_match_by_message_id(interaction.message.id)
        if not active:
            await interaction.response.send_message(
                "⚠️ Bu matç artıq aktual deyil (artıq bitib və ya ləğv olunub).", ephemeral=True
            )
            return None
        return active

    async def _set_ready(self, interaction: discord.Interaction, is_team_a: bool, button: discord.ui.Button):
        active = await self._get_active_for_message(interaction)
        if not active:
            return

        expected_captain_id = active["captain_a_id"] if is_team_a else active["captain_b_id"]
        if interaction.user.id != expected_captain_id and not is_staff(interaction):
            await interaction.response.send_message(
                "❌ Bu düyməni yalnız öz komandanızın kapitanı və ya rəhbərlik basa bilər.", ephemeral=True
            )
            return

        set_match_ready(active["match_number"], is_team_a)
        if is_team_a:
            button.disabled = True
            button.label = "Komanda A Hazırdır ✅"
        else:
            button.disabled = True
            button.label = "Komanda B Hazırdır ✅"

        active = get_active_match(active["match_number"])
        status_embed = _build_match_status_embed(active) if active else None
        await interaction.response.edit_message(embed=status_embed, view=self)

        if active and active.get("thread_id"):
            thread = interaction.guild.get_thread(active["thread_id"]) if interaction.guild else None
            if thread:
                team_label = "🔵 Komanda A" if is_team_a else "🔴 Komanda B"
                try:
                    await thread.send(f"✅ {team_label} hazırdır!")
                except discord.HTTPException:
                    pass

        if active and active["team_a_ready"] and active["team_b_ready"]:
            log_embed = discord.Embed(
                title=f"✅ 5v5 Matç No{active['match_number']} — Hər iki komanda hazır",
                description="Admin/moderator nəticəni aşağıdaki düymələrlə qeyd etməlidir.",
                color=discord.Color.blurple()
            )
            log_channel = await _get_log_channel_5v5() or await _get_log_channel()
            if log_channel:
                result_view = MatchResultView5v5(active["match_number"], active["team_a"], active["team_b"])
                await log_channel.send(embed=log_embed, view=result_view)

    @discord.ui.button(label="Komanda A Hazır", style=discord.ButtonStyle.primary, custom_id="ready_a_5v5", row=2)
    async def team_a_ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set_ready(interaction, True, button)

    @discord.ui.button(label="Komanda B Hazır", style=discord.ButtonStyle.danger, custom_id="ready_b_5v5", row=2)
    async def team_b_ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set_ready(interaction, False, button)

    async def _veto(self, interaction: discord.Interaction, is_team_a: bool, button: discord.ui.Button):
        active = await self._get_active_for_message(interaction)
        if not active:
            return
        expected_captain_id = active["captain_a_id"] if is_team_a else active["captain_b_id"]
        if interaction.user.id != expected_captain_id and not is_staff(interaction):
            await interaction.response.send_message(
                "❌ Xəritə veto yalnız öz komandanızın kapitanı üçündür.", ephemeral=True
            )
            return
        already_used = active["veto_a_used"] if is_team_a else active["veto_b_used"]
        if already_used:
            await interaction.response.send_message("❌ Veto haqqınızı artıq istifadə etmisiniz.", ephemeral=True)
            return
        excluded = set(active["map_vetoed"]) | {active["selected_map"]}
        candidates = [m for m in MAPS if m not in excluded]
        if not candidates:
            await interaction.response.send_message("❌ Vetolanacaq başqa xəritə qalmadı.", ephemeral=True)
            return
        new_map = random.choice(candidates)
        veto_map(active["match_number"], is_team_a, new_map)
        button.disabled = True
        button.label = "Veto istifadə edildi"
        await interaction.response.defer()
        card_path = os.path.join(DATA_DIR or ".", f"match_5v5_{active['match_number']}.png")
        await asyncio.to_thread(
            generate_match_card, active["match_number"], new_map, active["team_a"], active["team_b"],
            active["captain_a_id"], active["captain_b_id"], card_path
        )
        active = get_active_match(active["match_number"])
        await interaction.message.edit(
            attachments=[discord.File(card_path, filename="match.png")],
            embed=_build_match_status_embed(active) if active else None,
            view=self
        )
        await interaction.followup.send(
            f"🚫 {'Komanda A' if is_team_a else 'Komanda B'} kapitanı xəritəni vetoladı! Yeni xəritə: **{new_map}**",
        )

        if active and active.get("thread_id") and interaction.guild:
            thread = interaction.guild.get_thread(active["thread_id"])
            if thread:
                try:
                    await thread.send(f"🚫 Xəritə vetolandı — yeni xəritə: **{new_map}**")
                except discord.HTTPException:
                    pass

        if active and interaction.guild:
            if active.get("voice_a_id"):
                va = interaction.guild.get_channel(active["voice_a_id"])
                if va:
                    try:
                        await va.edit(name=f"🔵 M{active['match_number']}-A · {new_map}")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
            if active.get("voice_b_id"):
                vb = interaction.guild.get_channel(active["voice_b_id"])
                if vb:
                    try:
                        await vb.edit(name=f"🔴 M{active['match_number']}-B · {new_map}")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

    @discord.ui.button(label="🚫 Veto (A)", style=discord.ButtonStyle.secondary, custom_id="veto_a_5v5", row=3)
    async def veto_a_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._veto(interaction, True, button)

    @discord.ui.button(label="🚫 Veto (B)", style=discord.ButtonStyle.secondary, custom_id="veto_b_5v5", row=3)
    async def veto_b_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._veto(interaction, False, button)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="cancel_match_5v5", row=4)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız rəhbərlik üçündür.", ephemeral=True)
            return

        active = await self._get_active_for_message(interaction)
        if not active:
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        view = CancelMatchView5v5(active["match_number"], active["team_a"], active["team_b"])
        embed = discord.Embed(
            title=f"🚫 5v5 Matç No{active['match_number']} ləğv edilir",
            description=(
                "Gəlməyən oyunçu varsa aşağıdan seçin (ELO cəzası alacaq), "
                "yoxdursa \"Heç kimə cəza olmasın\"-ı seçin."
            ),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class CancelMatchView5v5(discord.ui.View):
    """`CancelMatchView`-in 5v5 analoqu — ELO cəzası `players_5v5`-ə yazılır, oyunçular
    `matchmaking_queue_5v5`-ə qaytarılır."""
    def __init__(self, match_number, team_a, team_b):
        super().__init__(timeout=120)
        self.match_number = match_number
        self.team_a = team_a
        self.team_b = team_b

        options = [
            discord.SelectOption(label=p["nick"][:100], value=str(p["discord_id"]))
            for p in team_a + team_b
        ]
        options.append(discord.SelectOption(label="Heç kimə cəza olmasın", value="none"))
        sel = discord.ui.Select(placeholder="Gəlməyən oyunçu (opsional)...", options=options[:25])
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu yalnız rəhbərlik üçündür.", ephemeral=True)
            return

        active = get_active_match(self.match_number)
        if not active:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(
                content="⚠️ Bu matç artıq aktiv deyil (başqa əməliyyatla bağlanıb).", embed=None, view=self
            )
            return

        value = self.select_menu.values[0]
        all_players = self.team_a + self.team_b
        absent_id = int(value) if value != "none" else None
        penalized_nick = None

        if absent_id is not None:
            stats5 = get_player_5v5(absent_id)
            if stats5:
                old_elo = stats5["elo"]
                new_elo = max(0, old_elo - MATCH_CANCEL_ELO_PENALTY)
                set_player_5v5_elo(absent_id, new_elo)
                log_admin_action(
                    "match_cancel_penalty_5v5", absent_id, "elo", str(old_elo), str(new_elo),
                    f"5v5 Matç No{self.match_number} ləğvi — gəlmədi", interaction.user.id
                )
                await _post_audit_log(
                    "match_cancel_penalty_5v5", absent_id, "elo", old_elo, new_elo,
                    f"5v5 Matç No{self.match_number} ləğvi — gəlmədi", interaction.user.id
                )
                penalized_nick = next((p["nick"] for p in all_players if p["discord_id"] == absent_id), None)

        returned = []
        for p in all_players:
            if absent_id is not None and p["discord_id"] == absent_id:
                continue
            stats5 = get_player_5v5(p["discord_id"])
            elo = stats5["elo"] if stats5 else 1000
            if add_to_queue_5v5(p["discord_id"], p["nick"], elo):
                returned.append(p["nick"])

        clear_active_match(self.match_number)
        await _cleanup_match_voice_channels(interaction.guild, active)

        desc = f"5v5 Matç No{self.match_number} ləğv edildi."
        if penalized_nick:
            desc += f"\n🔴 ELO cəzası: **{penalized_nick}** (-{MATCH_CANCEL_ELO_PENALTY} ELO)"
        if returned:
            desc += f"\n🔁 Sıraya qaytarıldı: {', '.join(returned)}"

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=desc, embed=None, view=self)

        if active.get("thread_id") and interaction.guild:
            thread = interaction.guild.get_thread(active["thread_id"])
            if thread:
                try:
                    await thread.send("🚫 Matç ləğv edildi.")
                except discord.HTTPException:
                    pass

        await update_queue_status_message_5v5()


MATCH_CANCEL_ELO_PENALTY = 15



class MatchResultView5v5(discord.ui.View):
    """Admin düymələri ilə 5v5 matç nəticəsini qeyd edir: ELO/streak/rütbə yenilənir,
    coin veriilir, matç tarixçəsinə yazılır, həm faceit-log, həm də match-history
    kanalına elan olunur."""
    def __init__(self, match_number, team_a, team_b):
        super().__init__(timeout=None)
        self.match_number = match_number
        self.team_a = team_a
        self.team_b = team_b
        self.finished = False

    async def _finish(self, interaction: discord.Interaction, winner_team, loser_team, winner_label, loser_label):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return

        if self.finished:
            await interaction.response.send_message("⚠️ Bu matçın nəticəsi artıq qeyd olunub.", ephemeral=True)
            return

        await interaction.response.defer()

        winner_ids = [p["discord_id"] for p in winner_team]
        loser_ids = [p["discord_id"] for p in loser_team]

        active_before = get_active_match(self.match_number)
        selected_map = active_before.get("selected_map") if active_before else None

        results = update_team_elo_5v5(winner_ids, loser_ids, elo_multiplier=1)
        if results is None:
            await interaction.followup.send("❌ Xəta: oyunçu məlumatları tapılmadı.", ephemeral=True)
            return

        self.finished = True
        for child in self.children:
            child.disabled = True

        stats_by_id = {}
        scan = get_scan_result(self.match_number)
        if scan and scan["confirmed"]:
            try:
                parsed = json.loads(scan["scan_data"])
            except (TypeError, ValueError):
                parsed = {}
            for key, s in parsed.items():
                try:
                    did = int(key)
                except ValueError:
                    continue
                add_combat_stats(did, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0))
                stats_by_id[did] = s

        current_season = get_or_create_current_season("5v5")

        for p, r in zip(winner_team, results["winners"]):
            did = p["discord_id"]
            add_season_stat(did, current_season["id"], kills=stats_by_id.get(did, {}).get("kills", 0),
                             assists=stats_by_id.get(did, {}).get("assists", 0),
                             deaths=stats_by_id.get(did, {}).get("deaths", 0),
                             wins=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"], mode="5v5")
            streak, _ = update_streak_5v5(did, True)
            bonus_coins, _bonus_elo = get_streak_bonus(streak)
            earned = random.randint(5, 10) + bonus_coins
            new_bal = add_coins(did, earned)
            reason = f"5v5 Matç No{self.match_number} qələbə" + (f" (seriya {streak})" if bonus_coins else "")
            add_coin_log(did, earned, reason, "earn", new_bal)
            await _sync_rank_role_5v5(interaction.guild, did, r["new_elo"])

        for p, r in zip(loser_team, results["losers"]):
            did = p["discord_id"]
            add_season_stat(did, current_season["id"], kills=stats_by_id.get(did, {}).get("kills", 0),
                             assists=stats_by_id.get(did, {}).get("assists", 0),
                             deaths=stats_by_id.get(did, {}).get("deaths", 0),
                             losses=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"], mode="5v5")
            update_streak_5v5(did, False)
            earned = random.randint(0, 5)
            new_bal = add_coins(did, earned)
            add_coin_log(did, earned, f"5v5 Matç No{self.match_number} iştirak", "earn", new_bal)
            await _sync_rank_role_5v5(interaction.guild, did, r["new_elo"])

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        embed = discord.Embed(
            title=f"✅ 5v5 Matç No{self.match_number} — Nəticə qeyd edildi",
            description=f"🗓️ {now.strftime('%d.%m.%Y %H:%M')} (AZ vaxtı)\n🏆 Qalib: **{winner_label}**",
            color=discord.Color.from_rgb(230, 130, 40)
        )

        def _fmt_line(p, r):
            line = f"{p['nick']} — {r['old_elo']} → **{r['new_elo']}** ({'+' if r['new_elo']-r['old_elo']>=0 else ''}{r['new_elo']-r['old_elo']})"
            s = stats_by_id.get(p["discord_id"])
            if s:
                line += f"  ·  K:{s.get('kills',0)} A:{s.get('assists',0)} D:{s.get('deaths',0)}"
            return line

        embed.add_field(
            name=f"✅ {winner_label}",
            value="\n".join([_fmt_line(p, r) for p, r in zip(winner_team, results["winners"])]),
            inline=False
        )
        embed.add_field(
            name=f"❌ {loser_label}",
            value="\n".join([_fmt_line(p, r) for p, r in zip(loser_team, results["losers"])]),
            inline=False
        )
        if selected_map:
            embed.add_field(name="🗺️ Xəritə", value=selected_map, inline=False)

        await asyncio.to_thread(
            record_match_history, "5v5", winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
            self.match_number, selected_map
        )
        asyncio.create_task(_update_live_board_message_5v5(f"5v5 Matç No{self.match_number}: **{winner_label}** qalib gəldi"))

        await interaction.edit_original_response(embed=embed, view=self)
        log_channel = await _get_log_channel_5v5()
        if log_channel and log_channel.id != interaction.channel.id:
            await log_channel.send(embed=embed)
        history_channel = await _get_match_history_channel()
        if history_channel:
            await history_channel.send(embed=embed)

        clear_active_match(self.match_number)

        if active_before:
            if active_before.get("log_channel_id") and active_before.get("log_message_id"):
                try:
                    msg_channel = bot.get_channel(active_before["log_channel_id"]) or \
                        await bot.fetch_channel(active_before["log_channel_id"])
                    old_msg = await msg_channel.fetch_message(active_before["log_message_id"])
                    await old_msg.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

            if interaction.guild:
                await _cleanup_match_voice_channels(interaction.guild, active_before)

                if active_before.get("thread_id"):
                    thread = interaction.guild.get_thread(active_before["thread_id"])
                    if thread:
                        try:
                            await thread.send("✅ Matç nəticəsi qeyd olundu.")
                        except discord.HTTPException:
                            pass
                        await _post_thread_summary_and_archive(thread)

        await _start_match_if_ready_5v5(log_channel or interaction.channel, interaction.guild)

    @discord.ui.button(label="Komanda A qalib", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="result_a_5v5")
    async def team_a_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_a, self.team_b, "Komanda A", "Komanda B")

    @discord.ui.button(label="Komanda B qalib", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="result_b_5v5")
    async def team_b_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_b, self.team_a, "Komanda B", "Komanda A")


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN SİSTEMİ — skor ekranından K/A/D oxuyub matç nəticəsinə əlavə edir
# ═══════════════════════════════════════════════════════════════════════════════

def _build_scan_embed(match_number, parsed):
    lines = []
    for key, s in parsed.items():
        mark = "✅" if isinstance(key, int) else "⚠️"
        ocr_nick = s.get("ocr_nick", "")
        arrow = f" ← *{ocr_nick}*" if ocr_nick and ocr_nick != s["nick"] else ""
        lines.append(f"{mark} **{s['nick']}**{arrow}  K:{s['kills']} A:{s['assists']} D:{s['deaths']}")

    embed = discord.Embed(
        title=f"🔍 Matç No{match_number} — Scan nəticəsi",
        description="\n".join(lines) or "Heç bir oyunçu tapılmadı.",
        color=discord.Color.orange()
    )
    embed.set_footer(text="✅ uyğun oyunçu  ⚠️ tapılmadı (0/0/5 veriləcək)  |  Düzəliş üçün oyunçunu seçin, sonra Yadda saxla")
    return embed


class StatEditModal(discord.ui.Modal, title="Stat Düzəliş"):
    kills_inp = discord.ui.TextInput(label="Kill", required=True, max_length=4)
    assists_inp = discord.ui.TextInput(label="Asist", required=True, max_length=4)
    deaths_inp = discord.ui.TextInput(label="Ölüm", required=True, max_length=4)

    def __init__(self, player_key, player_nick, current, view_ref):
        super().__init__(title=f"{player_nick[:20]} — Düzəliş")
        self.player_key = player_key
        self.view_ref = view_ref
        self.kills_inp.default = str(current["kills"])
        self.assists_inp.default = str(current["assists"])
        self.deaths_inp.default = str(current["deaths"])

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.view_ref.parsed[self.player_key]["kills"] = int(self.kills_inp.value)
            self.view_ref.parsed[self.player_key]["assists"] = int(self.assists_inp.value)
            self.view_ref.parsed[self.player_key]["deaths"] = int(self.deaths_inp.value)
        except ValueError:
            await interaction.response.send_message("❌ Rəqəm daxil edin.", ephemeral=True)
            return
        embed = _build_scan_embed(self.view_ref.match_number, self.view_ref.parsed)
        await interaction.response.edit_message(embed=embed, view=self.view_ref)


class ScanEditView(discord.ui.View):
    def __init__(self, match_number, parsed):
        super().__init__(timeout=600)
        self.match_number = match_number
        self.parsed = parsed
        self.saved = False

        options = [
            discord.SelectOption(
                label=s["nick"][:25], value=str(key),
                description=f"K:{s['kills']} A:{s['assists']} D:{s['deaths']}"
            )
            for key, s in parsed.items()
        ]
        if options:
            sel = discord.ui.Select(placeholder="Düzəltmək üçün oyunçu seçin...", options=options[:25])
            sel.callback = self._on_select
            self.add_item(sel)
            self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)
            return
        raw_key = self.select_menu.values[0]
        try:
            key = int(raw_key)
        except ValueError:
            key = raw_key
        stats = self.parsed.get(key)
        if stats is None:
            await interaction.response.send_message("❌ Tapılmadı.", ephemeral=True)
            return
        await interaction.response.send_modal(StatEditModal(key, stats["nick"], stats, self))

    @discord.ui.button(label="Yadda saxla ✅", style=discord.ButtonStyle.success, row=1)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)
            return
        if self.saved:
            await interaction.response.send_message("⚠️ Artıq yadda saxlanılıb.", ephemeral=True)
            return
        self.saved = True
        for child in self.children:
            child.disabled = True

        scan_json = json.dumps({str(k): v for k, v in self.parsed.items()}, ensure_ascii=False)
        scan_id = save_scan_result(self.match_number, scan_json)
        confirm_scan(scan_id)

        embed = _build_scan_embed(self.match_number, self.parsed)
        embed.title += " — Yadda saxlanıldı"
        await interaction.response.edit_message(
            content="✅ Statistika yadda saxlanıldı. Nəticəni bildirmək üçün matç kartındakı "
                    "Komanda A/B qalib düymələrini basın.",
            embed=embed, view=self
        )

    @discord.ui.button(label="Ləğv et ❌", style=discord.ButtonStyle.secondary, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Scan ləğv edildi.", embed=None, view=self)


@bot.tree.command(name="scan", description="[Admin] Skor ekranını scan edir (şəkli göndərib sonra /scan yazın)")
@app_commands.describe(matc_no="Birdən çox matç paralel aktivdirsə, hansının skanı olduğunu göstərin")
@staff_check()
async def scan_cmd(interaction: discord.Interaction, matc_no: int = None):
    if matc_no is not None:
        active = get_active_match(matc_no)
        if not active:
            await interaction.response.send_message(f"❌ Matç No{matc_no} aktiv deyil.", ephemeral=True)
            return
    else:
        active_matches = get_all_active_matches()
        if not active_matches:
            await interaction.response.send_message("❌ Aktiv matç yoxdur.", ephemeral=True)
            return
        if len(active_matches) > 1:
            nums = ", ".join(str(m["match_number"]) for m in active_matches)
            await interaction.response.send_message(
                f"⚠️ Birdən çox aktiv matç var ({nums}). `/scan matc_no:<nömrə>` ilə göstərin.",
                ephemeral=True
            )
            return
        active = active_matches[0]

    await interaction.response.defer()

    img_bytes = None
    try:
        async for msg in interaction.channel.history(limit=20):
            for att in msg.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    img_bytes = await att.read()
                    break
            if img_bytes:
                break
    except Exception:
        pass

    if not img_bytes:
        await interaction.followup.send(
            "❌ Son 20 mesajda şəkil tapılmadı. Skor ekranının şəklini bu kanala göndərib "
            "sonra `/scan` yazın.",
            ephemeral=True
        )
        return

    await interaction.followup.send("🔍 Skor ekranı analiz edilir...", ephemeral=True)
    try:
        ocr_results = await asyncio.to_thread(ocr_scoreboard, img_bytes)
    except Exception as e:
        await interaction.followup.send(f"❌ Scan xətası: {e}", ephemeral=True)
        return

    match_number = active["match_number"]
    all_players = active.get("team_a", []) + active.get("team_b", [])

    parsed = match_to_registered(ocr_results, all_players)
    parsed = apply_defaults_for_missing(all_players, parsed)

    embed = _build_scan_embed(match_number, parsed)
    view = ScanEditView(match_number, parsed)
    await interaction.followup.send(embed=embed, view=view)


@scan_cmd.error
async def scan_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


async def update_queue_status_message_5v5():
    global queue_status_message_id_5v5
    if queue_status_channel_id_5v5 is None or queue_status_message_id_5v5 is None:
        return
    channel = bot.get_channel(queue_status_channel_id_5v5)
    if channel is None:
        return
    players = get_queue_list_5v5()
    image_path = os.path.join(DATA_DIR or ".", "queue_status_5v5.png")
    await asyncio.to_thread(generate_queue_status_card, players, image_path, None, 10)
    try:
        message = await channel.fetch_message(queue_status_message_id_5v5)
        await message.edit(attachments=[discord.File(image_path, filename="queue_status_5v5.png")])
    except discord.NotFound:
        pass


async def _post_thread_summary_and_archive(thread):
    """Matç bitəndə thread-ə avtomatik qısa xülasə yazır (mesaj sayı, ən aktiv iştirakçı)
    və thread-i arxivləşdirir/kilidləyir ki, artıq lazımsız qalmasın."""
    counts = {}
    total = 0
    try:
        async for msg in thread.history(limit=200):
            if msg.author.bot:
                continue
            counts[msg.author.display_name] = counts.get(msg.author.display_name, 0) + 1
            total += 1
    except discord.HTTPException:
        return
    if total == 0:
        summary = "📋 **Thread Xülasəsi** — bu matçda əlavə mesajlaşma olmadı."
    else:
        top_name, top_count = max(counts.items(), key=lambda kv: kv[1])
        summary = f"📋 **Thread Xülasəsi** — cəmi {total} mesaj. Ən aktiv: **{top_name}** ({top_count} mesaj)."
    try:
        await thread.send(summary)
        await thread.edit(archived=True, locked=True)
    except discord.HTTPException:
        pass


async def _cleanup_match_voice_channels(guild, active):
    """Matçın dinamik səs kanallarını (varsa) silir, içindəkiləri əvvəlcə lobbiyə köçürür.
    Bu funksiya HEÇ VAXT exception qaldırmamalıdır — çağıran yerlərdə (_finish/_on_select)
    ondan dərhal sonra clear_active_match() gəlir; əvvəllər yalnız discord.Forbidden tutulurdu,
    başqa növ xəta (HTTPException, rate-limit, gözlənilməz exception) bütün callback-i
    dayandırıb clear_active_match-ı HEÇ VAXT işə düşməyə qoymurdu — nəticədə matç DB-də
    'aktiv' qalıb oyunçular yenidən sıraya qoşula bilmirdi (bax: 'aktiv matçda göstərir' bug-ı)."""
    if not guild:
        return
    lobby_channel = guild.get_channel(LOBBY_VOICE_ID)
    for key in ("voice_a_id", "voice_b_id"):
        vid = active.get(key)
        if not vid:
            continue
        try:
            vc = guild.get_channel(vid)
            if not vc:
                continue
            if lobby_channel:
                for member in list(vc.members):
                    try:
                        await member.move_to(lobby_channel)
                    except Exception:
                        pass
            await vc.delete(reason="Matç bitdi/ləğv oldu")
        except Exception as e:
            print(f"[VOICE CLEANUP] Kanal {vid} silinərkən xəta (matç davam edir): {e}", flush=True)


_match_start_lock_5v5 = asyncio.Lock()


async def _start_match_if_ready_5v5(channel, guild):
    """`_start_match_if_ready`-in 5v5 analoqu — AYRICA kilid istifadə edir ki, 2v2 və 5v5
    matç başlatma məntiqi bir-birini gözləməsin (əsl paralellik)."""
    async with _match_start_lock_5v5:
        while count_active_matches(mode="5v5") < MAX_PARALLEL_MATCHES and queue_size_5v5() >= 10:
            started = await _start_one_5v5_match(channel, guild)
            if not started:
                break


WARMUP_VOICE_CHANNEL_NAME_5V5 = "🎤 İsınma Otağı (5v5)"


async def _get_or_create_warmup_channel(guild, mode="5v5"):
    if not guild:
        return None
    name = WARMUP_VOICE_CHANNEL_NAME_5V5
    category_name = CATEGORY_5V5_NAME
    existing = discord.utils.get(guild.voice_channels, name=name)
    if existing:
        return existing
    category = discord.utils.get(guild.categories, name=category_name)
    try:
        return await guild.create_voice_channel(name, category=category)
    except discord.Forbidden:
        return None


async def _start_one_5v5_match(channel, guild) -> bool:
    """`_start_one_match`-ın 5v5 analoqu — eyni axın (kapitan reveal, matç kartı, thread,
    intel briefing, dinamik səs kanalları), yalnız 10 nəfər/2×5 komanda və AYRICA
    kateqoriya/queue/status funksiyaları istifadə edir."""
    result = pop_10_and_balance()
    if result is None:
        return False
    team_a, team_b, captain_a, captain_b = result
    selected_map = random.choice(MAPS)
    match_number = get_next_match_number()

    set_active_match(
        match_number,
        team_a_json=json.dumps(team_a, ensure_ascii=False),
        team_b_json=json.dumps(team_b, ensure_ascii=False),
        selected_map=selected_map,
        captain_a_id=captain_a["discord_id"],
        captain_b_id=captain_b["discord_id"],
        mode="5v5"
    )

    captain_reveal_msg = None
    try:
        captain_reveal_msg = await channel.send(f"🎲 5v5 Matç No{match_number} — kapitanlar seçilir...")
        await asyncio.sleep(1.0)
        await captain_reveal_msg.edit(content=f"🔵 Komanda A Kapitanı: **{captain_a['nick']}** seçildi!")
        await asyncio.sleep(0.8)
        await captain_reveal_msg.edit(
            content=f"🔵 Komanda A Kapitanı: **{captain_a['nick']}**\n🔴 Komanda B Kapitanı: **{captain_b['nick']}** seçildi!"
        )
        await asyncio.sleep(0.8)
    except discord.HTTPException:
        pass

    card_path = os.path.join(DATA_DIR or ".", f"match_5v5_{match_number}.png")
    await asyncio.to_thread(
        generate_match_card, match_number, selected_map, team_a, team_b,
        captain_a["discord_id"], captain_b["discord_id"], card_path
    )

    if captain_reveal_msg:
        try:
            await captain_reveal_msg.delete()
        except discord.HTTPException:
            pass

    mentions = " ".join([f"<@{p['discord_id']}>" for p in team_a + team_b])
    ready_view = TeamReadyView5v5(team_a, team_b)
    initial_status_embed = _build_match_status_embed({
        "match_number": match_number, "team_a_ready": False, "team_b_ready": False,
        "selected_map": selected_map, "voice_a_id": None, "voice_b_id": None,
    })
    sent_message = await channel.send(
        content=mentions,
        file=discord.File(card_path, filename="match.png"),
        embed=initial_status_embed,
        view=ready_view
    )

    thread_id = None
    try:
        thread = await sent_message.create_thread(
            name=f"5v5 Matç #{match_number} — {selected_map}", auto_archive_duration=60
        )
        thread_id = thread.id
        await thread.send(f"{mentions}\n💬 Bu matç üçün koordinasiyanı burada apara bilərsiniz.")
    except discord.HTTPException:
        pass

    set_active_match_message(match_number, sent_message.id, channel.id, thread_id)

    social_channel = await _get_social_channel()
    if social_channel:
        announce_embed = discord.Embed(
            title=f"🎯 Yeni 5v5 Matç Başladı — No{match_number}",
            description=(
                f"🗺️ Xəritə: **{selected_map}**\n\n"
                "Lobbi operativ qurulsun deyə kapitanlarla dərhal əlaqə saxlayın!"
            ),
            color=discord.Color.from_rgb(230, 130, 40)
        )
        announce_embed.add_field(
            name="🔵 Komanda A Kapitanı",
            value=f"**{captain_a['nick']}**\n<@{captain_a['discord_id']}> · `{captain_a['discord_id']}`",
            inline=True
        )
        announce_embed.add_field(
            name="🔴 Komanda B Kapitanı",
            value=f"**{captain_b['nick']}**\n<@{captain_b['discord_id']}> · `{captain_b['discord_id']}`",
            inline=True
        )
        announce_embed.set_footer(text="Nextlevelaz — 5v5")
        try:
            await social_channel.send(embed=announce_embed)
        except discord.Forbidden:
            pass

    voice_a_channel = voice_b_channel = None
    if guild:
        category = discord.utils.get(guild.categories, name=CATEGORY_5V5_NAME)
        try:
            voice_a_channel = await guild.create_voice_channel(f"🔵 M{match_number}-A · {selected_map}", category=category)
            voice_b_channel = await guild.create_voice_channel(f"🔴 M{match_number}-B · {selected_map}", category=category)
            set_active_match_voice(
                match_number,
                voice_a_channel.id if voice_a_channel else None,
                voice_b_channel.id if voice_b_channel else None
            )
            active_now = get_active_match(match_number)
            if active_now:
                try:
                    await sent_message.edit(embed=_build_match_status_embed(active_now))
                except discord.HTTPException:
                    pass
            if thread_id:
                thread_obj = guild.get_thread(thread_id)
                if thread_obj:
                    try:
                        await thread_obj.send(
                            f"🎙️ Səs kanalları hazırdır: {voice_a_channel.mention} (Komanda A) · "
                            f"{voice_b_channel.mention} (Komanda B)"
                        )
                    except discord.HTTPException:
                        pass
        except discord.Forbidden:
            print(f"[VOICE] 5v5 Matç #{match_number} üçün səs kanalları yaradıla bilmədi (icazə yoxdur).", flush=True)

    for p in team_a:
        member = guild.get_member(p["discord_id"]) if guild else None
        if member and member.voice and voice_a_channel:
            try:
                await member.move_to(voice_a_channel)
            except discord.Forbidden:
                pass

    for p in team_b:
        member = guild.get_member(p["discord_id"]) if guild else None
        if member and member.voice and voice_b_channel:
            try:
                await member.move_to(voice_b_channel)
            except discord.Forbidden:
                pass

    await update_queue_status_message_5v5()
    return True


class MatchmakingView5v5(discord.ui.View):
    """`MatchmakingView`-in 5v5 analoqu — AYRICA sıra (matchmaking_queue_5v5), 10 nəfər
    tamamlananda `_start_match_if_ready_5v5` işə düşür."""
    def __init__(self):
        super().__init__(timeout=None)

    async def _do_join_queue(self, interaction: discord.Interaction):
        if not is_queue_open():
            await interaction.response.send_message(
                f"🌙 Matchmaking yalnız gecə saatlarında aktivdir.\n🇦🇿 Azərbaycan vaxtı: **20:00 - 02:00**",
                ephemeral=True
            )
            return

        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "❌ Əvvəlcə qeydiyyatdan keçməlisiniz. `#faceit-qeydiyyat` kanalına keçin.",
                ephemeral=True
            )
            return

        if is_player_in_active_match(interaction.user.id):
            await interaction.response.send_message(
                "❌ Siz artıq aktiv bir matçdasınız — əvvəlcə onu bitirin, sonra yenidən sıraya qoşula bilərsiniz.",
                ephemeral=True
            )
            return

        if queue_size_5v5() >= 10:
            await interaction.response.send_message(
                "⏳ 5v5 sırası doludur (10/10). Zəhmət olmasa gözləyin, yer boşalan kimi qoşula bilərsiniz.",
                ephemeral=True
            )
            return

        discord_id, nick, so2_id, elo = player[0], player[1], player[2], player[3]
        ensure_5v5_stats_row(discord_id)
        stats5 = get_player_5v5(discord_id)

        added = add_to_queue_5v5(discord_id, nick, stats5["elo"], so2_id)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq 5v5 sırasındasınız.", ephemeral=True)
            return

        size = queue_size_5v5()
        active_count = count_active_matches(mode="5v5")
        if active_count >= MAX_PARALLEL_MATCHES:
            await interaction.response.send_message(
                f"✅ {nick} 5v5 sırasına qoşuldu! ({size}/10)\n"
                f"⏳ Hazırda {active_count}/{MAX_PARALLEL_MATCHES} 5v5 matç paralel davam edir — "
                f"yer boşalan kimi növbəti matç avtomatik başlayacaq.",
                ephemeral=True
            )
            await update_queue_status_message_5v5()
            return

        await interaction.response.send_message(f"✅ {nick} 5v5 sırasına qoşuldu! ({size}/10)", ephemeral=True)
        await update_queue_status_message_5v5()

        if interaction.guild:
            member = interaction.guild.get_member(discord_id)
            if member and member.voice and member.voice.channel:
                warmup = await _get_or_create_warmup_channel(interaction.guild, mode="5v5")
                if warmup and member.voice.channel.id != warmup.id:
                    try:
                        await member.move_to(warmup)
                    except discord.Forbidden:
                        pass

        await _start_match_if_ready_5v5(interaction.channel, interaction.guild)

    @discord.ui.button(label="5v5", style=discord.ButtonStyle.danger, emoji="🎯", custom_id="mm_join_5v5")
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._do_join_queue(interaction)

    @discord.ui.button(label="Sıradan çıx", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="mm_leave_5v5")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = remove_from_queue_5v5(interaction.user.id)
        if removed:
            await interaction.response.send_message("✅ 5v5 sırasından çıxdınız.", ephemeral=True)
            await update_queue_status_message_5v5()
        else:
            await interaction.response.send_message("⚠️ Siz 5v5 sırasında deyilsiniz.", ephemeral=True)

    @discord.ui.button(label="Queue-dən hamını çıxart - Admins Only", style=discord.ButtonStyle.danger, emoji="🧹", custom_id="mm_clear_5v5")
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        clear_queue_5v5()
        await interaction.response.send_message("🧹 5v5 sırası tam təmizləndi.", ephemeral=True)
        await update_queue_status_message_5v5()


@bot.event
async def on_ready():
    global LOG_CHANNEL_ID, AUDIT_LOG_CHANNEL_ID
    global STANDOFF2_NEWS_CHANNEL_ID, SOCIAL_CHANNEL_ID
    global MATCH_HISTORY_CHANNEL_ID, SEASON_REWARD_CHANNEL_ID, JOIN_LEAVE_LOG_CHANNEL_ID
    global LOG_CHANNEL_ID_5V5, leaderboard_channel_id_5v5, leaderboard_message_id_5v5
    global leaderboard_alltime_channel_id_5v5, leaderboard_alltime_message_id_5v5
    global CHAT_XP_CHANNEL_ID, chat_activity_channel_id, chat_activity_message_id
    global TICKET_PANEL_CHANNEL_ID, TICKET_CATEGORY_ID
    init_db()

    if not get_meta("backfill_5v5_stats_rows_2026_09_14"):
        try:
            backfilled = 0
            for p in get_all_players(limit=100000):
                if not get_player_5v5(p["discord_id"]):
                    ensure_5v5_stats_row(p["discord_id"])
                    backfilled += 1
            print(f"[BACKFILL] {backfilled} qeydiyyatlı oyunçu üçün players_5v5 sətri yaradıldı (leaderboard-da görünmə problemi düzəldildi).")
        except Exception as e:
            print(f"[BACKFILL] Xəta: {e}")
        set_meta("backfill_5v5_stats_rows_2026_09_14", "1")

    saved_log = get_meta("log_channel_id")
    if saved_log:
        LOG_CHANNEL_ID = int(saved_log)
    saved_log_5v5 = get_meta("log_channel_id_5v5")
    if saved_log_5v5:
        LOG_CHANNEL_ID_5V5 = int(saved_log_5v5)
    saved_lb_5v5 = get_meta("leaderboard_channel_id_5v5")
    if saved_lb_5v5:
        leaderboard_channel_id_5v5 = int(saved_lb_5v5)
    saved_lb_msg_5v5 = get_meta("leaderboard_message_id_5v5")
    if saved_lb_msg_5v5:
        leaderboard_message_id_5v5 = int(saved_lb_msg_5v5)
    saved_social = get_meta("social_channel_id")
    if saved_social:
        SOCIAL_CHANNEL_ID = int(saved_social)
    saved_chat_xp = get_meta("chat_xp_channel_id")
    if saved_chat_xp:
        CHAT_XP_CHANNEL_ID = int(saved_chat_xp)
    saved_chat_lb = get_meta("chat_activity_channel_id")
    if saved_chat_lb:
        chat_activity_channel_id = int(saved_chat_lb)
    saved_chat_lb_msg = get_meta("chat_activity_message_id")
    if saved_chat_lb_msg:
        chat_activity_message_id = int(saved_chat_lb_msg)
    saved_audit = get_meta("audit_log_channel_id")
    if saved_audit:
        AUDIT_LOG_CHANNEL_ID = int(saved_audit)
    saved_news = get_meta("standoff2_news_channel_id")
    if saved_news:
        STANDOFF2_NEWS_CHANNEL_ID = int(saved_news)
    saved_history = get_meta("match_history_channel_id")
    if saved_history:
        MATCH_HISTORY_CHANNEL_ID = int(saved_history)
    saved_lb_alltime = get_meta("leaderboard_alltime_channel_id_5v5")
    if saved_lb_alltime:
        leaderboard_alltime_channel_id_5v5 = int(saved_lb_alltime)
    saved_lb_alltime_msg = get_meta("leaderboard_alltime_message_id_5v5")
    if saved_lb_alltime_msg:
        leaderboard_alltime_message_id_5v5 = int(saved_lb_alltime_msg)
    saved_season_reward = get_meta("season_reward_channel_id")
    if saved_season_reward:
        SEASON_REWARD_CHANNEL_ID = int(saved_season_reward)
    saved_join_leave = get_meta("join_leave_log_channel_id")
    if saved_join_leave:
        JOIN_LEAVE_LOG_CHANNEL_ID = int(saved_join_leave)
    saved_ticket_panel = get_meta("ticket_panel_channel_id")
    if saved_ticket_panel:
        TICKET_PANEL_CHANNEL_ID = int(saved_ticket_panel)
    saved_ticket_category = get_meta("ticket_category_id")
    if saved_ticket_category:
        TICKET_CATEGORY_ID = int(saved_ticket_category)
    print(f"[CONFIG] LOG_CHANNEL_ID={LOG_CHANNEL_ID} "
          f"AUDIT_LOG_CHANNEL_ID={AUDIT_LOG_CHANNEL_ID} STANDOFF2_NEWS_CHANNEL_ID={STANDOFF2_NEWS_CHANNEL_ID} "
          f"MATCH_HISTORY_CHANNEL_ID={MATCH_HISTORY_CHANNEL_ID} SEASON_REWARD_CHANNEL_ID={SEASON_REWARD_CHANNEL_ID}", flush=True)

    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView5v5())
    bot.add_view(RegisterView())
    bot.add_view(TeamReadyView5v5())
    bot.add_view(TicketSelectView())
    bot.add_view(TicketCloseView())
    if not check_giveaways.is_running():
        check_giveaways.start()
    if not check_stuck_matches.is_running():
        check_stuck_matches.start()
    if not daily_report_loop.is_running():
        daily_report_loop.start()
    if not rotate_status_loop.is_running():
        rotate_status_loop.start()
    if not social_reminder_loop.is_running():
        social_reminder_loop.start()
    if not season_rotation_loop.is_running():
        season_rotation_loop.start()
    if not refresh_chat_activity_leaderboard.is_running():
        refresh_chat_activity_leaderboard.start()
    if not weekly_chat_activity_loop.is_running():
        weekly_chat_activity_loop.start()
    if not refresh_leaderboard_5v5.is_running():
        refresh_leaderboard_5v5.start()
    if not refresh_leaderboard_5v5_alltime.is_running():
        refresh_leaderboard_5v5_alltime.start()
    if not suspicious_activity_loop.is_running():
        suspicious_activity_loop.start()
    if not standoff2_news_loop.is_running():
        standoff2_news_loop.start()
    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"[SYNC] {guild.name} üçün komandalar dərhal sinxronlaşdı.", flush=True)

    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("[SYNC] Qlobal komandalar təmizləndi (dublikatların qarşısı alındı).", flush=True)


@bot.event
async def on_member_join(member: discord.Member):
    if not member.bot:
        member_role = discord.utils.get(member.guild.roles, name=MEMBER_ROLE_NAME)
        if member_role:
            try:
                await member.add_roles(member_role, reason="Yeni üzv — avtomatik NLA Member rolu")
            except (discord.Forbidden, discord.HTTPException):
                pass

    log_channel = await _get_join_leave_log_channel()
    if log_channel:
        embed = discord.Embed(
            title="📥 Üzv qoşuldu",
            description=f"{member.mention} ({member})",
            color=discord.Color.from_rgb(95, 208, 122)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Serverdə {member.guild.member_count} üzv")
        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass


@bot.event
async def on_member_remove(member: discord.Member):
    log_channel = await _get_join_leave_log_channel()
    if log_channel:
        embed = discord.Embed(
            title="📤 Üzv ayrıldı",
            description=f"{member.mention} ({member})",
            color=discord.Color.from_rgb(214, 69, 61)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Serverdə {member.guild.member_count} üzv")
        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    if CHAT_XP_CHANNEL_ID and message.channel.id == CHAT_XP_CHANNEL_ID:
        add_chat_xp(message.author.id)
    # Bu bot yalnız slash (app_commands) komandaları istifadə edir, prefiks-komanda
    # emalı (process_commands) lazım deyil — ona görə burada əlavə çağırış edilmir.


class LanguageSelectView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        options = [discord.SelectOption(label=name, value=code) for code, name in LANG_NAMES.items()]
        sel = discord.ui.Select(placeholder="Dili seçin / Select language...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return
        lang = self.select_menu.values[0]
        set_lang(self.discord_id, lang)
        await interaction.response.edit_message(
            content=t("lang.changed", lang, lang_name=LANG_NAMES[lang]), view=None
        )


class _ProfileSubMenuBase(discord.ui.View):
    """Bütün profil alt-menyularının (Statistika/İnventar/Mükafatlar/Sosial/Ayarlar) ortaq
    bazası — hər biri öz ayrıca ephemeral mesajı kimi açılır (bax: ProfileHubView), ona görə
    hər alt-menyunun ÖZ 25-komponent limiti var, əsas menyu ilə paylaşılmır."""
    def __init__(self, discord_id, lang="az", timeout=300):
        super().__init__(timeout=timeout)
        self.discord_id = discord_id
        self.lang = lang

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız profil sahibi üçündür.", ephemeral=True)
            return False
        return True

    def _display_name(self, interaction: discord.Interaction) -> str:
        member = interaction.guild.get_member(self.discord_id) if interaction.guild else None
        return member.display_name if member else str(self.discord_id)

    def _add_buttons(self, defs):
        for key, emoji, callback in defs:
            btn = discord.ui.Button(label=t(key, self.lang), style=discord.ButtonStyle.secondary, emoji=emoji)
            btn.callback = callback
            self.add_item(btn)


class StatsMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.stats", "📊", self.stats_btn),
            ("btn.history", "📜", self.history_btn),
            ("btn.chart", "📈", self.elo_chart_btn),
            ("btn.maps", "🗺️", self.maps_btn),
            ("btn.coach", "🤖", self.coach_btn),
            ("btn.stats_5v5", "🎯", self.stats_5v5_btn),
        ])

    async def stats_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_stats(interaction, self.discord_id)

    async def stats_5v5_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        stats5 = get_player_stats_dict_5v5(self.discord_id)
        if not stats5:
            await interaction.response.send_message(
                "ℹ️ Hələ 5v5 oynamamısınız — Matchmaking-5v5 kanalından sıraya qoşulun!", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        achievements = []
        card_path = os.path.join(DATA_DIR or ".", f"stats_5v5_{self.discord_id}.png")
        await asyncio.to_thread(generate_stats_card, stats5, achievements, card_path)
        await interaction.followup.send(file=discord.File(card_path, filename="stats_5v5.png"), ephemeral=True)

    async def history_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_history(interaction, self.discord_id)

    async def elo_chart_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_elo_chart(interaction, self.discord_id, self._display_name(interaction))

    async def maps_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_maps(interaction, self.discord_id, self._display_name(interaction))

    async def coach_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.discord_id)
        if not player:
            await interaction.followup.send("❌ Qeydiyyatdan keçməmisiniz.", ephemeral=True)
            return
        history = get_player_match_history(self.discord_id, limit=10)
        if not history:
            await interaction.followup.send("ℹ️ Analiz üçün kifayət qədər matç tarixçəniz yoxdur.", ephemeral=True)
            return
        wins = sum(1 for h in history if h["won"])
        losses = len(history) - wins
        elo_trend = history[0]["elo_after"] - history[-1]["elo_before"]
        combat = get_combat_stats(self.discord_id)
        report = await asyncio.to_thread(
            generate_personal_coach_report, self._display_name(interaction), len(history),
            combat["kills"], combat["assists"], combat["deaths"], wins, losses, elo_trend
        )
        if not report:
            await interaction.followup.send("❌ AI Coach hazırda əlçatan deyil.", ephemeral=True)
            return
        embed = discord.Embed(title="🤖 AI Koç Analizi", description=report, color=discord.Color.from_rgb(80, 160, 255))
        embed.set_footer(text=f"Son {len(history)} matç əsasında")
        await interaction.followup.send(embed=embed, ephemeral=True)


class RewardsMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.coins", "💰", self.coins_btn),
            ("btn.career", "🛤️", self.career_btn),
        ])

    async def coins_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_coins(interaction, self.discord_id)

    async def career_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.discord_id)
        current = get_or_create_current_season()
        season_stat = get_season_stat(self.discord_id, current["id"])
        embed = discord.Embed(
            title=f"🛤️ {self._display_name(interaction)} — Karyera Yolu",
            color=discord.Color.from_rgb(138, 92, 230)
        )
        created_at = player[21] if player and len(player) > 21 and player[21] else None
        if created_at:
            embed.add_field(name="📅 Qeydiyyat tarixi", value=f"<t:{created_at}:D>", inline=True)
        embed.add_field(name="⛰️ Ən yüksək ELO", value=str(player[18]) if player and len(player) > 18 else "?", inline=True)
        embed.add_field(name="🎮 Cəmi matç", value=str((player[4] or 0) + (player[5] or 0)) if player else "0", inline=True)
        embed.add_field(
            name=f"🛤️ Sezon #{current['season_number']} (davam edir)",
            value=(f"{'+' if season_stat['elo_gained'] >= 0 else ''}{season_stat['elo_gained']} ELO — "
                   f"{season_stat['wins']}Q/{season_stat['losses']}M"),
            inline=False
        )
        completed = get_completed_seasons()
        view = SeasonHistoryView(completed) if completed else discord.utils.MISSING
        if completed:
            embed.set_footer(text="Aşağıdan keçmiş bir ELO sezonunu seçib final sıralamasına baxa bilərsiniz.")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)



class SeasonHistoryView(discord.ui.View):
    """Bağlanmış ELO sezonlarının final sıralamasına Discord-dan baxmaq üçün — veb
    saytdakı "Zaman Kapsulu" funksiyasının Discord tərəfdaşı."""
    def __init__(self, completed_seasons):
        super().__init__(timeout=180)
        options = [
            discord.SelectOption(label=f"Sezon #{s['season_number']}", value=str(s["id"]),
                                  description=f"{s['start_date']} → {s['end_date']}")
            for s in completed_seasons[:25]
        ]
        sel = discord.ui.Select(placeholder="Keçmiş sezona bax...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        season_id = int(self.select_menu.values[0])
        rows = get_season_leaderboard(season_id, limit=10)
        if not rows:
            await interaction.response.send_message("ℹ️ Bu sezonda qeydə alınmış statistika yoxdur.", ephemeral=True)
            return
        lines = []
        for i, (nick, so2_id, elo_gained, kills, assists, deaths, wins, losses, discord_id) in enumerate(rows):
            lines.append(f"**#{i+1}** {nick} — {'+' if elo_gained >= 0 else ''}{elo_gained} ELO ({wins}Q/{losses}M)")
        embed = discord.Embed(
            title="🕰️ Sezon Nəticələri",
            description="\n".join(lines),
            color=discord.Color.from_rgb(138, 92, 230)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SettingsMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.lang", "🌐", self.lang_btn),
            ("btn.share", "🔗", self.share_btn),
        ])

    async def lang_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            t("lang.select_placeholder", self.lang), view=LanguageSelectView(self.discord_id), ephemeral=True
        )

    async def share_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        link = f"{PUBLIC_WEB_URL}/u/{self.discord_id}"
        await interaction.response.send_message(
            f"🔗 İctimai profil linkiniz:\n{link}", ephemeral=True
        )


class ProfileHubView(discord.ui.View):
    """Əsas profil menyusu — kateqoriya düymələri, hər biri öz alt-menyusunu ayrıca
    ephemeral mesaj kimi açır (bax: _ProfileSubMenuBase)."""
    def __init__(self, discord_id, lang="az"):
        super().__init__(timeout=300)
        self.discord_id = discord_id
        self.lang = lang

        category_defs = [
            ("btn.menu_stats", "📊", StatsMenuView, "Stats, tarixçə, qrafik, xəritələr, AI Koç"),
            ("btn.menu_rewards", "💰", RewardsMenuView, "Coin balansı, karyera yolu"),
            ("btn.menu_settings", "⚙️", SettingsMenuView, "Dil seçimi, profil paylaşım linki"),
        ]
        for key, emoji, view_cls, desc in category_defs:
            btn = discord.ui.Button(label=t(key, lang), style=discord.ButtonStyle.primary, emoji=emoji)
            btn.callback = self._make_category_callback(view_cls, t(key, lang), emoji, desc)
            self.add_item(btn)

    def _make_category_callback(self, view_cls, label, emoji, desc):
        async def _callback(interaction: discord.Interaction):
            if interaction.user.id != self.discord_id:
                await interaction.response.send_message("❌ Bu yalnız profil sahibi üçündür.", ephemeral=True)
                return
            embed = discord.Embed(
                title=f"{emoji} {label}", description=desc,
                color=discord.Color.from_rgb(138, 92, 230)
            )
            await interaction.response.send_message(embed=embed, view=view_cls(self.discord_id, self.lang), ephemeral=True)
        return _callback


@bot.tree.command(name="profile", description="Profilinizi göstərir")
async def profile(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return

    await interaction.response.defer()

    discord_id, nick, so2_id, elo, wins, losses = player[:6]
    stats = get_player_stats_dict(discord_id) or {}

    avatar_bytes = None
    try:
        avatar_url = interaction.user.display_avatar.replace(size=256).url
        avatar_bytes = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
        avatar_bytes = avatar_bytes.content
    except Exception:
        avatar_bytes = None

    player_lang = get_lang(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"profile_{discord_id}.png")
    await asyncio.to_thread(
        generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path,
        coins=stats.get("coins", 0),
        kills=stats.get("kills", 0), assists=stats.get("assists", 0), deaths=stats.get("deaths", 0),
        lang=player_lang,
    )

    await interaction.followup.send(
        file=discord.File(card_path, filename="profile.png"),
        view=ProfileHubView(discord_id, lang=player_lang)
    )


RULES_SECTIONS = [
    {
        "title": "Qeydiyyat qaydası",
        "body": "Oynamaq üçün əvvəlcə qeydiyyatdan keçmək lazımdır. Qeydiyyat kanalında Qeydiyyat düyməsinə basıb Standoff 2 ID və oyundakı adınızı yazın.",
        "accent": GREEN_ACCENT,
    },
    {
        "title": "Sıraya qoşulmaq",
        "body": "Matchmaking kanalında Sıraya qoşul düyməsinə basaraq sıraya qoşula bilərsiniz. Sıradan çıxmaq üçün Sıradan çıx düyməsindən istifadə edin. Eyni anda birdən çox sıraya qoşulmaq olmaz.",
        "accent": ACCENT_VIOLET,
    },
    {
        "title": "Matç tapılanda",
        "body": "Bot avtomatik komandaları (ELO-ya görə balanslaşdırılmış) və kapitanları elan edir, oyunçuları uyğun səs kanallarına köçürür. Oyunçular vaxtında qoşulmalıdır.",
        "accent": ACCENT_VIOLET,
    },
    {
        "title": "ELO sistemi",
        "body": "Matç nəticəsi moderator tərəfindən /matchresult ilə qeyd olunur. ELO dəyişimi FACEIT-ə bənzər dinamik sistemlə hesablanır — ELO fərqi nə qədər böyükdürsə, dəyişim də ona uyğun azalır/artır. Qalib ELO qazanır, məğlub ELO itirir.",
        "accent": ACCENT_VIOLET,
    },
    {
        "title": "Qadağandır",
        "body": "Smurf hesabla oynamaq\nBaşqasının hesabı ilə oynamaq\nNəticəni dəyişdirməyə çalışmaq\nKomanda yoldaşlarını bilərəkdən sabotaj etmək\nTəhqir, toxic davranış və mübahisə yaratmaq\nModerator qərarına qarşı spam etmək\nMatç zamanı oyundan səbəbsiz çıxmaq",
        "accent": RED_ACCENT,
    },
    {
        "title": "Cəza sistemi",
        "body": "Qayda pozuntusuna görə moderatorlar aşağıdakı cəzaları tətbiq edə bilər:\nELO silinməsi\nMatç nəticəsinin ləğvi\nMüvəqqəti FACEIT banı\nDaimi FACEIT banı\nServer qaydalarına görə əlavə cəza",
        "accent": RED_ACCENT,
    },
    {
        "title": "Moderator qərarı və vacib qeyd",
        "body": "Son qərar moderatorlara aiddir. Mübahisəli hallarda oyunçuların davranışı nəzərə alınacaq. Bu sistem ədalətli oyun üçündür — qaydaları bilməmək cəzadan azad etmir. Matçə qoşulan hər oyunçu bu qaydaları qəbul etmiş sayılır.",
        "accent": ACCENT_VIOLET,
    },
]


async def _post_rules(channel):
    card_path = os.path.join(DATA_DIR or ".", "rules_card.png")
    await asyncio.to_thread(generate_rules_card, RULES_SECTIONS, card_path)
    await channel.send(file=discord.File(card_path, filename="rules_card.png"))


async def _post_leaderboard_5v5(channel):
    global leaderboard_channel_id_5v5, leaderboard_message_id_5v5

    rows = get_leaderboard_5v5(20)
    generate_leaderboard_image(rows, LEADERBOARD_IMAGE_PATH_5V5)

    link_view = discord.ui.View(timeout=None)
    link_view.add_item(discord.ui.Button(
        label="🌐 Tam Siyahını Gör (Vebsayt)", style=discord.ButtonStyle.link, url=PUBLIC_WEB_URL
    ))

    message = await channel.send(
        content=(
            "🎯 **Nextlevelaz FACEIT 5v5 Leaderboard** — hər 60 saniyədə avtomatik yenilənir "
            "(bu şəkil Top-20-ni göstərir).\n"
            f"🌐 Bütün oyunçuların tam, axtarışlı siyahısı üçün vebsaytımıza baxın: {PUBLIC_WEB_URL}"
        ),
        file=discord.File(LEADERBOARD_IMAGE_PATH_5V5, filename="leaderboard_5v5.png"),
        view=link_view
    )

    leaderboard_channel_id_5v5 = channel.id
    leaderboard_message_id_5v5 = message.id
    set_meta("leaderboard_channel_id_5v5", str(channel.id))
    set_meta("leaderboard_message_id_5v5", str(message.id))

    if not refresh_leaderboard_5v5.is_running():
        refresh_leaderboard_5v5.start()


leaderboard_alltime_channel_id_5v5 = None
leaderboard_alltime_message_id_5v5 = None
LEADERBOARD_ALLTIME_IMAGE_PATH_5V5 = "leaderboard_5v5_alltime.png"


async def _post_leaderboard_5v5_alltime(channel):
    """Peak ELO-ya əsaslanan, sezon sıfırlamalarından toxunulmaz ümumi leaderboard."""
    global leaderboard_alltime_channel_id_5v5, leaderboard_alltime_message_id_5v5

    rows = get_leaderboard_5v5_alltime(20)
    generate_leaderboard_image(rows, LEADERBOARD_ALLTIME_IMAGE_PATH_5V5)

    message = await channel.send(
        content=(
            "🏆 **Nextlevelaz FACEIT 5v5 Ümumi Leaderboard** — bütün-zamanların ən yüksək ELO-suna (peak ELO) "
            "əsaslanır, sezon sıfırlamalarından TOXUNULMAZ qalır.\n"
            "Hər 60 saniyədə avtomatik yenilənir."
        ),
        file=discord.File(LEADERBOARD_ALLTIME_IMAGE_PATH_5V5, filename="leaderboard_5v5_alltime.png")
    )

    leaderboard_alltime_channel_id_5v5 = channel.id
    leaderboard_alltime_message_id_5v5 = message.id
    set_meta("leaderboard_alltime_channel_id_5v5", str(channel.id))
    set_meta("leaderboard_alltime_message_id_5v5", str(message.id))

    if not refresh_leaderboard_5v5_alltime.is_running():
        refresh_leaderboard_5v5_alltime.start()


@tasks.loop(seconds=60)
async def refresh_leaderboard_5v5_alltime():
    if leaderboard_alltime_channel_id_5v5 is None or leaderboard_alltime_message_id_5v5 is None:
        return
    channel = bot.get_channel(leaderboard_alltime_channel_id_5v5)
    if channel is None:
        return
    rows = get_leaderboard_5v5_alltime(20)
    generate_leaderboard_image(rows, LEADERBOARD_ALLTIME_IMAGE_PATH_5V5)
    try:
        message = await channel.fetch_message(leaderboard_alltime_message_id_5v5)
        await message.edit(attachments=[discord.File(LEADERBOARD_ALLTIME_IMAGE_PATH_5V5, filename="leaderboard_5v5_alltime.png")])
    except discord.NotFound:
        pass


CHAT_ACTIVITY_IMAGE_PATH = "chat_activity.png"
CHAT_XP_CHANNEL_ID = None
chat_activity_channel_id = None
chat_activity_message_id = None


async def _post_chat_activity_leaderboard(channel):
    global chat_activity_channel_id, chat_activity_message_id
    rows = get_chat_leaderboard(20)
    await asyncio.to_thread(generate_chat_activity_card, rows, CHAT_ACTIVITY_IMAGE_PATH)

    message = await channel.send(
        content="💬 **Həftəlik Aktivlik Lövhəsi** — hər 60 saniyədə avtomatik yenilənir.",
        file=discord.File(CHAT_ACTIVITY_IMAGE_PATH, filename="chat_activity.png"),
    )
    chat_activity_channel_id = channel.id
    chat_activity_message_id = message.id
    set_meta("chat_activity_channel_id", str(channel.id))
    set_meta("chat_activity_message_id", str(message.id))
    try:
        pins = await channel.pins()
        for old in pins:
            if old.author.id == bot.user.id:
                await old.unpin()
    except (discord.Forbidden, discord.HTTPException):
        pass
    try:
        await message.pin()
    except (discord.Forbidden, discord.HTTPException):
        pass

    if not refresh_chat_activity_leaderboard.is_running():
        refresh_chat_activity_leaderboard.start()


@tasks.loop(seconds=60)
async def refresh_chat_activity_leaderboard():
    if chat_activity_channel_id is None or chat_activity_message_id is None:
        return
    channel = bot.get_channel(chat_activity_channel_id)
    if channel is None:
        return
    rows = get_chat_leaderboard(20)
    await asyncio.to_thread(generate_chat_activity_card, rows, CHAT_ACTIVITY_IMAGE_PATH)
    try:
        message = await channel.fetch_message(chat_activity_message_id)
        await message.edit(attachments=[discord.File(CHAT_ACTIVITY_IMAGE_PATH, filename="chat_activity.png")])
    except (discord.NotFound, discord.HTTPException):
        pass


_last_chat_activity_sunday = None


@tasks.loop(minutes=5)
async def weekly_chat_activity_loop():
    """Hər Bazar günü (AZ vaxtı, weekday()==6) saat 23:00-23:59 aralığında bir dəfə işə düşür
    (5 dəqiqəlik interval, dəqiq 23:59-u qaçırmamaq üçün tam saatlıq pəncərə yoxlanılır).
    Bayraq DB-də saxlanılır (bax: season_rotation_loop-dakı eyni izah) ki, bot həmin saat
    aralığında bir neçə dəfə restart olsa belə, elan TƏKRARLANMASIN."""
    global _last_chat_activity_sunday
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    if now.weekday() != 6 or now.hour != 23:
        return
    today_key = now.strftime("%Y-%m-%d")
    if _last_chat_activity_sunday == today_key:
        return
    if get_meta("last_chat_activity_announce") == today_key:
        _last_chat_activity_sunday = today_key
        return
    _last_chat_activity_sunday = today_key
    set_meta("last_chat_activity_announce", today_key)

    top = get_top_chat_activity()
    channel = bot.get_channel(CHAT_XP_CHANNEL_ID) if CHAT_XP_CHANNEL_ID else None
    if top and channel:
        embed = discord.Embed(
            title="🏆 Həftənin Ən Aktivi!",
            description=(f"<@{top['discord_id']}> (**{top['nick']}**) bu həftə **{top['weekly_xp']} XP** "
                         "qazanaraq ən aktiv üzv oldu! 🎉"),
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)

    reset_weekly_chat_xp()
    if chat_activity_channel_id and chat_activity_message_id:
        await refresh_chat_activity_leaderboard()


async def _post_register(channel):
    banner_path = os.path.join(DATA_DIR or ".", "register_banner.png")
    await asyncio.to_thread(generate_register_banner, LOGO_PATH, banner_path)
    view = RegisterView()
    await channel.send(file=discord.File(banner_path, filename="register_banner.png"), view=view)


async def _post_matchmaking_5v5(channel):
    global queue_status_channel_id_5v5, queue_status_message_id_5v5

    banner_path = os.path.join(DATA_DIR or ".", "matchmaking_banner_5v5.png")
    await asyncio.to_thread(generate_matchmaking_banner, QUEUE_OPEN_HOUR, QUEUE_CLOSE_HOUR, LOGO_PATH, banner_path, "5v5")
    view = MatchmakingView5v5()
    await channel.send(
        content="🎯 **FACEIT 5v5** — bu kanaldan yalnız 5v5 sırasına qoşulun.",
        file=discord.File(banner_path, filename="matchmaking_banner_5v5.png"), view=view
    )

    status_image_path = os.path.join(DATA_DIR or ".", "queue_status_5v5.png")
    await asyncio.to_thread(generate_queue_status_card, [], status_image_path, None, 10)
    status_message = await channel.send(file=discord.File(status_image_path, filename="queue_status_5v5.png"))
    queue_status_channel_id_5v5 = channel.id
    queue_status_message_id_5v5 = status_message.id


@bot.tree.command(name="setup_rules", description="[Admin] FACEIT qaydaları mesajını bu kanalda yaradır")
@staff_check()
async def setup_rules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_rules(interaction.channel)
    await interaction.followup.send("✅ Qaydalar mesajı yaradıldı.", ephemeral=True)


@setup_rules.error
async def setup_rules_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_register", description="[Admin] Qeydiyyat mesajını bu kanalda yaradır")
@staff_check()
async def setup_register(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_register(interaction.channel)
    await interaction.followup.send("✅ Qeydiyyat mesajı yaradıldı.", ephemeral=True)


@setup_register.error
async def setup_register_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


async def _execute_server_reset(interaction: discord.Interaction):
    """`/server_sifirla` təsdiqləndikdən sonra əsl işi görür: BÜTÜN kanal/kataqoriya və
    rolları silir (bot-un özünün roluna VƏ idarə olunan/@everyone rollarına toxunmadan),
    sonra istifadəçinin təyin etdiyi 4-kataqoriyalı struktur və 11 rolu yenidən qurur,
    ELO rütbə rollarını yaradır və loqonu bot avatarı/server ikonu kimi tətbiq edir."""
    global LOG_CHANNEL_ID, AUDIT_LOG_CHANNEL_ID
    global LOG_CHANNEL_ID_5V5, SOCIAL_CHANNEL_ID, STANDOFF2_NEWS_CHANNEL_ID
    global MATCH_HISTORY_CHANNEL_ID, SEASON_REWARD_CHANNEL_ID, JOIN_LEAVE_LOG_CHANNEL_ID
    global CHAT_XP_CHANNEL_ID, chat_activity_channel_id

    guild = interaction.guild
    admin_user = interaction.user
    bot_role_ids = {r.id for r in guild.me.roles}

    # ── 1. Bütün rolları sil — @everyone, idarə olunan (bot inteqrasiyası/booster) və
    # botun öz rolları avtomatik keçilir (bunlar silinsə bot öz icazələrini itirər). ──
    deleted_roles = 0
    for role in list(guild.roles):
        if role.name == "@everyone" or role.managed or role.id in bot_role_ids:
            continue
        try:
            await role.delete(reason="server_sifirla: tam sıfırlama")
            deleted_roles += 1
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── 2. Bütün kanal/kataqoriyaları sil (botun tanımadıqları da daxil) ──
    deleted_channels = 0
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="server_sifirla: tam sıfırlama")
            deleted_channels += 1
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── 3. 11 rolu yarat (ən aşağıdan yuxarıya — Discord yeni rolu həmişə @everyone-dan
    # bir pillə yuxarı əlavə edir, ona görə son yaradılan ən yuxarıda çıxır). ──
    role_bot = await guild.create_role(
        name="Bot", color=discord.Color.from_rgb(149, 165, 166),
        reason="server_sifirla", hoist=False, mentionable=False
    )
    role_member = await guild.create_role(
        name=MEMBER_ROLE_NAME, color=discord.Color.from_rgb(138, 92, 230),
        reason="server_sifirla", hoist=True
    )
    role_nla_clan = await guild.create_role(
        name="NLA Clan", color=discord.Color.from_rgb(26, 188, 156),
        reason="server_sifirla", hoist=True
    )
    role_calestify_clan = await guild.create_role(
        name="Calestify Clan", color=discord.Color.from_rgb(233, 30, 99),
        reason="server_sifirla", hoist=True
    )
    role_k4ge_clan = await guild.create_role(
        name="K4GE Clan", color=discord.Color.from_rgb(230, 126, 34),
        reason="server_sifirla", hoist=True
    )
    role_ele1_clan = await guild.create_role(
        name="ELE1 Clan", color=discord.Color.from_rgb(52, 73, 94),
        reason="server_sifirla", hoist=True
    )
    role_partner = await guild.create_role(
        name="Partner", color=discord.Color.from_rgb(241, 196, 15),
        reason="server_sifirla", hoist=True
    )
    role_streamer = await guild.create_role(
        name="Streamer", color=discord.Color.from_rgb(155, 89, 182),
        reason="server_sifirla", hoist=True
    )
    role_moderator = await guild.create_role(
        name="Moderator", color=discord.Color.from_rgb(46, 204, 113),
        permissions=discord.Permissions(kick_members=True, moderate_members=True, manage_messages=True, view_audit_log=True),
        reason="server_sifirla", hoist=True
    )
    role_admin = await guild.create_role(
        name="Admin", color=discord.Color.from_rgb(52, 152, 219),
        permissions=discord.Permissions(
            kick_members=True, ban_members=True, moderate_members=True, manage_messages=True,
            manage_channels=True, manage_roles=True, view_audit_log=True, mention_everyone=True
        ),
        reason="server_sifirla", hoist=True
    )
    role_founder = await guild.create_role(
        name="Founder", color=discord.Color.from_rgb(230, 30, 60),
        permissions=discord.Permissions(administrator=True), reason="server_sifirla", hoist=True
    )
    staff_roles = [role_founder, role_admin]

    # ── 4. Yeni struktur: 4 kataqoriya ──
    category_announcements = await guild.create_category(CATEGORY_ANNOUNCEMENTS_NAME)
    category_general = await guild.create_category(CATEGORY_GENERAL_NAME)
    category_5v5 = await guild.create_category(CATEGORY_5V5_NAME)
    staff_view_overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    for r in staff_roles + [role_moderator]:
        staff_view_overwrites[r] = discord.PermissionOverwrite(view_channel=True)
    category_staff = await guild.create_category(CATEGORY_STAFF_NAME, overwrites=staff_view_overwrites)

    announce_overwrites = {guild.default_role: discord.PermissionOverwrite(send_messages=False)}

    # ── Kataqoriya 1: Elanlar ──
    ch_social = await guild.create_text_channel("social-media", category=category_announcements, overwrites=announce_overwrites)
    ch_duyuru = await guild.create_text_channel("announcements", category=category_announcements, overwrites=announce_overwrites)
    ch_giveaway = await guild.create_text_channel("giveaways", category=category_announcements, overwrites=announce_overwrites)
    ch_news = await guild.create_text_channel("news", category=category_announcements, overwrites=announce_overwrites)
    ch_join_leave = await guild.create_text_channel("join-leave-log", category=category_announcements, overwrites=announce_overwrites)

    # ── Kataqoriya 2: Community ──
    await guild.create_voice_channel("Voice Chat 1", category=category_general)
    await guild.create_voice_channel("Voice Chat 2", category=category_general)
    await guild.create_voice_channel("Voice Chat 3", category=category_general)
    ch_chat_xp = await guild.create_text_channel("general-chat", category=category_general)
    ch_media = await guild.create_text_channel("media-share", category=category_general)
    ch_bot_commands = await guild.create_text_channel("bot-commands", category=category_general)
    ch_chat_lb = await guild.create_text_channel("activity-board", category=category_general, overwrites=announce_overwrites)

    # ── Kataqoriya 3: FACEIT 5V5 ──
    ch_register = await guild.create_text_channel("registration", category=category_5v5, overwrites=announce_overwrites)
    ch_rules = await guild.create_text_channel("rules", category=category_5v5, overwrites=announce_overwrites)
    ch_matchmaking_5v5 = await guild.create_text_channel("matchmaking", category=category_5v5, overwrites=announce_overwrites)
    ch_log_5v5 = await guild.create_text_channel("match-results", category=category_5v5)
    ch_history = await guild.create_text_channel("match-history", category=category_5v5, overwrites=announce_overwrites)
    current_season_5v5 = get_or_create_current_season("5v5")
    ch_leaderboard_5v5 = await guild.create_text_channel(
        f"season-leaderboard-{current_season_5v5['season_number']}", category=category_5v5, overwrites=announce_overwrites
    )
    ch_general_leaderboard = await guild.create_text_channel("general-leaderboard", category=category_5v5, overwrites=announce_overwrites)
    ch_season_reward = await guild.create_text_channel("season-rewards", category=category_5v5, overwrites=announce_overwrites)
    await _get_or_create_warmup_channel(guild, mode="5v5")

    # ── Kataqoriya 4: Staff ──
    await guild.create_voice_channel("Staff Voice", category=category_staff)
    ch_staff_chat = await guild.create_text_channel("staff-chat", category=category_staff)
    ch_audit = await guild.create_text_channel("server-log", category=category_staff)

    # ── Kataqoriya 5: Tickets (klan qoşulma + Gold/Boost/Emulator satışı) ──
    category_tickets = await guild.create_category(TICKET_CATEGORY_NAME)
    ch_ticket_panel = await guild.create_text_channel("open-ticket", category=category_tickets, overwrites=announce_overwrites)

    LOG_CHANNEL_ID = ch_log_5v5.id
    set_meta("log_channel_id", ch_log_5v5.id)
    LOG_CHANNEL_ID_5V5 = ch_log_5v5.id
    set_meta("log_channel_id_5v5", ch_log_5v5.id)
    AUDIT_LOG_CHANNEL_ID = ch_audit.id
    set_meta("audit_log_channel_id", ch_audit.id)
    SOCIAL_CHANNEL_ID = ch_social.id
    set_meta("social_channel_id", ch_social.id)
    STANDOFF2_NEWS_CHANNEL_ID = ch_news.id
    set_meta("standoff2_news_channel_id", ch_news.id)
    JOIN_LEAVE_LOG_CHANNEL_ID = ch_join_leave.id
    set_meta("join_leave_log_channel_id", ch_join_leave.id)
    CHAT_XP_CHANNEL_ID = ch_chat_xp.id
    set_meta("chat_xp_channel_id", ch_chat_xp.id)
    chat_activity_channel_id = ch_chat_lb.id
    set_meta("chat_activity_channel_id", ch_chat_lb.id)
    MATCH_HISTORY_CHANNEL_ID = ch_history.id
    set_meta("match_history_channel_id", ch_history.id)
    SEASON_REWARD_CHANNEL_ID = ch_season_reward.id
    set_meta("season_reward_channel_id", ch_season_reward.id)

    # ── 5. ELO rütbə rolları (Nova/Elite/... — 11 roldan ayrı sistemdir, onların yanında işləyir) ──
    created_roles, synced_players = await _create_rank_roles(guild)

    # ── 6. Hər kəsə NLA Member, botlara Bot rolu ver (yeni qoşulanlara avtomatik verilməsi on_member_join-də) ──
    member_role_given = 0
    for member in guild.members:
        try:
            if member.bot:
                await member.add_roles(role_bot, reason="server_sifirla: Bot rolu təyinatı")
            else:
                await member.add_roles(role_member, reason="server_sifirla: ilkin NLA Member təyinatı")
                member_role_given += 1
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── 7. Loqo: bot avatarı + server ikonu ──
    avatar_status = icon_status = "❌ loqo faylı tapılmadı"
    try:
        with open(NEXTLEVELAZ_LOGO_PATH, "rb") as f:
            logo_bytes = f.read()
        try:
            await bot.user.edit(avatar=logo_bytes)
            avatar_status = "✅ yeniləndi"
        except (discord.HTTPException, discord.Forbidden) as e:
            avatar_status = f"❌ xəta: {e}"
        try:
            await guild.edit(icon=logo_bytes)
            icon_status = "✅ yeniləndi"
        except (discord.HTTPException, discord.Forbidden) as e:
            icon_status = f"❌ xəta: {e}"
    except (FileNotFoundError, OSError):
        pass

    # ── 8. Tanıtım mesajları ──
    await _post_register(ch_register)
    await _post_matchmaking_5v5(ch_matchmaking_5v5)
    await _post_rules(ch_rules)
    await _post_leaderboard_5v5(ch_leaderboard_5v5)
    await _post_leaderboard_5v5_alltime(ch_general_leaderboard)
    await ch_season_reward.send(
        "🏆 **Sezon Mükafatları** — hər sezon sonunda Top-3 ELO sırası Gold qazanır:\n"
        "🥇 1-ci yer: **3000 Gold**  ·  🥈 2-ci yer: **2000 Gold**  ·  🥉 3-cü yer: **1000 Gold**\n"
        "Nəticələr burada avtomatik elan olunacaq."
    )
    await ch_history.send("📜 **Match History** — bitmiş bütün 5v5 matçların yekun nəticələri burada arxivlənir.")
    await ch_news.send("📰 **News** — Standoff 2 rəsmi yenilikləri və gündəlik AI xülasəsi burada paylaşılır.")
    await ch_join_leave.send("📥 **Join/Leave Log** — üzv serverə qoşulanda/ayrılanda bura avtomatik qeyd düşür.")
    await ch_duyuru.send("📢 **Announcements** — Nextlevelaz-ın rəsmi elanları burada paylaşılacaq.")
    await ch_social.send(
        "📱 **Social Media** — Nextlevelaz-ı bütün platformalarda izləyin! Bot burada mütəmadi "
        "olaraq TikTok/YouTube paylaşımlarımızı xatırladacaq."
    )
    await ch_giveaway.send(
        "🎉 **Giveaways** — bütün hədiyyə çəkilişləri burada elan olunacaq. `/giveaway_create` ilə admin yeni giveaway başlada bilər."
    )
    await ch_chat_xp.send(
        "💬 **General Chat** — burada yazdığın hər mesaja görə XP qazanırsan! "
        f"Hər Bazar günü saat 23:59 həftənin ən aktivi elan olunacaq. Lövhə: {ch_chat_lb.mention}"
    )
    await ch_media.send("🖼️ **Media Share** — oyun klipləri, şəkillər və digər media paylaşımları üçün.")
    await ch_bot_commands.send("🤖 **Bot Commands** — bot komandalarını burada sərbəst istifadə edə bilərsiniz.")
    await _post_chat_activity_leaderboard(ch_chat_lb)
    await ch_staff_chat.send("🛡️ **Staff Chat** — yalnız rəhbərlik görə bilər.")
    await _post_ticket_panel(ch_ticket_panel)

    summary = (
        "✅ **Server tam sıfırlanıb yeni strukturda yenidən quruldu!**\n\n"
        f"🗑️ Silinən rollar: {deleted_roles} · Silinən kanal/kataqoriya: {deleted_channels}\n"
        f"🖼️ Bot avatarı: {avatar_status} · Server ikonu: {icon_status}\n"
        f"🏅 ELO rütbə rolları: {len(created_roles)} yaradıldı, {synced_players} oyunçu sinxronlaşdı\n"
        f"👤 {member_role_given} üzvə **{MEMBER_ROLE_NAME}** rolu verildi (yeni qoşulanlara avtomatik veriləcək)\n\n"
        "Yaradılan rollar (yuxarıdan aşağı): **Founder → Admin → Moderator → Streamer → Partner → "
        "NLA Clan → Calestify Clan → K4GE Clan → ELE1 Clan → NLA Member → Bot**\n\n"
        f"Kanallar 5 kataqoriyaya bölünüb: **{CATEGORY_ANNOUNCEMENTS_NAME}**, **{CATEGORY_GENERAL_NAME}**, "
        f"**{CATEGORY_5V5_NAME}**, **{CATEGORY_STAFF_NAME}**, **{TICKET_CATEGORY_NAME}**.\n\n"
        f"**{CATEGORY_ANNOUNCEMENTS_NAME}**\n"
        f"📱 Social media: {ch_social.mention}\n"
        f"📢 Announcements: {ch_duyuru.mention}\n"
        f"🎉 Giveaways: {ch_giveaway.mention}\n"
        f"📰 News: {ch_news.mention}\n"
        f"📥 Join/Leave log: {ch_join_leave.mention}\n\n"
        f"**{CATEGORY_GENERAL_NAME}**\n"
        f"🔊 3 səsli kanal\n"
        f"💬 General chat: {ch_chat_xp.mention}\n"
        f"🖼️ Media share: {ch_media.mention}\n"
        f"🤖 Bot commands: {ch_bot_commands.mention}\n\n"
        f"**{CATEGORY_5V5_NAME}**\n"
        f"📋 Registration: {ch_register.mention}\n"
        f"📜 Rules: {ch_rules.mention}\n"
        f"🎮 Matchmaking: {ch_matchmaking_5v5.mention}\n"
        f"🏁 Match results: {ch_log_5v5.mention}\n"
        f"📜 Match history: {ch_history.mention}\n"
        f"🏆 Season leaderboard: {ch_leaderboard_5v5.mention}\n"
        f"🏆 General leaderboard: {ch_general_leaderboard.mention}\n"
        f"🎁 Season rewards: {ch_season_reward.mention}\n\n"
        f"**{CATEGORY_STAFF_NAME}** (yalnız Founder/Admin/Moderator görür)\n"
        f"🔊 Staff voice\n"
        f"💬 Staff chat: {ch_staff_chat.mention}\n"
        f"🛡️ Server log: {ch_audit.mention}\n\n"
        f"**{TICKET_CATEGORY_NAME}**\n"
        f"🎫 Ticket aç: {ch_ticket_panel.mention} (klan qoşulma + Gold/Boost/Emulator satışı — seçimə görə özəl kanal açılır)\n\n"
        "⚠️ **Diqqət:** köhnə rol təyinatları itdi — hər kəsə YENİ Founder/Admin/Moderator/Streamer/Partner/klan "
        "rollarını əl ilə verməlisiniz (yalnız NLA Member və Bot avtomatik verildi). Oyunçu datası (qeydiyyat/"
        "statistika/coin/sezon) bu komanda ilə TOXUNULMADI — onu ayrıca `/admin_full_reset` ilə "
        "sıfırlaya bilərsiniz (Sezon 1-dən yenidən başlayır)."
    )

    try:
        await interaction.followup.send(summary, ephemeral=True)
    except discord.HTTPException:
        pass
    try:
        await admin_user.send(summary)
    except discord.HTTPException:
        pass


class ServerResetConfirmView(discord.ui.View):
    def __init__(self, requester_id):
        super().__init__(timeout=60)
        self.requester_id = requester_id

    @discord.ui.button(label="Bəli, SERVERİ TAM SIFIRLA", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı çağıran şəxs üçündür.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="⏳ Server sıfırlanır — kanal/rol sayına görə bir neçə dəqiqə çəkə bilər...", view=self
        )
        await _execute_server_reset(interaction)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı çağıran şəxs üçündür.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Ləğv edildi, heç nə silinmədi.", view=self)


@bot.tree.command(name="server_sifirla", description="[Admin] TƏHLÜKƏLİ: serverin BÜTÜN kanal/rollarını silib Nextlevelaz formatında yenidən qurur")
@staff_check()
async def server_sifirla_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return
    await interaction.response.send_message(
        "⚠️ **DİQQƏT — GERİ QAYTARILA BİLMƏZ!**\n\n"
        "Bu əməliyyat serverdəki **BÜTÜN kanal, kataqoriya və rolları** (bot-un tanımadıqları da daxil "
        "olmaqla, `@everyone`, Discord-un özəl idarə etdiyi rollar və botun öz rolu xaric) həmişəlik "
        "siləcək və onların yerinə yeni struktur quracaq:\n"
        "• **📢 ANNOUNCEMENTS** — social-media, announcements, giveaways, news, join-leave-log\n"
        "• **💬 COMMUNITY** — 3 səsli kanal, general-chat, media-share, bot-commands\n"
        "• **🎯 FACEIT 5V5** — registration, rules, matchmaking, match-results, match-history, "
        "season/general leaderboard, season-rewards\n"
        "• **🛡️ STAFF** (yalnız Founder/Admin/Moderator görür) — staff voice, staff-chat, server-log\n"
        "• **🎫 TICKETS** — klan qoşulma (NLA/Calestify/K4GE/ELE1) + Gold/Boost/Emulator satışı üçün düymə/seçim əsaslı özəl ticket sistemi\n\n"
        "Yeni rollar yaradılacaq: **Founder, Admin, Moderator, Streamer, Partner, NLA Clan, Calestify Clan, "
        "K4GE Clan, ELE1 Clan, NLA Member, Bot** (hər kəsə NLA Member, botlara Bot rolu avtomatik veriləcək, "
        "yeni qoşulanlara NLA Member avtomatik veriləcək). Köhnə rol təyinatları itəcək — digərlərini əl ilə "
        "verməlisiniz.\n\n"
        "Bot avatarı və server ikonu yeni loqo ilə yenilənəcək. ELO rütbə rolları yenidən yaradılacaq.\n\n"
        "🚫 **İtiriləcəklər:** bütün rol təyinatları (yenilərini əl ilə verməlisiniz), "
        "bütün köhnə kanal mesaj tarixçəsi, bütün köhnə kanal/rol strukturu.\n"
        "✅ **TOXUNULMAYACAQ:** oyunçu qeydiyyatı/statistika/coin (bunu ayrıca `/admin_full_reset` sıfırlayır).\n\n"
        "Davam etmək istədiyinizə **əminsiniz**?",
        view=ServerResetConfirmView(interaction.user.id),
        ephemeral=True
    )


@server_sifirla_cmd.error
async def server_sifirla_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET SİSTEMİ — klan qoşulma (NLA/Calestify/K4GE/ELE1) + Gold/Boost/Emulator satışı
# ═══════════════════════════════════════════════════════════════════════════════

TICKET_CATEGORY_NAME = "🎫 TICKETS"
TICKET_PANEL_CHANNEL_ID = None
TICKET_CATEGORY_ID = None

TICKET_TYPES = [
    ("clan_nla", "Next Level Azerbaijan Clan", "🏷️", "Next Level Azerbaijan klanına qoşulmaq istəyirəm"),
    ("clan_calestify", "Calestify Clan", "🏷️", "Calestify klanına qoşulmaq istəyirəm"),
    ("clan_k4ge", "K4GE Clan", "🏷️", "K4GE klanına qoşulmaq istəyirəm"),
    ("clan_ele1", "ELE1 Clan", "🏷️", "ELE1 klanına qoşulmaq istəyirəm"),
    ("gold", "Gold Satışı", "💰", "Gold almaq istəyirəm"),
    ("boost", "Boost Satışı", "🚀", "ELO/rank boost almaq istəyirəm"),
    ("emulator", "Emulator Satışı", "📱", "Emulator almaq istəyirəm"),
]
TICKET_TYPE_LABELS = {value: label for value, label, emoji, desc in TICKET_TYPES}


def _slugify_for_channel(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:20] or "user"


async def _get_ticket_category(guild: discord.Guild):
    if TICKET_CATEGORY_ID:
        cat = guild.get_channel(TICKET_CATEGORY_ID)
        if cat:
            return cat
    return discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)


async def _open_ticket(interaction: discord.Interaction, ticket_type: str):
    guild = interaction.guild
    user = interaction.user

    existing = get_open_ticket(user.id)
    if existing and existing["channel_id"] and guild.get_channel(existing["channel_id"]):
        await interaction.response.send_message(
            f"⚠️ Artıq açıq bir ticket-iniz var: <#{existing['channel_id']}>. "
            "Yeni ticket açmadan əvvəl onu bağlayın.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    category = await _get_ticket_category(guild)
    if category is None:
        category = await guild.create_category(TICKET_CATEGORY_NAME)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    for role_name in ("Founder", "Admin", "Moderator"):
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    short_type = ticket_type.replace("clan_", "")
    channel_name = f"ticket-{short_type}-{_slugify_for_channel(user.name)}"
    channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

    ticket_id = create_ticket(user.id, channel.id, ticket_type)

    label = TICKET_TYPE_LABELS.get(ticket_type, ticket_type)
    embed = discord.Embed(
        title=f"🎫 Ticket — {label}",
        description=(
            f"Salam {user.mention}! Bu ticket **{label}** mövzusunda açıldı.\n"
            "Zəhmət olmasa tələbinizi aşağıda ətraflı izah edin — tezliklə heyət üzvü sizə cavab verəcək.\n\n"
            "Ticket-i bağlamaq üçün aşağıdakı düyməni istifadə edin."
        ),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.set_footer(text=f"Ticket #{ticket_id} · {user}")
    await channel.send(content=user.mention, embed=embed, view=TicketCloseView())

    await interaction.followup.send(f"✅ Ticket-iniz yaradıldı: {channel.mention}", ephemeral=True)


class TicketSelectView(discord.ui.View):
    """Ticket panelindəki seçim menyusu — persistent (bot restart olsa belə işləyir)."""
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label=label, value=value, emoji=emoji, description=desc[:100])
            for value, label, emoji, desc in TICKET_TYPES
        ]
        select = discord.ui.Select(
            placeholder="Mövzu seçin...", options=options, custom_id="ticket_type_select"
        )
        select.callback = self._on_select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        select = self.children[0]
        await _open_ticket(interaction, select.values[0])


class TicketCloseView(discord.ui.View):
    """Hər ticket kanalının içində göstərilən 'Bağla' düyməsi — persistent."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket-i bağla", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_btn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = get_ticket_by_channel(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("❌ Bu kanal aktiv ticket kimi tapılmadı.", ephemeral=True)
            return
        if interaction.user.id != ticket["discord_id"] and not is_staff(interaction):
            await interaction.response.send_message("❌ Yalnız ticket sahibi və ya heyət bağlaya bilər.", ephemeral=True)
            return
        close_ticket(ticket["id"])
        await interaction.response.send_message("🔒 Ticket 5 saniyə sonra bağlanıb silinəcək...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Ticket bağlandı")
        except (discord.Forbidden, discord.HTTPException):
            pass


async def _post_ticket_panel(channel):
    global TICKET_PANEL_CHANNEL_ID, TICKET_CATEGORY_ID
    embed = discord.Embed(
        title="🎫 Ticket Sistemi",
        description=(
            "Aşağıdan mövzu seçərək özəl ticket kanalı açın:\n\n"
            "🏷️ **Klan qoşulma** — Next Level Azerbaijan, Calestify, K4GE, ELE1\n"
            "💰 **Gold satışı**  ·  🚀 **Boost satışı**  ·  📱 **Emulator satışı**\n\n"
            "Seçim etdikdən sonra sizin və heyətin görə biləcəyi özəl kanal yaradılacaq."
        ),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    await channel.send(embed=embed, view=TicketSelectView())
    TICKET_PANEL_CHANNEL_ID = channel.id
    set_meta("ticket_panel_channel_id", channel.id)
    if channel.category:
        TICKET_CATEGORY_ID = channel.category.id
        set_meta("ticket_category_id", channel.category.id)


class FullResetConfirmView(discord.ui.View):
    def __init__(self, requester_id):
        super().__init__(timeout=60)
        self.requester_id = requester_id

    @discord.ui.button(label="Bəli, HƏR ŞEYİ SİL", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı çağıran şəxs üçündür.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="⏳ Silinir...", view=self)
        reset_all_player_data()
        await interaction.edit_original_response(
            content="✅ Bütün oyunçu qeydiyyatları, matç tarixçəsi, balanslar, nailiyyətlər, "
                    "inventar və mükafat tarixçəsi silindi. Bot konfiqurasiyası (kanallar və s.) toxunulmadı.",
            view=None
        )

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı çağıran şəxs üçündür.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Ləğv edildi, heç nə silinmədi.", view=self)


@bot.tree.command(name="admin_full_reset", description="[Admin] TƏHLÜKƏLİ: bütün oyunçu/matç/balans/nailiyyət/inventar datasını həmişəlik silir")
@staff_check()
async def admin_full_reset_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⚠️ **DİQQƏT — geri qaytarıla bilməz!**\n\n"
        "Bu əməliyyat aşağıdakıların HAMISINI həmişəlik siləcək:\n"
        "• Bütün qeydiyyatlı oyunçular (ELO, K/D, seriya)\n"
        "• Bütün matç tarixçəsi (nömrələmə də 0-dan başlayacaq)\n"
        "• Bütün coin/AZN balansları\n"
        "• Bütün nailiyyətlər, ləqəblər, quest/tapşırıq irəliləyişi\n"
        "• Bütün inventar (banner/çərçivə/tema/skin/ELO kartları daxil)\n"
        "• Bütün squad-lar və referral tarixçəsi\n\n"
        "Bot konfiqurasiyası (kanal ID-ləri, admin loglar, giveaway-lər, market kataloqu) TOXUNULMAYACAQ.\n\n"
        "Davam etmək istədiyinizə əminsiniz?",
        view=FullResetConfirmView(interaction.user.id),
        ephemeral=True
    )


@admin_full_reset_cmd.error
async def admin_full_reset_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="giveaway_create", description="[Admin] Giveaway yaradır (gizli qalib və ya əsl-random seçim)")
@app_commands.describe(
    mukafat="Mükafatın adı (məs: 1000 Gold)",
    saat="Çəkilişin neçə saat sürəcəyi (0 ola bilər)",
    deqiqe="Çəkilişin neçə dəqiqə sürəcəyi (0 ola bilər)",
    elan_kanal="Giveaway-in elan olunacağı kanal",
    qalib="Gizli qalib (yalnız siz görürsünüz) — boş buraxsanız 🎉 reaksiya verənlər arasından ƏSL RANDOM seçilir"
)
@staff_check()
async def giveaway_create(
    interaction: discord.Interaction,
    mukafat: str,
    saat: int,
    deqiqe: int,
    elan_kanal: discord.TextChannel,
    qalib: discord.Member = None
):
    total_seconds = saat * 3600 + deqiqe * 60
    if total_seconds <= 0:
        await interaction.response.send_message("❌ Müddət 0-dan böyük olmalıdır.", ephemeral=True)
        return

    end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=total_seconds)
    end_unix = int(end_time.timestamp())

    mode_line = "🎲 Qalib 🎉 reaksiya verənlər arasından ƏSL RANDOM seçiləcək!" if qalib is None else ""
    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=f"**Mükafat:** {mukafat}\n\nQoşulmaq üçün 🎉 emojisinə bas!\n\n⏰ Bitmə vaxtı: <t:{end_unix}:R>"
                    + (f"\n\n{mode_line}" if mode_line else ""),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.set_footer(text="Nextlevelaz")

    message = await elan_kanal.send(embed=embed)
    await message.add_reaction("🎉")

    create_giveaway(mukafat, end_unix, qalib.id if qalib else 0, elan_kanal.id, message.id)

    await interaction.response.send_message(
        f"✅ Giveaway yaradıldı ({'gizli qalib: ' + qalib.mention if qalib else 'əsl random seçim'}).\n"
        f"📍 Kanal: {elan_kanal.mention}\n⏰ Bitmə: <t:{end_unix}:F>",
        ephemeral=True
    )


@giveaway_create.error
async def giveaway_create_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


class AnnouncementModal(discord.ui.Modal, title="Yeni Elan"):
    baslik = discord.ui.TextInput(
        label="Başlıq", placeholder="məs: Yeni Turnir Elanı!",
        max_length=100
    )
    metn = discord.ui.TextInput(
        label="Elan mətni", style=discord.TextStyle.paragraph,
        placeholder="Elanın tam mətnini buraya yazın...", max_length=1800
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        card_path = os.path.join(DATA_DIR or ".", f"announcement_{interaction.id}.png")
        await asyncio.to_thread(generate_announcement_card, str(self.baslik), str(self.metn), card_path)
        try:
            await self.channel.send(file=discord.File(card_path, filename="elan.png"))
        finally:
            if os.path.exists(card_path):
                os.remove(card_path)
        await interaction.followup.send(f"✅ Elan {self.channel.mention} kanalına göndərildi.", ephemeral=True)


@bot.tree.command(name="elan", description="[Admin] Sərbəst mətndən vizual, peşəkar elan kartı yaradıb kanala göndərir")
@app_commands.describe(kanal="Elanın göndəriləcəyi kanal (boş buraxsanız bu kanala göndərilir)")
@staff_check()
async def elan(interaction: discord.Interaction, kanal: discord.TextChannel = None):
    target = kanal or interaction.channel
    await interaction.response.send_modal(AnnouncementModal(target))


@elan.error
async def elan_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


async def _render_coins(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    balance = get_coins(discord_id)
    logs = get_coin_logs(discord_id, limit=15)
    card_path = os.path.join(DATA_DIR or ".", f"coins_{discord_id}.png")
    await asyncio.to_thread(generate_coin_logs_card, logs, balance, None, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="coins.png"), ephemeral=True)


async def _render_stats(interaction: discord.Interaction, target_id: int):
    await interaction.response.defer(ephemeral=True)
    player_data = get_player_stats_dict(target_id)
    achievements = []
    card_path = os.path.join(DATA_DIR or ".", f"stats_{target_id}.png")
    await asyncio.to_thread(generate_stats_card, player_data, achievements, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="stats.png"), ephemeral=True)


async def _render_history(interaction: discord.Interaction, target_id: int):
    await interaction.response.defer(ephemeral=True)
    history = get_player_match_history(target_id, limit=10)
    card_path = os.path.join(DATA_DIR or ".", f"history_{target_id}.png")
    await asyncio.to_thread(generate_match_history_card, history, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="history.png"), ephemeral=True)


async def _render_maps(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    stats = get_map_stats(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"maps_{discord_id}.png")
    await asyncio.to_thread(generate_map_stats_card, nick, stats, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="maps.png"), ephemeral=True)


async def _render_elo_chart(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    history = list(reversed(get_player_match_history(discord_id, limit=30)))
    chart_data = [{"match_number": h["match_number"], "elo_after": h["elo_after"]} for h in history]
    card_path = os.path.join(DATA_DIR or ".", f"elo_chart_{discord_id}.png")
    await asyncio.to_thread(generate_elo_chart_card, nick, chart_data, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="elo_chart.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMİN PANELİ
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="admin_oyuncu", description="[Admin] Oyunçunun bütün məlumatlarını göstərir")
@app_commands.describe(oyunçu="Baxılacaq oyunçu")
@staff_check()
async def admin_oyuncu_cmd(interaction: discord.Interaction, oyunçu: discord.Member):
    data = get_player_stats_dict(oyunçu.id)
    if not data:
        await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
        return
    stats5 = get_player_5v5(oyunçu.id) or {"elo": 1000, "wins": 0, "losses": 0, "kills": 0, "assists": 0, "deaths": 0, "win_streak": 0, "max_streak": 0}
    embed = discord.Embed(title=f"🔧 Admin — {oyunçu.display_name}", color=discord.Color.blurple())
    embed.add_field(name="Nick / SO2 ID", value=f"{data['nick']} / {data['so2_id']}", inline=False)
    embed.add_field(name="ELO (5v5)", value=str(stats5["elo"]), inline=True)
    embed.add_field(name="Qələbə/Məğlub (5v5)", value=f"{stats5['wins']}/{stats5['losses']}", inline=True)
    embed.add_field(name="K/A/D (5v5)", value=f"{stats5['kills']}/{stats5['assists']}/{stats5['deaths']}", inline=True)
    embed.add_field(name="Seriya (5v5)", value=f"{stats5['win_streak']} (max {stats5['max_streak']})", inline=True)
    embed.add_field(name="Coin", value=str(data["coins"]), inline=True)
    embed.add_field(name="Ban", value="🔴 Bəli" if is_banned(oyunçu.id) else "🟢 Xeyr", inline=True)
    embed.set_footer(text=f"Discord ID: {oyunçu.id}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@admin_oyuncu_cmd.error
async def admin_oyuncu_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


ADMIN_FIELD_CHOICES = [
    app_commands.Choice(name="ELO", value="elo"),
    app_commands.Choice(name="Coin", value="coins"),
    app_commands.Choice(name="Qələbə (wins)", value="wins"),
    app_commands.Choice(name="Məğlubiyyət (losses)", value="losses"),
    app_commands.Choice(name="Kill", value="kills"),
    app_commands.Choice(name="Assist", value="assists"),
    app_commands.Choice(name="Ölüm (deaths)", value="deaths"),
    app_commands.Choice(name="Nick (so2_nick)", value="so2_nick"),
    app_commands.Choice(name="SO2 ID", value="so2_id"),
]
ADMIN_NUMERIC_FIELDS = {"elo", "coins", "wins", "losses", "kills", "assists", "deaths"}
ADMIN_5V5_STAT_FIELDS = {"elo", "wins", "losses", "kills", "assists", "deaths"}


@bot.tree.command(name="admin_duzelt", description="[Admin] Oyunçunun bir sahəsini dəyişir")
@app_commands.describe(oyunçu="Dəyişəcəyiniz oyunçu", sahə="Dəyişəcəyiniz sahə", dəyər="Yeni dəyər")
@app_commands.choices(sahə=ADMIN_FIELD_CHOICES)
@staff_check()
async def admin_duzelt_cmd(interaction: discord.Interaction, oyunçu: discord.Member,
                            sahə: app_commands.Choice[str], dəyər: str):
    if not get_player(oyunçu.id):
        await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
        return

    field = sahə.value
    if field in ADMIN_NUMERIC_FIELDS:
        try:
            value = int(dəyər)
        except ValueError:
            await interaction.response.send_message("❌ Bu sahə üçün rəqəm daxil edin.", ephemeral=True)
            return
    else:
        value = dəyər

    if field in ADMIN_5V5_STAT_FIELDS:
        stats5 = get_player_5v5(oyunçu.id) or {"elo": 1000, "wins": 0, "losses": 0, "kills": 0, "assists": 0, "deaths": 0}
        old_val = stats5.get(field, 0)
        admin_set_player_field_5v5(oyunçu.id, field, value)
    else:
        old_data = get_player_stats_dict(oyunçu.id)
        old_val = old_data.get("nick" if field == "so2_nick" else field, "?")
        if not admin_set_player_field(oyunçu.id, field, value):
            await interaction.response.send_message("❌ Bu sahə dəyişdirilə bilməz.", ephemeral=True)
            return

    log_admin_action("admin_duzelt", oyunçu.id, field, str(old_val), str(value), "-", interaction.user.id)
    await _post_audit_log("admin_duzelt", oyunçu.id, field, old_val, value, "-", interaction.user.id)

    if field == "elo":
        await _sync_rank_role_5v5(interaction.guild, oyunçu.id, value)

    embed = discord.Embed(title="✅ Dəyişdirildi", color=discord.Color.green())
    embed.add_field(name=oyunçu.display_name, value=f"**{sahə.name}**: {old_val} → **{value}**")
    embed.set_footer(text=f"Admin: {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@admin_duzelt_cmd.error
async def admin_duzelt_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="admin_matclar", description="[Admin] Son matçların siyahısını göstərir")
@app_commands.describe(say="Neçə matç göstərilsin (default 15)")
@staff_check()
async def admin_matclar_cmd(interaction: discord.Interaction, say: int = 15):
    matches = get_recent_matches(limit=say)
    if not matches:
        await interaction.response.send_message("Hələ heç bir matç qeyd olunmayıb.", ephemeral=True)
        return
    lines = []
    for m in matches:
        dt = datetime.datetime.utcfromtimestamp(m["played_at"]) + datetime.timedelta(hours=4)
        lines.append(
            f"**#{m['match_number']}** ({m['match_type']}, {dt.strftime('%d.%m %H:%M')}) — "
            f"✅ {', '.join(m['winner_nicks'])} vs ❌ {', '.join(m['loser_nicks'])}"
        )
    embed = discord.Embed(title="📋 Son matçlar", description="\n".join(lines), color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@admin_matclar_cmd.error
async def admin_matclar_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


class ConfirmDeleteMatchView(discord.ui.View):
    def __init__(self, match_number, admin_id):
        super().__init__(timeout=60)
        self.match_number = match_number
        self.admin_id = admin_id

    @discord.ui.button(label="Təsdiqlə və sil", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı işlədən admin üçündür.", ephemeral=True)
            return
        affected = delete_match_and_revert(self.match_number)
        for child in self.children:
            child.disabled = True
        if affected is None:
            await interaction.response.edit_message(content="❌ Matç artıq tapılmadı.", embed=None, view=self)
            return
        log_admin_action("admin_matc_sil", 0, "match_history", str(self.match_number), "silindi", "-", self.admin_id)
        await _post_audit_log("admin_matc_sil", 0, "match_history", self.match_number, "silindi", "-", self.admin_id)
        for p in affected:
            await _sync_rank_role_5v5(interaction.guild, p["discord_id"], p["new_elo"])
        lines = [f"{p['nick']}: {p['old_elo']} → {p['new_elo']}" for p in affected]
        embed = discord.Embed(
            title=f"🗑️ Matç No{self.match_number} silindi",
            description="\n".join(lines) + "\n\n⚠️ Coin/kill-assist-death/nailiyyət dəyişiklikləri geri alınmadı.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Ləğv edildi.", embed=None, view=self)


@bot.tree.command(name="admin_matc_sil", description="[Admin] Bir matçı bazadan silir və ELO-nu geri qaytarır")
@app_commands.describe(matc_no="Silinəcək matçın nömrəsi")
@staff_check()
async def admin_matc_sil_cmd(interaction: discord.Interaction, matc_no: int):
    match = get_match_by_number(matc_no)
    if not match:
        await interaction.response.send_message(f"❌ Matç No{matc_no} tapılmadı.", ephemeral=True)
        return
    embed = discord.Embed(
        title=f"⚠️ Matç No{matc_no} silinsin?",
        description=(
            f"Tip: {match['match_type']}\n"
            "Bu əməliyyat geri qaytarıla bilməz — ELO və qələbə/məğlubiyyət sayı "
            "avtomatik geri alınacaq, coin/kill-assist-death/nailiyyət isə saxlanılacaq."
        ),
        color=discord.Color.orange()
    )
    view = ConfirmDeleteMatchView(matc_no, interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@admin_matc_sil_cmd.error
async def admin_matc_sil_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


class ConfirmSwapMatchView(discord.ui.View):
    def __init__(self, match_number, admin_id):
        super().__init__(timeout=60)
        self.match_number = match_number
        self.admin_id = admin_id

    @discord.ui.button(label="Təsdiqlə və dəyiş", style=discord.ButtonStyle.danger, emoji="🔄")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı işlədən admin üçündür.", ephemeral=True)
            return
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True

        match = get_match_by_number(self.match_number)
        if not match:
            await interaction.edit_original_response(content="❌ Matç artıq tapılmadı.", embed=None, view=self)
            return

        if match["match_type"] != "5v5":
            await interaction.edit_original_response(
                content="❌ Bu alət yalnız 5v5 matçlar üçündür (köhnə 2v2 matçlar daha dəstəklənmir).",
                embed=None, view=self
            )
            return

        old_winner_ids = match["winner_ids"]
        old_loser_ids = match["loser_ids"]

        # Köhnə mükafatları (bu matça aid coin log-ları) geri al
        for did in old_winner_ids + old_loser_ids:
            amt = get_match_coin_total(did, self.match_number)
            if amt:
                new_bal = add_coins(did, -amt)
                add_coin_log(
                    did, -amt,
                    f"Matç No{self.match_number} nəticə düzəlişi — köhnə mükafat geri alındı",
                    "spend", new_bal
                )

        # ELO/qələbə-məğlubiyyəti köhnə (matçdan əvvəlki) vəziyyətə qaytar
        affected = delete_match_and_revert(self.match_number)
        if affected is None:
            await interaction.edit_original_response(content="❌ Matç geri qaytarılarkən xəta baş verdi.", embed=None, view=self)
            return

        # Yeni (dəyişdirilmiş) nəticəni tətbiq et — köhnə uduzanlar indi qalib
        results = update_team_elo_5v5(old_loser_ids, old_winner_ids)
        if not results:
            await interaction.edit_original_response(
                content="❌ Yeni nəticə tətbiq edilə bilmədi (oyunçu(lar) tapılmadı).", embed=None, view=self
            )
            return

        record_match_history(
            match["match_type"], old_loser_ids, old_winner_ids,
            [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
            match_number=self.match_number
        )

        # Yeni rola uyğun təzə coin mükafatı — köhnə ədəd köçürülmür, standart düsturla yenidən verilir
        coin_lines = []
        for r in results["winners"]:
            earned = random.randint(5, 10)
            new_bal = add_coins(r["discord_id"], earned)
            add_coin_log(r["discord_id"], earned, f"Matç No{self.match_number} nəticə düzəlişi — yeni qələbə", "earn", new_bal)
            coin_lines.append(f"**{r['nick']}**: +{earned} coin (yeni qalib)")
        for r in results["losers"]:
            earned = random.randint(0, 5)
            new_bal = add_coins(r["discord_id"], earned)
            add_coin_log(r["discord_id"], earned, f"Matç No{self.match_number} nəticə düzəlişi — yeni məğlubiyyət", "earn", new_bal)
            coin_lines.append(f"**{r['nick']}**: +{earned} coin (yeni məğlub)")

        for p in results["winners"] + results["losers"]:
            await _sync_rank_role_5v5(interaction.guild, p["discord_id"], p["new_elo"])

        log_admin_action(
            "admin_matc_qalib_deyis", 0, "match_history",
            f"qalib={old_winner_ids}", f"qalib={old_loser_ids}",
            f"matc_no={self.match_number}", self.admin_id
        )
        await _post_audit_log(
            "admin_matc_qalib_deyis", 0, "match_history",
            f"qalib={old_winner_ids}", f"qalib={old_loser_ids}",
            f"matc_no={self.match_number}", self.admin_id
        )

        elo_lines = [f"{r['nick']}: {r['old_elo']} → {r['new_elo']} (✅ Qalib)" for r in results["winners"]]
        elo_lines += [f"{r['nick']}: {r['old_elo']} → {r['new_elo']} (❌ Məğlub)" for r in results["losers"]]
        embed = discord.Embed(
            title=f"🔄 Matç No{self.match_number} nəticəsi dəyişdirildi",
            description=(
                "**Yeni ELO:**\n" + "\n".join(elo_lines) +
                "\n\n**Yeni coin mükafatı:**\n" + "\n".join(coin_lines) +
                "\n\n⚠️ Kill/asist/ölüm, nailiyyət, missiya XP və artıq istifadə olunmuş "
                "ELO kartları köhnə (səhv) nəticəyə görə hesablanmış olaraq qalır — düzəlmir."
            ),
            color=discord.Color.blurple()
        )
        await interaction.edit_original_response(content=None, embed=embed, view=self)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu təsdiq yalnız komandanı işlədən admin üçündür.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Ləğv edildi.", embed=None, view=self)


@bot.tree.command(name="admin_matc_qalib_deyis", description="[Admin] Bitmiş matçın qalib komandasını dəyişir, ELO və coin mükafatını buna uyğun düzəldir")
@app_commands.describe(matc_no="Nəticəsi dəyişəcək matçın nömrəsi")
@staff_check()
async def admin_matc_qalib_deyis_cmd(interaction: discord.Interaction, matc_no: int):
    match = get_match_by_number(matc_no)
    if not match:
        await interaction.response.send_message(f"❌ Matç No{matc_no} tapılmadı.", ephemeral=True)
        return

    def _nick(did):
        row = get_player(did)
        return row[1] if row else f"`{did}`"

    winner_nicks = [_nick(did) for did in match["winner_ids"]]
    loser_nicks = [_nick(did) for did in match["loser_ids"]]

    embed = discord.Embed(
        title=f"🔄 Matç No{matc_no} qalibi dəyişilsin?",
        description=(
            f"Hazırkı qalib: **{', '.join(winner_nicks)}**\n"
            f"Hazırkı məğlub: **{', '.join(loser_nicks)}**\n\n"
            f"Təsdiqlədikdə: **{', '.join(loser_nicks)}** yeni qalib olacaq.\n\n"
            "ELO və qələbə/məğlubiyyət sayı köhnə vəziyyətə qaytarılıb yeni nəticəyə görə YENİDƏN "
            "hesablanacaq (əvvəlki kimi eyni formula ilə). Coin mükafatı da yeni rola uyğun təzədən "
            "verilir (köhnə ədəd köçürülmür, standart düsturla yenidən hesablanır).\n\n"
            "⚠️ Kill/asist/ölüm, nailiyyət, missiya XP və artıq istifadə olunmuş ELO "
            "kartları köhnə nəticəyə görə qalır — bunlar düzəlmir."
        ),
        color=discord.Color.orange()
    )
    view = ConfirmSwapMatchView(matc_no, interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@admin_matc_qalib_deyis_cmd.error
async def admin_matc_qalib_deyis_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="admin_matc_netice", description="[Admin] Aktiv matç üçün nəticə düymələrini yenidən göstərir (bot restart olduqdan sonra)")
@app_commands.describe(matc_no="Birdən çox matç paralel aktivdirsə, hansının olduğunu göstərin")
@staff_check()
async def admin_matc_netice_cmd(interaction: discord.Interaction, matc_no: int = None):
    if matc_no is not None:
        active = get_active_match(matc_no)
        if not active:
            await interaction.response.send_message(f"❌ Matç No{matc_no} aktiv deyil.", ephemeral=True)
            return
    else:
        active_matches = get_all_active_matches()
        if not active_matches:
            await interaction.response.send_message("❌ Hazırda aktiv matç yoxdur.", ephemeral=True)
            return
        if len(active_matches) > 1:
            nums = ", ".join(str(m["match_number"]) for m in active_matches)
            await interaction.response.send_message(
                f"⚠️ Birdən çox aktiv matç var ({nums}). `/admin_matc_netice matc_no:<nömrə>` ilə göstərin.",
                ephemeral=True
            )
            return
        active = active_matches[0]
    team_a = active.get("team_a", [])
    team_b = active.get("team_b", [])
    if not team_a or not team_b:
        await interaction.response.send_message("❌ Aktiv matçın komanda məlumatı tapılmadı.", ephemeral=True)
        return
    match_number = active["match_number"]
    view = MatchResultView5v5(match_number, team_a, team_b)
    embed = discord.Embed(
        title=f"🔁 Matç No{match_number} — Nəticə düymələri yeniləndi",
        description=(
            f"Xəritə: {active.get('selected_map', '?')}\n"
            f"🔵 Komanda A: {', '.join(p['nick'] for p in team_a)}\n"
            f"🔴 Komanda B: {', '.join(p['nick'] for p in team_b)}\n\n"
            "Aşağıdakı düymələrlə nəticəni qeyd edə bilərsiniz (`/scan` ilə əvvəlcədən "
            "statistika əlavə etmisinizsə, o da tətbiq olunacaq)."
        ),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=view)


@admin_matc_netice_cmd.error
async def admin_matc_netice_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)




async def _create_rank_roles(guild):
    """ELO rütbə rollarını (RANKS) serverdə yaradır (mövcud olmayanları) və bütün
    qeydiyyatlı 5v5 oyunçularına təyin edir. `created` (yeni yaradılan rol adları) və
    `player_count` (rolu yenilənən oyunçu sayı) qaytarır."""
    created = []
    for lo, hi, name, color, emoji in RANKS:
        role = discord.utils.get(guild.roles, name=name)
        if not role:
            await guild.create_role(name=name, color=discord.Color.from_rgb(*color), reason="Rütbə rolu")
            created.append(name)

    players_5v5 = get_all_players_5v5(limit=1000)
    for p in players_5v5:
        await _sync_rank_role_5v5(guild, p["discord_id"], p["elo"])

    return created, len(players_5v5)


@bot.tree.command(name="rank_rollari_qur", description="[Admin] ELO rütbə rollarını serverdə yaradır və bütün oyunçulara təyin edir")
@staff_check()
async def rank_rollari_qur_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    created, player_count = await _create_rank_roles(interaction.guild)

    await interaction.followup.send(
        f"✅ Rütbə rolları hazırdır.\n"
        f"🆕 Yaradılan rollar: {', '.join(created) if created else 'yoxdur (artıq mövcud idi)'}\n"
        f"🔄 {player_count} oyunçunun rütbə rolu yeniləndi.",
        ephemeral=True
    )


@rank_rollari_qur_cmd.error
async def rank_rollari_qur_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="hamisina_rol_ver", description="[Admin] Seçilmiş rolu serverdəki bütün üzvlərə (botlar xaric) tək dəfəyə verir")
@app_commands.describe(rol="Hər kəsə veriləcək rol")
@staff_check()
async def hamisina_rol_ver_cmd(interaction: discord.Interaction, rol: discord.Role):
    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    given = 0
    skipped = 0
    failed = 0
    for member in interaction.guild.members:
        if member.bot:
            continue
        if rol in member.roles:
            skipped += 1
            continue
        try:
            await member.add_roles(rol, reason=f"/hamisina_rol_ver — {interaction.user}")
            given += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
    msg = f"✅ **{rol.name}** rolu **{given}** üzvə verildi ({skipped} nəfərdə artıq var idi)."
    if failed:
        msg += f"\n⚠️ {failed} üzvə verilə bilmədi (icazə/roluğu yerləşdirmə problemi ola bilər)."
    await interaction.followup.send(msg, ephemeral=True)


@hamisina_rol_ver_cmd.error
async def hamisina_rol_ver_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="kanallari_yenile", description="[Admin] Ay sonu mükafatı/leaderboard/matchmaking/aktivlik lövhəsi mesajlarını dərhal yeniləyir")
@staff_check()
async def kanallari_yenile_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    results = []

    try:
        await refresh_leaderboard_5v5.coro()
        results.append("✅ Leaderboard")
    except Exception as e:
        results.append(f"❌ Leaderboard ({e})")

    try:
        await update_queue_status_message_5v5()
        results.append("✅ Matchmaking (sıra statusu)")
    except Exception as e:
        results.append(f"❌ Matchmaking ({e})")

    try:
        await refresh_chat_activity_leaderboard.coro()
        results.append("✅ Aktivlik lövhəsi")
    except Exception as e:
        results.append(f"❌ Aktivlik lövhəsi ({e})")

    await interaction.followup.send(
        "🔄 **Kanallar yeniləndi:**\n" + "\n".join(results) +
        "\n\nℹ️ Qeydiyyat mesajı statik bannerdir (dinamik məlumat göstərmir) — yeniləmə tələb etmir, həmişə aktualdır.",
        ephemeral=True
    )


@kanallari_yenile_cmd.error
async def kanallari_yenile_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANELİ (VİZUAL) — bütün admin komandalarını tək /admin_panel altında
# birləşdirən düymə/select-əsaslı interfeys. Hər addım MÖVCUD slash komandanın
# `.callback(interaction, ...)` metodunu birbaşa çağırır (məntiq TƏKRARLANMIR,
# panel yalnız parametr toplayan nazik bir təbəqədir).
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUserPickView(discord.ui.View):
    def __init__(self, admin_id, mode):
        super().__init__(timeout=120)
        self.admin_id = admin_id
        self.mode = mode  # "info" | "edit"
        self.select = discord.ui.UserSelect(placeholder="Oyunçu seçin...")
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return
        member = self.select.values[0]
        if self.mode == "info":
            await admin_oyuncu_cmd.callback(interaction, member)
        else:
            await interaction.response.send_message(
                f"✏️ **{member.display_name}** üçün dəyişəcəyiniz sahəni seçin:",
                view=AdminPlayerFieldSelectView(self.admin_id, member),
                ephemeral=True
            )


class AdminFieldValueModal(discord.ui.Modal, title="Yeni dəyər"):
    deyer = discord.ui.TextInput(label="Yeni dəyər", max_length=50)

    def __init__(self, member, choice):
        super().__init__(title=f"Yeni dəyər — {choice.name}")
        self.member = member
        self.choice = choice

    async def on_submit(self, interaction: discord.Interaction):
        await admin_duzelt_cmd.callback(interaction, self.member, self.choice, str(self.deyer))


class AdminPlayerFieldSelectView(discord.ui.View):
    def __init__(self, admin_id, member):
        super().__init__(timeout=120)
        self.admin_id = admin_id
        self.member = member
        options = [discord.SelectOption(label=c.name, value=c.value) for c in ADMIN_FIELD_CHOICES]
        sel = discord.ui.Select(placeholder="Dəyişəcəyiniz sahəni seçin...", options=options)
        sel.callback = self._on_select
        self.select = sel
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return
        field_value = self.select.values[0]
        choice = next(c for c in ADMIN_FIELD_CHOICES if c.value == field_value)
        await interaction.response.send_modal(AdminFieldValueModal(self.member, choice))


class AdminPlayerMenuView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=180)
        self.admin_id = admin_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Oyunçu məlumatı", style=discord.ButtonStyle.primary, emoji="🔍")
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("Oyunçu seçin:", view=AdminUserPickView(self.admin_id, "info"), ephemeral=True)

    @discord.ui.button(label="Sahə dəyiş", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def edit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("Oyunçu seçin:", view=AdminUserPickView(self.admin_id, "edit"), ephemeral=True)


class AdminMatchNumberModal(discord.ui.Modal):
    matc_no = discord.ui.TextInput(label="Matç nömrəsi", placeholder="məs: 42", max_length=10, required=True)

    def __init__(self, title, action):
        super().__init__(title=title)
        self.action = action  # "sil" | "qalib_deyis" | "netice"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            no = int(str(self.matc_no))
        except ValueError:
            await interaction.response.send_message("❌ Rəqəm daxil edin.", ephemeral=True)
            return
        if self.action == "sil":
            await admin_matc_sil_cmd.callback(interaction, no)
        elif self.action == "qalib_deyis":
            await admin_matc_qalib_deyis_cmd.callback(interaction, no)
        elif self.action == "netice":
            await admin_matc_netice_cmd.callback(interaction, no)


class AdminMatchMenuView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=180)
        self.admin_id = admin_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Son matçlar", style=discord.ButtonStyle.primary, emoji="📋")
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await admin_matclar_cmd.callback(interaction)

    @discord.ui.button(label="Matç sil", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def del_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(AdminMatchNumberModal("Matçı sil", "sil"))

    @discord.ui.button(label="Qalibi dəyiş", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def swap_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(AdminMatchNumberModal("Qalibi dəyiş", "qalib_deyis"))

    @discord.ui.button(label="Nəticə düymələrini yenilə", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def redisplay_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(AdminMatchNumberModal("Nəticə düymələrini yenilə", "netice"))


class AdminRolePickView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=120)
        self.admin_id = admin_id
        self.select = discord.ui.RoleSelect(placeholder="Hər kəsə veriləcək rolu seçin...")
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return
        role = self.select.values[0]
        await hamisina_rol_ver_cmd.callback(interaction, role)


class AdminServerMenuView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=180)
        self.admin_id = admin_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Kanalları yenilə", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await kanallari_yenile_cmd.callback(interaction)

    @discord.ui.button(label="Rütbə rollarını qur", style=discord.ButtonStyle.primary, emoji="🏅")
    async def ranks_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await rank_rollari_qur_cmd.callback(interaction)

    @discord.ui.button(label="Hamısına rol ver", style=discord.ButtonStyle.secondary, emoji="👥")
    async def giveall_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("Rolu seçin:", view=AdminRolePickView(self.admin_id), ephemeral=True)

    @discord.ui.button(label="⚠️ Server sıfırla", style=discord.ButtonStyle.danger, emoji="🧨", row=1)
    async def server_reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await server_sifirla_cmd.callback(interaction)

    @discord.ui.button(label="⚠️ Bütün datanı sıfırla", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def full_reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await admin_full_reset_cmd.callback(interaction)


class AdminMiscMenuView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=180)
        self.admin_id = admin_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Elan et (bu kanala)", style=discord.ButtonStyle.primary, emoji="📢")
    async def announce_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await elan.callback(interaction, None)

    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, emoji="🎉")
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            "🎉 Giveaway: `/giveaway_create`\n\n"
            "ℹ️ Elan kanalı seçimi tələb etdiyi üçün birbaşa slash komandası kimi işlədilir.",
            ephemeral=True
        )


class AdminPanelHubView(discord.ui.View):
    def __init__(self, admin_id):
        super().__init__(timeout=300)
        self.admin_id = admin_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("❌ Bu panel yalnız çağıran admin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Oyunçu", style=discord.ButtonStyle.primary, emoji="👤")
    async def player_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("👤 **Oyunçu İdarəetməsi**", view=AdminPlayerMenuView(self.admin_id), ephemeral=True)

    @discord.ui.button(label="Matçlar", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def match_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("⚔️ **Matç İdarəetməsi**", view=AdminMatchMenuView(self.admin_id), ephemeral=True)

    @discord.ui.button(label="Server", style=discord.ButtonStyle.primary, emoji="🖥️")
    async def server_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("🖥️ **Server İdarəetməsi**", view=AdminServerMenuView(self.admin_id), ephemeral=True)

    @discord.ui.button(label="Digər", style=discord.ButtonStyle.primary, emoji="🎁")
    async def misc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message("🎁 **Digər**", view=AdminMiscMenuView(self.admin_id), ephemeral=True)


@bot.tree.command(name="admin_panel", description="[Admin] Bütün admin əməliyyatlarına vizual panel")
@staff_check()
async def admin_panel_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ Nextlevelaz Admin Paneli",
        description=(
            "Aşağıdan kateqoriya seçin:\n\n"
            "👤 **Oyunçu** — məlumata bax, sahə dəyiş\n"
            "⚔️ **Matçlar** — siyahı, sil, qalib dəyiş, nəticə düymələrini yenilə\n"
            "🖥️ **Server** — kanalları yenilə, rütbə rolları, rol ver, sıfırlama\n"
            "🎁 **Digər** — elan et, giveaway/hərrac bələdçisi"
        ),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    await interaction.response.send_message(embed=embed, view=AdminPanelHubView(interaction.user.id), ephemeral=True)


@admin_panel_cmd.error
async def admin_panel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# KOMANDA PANELİ
# ═══════════════════════════════════════════════════════════════════════════════

PANEL_CATEGORIES = {
    "profil": {
        "label": "Profil",
        "title": "👤 Profil və Statistika",
        "items": [
            ("/profile", "Profil kartınızı və bütün aşağıdakı bölmələrə keçid düymələrini göstərir"),
            ("📊 Stats (profil düyməsi)", "ELO, K/D, seriya və digər statistikanızı göstərir"),
            ("📜 Tarixçə (profil düyməsi)", "Son matçlarınızın tarixçəsini göstərir"),
            ("🗺️ Xəritələr (profil düyməsi)", "Hər xəritədə qələbə/məğlubiyyət faizinizi göstərir"),
            ("📈 Qrafik (profil düyməsi)", "ELO-nuzun zaman keçdikcə necə dəyişdiyini xətti qrafikdə göstərir"),
            ("🔗 Paylaş (profil düyməsi)", "Profilinizin ictimai (Discorddan kənar) linkini göndərir"),
            ("🧠 AI Coach (profil düyməsi)", "Son matçlarınıza əsaslanan şəxsi məsləhət göstərir"),
            ("🌐 Dil (profil düyməsi)", "Profil kartınızı və menyu düymələrini Azərbaycan/English/Русский dilində göstərir"),
        ],
    },
    "diger": {
        "label": "Digər",
        "title": "🎉 Digər",
        "items": [
            ("Qeydiyyat düyməsi", "Qeydiyyat kanalındakı düymə ilə FACEIT sisteminə qeydiyyatdan keçirsiniz"),
            ("Sıraya qoşul düyməsi", "Matchmaking kanalındakı düymə ilə 5v5 sırasına qoşulursunuz"),
            ("Rütbə rolu", "ELO-nuz dəyişəndə Discord rolunuz avtomatik yenilənir"),
            ("📥 Giriş/çıxış logu", "Üzv serverə qoşulanda/ayrılanda bu kanala avtomatik qeyd düşür"),
            ("📡 Bot statusu", "Botun Discord statusu canlı oyunçu/matç rəqəmləri ilə növbələnir"),
            ("🎮 Matç Başlama Elanı", "Hər yeni matçda kapitanların adı/ID-si elan kanalına avtomatik göndərilir — lobbi tez qurulsun deyə"),
            ("🗑️ Qeydiyyat təmizliyi",
             f"Qeydiyyatdan {INACTIVE_REGISTRATION_DAYS} gün keçməsinə baxmayaraq heç bir matç oynamayan "
             "oyunçunun qeydiyyatı avtomatik silinir (istəsə yenidən qeydiyyatdan keçə bilər)"),
            ("🏆 Sezon mükafatı", "Hər sezon sonunda Top-3 Gold mükafatı qazanır, nəticə sezon-mükafat kanalında elan olunur"),
            ("🛤️ Sezonlar", "Hər sezon bağlananda Top-3 mükafat alır, Karyera Yolu düyməsində tarixçə qalır"),
            ("🚫 Xəritə Veto", "Hər komandanın kapitanı matç başladıqdan sonra xəritəni 1 dəfə vetolaya bilər"),
            ("🎫 Ticket sistemi", "Ticket kanalında mövzu seçərək (klan qoşulma / Gold / Boost / Emulator) özəl ticket kanalı açırsınız"),
        ],
    },
    "admin": {
        "label": "Admin",
        "title": "🔧 Admin (Founder / Admin / Moderator)",
        "items": [
            ("/admin_panel", "🛠️ Bütün admin əməliyyatlarına vizual, düymə-əsaslı panel (tövsiyə olunur)"),
            ("/scan", "Skor ekranı şəklindən K/A/D oxuyur"),
            ("/admin_oyuncu", "Oyunçunun tam profil məlumatını göstərir"),
            ("/admin_duzelt", "Oyunçunun ELO/coin/stat və s. sahəsini dəyişir"),
            ("/admin_matclar", "Son matçların siyahısı"),
            ("/admin_matc_sil", "Bir matçı silib ELO-nu geri qaytarır"),
            ("/admin_matc_netice", f"Aktiv matç üçün nəticə düymələrini yenidən göstərir (2 matç paralel gedirsə `matc_no` göstərin)"),
            ("🎮 Paralel matçlar", f"Eyni anda {MAX_PARALLEL_MATCHES} matça qədər paralel oynanıla bilər, hər biri öz thread/səs kanalları ilə"),
            ("/rank_rollari_qur", "ELO rütbə rollarını serverdə yaradır və bütün oyunçulara təyin edir"),
            ("/hamisina_rol_ver", "Seçilmiş rolu serverdəki bütün üzvlərə (botlar xaric) tək dəfəyə verir"),
            ("/kanallari_yenile", "Leaderboard/matchmaking/aktivlik lövhəsi mesajlarını dərhal yeniləyir"),
            ("📊 Aktivlik (aşağıdakı düymə)", "Son 7 günün aktivlik statistikasını göstərir"),
            ("📋 Günlük hesabat", "Bot hər gün AZ vaxtı ilə 00:00-da avtomatik günlük statistikanı bu kanala göndərir"),
            ("📰 Nextlevelaz Xəbərləri", "Gündəlik hesabatın ardınca AI (Claude) yazılmış qısa icmal göndərilir"),
            ("🚫 Ləğv et (matç mesajında)", "Asılı qalan matçı ləğv edir, gəlməyənə ELO cəzası verə bilər"),
            ("/server_sifirla", "⚠️ TƏHLÜKƏLİ: serverin BÜTÜN kanal/rollarını silib yenidən qurur"),
            ("/setup_register", "Qeydiyyat mesajını yaradır"),
            ("/setup_rules", "Qaydalar mesajını yaradır"),
            ("/giveaway_create", "Giveaway yaradır — gizli qalib təyin edə, ya da boş buraxıb əsl-random seçim edə bilərsiniz"),
            ("🛡️ Audit Log kanalı", "Bütün admin əməliyyatları (ELO düzəlişi, matç silmə/dəyişmə və s.) canlı qeydə alınır"),
            ("⚠️ Şübhəli fəaliyyət xəbərdarlığı", "Qeyri-adi sürətli coin qazancı avtomatik audit-log kanalına bildirilir"),
        ],
    },
}


def _build_panel_embed(category_key: str) -> discord.Embed:
    cat = PANEL_CATEGORIES[category_key]
    embed = discord.Embed(title=cat["title"], color=discord.Color.from_rgb(138, 92, 230))
    for name, desc in cat["items"]:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="Nextlevelaz")
    return embed


class HelpPanelView(discord.ui.View):
    def __init__(self, is_staff_user: bool):
        super().__init__(timeout=300)
        self.is_staff_user = is_staff_user
        if not is_staff_user:
            for item in list(self.children):
                if getattr(item, "custom_id", None) in ("panel_admin", "panel_activity"):
                    self.remove_item(item)

    async def _switch(self, interaction: discord.Interaction, category_key: str):
        await interaction.response.edit_message(embed=_build_panel_embed(category_key), view=self)

    @discord.ui.button(label="Profil", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="panel_profil")
    async def profil_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch(interaction, "profil")

    @discord.ui.button(label="Digər", style=discord.ButtonStyle.secondary, emoji="🎉", custom_id="panel_diger")
    async def diger_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch(interaction, "diger")

    @discord.ui.button(label="Admin", style=discord.ButtonStyle.danger, emoji="🔧", custom_id="panel_admin")
    async def admin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu kataqoriya yalnız admin heyəti üçündür.", ephemeral=True)
            return
        await self._switch(interaction, "admin")

    @discord.ui.button(label="Aktivlik", style=discord.ButtonStyle.danger, emoji="📊", custom_id="panel_activity")
    async def activity_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız admin heyəti üçündür.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        stats = get_activity_stats(days=7)
        hourly = get_hourly_activity(days=7)
        card_path = os.path.join(DATA_DIR or ".", "activity.png")
        await asyncio.to_thread(generate_activity_card, stats, card_path, hourly)
        await interaction.followup.send(file=discord.File(card_path, filename="activity.png"), ephemeral=True)


@bot.tree.command(name="panel", description="Bütün bot komandalarını kataqoriyalı şəkildə göstərir")
async def panel_cmd(interaction: discord.Interaction):
    view = HelpPanelView(is_staff(interaction))
    await interaction.response.send_message(embed=_build_panel_embed("profil"), view=view, ephemeral=True)


web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

bot.run(TOKEN)