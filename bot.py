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
    init_db, register_player, get_player, update_elo,
    add_to_queue, remove_from_queue, queue_size, clear_queue,
    is_in_queue, pop_4_and_balance, get_leaderboard,
    update_team_elo, get_next_match_number,
    create_giveaway, get_due_giveaways, mark_giveaway_finished,
    get_queue_list,
    set_active_match, clear_active_match, get_active_match, veto_map,
    set_active_match_message, set_match_ready,
    get_active_match_by_message_id, get_all_active_matches, count_active_matches,
    is_player_in_active_match, set_active_match_voice,
    add_combat_stats, get_combat_stats, record_match_history,
    save_scan_result, get_scan_result, confirm_scan,
    add_coins, get_coins, spend_coins, get_inventory, owns_item, add_to_inventory, remove_from_inventory,
    set_active_banner, get_active_banner, set_active_frame, get_active_frame,
    set_active_theme, get_active_theme, add_coin_log, get_coin_logs, check_daily_login,
    refresh_daily_tasks, get_active_daily_tasks, get_player_active_task,
    assign_task_to_player, update_task_progress,
    check_and_grant_achievements, get_player_achievements,
    update_streak, get_streak_bonus,
    get_player_stats_dict, get_player_match_history,
    get_recent_matches, get_match_by_number, delete_match_and_revert, get_match_coin_total,
    get_weekly_mvp,
    admin_set_player_field, log_admin_action, is_banned,
    get_map_stats, get_all_players,
    get_squad, get_pending_squad_invite, create_squad_invite,
    accept_squad_invite, reject_squad_invite, record_squad_win, wipe_squads,
    get_personal_record, update_personal_record,
    get_activity_stats, get_hourly_activity,
    get_daily_stats, get_monthly_top_player,
    get_meta, set_meta,
    get_achievement_rarity, apply_elo_decay,
    get_player_count, get_total_match_count,
    ensure_community_goal, get_community_goal, mark_goal_rewarded,
    get_month_match_count, get_month_participants,
    get_most_improved_player, get_month_most_active,
    check_and_grant_titles, get_player_titles, set_active_title, get_active_title_name,
    get_lang, set_lang,
    update_quest_progress, get_player_quests,
    ensure_daily_challenge, get_daily_challenge, claim_daily_challenge,
    get_best_duo,
    get_inactive_unplayed_players, delete_player,
    add_skin_to_inventory,
    get_zm_balance, spend_zm, add_zm,
    add_boost_cards, get_boost_card_counts,
    reset_all_player_data,
    transfer_coins, set_discount, get_discount, get_all_discounts, clear_expired_discounts,
    add_boost, get_active_boost, get_all_active_boosts,
    get_or_create_current_season, get_season_by_number, add_season_stat,
    get_season_stat, get_season_leaderboard, close_season,
    get_completed_seasons, reset_all_players_for_new_season,
    get_combined_elo_snapshot, collapse_erroneous_season_rotations, revoke_skin_grants,
    add_teammate_rating, get_teammate_rating_summary,
    mark_anniversary_greeted, get_players_with_anniversary_today,
    ensure_5v5_stats_row, get_player_5v5, get_player_stats_dict_5v5, update_team_elo_5v5,
    update_streak_5v5, get_loss_streak_5v5, add_to_queue_5v5, remove_from_queue_5v5,
    queue_size_5v5, get_queue_list_5v5, clear_queue_5v5, is_in_queue_5v5, pop_10_and_balance,
    get_leaderboard_5v5, get_all_players_5v5,
    get_dm_notifications, set_dm_notifications, use_free_nickname_change,
    check_and_grant_comeback_bonus, COMEBACK_BONUS_COINS,
    create_report, get_recent_reports_for,
    bulk_add_coins, check_suspicious_activity,
    create_auction, get_auction, place_bid, get_due_auctions, mark_auction_finished, get_open_auction_ids,
    get_activity_heatmap, WEEKDAY_NAMES_AZ,
    get_weekly_recap,
    get_map_masters, get_loss_streak,
    get_or_create_boss_event, set_boss_message, apply_boss_damage,
    get_boss_leaderboard, get_all_boss_contributors,
    add_voice_seconds, get_voice_leaderboard,
    create_tournament, get_tournament, get_active_tournament, list_tournaments,
    join_tournament, leave_tournament, get_tournament_signup_count, get_tournament_participants,
    start_tournament, record_tournament_match_winner, get_tournament_match, get_tournament_bracket,
    get_tournament_team_members, get_open_tournament_matches, cancel_tournament,
    set_tournament_meta, set_tournament_match_message,
    add_chat_xp, get_chat_leaderboard, get_top_chat_activity, reset_weekly_chat_xp,
)
from i18n import t, LANG_NAMES
from ai_chat import generate_match_coach_tip, generate_daily_news, generate_intel_briefing, generate_personal_coach_report
import standoff2_news
from leaderboard_image import generate_leaderboard_image
from web_server import run_web_server
from profile_card import generate_profile_card
from match_card import generate_match_card
from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
from rules_card import generate_rules_card, generate_register_banner
from scan_system import ocr_scoreboard, match_to_registered, apply_defaults_for_missing
from market_config import (
    MARKET_ITEMS, get_item_by_id, ELO_CARD_PACKS, get_elo_card_pack,
    MARKET_BUNDLES, get_bundle_by_id, bundle_full_price,
)
from visual_cards import (
    generate_inventory_card, generate_coin_logs_card,
    generate_tasks_card, generate_achievements_card,
    generate_stats_card, generate_match_history_card,
    generate_map_stats_card, generate_personal_record_card, generate_squad_card,
    generate_activity_card, generate_elo_chart_card, generate_quest_card, generate_synergy_card,
    generate_elo_cards_market_card, generate_monthly_reward_card, generate_weekly_mvp_card,
    generate_boss_event_card, generate_map_masters_card,
    generate_announcement_card, generate_sticker_card, generate_chat_activity_card,
    RANKS, get_rank
)
from sticker_config import STICKER_ITEMS, get_sticker_by_achievement, get_sticker_by_id
from referral_visual import generate_item_preview_card
from tournament_card import generate_tournament_bracket_image, generate_tournament_signup_card
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
COMMUNITY_GOAL_TARGET = 150
COMMUNITY_GOAL_REWARD_COINS = 15

GOLDEN_MATCH_CHANCE = 0.15
UPSET_ELO_THRESHOLD = 150
MAX_PARALLEL_MATCHES = 2

DAILY_CHALLENGE_TEMPLATES = [
    ("kills_in_match", 10, 20, "Bir matçda 10+ kill əldə et"),
    ("assists_in_match", 5, 15, "Bir matçda 5+ asist əldə et"),
    ("win_match", 1, 15, "Bu gün 1 matç qazan"),
    ("kd_in_match", 3, 20, "Bir matçda 3.0+ K/D əldə et"),
]
DAILY_CHALLENGE_DESCRIPTIONS = {c[0]: c[3] for c in DAILY_CHALLENGE_TEMPLATES}

LIGHTNING_ROUND_CHECK_CHANCE = 0.05
LIGHTNING_ROUND_DURATION_MINUTES = 10

SOCIAL_CHANNEL_ID = 1529227720939012229
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@nextlevelaze",
    "tiktok": "https://www.tiktok.com/@nextlevelaz",
    "discord": "https://discord.gg/nextlevelaz",
    "shop": "https://zenithshop.up.railway.app/",
}

FULL_SETUP_CATEGORY_NAME = "🏆 FACEIT 2v2"
CATEGORY_GENERAL_NAME = "📌 Ümumi"
CATEGORY_5V5_NAME = "🎯 FACEIT 5v5"
CATEGORY_TOURNAMENT_NAME = "🏆 Turnirlər"

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

LOGO_PATH = "logo.jpg"
MONTHLY_CHAMPION_IMAGE_PATH = os.path.join("assets", "butterfly_legacy.jpg")
MONTHLY_CHAMPION_SKIN_NAME = "Butterfly | Legacy"
INACTIVE_REGISTRATION_DAYS = 3
REWARD_CHANNEL_ID = None
HALL_OF_FAME_CHANNEL_ID = None
REPORTS_CHANNEL_ID = None
AUDIT_LOG_CHANNEL_ID = None
ACHIEVEMENT_WALL_CHANNEL_ID = None
BOSS_EVENT_CHANNEL_ID = None
MAP_MASTERS_CHANNEL_ID = None
STANDOFF2_NEWS_CHANNEL_ID = None
RARE_ACHIEVEMENT_THRESHOLD_PCT = 15
BOSS_MAX_HP = 500
BOSS_REWARD_COINS = 40
BOSS_TOP_DAMAGE_BONUS = 40
TILT_LOSS_STREAK_THRESHOLD = 3

# ── Coin ↔ AZN çevrilməsi (ai_chat.py-dakı elan olunmuş məzənnə ilə eynidir) ────
COIN_TO_AZN_RATE = 2500  # 2500 coin = 0.5 AZN
COIN_TO_AZN_VALUE = 0.5

# ── Flash Sale ───────────────────────────────────────────────────────────────
FLASH_SALE_CHECK_CHANCE = 0.08
FLASH_SALE_DISCOUNT_PCT = 30
FLASH_SALE_DURATION_HOURS = 6

# ── Xəritə Veto ──────────────────────────────────────────────────────────────
MAP_VETO_MAX_REROLLS_PER_CAPTAIN = 1

# ── Bayram matçları / Mövsümi tema ───────────────────────────────────────────
# (ay, gün) cütləri ilə Azərbaycanda geniş qeyd olunan bayramlar — həmin GÜN
# avtomatik 2x coin/ELO bonusu aktivdir və elan embed-ləri bayram rənginə keçir.
HOLIDAY_DATES = {
    (1, 1):   "Yeni İl",
    (3, 20):  "Novruz Bayramı",
    (3, 21):  "Novruz Bayramı",
    (5, 28):  "Respublika Günü",
    (10, 18): "Müstəqillik Günü",
}
HOLIDAY_ACCENT = (230, 60, 55)


def _current_holiday_name():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    return HOLIDAY_DATES.get((now.month, now.day))


def _is_holiday_bonus_active():
    return _current_holiday_name() is not None


def _seasonal_accent():
    """Mövsümi tema: bayram günü elan embed-lərinin aksent rəngini dəyişir (RGB tuple qaytarır)."""
    return HOLIDAY_ACCENT if _is_holiday_bonus_active() else (138, 92, 230)

GREEN_ACCENT = (95, 208, 122)
ACCENT_VIOLET = (138, 92, 230)
RED_ACCENT = (214, 69, 61)

# Matchmaking üçün açıq saatlar (Azərbaycan vaxtı, UTC+4)
QUEUE_OPEN_HOUR = 20   # 20:00
QUEUE_CLOSE_HOUR = 2   # 02:00

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


STAFF_ROLE_NAMES = {"founder", "co-founder", "head admin", "admin"}


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


RANK_ROLE_NAMES = {r[2] for r in RANKS}


async def _sync_rank_role(guild, discord_id, elo):
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

    to_remove = [r for r in member.roles if r.name in RANK_ROLE_NAMES and r.id != target_role.id]
    try:
        if to_remove:
            await member.remove_roles(*to_remove, reason="Rütbə yeniləndi")
        if target_role not in member.roles:
            await member.add_roles(target_role, reason="Rütbə yeniləndi")
    except discord.Forbidden:
        pass


RANK_ROLE_NAMES_5V5 = {f"5v5 {r[2]}" for r in RANKS}


async def _sync_rank_role_5v5(guild, discord_id, elo):
    """`_sync_rank_role`-un 5v5 analoqu — "5v5 {Rütbə}" adlı AYRICA rol dəstini idarə edir,
    2v2 rütbə rollarına TOXUNMUR."""
    if not guild:
        return
    member = guild.get_member(discord_id)
    if not member:
        try:
            member = await guild.fetch_member(discord_id)
        except (discord.NotFound, discord.HTTPException):
            return
    rank_name, _color, _emoji = get_rank(elo)
    target_role_name = f"5v5 {rank_name}"
    target_role = discord.utils.get(guild.roles, name=target_role_name)
    if not target_role:
        return

    to_remove = [r for r in member.roles if r.name in RANK_ROLE_NAMES_5V5 and r.id != target_role.id]
    try:
        if to_remove:
            await member.remove_roles(*to_remove, reason="5v5 rütbə yeniləndi")
        if target_role not in member.roles:
            await member.add_roles(target_role, reason="5v5 rütbə yeniləndi")
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


async def _get_reward_channel():
    if not REWARD_CHANNEL_ID:
        return None
    channel = bot.get_channel(REWARD_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(REWARD_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        print(f"[REWARD_CHANNEL] Kanal tapılmadı: {REWARD_CHANNEL_ID}", flush=True)
        return None


async def _get_hall_of_fame_channel():
    if not HALL_OF_FAME_CHANNEL_ID:
        return None
    channel = bot.get_channel(HALL_OF_FAME_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(HALL_OF_FAME_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        print(f"[HALL_OF_FAME_CHANNEL] Kanal tapılmadı: {HALL_OF_FAME_CHANNEL_ID}", flush=True)
        return None


async def _render_boss_card(boss, leaderboard):
    card_path = os.path.join(DATA_DIR or ".", "boss_event_card.png")
    await asyncio.to_thread(generate_boss_event_card, boss, leaderboard, card_path)
    return discord.File(card_path, filename="boss_event.png")


async def _post_boss_event(channel):
    boss = get_or_create_boss_event(BOSS_MAX_HP, BOSS_REWARD_COINS)
    file = await _render_boss_card(boss, [])
    message = await channel.send(file=file)
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
    set_boss_message(boss["week_key"], message.id, channel.id)
    return message


async def _update_boss_progress(contributions: dict):
    """Matçdan sonra kill-əsaslı töhfələri boss-a tətbiq edir, canlı mesajı yeniləyir,
    boss məğlub olubsa iştirakçılara mükafat verir."""
    if not contributions:
        return
    channel = await _get_boss_event_channel()
    if not channel:
        return
    boss = get_or_create_boss_event(BOSS_MAX_HP, BOSS_REWARD_COINS)
    if boss["defeated"]:
        return
    if boss["is_new"] or not boss.get("message_id"):
        message = await _post_boss_event(channel)
        boss = get_or_create_boss_event(BOSS_MAX_HP, BOSS_REWARD_COINS)
    new_hp, max_hp, just_defeated = apply_boss_damage(boss["week_key"], contributions)
    leaderboard = get_boss_leaderboard(boss["week_key"])
    boss["current_hp"] = new_hp
    boss["defeated"] = just_defeated
    try:
        message = await channel.fetch_message(int(boss["message_id"]))
        file = await _render_boss_card(boss, leaderboard)
        await message.edit(attachments=[file])
    except (discord.NotFound, discord.HTTPException, TypeError, ValueError):
        pass
    if just_defeated:
        contributors = get_all_boss_contributors(boss["week_key"])
        for did in contributors:
            new_bal = add_coins(did, BOSS_REWARD_COINS)
            add_coin_log(did, BOSS_REWARD_COINS, "Boss Event qələbəsi", "earn", new_bal)
        if leaderboard:
            top_id = leaderboard[0]["discord_id"]
            new_bal = add_coins(top_id, BOSS_TOP_DAMAGE_BONUS)
            add_coin_log(top_id, BOSS_TOP_DAMAGE_BONUS, "Boss Event — ən çox zərbə bonusu", "earn", new_bal)
        try:
            await channel.send(
                f"🎉 Boss məğlub edildi! {len(contributors)} nəfər töhfə verdi, hamısı "
                f"**{BOSS_REWARD_COINS} coin** qazandı. Ən çox zərbə vuran: "
                f"{'<@' + str(leaderboard[0]['discord_id']) + '>' if leaderboard else '-'} 🏅"
            )
        except discord.HTTPException:
            pass


async def _post_wall_announcement(guild, discord_id, nick, name, icon, kind):
    """Nadir nailiyyət/ləqəb qazananda dərhal Nailiyyət Divarı kanalına elan edir."""
    channel = await _get_achievement_wall_channel()
    if not channel:
        return
    embed = discord.Embed(
        title=f"{icon} Yeni {kind.capitalize()}!",
        description=f"<@{discord_id}> (**{nick}**) — **{name}** {kind}ini qazandı!",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Nextlevelaz")
    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass


async def _maybe_grant_sticker(guild, discord_id, nick, achievement_id):
    """Qazanılan nailiyyət `sticker_config.STICKER_ITEMS`-də qeyd olunubsa, mövcud generik
    `inventory`/`add_to_inventory` mexanizmi ilə (bax: market_config.py-dəki eyni idiom) sticker-i
    açır və Nailiyyət Divarında elan edir. Adi `add_to_inventory` UNIQUE constraint-ə görə
    təkrar-qazanılanda səssizcə no-op edir, ona görə xüsusi yoxlama lazım deyil."""
    sticker = get_sticker_by_achievement(achievement_id)
    if not sticker:
        return
    if owns_item(discord_id, sticker["id"]):
        return
    add_to_inventory(discord_id, sticker["id"])
    if guild:
        await _post_wall_announcement(guild, discord_id, nick, sticker["name"], "🔓", "sticker")


class StickerShareView(discord.ui.View):
    def __init__(self, discord_id, owned_stickers):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        self.select_menu = discord.ui.Select(
            placeholder="Paylaşmaq üçün sticker seçin...",
            options=[discord.SelectOption(label=s["name"], value=s["id"], description=s["label"])
                     for s in owned_stickers]
        )
        self.select_menu.callback = self.share_selected
        self.add_item(self.select_menu)

    async def share_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız sizin panelinizdir.", ephemeral=True)
            return
        sticker_id = self.select_menu.values[0]
        sticker = get_sticker_by_id(sticker_id)
        if not sticker:
            await interaction.response.send_message("❌ Sticker tapılmadı.", ephemeral=True)
            return
        await interaction.response.defer()
        card_path = os.path.join(DATA_DIR or ".", f"sticker_{sticker_id}_{interaction.user.id}.png")
        await asyncio.to_thread(generate_sticker_card, sticker["name"], sticker["label"], card_path)
        await interaction.channel.send(
            content=f"🔓 **{interaction.user.display_name}** stikerini paylaşdı!",
            file=discord.File(card_path, filename="sticker.png")
        )


@bot.tree.command(name="stickerlerim", description="Açdığınız nailiyyət stikerlərini görüb paylaşın")
async def stickerlerim(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Əvvəlcə qeydiyyatdan keçməlisiniz.", ephemeral=True)
        return
    owned_ids = set(get_inventory(interaction.user.id))
    owned_stickers = [s for s in STICKER_ITEMS if s["id"] in owned_ids]
    if not owned_stickers:
        await interaction.response.send_message(
            "😔 Hələ heç bir sticker açmamısınız. Xüsusi nailiyyətlər qazanaraq "
            "(50 qələbə, 500 kill, 10x MVP, 10 seriya, 1500 ELO və s.) sticker qazana bilərsiniz.",
            ephemeral=True
        )
        return
    lines = "\n".join(f"• **{s['name']}** — {s['label']}" for s in owned_stickers)
    await interaction.response.send_message(
        f"🎖️ Sizin stikerləriniz:\n{lines}\n\nAşağıdan paylaşmaq istədiyinizi seçin:",
        view=StickerShareView(interaction.user.id, owned_stickers),
        ephemeral=True
    )


async def _post_map_masters(channel):
    masters = get_map_masters(min_matches=3, top_n=3)
    if not masters:
        return
    card_path = os.path.join(DATA_DIR or ".", "map_masters_card.png")
    await asyncio.to_thread(generate_map_masters_card, masters, card_path)
    await channel.send(file=discord.File(card_path, filename="map_masters.png"))


async def _post_weekly_mvp(channel):
    """Son 7 günün MVP-sini (ən çox qələbə, min. 3 matç) kart şəklində göndərib pinləyir,
    əvvəlki bot pinini götürür — hər həftə YENİ mesaj, canlı redaktə edilmir (mükafat kartından
    fərqli olaraq, tarixçə kimi qalması üçün köhnə mesajlar kanalda saxlanılır)."""
    mvp = get_weekly_mvp()
    if not mvp:
        return None
    card_path = os.path.join(DATA_DIR or ".", "weekly_mvp_card.png")
    await asyncio.to_thread(generate_weekly_mvp_card, mvp, card_path)
    message = await channel.send(
        content=f"🎉 Təbriklər <@{mvp['discord_id']}>! Bu həftənin MVP-si sizsiniz!",
        file=discord.File(card_path, filename="weekly_mvp.png")
    )
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
    return message


_last_weekly_mvp_monday = None


@tasks.loop(minutes=30)
async def weekly_mvp_loop():
    """tasks.loop-da həftəlik interval dəstəyi yoxdur, ona görə tez-tez (30 dəq) yoxlanır,
    amma yalnız Bazar ertəsi (AZ vaxtı ilə, weekday()==0) VƏ bu Bazar ertəsi üçün hələ elan
    edilməyibsə işə düşür — beləliklə bot restart olsa belə eyni gündə təkrar elan getmir.
    30 dəqiqəlik interval seçilib ki, gün AZ vaxtı ilə başlayan kimi (bot son nə vaxt
    restart olduğundan asılı olmadan) tezliklə aşkarlanıb elan olunsun — əvvəlki 24 saatlıq
    interval bot-un son restart vaxtına bağlı idi və gün başlayandan saatlarla sonra
    işə düşə bilirdi."""
    global _last_weekly_mvp_monday
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)  # AZ vaxtı
    if now.weekday() != 0:
        return
    today_key = now.strftime("%Y-%m-%d")
    if _last_weekly_mvp_monday == today_key:
        return
    _last_weekly_mvp_monday = today_key

    channel = await _get_hall_of_fame_channel()
    if channel:
        await _post_weekly_mvp(channel)

    masters_channel = await _get_map_masters_channel()
    if masters_channel:
        await _post_map_masters(masters_channel)


async def _get_reports_channel():
    if not REPORTS_CHANNEL_ID:
        return None
    channel = bot.get_channel(REPORTS_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(REPORTS_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
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


async def _get_achievement_wall_channel():
    if not ACHIEVEMENT_WALL_CHANNEL_ID:
        return None
    channel = bot.get_channel(ACHIEVEMENT_WALL_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(ACHIEVEMENT_WALL_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_boss_event_channel():
    if not BOSS_EVENT_CHANNEL_ID:
        return None
    channel = bot.get_channel(BOSS_EVENT_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(BOSS_EVENT_CHANNEL_ID)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def _get_map_masters_channel():
    if not MAP_MASTERS_CHANNEL_ID:
        return None
    channel = bot.get_channel(MAP_MASTERS_CHANNEL_ID)
    if channel:
        return channel
    try:
        return await bot.fetch_channel(MAP_MASTERS_CHANNEL_ID)
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


_last_anniversary_check_day = None


@tasks.loop(minutes=30)
async def anniversary_check_loop():
    """Qeydiyyat ildönümü olan oyunçulara gündə 1 dəfə (AZ vaxtı ilə) DM təbrik göndərir."""
    global _last_anniversary_check_day
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    day_key = now.strftime("%Y-%m-%d")
    if _last_anniversary_check_day == day_key:
        return
    _last_anniversary_check_day = day_key

    for entry in get_players_with_anniversary_today():
        if not mark_anniversary_greeted(entry["discord_id"], entry["years"]):
            continue
        for guild in bot.guilds:
            member = guild.get_member(entry["discord_id"])
            if member:
                try:
                    await member.send(
                        f"🎉 **{entry['years']} illik ildönümün mübarək, {entry['nick']}!** "
                        "Nextlevelaz icmasına qoşulmağının üstündən düz bu qədər vaxt keçdi. "
                        "Uğurların davam etsin! 🏆"
                    )
                except discord.Forbidden:
                    pass
                break


REWARDS_5V5_TOP3 = [250, 125, 50]  # 2v2-dən fərqli (daha böyük komanda formatı) sezon-sonu mükafatı


async def _rotate_season_for_mode(mode, rewards, lb_channel_id, channel_name_prefix):
    """`season_rotation_loop`-un hər format üçün ortaq işi — sezonu bağlayır, top-3-ə mükafat
    verir, Hall of Fame-də elan edir, statistikanı sıfırlayır, yeni sezon açır və leaderboard
    kanalının adını yeniləyir. 2v2 və 5v5 TAM MÜSTƏQİL çağırılır (öz season_id/cədvəlləri)."""
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
                         + (f" 🎁 +{reward} coin" if reward else ""))
        channel = await _get_hall_of_fame_channel()
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
                color=discord.Color.from_rgb(*_seasonal_accent())
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
    """Ayın 1-ində (AZ vaxtı ilə) 2v2 VƏ 5v5 sezonlarını SİNXRON (eyni tsikldə, ardıcıl)
    bağlayıb yeni sezon açır — hər biri öz mükafat cədvəli və öz statistika cədvəli ilə,
    biri digərinə TOXUNMUR (bax: _rotate_season_for_mode, reset_all_players_for_new_season).
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

    await _rotate_season_for_mode("2v2", [150, 75, 30], leaderboard_channel_id, "leaderboard-sezon")
    await _rotate_season_for_mode("5v5", REWARDS_5V5_TOP3, leaderboard_channel_id_5v5, "leaderboard-5v5-sezon")


# ═══════════════════════════════════════════════════════════════════════════════
# FLASH SALE
# ═══════════════════════════════════════════════════════════════════════════════

@tasks.loop(minutes=45)
async def flash_sale_loop():
    clear_expired_discounts()
    if get_all_discounts():
        return  # artıq aktiv bir flash sale var
    if random.random() >= FLASH_SALE_CHECK_CHANCE:
        return
    candidates = [i for i in MARKET_ITEMS if not i.get("exclusive") and i.get("price") is not None]
    if not candidates:
        return
    item = random.choice(candidates)
    set_discount(item["id"], "market", FLASH_SALE_DISCOUNT_PCT, FLASH_SALE_DURATION_HOURS)
    log_channel = await _get_log_channel()
    if log_channel:
        discounted_price = round(item["price"] * (100 - FLASH_SALE_DISCOUNT_PCT) / 100)
        embed = discord.Embed(
            title="🔥 FLASH SALE!",
            description=(
                f"**{item['name']}** növbəti **{FLASH_SALE_DURATION_HOURS} saat** ərzində "
                f"**{FLASH_SALE_DISCOUNT_PCT}% endirimlə**!\n"
                f"~~{item['price']} coin~~ → **{discounted_price} coin**\n\n"
                "Market → uyğun kataqoriyadan indi alın!"
            ),
            color=discord.Color.from_rgb(255, 120, 40)
        )
        await log_channel.send(embed=embed)


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


# ═══════════════════════════════════════════════════════════════════════════════
# HƏFTƏLİK ŞƏXSİ XÜLASƏ (DM)
# ═══════════════════════════════════════════════════════════════════════════════

@tasks.loop(minutes=30)
async def weekly_summary_dm_loop():
    """Hər Bazar günü (AZ vaxtı ilə), o həftə ən azı 1 matç oynamış (VƏ DM bildirişlərini
    bağlamamış) oyunçulara şəxsi xülasə göndərir. 30 dəqiqəlik interval (bax:
    weekly_mvp_loop-dakı eyni izah) bot-un son restart vaxtından asılı olmadan Bazar günü
    başlayan kimi tezliklə aşkarlanmasını təmin edir."""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)  # AZ vaxtı
    if now.weekday() != 6:  # Bazar
        return
    today_key = now.strftime("%Y-%m-%d")
    if get_meta("last_weekly_summary_date") == today_key:
        return
    set_meta("last_weekly_summary_date", today_key)

    since_ts = int((now - datetime.timedelta(days=7)).timestamp())
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot or not get_dm_notifications(member.id):
                continue
            recap = get_weekly_recap(member.id, since_ts)
            if recap["matches"] == 0:
                continue
            embed = discord.Embed(
                title="📬 Həftəlik Xülasəniz",
                description=(
                    f"Bu həftə **{recap['matches']}** matç oynadınız: **{recap['wins']}Q / {recap['losses']}M**\n"
                    f"ELO dəyişimi: **{'+' if recap['elo_change'] >= 0 else ''}{recap['elo_change']}**\n"
                    f"Qazanılan coin: **{recap['coins_earned']}**\n\n"
                    "Nextlevelaz-də növbəti həftə uğurlar! 🎮"
                ),
                color=discord.Color.from_rgb(138, 92, 230)
            )
            embed.set_footer(text="Bu bildirişi Profil → Bildirişlər düyməsindən bağlaya bilərsiniz.")
            try:
                await member.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass


reward_message_id = None


async def _post_monthly_reward_card(channel):
    """Ayın ELO Çempionu mükafat kartını (bıçaq şəkli + canlı sıralama) kanala göndərib pinləyir,
    əvvəlki bot mesajlarının pinini götürür. Bu mesajı refresh_reward_card loop-u yerində redaktə
    edərək canlı saxlayır (yeni mesaj yox, mövcud mesaj yenilənir)."""
    global reward_message_id
    top_players = [{"nick": r["nick"], "elo": r["combined"]} for r in get_combined_elo_snapshot(5)]
    card_path = os.path.join(DATA_DIR or ".", "monthly_reward_card.png")
    await asyncio.to_thread(generate_monthly_reward_card, MONTHLY_CHAMPION_IMAGE_PATH, top_players, card_path)
    message = await channel.send(file=discord.File(card_path, filename="monthly_reward.png"))
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
    reward_message_id = message.id
    if not refresh_reward_card.is_running():
        refresh_reward_card.start()
    return message


@tasks.loop(minutes=5)
async def refresh_reward_card():
    """Pinlənmiş mükafat kartını yerində redaktə edərək canlı saxlayır (leaderboard kanalındakı
    refresh_leaderboard ilə eyni məntiq). Bot restart olsa, pinlənmiş mesajı özü tapıb bərpa edir."""
    global reward_message_id
    channel = await _get_reward_channel()
    if not channel:
        return

    if reward_message_id is None:
        try:
            pins = await channel.pins()
        except (discord.Forbidden, discord.HTTPException):
            return
        mine = next((m for m in pins if m.author.id == bot.user.id), None)
        if not mine:
            return
        reward_message_id = mine.id

    top_players = [{"nick": r["nick"], "elo": r["combined"]} for r in get_combined_elo_snapshot(5)]
    card_path = os.path.join(DATA_DIR or ".", "monthly_reward_card.png")
    await asyncio.to_thread(generate_monthly_reward_card, MONTHLY_CHAMPION_IMAGE_PATH, top_players, card_path)
    try:
        message = await channel.fetch_message(reward_message_id)
        await message.edit(attachments=[discord.File(card_path, filename="monthly_reward.png")])
    except discord.NotFound:
        reward_message_id = None


async def _send_coach_dm(guild, discord_id, nick, s, old_elo, new_elo, won, match_number):
    """Matçdan sonra oyunçuya AI Coach məsləhətini şəxsi mesajla göndərir. Xəta olarsa sakitcə çıxır."""
    member = guild.get_member(discord_id) if guild else None
    if not member and guild:
        try:
            member = await guild.fetch_member(discord_id)
        except (discord.NotFound, discord.HTTPException):
            return
    if not member:
        return

    tip = await asyncio.to_thread(
        generate_match_coach_tip, nick,
        s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0),
        old_elo, new_elo, won
    )
    if not tip:
        return

    embed = discord.Embed(
        title=f"🧠 AI Coach — Matç No{match_number}",
        description=(
            f"{'✅ Qələbə' if won else '❌ Məğlubiyyət'} · "
            f"K:{s.get('kills',0)} A:{s.get('assists',0)} D:{s.get('deaths',0)} · "
            f"ELO {old_elo} → **{new_elo}**\n\n{tip}"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Nextlevelaz")
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass


TILT_ENCOURAGEMENT_MESSAGES = [
    "Hamının pis günü olur — bir az mola vermək, təzə başla düyməsi kimi işləyir. Su iç, dərin nəfəs al, sonra geri qayıt! 💪",
    "Ardıcıl məğlubiyyətlər çox vaxt yorğunluqdan gəlir, bacarıqdan yox. 10-15 dəqiqə fasilə verməyi düşün.",
    "Unutma: hər ELO düşən oyunçu bir gün geri qayıdıb daha güclü qazanıb. Sakit qal, mövqe seçiminə fokuslan.",
    "Tilt gerçəkdir! İndi bir fasilə verib təzə gözlə qayıtmaq, davam etməkdən daha ağıllı olar.",
]


async def _send_tilt_warning_dm(guild, discord_id, nick, loss_streak):
    """Ardıcıl məğlubiyyət seriyası həvəsdən salmasın deyə həvəsləndirici DM göndərir."""
    member = guild.get_member(discord_id) if guild else None
    if not member and guild:
        try:
            member = await guild.fetch_member(discord_id)
        except (discord.NotFound, discord.HTTPException):
            return
    if not member:
        return
    embed = discord.Embed(
        title="☕ Bir Az Mola Vermə Vaxtıdır?",
        description=(
            f"**{nick}**, son **{loss_streak}** matçda məğlub oldunuz.\n\n"
            f"{random.choice(TILT_ENCOURAGEMENT_MESSAGES)}"
        ),
        color=discord.Color.from_rgb(90, 150, 220)
    )
    embed.set_footer(text="Bu bildirişi Profil → Bildirişlər düyməsindən bağlaya bilərsiniz.")
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass


_intel_briefing_message_ids = set()  # 👍/👎 reaksiya-ilə faydalılıq rəyi izlənilən DM-lər


async def _send_intel_briefing(guild, discord_id, nick, opponent_team, selected_map):
    """Matç başlamazdan əvvəl rəqib komandanın xəritə statistikasına əsaslanan qısa DM göndərir."""
    member = guild.get_member(discord_id) if guild else None
    if not member and guild:
        try:
            member = await guild.fetch_member(discord_id)
        except (discord.NotFound, discord.HTTPException):
            return
    if not member:
        return

    wins, losses = 0, 0
    for opp in opponent_team:
        m = get_map_stats(opp["discord_id"]).get(selected_map)
        if m:
            wins += m.get("wins", 0)
            losses += m.get("losses", 0)

    briefing = await asyncio.to_thread(
        generate_intel_briefing, nick, {"wins": wins, "losses": losses}, selected_map
    )
    if not briefing:
        return

    embed = discord.Embed(
        title=f"🧭 Kəşfiyyat Briefinqi — {selected_map}",
        description=briefing,
        color=discord.Color.dark_teal()
    )
    embed.set_footer(text="Nextlevelaz")
    try:
        briefing_msg = await member.send(embed=embed)
        _intel_briefing_message_ids.add(briefing_msg.id)
        for emoji in ("👍", "👎"):
            await briefing_msg.add_reaction(emoji)
    except discord.Forbidden:
        pass


async def _check_community_goal(guild):
    """Cari AZ ayının icma hədəfini yoxlayır, yeni çatılıbsa hər iştirakçıya mükafat verir."""
    az_now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    month_key = az_now.strftime("%Y-%m")
    ensure_community_goal(month_key, COMMUNITY_GOAL_TARGET, COMMUNITY_GOAL_REWARD_COINS)
    goal = get_community_goal(month_key)
    if not goal or goal["rewarded"]:
        return

    start_ts, end_ts = _month_bounds_ts(az_now.date())
    current = get_month_match_count(start_ts, end_ts)
    if current < goal["target"]:
        return

    mark_goal_rewarded(month_key)
    participants = get_month_participants(start_ts, end_ts)
    for discord_id in participants:
        new_bal = add_coins(discord_id, goal["reward_coins"])
        add_coin_log(discord_id, goal["reward_coins"], f"İcma hədəfi mükafatı ({month_key})", "earn", new_bal)

    log_channel = await _get_log_channel()
    if log_channel:
        embed = discord.Embed(
            title="🌍 İcma hədəfinə çatıldı!",
            description=(
                f"Bu ay **{current}/{goal['target']}** matç oynanıldı! 🎉\n"
                f"İştirak edən **{len(participants)}** oyunçuya **{goal['reward_coins']} coin** verildi."
            ),
            color=discord.Color.green()
        )
        await log_channel.send(embed=embed)


def is_queue_open():
    return True
    az_time = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    hour = az_time.hour
    if QUEUE_OPEN_HOUR > QUEUE_CLOSE_HOUR:
        return hour >= QUEUE_OPEN_HOUR or hour < QUEUE_CLOSE_HOUR
    return QUEUE_OPEN_HOUR <= hour < QUEUE_CLOSE_HOUR


leaderboard_channel_id = None
leaderboard_message_id = None
leaderboard_channel_id_5v5 = None
leaderboard_message_id_5v5 = None
tournament_signup_channel_id = None
tournament_bracket_channel_id = None
queue_status_channel_id = None
queue_status_message_id = None
queue_status_channel_id_5v5 = None
queue_status_message_id_5v5 = None
async def _update_live_board_message(change_note=None):
    """Hər matçdan sonra (60 saniyəlik şəkil-yeniləməsindən daha sürətli) MÖVCUD leaderboard
    mesajının mətn hissəsini Top-10 + son dəyişikliklə yeniləyir. Qəsdən AYRI bir ikinci
    mesaj YARATMIR — eyni pinlənmiş mesajı refresh_leaderboard-ın (şəkli hər 60 saniyə
    yeniləyən loop) payı ilə bölüşür, kanalda iki fərqli "leaderboard" görünüşü olmasın."""
    if leaderboard_channel_id is None or leaderboard_message_id is None:
        return
    channel = bot.get_channel(leaderboard_channel_id)
    if channel is None:
        return
    rows = get_leaderboard(10)
    if not rows:
        return
    lines = [f"{i+1}. **{r[0]}** — {r[2]} ELO ({r[3]}Q/{r[4]}M)" for i, r in enumerate(rows)]
    content = (
        "🏆 **Nextlevelaz FACEIT Leaderboard** — hər 60 saniyədə avtomatik yenilənir "
        "(bu şəkil Top-20-ni göstərir).\n"
        f"🌐 Bütün oyunçuların tam, axtarışlı siyahısı üçün vebsaytımıza baxın: {PUBLIC_WEB_URL}\n\n"
        "📊 **Top 10 (canlı):**\n" + "\n".join(lines)
    )
    if change_note:
        content += f"\n\n🔄 {change_note}"
    content += f"\n\n🕒 Son yeniləmə: <t:{int(datetime.datetime.utcnow().timestamp())}:R>"
    try:
        message = await channel.fetch_message(leaderboard_message_id)
        await message.edit(content=content)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


LEADERBOARD_IMAGE_PATH = "leaderboard.png"
LEADERBOARD_IMAGE_PATH_5V5 = "leaderboard_5v5.png"


@tasks.loop(seconds=60)
async def refresh_leaderboard():
    global leaderboard_message_id
    if leaderboard_channel_id is None or leaderboard_message_id is None:
        return
    channel = bot.get_channel(leaderboard_channel_id)
    if channel is None:
        return
    rows = get_leaderboard(20)
    generate_leaderboard_image(rows, LEADERBOARD_IMAGE_PATH)
    try:
        message = await channel.fetch_message(leaderboard_message_id)
        await message.edit(attachments=[discord.File(LEADERBOARD_IMAGE_PATH, filename="leaderboard.png")])
    except discord.NotFound:
        pass


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


@tasks.loop(seconds=30)
async def check_auctions():
    now_unix = int(datetime.datetime.utcnow().timestamp())
    for auction_id, item_name, current_bid, current_bidder_id, channel_id, message_id in get_due_auctions(now_unix):
        mark_auction_finished(auction_id)
        channel = bot.get_channel(channel_id)
        if channel is None:
            continue
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            message = None

        if current_bidder_id is None:
            result_embed = discord.Embed(
                title="🔨 HƏRRAC BİTDİ",
                description=f"**{item_name}** — heç kim təklif vermədi, qalib təyin olunmadı.",
                color=discord.Color.red()
            )
        elif get_coins(current_bidder_id) < current_bid:
            result_embed = discord.Embed(
                title="🔨 HƏRRAC BİTDİ",
                description=(f"**{item_name}** — qalib <@{current_bidder_id}> ({current_bid} coin) "
                              "hesabında kifayət qədər coin qalmadığı üçün diskvalifikasiya edildi."),
                color=discord.Color.red()
            )
        else:
            spend_coins(current_bidder_id, current_bid)
            new_bal = get_coins(current_bidder_id)
            add_coin_log(current_bidder_id, -current_bid, f"Hərrac qalibi: {item_name}", "spend", new_bal)
            result_embed = discord.Embed(
                title="🔨 HƏRRAC BİTDİ",
                description=f"**{item_name}**\n\n🏆 Qalib: <@{current_bidder_id}> — **{current_bid} coin**\n\nTəbriklər! Zəhmət olmasa mükafatınızı almaq üçün admin ilə əlaqə saxlayın.",
                color=discord.Color.green()
            )
        try:
            if message:
                await message.edit(embed=result_embed, view=None)
            else:
                await channel.send(embed=result_embed)
        except discord.HTTPException:
            pass


@tasks.loop(seconds=3600)
async def refresh_tasks_loop():
    refresh_daily_tasks()


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
                f"`/admin_matc_netice matc_no:{match_number}` ilə nəticə düymələrini yenidən göstərə, "
                "ya da hazır olan komandanı `/admin_matc_elave_et` ilə əl ilə qeyd edə bilərsiniz."
            ),
            color=discord.Color.red()
        )
        await log_channel.send(embed=embed)


def _is_weekend_bonus_active():
    az_now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    # Bayram günləri də eyni 2x coin/ELO bonusunu aktivləşdirir (bax: HOLIDAY_DATES) —
    # matç nəticəsi mətnində "həftəsonu" yazsa da, effekt eynidir; bayramın öz adı ilə
    # ayrıca elan _post_holiday_banner ilə göndərilir.
    return az_now.weekday() in (5, 6) or _is_holiday_bonus_active()  # Şənbə, Bazar


def _is_lightning_round_active():
    until = get_meta("lightning_round_until")
    return bool(until) and int(until) > int(datetime.datetime.utcnow().timestamp())


@tasks.loop(minutes=30)
async def lightning_round_loop():
    if _is_lightning_round_active():
        return
    if random.random() >= LIGHTNING_ROUND_CHECK_CHANCE:
        return

    until_ts = int(datetime.datetime.utcnow().timestamp()) + LIGHTNING_ROUND_DURATION_MINUTES * 60
    set_meta("lightning_round_until", until_ts)

    log_channel = await _get_log_channel()
    if log_channel:
        embed = discord.Embed(
            title="⚡ İLDIRIM TURU BAŞLADI!",
            description=(
                f"Növbəti **{LIGHTNING_ROUND_DURATION_MINUTES} dəqiqə** ərzində başlayan/davam edən "
                "bütün matçlarda ELO və Coin **2x**-dir! Tələsin! ⚡"
            ),
            color=discord.Color.yellow()
        )
        await log_channel.send(embed=embed)


def _month_bounds_ts(d):
    start = datetime.datetime(d.year, d.month, 1, tzinfo=datetime.timezone.utc)
    if d.month == 12:
        end = datetime.datetime(d.year + 1, 1, 1, tzinfo=datetime.timezone.utc)
    else:
        end = datetime.datetime(d.year, d.month + 1, 1, tzinfo=datetime.timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


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

        decayed = apply_elo_decay()
        for d in decayed:
            for guild in bot.guilds:
                await _sync_rank_role(guild, d["discord_id"], d["new_elo"])

        # ── Qeydiyyatdan 3+ gün keçib, heç bir matç oynamayanları təmizlə ────
        inactive_cutoff_ts = day_end_ts - INACTIVE_REGISTRATION_DAYS * 86400
        inactive_players = get_inactive_unplayed_players(inactive_cutoff_ts)
        for p in inactive_players:
            delete_player(p["discord_id"])

        month_start_ts, month_end_ts = _month_bounds_ts(ended_az_date)
        month_match_count = get_month_match_count(month_start_ts, month_end_ts)

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
            embed.add_field(
                name="🌍 İcma hədəfi",
                value=f"{month_match_count}/{COMMUNITY_GOAL_TARGET} matç (bu ay)",
                inline=False
            )
            if decayed:
                embed.add_field(
                    name="📉 Passivlik cəzası",
                    value=f"{len(decayed)} oyunçu 7+ gündür oynamadığı üçün ELO itirdi",
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

            # ── Günün Ortaq Çağırışı (bu gün üçün) ──────────────────────────
            challenge_date_key = new_az_date.strftime("%Y-%m-%d")
            ctype, target, reward, desc = random.choice(DAILY_CHALLENGE_TEMPLATES)
            ensure_daily_challenge(challenge_date_key, ctype, target, reward)
            challenge = get_daily_challenge(challenge_date_key)
            if challenge:
                challenge_embed = discord.Embed(
                    title="🎯 Günün Ortaq Çağırışı",
                    description=(
                        f"{DAILY_CHALLENGE_DESCRIPTIONS.get(challenge['challenge_type'], 'Çağırış')}\n\n"
                        f"Şərti ödəyən hər oyunçu **{challenge['reward_coins']} coin** qazanır!"
                    ),
                    color=discord.Color.teal()
                )
                await log_channel.send(embed=challenge_embed)

            # ── Bayram Matçları (sabahkı gün bayramdırsa elan et) ────────────
            holiday_name = HOLIDAY_DATES.get((new_az_date.month, new_az_date.day))
            if holiday_name:
                holiday_embed = discord.Embed(
                    title=f"🎉 {holiday_name} — Bayram Matçları!",
                    description=(
                        f"Bu gün **{holiday_name}** münasibətilə bütün matçlarda "
                        "**2x Coin və ELO** bonusu aktivdir! Gün ərzində oynayın, "
                        "bonusdan maksimum yararlanın! 🎊"
                    ),
                    color=discord.Color.from_rgb(*HOLIDAY_ACCENT)
                )
                await log_channel.send(embed=holiday_embed)

    # ── Aylıq "Ay Ulduzu" (ayın ilk günündə, keçən ay üçün) ──────────────────
    if new_az_date.day == 1:
        month_key = ended_az_date.strftime("%Y-%m")
        if get_meta("last_star_month") != month_key:
            set_meta("last_star_month", month_key)
            month_start_ts, month_end_ts = _month_bounds_ts(ended_az_date)
            top = get_monthly_top_player(month_start_ts, month_end_ts)
            if top:
                role = None
                for guild in bot.guilds:
                    role = discord.utils.get(guild.roles, name="⭐ Ay Ulduzu")
                    if not role:
                        try:
                            role = await guild.create_role(
                                name="⭐ Ay Ulduzu",
                                color=discord.Color.from_rgb(240, 180, 41),
                                reason="Ay Ulduzu rolu"
                            )
                        except discord.Forbidden:
                            continue

                    old_holder_id = get_meta("last_star_holder_id")
                    if old_holder_id:
                        try:
                            old_member = await guild.fetch_member(int(old_holder_id))
                            if role in old_member.roles:
                                await old_member.remove_roles(role, reason="Ay Ulduzu yeniləndi")
                        except (discord.NotFound, discord.Forbidden, ValueError):
                            pass

                    try:
                        new_member = await guild.fetch_member(top["discord_id"])
                        await new_member.add_roles(role, reason="Ay Ulduzu")
                    except (discord.NotFound, discord.Forbidden):
                        pass

                set_meta("last_star_holder_id", top["discord_id"])

                log_channel = await _get_log_channel()
                if log_channel:
                    embed = discord.Embed(
                        title="⭐ Ayın Ulduzu",
                        description=(
                            f"**{top['nick']}** keçən ayın ən uğurlu oyunçusu oldu!\n"
                            f"🏆 {top['wins']} qələbə · 🎮 {top['matches']} matç\n\n"
                            f"Təbriklər! ⭐ **Ay Ulduzu** rolu təyin edildi."
                        ),
                        color=discord.Color.from_rgb(138, 92, 230)
                    )
                    await log_channel.send(embed=embed)

                    improved = get_most_improved_player(month_start_ts, month_end_ts)
                    most_active = get_month_most_active(month_start_ts, month_end_ts)
                    awards_embed = discord.Embed(
                        title="🏆 Nextlevelaz Mükafatları",
                        description=f"Keçən ayın ({ended_az_date.strftime('%m.%Y')}) mükafatları:",
                        color=discord.Color.from_rgb(138, 92, 230)
                    )
                    awards_embed.add_field(
                        name="🥇 MVP", value=f"{top['nick']} — {top['wins']} qələbə", inline=False
                    )
                    if improved:
                        gain = improved["elo_gain"]
                        awards_embed.add_field(
                            name="📈 Ən Çox İnkişaf Edən",
                            value=f"{improved['nick']} — {'+' if gain >= 0 else ''}{gain} ELO",
                            inline=False
                        )
                    if most_active:
                        awards_embed.add_field(
                            name="🎮 Ən Aktiv Oyunçu",
                            value=f"{most_active['nick']} — {most_active['matches']} matç",
                            inline=False
                        )
                    await log_channel.send(embed=awards_embed)

                    # ── Ayın ELO çempionuna (2v2+5v5 ELO cəmi) bıçaq mükafatı ────
                    top_combined = get_combined_elo_snapshot(limit=1)
                    top_elo = top_combined[0] if top_combined and top_combined[0]["combined"] > 0 else None
                    if top_elo:
                        add_skin_to_inventory(
                            top_elo["discord_id"], 0, MONTHLY_CHAMPION_SKIN_NAME, 0,
                            image_url=MONTHLY_CHAMPION_IMAGE_PATH
                        )
                        knife_embed = discord.Embed(
                            title=f"🔪 Ayın ELO Çempionu — {MONTHLY_CHAMPION_SKIN_NAME}",
                            description=(
                                f"**{top_elo['nick']}** {ended_az_date.strftime('%m.%Y')} ayının son günündə "
                                f"2v2+5v5 ELO cəminə görə (**{top_elo['combined']}** = {top_elo['elo_2v2']} + "
                                f"{top_elo['elo_5v5']}) ən yüksək nəticəyə sahib oyunçu oldu və mükafat olaraq "
                                f"**{MONTHLY_CHAMPION_SKIN_NAME}** skinini qazandı! 🎉\n\n"
                                f"Rəhbərlik tezliklə oyun daxilində təhvil verəcək."
                            ),
                            color=discord.Color.from_rgb(138, 92, 230)
                        )
                        if os.path.exists(MONTHLY_CHAMPION_IMAGE_PATH):
                            knife_file = discord.File(MONTHLY_CHAMPION_IMAGE_PATH, filename="butterfly_legacy.jpg")
                            knife_embed.set_image(url="attachment://butterfly_legacy.jpg")
                            await log_channel.send(embed=knife_embed, file=knife_file)
                        else:
                            await log_channel.send(embed=knife_embed)


_status_index = 0


@tasks.loop(minutes=5)
async def rotate_status_loop():
    global _status_index
    texts = [
        f"👀 {get_player_count()} qeydiyyatlı oyunçu",
        f"🎮 {get_total_match_count()} matç oynanılıb",
    ]
    star_holder_id = get_meta("last_star_holder_id")
    if star_holder_id:
        row = get_player(int(star_holder_id))
        if row:
            texts.append(f"⭐ Ay Ulduzu: {row[1]}")

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


class TeamReadyView(discord.ui.View):
    """Stateless/persistent görünüş: hər klik zamanı aktiv matçı bazadan təzədən oxuyur,
    ona görə bot restart olsa belə (deploy zamanı) düymələr işləməyə davam edir."""

    def __init__(self, team_a=None, team_b=None):
        super().__init__(timeout=None)
        roster = list(team_a or []) + list(team_b or [])
        for i in range(4):
            label = roster[i]["nick"][:80] if i < len(roster) else f"Oyunçu {i + 1}"
            btn = discord.ui.Button(
                label=label, style=discord.ButtonStyle.secondary,
                custom_id=f"player_info_{i}", row=1
            )
            btn.callback = self._make_player_info_callback(i)
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
            await _render_stats(interaction, target_id)
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
                title=f"✅ Matç No{active['match_number']} — Hər iki komanda hazır",
                description="Admin/moderator nəticəni aşağıdaki düymələrlə qeyd etməlidir.",
                color=discord.Color.blurple()
            )
            log_channel = await _get_log_channel()
            if log_channel:
                result_view = MatchResultView(active["match_number"], active["team_a"], active["team_b"])
                await log_channel.send(embed=log_embed, view=result_view)

    @discord.ui.button(label="Komanda A Hazır", style=discord.ButtonStyle.primary, custom_id="ready_a")
    async def team_a_ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set_ready(interaction, True, button)

    @discord.ui.button(label="Komanda B Hazır", style=discord.ButtonStyle.danger, custom_id="ready_b")
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
        card_path = os.path.join(DATA_DIR or ".", f"match_{active['match_number']}.png")
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

        # Səs kanalları artıq yaradılıbsa, yeni xəritəni əks etdirsin deyə adları yenilənir
        # (hər komanda cəmi 1 veto haqqına malikdir, ona görə kanal başına maksimum 1 rename —
        # Discord-un ad-dəyişmə limitindən (10 dəqiqədə 2) çox-çox aşağıdır).
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

    @discord.ui.button(label="🚫 Xəritəni Veto Et (A)", style=discord.ButtonStyle.secondary, custom_id="veto_a", row=2)
    async def veto_a_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._veto(interaction, True, button)

    @discord.ui.button(label="🚫 Xəritəni Veto Et (B)", style=discord.ButtonStyle.secondary, custom_id="veto_b", row=2)
    async def veto_b_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._veto(interaction, False, button)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="cancel_match")
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

        view = CancelMatchView(active["match_number"], active["team_a"], active["team_b"])
        embed = discord.Embed(
            title=f"🚫 Matç No{active['match_number']} ləğv edilir",
            description=(
                "Gəlməyən oyunçu varsa aşağıdan seçin (ELO cəzası alacaq), "
                "yoxdursa \"Heç kimə cəza olmasın\"-ı seçin."
            ),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


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
            achievements = get_player_achievements(target_id)
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


class CancelMatchView(discord.ui.View):
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
            row = get_player(absent_id)
            if row:
                old_elo = row[3]
                new_elo = max(0, old_elo - MATCH_CANCEL_ELO_PENALTY)
                admin_set_player_field(absent_id, "elo", new_elo)
                log_admin_action(
                    "match_cancel_penalty", absent_id, "elo", str(old_elo), str(new_elo),
                    f"Matç No{self.match_number} ləğvi — gəlmədi", interaction.user.id
                )
                await _post_audit_log(
                    "match_cancel_penalty", absent_id, "elo", old_elo, new_elo,
                    f"Matç No{self.match_number} ləğvi — gəlmədi", interaction.user.id
                )
                penalized_nick = next((p["nick"] for p in all_players if p["discord_id"] == absent_id), None)

        returned = []
        for p in all_players:
            if absent_id is not None and p["discord_id"] == absent_id:
                continue
            row = get_player(p["discord_id"])
            elo = row[3] if row else p.get("elo", 1000)
            if add_to_queue(p["discord_id"], p["nick"], elo):
                returned.append(p["nick"])

        # Əvvəlcə DB-də ləğv edilir (oyunçular dərhal sıraya qoşula bilsin), SONRA Discord
        # tərəfi (səs kanalı silinməsi) — bu sıra ilə, Discord API xətası heç vaxt oyunçuları
        # "aktiv matçda" vəziyyətində ilişik saxlaya bilməz.
        clear_active_match(self.match_number)
        await _cleanup_match_voice_channels(interaction.guild, active)

        desc = f"Matç No{self.match_number} ləğv edildi."
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

        # Qəsdən _start_match_if_ready çağırılmır — ləğvdən sonra yeni matç
        # dərhal deyil, yalnız YENİ bir sıra dolduqda (kimsə /2v2 ilə qoşulanda) başlasın.
        await update_queue_status_message()


class MatchResultView(discord.ui.View):
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

        # Aşağıdakı proses (ELO, coin, achievement, rütbə rol sinxronizasiyası hər oyunçu
        # üçün canlı Discord API çağırışı tələb edir) 3 saniyəlik Discord cavab limitini
        # asanlıqla keçə bilər (xüsusən scan statistikası varsa, hər oyunçu üçün əlavə iş
        # olur) — buna görə dərhal defer edilir, "Zenbot yanıt vermədi" xətasının qarşısı
        # alınır. Sonda nəticəni edit_original_response ilə eyni mesaja yazırıq.
        await interaction.response.defer()

        winner_ids = [p["discord_id"] for p in winner_team]
        loser_ids = [p["discord_id"] for p in loser_team]

        active_before = get_active_match(self.match_number)
        selected_map = active_before.get("selected_map") if active_before else None
        is_golden = bool(active_before.get("is_golden")) if active_before else False
        is_lightning = bool(active_before.get("is_lightning")) if active_before else False
        elo_multiplier = (2 if is_golden else 1) * (2 if is_lightning else 1)

        results = update_team_elo(winner_ids, loser_ids, elo_multiplier=elo_multiplier)
        if results is None:
            await interaction.followup.send("❌ Xəta: oyunçu məlumatları tapılmadı.", ephemeral=True)
            return

        self.finished = True
        for child in self.children:
            child.disabled = True

        # Scan sistemi ilə oxunmuş K/A/D varsa, tətbiq et
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

        if stats_by_id:
            boss_contributions = {did: s.get("kills", 0) for did, s in stats_by_id.items() if s.get("kills", 0) > 0}
            asyncio.create_task(_update_boss_progress(boss_contributions))

        # Sürpriz Aşkarlayıcı — məğlub komandanın ELO ortalaması qalibdən xeyli yüksəkdirsə
        winner_avg_old_elo = sum(r["old_elo"] for r in results["winners"]) / len(results["winners"])
        loser_avg_old_elo = sum(r["old_elo"] for r in results["losers"]) / len(results["losers"])
        is_upset = (loser_avg_old_elo - winner_avg_old_elo) >= UPSET_ELO_THRESHOLD

        az_now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        today_key = az_now.strftime("%Y-%m-%d")

        # Coin mükafatı, seriya, günlük tapşırıq irəliləyişi, nailiyyətlər, rütbə, rekord
        new_achievements = []
        new_titles = []
        new_quests = []
        challenge_claimers = []
        achievement_rarity = get_achievement_rarity()

        mvp_id = None
        if stats_by_id:
            mvp_id = max(
                stats_by_id.items(),
                key=lambda kv: kv[1].get("kills", 0) * 2 + kv[1].get("assists", 0) - kv[1].get("deaths", 0)
            )[0]

        current_season = get_or_create_current_season()

        for p, r in zip(winner_team, results["winners"]):
            did = p["discord_id"]
            add_season_stat(did, current_season["id"], kills=stats_by_id.get(did, {}).get("kills", 0),
                             assists=stats_by_id.get(did, {}).get("assists", 0),
                             deaths=stats_by_id.get(did, {}).get("deaths", 0),
                             wins=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"])
            streak, _ = update_streak(did, True)
            bonus_coins, _bonus_elo = get_streak_bonus(streak)
            earned = random.randint(5, 10) + bonus_coins
            if _is_weekend_bonus_active():
                earned *= 2
            if is_golden:
                earned *= 2
            if is_lightning:
                earned *= 2
            new_bal = add_coins(did, earned)
            reason = f"Matç No{self.match_number} qələbə" + (f" (seriya {streak})" if bonus_coins else "")
            if _is_weekend_bonus_active():
                reason += " (həftəsonu 2x)"
            if is_golden:
                reason += " (Qızıl Matç 2x)"
            if is_lightning:
                reason += " (İldırım Turu 2x)"
            add_coin_log(did, earned, reason, "earn", new_bal)
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            if did in stats_by_id:
                update_personal_record(did, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), self.match_number)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
                if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ach["name"], ach["icon"], "nailiyyət"))
                asyncio.create_task(_maybe_grant_sticker(interaction.guild, did, p["nick"], ach["id"]))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
                if interaction.guild:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ti["name"], ti["icon"], "ləqəb"))
            for q in update_quest_progress(did, "win_matches"):
                new_quests.append((p["nick"], q))
            if is_golden:
                for q in update_quest_progress(did, "golden_match_play"):
                    new_quests.append((p["nick"], q))
            if did in stats_by_id and claim_daily_challenge(
                did, today_key, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), True
            ):
                challenge_claimers.append(p["nick"])
            await _sync_rank_role(interaction.guild, did, r["new_elo"])
            if did in stats_by_id and interaction.guild:
                asyncio.create_task(_send_coach_dm(
                    interaction.guild, did, p["nick"], s, r["old_elo"], r["new_elo"], True, self.match_number
                ))

        for p, r in zip(loser_team, results["losers"]):
            did = p["discord_id"]
            add_season_stat(did, current_season["id"], kills=stats_by_id.get(did, {}).get("kills", 0),
                             assists=stats_by_id.get(did, {}).get("assists", 0),
                             deaths=stats_by_id.get(did, {}).get("deaths", 0),
                             losses=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"])
            update_streak(did, False)
            loss_streak = get_loss_streak(did)
            if loss_streak == TILT_LOSS_STREAK_THRESHOLD and get_dm_notifications(did) and interaction.guild:
                asyncio.create_task(_send_tilt_warning_dm(interaction.guild, did, p["nick"], loss_streak))
            earned = random.randint(0, 5)
            if _is_weekend_bonus_active():
                earned *= 2
            if is_golden:
                earned *= 2
            if is_lightning:
                earned *= 2
            new_bal = add_coins(did, earned)
            add_coin_log(
                did, earned,
                f"Matç No{self.match_number} iştirak"
                + (" (həftəsonu 2x)" if _is_weekend_bonus_active() else "")
                + (" (Qızıl Matç 2x)" if is_golden else "")
                + (" (İldırım Turu 2x)" if is_lightning else ""),
                "earn", new_bal
            )
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            if did in stats_by_id:
                update_personal_record(did, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), self.match_number)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
                if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ach["name"], ach["icon"], "nailiyyət"))
                asyncio.create_task(_maybe_grant_sticker(interaction.guild, did, p["nick"], ach["id"]))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
                if interaction.guild:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ti["name"], ti["icon"], "ləqəb"))
            if did in stats_by_id and claim_daily_challenge(
                did, today_key, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), False
            ):
                challenge_claimers.append(p["nick"])
            await _sync_rank_role(interaction.guild, did, r["new_elo"])
            if did in stats_by_id and interaction.guild:
                asyncio.create_task(_send_coach_dm(
                    interaction.guild, did, p["nick"], s, r["old_elo"], r["new_elo"], False, self.match_number
                ))

        # Squad bonusu — qalib komandanın iki üzvü eyni aktiv squad-dırsa
        if len(winner_team) == 2:
            squad = get_squad(winner_team[0]["discord_id"])
            if squad and squad["partner_id"] == winner_team[1]["discord_id"]:
                for p in winner_team:
                    bal = add_coins(p["discord_id"], 10)
                    add_coin_log(p["discord_id"], 10, f"Squad bonusu — Matç No{self.match_number}", "earn", bal)
                    for q in update_quest_progress(p["discord_id"], "squad_win"):
                        new_quests.append((p["nick"], q))
                record_squad_win(winner_team[0]["discord_id"], winner_team[1]["discord_id"])

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        embed = discord.Embed(
            title=f"✅ Matç No{self.match_number} — Nəticə qeyd edildi",
            description=f"🗓️ {now.strftime('%d.%m.%Y %H:%M')} (AZ vaxtı)\n🏆 Qalib: **{winner_label}**"
            + ("\n🎉 **Həftəsonu bonusu aktivdir — 2x coin!**" if _is_weekend_bonus_active() else "")
            + ("\n🌟 **Qızıl Matç idi — 2x ELO və Coin!**" if is_golden else "")
            + ("\n⚡ **İldırım Turu idi — əlavə 2x ELO və Coin!**" if is_lightning else ""),
            color=discord.Color.from_rgb(138, 92, 230)
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

        # Animasiyalı nailiyyət/ləqəb bildirişi — əvvəlcə "açılır..." teaser göstərilir,
        # sonra (aşağıda) tam siyahı ilə redaktə olunur ki hədiyyə qutusu açılan effekti yaransın.
        if new_achievements or new_titles:
            teaser = embed.copy()
            teaser.set_footer(text="🎁 Yeni nailiyyətlər açılır...")
            await interaction.edit_original_response(embed=teaser, view=self)
            await asyncio.sleep(1.4)

        if new_achievements:
            embed.add_field(
                name="🏆 Yeni nailiyyətlər",
                value="\n".join(f"{ach['icon']} **{ach['name']}** — {nick}" for nick, ach in new_achievements),
                inline=False
            )
        if new_titles:
            embed.add_field(
                name="🏅 Yeni ləqəblər",
                value="\n".join(f"{t['icon']} **{t['name']}** — {nick}" for nick, t in new_titles),
                inline=False
            )
        if new_quests:
            embed.add_field(
                name="🧗 Quest tamamlandı!",
                value="\n".join(f"**{q['name']}** ({q['reward_coins']} coin) — {nick}" for nick, q in new_quests),
                inline=False
            )
        if challenge_claimers:
            embed.add_field(
                name="🎯 Günün Çağırışı tamamlandı",
                value=", ".join(challenge_claimers),
                inline=False
            )

        await asyncio.to_thread(
            record_match_history, "2v2", winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
            self.match_number, selected_map
        )
        if interaction.guild:
            await _check_community_goal(interaction.guild)
        asyncio.create_task(_update_live_board_message(f"Matç No{self.match_number}: **{winner_label}** qalib gəldi"))
        if interaction.guild:
            asyncio.create_task(_send_teammate_rating_prompts(interaction.guild, winner_team, self.match_number))
            asyncio.create_task(_send_teammate_rating_prompts(interaction.guild, loser_team, self.match_number))

        await interaction.edit_original_response(embed=embed, view=self)
        log_channel = await _get_log_channel()
        if log_channel and log_channel.id != interaction.channel.id:
            await log_channel.send(embed=embed)

        if is_upset:
            upset_embed = discord.Embed(
                title="🔥 BÖYÜK SÜRPRİZ!",
                description=(
                    f"**{winner_label}** ({round(winner_avg_old_elo)} orta ELO) "
                    f"**{loser_label}**-i ({round(loser_avg_old_elo)} orta ELO) məğlub etdi — "
                    f"{round(loser_avg_old_elo - winner_avg_old_elo)} ELO fərqinə baxmayaraq!"
                ),
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=upset_embed)
            if log_channel and log_channel.id != interaction.channel.id:
                await log_channel.send(embed=upset_embed)

        # Əvvəlcə DB-də matç bağlanır (oyunçular dərhal sıraya qoşula bilsin) — SONRA Discord
        # tərəfi (köhnə mesaj/səs kanalı/thread təmizliyi), ki bu best-effort addımlardan
        # hər hansı biri xəta versə belə oyunçular "aktiv matçda" vəziyyətində ilişib qalmasın.
        clear_active_match(self.match_number)

        # Orijinal "Hazır" mesajını sil, dinamik səs kanallarını təmizlə
        # (oyunçuları lobbiyə köçürüb), thread-i yekunlaşdır
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

        await _start_match_if_ready(log_channel or interaction.channel, interaction.guild)

    @discord.ui.button(label="Komanda A qalib", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="result_a")
    async def team_a_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_a, self.team_b, "Komanda A", "Komanda B")

    @discord.ui.button(label="Komanda B qalib", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="result_b")
    async def team_b_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_b, self.team_a, "Komanda B", "Komanda A")


class MatchResultView5v5(discord.ui.View):
    """`MatchResultView`-in 5v5 analoqu. FƏRQ: ELO/streak/rütbə/mövsüm 5v5 cədvəllərinə
    yazılır, `match_history` "5v5" işarəli. PAYLAŞILAN (dəyişməz): coin,
    gündəlik çağırış, nailiyyət/ləqəb, şəxsi rekord, coach/tilt DM-ləri — bunlar discord_id-yə
    bağlıdır, formatdan asılı deyil. Squad bonusu (2-nəfərlik sabit cütlük konsepti) 5 nəfərlik
    komandaya aid olmadığı üçün buraxılıb."""
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
        is_golden = bool(active_before.get("is_golden")) if active_before else False
        is_lightning = bool(active_before.get("is_lightning")) if active_before else False
        elo_multiplier = (2 if is_golden else 1) * (2 if is_lightning else 1)

        results = update_team_elo_5v5(winner_ids, loser_ids, elo_multiplier=elo_multiplier)
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

        winner_avg_old_elo = sum(r["old_elo"] for r in results["winners"]) / len(results["winners"])
        loser_avg_old_elo = sum(r["old_elo"] for r in results["losers"]) / len(results["losers"])
        is_upset = (loser_avg_old_elo - winner_avg_old_elo) >= UPSET_ELO_THRESHOLD

        az_now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        today_key = az_now.strftime("%Y-%m-%d")

        new_achievements = []
        new_titles = []
        new_quests = []
        challenge_claimers = []
        achievement_rarity = get_achievement_rarity()

        mvp_id = None
        if stats_by_id:
            mvp_id = max(
                stats_by_id.items(),
                key=lambda kv: kv[1].get("kills", 0) * 2 + kv[1].get("assists", 0) - kv[1].get("deaths", 0)
            )[0]

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
            if _is_weekend_bonus_active():
                earned *= 2
            if is_golden:
                earned *= 2
            if is_lightning:
                earned *= 2
            new_bal = add_coins(did, earned)
            reason = f"5v5 Matç No{self.match_number} qələbə" + (f" (seriya {streak})" if bonus_coins else "")
            if _is_weekend_bonus_active():
                reason += " (həftəsonu 2x)"
            if is_golden:
                reason += " (Qızıl Matç 2x)"
            if is_lightning:
                reason += " (İldırım Turu 2x)"
            add_coin_log(did, earned, reason, "earn", new_bal)
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            if did in stats_by_id:
                update_personal_record(did, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), self.match_number)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
                if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ach["name"], ach["icon"], "nailiyyət"))
                asyncio.create_task(_maybe_grant_sticker(interaction.guild, did, p["nick"], ach["id"]))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
                if interaction.guild:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ti["name"], ti["icon"], "ləqəb"))
            for q in update_quest_progress(did, "win_matches"):
                new_quests.append((p["nick"], q))
            if is_golden:
                for q in update_quest_progress(did, "golden_match_play"):
                    new_quests.append((p["nick"], q))
            if did in stats_by_id and claim_daily_challenge(
                did, today_key, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), True
            ):
                challenge_claimers.append(p["nick"])
            await _sync_rank_role_5v5(interaction.guild, did, r["new_elo"])
            if did in stats_by_id and interaction.guild:
                asyncio.create_task(_send_coach_dm(
                    interaction.guild, did, p["nick"], s, r["old_elo"], r["new_elo"], True, self.match_number
                ))

        for p, r in zip(loser_team, results["losers"]):
            did = p["discord_id"]
            add_season_stat(did, current_season["id"], kills=stats_by_id.get(did, {}).get("kills", 0),
                             assists=stats_by_id.get(did, {}).get("assists", 0),
                             deaths=stats_by_id.get(did, {}).get("deaths", 0),
                             losses=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"], mode="5v5")
            update_streak_5v5(did, False)
            loss_streak = get_loss_streak_5v5(did)
            if loss_streak == TILT_LOSS_STREAK_THRESHOLD and get_dm_notifications(did) and interaction.guild:
                asyncio.create_task(_send_tilt_warning_dm(interaction.guild, did, p["nick"], loss_streak))
            earned = random.randint(0, 5)
            if _is_weekend_bonus_active():
                earned *= 2
            if is_golden:
                earned *= 2
            if is_lightning:
                earned *= 2
            new_bal = add_coins(did, earned)
            add_coin_log(
                did, earned,
                f"5v5 Matç No{self.match_number} iştirak"
                + (" (həftəsonu 2x)" if _is_weekend_bonus_active() else "")
                + (" (Qızıl Matç 2x)" if is_golden else "")
                + (" (İldırım Turu 2x)" if is_lightning else ""),
                "earn", new_bal
            )
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            if did in stats_by_id:
                update_personal_record(did, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), self.match_number)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
                if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ach["name"], ach["icon"], "nailiyyət"))
                asyncio.create_task(_maybe_grant_sticker(interaction.guild, did, p["nick"], ach["id"]))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
                if interaction.guild:
                    asyncio.create_task(_post_wall_announcement(interaction.guild, did, p["nick"], ti["name"], ti["icon"], "ləqəb"))
            if did in stats_by_id and claim_daily_challenge(
                did, today_key, s.get("kills", 0), s.get("assists", 0), s.get("deaths", 0), False
            ):
                challenge_claimers.append(p["nick"])
            await _sync_rank_role_5v5(interaction.guild, did, r["new_elo"])
            if did in stats_by_id and interaction.guild:
                asyncio.create_task(_send_coach_dm(
                    interaction.guild, did, p["nick"], s, r["old_elo"], r["new_elo"], False, self.match_number
                ))

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        embed = discord.Embed(
            title=f"✅ 5v5 Matç No{self.match_number} — Nəticə qeyd edildi",
            description=f"🗓️ {now.strftime('%d.%m.%Y %H:%M')} (AZ vaxtı)\n🏆 Qalib: **{winner_label}**"
            + ("\n🎉 **Həftəsonu bonusu aktivdir — 2x coin!**" if _is_weekend_bonus_active() else "")
            + ("\n🌟 **Qızıl Matç idi — 2x ELO və Coin!**" if is_golden else "")
            + ("\n⚡ **İldırım Turu idi — əlavə 2x ELO və Coin!**" if is_lightning else ""),
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

        if new_achievements or new_titles:
            teaser = embed.copy()
            teaser.set_footer(text="🎁 Yeni nailiyyətlər açılır...")
            await interaction.edit_original_response(embed=teaser, view=self)
            await asyncio.sleep(1.4)

        if new_achievements:
            embed.add_field(
                name="🏆 Yeni nailiyyətlər",
                value="\n".join(f"{ach['icon']} **{ach['name']}** — {nick}" for nick, ach in new_achievements),
                inline=False
            )
        if new_titles:
            embed.add_field(
                name="🏅 Yeni ləqəblər",
                value="\n".join(f"{t['icon']} **{t['name']}** — {nick}" for nick, t in new_titles),
                inline=False
            )
        if new_quests:
            embed.add_field(
                name="🧗 Quest tamamlandı!",
                value="\n".join(f"**{q['name']}** ({q['reward_coins']} coin) — {nick}" for nick, q in new_quests),
                inline=False
            )
        if challenge_claimers:
            embed.add_field(
                name="🎯 Günün Çağırışı tamamlandı",
                value=", ".join(challenge_claimers),
                inline=False
            )

        await asyncio.to_thread(
            record_match_history, "5v5", winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
            self.match_number, selected_map
        )
        if interaction.guild:
            await _check_community_goal(interaction.guild)
        asyncio.create_task(_update_live_board_message_5v5(f"5v5 Matç No{self.match_number}: **{winner_label}** qalib gəldi"))
        if interaction.guild:
            asyncio.create_task(_send_teammate_rating_prompts(interaction.guild, winner_team, self.match_number))
            asyncio.create_task(_send_teammate_rating_prompts(interaction.guild, loser_team, self.match_number))

        await interaction.edit_original_response(embed=embed, view=self)
        log_channel = await _get_log_channel_5v5() or await _get_log_channel()
        if log_channel and log_channel.id != interaction.channel.id:
            await log_channel.send(embed=embed)

        if is_upset:
            upset_embed = discord.Embed(
                title="🔥 BÖYÜK SÜRPRİZ!",
                description=(
                    f"**{winner_label}** ({round(winner_avg_old_elo)} orta ELO) "
                    f"**{loser_label}**-i ({round(loser_avg_old_elo)} orta ELO) məğlub etdi — "
                    f"{round(loser_avg_old_elo - winner_avg_old_elo)} ELO fərqinə baxmayaraq!"
                ),
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=upset_embed)
            if log_channel and log_channel.id != interaction.channel.id:
                await log_channel.send(embed=upset_embed)

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


QUEUE_STATUS_IMAGE_PATH = "queue_status.png"


async def update_queue_status_message():
    global queue_status_message_id
    if queue_status_channel_id is None or queue_status_message_id is None:
        return
    channel = bot.get_channel(queue_status_channel_id)
    if channel is None:
        return
    players = get_queue_list()
    image_path = os.path.join(DATA_DIR or ".", QUEUE_STATUS_IMAGE_PATH)
    await asyncio.to_thread(generate_queue_status_card, players, image_path)
    try:
        message = await channel.fetch_message(queue_status_message_id)
        await message.edit(attachments=[discord.File(image_path, filename="queue_status.png")])
    except discord.NotFound:
        pass


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


_match_start_lock = asyncio.Lock()


async def _start_match_if_ready(channel, guild):
    """Sırada 4 nəfər varsa VƏ paralel matç limitində yer varsa, ardıcıl yeni matç(lar) başladır.
    Kilidlə əhatələnir ki eyni 4 nəfər üçün paralel çağırışlar (məs. bir neçə oyunçu demək olar
    eyni anda sıraya qoşulanda, hər birinin öz handler-i də bu funksiyanı çağırır) təsadüfən
    2 dublikat matç yaratmasın — kilid altında sıra artıq boşalmış olacaq, ikinci çağırış heç nə etməyəcək."""
    async with _match_start_lock:
        while count_active_matches(mode="2v2") < MAX_PARALLEL_MATCHES and queue_size() >= 4:
            started = await _start_one_match(channel, guild)
            if not started:
                break


_match_start_lock_5v5 = asyncio.Lock()


async def _start_match_if_ready_5v5(channel, guild):
    """`_start_match_if_ready`-in 5v5 analoqu — AYRICA kilid istifadə edir ki, 2v2 və 5v5
    matç başlatma məntiqi bir-birini gözləməsin (əsl paralellik)."""
    async with _match_start_lock_5v5:
        while count_active_matches(mode="5v5") < MAX_PARALLEL_MATCHES and queue_size_5v5() >= 10:
            started = await _start_one_5v5_match(channel, guild)
            if not started:
                break


WARMUP_VOICE_CHANNEL_NAME = "🎤 İsınma Otağı"
WARMUP_VOICE_CHANNEL_NAME_5V5 = "🎤 İsınma Otağı (5v5)"


async def _get_or_create_warmup_channel(guild, mode="2v2"):
    if not guild:
        return None
    name = WARMUP_VOICE_CHANNEL_NAME_5V5 if mode == "5v5" else WARMUP_VOICE_CHANNEL_NAME
    category_name = CATEGORY_5V5_NAME if mode == "5v5" else FULL_SETUP_CATEGORY_NAME
    existing = discord.utils.get(guild.voice_channels, name=name)
    if existing:
        return existing
    category = discord.utils.get(guild.categories, name=category_name)
    try:
        return await guild.create_voice_channel(name, category=category)
    except discord.Forbidden:
        return None


async def _start_one_match(channel, guild) -> bool:
    result = pop_4_and_balance()
    if result is None:
        return False
    team_a, team_b, captain_a, captain_b = result
    selected_map = random.choice(MAPS)
    match_number = get_next_match_number()
    is_golden = random.random() < GOLDEN_MATCH_CHANCE
    is_lightning = _is_lightning_round_active()

    set_active_match(
        match_number,
        team_a_json=json.dumps(team_a, ensure_ascii=False),
        team_b_json=json.dumps(team_b, ensure_ascii=False),
        selected_map=selected_map,
        captain_a_id=captain_a["discord_id"],
        captain_b_id=captain_b["discord_id"],
        is_golden=is_golden, is_lightning=is_lightning
    )

    # Kapitan seçimi animasiyası — matç kartından ƏVVƏL qısa "🎲 seçilir..." reveal effekti
    captain_reveal_msg = None
    try:
        captain_reveal_msg = await channel.send(f"🎲 Matç No{match_number} — kapitanlar seçilir...")
        await asyncio.sleep(1.0)
        await captain_reveal_msg.edit(content=f"🔵 Komanda A Kapitanı: **{captain_a['nick']}** seçildi!")
        await asyncio.sleep(0.8)
        await captain_reveal_msg.edit(
            content=f"🔵 Komanda A Kapitanı: **{captain_a['nick']}**\n🔴 Komanda B Kapitanı: **{captain_b['nick']}** seçildi!"
        )
        await asyncio.sleep(0.8)
    except discord.HTTPException:
        pass

    card_path = os.path.join(DATA_DIR or ".", f"match_{match_number}.png")
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
    if is_golden:
        mentions += "\n\n🌟 **QIZIL MATÇ!** Bu matçda ELO və Coin dəyişimi 2x-dir!"
    if is_lightning:
        mentions += "\n\n⚡ **İldırım Turu davam edir!** Bu matçda ELO və Coin əlavə 2x-dir!"
    ready_view = TeamReadyView(team_a, team_b)
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

    # Hər matç üçün ayrıca thread — koordinasiya bir-birinə qarışmasın
    thread_id = None
    try:
        thread = await sent_message.create_thread(
            name=f"Matç #{match_number} — {selected_map}", auto_archive_duration=60
        )
        thread_id = thread.id
        await thread.send(f"{mentions}\n💬 Bu matç üçün koordinasiyanı burada apara bilərsiniz.")
    except discord.HTTPException:
        pass

    set_active_match_message(match_number, sent_message.id, channel.id, thread_id)

    social_channel = await _get_social_channel()
    if social_channel:
        announce_embed = discord.Embed(
            title=f"🎮 Yeni Matç Başladı — No{match_number}",
            description=(
                f"🗺️ Xəritə: **{selected_map}**\n\n"
                "Lobbi operativ qurulsun deyə kapitanlarla dərhal əlaqə saxlayın!"
            ),
            color=discord.Color.from_rgb(138, 92, 230)
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
        announce_embed.set_footer(text="Nextlevelaz")
        try:
            await social_channel.send(embed=announce_embed)
        except discord.Forbidden:
            pass

    if guild:
        for p in team_a:
            asyncio.create_task(_send_intel_briefing(guild, p["discord_id"], p["nick"], team_b, selected_map))
        for p in team_b:
            asyncio.create_task(_send_intel_briefing(guild, p["discord_id"], p["nick"], team_a, selected_map))

    # Hər matç üçün dinamik, müvəqqəti səs kanalları (paralel matçlar qarışmasın)
    voice_a_channel = voice_b_channel = None
    if guild:
        category = discord.utils.get(guild.categories, name=FULL_SETUP_CATEGORY_NAME)
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
            print(f"[VOICE] Matç #{match_number} üçün səs kanalları yaradıla bilmədi (icazə yoxdur).", flush=True)

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

    await update_queue_status_message()
    return True


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
    is_golden = random.random() < GOLDEN_MATCH_CHANCE
    is_lightning = _is_lightning_round_active()

    set_active_match(
        match_number,
        team_a_json=json.dumps(team_a, ensure_ascii=False),
        team_b_json=json.dumps(team_b, ensure_ascii=False),
        selected_map=selected_map,
        captain_a_id=captain_a["discord_id"],
        captain_b_id=captain_b["discord_id"],
        is_golden=is_golden, is_lightning=is_lightning,
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
    if is_golden:
        mentions += "\n\n🌟 **QIZIL MATÇ!** Bu matçda ELO və Coin dəyişimi 2x-dir!"
    if is_lightning:
        mentions += "\n\n⚡ **İldırım Turu davam edir!** Bu matçda ELO və Coin əlavə 2x-dir!"
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

    if guild:
        for p in team_a:
            asyncio.create_task(_send_intel_briefing(guild, p["discord_id"], p["nick"], team_b, selected_map))
        for p in team_b:
            asyncio.create_task(_send_intel_briefing(guild, p["discord_id"], p["nick"], team_a, selected_map))

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


class MatchmakingView(discord.ui.View):
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

        if queue_size() >= 4:
            await interaction.response.send_message(
                "⏳ Sıra doludur (4/4). Zəhmət olmasa gözləyin, yer boşalan kimi qoşula bilərsiniz.",
                ephemeral=True
            )
            return

        discord_id, nick, so2_id, elo, wins, losses = player[:6]

        comeback_bonus = check_and_grant_comeback_bonus(discord_id)

        added = add_to_queue(discord_id, nick, elo)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()
        active_count = count_active_matches(mode="2v2")
        comeback_line = f"\n🎉 **Geri dönüş bonusu: +{comeback_bonus} coin!** Yenidən görməyə şadıq!" if comeback_bonus else ""
        if active_count >= MAX_PARALLEL_MATCHES:
            await interaction.response.send_message(
                f"✅ {nick} sıraya qoşuldu! ({size}/4)\n"
                f"⏳ Hazırda {active_count}/{MAX_PARALLEL_MATCHES} matç paralel davam edir — "
                f"yer boşalan kimi növbəti matç avtomatik başlayacaq.{comeback_line}",
                ephemeral=True
            )
            await update_queue_status_message()
            return

        await interaction.response.send_message(f"✅ {nick} sıraya qoşuldu! ({size}/4){comeback_line}", ephemeral=True)
        await update_queue_status_message()

        # İsınma Otağı — artıq səsdə olan oyunçular sıraya qoşulanda ortaq gözləmə
        # kanalına köçürülür ki, matç tapılanda komanda kanalına köçmək təbii olsun.
        if interaction.guild:
            member = interaction.guild.get_member(discord_id)
            if member and member.voice and member.voice.channel:
                warmup = await _get_or_create_warmup_channel(interaction.guild)
                if warmup and member.voice.channel.id != warmup.id:
                    try:
                        await member.move_to(warmup)
                    except discord.Forbidden:
                        pass

        await _start_match_if_ready(interaction.channel, interaction.guild)

    @discord.ui.button(label="2v2", style=discord.ButtonStyle.danger, emoji="🔥", custom_id="mm_join")
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._do_join_queue(interaction)

    @discord.ui.button(label="Sıradan çıx", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="mm_leave")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = remove_from_queue(interaction.user.id)
        if removed:
            await interaction.response.send_message("✅ Sıradan çıxdınız.", ephemeral=True)
            await update_queue_status_message()
        else:
            await interaction.response.send_message("⚠️ Siz sırada deyilsiniz.", ephemeral=True)

    @discord.ui.button(label="Queue-dən hamını çıxart - Admins Only", style=discord.ButtonStyle.danger, emoji="🧹", custom_id="mm_clear")
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        clear_queue()
        await interaction.response.send_message("🧹 Sıra tam təmizləndi.", ephemeral=True)
        await update_queue_status_message()


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
    global LOG_CHANNEL_ID, REWARD_CHANNEL_ID, HALL_OF_FAME_CHANNEL_ID, REPORTS_CHANNEL_ID, AUDIT_LOG_CHANNEL_ID
    global ACHIEVEMENT_WALL_CHANNEL_ID, BOSS_EVENT_CHANNEL_ID, MAP_MASTERS_CHANNEL_ID, STANDOFF2_NEWS_CHANNEL_ID
    global LOG_CHANNEL_ID_5V5, leaderboard_channel_id_5v5, leaderboard_message_id_5v5
    global leaderboard_channel_id, leaderboard_message_id
    global tournament_signup_channel_id, tournament_bracket_channel_id
    global CHAT_XP_CHANNEL_ID, chat_activity_channel_id, chat_activity_message_id
    init_db()

    if not get_meta("season_correction_2026_09_01"):
        try:
            for _m, _prefix in (("2v2", "leaderboard-sezon-"), ("5v5", "leaderboard-5v5-sezon-")):
                new_id = collapse_erroneous_season_rotations(_m)
                if new_id is None:
                    continue
                for guild in bot.guilds:
                    for ch in guild.text_channels:
                        if ch.name.startswith(_prefix):
                            try:
                                await ch.edit(name=f"{_prefix}2")
                            except discord.Forbidden:
                                pass
                print(f"[SEASON-FIX] {_m}: yanlış təkrarlanan sezonlar silindi, season_number=2 (id={new_id}) aktiv edildi")
            revoked = revoke_skin_grants(SEASON_CHAMPION_SKIN["name"])
            if revoked:
                print(f"[SEASON-FIX] Bagli rotasiya zamanı yanlışlıqla verilmiş {revoked}x '{SEASON_CHAMPION_SKIN['name']}' skini geri alındı")
        except Exception as e:
            print(f"[SEASON-FIX] Xəta: {e}")
        set_meta("season_correction_2026_09_01", "1")

    saved_log = get_meta("log_channel_id")
    if saved_log:
        LOG_CHANNEL_ID = int(saved_log)
    saved_log_5v5 = get_meta("log_channel_id_5v5")
    if saved_log_5v5:
        LOG_CHANNEL_ID_5V5 = int(saved_log_5v5)
    saved_lb = get_meta("leaderboard_channel_id")
    if saved_lb:
        leaderboard_channel_id = int(saved_lb)
    saved_lb_msg = get_meta("leaderboard_message_id")
    if saved_lb_msg:
        leaderboard_message_id = int(saved_lb_msg)
    saved_lb_5v5 = get_meta("leaderboard_channel_id_5v5")
    if saved_lb_5v5:
        leaderboard_channel_id_5v5 = int(saved_lb_5v5)
    saved_lb_msg_5v5 = get_meta("leaderboard_message_id_5v5")
    if saved_lb_msg_5v5:
        leaderboard_message_id_5v5 = int(saved_lb_msg_5v5)
    saved_tourn_signup = get_meta("tournament_signup_channel_id")
    if saved_tourn_signup:
        tournament_signup_channel_id = int(saved_tourn_signup)
    saved_tourn_bracket = get_meta("tournament_bracket_channel_id")
    if saved_tourn_bracket:
        tournament_bracket_channel_id = int(saved_tourn_bracket)
    saved_chat_xp = get_meta("chat_xp_channel_id")
    if saved_chat_xp:
        CHAT_XP_CHANNEL_ID = int(saved_chat_xp)
    saved_chat_lb = get_meta("chat_activity_channel_id")
    if saved_chat_lb:
        chat_activity_channel_id = int(saved_chat_lb)
    saved_chat_lb_msg = get_meta("chat_activity_message_id")
    if saved_chat_lb_msg:
        chat_activity_message_id = int(saved_chat_lb_msg)
    saved_reward = get_meta("reward_channel_id")
    if saved_reward:
        REWARD_CHANNEL_ID = int(saved_reward)
    saved_hof = get_meta("hall_of_fame_channel_id")
    if saved_hof:
        HALL_OF_FAME_CHANNEL_ID = int(saved_hof)
    saved_reports = get_meta("reports_channel_id")
    if saved_reports:
        REPORTS_CHANNEL_ID = int(saved_reports)
    saved_audit = get_meta("audit_log_channel_id")
    if saved_audit:
        AUDIT_LOG_CHANNEL_ID = int(saved_audit)
    saved_wall = get_meta("achievement_wall_channel_id")
    if saved_wall:
        ACHIEVEMENT_WALL_CHANNEL_ID = int(saved_wall)
    saved_boss = get_meta("boss_event_channel_id")
    if saved_boss:
        BOSS_EVENT_CHANNEL_ID = int(saved_boss)
    saved_masters = get_meta("map_masters_channel_id")
    if saved_masters:
        MAP_MASTERS_CHANNEL_ID = int(saved_masters)
    saved_news = get_meta("standoff2_news_channel_id")
    if saved_news:
        STANDOFF2_NEWS_CHANNEL_ID = int(saved_news)
    print(f"[CONFIG] LOG_CHANNEL_ID={LOG_CHANNEL_ID} REWARD_CHANNEL_ID={REWARD_CHANNEL_ID} "
          f"HALL_OF_FAME_CHANNEL_ID={HALL_OF_FAME_CHANNEL_ID} REPORTS_CHANNEL_ID={REPORTS_CHANNEL_ID} "
          f"AUDIT_LOG_CHANNEL_ID={AUDIT_LOG_CHANNEL_ID} ACHIEVEMENT_WALL_CHANNEL_ID={ACHIEVEMENT_WALL_CHANNEL_ID} "
          f"BOSS_EVENT_CHANNEL_ID={BOSS_EVENT_CHANNEL_ID} MAP_MASTERS_CHANNEL_ID={MAP_MASTERS_CHANNEL_ID} "
          f"STANDOFF2_NEWS_CHANNEL_ID={STANDOFF2_NEWS_CHANNEL_ID}", flush=True)

    if os.environ.get("RESET_SQUADS_ON_BOOT") == "1":
        n = wipe_squads()
        print(f"[RESET_SQUADS] {n} squad/dəvət sətri silindi.", flush=True)

    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView())
    bot.add_view(MatchmakingView5v5())
    bot.add_view(RegisterView())
    bot.add_view(TeamReadyView())
    bot.add_view(TeamReadyView5v5())
    bot.add_view(SquadInviteView())
    for aid in get_open_auction_ids():
        bot.add_view(AuctionBidView(aid))
    active_tournament = get_active_tournament()
    if active_tournament and active_tournament["status"] == "signup":
        bot.add_view(TournamentSignupView(active_tournament["id"]))
    for open_match_id in get_open_tournament_matches():
        bot.add_view(TournamentMatchView(open_match_id))
    if not check_giveaways.is_running():
        check_giveaways.start()
    refresh_daily_tasks()
    if not refresh_tasks_loop.is_running():
        refresh_tasks_loop.start()
    if not check_stuck_matches.is_running():
        check_stuck_matches.start()
    if not daily_report_loop.is_running():
        daily_report_loop.start()
    if not rotate_status_loop.is_running():
        rotate_status_loop.start()
    if not social_reminder_loop.is_running():
        social_reminder_loop.start()
    if not lightning_round_loop.is_running():
        lightning_round_loop.start()
    if not weekly_mvp_loop.is_running():
        weekly_mvp_loop.start()
    if not season_rotation_loop.is_running():
        season_rotation_loop.start()
    if not refresh_chat_activity_leaderboard.is_running():
        refresh_chat_activity_leaderboard.start()
    if not weekly_chat_activity_loop.is_running():
        weekly_chat_activity_loop.start()
    if not refresh_leaderboard.is_running():
        refresh_leaderboard.start()
    if not refresh_leaderboard_5v5.is_running():
        refresh_leaderboard_5v5.start()
    if not anniversary_check_loop.is_running():
        anniversary_check_loop.start()
    if not flash_sale_loop.is_running():
        flash_sale_loop.start()
    if not suspicious_activity_loop.is_running():
        suspicious_activity_loop.start()
    if not weekly_summary_dm_loop.is_running():
        weekly_summary_dm_loop.start()
    if not check_auctions.is_running():
        check_auctions.start()
    if not standoff2_news_loop.is_running():
        standoff2_news_loop.start()
    if REWARD_CHANNEL_ID and not refresh_reward_card.is_running():
        refresh_reward_card.start()
    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"[SYNC] {guild.name} üçün komandalar dərhal sinxronlaşdı.", flush=True)

    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("[SYNC] Qlobal komandalar təmizləndi (dublikatların qarşısı alındı).", flush=True)


@bot.event
async def on_member_join(member: discord.Member):
    view = OnboardingTourView(member.name, member.guild.name)
    try:
        await member.send(embed=view._embed(), view=view)
    except discord.Forbidden:
        pass


ONBOARDING_STEPS = [
    {
        "title": "👋 Xoş gəldin!",
        "description": "**{guild}** — Standoff 2 FACEIT 2v2 icması!\n\nBu qısa tur botun əsas funksiyalarını 3 addımda tanıdacaq — \"Növbəti →\" düyməsinə basaraq davam et."
    },
    {
        "title": "1️⃣ Qeydiyyat",
        "description": "Qeydiyyat kanalındakı **Qeydiyyat** düyməsini bas (ya da `/register` yaz) — Standoff 2 ID-ni hesabına əlaqələndir."
    },
    {
        "title": "2️⃣ Matchmaking",
        "description": "Matchmaking kanalında **Sıraya qoşul** düyməsi ilə 2v2 sıraya yaz — 4 nəfər tamamlanan kimi matç avtomatik başlayır."
    },
    {
        "title": "3️⃣ Profilin",
        "description": "`/profile` ilə profilini, ELO-nu, statistikanı və inventarını izlə. Sual üçün rəhbərliklə əlaqə saxlaya bilərsən. Uğurlar! 🎮"
    },
]


class OnboardingTourView(discord.ui.View):
    """Yeni üzv qoşulanda DM-ə göndərilən addım-addım tanışlıq turu."""
    def __init__(self, member_name, guild_name):
        super().__init__(timeout=600)
        self.step = 0
        self.member_name = member_name
        self.guild_name = guild_name
        self._update_button_label()

    def _update_button_label(self):
        self.next_btn.label = "Bitir ✅" if self.step == len(ONBOARDING_STEPS) - 1 else "Növbəti →"

    def _embed(self):
        s = ONBOARDING_STEPS[self.step]
        embed = discord.Embed(
            title=s["title"],
            description=s["description"].format(name=self.member_name, guild=self.guild_name),
            color=discord.Color.from_rgb(138, 92, 230)
        )
        embed.set_footer(text=f"Nextlevelaz · Addım {self.step + 1}/{len(ONBOARDING_STEPS)}")
        return embed

    @discord.ui.button(label="Növbəti →", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.step < len(ONBOARDING_STEPS) - 1:
            self.step += 1
            self._update_button_label()
            await interaction.response.edit_message(embed=self._embed(), view=self)
        else:
            button.disabled = True
            await interaction.response.edit_message(embed=self._embed(), view=self)


# discord_id -> unix timestamp botların səs kanalına qoşulduğu an. Bu, YALNIZ canlı, cari
# sessiyanın müvəqqəti vəziyyətidir (yaddaşda saxlanılır) — bot restart olsa açıq sessiyaların
# vaxtı itir (aşağı-risk, məqbul tradeoff), amma DB-yə yazılan `total_seconds` HƏMİŞƏ
# toplanaraq qalır (bax: add_voice_seconds).
_voice_session_start = {}


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    now = int(datetime.datetime.utcnow().timestamp())
    was_in_voice = before.channel is not None
    is_in_voice = after.channel is not None
    if not was_in_voice and is_in_voice:
        _voice_session_start[member.id] = now
    elif was_in_voice and not is_in_voice:
        start = _voice_session_start.pop(member.id, None)
        if start:
            add_voice_seconds(member.id, now - start)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    if CHAT_XP_CHANNEL_ID and message.channel.id == CHAT_XP_CHANNEL_ID:
        add_chat_xp(message.author.id)
    # Bu bot yalnız slash (app_commands) komandaları istifadə edir, prefiks-komanda
    # emalı (process_commands) lazım deyil — ona görə burada əlavə çağırış edilmir.


class ConvertCoinsView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="Hamısını çevir", style=discord.ButtonStyle.success, emoji="💱")
    async def convert_all_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return
        balance = get_coins(self.discord_id)
        blocks = balance // COIN_TO_AZN_RATE
        if blocks <= 0:
            await interaction.response.send_message("❌ Çevirmək üçün kifayət qədər coin yoxdur.", ephemeral=True)
            return
        coin_amount = blocks * COIN_TO_AZN_RATE
        azn_amount = blocks * COIN_TO_AZN_VALUE
        spend_coins(self.discord_id, coin_amount)
        add_zm(self.discord_id, azn_amount)
        new_bal = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -coin_amount, f"Coin → AZN çevrilməsi ({azn_amount} AZN)", "spend", new_bal)
        await interaction.response.edit_message(
            content=f"✅ **{coin_amount} coin → {azn_amount:.2f} AZN** çevrildi! Yeni coin balansı: **{new_bal}**.",
            embed=None, view=None
        )


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
            ("btn.record", "🥇", self.record_btn),
            ("btn.maps", "🗺️", self.maps_btn),
            ("btn.heatmap", "🔥", self.heatmap_btn),
            ("btn.synergy", "🔍", self.synergy_btn),
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
        achievements = get_player_achievements(self.discord_id)
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

    async def record_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_record(interaction, self.discord_id, self._display_name(interaction))

    async def maps_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_maps(interaction, self.discord_id, self._display_name(interaction))

    async def heatmap_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        counts = get_activity_heatmap(self.discord_id)
        max_c = max(counts) or 1
        lines = []
        for name, c in zip(WEEKDAY_NAMES_AZ, counts):
            bar = "█" * round((c / max_c) * 15) or "▏"
            lines.append(f"{name:<16} {bar} {c}")
        embed = discord.Embed(
            title=f"🔥 {self._display_name(interaction)} — Fəallıq Xəritəsi (son 90 gün)",
            description="```\n" + "\n".join(lines) + "\n```",
            color=discord.Color.from_rgb(255, 120, 40)
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def synergy_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_synergy(interaction, self.discord_id, self._display_name(interaction))

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


class InventoryMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.inventory", "🎒", self.inventory_btn),
            ("btn.market", "🛒", self.market_btn),
            ("btn.convert", "💱", self.convert_btn),
        ])

    async def inventory_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_inventory(interaction, self.discord_id)

    async def market_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_market(interaction, self.discord_id)


    async def convert_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        balance = get_coins(self.discord_id)
        max_blocks = balance // COIN_TO_AZN_RATE
        embed = discord.Embed(
            title="💱 Coin → AZN Çevirmə",
            description=(
                f"Məzənnə: **{COIN_TO_AZN_RATE} coin = {COIN_TO_AZN_VALUE} AZN**\n"
                f"Balansınız: **{balance} coin**\n\n"
                + (f"Maksimum çevirə bilərsiniz: **{max_blocks * COIN_TO_AZN_RATE} coin → {max_blocks * COIN_TO_AZN_VALUE:.2f} AZN**"
                   if max_blocks > 0 else f"Çevirmək üçün ən azı {COIN_TO_AZN_RATE} coin lazımdır.")
            ),
            color=discord.Color.from_rgb(80, 200, 160)
        )
        view = ConvertCoinsView(self.discord_id) if max_blocks > 0 else discord.utils.MISSING
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class RewardsMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.coins", "💰", self.coins_btn),
            ("btn.daily", "📅", self.gunluk_btn),
            ("btn.daily_bonus", "🎁", self.daily_bonus_btn),
            ("btn.career", "🛤️", self.career_btn),
        ])

    async def coins_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_coins(interaction, self.discord_id)

    async def gunluk_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_gunluk(interaction, self.discord_id)

    async def daily_bonus_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        coins_earned, streak, _ = check_daily_login(self.discord_id)
        if coins_earned <= 0:
            embed = discord.Embed(
                title="🎁 Gündəlik Bonus",
                description=f"Bugünkü bonusu artıq aldınız — sabah yenidən gəlin!\n🔥 Davamlı seriya: **{streak} gün**",
                color=discord.Color.greyple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        new_bal = add_coins(self.discord_id, coins_earned)
        add_coin_log(self.discord_id, coins_earned, f"Gündəlik bonus (seriya {streak})", "earn", new_bal)
        embed = discord.Embed(
            title="🎁 Gündəlik Bonus alındı!",
            description=(
                f"**+{coins_earned} coin**\n"
                f"🔥 Davamlı seriya: **{streak} gün**\n\n"
                "Seriya nə qədər uzun olsa, bonus bir o qədər böyükdür: "
                "3 gün → 15, 7 gün → 25, 14 gün → 35, 30 gün → 50 coin.\n"
                "Bir gün buraxsanız seriya sıfırlanır — hər gün gəlin! ⚡"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Yeni balans: {new_bal} coin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        rating_summary = get_teammate_rating_summary(self.discord_id)
        rating_value = (f"{'⭐' * round(rating_summary['avg_rating'])} {rating_summary['avg_rating']}/5 "
                        f"({rating_summary['rating_count']} rəy)") if rating_summary["avg_rating"] else "Hələ rəy yoxdur"
        embed.add_field(name="🤝 İşbirliyi reytinqi", value=rating_value, inline=True)
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


class TeammateRatingView(discord.ui.View):
    """Matçdan sonra DM-ə göndərilən 1-5 ulduzlu komanda yoldaşı qiymətləndirməsi —
    2v2 formatında hər oyunçunun cəmi 1 komanda yoldaşı olduğu üçün UI sadələşir."""
    def __init__(self, rater_id, rated_id, rated_nick, match_number):
        super().__init__(timeout=3600)
        self.rater_id = rater_id
        self.rated_id = rated_id
        self.rated_nick = rated_nick
        self.match_number = match_number

    async def _rate(self, interaction: discord.Interaction, stars: int):
        if interaction.user.id != self.rater_id:
            await interaction.response.send_message("❌ Bu qiymətləndirmə sizin üçün deyil.", ephemeral=True)
            return
        if not add_teammate_rating(self.rater_id, self.rated_id, self.match_number, stars):
            await interaction.response.send_message("⚠️ Bu matç üçün artıq qiymətləndirmisiniz.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"✅ **{self.rated_nick}** — {'⭐' * stars} qiymətləndirildi. Təşəkkürlər!", view=self
        )

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.secondary)
    async def s1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rate(interaction, 1)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.secondary)
    async def s2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rate(interaction, 2)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def s3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rate(interaction, 3)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def s4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rate(interaction, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def s5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rate(interaction, 5)


async def _send_teammate_rating_prompts(guild, team, match_number):
    """Komandadakı hər oyunçuya QALAN bütün komanda yoldaşlarını qiymətləndirmək üçün DM
    göndərir — 2v2-də hər oyunçunun 1, 5v5-də 4 yoldaşı olur, hər biri üçün ayrıca DM."""
    if not guild or len(team) < 2:
        return
    for rater in team:
        member = guild.get_member(rater["discord_id"])
        if not member:
            continue
        for rated in team:
            if rated["discord_id"] == rater["discord_id"]:
                continue
            view = TeammateRatingView(rater["discord_id"], rated["discord_id"], rated["nick"], match_number)
            try:
                await member.send(
                    f"🤝 Matç No{match_number} bitdi! Komanda yoldaşınız **{rated['nick']}** ilə "
                    "əməkdaşlığınızı necə qiymətləndirərdiniz?",
                    view=view
                )
            except discord.Forbidden:
                break


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


class SocialMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.achievements", "🏆", self.achievements_btn),
            ("btn.title", "🏅", self.title_btn),
            ("btn.quests", "🧗", self.quests_btn),
            ("btn.squad", "🤝", self.squad_btn),
            ("btn.social", "🎙️", self.social_btn),
            ("btn.share", "🔗", self.share_btn),
        ])

    async def achievements_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_achievements(interaction, self.discord_id, self._display_name(interaction))

    async def title_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_titles(interaction, self.discord_id, self._display_name(interaction))

    async def quests_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_quests(interaction, self.discord_id, self._display_name(interaction))

    async def squad_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_squad(interaction, self.discord_id, self._display_name(interaction))

    async def social_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        lb = get_voice_leaderboard(limit=10)
        if not lb:
            await interaction.response.send_message("ℹ️ Hələ heç kim səs kanalında vaxt keçirməyib.", ephemeral=True)
            return

        def _fmt_time(seconds):
            h, rem = divmod(seconds, 3600)
            m, _ = divmod(rem, 60)
            return f"{h}s {m}dəq" if h else f"{m}dəq"

        lines = [f"{i+1}. **{p['nick']}** — {_fmt_time(p['total_seconds'])}" for i, p in enumerate(lb)]
        embed = discord.Embed(
            title="🎙️ Ən Sosial Oyunçular",
            description="Səs kanallarında ən çox vaxt keçirən oyunçular:\n\n" + "\n".join(lines),
            color=discord.Color.from_rgb(80, 200, 160)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def share_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        link = f"{PUBLIC_WEB_URL}/u/{self.discord_id}"
        await interaction.response.send_message(
            f"🔗 İctimai profil linkiniz:\n{link}", ephemeral=True
        )


class NicknameModal(discord.ui.Modal, title="Ad Dəyiş"):
    yeni_ad = discord.ui.TextInput(label="Yeni Standoff 2 nickiniz", placeholder="məs: NextlevelazPro", max_length=32, min_length=2)

    def __init__(self, discord_id):
        super().__init__()
        self.discord_id = discord_id

    async def on_submit(self, interaction: discord.Interaction):
        new_nick = self.yeni_ad.value.strip()
        if not new_nick:
            await interaction.response.send_message("❌ Ad boş ola bilməz.", ephemeral=True)
            return
        ok, msg = use_free_nickname_change(self.discord_id, new_nick)
        if not ok:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"✅ Adınız **{new_nick}** olaraq dəyişdirildi! (pulsuz haqqınız istifadə edildi, bu bir dəfəlik idi)",
            ephemeral=True
        )


class SettingsMenuView(_ProfileSubMenuBase):
    def __init__(self, discord_id, lang="az"):
        super().__init__(discord_id, lang)
        self._add_buttons([
            ("btn.notifications", "🔔", self.notifications_btn),
            ("btn.lang", "🌐", self.lang_btn),
            ("btn.nickname", "✏️", self.nickname_btn),
            ("btn.more", "⚙️", self.more_btn),
        ])

    async def notifications_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        enabled = get_dm_notifications(self.discord_id)
        set_dm_notifications(self.discord_id, not enabled)
        new_state = "AÇIQ ✅" if not enabled else "BAĞLI ❌"
        await interaction.response.send_message(
            f"🔔 Şəxsi mesaj (DM) bildirişləri indi: **{new_state}**\n"
            "(həftəlik xülasə və digər fərdi bildirişlərə aiddir)",
            ephemeral=True
        )

    async def lang_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            t("lang.select_placeholder", self.lang), view=LanguageSelectView(self.discord_id), ephemeral=True
        )

    async def nickname_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(NicknameModal(self.discord_id))

    async def more_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        embed = discord.Embed(
            title="⚙️ Digər Əməliyyatlar",
            description="🎁 Bir oyunçuya coin hədiyyə edin\n🚩 Bir oyunçunu admin komandasına şikayət edin",
            color=discord.Color.from_rgb(138, 92, 230)
        )
        await interaction.response.send_message(embed=embed, view=MoreOptionsView(self.discord_id), ephemeral=True)


class ProfileHubView(discord.ui.View):
    """Əsas profil menyusu — 5 kateqoriya düyməsi, hər biri öz alt-menyusunu ayrıca
    ephemeral mesaj kimi açır (bax: _ProfileSubMenuBase). Bu, Discord-un tək mesajdakı
    komponentlər üçün QOYDUĞU 25 limitini kateqoriyalar arasında bölərək gələcək
    genişlənməyə yer saxlayır — əvvəlki tək-səviyyəli dizaynda bütün 25 slot dolu idi."""
    def __init__(self, discord_id, lang="az"):
        super().__init__(timeout=300)
        self.discord_id = discord_id
        self.lang = lang

        category_defs = [
            ("btn.menu_stats", "📊", StatsMenuView, "Stats, tarixçə, qrafik, rekord, xəritələr, fəallıq, sinergiya, AI Koç"),
            ("btn.menu_inventory", "🎒", InventoryMenuView, "İnventar, market, Coin→AZN çevirmə"),
            ("btn.menu_rewards", "💰", RewardsMenuView, "Coin balansı, gündəlik giriş, gündəlik bonus, karyera yolu"),
            ("btn.menu_social", "🏆", SocialMenuView, "Nailiyyətlər, ləqəblər, questlər, squad, sosial reytinq, paylaşım"),
            ("btn.menu_settings", "⚙️", SettingsMenuView, "Bildirişlər, dil, ad dəyişmə, hədiyyə/şikayət"),
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

    banner_path = None
    active_banner_id = get_active_banner(discord_id)
    if active_banner_id:
        banner_item = get_item_by_id(active_banner_id)
        if banner_item and banner_item.get("file"):
            p = os.path.join("banners", banner_item["file"])
            if os.path.exists(p):
                banner_path = p

    frame_path = None
    active_frame_id = get_active_frame(discord_id)
    if active_frame_id:
        frame_item = get_item_by_id(active_frame_id)
        if frame_item and frame_item.get("file"):
            p = os.path.join("frames", frame_item["file"])
            if os.path.exists(p):
                frame_path = p

    theme_colors = None
    active_theme_id = get_active_theme(discord_id)
    if active_theme_id:
        theme_item = get_item_by_id(active_theme_id)
        if theme_item:
            theme_colors = theme_item.get("colors")

    player_lang = get_lang(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"profile_{discord_id}.png")
    await asyncio.to_thread(
        generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path,
        banner_path=banner_path, coins=stats.get("coins", 0), frame_path=frame_path,
        zm_balance=stats.get("zm_balance", 0),
        kills=stats.get("kills", 0), assists=stats.get("assists", 0), deaths=stats.get("deaths", 0),
        theme_colors=theme_colors, title=get_active_title_name(discord_id), lang=player_lang,
    )

    await interaction.followup.send(
        file=discord.File(card_path, filename="profile.png"),
        view=ProfileHubView(discord_id, lang=player_lang)
    )


@bot.tree.command(name="matchresult", description="[Admin] Matç nəticəsini qeyd edir və ELO-nu yeniləyir")
@app_commands.describe(qalib="Qalib oyunçu", məğlub="Məğlub oyunçu")
@staff_check()
async def matchresult(interaction: discord.Interaction, qalib: discord.Member, məğlub: discord.Member):
    if not get_player(qalib.id) or not get_player(məğlub.id):
        await interaction.response.send_message("❌ Hər iki oyunçu əvvəlcə `/register` etməlidir.", ephemeral=True)
        return

    result = update_elo(qalib.id, məğlub.id)

    embed = discord.Embed(title="🏆 Matç nəticəsi qeyd edildi", color=discord.Color.from_rgb(138, 92, 230))
    embed.add_field(
        name=f"✅ Qalib: {qalib.display_name}",
        value=f"{result['winner_old_elo']} → **{result['winner_new_elo']}** ELO (+{result['winner_new_elo'] - result['winner_old_elo']})",
        inline=False
    )
    embed.add_field(
        name=f"❌ Məğlub: {məğlub.display_name}",
        value=f"{result['loser_old_elo']} → **{result['loser_new_elo']}** ELO ({result['loser_new_elo'] - result['loser_old_elo']})",
        inline=False
    )
    await interaction.response.send_message(embed=embed)


@matchresult.error
async def matchresult_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


RULES_SECTIONS = [
    {
        "title": "Qeydiyyat qaydası",
        "body": "Oynamaq üçün əvvəlcə qeydiyyatdan keçmək lazımdır. Qeydiyyat kanalında Qeydiyyat düyməsinə basıb Standoff 2 ID və oyundakı adınızı yazın.",
        "accent": GREEN_ACCENT,
    },
    {
        "title": "Sıraya qoşulmaq",
        "body": "Matchmaking kanalında 2v2 düyməsinə basaraq sıraya qoşula bilərsiniz. Sıradan çıxmaq üçün Sıradan çıx düyməsindən istifadə edin. Eyni anda birdən çox sıraya qoşulmaq olmaz.",
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


async def _post_leaderboard(channel):
    global leaderboard_channel_id, leaderboard_message_id

    rows = get_leaderboard(20)
    generate_leaderboard_image(rows, LEADERBOARD_IMAGE_PATH)

    link_view = discord.ui.View(timeout=None)
    link_view.add_item(discord.ui.Button(
        label="🌐 Tam Siyahını Gör (Vebsayt)", style=discord.ButtonStyle.link, url=PUBLIC_WEB_URL
    ))

    message = await channel.send(
        content=(
            "🏆 **Nextlevelaz FACEIT Leaderboard** — hər 60 saniyədə avtomatik yenilənir "
            "(bu şəkil Top-20-ni göstərir).\n"
            f"🌐 Bütün oyunçuların tam, axtarışlı siyahısı üçün vebsaytımıza baxın: {PUBLIC_WEB_URL}"
        ),
        file=discord.File(LEADERBOARD_IMAGE_PATH, filename="leaderboard.png"),
        view=link_view
    )

    leaderboard_channel_id = channel.id
    leaderboard_message_id = message.id
    set_meta("leaderboard_channel_id", str(channel.id))
    set_meta("leaderboard_message_id", str(message.id))

    if not refresh_leaderboard.is_running():
        refresh_leaderboard.start()


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


async def _post_matchmaking(channel):
    global queue_status_channel_id, queue_status_message_id

    banner_path = os.path.join(DATA_DIR or ".", "matchmaking_banner.png")
    await asyncio.to_thread(generate_matchmaking_banner, QUEUE_OPEN_HOUR, QUEUE_CLOSE_HOUR, LOGO_PATH, banner_path)
    view = MatchmakingView()
    await channel.send(file=discord.File(banner_path, filename="matchmaking_banner.png"), view=view)

    status_image_path = os.path.join(DATA_DIR or ".", QUEUE_STATUS_IMAGE_PATH)
    await asyncio.to_thread(generate_queue_status_card, [], status_image_path)
    status_message = await channel.send(file=discord.File(status_image_path, filename="queue_status.png"))
    queue_status_channel_id = channel.id
    queue_status_message_id = status_message.id


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


@bot.tree.command(name="setup_leaderboard", description="[Admin] Leaderboard mesajını bu kanalda yaradır və avtomatik yeniləməyə başlayır")
@staff_check()
async def setup_leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_leaderboard(interaction.channel)
    await interaction.followup.send("✅ Leaderboard mesajı yaradıldı, avtomatik yenilənəcək.", ephemeral=True)


@setup_leaderboard.error
async def setup_leaderboard_error(interaction: discord.Interaction, error):
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


@bot.tree.command(name="setup", description="[Admin] Matchmaking mesajını bu kanalda yaradır")
@staff_check()
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_matchmaking(interaction.channel)
    await interaction.followup.send("✅ Matchmaking mesajı yaradıldı.", ephemeral=True)


@setup.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="full_setup", description="[Admin] FACEIT 2v2+5v5 kanallarını silib yenilənmiş, kataqoriyalaşdırılmış formada təzədən qurur")
@staff_check()
async def full_setup(interaction: discord.Interaction):
    global LOG_CHANNEL_ID, REWARD_CHANNEL_ID, HALL_OF_FAME_CHANNEL_ID, REPORTS_CHANNEL_ID, AUDIT_LOG_CHANNEL_ID
    global ACHIEVEMENT_WALL_CHANNEL_ID, BOSS_EVENT_CHANNEL_ID, MAP_MASTERS_CHANNEL_ID, STANDOFF2_NEWS_CHANNEL_ID
    global LOG_CHANNEL_ID_5V5
    global tournament_signup_channel_id, tournament_bracket_channel_id

    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    progress_msg = await interaction.followup.send("⏳ Server qurulur...\n`░░░░░░░░░░░░░░░░░░░░` 0%", ephemeral=True)

    # Üç ayrı kataqoriya: Ümumi (hər iki formata aid), 2v2, 5v5 — kanallar səliqəli
    # şəkildə ayrılsın deyə. Hər kataqoriya öz matchmaking/leaderboard/log üçlüyünə malikdir.
    category_general = discord.utils.get(guild.categories, name=CATEGORY_GENERAL_NAME)
    if category_general is None:
        category_general = await guild.create_category(CATEGORY_GENERAL_NAME)
    category_2v2 = discord.utils.get(guild.categories, name=FULL_SETUP_CATEGORY_NAME)
    if category_2v2 is None:
        category_2v2 = await guild.create_category(FULL_SETUP_CATEGORY_NAME)
    category_5v5 = discord.utils.get(guild.categories, name=CATEGORY_5V5_NAME)
    if category_5v5 is None:
        category_5v5 = await guild.create_category(CATEGORY_5V5_NAME)
    category_tournament = discord.utils.get(guild.categories, name=CATEGORY_TOURNAMENT_NAME)
    if category_tournament is None:
        category_tournament = await guild.create_category(CATEGORY_TOURNAMENT_NAME)
    await _progress_step(progress_msg, 1, 5, "Kataqoriyalar hazırlanır...")

    announce_overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False)
    }
    staff_only_overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    async def _recreate_text(name, category, overwrites=None):
        existing = discord.utils.get(category.text_channels, name=name)
        if existing:
            try:
                await existing.delete(reason="full_setup: yenilənmiş formada yenidən qurulur")
            except discord.Forbidden:
                pass
        return await guild.create_text_channel(name, category=category, overwrites=overwrites or {})

    # ── Ümumi (hər iki formata aid) ────────────────────────────────────────────
    # Ay sonu mükafat kanalı ən üstdə olsun deyə digərlərindən ƏVVƏL yaradılır.
    ch_reward = await _recreate_text("ay-sonu-mukafati", category_general, announce_overwrites)
    ch_register = await _recreate_text("faceit-qeydiyyat", category_general, announce_overwrites)
    ch_rules = await _recreate_text("faceit-qaydalari", category_general, announce_overwrites)
    ch_hof = await _recreate_text("hall-of-fame", category_general, announce_overwrites)
    ch_reports = await _recreate_text("reports", category_general, staff_only_overwrites)
    ch_audit = await _recreate_text("audit-log", category_general, staff_only_overwrites)
    ch_wall = await _recreate_text("nailiyyet-divari", category_general, announce_overwrites)
    ch_boss = await _recreate_text("boss-event", category_general, announce_overwrites)
    ch_masters = await _recreate_text("xerite-ustalari", category_general, announce_overwrites)
    ch_news = await _recreate_text("standoff2-yenilikleri", category_general, announce_overwrites)
    ch_chat_xp = await _recreate_text("umumi-sohbet", category_general)
    ch_chat_lb = await _recreate_text("aktivlik-lovhesi", category_general, announce_overwrites)

    # ── 2v2 ──────────────────────────────────────────────────────────────────
    ch_matchmaking = await _recreate_text("matchmaking", category_2v2, announce_overwrites)
    current_season_2v2 = get_or_create_current_season("2v2")
    ch_leaderboard = await _recreate_text(
        f"leaderboard-sezon-{current_season_2v2['season_number']}", category_2v2, announce_overwrites
    )
    ch_log = await _recreate_text("faceit-log", category_2v2)

    # ── 5v5 ──────────────────────────────────────────────────────────────────
    ch_matchmaking_5v5 = await _recreate_text("matchmaking-5v5", category_5v5, announce_overwrites)
    current_season_5v5 = get_or_create_current_season("5v5")
    ch_leaderboard_5v5 = await _recreate_text(
        f"leaderboard-5v5-sezon-{current_season_5v5['season_number']}", category_5v5, announce_overwrites
    )
    ch_log_5v5 = await _recreate_text("faceit-log-5v5", category_5v5)

    # ── Turnirlər (FACEIT ELO/2v2/5v5-dən müstəqil) ─────────────────────────────
    ch_tournament_signup = await _recreate_text("turnir-qeydiyyat", category_tournament, announce_overwrites)
    ch_tournament_bracket = await _recreate_text("turnir-cetveli", category_tournament, announce_overwrites)
    await _progress_step(progress_msg, 2, 5, "Kanallar yaradılır...")

    # Köhnə statik "Komanda A/B" səs kanalları artıq lazım deyil — hər matç
    # üçün səs kanalları indi avtomatik, dinamik yaradılır/silinir (bax:
    # _start_one_match/_cleanup_match_voice_channels). Əvvəllər bu komanda
    # yaratmış ola biləcəyi köhnə statik kanallar varsa təmizlənir.
    for stale_name in ("🔵 Komanda A", "🔴 Komanda B"):
        stale = discord.utils.get(category_2v2.voice_channels, name=stale_name)
        if stale:
            try:
                await stale.delete(reason="full_setup: statik komanda kanalları artıq istifadə olunmur")
            except discord.Forbidden:
                pass

    await _get_or_create_warmup_channel(guild, mode="2v2")
    await _get_or_create_warmup_channel(guild, mode="5v5")

    LOG_CHANNEL_ID = ch_log.id
    set_meta("log_channel_id", ch_log.id)
    LOG_CHANNEL_ID_5V5 = ch_log_5v5.id
    set_meta("log_channel_id_5v5", ch_log_5v5.id)
    REWARD_CHANNEL_ID = ch_reward.id
    set_meta("reward_channel_id", ch_reward.id)
    HALL_OF_FAME_CHANNEL_ID = ch_hof.id
    set_meta("hall_of_fame_channel_id", ch_hof.id)
    REPORTS_CHANNEL_ID = ch_reports.id
    set_meta("reports_channel_id", ch_reports.id)
    AUDIT_LOG_CHANNEL_ID = ch_audit.id
    set_meta("audit_log_channel_id", ch_audit.id)
    ACHIEVEMENT_WALL_CHANNEL_ID = ch_wall.id
    set_meta("achievement_wall_channel_id", ch_wall.id)
    BOSS_EVENT_CHANNEL_ID = ch_boss.id
    set_meta("boss_event_channel_id", ch_boss.id)
    MAP_MASTERS_CHANNEL_ID = ch_masters.id
    set_meta("map_masters_channel_id", ch_masters.id)
    STANDOFF2_NEWS_CHANNEL_ID = ch_news.id
    set_meta("standoff2_news_channel_id", ch_news.id)
    tournament_signup_channel_id = ch_tournament_signup.id
    set_meta("tournament_signup_channel_id", ch_tournament_signup.id)
    tournament_bracket_channel_id = ch_tournament_bracket.id
    set_meta("tournament_bracket_channel_id", ch_tournament_bracket.id)
    global CHAT_XP_CHANNEL_ID, chat_activity_channel_id, chat_activity_message_id
    CHAT_XP_CHANNEL_ID = ch_chat_xp.id
    set_meta("chat_xp_channel_id", ch_chat_xp.id)
    chat_activity_channel_id = ch_chat_lb.id
    set_meta("chat_activity_channel_id", ch_chat_lb.id)
    await _progress_step(progress_msg, 3, 5, "İcazələr və köhnə kanallar təmizlənir...")

    await _post_register(ch_register)
    await _post_matchmaking(ch_matchmaking)
    await _post_matchmaking_5v5(ch_matchmaking_5v5)
    await _post_rules(ch_rules)
    await _post_leaderboard(ch_leaderboard)
    await _post_leaderboard_5v5(ch_leaderboard_5v5)
    await _post_monthly_reward_card(ch_reward)
    await ch_hof.send(
        "🏆 **Həftənin MVP-si** buraya elan olunacaq — hər həftə Bazar ertəsi, "
        "keçən 7 gündə ən çox qələbə qazanan oyunçu seçilib pinlənmiş kartla təbrik ediləcək."
    )
    await ch_wall.send(
        "🏅 **Nailiyyət Divarı** — nadir nailiyyət/ləqəb qazanan oyunçular avtomatik burada elan olunacaq."
    )
    await _post_boss_event(ch_boss)
    await ch_masters.send(
        "🗺️ **Xəritə Ustaları** — hər xəritənin ən yüksək win-rate-li top-3 oyunçusu bu siyahıda hər həftə yenilənəcək."
    )
    await ch_news.send(
        "🎮 **Standoff 2 Rəsmi Yenilikləri** — help.standoff2.com saytındakı yeni yenilik (patch notes) "
        "məqalələri aşkarlanan kimi bura Azərbaycan dilinə tərcümə edilib avtomatik göndəriləcək "
        "(hər 6 saatdan bir yoxlanılır)."
    )
    await ch_tournament_signup.send(
        "🏆 **Turnirlər** — FACEIT ELO/2v2/5v5 sistemindən TAM MÜSTƏQİL, ayrı bracket turnirlər "
        "burada elan olunacaq. Admin `/turnir_yarat` ilə yeni turnir başladanda qeydiyyat kartı "
        "bura göndəriləcək — qoşulmaq üçün FACEIT-də qeydiyyatdan keçmiş olmaq kifayətdir."
    )
    await ch_tournament_bracket.send(
        "🗂️ **Turnir Cədvəli** — aktiv turnirin canlı bracket şəkli və hər matçın nəticə düymələri "
        "burada göstəriləcək."
    )
    await ch_chat_xp.send(
        "💬 **Ümumi Söhbət** — burada yazdığın hər mesaja görə XP qazanırsan! "
        f"Hər Bazar günü saat 23:59 həftənin ən aktivi elan olunacaq. Lövhə: {ch_chat_lb.mention}"
    )
    await _post_chat_activity_leaderboard(ch_chat_lb)
    await _progress_step(progress_msg, 4, 5, "Tanıtım mesajları göndərilir...")
    await _progress_step(progress_msg, 5, 5, "Tamamlandı!")

    await interaction.followup.send(
        "✅ Server yenidən quruldu! Kanallar 4 kataqoriyaya bölünüb: **📌 Ümumi**, **🏆 FACEIT 2v2**, "
        "**🎯 FACEIT 5v5**, **🏆 Turnirlər**.\n\n"
        f"**📌 Ümumi**\n"
        f"🔪 Ay sonu mükafatı: {ch_reward.mention}\n"
        f"📋 Qeydiyyat: {ch_register.mention}\n"
        f"📜 Qaydalar: {ch_rules.mention}\n"
        f"🏆 Hall of Fame: {ch_hof.mention}\n"
        f"🚩 Reports: {ch_reports.mention} (yalnız adminlər)\n"
        f"🛡️ Audit Log: {ch_audit.mention} (yalnız adminlər)\n"
        f"🏅 Nailiyyət Divarı: {ch_wall.mention}\n"
        f"👹 Boss Event: {ch_boss.mention}\n"
        f"🗺️ Xəritə Ustaları: {ch_masters.mention}\n"
        f"🎮 Standoff 2 Yenilikləri: {ch_news.mention}\n\n"
        f"**🏆 FACEIT 2v2**\n"
        f"🎮 Matchmaking: {ch_matchmaking.mention}\n"
        f"🏆 Leaderboard: {ch_leaderboard.mention}\n"
        f"📰 Faceit log: {ch_log.mention}\n\n"
        f"**🎯 FACEIT 5v5**\n"
        f"🎮 Matchmaking: {ch_matchmaking_5v5.mention}\n"
        f"🏆 Leaderboard: {ch_leaderboard_5v5.mention}\n"
        f"📰 Faceit log: {ch_log_5v5.mention}\n\n"
        f"**🏆 Turnirlər** (FACEIT ELO-dan müstəqil)\n"
        f"📋 Qeydiyyat: {ch_tournament_signup.mention}\n"
        f"🗂️ Cədvəl: {ch_tournament_bracket.mention}\n"
        f"➡️ Yeni turnir üçün: `/turnir_yarat`\n\n"
        f"🔊 Səs kanalları (isınma otağı daxil) hər format üçün öz kataqoriyasında avtomatik yaradılır/silinir.\n\n"
        "Elan kanallarında adi üzvlər yazı yaza bilmir, yalnız düymələrlə əməliyyat edə bilirlər.\n"
        "⚠️ Diqqət: bu komanda hər işə düşdükdə mövcud FACEIT kanallarını silib təzədən qurur "
        "(köhnə mesaj tarixçəsi itir).",
        ephemeral=True
    )


@full_setup.error
async def full_setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


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


class BidModal(discord.ui.Modal, title="Hərraca təklif ver"):
    teklif = discord.ui.TextInput(label="Təklifiniz (coin)", placeholder="məs: 250", max_length=10)

    def __init__(self, auction_id):
        super().__init__()
        self.auction_id = auction_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.teklif.value)
        except ValueError:
            await interaction.response.send_message("❌ Rəqəm daxil edin.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("❌ Təklif müsbət olmalıdır.", ephemeral=True)
            return
        ok, msg = place_bid(self.auction_id, interaction.user.id, amount)
        if not ok:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return
        auction = get_auction(self.auction_id)
        embed = discord.Embed(
            title=f"🔨 HƏRRAC: {auction['item_name']}",
            description=(f"{auction['description'] or ''}\n\n"
                         f"💰 Cari ən yüksək təklif: **{auction['current_bid']} coin** — {interaction.user.mention}\n"
                         f"⏰ Bitmə: <t:{auction['end_unix']}:R>"),
            color=discord.Color.from_rgb(255, 120, 40)
        )
        try:
            channel = bot.get_channel(auction["channel_id"])
            message = await channel.fetch_message(auction["message_id"])
            await message.edit(embed=embed)
        except (discord.NotFound, discord.HTTPException, AttributeError):
            pass
        await interaction.response.send_message(f"✅ Təklifiniz ({amount} coin) qeydə alındı!", ephemeral=True)


class AuctionBidView(discord.ui.View):
    """custom_id auction_id-ni özündə saxlayır ki, hər hərrac üçün AYRI persistent view
    qeydiyyatdan keçsin — bot restart olsa belə, paralel açıq hərraclardan hər birinin
    düyməsi düzgün auction_id-yə yönləndirilsin (bax: on_ready-dəki yenidən-qeydiyyat)."""
    def __init__(self, auction_id):
        super().__init__(timeout=None)
        self.auction_id = auction_id
        btn = discord.ui.Button(label="Təklif ver", style=discord.ButtonStyle.success, emoji="🔨",
                                 custom_id=f"auction_bid_{auction_id}")
        btn.callback = self.bid_btn
        self.add_item(btn)

    async def bid_btn(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BidModal(self.auction_id))


@bot.tree.command(name="admin_herrac_baslat", description="[Admin] Coin ilə hərrac başladır")
@app_commands.describe(
    esya_adi="Hərraca çıxarılan əşyanın adı",
    tesviri="Qısa təsvir",
    baslangic_teklifi="Minimum başlanğıc təklifi (coin)",
    saat="Hərracın neçə saat sürəcəyi",
    elan_kanal="Hərracın elan olunacağı kanal"
)
@staff_check()
async def admin_herrac_baslat(
    interaction: discord.Interaction,
    esya_adi: str,
    tesviri: str,
    baslangic_teklifi: int,
    saat: int,
    elan_kanal: discord.TextChannel
):
    if baslangic_teklifi <= 0 or saat <= 0:
        await interaction.response.send_message("❌ Başlanğıc təklifi və müddət müsbət olmalıdır.", ephemeral=True)
        return
    end_unix = int(datetime.datetime.utcnow().timestamp()) + saat * 3600
    embed = discord.Embed(
        title=f"🔨 HƏRRAC: {esya_adi}",
        description=(f"{tesviri}\n\n💰 Başlanğıc təklifi: **{baslangic_teklifi} coin**\n"
                     f"⏰ Bitmə: <t:{end_unix}:R>\n\nTəklif vermək üçün aşağıdakı düyməni basın!"),
        color=discord.Color.from_rgb(255, 120, 40)
    )
    message = await elan_kanal.send(embed=embed)
    auction_id = create_auction(esya_adi, tesviri, baslangic_teklifi, saat * 3600, elan_kanal.id, message.id, interaction.user.id)
    await message.edit(view=AuctionBidView(auction_id))
    await interaction.response.send_message(f"✅ Hərrac başladı: {elan_kanal.mention}", ephemeral=True)


@admin_herrac_baslat.error
async def admin_herrac_baslat_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TURNIR BRACKET SİSTEMİ (FACEIT ELO/2v2/5v5-dən TAM MÜSTƏQİL)
# ═══════════════════════════════════════════════════════════════════════════════

async def _post_tournament_signup(tournament_id, channel):
    t = get_tournament(tournament_id)
    participants = get_tournament_participants(tournament_id)
    card_path = os.path.join(DATA_DIR or ".", f"tournament_signup_{tournament_id}.png")
    await asyncio.to_thread(generate_tournament_signup_card, t, participants, card_path)
    message = await channel.send(file=discord.File(card_path, filename="signup.png"),
                                  view=TournamentSignupView(tournament_id))
    set_tournament_meta(tournament_id, signup_channel_id=str(channel.id), signup_message_id=str(message.id))
    return message


async def _refresh_tournament_signup_message(tournament_id):
    t = get_tournament(tournament_id)
    if not t or not t.get("signup_channel_id") or not t.get("signup_message_id"):
        return
    channel = bot.get_channel(int(t["signup_channel_id"]))
    if not channel:
        return
    participants = get_tournament_participants(tournament_id)
    card_path = os.path.join(DATA_DIR or ".", f"tournament_signup_{tournament_id}.png")
    await asyncio.to_thread(generate_tournament_signup_card, t, participants, card_path)
    try:
        message = await channel.fetch_message(int(t["signup_message_id"]))
        await message.edit(attachments=[discord.File(card_path, filename="signup.png")])
    except (discord.NotFound, discord.HTTPException):
        pass


async def _post_tournament_match_view(match, channel=None):
    if channel is None:
        channel = bot.get_channel(tournament_bracket_channel_id) if tournament_bracket_channel_id else None
    if not channel:
        return
    a_members = get_tournament_team_members(match["team_a_id"])
    b_members = get_tournament_team_members(match["team_b_id"])
    a_label = " / ".join(m["nick"] for m in a_members) or "?"
    b_label = " / ".join(m["nick"] for m in b_members) or "?"
    embed = discord.Embed(
        title=f"⚔️ Raund {match['round_number']} — Matç",
        description=f"**A:** {a_label}\n**B:** {b_label}\n\nAdmin qalibi elan etsin:",
        color=discord.Color.from_rgb(138, 92, 230)
    )
    message = await channel.send(embed=embed, view=TournamentMatchView(match["id"]))
    set_tournament_match_message(match["id"], channel.id, message.id)


async def _post_tournament_bracket(tournament_id):
    channel = bot.get_channel(tournament_bracket_channel_id) if tournament_bracket_channel_id else None
    if not channel:
        return
    bracket = get_tournament_bracket(tournament_id)
    card_path = os.path.join(DATA_DIR or ".", f"tournament_bracket_{tournament_id}.png")
    await asyncio.to_thread(generate_tournament_bracket_image, bracket, card_path)
    message = await channel.send(file=discord.File(card_path, filename="bracket.png"))
    set_tournament_meta(tournament_id, bracket_channel_id=str(channel.id), bracket_message_id=str(message.id))
    for rnd in bracket["rounds"]:
        for m in rnd:
            if m["status"] != "completed" and m["team_a_id"] and m["team_b_id"]:
                await _post_tournament_match_view(m, channel=channel)


async def _refresh_tournament_bracket_image(tournament_id):
    t = get_tournament(tournament_id)
    if not t or not t.get("bracket_channel_id") or not t.get("bracket_message_id"):
        return
    channel = bot.get_channel(int(t["bracket_channel_id"]))
    if not channel:
        return
    bracket = get_tournament_bracket(tournament_id)
    card_path = os.path.join(DATA_DIR or ".", f"tournament_bracket_{tournament_id}.png")
    await asyncio.to_thread(generate_tournament_bracket_image, bracket, card_path)
    try:
        message = await channel.fetch_message(int(t["bracket_message_id"]))
        await message.edit(attachments=[discord.File(card_path, filename="bracket.png")])
    except (discord.NotFound, discord.HTTPException):
        pass


async def _finish_tournament(tournament_id, winner_team_id, loser_team_id):
    t = get_tournament(tournament_id)
    winners = get_tournament_team_members(winner_team_id)
    prize_winner = t.get("prize_winner") or 0
    prize_runner_up = t.get("prize_runner_up") or 0
    for m in winners:
        if prize_winner > 0:
            new_bal = add_coins(m["discord_id"], prize_winner)
            add_coin_log(m["discord_id"], prize_winner, f"Turnir #{tournament_id} Qalibi", "earn", new_bal)
    if prize_runner_up > 0:
        for m in get_tournament_team_members(loser_team_id):
            new_bal = add_coins(m["discord_id"], prize_runner_up)
            add_coin_log(m["discord_id"], prize_runner_up, f"Turnir #{tournament_id} Finalisti", "earn", new_bal)

    channel = bot.get_channel(tournament_bracket_channel_id) if tournament_bracket_channel_id else None
    if channel:
        winner_label = " / ".join(m["nick"] for m in winners)
        embed = discord.Embed(
            title="🏆 Turnir Qalibi!",
            description=(f"**{t['name']}** turnirinin qalibi: **{winner_label}**"
                         + (f"\n🎁 Mükafat: {prize_winner} coin (hər üzvə)" if prize_winner else "")),
            color=discord.Color.gold()
        )
        await channel.send(content=" ".join(f"<@{m['discord_id']}>" for m in winners), embed=embed)


class TournamentSignupView(discord.ui.View):
    """custom_id tournament_id-ni özündə saxlayır (bax: AuctionBidView) — hər turnir üçün
    ayrı persistent view, bot restart olsa belə funksional qalır (bax: on_ready-dəki
    yenidən-qeydiyyat)."""
    def __init__(self, tournament_id):
        super().__init__(timeout=None)
        self.tournament_id = tournament_id
        join_btn = discord.ui.Button(label="Qatıl", style=discord.ButtonStyle.success, emoji="✅",
                                      custom_id=f"tourn_join_{tournament_id}")
        join_btn.callback = self.join_btn_cb
        leave_btn = discord.ui.Button(label="Ayrıl", style=discord.ButtonStyle.secondary, emoji="🚪",
                                       custom_id=f"tourn_leave_{tournament_id}")
        leave_btn.callback = self.leave_btn_cb
        start_btn = discord.ui.Button(label="Turniri Başlat (Admin)", style=discord.ButtonStyle.danger, emoji="🚀",
                                       custom_id=f"tourn_start_{tournament_id}")
        start_btn.callback = self.start_btn_cb
        self.add_item(join_btn)
        self.add_item(leave_btn)
        self.add_item(start_btn)

    async def join_btn_cb(self, interaction: discord.Interaction):
        t = get_tournament(self.tournament_id)
        if not t or t["status"] != "signup":
            await interaction.response.send_message("❌ Bu turnirə artıq qoşulmaq mümkün deyil.", ephemeral=True)
            return
        player = get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "❌ Əvvəlcə qeydiyyatdan keçməlisiniz. `#faceit-qeydiyyat` kanalına keçin.",
                ephemeral=True
            )
            return
        ok, msg = join_tournament(self.tournament_id, interaction.user.id)
        await interaction.response.send_message(("✅ " if ok else "⚠️ ") + msg, ephemeral=True)
        if ok:
            await _refresh_tournament_signup_message(self.tournament_id)

    async def leave_btn_cb(self, interaction: discord.Interaction):
        ok, msg = leave_tournament(self.tournament_id, interaction.user.id)
        await interaction.response.send_message(("✅ " if ok else "⚠️ ") + msg, ephemeral=True)
        if ok:
            await _refresh_tournament_signup_message(self.tournament_id)

    async def start_btn_cb(self, interaction: discord.Interaction):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        t = get_tournament(self.tournament_id)
        if not t or t["status"] != "signup":
            await interaction.response.send_message("❌ Bu turnir artıq başlayıb.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        result = start_tournament(self.tournament_id)
        if result is None:
            await interaction.followup.send(
                f"❌ Turniri başlatmaq üçün ən azı 2 tam komanda lazımdır (komanda ölçüsü: {t['team_size']}).",
                ephemeral=True
            )
            return
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass
        await _post_tournament_bracket(self.tournament_id)
        await interaction.followup.send(
            f"✅ Turnir başladı! {result['team_count']} komanda, {result['bracket_size']}-lik bracket.",
            ephemeral=True
        )


class TournamentMatchView(discord.ui.View):
    """custom_id match_id-ni saxlayır (bax: AuctionBidView). Hər klikdə DB-dən matçı
    YENİDƏN oxuyur (bax: TeamReadyView-dəki restart-safe idiom) — instansiya vəziyyətinə
    etibar etmir."""
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = match_id
        a_btn = discord.ui.Button(label="A Qalib", style=discord.ButtonStyle.primary,
                                   custom_id=f"tourn_win_a_{match_id}")
        a_btn.callback = self.declare_a
        b_btn = discord.ui.Button(label="B Qalib", style=discord.ButtonStyle.primary,
                                   custom_id=f"tourn_win_b_{match_id}")
        b_btn.callback = self.declare_b
        self.add_item(a_btn)
        self.add_item(b_btn)

    async def _declare(self, interaction: discord.Interaction, side):
        if not is_staff(interaction):
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        match = get_tournament_match(self.match_id)
        if not match or match["status"] == "completed":
            await interaction.response.send_message("⚠️ Bu matç artıq həll olunub.", ephemeral=True)
            return
        winner_team_id = match["team_a_id"] if side == "a" else match["team_b_id"]
        await interaction.response.defer(ephemeral=True)
        result = record_tournament_match_winner(self.match_id, winner_team_id)
        if result is None:
            await interaction.followup.send("⚠️ Bu matç artıq həll olunub.", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        await _refresh_tournament_bracket_image(match["tournament_id"])

        if result["is_final"]:
            await _finish_tournament(match["tournament_id"], result["winner_team_id"], result["loser_team_id"])
        elif result["next_match_id"] is not None:
            next_match = get_tournament_match(result["next_match_id"])
            if next_match and next_match["team_a_id"] and next_match["team_b_id"]:
                await _post_tournament_match_view(next_match)

        await interaction.followup.send("✅ Nəticə qeydə alındı.", ephemeral=True)

    async def declare_a(self, interaction: discord.Interaction):
        await self._declare(interaction, "a")

    async def declare_b(self, interaction: discord.Interaction):
        await self._declare(interaction, "b")


@bot.tree.command(name="turnir_yarat", description="[Admin] Yeni turnir yaradır (bracket sistemi, FACEIT ELO-dan tam müstəqil)")
@app_commands.describe(
    ad="Turnirin adı",
    komanda_olcusu="Komanda ölçüsü: 1 (solo/1v1), 2 (2v2) və ya 5 (5v5)",
    mukafat_qalib="Qalib komandanın hər üzvünə veriləcək coin (defolt 0)",
    mukafat_finalist="Finalist (2-ci yer) komandanın hər üzvünə veriləcək coin (defolt 0)"
)
@staff_check()
async def turnir_yarat(interaction: discord.Interaction, ad: str, komanda_olcusu: int,
                        mukafat_qalib: int = 0, mukafat_finalist: int = 0):
    if komanda_olcusu not in (1, 2, 5):
        await interaction.response.send_message("❌ Komanda ölçüsü 1, 2 və ya 5 olmalıdır.", ephemeral=True)
        return
    if tournament_signup_channel_id is None:
        await interaction.response.send_message(
            "❌ Turnir kanalları hələ qurulmayıb. Əvvəlcə `/full_setup` işə salın.", ephemeral=True
        )
        return
    existing = get_active_tournament()
    if existing:
        await interaction.response.send_message(
            f"❌ Artıq aktiv bir turnir var: **{existing['name']}** (status: {existing['status']}). "
            "Yeni turnir yaratmazdan əvvəl onu bitirin/ləğv edin (`/turnir_legv_et`).", ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)
    tid = create_tournament(ad, komanda_olcusu, interaction.user.id)
    if mukafat_qalib or mukafat_finalist:
        set_tournament_meta(tid, prize_winner=mukafat_qalib, prize_runner_up=mukafat_finalist)
    channel = bot.get_channel(tournament_signup_channel_id)
    if channel:
        await _post_tournament_signup(tid, channel)
    await interaction.followup.send(
        f"✅ Turnir yaradıldı: **{ad}** (#{tid}). Qeydiyyat: <#{tournament_signup_channel_id}>", ephemeral=True
    )


@turnir_yarat.error
async def turnir_yarat_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="turnir_legv_et", description="[Admin] Cari aktiv turniri ləğv edir")
@staff_check()
async def turnir_legv_et(interaction: discord.Interaction):
    t = get_active_tournament()
    if not t:
        await interaction.response.send_message("ℹ️ Aktiv turnir yoxdur.", ephemeral=True)
        return
    cancel_tournament(t["id"])
    await interaction.response.send_message(f"✅ **{t['name']}** turniri ləğv edildi.", ephemeral=True)


@turnir_legv_et.error
async def turnir_legv_et_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


async def _submit_report(interaction: discord.Interaction, reporter_id, target_id, target_mention, reason):
    create_report(reporter_id, target_id, reason)
    channel = await _get_reports_channel()
    if channel:
        embed = discord.Embed(title="🚩 Yeni Şikayət", color=discord.Color.red())
        embed.add_field(name="Şikayətçi", value=f"<@{reporter_id}>", inline=True)
        embed.add_field(name="Hədəf", value=target_mention, inline=True)
        embed.add_field(name="Səbəb", value=reason, inline=False)
        prior = get_recent_reports_for(target_id, limit=5)
        if len(prior) > 1:
            embed.add_field(name="⚠️ Əvvəlki şikayətlər", value=f"Bu oyunçu üçün cəmi **{len(prior)}** şikayət qeydə alınıb.", inline=False)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)


class ReportReasonModal(discord.ui.Modal, title="Şikayət səbəbi"):
    sebeb = discord.ui.TextInput(label="Şikayətin səbəbi", style=discord.TextStyle.paragraph, max_length=500)

    def __init__(self, reporter_id, target_id, target_mention):
        super().__init__()
        self.reporter_id = reporter_id
        self.target_id = target_id
        self.target_mention = target_mention

    async def on_submit(self, interaction: discord.Interaction):
        await _submit_report(interaction, self.reporter_id, self.target_id, self.target_mention, self.sebeb.value)
        await interaction.response.send_message("✅ Şikayətiniz admin komandasına göndərildi. Təşəkkürlər!", ephemeral=True)


class ReportUserSelectView(discord.ui.View):
    def __init__(self, reporter_id):
        super().__init__(timeout=120)
        self.reporter_id = reporter_id
        self.select = discord.ui.UserSelect(placeholder="Şikayət olunan oyunçunu seçin...")
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.reporter_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return
        target = self.select.values[0]
        if target.id == self.reporter_id:
            await interaction.response.send_message("❌ Özünüzü şikayət edə bilməzsiniz.", ephemeral=True)
            return
        await interaction.response.send_modal(ReportReasonModal(self.reporter_id, target.id, target.mention))


class GiftAmountModal(discord.ui.Modal, title="Hədiyyə miqdarı"):
    meqdar = discord.ui.TextInput(label="Neçə coin göndərmək istəyirsiniz?", placeholder="məs: 100", max_length=10)

    def __init__(self, sender_id, target_id, target_name, target_mention):
        super().__init__()
        self.sender_id = sender_id
        self.target_id = target_id
        self.target_name = target_name
        self.target_mention = target_mention

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.meqdar.value)
        except ValueError:
            await interaction.response.send_message("❌ Rəqəm daxil edin.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("❌ Miqdar müsbət olmalıdır.", ephemeral=True)
            return
        if not get_player(self.target_id):
            await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
            return
        ok, msg, commission, receiver_amt = transfer_coins(self.sender_id, self.target_id, amount)
        if not ok:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return
        add_coin_log(self.sender_id, -amount, f"Hədiyyə → {self.target_name}", "spend", get_coins(self.sender_id))
        add_coin_log(self.target_id, receiver_amt, "Hədiyyə alındı", "earn", get_coins(self.target_id))
        await interaction.response.send_message(
            f"🎁 **{amount} coin**-dən {self.target_mention} **{receiver_amt} coin** aldı "
            f"(20% komissiya: {commission} coin). Qalan balansınız: **{get_coins(self.sender_id)}** coin.",
            ephemeral=True
        )
        try:
            if interaction.guild:
                target_member = interaction.guild.get_member(self.target_id)
                if target_member:
                    await target_member.send(f"🎁 Sizə **{receiver_amt} coin** hədiyyə edildi!")
        except (discord.Forbidden, discord.HTTPException):
            pass


class GiftUserSelectView(discord.ui.View):
    def __init__(self, sender_id):
        super().__init__(timeout=120)
        self.sender_id = sender_id
        self.select = discord.ui.UserSelect(placeholder="Hədiyyə göndəriləcək oyunçunu seçin...")
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.sender_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return
        target = self.select.values[0]
        if target.id == self.sender_id:
            await interaction.response.send_message("❌ Özünüzə hədiyyə edə bilməzsiniz.", ephemeral=True)
            return
        if target.bot:
            await interaction.response.send_message("❌ Bota hədiyyə edə bilməzsiniz.", ephemeral=True)
            return
        await interaction.response.send_modal(GiftAmountModal(self.sender_id, target.id, target.display_name, target.mention))


class MoreOptionsView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Hədiyyə et", style=discord.ButtonStyle.success, emoji="🎁")
    async def gift_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            "🎁 Hədiyyə göndəriləcək oyunçunu seçin:", view=GiftUserSelectView(self.discord_id), ephemeral=True
        )

    @discord.ui.button(label="Şikayət et", style=discord.ButtonStyle.danger, emoji="🚩")
    async def report_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            "🚩 Şikayət olunan oyunçunu seçin:", view=ReportUserSelectView(self.discord_id), ephemeral=True
        )


@bot.tree.command(name="admin_toplu_coin", description="[Admin] Bir neçə oyunçuya eyni anda coin verir/çıxarır")
@app_commands.describe(
    discord_idler="Vergüllə ayrılmış Discord ID-lər (məs: 111,222,333)",
    meqdar="Verilən/çıxarılan coin miqdarı (mənfi ola bilər)",
    sebeb="Səbəb (log üçün)"
)
@staff_check()
async def admin_toplu_coin(interaction: discord.Interaction, discord_idler: str, meqdar: int, sebeb: str):
    try:
        ids = [int(x.strip()) for x in discord_idler.split(",") if x.strip()]
    except ValueError:
        await interaction.response.send_message("❌ ID-lər düzgün formatda deyil.", ephemeral=True)
        return
    if not ids:
        await interaction.response.send_message("❌ Ən azı bir ID daxil edin.", ephemeral=True)
        return
    ok, missing = bulk_add_coins(ids, meqdar, f"Toplu admin: {sebeb}")
    log_admin_action("admin_toplu_coin", 0, "coins", "-", f"{len(ok)} oyunçu, {meqdar} coin", sebeb, interaction.user.id)
    await _post_audit_log("admin_toplu_coin", 0, "coins", "-", f"{len(ok)} oyunçu × {meqdar} coin", sebeb, interaction.user.id)
    msg = f"✅ **{len(ok)}** oyunçuya {meqdar} coin tətbiq edildi."
    if missing:
        msg += f"\n⚠️ Tapılmayan ID-lər: {', '.join(str(m) for m in missing)}"
    await interaction.response.send_message(msg, ephemeral=True)


@admin_toplu_coin.error
async def admin_toplu_coin_error(interaction: discord.Interaction, error):
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


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET / COIN
# ═══════════════════════════════════════════════════════════════════════════════

def _market_items_by_type(item_type):
    return [i for i in MARKET_ITEMS if i.get("type") == item_type and not i.get("exclusive")]


class MarketItemView(discord.ui.View):
    def __init__(self, discord_id, item_type):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.item_type = item_type
        self.selected_item_id = None

        options = []
        for item in _market_items_by_type(item_type):
            owned = owns_item(discord_id, item["id"])
            if owned:
                desc = "Artıq sahibsiniz"
            elif item.get("price_azn") is not None:
                desc = f"{item['price_azn']} AZN"
            else:
                discount = get_discount(item["id"])
                if discount:
                    desc = f"🔥 {round(item['price'] * (100 - discount) / 100)} coin (endirim {discount}%)"
                else:
                    desc = f"{item['price']} coin"
            options.append(discord.SelectOption(label=item["name"][:100], value=item["id"], description=desc[:100]))
        if options:
            sel = discord.ui.Select(placeholder="Əşya seçin...", options=options[:25])
            sel.callback = self._on_select
            self.add_item(sel)
            self.select_menu = sel

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu market yalnız sizin üçündür — Profil → Market düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.selected_item_id = self.select_menu.values[0]
        item = get_item_by_id(self.selected_item_id)
        name = item["name"] if item else self.selected_item_id
        await interaction.response.send_message(
            f"✅ Seçildi: **{name}**. İndi \"Önizlə\" və ya \"Al\" düymələrini basa bilərsiniz.",
            ephemeral=True
        )

    @discord.ui.button(label="Önizlə", style=discord.ButtonStyle.secondary, emoji="👁️", row=1)
    async def preview_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_item_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir əşya seçin.", ephemeral=True)
            return
        item = get_item_by_id(self.selected_item_id)
        if not item:
            await interaction.response.send_message("❌ Əşya tapılmadı.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if item["type"] in ("banner", "avatar_frame"):
            avatar_bytes = None
            try:
                avatar_url = interaction.user.display_avatar.replace(size=256).url
                resp = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
                avatar_bytes = resp.content
            except Exception:
                avatar_bytes = None
            preview_path = os.path.join(DATA_DIR or ".", f"preview_{self.discord_id}_{item['id']}.png")
            await asyncio.to_thread(generate_item_preview_card, interaction.user.display_name, avatar_bytes, item, preview_path)
            await interaction.followup.send(file=discord.File(preview_path, filename="preview.png"), ephemeral=True)
        else:
            accent = item.get("colors", {}).get("accent", (240, 180, 41))
            embed = discord.Embed(
                title=f"🌈 {item['name']} — Önizləmə",
                description="Bu tema aktiv olanda profilinizin aksent rəngi bu olacaq.",
                color=discord.Color.from_rgb(*accent)
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Al", style=discord.ButtonStyle.success, emoji="🛒", row=1)
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_item_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir əşya seçin.", ephemeral=True)
            return
        item = get_item_by_id(self.selected_item_id)
        if not item:
            await interaction.response.send_message("❌ Əşya tapılmadı.", ephemeral=True)
            return
        if owns_item(self.discord_id, item["id"]):
            await interaction.response.send_message(f"⚠️ **{item['name']}** əşyasına artıq sahibsiniz.", ephemeral=True)
            return

        if item.get("price_azn") is not None:
            azn_balance = get_zm_balance(self.discord_id)
            if azn_balance < item["price_azn"]:
                await interaction.response.send_message(
                    f"❌ AZN balansınız kifayət etmir. **{item['name']}** — {item['price_azn']} AZN, "
                    f"sizdə **{azn_balance:.2f}** AZN var.",
                    ephemeral=True
                )
                return
            spend_zm(self.discord_id, item["price_azn"])
            add_to_inventory(self.discord_id, item["id"])
            await interaction.response.send_message(
                f"✅ **{item['name']}** alındı! Qalan balans: **{get_zm_balance(self.discord_id):.2f}** AZN.\n"
                "Profil → İnventar düyməsindən aktiv edə bilərsiniz.",
                ephemeral=True
            )
            return

        discount = get_discount(item["id"])
        price = round(item["price"] * (100 - discount) / 100) if discount else item["price"]
        balance = get_coins(self.discord_id)
        if balance < price:
            await interaction.response.send_message(
                f"❌ Balansınız kifayət etmir. **{item['name']}** — {price} coin, sizdə **{balance}** coin var.",
                ephemeral=True
            )
            return
        spend_coins(self.discord_id, price)
        add_to_inventory(self.discord_id, item["id"])
        new_bal = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -price, f"Market alışı: {item['name']}" + (f" (flash sale {discount}%)" if discount else ""), "spend", new_bal)
        await interaction.response.send_message(
            f"✅ **{item['name']}** alındı{' 🔥 flash sale endirimi ilə' if discount else ''}! Qalan balans: **{new_bal}** coin.\nProfil → İnventar düyməsindən aktiv edə bilərsiniz.",
            ephemeral=True
        )


class EloCardView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.selected_pack_id = None

        options = [
            discord.SelectOption(label=p["label"], value=p["id"], description=f"{p['price_azn']} AZN")
            for p in ELO_CARD_PACKS
        ]
        sel = discord.ui.Select(placeholder="Paket seçin...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu market yalnız sizin üçündür — Profil → Market düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.selected_pack_id = self.select_menu.values[0]
        pack = get_elo_card_pack(self.selected_pack_id)
        await interaction.response.send_message(
            f"✅ Seçildi: **{pack['label']}** — {pack['price_azn']} AZN. İndi \"Al\" düyməsini basa bilərsiniz.",
            ephemeral=True
        )

    @discord.ui.button(label="Al", style=discord.ButtonStyle.success, emoji="⚡", row=1)
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_pack_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir paket seçin.", ephemeral=True)
            return
        pack = get_elo_card_pack(self.selected_pack_id)
        if not pack:
            await interaction.response.send_message("❌ Paket tapılmadı.", ephemeral=True)
            return
        balance = get_zm_balance(self.discord_id)
        if balance < pack["price_azn"]:
            await interaction.response.send_message(
                f"❌ AZN balansınız kifayət etmir. **{pack['label']}** — {pack['price_azn']} AZN, "
                f"sizdə **{balance:.2f}** AZN var.",
                ephemeral=True
            )
            return
        spend_zm(self.discord_id, pack["price_azn"])
        add_boost_cards(self.discord_id, pack["card_type"], pack["qty"])
        await interaction.response.send_message(
            f"✅ **{pack['label']}** alındı! Kartlarınız avtomatik olaraq növbəti uyğun matç "
            f"nəticəsində tətbiq olunacaq.",
            ephemeral=True
        )


class BundleView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.selected_bundle_id = None

        options = [discord.SelectOption(label=b["name"][:100], value=b["id"], description=f"{b['price']} coin")
                   for b in MARKET_BUNDLES]
        sel = discord.ui.Select(placeholder="Paket seçin...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu market yalnız sizin üçündür — Profil → Market düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.selected_bundle_id = self.select_menu.values[0]
        bundle = get_bundle_by_id(self.selected_bundle_id)
        await interaction.response.send_message(
            f"✅ Seçildi: **{bundle['name']}** — {bundle['price']} coin. İndi \"Al\" düyməsini basa bilərsiniz.",
            ephemeral=True
        )

    @discord.ui.button(label="Al", style=discord.ButtonStyle.success, emoji="📦", row=1)
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_bundle_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir paket seçin.", ephemeral=True)
            return
        bundle = get_bundle_by_id(self.selected_bundle_id)
        if not bundle:
            await interaction.response.send_message("❌ Paket tapılmadı.", ephemeral=True)
            return
        already_owned = [i for i in bundle["items"] if owns_item(self.discord_id, i)]
        if already_owned:
            names = ", ".join(get_item_by_id(i)["name"] for i in already_owned)
            await interaction.response.send_message(f"⚠️ Artıq bu əşyalara sahibsiniz: {names}", ephemeral=True)
            return
        balance = get_coins(self.discord_id)
        if balance < bundle["price"]:
            await interaction.response.send_message(
                f"❌ Balansınız kifayət etmir. **{bundle['name']}** — {bundle['price']} coin, sizdə **{balance}** coin var.",
                ephemeral=True
            )
            return
        spend_coins(self.discord_id, bundle["price"])
        for item_id in bundle["items"]:
            add_to_inventory(self.discord_id, item_id)
        new_bal = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -bundle["price"], f"Paket alışı: {bundle['name']}", "spend", new_bal)
        await interaction.response.send_message(
            f"✅ **{bundle['name']}** alındı! Qalan balans: **{new_bal}** coin.\nProfil → İnventar düyməsindən aktiv edə bilərsiniz.",
            ephemeral=True
        )


class MarketCategoryView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu market yalnız sizin üçündür — Profil → Market düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    async def _open_category(self, interaction: discord.Interaction, item_type: str, label: str):
        if not await self._guard(interaction):
            return
        items = _market_items_by_type(item_type)
        balance = get_coins(self.discord_id)
        azn_balance = get_zm_balance(self.discord_id)
        embed = discord.Embed(
            title=f"🛒 {label}",
            description=(f"Balansınız: **{balance} coin**\n💵 **{azn_balance:.2f} AZN**"
                         + ("" if items else "\n\nBu kataqoriyada hələ əşya yoxdur.")),
            color=discord.Color.from_rgb(138, 92, 230)
        )
        for item in items:
            owned = owns_item(self.discord_id, item["id"])
            if owned:
                value = "✅ Sahibsiniz"
            elif item.get("price_azn") is not None:
                value = f"**{item['price_azn']} AZN**"
            else:
                discount = get_discount(item["id"])
                if discount:
                    discounted = round(item["price"] * (100 - discount) / 100)
                    value = f"🔥 ~~{item['price']}~~ **{discounted} coin** ({discount}% endirim)"
                else:
                    value = f"**{item['price']} coin**"
            embed.add_field(name=item["name"], value=value, inline=True)
        view = MarketItemView(self.discord_id, item_type)
        await interaction.response.edit_message(embed=embed, attachments=[], view=view)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.primary, emoji="🎨")
    async def banner_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._open_category(interaction, "banner", "Bannerlər")

    @discord.ui.button(label="Çərçivə", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def frame_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._open_category(interaction, "avatar_frame", "Çərçivələr")

    @discord.ui.button(label="Tema", style=discord.ButtonStyle.primary, emoji="🌈")
    async def theme_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._open_category(interaction, "profile_theme", "Temalar")

    @discord.ui.button(label="ELO Kartları", style=discord.ButtonStyle.primary, emoji="⚡")
    async def elo_cards_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        balance = get_zm_balance(self.discord_id)
        counts = get_boost_card_counts(self.discord_id)
        card_path = os.path.join(DATA_DIR or ".", f"elo_cards_{self.discord_id}.png")
        await asyncio.to_thread(generate_elo_cards_market_card, balance, counts, ELO_CARD_PACKS, card_path)
        view = EloCardView(self.discord_id)
        await interaction.response.edit_message(
            embed=None, attachments=[discord.File(card_path, filename="elo_cards.png")], view=view
        )

    @discord.ui.button(label="Paketlər", style=discord.ButtonStyle.primary, emoji="📦")
    async def bundles_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        balance = get_coins(self.discord_id)
        embed = discord.Embed(
            title="📦 Paketlər (Bundle)",
            description=f"Balansınız: **{balance} coin**\n\nBirdən çox əşyanı endirimli qiymətə birlikdə alın!",
            color=discord.Color.from_rgb(138, 92, 230)
        )
        for b in MARKET_BUNDLES:
            full_price = bundle_full_price(b)
            saving = full_price - b["price"]
            item_names = ", ".join(get_item_by_id(i)["name"] for i in b["items"] if get_item_by_id(i))
            embed.add_field(
                name=f"{b['name']} — {b['price']} coin",
                value=f"{item_names}\n~~{full_price} coin~~ (**{saving} coin qənaət**)",
                inline=False
            )
        view = BundleView(self.discord_id)
        await interaction.response.edit_message(embed=embed, attachments=[], view=view)


async def _render_market(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    balance = get_coins(discord_id)
    azn_balance = get_zm_balance(discord_id)
    embed = discord.Embed(
        title="🛒 Nextlevelaz Market",
        description=f"Balansınız: **{balance} coin**\n💵 **{azn_balance:.2f} AZN**\n\nBir kataqoriya seçin:",
        color=discord.Color.from_rgb(138, 92, 230)
    )
    view = MarketCategoryView(discord_id)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class InventoryView(discord.ui.View):
    def __init__(self, discord_id, owned_ids):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.selected_item_id = None

        options = []
        for item_id in owned_ids:
            item = get_item_by_id(item_id)
            if not item or item["type"] not in ("banner", "avatar_frame", "profile_theme"):
                continue
            type_label = {"banner": "Banner", "avatar_frame": "Çərçivə", "profile_theme": "Tema"}[item["type"]]
            options.append(discord.SelectOption(label=item["name"][:100], value=item["id"], description=type_label))
        if options:
            sel = discord.ui.Select(placeholder="Aktivləşdirmək üçün əşya seçin...", options=options[:25])
            sel.callback = self._on_select
            self.add_item(sel)
            self.select_menu = sel

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu inventar yalnız sizin üçündür — Profil → İnventar düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.selected_item_id = self.select_menu.values[0]
        item = get_item_by_id(self.selected_item_id)
        name = item["name"] if item else self.selected_item_id
        await interaction.response.send_message(
            f"✅ Seçildi: **{name}**. İndi \"Aktiv et\" düyməsini basa bilərsiniz.", ephemeral=True
        )

    @discord.ui.button(label="Aktiv et", style=discord.ButtonStyle.success, emoji="✨", row=1)
    async def activate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_item_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir əşya seçin.", ephemeral=True)
            return
        item = get_item_by_id(self.selected_item_id)
        if not item:
            await interaction.response.send_message("❌ Əşya tapılmadı.", ephemeral=True)
            return
        if item["type"] == "banner":
            set_active_banner(self.discord_id, self.selected_item_id)
        elif item["type"] == "avatar_frame":
            set_active_frame(self.discord_id, self.selected_item_id)
        elif item["type"] == "profile_theme":
            set_active_theme(self.discord_id, self.selected_item_id)
        else:
            await interaction.response.send_message("❌ Bu əşya növü aktiv edilə bilmir.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ **{item['name']}** aktiv edildi!", ephemeral=True)

    @discord.ui.button(label="Coin qarşılığı sat", style=discord.ButtonStyle.primary, emoji="💰", row=2)
    async def sell_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_item_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir əşya seçin.", ephemeral=True)
            return
        item = get_item_by_id(self.selected_item_id)
        if not item:
            await interaction.response.send_message("❌ Əşya tapılmadı.", ephemeral=True)
            return
        if item.get("exclusive") or item.get("price") is None:
            await interaction.response.send_message(
                "❌ Bu əşya satıla bilməz (unikal hədiyyə və ya pulla alınıb).", ephemeral=True
            )
            return
        refund = item["price"] // 2
        removed = remove_from_inventory(self.discord_id, self.selected_item_id)
        if not removed:
            await interaction.response.send_message("❌ Bu əşya artıq inventarınızda yoxdur.", ephemeral=True)
            return
        new_bal = add_coins(self.discord_id, refund)
        add_coin_log(self.discord_id, refund, f"Satış: {item['name']}", "earn", new_bal)
        self.selected_item_id = None
        await interaction.response.send_message(
            f"💰 **{item['name']}** satıldı — **+{refund} coin** (yeni balans: {new_bal}).", ephemeral=True
        )

    @discord.ui.button(label="Sil", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if not self.selected_item_id:
            await interaction.response.send_message("❌ Əvvəlcə yuxarıdan bir əşya seçin.", ephemeral=True)
            return
        item = get_item_by_id(self.selected_item_id)
        name = item["name"] if item else self.selected_item_id
        removed = remove_from_inventory(self.discord_id, self.selected_item_id)
        if not removed:
            await interaction.response.send_message("❌ Bu əşya artıq inventarınızda yoxdur.", ephemeral=True)
            return
        self.selected_item_id = None
        await interaction.response.send_message(f"🗑️ **{name}** inventardan silindi (əvəzi qaytarılmır).", ephemeral=True)


async def _render_inventory(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    owned = get_inventory(discord_id)
    active_banner = get_active_banner(discord_id)
    active_frame = get_active_frame(discord_id)
    elo_cards = get_boost_card_counts(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"inventory_{discord_id}.png")
    await asyncio.to_thread(
        generate_inventory_card, owned, active_banner, active_frame, [], get_item_by_id, card_path,
        elo_cards=elo_cards
    )
    view = InventoryView(discord_id, owned) if owned else discord.utils.MISSING
    await interaction.followup.send(file=discord.File(card_path, filename="inventory.png"), view=view, ephemeral=True)


async def _render_coins(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    balance = get_coins(discord_id)
    azn_balance = get_zm_balance(discord_id)
    logs = get_coin_logs(discord_id, limit=15)
    card_path = os.path.join(DATA_DIR or ".", f"coins_{discord_id}.png")
    await asyncio.to_thread(generate_coin_logs_card, logs, balance, None, card_path, azn_balance)
    await interaction.followup.send(file=discord.File(card_path, filename="coins.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NAİLİYYƏTLƏR
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_achievements(interaction: discord.Interaction, target_id: int, target_name: str):
    await interaction.response.defer(ephemeral=True)
    achievements = get_player_achievements(target_id)
    rarity = get_achievement_rarity()
    card_path = os.path.join(DATA_DIR or ".", f"achievements_{target_id}.png")
    await asyncio.to_thread(generate_achievements_card, target_name, achievements, card_path, rarity)
    await interaction.followup.send(file=discord.File(card_path, filename="achievements.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STATİSTİKA (K/D) VƏ MATÇ TARİXÇƏSİ
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_stats(interaction: discord.Interaction, target_id: int):
    await interaction.response.defer(ephemeral=True)
    player_data = get_player_stats_dict(target_id)
    achievements = get_player_achievements(target_id)
    card_path = os.path.join(DATA_DIR or ".", f"stats_{target_id}.png")
    await asyncio.to_thread(generate_stats_card, player_data, achievements, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="stats.png"), ephemeral=True)


async def _render_history(interaction: discord.Interaction, target_id: int):
    await interaction.response.defer(ephemeral=True)
    history = get_player_match_history(target_id, limit=10)
    card_path = os.path.join(DATA_DIR or ".", f"history_{target_id}.png")
    await asyncio.to_thread(generate_match_history_card, history, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="history.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# XƏRİTƏ STATİSTİKASI
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_maps(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    stats = get_map_stats(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"maps_{discord_id}.png")
    await asyncio.to_thread(generate_map_stats_card, nick, stats, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="maps.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ŞƏXSİ REKORD
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_record(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    record = get_personal_record(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"record_{discord_id}.png")
    await asyncio.to_thread(generate_personal_record_card, nick, record, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="record.png"), ephemeral=True)


async def _render_elo_chart(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    history = list(reversed(get_player_match_history(discord_id, limit=30)))
    chart_data = [{"match_number": h["match_number"], "elo_after": h["elo_after"]} for h in history]
    card_path = os.path.join(DATA_DIR or ".", f"elo_chart_{discord_id}.png")
    await asyncio.to_thread(generate_elo_chart_card, nick, chart_data, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="elo_chart.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FƏRDİ LƏQƏBLƏR
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_titles(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    titles = get_player_titles(discord_id)
    active_name = get_active_title_name(discord_id)

    embed = discord.Embed(
        title=f"🏅 {nick} — Fərdi Ləqəblər",
        description=f"Aktiv ləqəb: **{active_name}**" if active_name else "Aktiv ləqəb seçilməyib.",
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.add_field(
        name="Qazanılmış ləqəblər",
        value="\n".join(f"{t['icon']} {t['name']}" for t in titles) if titles else "Hələ heç bir ləqəb qazanılmayıb.",
        inline=False
    )

    kwargs = {"embed": embed, "ephemeral": True}
    if titles:
        kwargs["view"] = TitleSelectView(discord_id, titles)
    await interaction.followup.send(**kwargs)


async def _render_quests(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    quests = get_player_quests(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"quests_{discord_id}.png")
    await asyncio.to_thread(generate_quest_card, nick, quests, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="quests.png"), ephemeral=True)


async def _render_synergy(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    synergy = get_best_duo(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"synergy_{discord_id}.png")
    await asyncio.to_thread(generate_synergy_card, nick, synergy, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="synergy.png"), ephemeral=True)


class TitleSelectView(discord.ui.View):
    def __init__(self, discord_id, titles):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        options = [
            discord.SelectOption(label=t["name"], value=t["id"], emoji=t["icon"])
            for t in titles[:24]
        ]
        options.append(discord.SelectOption(label="Ləqəbi sıfırla", value="__none__"))
        sel = discord.ui.Select(placeholder="Aktiv ləqəbi seçin...", options=options)
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız sizin üçündür.", ephemeral=True)
            return
        value = self.select_menu.values[0]
        title_id = None if value == "__none__" else value
        set_active_title(self.discord_id, title_id)
        label = "sıfırlandı" if title_id is None else "təyin edildi"
        await interaction.response.edit_message(content=f"✅ Ləqəb {label}.", embed=None, view=None)


# ═══════════════════════════════════════════════════════════════════════════════
# SQUAD (SABİT DUO)
# ═══════════════════════════════════════════════════════════════════════════════

async def _render_squad(interaction: discord.Interaction, discord_id: int, nick: str):
    await interaction.response.defer(ephemeral=True)
    squad = get_squad(discord_id)
    squad_info = None
    if squad:
        partner_row = get_player(squad["partner_id"])
        squad_info = {
            "partner_nick": partner_row[1] if partner_row else str(squad["partner_id"]),
            "wins_together": squad["wins_together"]
        }
    card_path = os.path.join(DATA_DIR or ".", f"squad_{discord_id}.png")
    await asyncio.to_thread(generate_squad_card, nick, squad_info, card_path)

    kwargs = {"file": discord.File(card_path, filename="squad.png"), "ephemeral": True}
    if not squad:
        invite = get_pending_squad_invite(discord_id)
        if invite:
            inviter_row = get_player(invite["inviter_id"])
            inviter_nick = inviter_row[1] if inviter_row else str(invite["inviter_id"])
            kwargs["content"] = f"🤝 **{inviter_nick}** sizə squad dəvəti göndərib!"
            kwargs["view"] = SquadInviteView()
    await interaction.followup.send(**kwargs)


class SquadInviteView(discord.ui.View):
    """Stateless/persistent görünüş: klik zamanı klikləyən şəxsin öz aktiv dəvətini
    bazadan oxuyur, ona görə bot restart olsa və ya 5+ dəqiqə keçsə belə işləyir."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Qəbul et", style=discord.ButtonStyle.success, emoji="✅", custom_id="squad_accept")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        invite = get_pending_squad_invite(interaction.user.id)
        if not invite:
            await interaction.response.send_message("❌ Sizin üçün aktiv squad dəvəti yoxdur.", ephemeral=True)
            return
        ok = accept_squad_invite(invite["id"])
        for child in self.children:
            child.disabled = True
        if ok:
            await interaction.response.edit_message(
                content="✅ Squad yaradıldı! `/profile`-dakı Squad düyməsindən baxa bilərsiniz.",
                embed=None, view=self
            )
        else:
            await interaction.response.edit_message(content="❌ Bu dəvət artıq etibarsızdır.", embed=None, view=self)

    @discord.ui.button(label="Rədd et", style=discord.ButtonStyle.danger, emoji="❌", custom_id="squad_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        invite = get_pending_squad_invite(interaction.user.id)
        if not invite:
            await interaction.response.send_message("❌ Sizin üçün aktiv squad dəvəti yoxdur.", ephemeral=True)
            return
        reject_squad_invite(invite["id"])
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Dəvət rədd edildi.", embed=None, view=self)


@bot.tree.command(name="squad", description="Sabit duo tərəfdaşınıza squad dəvəti göndərir")
@app_commands.describe(partnyor="Squad tərəfdaşı olmaq istədiyiniz oyunçu")
async def squad_cmd(interaction: discord.Interaction, partnyor: discord.Member):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    if not get_player(partnyor.id):
        await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
        return
    if partnyor.id == interaction.user.id:
        await interaction.response.send_message("❌ Özünüzü squad-a dəvət edə bilməzsiniz.", ephemeral=True)
        return
    if get_squad(interaction.user.id):
        await interaction.response.send_message("⚠️ Artıq aktiv bir squad-dasınız.", ephemeral=True)
        return

    squad_id = create_squad_invite(interaction.user.id, partnyor.id)
    if squad_id is None:
        await interaction.response.send_message(
            "❌ Dəvət göndərilə bilmədi (siz və ya partnyor artıq squad-dadır).", ephemeral=True
        )
        return

    view = SquadInviteView()
    embed = discord.Embed(
        title="🤝 Squad dəvəti",
        description=(
            f"{interaction.user.mention} sizi squad tərəfdaşı olmağa dəvət edir!\n"
            "Birlikdə qazandığınız hər matçda hər ikiniz bonus coin alacaqsınız."
        ),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(content=partnyor.mention, embed=embed, view=view)


# ═══════════════════════════════════════════════════════════════════════════════
# REAKSİYA-ƏSASLI CANLI SORĞU VƏ REAKSİYA-YARIŞI (yaddaşda, keçici vəziyyət —
# bot restart olsa aktiv sorğu/yarış sıfırlanır, məqbul tərəddüddür)
# ═══════════════════════════════════════════════════════════════════════════════

_active_polls = {}            # message_id -> {"question", "options", "channel_id"}
_active_reaction_races = {}   # message_id -> {"target_emoji", "resolved", "started_at"}
POLL_NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


def _render_poll_embed(question, options, counts):
    total = sum(counts) or 1
    lines = []
    for i, opt in enumerate(options):
        pct = round(counts[i] / total * 100) if sum(counts) else 0
        filled = round(pct / 5)
        bar = "▓" * filled + "░" * (20 - filled)
        lines.append(f"{POLL_NUMBER_EMOJIS[i]} **{opt}**\n`{bar}` {pct}% ({counts[i]} səs)")
    embed = discord.Embed(title=f"📊 {question}", description="\n\n".join(lines), color=discord.Color.blurple())
    embed.set_footer(text=f"Cəmi səs: {sum(counts)}")
    return embed


async def _refresh_poll(payload):
    poll = _active_polls.get(payload.message_id)
    if not poll:
        return
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except discord.HTTPException:
            return
    try:
        message = await channel.fetch_message(payload.message_id)
    except (discord.NotFound, discord.Forbidden):
        _active_polls.pop(payload.message_id, None)
        return
    counts = []
    for i in range(len(poll["options"])):
        reaction = discord.utils.get(message.reactions, emoji=POLL_NUMBER_EMOJIS[i])
        counts.append(max(0, (reaction.count - 1) if reaction else 0))  # botun öz reaksiyası çıxarılır
    try:
        await message.edit(embed=_render_poll_embed(poll["question"], poll["options"], counts))
    except discord.HTTPException:
        pass


async def _handle_race_reaction(payload):
    race = _active_reaction_races.get(payload.message_id)
    if not race or race["resolved"] or str(payload.emoji) != race["target_emoji"]:
        return
    race["resolved"] = True
    elapsed = (datetime.datetime.utcnow() - race["started_at"]).total_seconds()
    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except discord.HTTPException:
            return
    try:
        message = await channel.fetch_message(payload.message_id)
        await message.edit(content=f"🏆 <@{payload.user_id}> qazandı! ({elapsed:.2f} saniyə)")
    except discord.HTTPException:
        pass
    _active_reaction_races.pop(payload.message_id, None)


async def _handle_intel_feedback(payload):
    if str(payload.emoji) not in ("👍", "👎"):
        return
    _intel_briefing_message_ids.discard(payload.message_id)  # hər DM üçün cəmi 1 rəy sayılır
    rating = "faydalı 👍" if str(payload.emoji) == "👍" else "faydasız 👎"
    audit_channel = await _get_audit_log_channel()
    if audit_channel:
        try:
            await audit_channel.send(f"🧭 Kəşfiyyat briefinqi rəyi: <@{payload.user_id}> — {rating}")
        except discord.HTTPException:
            pass


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if bot.user and payload.user_id == bot.user.id:
        return
    if payload.message_id in _active_polls:
        await _refresh_poll(payload)
    elif payload.message_id in _active_reaction_races:
        await _handle_race_reaction(payload)
    elif payload.message_id in _intel_briefing_message_ids:
        await _handle_intel_feedback(payload)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id in _active_polls:
        await _refresh_poll(payload)


@bot.tree.command(name="sorgu", description="Reaksiya ilə canlı faiz-bar sorğu yaradır")
@app_commands.describe(sual="Sorğu sualı", seçimlər="Vergüllə ayrılmış 2-5 seçim (məs: Bəli,Xeyr,Bilmirəm)")
async def sorgu_cmd(interaction: discord.Interaction, sual: str, seçimlər: str):
    options = [o.strip() for o in seçimlər.split(",") if o.strip()][:5]
    if len(options) < 2:
        await interaction.response.send_message("❌ Vergüllə ayrılmış ən azı 2 seçim daxil edin.", ephemeral=True)
        return
    await interaction.response.send_message(embed=_render_poll_embed(sual, options, [0] * len(options)))
    message = await interaction.original_response()
    _active_polls[message.id] = {"question": sual, "options": options, "channel_id": interaction.channel_id}
    for i in range(len(options)):
        try:
            await message.add_reaction(POLL_NUMBER_EMOJIS[i])
        except discord.HTTPException:
            pass


class FeedbackModal(discord.ui.Modal, title="Rəy Bildir"):
    mesaj = discord.ui.TextInput(
        label="Rəyiniz / təklifiniz", style=discord.TextStyle.paragraph, max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        reports_channel = await _get_reports_channel()
        if reports_channel:
            embed = discord.Embed(title="📝 Yeni Rəy/Təklif", description=self.mesaj.value, color=discord.Color.blurple())
            embed.set_footer(text=f"{interaction.user} · {interaction.user.id}")
            try:
                await reports_channel.send(embed=embed)
            except discord.HTTPException:
                pass
        await interaction.response.send_message("✅ Rəyiniz göndərildi — təşəkkürlər!", ephemeral=True)


@bot.tree.command(name="feedback", description="Bot və ya server haqqında rəy/təklif bildirin")
async def feedback_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(FeedbackModal())


@bot.tree.command(name="reaksiya_yarisi", description="Reaksiya sürəti mini-oyunu — ilk düzgün reaksiya verən udur!")
async def reaksiya_yarisi_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🎮 **Reaksiya Yarışı** başlayır... Hazır olun! ⏳")
    message = await interaction.original_response()
    await asyncio.sleep(random.uniform(3, 8))
    target = random.choice(["⚡", "🔥", "🎯", "💥"])
    # Yarış vəziyyəti mesaj redaktəsindən ƏVVƏL qeydə alınır ki, "BAŞLA!" görünən kimi
    # (super-sürətli) reaksiya versə belə heç bir hadisə itirilmiş olmasın.
    _active_reaction_races[message.id] = {
        "target_emoji": target, "resolved": False, "started_at": datetime.datetime.utcnow()
    }
    await message.edit(content=f"🏁 **BAŞLA!** İlk kim {target} ilə reaksiya versə udur!")
    try:
        await message.add_reaction(target)
    except discord.HTTPException:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK TAPŞIRIQ
# ═══════════════════════════════════════════════════════════════════════════════

class TaskSelectView(discord.ui.View):
    def __init__(self, discord_id, tasks_list):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        options = [
            discord.SelectOption(
                label=t["description"][:100], value=str(t["id"]),
                description=f"Mükafat: {t['reward_coins']} coin"
            )
            for t in tasks_list
        ]
        sel = discord.ui.Select(placeholder="Bir tapşırıq seçin...", options=options[:25])
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu tapşırıq seçimi yalnız sizin üçündür.", ephemeral=True)
            return
        task_id = int(self.select_menu.values[0])
        assigned = assign_task_to_player(self.discord_id, task_id)
        if not assigned:
            await interaction.response.send_message("⚠️ Artıq aktiv bir tapşırığınız var.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="✅ Tapşırıq seçildi! Profil → Gündəlik düyməsi ilə irəliləyişinizi izləyə bilərsiniz.",
            view=self
        )


async def _render_gunluk(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    active = get_player_active_task(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"tasks_{discord_id}.png")
    if active:
        await asyncio.to_thread(generate_tasks_card, active, [], card_path)
        await interaction.followup.send(file=discord.File(card_path, filename="tasks.png"), ephemeral=True)
        return

    available = get_active_daily_tasks()
    await asyncio.to_thread(generate_tasks_card, None, available, card_path)
    view = TaskSelectView(discord_id, available) if available else discord.utils.MISSING
    await interaction.followup.send(file=discord.File(card_path, filename="tasks.png"), view=view, ephemeral=True)


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
    embed = discord.Embed(title=f"🔧 Admin — {oyunçu.display_name}", color=discord.Color.blurple())
    embed.add_field(name="Nick / SO2 ID", value=f"{data['nick']} / {data['so2_id']}", inline=False)
    embed.add_field(name="ELO", value=str(data["elo"]), inline=True)
    embed.add_field(name="Qələbə/Məğlub", value=f"{data['wins']}/{data['losses']}", inline=True)
    embed.add_field(name="K/A/D", value=f"{data['kills']}/{data['assists']}/{data['deaths']}", inline=True)
    embed.add_field(name="Seriya", value=f"{data['win_streak']} (max {data['max_streak']})", inline=True)
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
    app_commands.Choice(name="AZN Balans", value="zm_balance"),
    app_commands.Choice(name="Qələbə (wins)", value="wins"),
    app_commands.Choice(name="Məğlubiyyət (losses)", value="losses"),
    app_commands.Choice(name="Kill", value="kills"),
    app_commands.Choice(name="Assist", value="assists"),
    app_commands.Choice(name="Ölüm (deaths)", value="deaths"),
    app_commands.Choice(name="Nick (so2_nick)", value="so2_nick"),
    app_commands.Choice(name="SO2 ID", value="so2_id"),
]
ADMIN_NUMERIC_FIELDS = {"elo", "coins", "wins", "losses", "kills", "assists", "deaths"}
ADMIN_FLOAT_FIELDS = {"zm_balance"}


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
    elif field in ADMIN_FLOAT_FIELDS:
        try:
            value = round(float(dəyər), 2)
        except ValueError:
            await interaction.response.send_message("❌ Bu sahə üçün rəqəm daxil edin (məs: 12.5).", ephemeral=True)
            return
    else:
        value = dəyər

    old_data = get_player_stats_dict(oyunçu.id)
    old_val = old_data.get("nick" if field == "so2_nick" else field, "?")

    if not admin_set_player_field(oyunçu.id, field, value):
        await interaction.response.send_message("❌ Bu sahə dəyişdirilə bilməz.", ephemeral=True)
        return

    log_admin_action("admin_duzelt", oyunçu.id, field, str(old_val), str(value), "-", interaction.user.id)
    await _post_audit_log("admin_duzelt", oyunçu.id, field, old_val, value, "-", interaction.user.id)

    if field == "elo":
        await _sync_rank_role(interaction.guild, oyunçu.id, value)

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
            await _sync_rank_role(interaction.guild, p["discord_id"], p["new_elo"])
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
        results = update_team_elo(old_loser_ids, old_winner_ids)
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
            await _sync_rank_role(interaction.guild, p["discord_id"], p["new_elo"])

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
    view = MatchResultView(match_number, team_a, team_b)
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


def _parse_kad(text):
    """'K/A/D' formatını (kills, assists, deaths) tuple-a çevirir, uyğun deyilsə (0,0,0)."""
    if not text:
        return 0, 0, 0
    parts = text.replace(" ", "").split("/")
    if len(parts) != 3:
        return 0, 0, 0
    try:
        return max(0, int(parts[0])), max(0, int(parts[1])), max(0, int(parts[2]))
    except ValueError:
        return 0, 0, 0


@bot.tree.command(name="admin_matc_elave_et", description="[Admin] İtirilmiş/əl ilə matç nəticəsini ELO+statistika ilə bazaya əlavə edir")
@app_commands.describe(
    komanda_a_1="Komanda A — 1-ci oyunçu", komanda_a_2="Komanda A — 2-ci oyunçu",
    komanda_b_1="Komanda B — 1-ci oyunçu", komanda_b_2="Komanda B — 2-ci oyunçu",
    qalib="Qalib komanda",
    a1_kad="Komanda A 1-ci oyunçunun K/A/D (məs: 9/1/1) — boş buraxıla bilər",
    a2_kad="Komanda A 2-ci oyunçunun K/A/D — boş buraxıla bilər",
    b1_kad="Komanda B 1-ci oyunçunun K/A/D — boş buraxıla bilər",
    b2_kad="Komanda B 2-ci oyunçunun K/A/D — boş buraxıla bilər",
    matc_no="Matç nömrəsi (boş buraxsanız avtomatik növbəti nömrə verilir)",
    xerite="Xəritə adı (opsional, xəritə statistikası üçün)"
)
@app_commands.choices(qalib=[
    app_commands.Choice(name="Komanda A", value="A"),
    app_commands.Choice(name="Komanda B", value="B"),
])
@staff_check()
async def admin_matc_elave_et_cmd(
    interaction: discord.Interaction,
    komanda_a_1: discord.Member, komanda_a_2: discord.Member,
    komanda_b_1: discord.Member, komanda_b_2: discord.Member,
    qalib: app_commands.Choice[str],
    a1_kad: str = None, a2_kad: str = None,
    b1_kad: str = None, b2_kad: str = None,
    matc_no: int = None, xerite: str = None
):
    members = [komanda_a_1, komanda_a_2, komanda_b_1, komanda_b_2]
    if len(set(m.id for m in members)) != 4:
        await interaction.response.send_message("❌ Eyni oyunçunu bir neçə mövqedə göstərə bilməzsiniz.", ephemeral=True)
        return

    players = {}
    for m in members:
        row = get_player(m.id)
        if not row:
            await interaction.response.send_message(f"❌ {m.display_name} qeydiyyatdan keçməyib.", ephemeral=True)
            return
        players[m.id] = {"discord_id": m.id, "nick": row[1]}

    team_a = [players[komanda_a_1.id], players[komanda_a_2.id]]
    team_b = [players[komanda_b_1.id], players[komanda_b_2.id]]
    winner_team, loser_team = (team_a, team_b) if qalib.value == "A" else (team_b, team_a)
    winner_ids = [p["discord_id"] for p in winner_team]
    loser_ids = [p["discord_id"] for p in loser_team]

    results = update_team_elo(winner_ids, loser_ids)
    if results is None:
        await interaction.response.send_message("❌ Xəta: oyunçu məlumatları tapılmadı.", ephemeral=True)
        return

    winner_avg_old_elo = sum(r["old_elo"] for r in results["winners"]) / len(results["winners"])
    loser_avg_old_elo = sum(r["old_elo"] for r in results["losers"]) / len(results["losers"])
    is_upset = (loser_avg_old_elo - winner_avg_old_elo) >= UPSET_ELO_THRESHOLD

    match_number = matc_no if matc_no is not None else get_next_match_number()

    kad_by_id = {
        komanda_a_1.id: _parse_kad(a1_kad), komanda_a_2.id: _parse_kad(a2_kad),
        komanda_b_1.id: _parse_kad(b1_kad), komanda_b_2.id: _parse_kad(b2_kad),
    }
    had_kad = {
        komanda_a_1.id: bool(a1_kad), komanda_a_2.id: bool(a2_kad),
        komanda_b_1.id: bool(b1_kad), komanda_b_2.id: bool(b2_kad),
    }
    for discord_id, (k, a, d) in kad_by_id.items():
        add_combat_stats(discord_id, k, a, d)

    az_now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    today_key = az_now.strftime("%Y-%m-%d")

    new_achievements = []
    new_titles = []
    new_quests = []
    challenge_claimers = []
    current_season = get_or_create_current_season()
    achievement_rarity = get_achievement_rarity()
    boss_contributions = {did: k for did, (k, a, d) in kad_by_id.items() if had_kad[did] and k > 0}
    if boss_contributions:
        asyncio.create_task(_update_boss_progress(boss_contributions))
    for p, r in zip(winner_team, results["winners"]):
        k, a, d = kad_by_id[p["discord_id"]]
        add_season_stat(p["discord_id"], current_season["id"], kills=k, assists=a, deaths=d,
                         wins=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"])
        streak, _ = update_streak(p["discord_id"], True)
        bonus_coins, _ = get_streak_bonus(streak)
        earned = random.randint(5, 10) + bonus_coins
        if _is_weekend_bonus_active():
            earned *= 2
        new_bal = add_coins(p["discord_id"], earned)
        add_coin_log(
            p["discord_id"], earned,
            f"Matç No{match_number} qələbə (əl ilə əlavə)" + (" (həftəsonu 2x)" if _is_weekend_bonus_active() else ""),
            "earn", new_bal
        )
        if had_kad[p["discord_id"]]:
            k, a, d = kad_by_id[p["discord_id"]]
            update_personal_record(p["discord_id"], k, a, d, match_number)
        for ach in check_and_grant_achievements(p["discord_id"]):
            new_achievements.append((p["nick"], ach))
            if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                asyncio.create_task(_post_wall_announcement(interaction.guild, p["discord_id"], p["nick"], ach["name"], ach["icon"], "nailiyyət"))
            asyncio.create_task(_maybe_grant_sticker(interaction.guild, p["discord_id"], p["nick"], ach["id"]))
        for ti in check_and_grant_titles(p["discord_id"]):
            new_titles.append((p["nick"], ti))
            if interaction.guild:
                asyncio.create_task(_post_wall_announcement(interaction.guild, p["discord_id"], p["nick"], ti["name"], ti["icon"], "ləqəb"))
        for q in update_quest_progress(p["discord_id"], "win_matches"):
            new_quests.append((p["nick"], q))
        if had_kad[p["discord_id"]]:
            k, a, d = kad_by_id[p["discord_id"]]
            if claim_daily_challenge(p["discord_id"], today_key, k, a, d, True):
                challenge_claimers.append(p["nick"])
        await _sync_rank_role(interaction.guild, p["discord_id"], r["new_elo"])
        if had_kad[p["discord_id"]] and interaction.guild:
            k, a, d = kad_by_id[p["discord_id"]]
            asyncio.create_task(_send_coach_dm(
                interaction.guild, p["discord_id"], p["nick"], {"kills": k, "assists": a, "deaths": d},
                r["old_elo"], r["new_elo"], True, match_number
            ))

    for p, r in zip(loser_team, results["losers"]):
        k, a, d = kad_by_id[p["discord_id"]]
        add_season_stat(p["discord_id"], current_season["id"], kills=k, assists=a, deaths=d,
                         losses=1, elo_gained=r["new_elo"] - r["old_elo"], elo_start=r["old_elo"])
        update_streak(p["discord_id"], False)
        loss_streak = get_loss_streak(p["discord_id"])
        if loss_streak == TILT_LOSS_STREAK_THRESHOLD and get_dm_notifications(p["discord_id"]) and interaction.guild:
            asyncio.create_task(_send_tilt_warning_dm(interaction.guild, p["discord_id"], p["nick"], loss_streak))
        earned = random.randint(0, 5)
        if _is_weekend_bonus_active():
            earned *= 2
        new_bal = add_coins(p["discord_id"], earned)
        add_coin_log(
            p["discord_id"], earned,
            f"Matç No{match_number} iştirak (əl ilə əlavə)" + (" (həftəsonu 2x)" if _is_weekend_bonus_active() else ""),
            "earn", new_bal
        )
        if had_kad[p["discord_id"]]:
            k, a, d = kad_by_id[p["discord_id"]]
            update_personal_record(p["discord_id"], k, a, d, match_number)
        for ach in check_and_grant_achievements(p["discord_id"]):
            new_achievements.append((p["nick"], ach))
            if interaction.guild and achievement_rarity.get(ach["id"], 100) <= RARE_ACHIEVEMENT_THRESHOLD_PCT:
                asyncio.create_task(_post_wall_announcement(interaction.guild, p["discord_id"], p["nick"], ach["name"], ach["icon"], "nailiyyət"))
            asyncio.create_task(_maybe_grant_sticker(interaction.guild, p["discord_id"], p["nick"], ach["id"]))
        for ti in check_and_grant_titles(p["discord_id"]):
            new_titles.append((p["nick"], ti))
            if interaction.guild:
                asyncio.create_task(_post_wall_announcement(interaction.guild, p["discord_id"], p["nick"], ti["name"], ti["icon"], "ləqəb"))
        if had_kad[p["discord_id"]]:
            k, a, d = kad_by_id[p["discord_id"]]
            if claim_daily_challenge(p["discord_id"], today_key, k, a, d, False):
                challenge_claimers.append(p["nick"])
        await _sync_rank_role(interaction.guild, p["discord_id"], r["new_elo"])
        if had_kad[p["discord_id"]] and interaction.guild:
            k, a, d = kad_by_id[p["discord_id"]]
            asyncio.create_task(_send_coach_dm(
                interaction.guild, p["discord_id"], p["nick"], {"kills": k, "assists": a, "deaths": d},
                r["old_elo"], r["new_elo"], False, match_number
            ))

    if len(winner_team) == 2:
        squad = get_squad(winner_team[0]["discord_id"])
        if squad and squad["partner_id"] == winner_team[1]["discord_id"]:
            for p in winner_team:
                bal = add_coins(p["discord_id"], 10)
                add_coin_log(p["discord_id"], 10, f"Squad bonusu — Matç No{match_number}", "earn", bal)
                for q in update_quest_progress(p["discord_id"], "squad_win"):
                    new_quests.append((p["nick"], q))
            record_squad_win(winner_team[0]["discord_id"], winner_team[1]["discord_id"])

    await asyncio.to_thread(
        record_match_history, "2v2", winner_ids, loser_ids,
        [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
        [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
        match_number, xerite
    )
    if interaction.guild:
        await _check_community_goal(interaction.guild)
    log_admin_action("admin_matc_elave_et", 0, "match_history", "-", f"matc_no={match_number}", "manual entry", interaction.user.id)
    await _post_audit_log("admin_matc_elave_et", 0, "match_history", "-", f"matc_no={match_number}", "manual entry", interaction.user.id)

    winner_label = "Komanda A" if qalib.value == "A" else "Komanda B"
    loser_label = "Komanda B" if qalib.value == "A" else "Komanda A"
    asyncio.create_task(_update_live_board_message(f"Matç No{match_number}: **{winner_label}** qalib gəldi"))

    def _fmt(p, r):
        k, a, d = kad_by_id[p["discord_id"]]
        return (f"{p['nick']} — {r['old_elo']} → **{r['new_elo']}** "
                f"({'+' if r['new_elo']-r['old_elo']>=0 else ''}{r['new_elo']-r['old_elo']})  ·  K:{k} A:{a} D:{d}")

    embed = discord.Embed(
        title=f"✅ Matç No{match_number} əl ilə əlavə edildi",
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.add_field(name=f"✅ {winner_label}", value="\n".join(_fmt(p, r) for p, r in zip(winner_team, results["winners"])), inline=False)
    embed.add_field(name=f"❌ {loser_label}", value="\n".join(_fmt(p, r) for p, r in zip(loser_team, results["losers"])), inline=False)
    if _is_weekend_bonus_active():
        embed.add_field(name="🎉 Bonus", value="Həftəsonu bonusu aktivdir — 2x coin!", inline=False)
    if new_achievements:
        embed.add_field(
            name="🏆 Yeni nailiyyətlər",
            value="\n".join(f"{ach['icon']} **{ach['name']}** — {nick}" for nick, ach in new_achievements),
            inline=False
        )
    if new_titles:
        embed.add_field(
            name="🏅 Yeni ləqəblər",
            value="\n".join(f"{ti['icon']} **{ti['name']}** — {nick}" for nick, ti in new_titles),
            inline=False
        )
    if new_quests:
        embed.add_field(
            name="🧗 Quest tamamlandı!",
            value="\n".join(f"**{q['name']}** ({q['reward_coins']} coin) — {nick}" for nick, q in new_quests),
            inline=False
        )
    if challenge_claimers:
        embed.add_field(
            name="🎯 Günün Çağırışı tamamlandı",
            value=", ".join(challenge_claimers),
            inline=False
        )
    await interaction.response.send_message(embed=embed)

    if is_upset:
        upset_embed = discord.Embed(
            title="🔥 BÖYÜK SÜRPRİZ!",
            description=(
                f"**{winner_label}** ({round(winner_avg_old_elo)} orta ELO) "
                f"**{loser_label}**-i ({round(loser_avg_old_elo)} orta ELO) məğlub etdi — "
                f"{round(loser_avg_old_elo - winner_avg_old_elo)} ELO fərqinə baxmayaraq!"
            ),
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=upset_embed)


@admin_matc_elave_et_cmd.error
async def admin_matc_elave_et_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@admin_matc_elave_et_cmd.autocomplete("xerite")
async def admin_matc_elave_et_xerite_autocomplete(interaction: discord.Interaction, current: str):
    current_lower = current.lower()
    matches = [m for m in MAPS if current_lower in m.lower()] if current else list(MAPS)
    return [app_commands.Choice(name=m, value=m) for m in matches[:25]]


@bot.tree.command(name="rank_rollari_qur", description="[Admin] ELO rütbə rollarını serverdə yaradır və bütün oyunçulara təyin edir")
@staff_check()
async def rank_rollari_qur_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    created = []
    for lo, hi, name, color, emoji in RANKS:
        role = discord.utils.get(guild.roles, name=name)
        if not role:
            await guild.create_role(name=name, color=discord.Color.from_rgb(*color), reason="Rütbə rolu")
            created.append(name)
        role_5v5_name = f"5v5 {name}"
        role_5v5 = discord.utils.get(guild.roles, name=role_5v5_name)
        if not role_5v5:
            await guild.create_role(name=role_5v5_name, color=discord.Color.from_rgb(*color), reason="5v5 rütbə rolu")
            created.append(role_5v5_name)

    players = get_all_players(limit=1000)
    for p in players:
        await _sync_rank_role(guild, p["discord_id"], p["elo"])

    players_5v5 = get_all_players_5v5(limit=1000)
    for p in players_5v5:
        await _sync_rank_role_5v5(guild, p["discord_id"], p["elo"])

    await interaction.followup.send(
        f"✅ Rütbə rolları hazırdır (2v2 + 5v5).\n"
        f"🆕 Yaradılan rollar: {', '.join(created) if created else 'yoxdur (artıq mövcud idi)'}\n"
        f"🔄 {len(players)} oyunçunun 2v2 rolu, {len(players_5v5)} oyunçunun 5v5 rolu yeniləndi.",
        ephemeral=True
    )


@rank_rollari_qur_cmd.error
async def rank_rollari_qur_error(interaction: discord.Interaction, error):
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
            ("🥇 Rekord (profil düyməsi)", "Ən yaxşı kill/asist/K-D göstəricilərinizi göstərir"),
            ("🤝 Squad (profil düyməsi)", "Sabit duo tərəfdaşınızı və birlikdə qələbələrinizi göstərir"),
            ("/squad", "Bir oyunçuya squad (sabit duo) dəvəti göndərir"),
            ("🔗 Paylaş (profil düyməsi)", "Profilinizin ictimai (Discorddan kənar) linkini göndərir"),
            ("🧠 AI Coach", "Hər matçdan sonra real statistikanıza əsaslanan şəxsi məsləhət DM-lə gəlir"),
            ("📈 Qrafik (profil düyməsi)", "ELO-nuzun zaman keçdikcə necə dəyişdiyini xətti qrafikdə göstərir"),
            ("🏅 Ləqəb (profil düyməsi)", "Qazandığınız fərdi ləqəblər arasından aktiv ləqəb seçirsiniz"),
            ("🧭 Kəşfiyyat Briefinqi", "Hər matç başlayanda rəqib komandanın xəritə statistikasına görə DM gəlir"),
            ("🧗 Questlər (profil düyməsi)", "Çoxmərhələli tapşırıq zəncirlərindəki irəliləyişinizi göstərir"),
            ("🌐 Dil (profil düyməsi)", "Profil kartınızı və menyu düymələrini Azərbaycan/English/Русский dilində göstərir"),
            ("🔍 Sinergiya (profil düyməsi)", "Rəsmi squad-dan asılı olmadan, birlikdə ən yüksək qələbə faizinizin olduğu tərəfdaşı göstərir"),
        ],
    },
    "market": {
        "label": "Market",
        "title": "🛒 Market və İqtisadiyyat",
        "items": [
            ("🛒 Market (profil düyməsi)", "Banner/Çərçivə/Tema kataqoriyalarına baxıb önizləmə ilə satın alır"),
            ("🎒 İnventar (profil düyməsi)", "Sahib olduğunuz əşyaları göstərir və aktivləşdirmək üçün seçim/düymə təqdim edir"),
            ("🪙 Coin (profil düyməsi)", "Coin balansınızı və son əməliyyatları göstərir"),
            ("⚡ ELO Kartları (Market → ELO Kartları)",
             "AZN balansı ilə ELO Boost (50%/100%) və ELO Qoruma kartları alınır — hər kart növbəti "
             "uyğun matç nəticəsində avtomatik tətbiq olunur"),
        ],
    },
    "naliyyet": {
        "label": "Nailiyyət",
        "title": "🏆 Nailiyyət və Gündəlik Tapşırıq",
        "items": [
            ("🏆 Nailiyyətlər (profil düyməsi)", "Qazandığınız nailiyyətləri (nadirlik faizi ilə) göstərir"),
            ("📅 Gündəlik (profil düyməsi)", "Gündəlik tapşırığınızı göstərir və ya seçir"),
        ],
    },
    "diger": {
        "label": "Digər",
        "title": "🎉 Digər",
        "items": [
            ("Qeydiyyat düyməsi", "Qeydiyyat kanalındakı düymə ilə FACEIT sisteminə qeydiyyatdan keçirsiniz"),
            ("2v2 düyməsi", "Matchmaking kanalındakı düymə ilə sıraya qoşulursunuz"),
            ("Rütbə rolu", "ELO-nuz dəyişəndə Discord rolunuz avtomatik yenilənir"),
            ("Xoş gəldin DM-i", "Serverə qoşulanda bot avtomatik təlimat mesajı göndərir"),
            ("Həftəsonu bonusu", "Şənbə/Bazar günləri matçlardan qazanılan coin avtomatik 2x olur"),
            ("⭐ Ay Ulduzu", "Hər ayın 1-də keçən ayın ən uğurlu oyunçusuna avtomatik rol və elan verilir"),
            ("📉 ELO Decay", "7+ gün oynamayan oyunçunun ELO-su tədricən azalır (500-dən aşağı enmir)"),
            ("🌍 İcma hədəfi", f"Bu ay birlikdə {COMMUNITY_GOAL_TARGET} matç oynanılanda hər iştirakçıya coin bonusu verilir"),
            ("📡 Bot statusu", "Botun Discord statusu canlı oyunçu/matç rəqəmləri ilə növbələnir"),
            ("🌟 Qızıl Matç", f"Hər yeni matç ~{int(GOLDEN_MATCH_CHANCE*100)}% ehtimalla 2x ELO/Coin \"Qızıl Matç\" ola bilər"),
            ("🔥 Sürpriz Aşkarlayıcı", "Böyük ELO fərqi ilə qazanılan matçlar avtomatik xüsusi elanla qeyd olunur"),
            ("🏆 Nextlevelaz Mükafatları", "Hər ayın 1-də keçən ayın MVP-si, ən inkişaf edəni və ən aktivi elan olunur"),
            ("⚡ İldırım Turu", f"Təsadüfi olaraq {LIGHTNING_ROUND_DURATION_MINUTES} dəqiqəlik əlavə 2x ELO/Coin dövrü elan oluna bilər"),
            ("🎮 Matç Başlama Elanı", "Hər yeni matçda kapitanların adı/ID-si elan kanalına avtomatik göndərilir — lobbi tez qurulsun deyə"),
            ("🗑️ Qeydiyyat təmizliyi",
             f"Qeydiyyatdan {INACTIVE_REGISTRATION_DAYS} gün keçməsinə baxmayaraq heç bir matç oynamayan "
             "oyunçunun qeydiyyatı avtomatik silinir (istəsə yenidən qeydiyyatdan keçə bilər)"),
            ("🔪 Ayın ELO Çempionu",
             f"Hər ayın son günü 2v2+5v5 ELO cəmi ən yüksək olan oyunçu {MONTHLY_CHAMPION_SKIN_NAME} skinini qazanır"),
            ("🔪 Ay sonu mükafatı kanalı",
             "Serverin ən üstündəki kanalda mükafatın şəkli/qaydaları pinlənir, Top-5 sıralama "
             "həmin mesajda hər 5 dəqiqədən bir avtomatik yenilənir (yeni mesaj yox)"),
            ("🔥 Flash Sale", "Təsadüfi olaraq marketdə bir əşyaya müvəqqəti endirim elan oluna bilər"),
            ("🛤️ Sezonlar", "Hər ayın 1-də ELO sezonu bağlanır, Top-3 mükafat alır, Karyera Yolu düyməsində tarixçə qalır"),
            ("🚫 Xəritə Veto", "Hər komandanın kapitanı matç başladıqdan sonra xəritəni 1 dəfə vetolaya bilər"),
            ("🎁 Hədiyyə et", "Profil → Ayarlar → Digər → Hədiyyə et düyməsi ilə coin-lərinizi başqa oyunçuya göndərə bilərsiniz (20% komissiya)"),
            ("💱 Coin → AZN", "Profil → İnventar → Çevir düyməsi ilə 2500 coin = 0.5 AZN məzənnəsi ilə çevirmə"),
            ("📦 Paketlər", "Market → Paketlər bölməsində bir neçə əşya birlikdə endirimli qiymətə satılır"),
            ("🔨 Hərraclar", "Admin nadir əşyaları coin ilə hərraca çıxara bilər"),
            ("🎉 Bayram Matçları", "Milli bayram günlərində bütün matçlarda avtomatik 2x coin/ELO bonusu aktivdir"),
            ("🚩 Report sistemi", "Profil → Ayarlar → Digər → Şikayət et düyməsi ilə admin komandasına şikayət göndərə bilərsiniz"),
            ("👹 Həftəlik Boss Event", "İcma birlikdə matçlardakı kill-lərlə boss-u vurur, məğlub edəndə hamı coin qazanır"),
            ("🏅 Nailiyyət Divarı", "Nadir nailiyyət/ləqəb qazananlar dərhal ayrıca kanalda elan olunur"),
            ("🎙️ Ən Sosial Reytinq", "Profil → Sosial → Sosial düyməsində səs kanallarında ən çox vaxt keçirənlərin reytinqi"),
            ("🗺️ Xəritə Ustaları", "Hər xəritənin ən yüksək win-rate-li top-3 oyunçusu hər Bazar ertəsi elan olunur"),
            ("☕ Tilt Xəbərdarlığı", "3 ardıcıl məğlubiyyətdən sonra həvəsləndirici DM göndərilir"),
            ("✏️ Ad Dəyişmə", "Profil → Ayarlar → Ad Dəyiş düyməsi ilə hər hesab BİR DƏFƏ pulsuz nickini dəyişə bilər"),
            ("📂 Profil Menyusu", "/profile 5 kateqoriyaya bölünüb: Statistika, İnventar, Mükafatlar, Sosial, Ayarlar — hər biri ayrıca alt-menyu açır"),
            ("🎮 Standoff 2 Yenilikləri", "help.standoff2.com saytındakı rəsmi yenilik məqalələri avtomatik aşkarlanıb Azərbaycan dilinə tərcümə edilərək kanala göndərilir (hər 6 saatda yoxlanılır)"),
        ],
    },
    "admin": {
        "label": "Admin",
        "title": "🔧 Admin (Founder / Co-Founder / Head Admin / Admin)",
        "items": [
            ("/scan", "Skor ekranı şəklindən K/A/D oxuyur"),
            ("/matchresult", "Manual 1v1 nəticə qeydi"),
            ("/admin_oyuncu", "Oyunçunun tam profil məlumatını göstərir"),
            ("/admin_duzelt", "Oyunçunun ELO/coin/stat və s. sahəsini dəyişir"),
            ("/admin_matclar", "Son matçların siyahısı"),
            ("/admin_matc_sil", "Bir matçı silib ELO-nu geri qaytarır"),
            ("/admin_matc_elave_et", "İtirilmiş/əl ilə matç nəticəsini ELO+statistika ilə əlavə edir"),
            ("/admin_matc_netice", f"Aktiv matç üçün nəticə düymələrini yenidən göstərir (2 matç paralel gedirsə `matc_no` göstərin)"),
            ("🎮 Paralel matçlar", f"Eyni anda {MAX_PARALLEL_MATCHES} matça qədər paralel oynanıla bilər, hər biri öz thread/səs kanalları ilə"),
            ("/rank_rollari_qur", "ELO rütbə rollarını serverdə yaradır və bütün oyunçulara təyin edir"),
            ("📊 Aktivlik (aşağıdakı düymə)", "Son 7 günün aktivlik statistikasını göstərir"),
            ("📋 Günlük hesabat", "Bot hər gün AZ vaxtı ilə 00:00-da avtomatik günlük statistikanı bu kanala göndərir"),
            ("📰 Nextlevelaz Xəbərləri", "Gündəlik hesabatın ardınca AI (Claude) yazılmış qısa icmal göndərilir"),
            ("🎯 Günün Ortaq Çağırışı", "Hər gün hamı üçün eyni ortaq tapşırıq elan olunur, şərti ödəyən bonus coin qazanır"),
            ("🚫 Ləğv et (matç mesajında)", "Asılı qalan matçı ləğv edir, gəlməyənə ELO cəzası verə bilər"),
            ("/full_setup", "Bütün FACEIT kanallarını avtomatik qurur"),
            ("/setup", "Matchmaking mesajını yaradır"),
            ("/setup_register", "Qeydiyyat mesajını yaradır"),
            ("/setup_rules", "Qaydalar mesajını yaradır"),
            ("/setup_leaderboard", "Leaderboard mesajını yaradıb avtomatik yeniləyir"),
            ("/giveaway_create", "Giveaway yaradır — gizli qalib təyin edə, ya da boş buraxıb əsl-random seçim edə bilərsiniz"),
            ("/admin_herrac_baslat", "Coin ilə hərrac başladır"),
            ("/admin_toplu_coin", "Bir neçə oyunçuya eyni anda coin verir/çıxarır"),
            ("🛡️ Audit Log kanalı", "Bütün admin əməliyyatları (ELO düzəlişi, matç silmə/dəyişmə və s.) canlı qeydə alınır"),
            ("🚩 Reports kanalı", "Profil → Ayarlar → Digər → Şikayət et ilə göndərilən şikayətlər buraya düşür"),
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

    @discord.ui.button(label="Market", style=discord.ButtonStyle.secondary, emoji="🛒", custom_id="panel_market")
    async def market_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch(interaction, "market")

    @discord.ui.button(label="Nailiyyət", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="panel_naliyyet")
    async def naliyyet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._switch(interaction, "naliyyet")

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