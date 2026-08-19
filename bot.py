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
    set_active_match, clear_active_match, get_active_match,
    set_active_match_message, set_match_ready,
    get_active_match_by_message_id, get_all_active_matches, count_active_matches,
    is_player_in_active_match, set_active_match_voice,
    add_combat_stats, record_match_history,
    save_scan_result, get_scan_result, confirm_scan,
    add_coins, get_coins, spend_coins, get_inventory, owns_item, add_to_inventory,
    set_active_banner, get_active_banner, set_active_frame, get_active_frame,
    set_active_theme, get_active_theme, add_coin_log, get_coin_logs,
    refresh_daily_tasks, get_active_daily_tasks, get_player_active_task,
    assign_task_to_player, update_task_progress,
    check_and_grant_achievements, get_player_achievements,
    update_streak, get_streak_bonus,
    get_player_stats_dict, get_player_match_history,
    get_recent_matches, get_match_by_number, delete_match_and_revert,
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
    get_inactive_unplayed_players, delete_player, get_top_elo_player,
    add_skin_to_inventory,
    get_zm_balance, spend_zm,
    add_boost_cards, get_boost_card_counts,
    reset_all_player_data,
    update_bp_mission, add_bp_xp, get_pass_data, has_battle_pass, is_premium_pass,
    buy_battle_pass, get_active_bp_missions,
    BP_XP_PER_LEVEL, BP_MAX_LEVEL, BP_PRICE_AZN, BP_LEVEL_REWARDS, BP_PREMIUM_REWARDS,
    BP_SEASON_NAME, BP_SEASON_NAME_AZ
)
from i18n import t, LANG_NAMES
from ai_chat import generate_match_coach_tip, generate_daily_news, generate_intel_briefing
from leaderboard_image import generate_leaderboard_image
from web_server import run_web_server
from profile_card import generate_profile_card
from match_card import generate_match_card
from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
from rules_card import generate_rules_card, generate_register_banner
from scan_system import ocr_scoreboard, match_to_registered, apply_defaults_for_missing
from market_config import MARKET_ITEMS, get_item_by_id, ELO_CARD_PACKS, get_elo_card_pack
from visual_cards import (
    generate_inventory_card, generate_coin_logs_card,
    generate_tasks_card, generate_achievements_card,
    generate_stats_card, generate_match_history_card,
    generate_map_stats_card, generate_personal_record_card, generate_squad_card,
    generate_activity_card, generate_elo_chart_card, generate_quest_card, generate_synergy_card,
    generate_elo_cards_market_card, generate_monthly_reward_card,
    RANKS, get_rank
)
from referral_visual import generate_item_preview_card
from pass_visual import generate_pass_card, generate_pass_levels_card, generate_pass_announcement, generate_pass_missions_card
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
    "youtube": "https://www.youtube.com/@zenithst2",
    "tiktok": "https://www.tiktok.com/@zenithst2",
    "discord": "https://discord.com/invite/5uTvVKejG7",
    "shop": "https://zenithshop.up.railway.app/",
}

FULL_SETUP_CATEGORY_NAME = "🏆 FACEIT 2v2"

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

LOGO_PATH = "logo.jpg"
DUAL_DAGGERS_IMAGE_PATH = os.path.join("assets", "dual_daggers_grunge.webp")
INACTIVE_REGISTRATION_DAYS = 3
REWARD_CHANNEL_ID = None

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


reward_message_id = None


async def _post_monthly_reward_card(channel):
    """Ayın ELO Çempionu mükafat kartını (bıçaq şəkli + canlı sıralama) kanala göndərib pinləyir,
    əvvəlki bot mesajlarının pinini götürür. Bu mesajı refresh_reward_card loop-u yerində redaktə
    edərək canlı saxlayır (yeni mesaj yox, mövcud mesaj yenilənir)."""
    global reward_message_id
    rows = get_leaderboard(5)
    top_players = [{"nick": r[0], "elo": r[2]} for r in rows]
    card_path = os.path.join(DATA_DIR or ".", "monthly_reward_card.png")
    await asyncio.to_thread(generate_monthly_reward_card, DUAL_DAGGERS_IMAGE_PATH, top_players, card_path)
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

    rows = get_leaderboard(5)
    top_players = [{"nick": r[0], "elo": r[2]} for r in rows]
    card_path = os.path.join(DATA_DIR or ".", "monthly_reward_card.png")
    await asyncio.to_thread(generate_monthly_reward_card, DUAL_DAGGERS_IMAGE_PATH, top_players, card_path)
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
    embed.set_footer(text="Zenith's Academy")
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass


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
    embed.set_footer(text="Zenith's Academy")
    try:
        await member.send(embed=embed)
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
queue_status_channel_id = None
queue_status_message_id = None


LEADERBOARD_IMAGE_PATH = "leaderboard.png"


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
                no_winner_embed.set_footer(text="Zenith's Academy")
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
        final_embed.set_footer(text="Zenith's Academy")
        try:
            await message.edit(embed=final_embed)
        except discord.HTTPException:
            pass
        await channel.send(f"🎉 Təbriklər {winner_mention}! Sən **{mukafat}** qazandın!")


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
    return az_now.weekday() in (5, 6)  # Şənbə, Bazar


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
                    title="📰 Zenith Xəbərləri",
                    description=news_text,
                    color=discord.Color.from_rgb(138, 92, 230)
                )
                news_embed.set_footer(text="Zenith's Academy")
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
                        title="🏆 Zenith Mükafatları",
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

                    # ── Ayın ELO çempionuna bıçaq mükafatı ───────────────────
                    top_elo = get_top_elo_player()
                    if top_elo:
                        add_skin_to_inventory(
                            top_elo["discord_id"], 0, "Dual Daggers | Grunge", 0,
                            image_url=DUAL_DAGGERS_IMAGE_PATH
                        )
                        knife_embed = discord.Embed(
                            title="🔪 Ayın ELO Çempionu — Dual Daggers \"Grunge\"",
                            description=(
                                f"**{top_elo['nick']}** {ended_az_date.strftime('%m.%Y')} ayının son günündə "
                                f"ən yüksək ELO-ya (**{top_elo['elo']}**) sahib oyunçu oldu və mükafat olaraq "
                                f"**Dual Daggers \"Grunge\"** bıçağını qazandı! 🎉\n\n"
                                f"Rəhbərlik tezliklə oyun daxilində təhvil verəcək."
                            ),
                            color=discord.Color.from_rgb(138, 92, 230)
                        )
                        if os.path.exists(DUAL_DAGGERS_IMAGE_PATH):
                            knife_file = discord.File(DUAL_DAGGERS_IMAGE_PATH, filename="dual_daggers_grunge.webp")
                            knife_embed.set_image(url="attachment://dual_daggers_grunge.webp")
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
        self.add_item(discord.ui.Button(label="ZenithShop", emoji="🛒", style=discord.ButtonStyle.link, url=SOCIAL_LINKS["shop"]))


SOCIAL_REMINDER_TEXTS = [
    "Zenith's Academy icmasının bir hissəsi olduğunuz üçün təşəkkürlər! Bizi sosial mediada da izləyin ki, "
    "turnir elanlarını, canlı yayımları və xüsusi endirimləri qaçırmayasınız.",
    "Bilirdinizmi? Bizim YouTube və TikTok hesablarımızda ən gözəl anlar, matç xülasələri və məsləhətlər paylaşılır. "
    "Bir kliklə izləyin, geridə qalmayın!",
    "ZenithShop-da xüsusi əşyalar sizi gözləyir! Aşağıdakı düymələrdən bizim bütün platformalarımıza baş çəkə bilərsiniz.",
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
        title="📢 Zenith's Academy — Bizi izləyin!",
        description=text,
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.add_field(name="▶️ YouTube", value=SOCIAL_LINKS["youtube"], inline=False)
    embed.add_field(name="🎵 TikTok", value=SOCIAL_LINKS["tiktok"], inline=False)
    embed.add_field(name="💬 Discord", value=SOCIAL_LINKS["discord"], inline=False)
    embed.add_field(name="🛒 ZenithShop", value=SOCIAL_LINKS["shop"], inline=False)
    embed.set_footer(text="Zenith's Academy")
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

        await interaction.response.edit_message(view=self)

        active = get_active_match(active["match_number"])
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
        new_bp_levels = []
        challenge_claimers = []

        mvp_id = None
        if stats_by_id:
            mvp_id = max(
                stats_by_id.items(),
                key=lambda kv: kv[1].get("kills", 0) * 2 + kv[1].get("assists", 0) - kv[1].get("deaths", 0)
            )[0]

        def _award_bp_xp(did, nick, s, is_winner):
            """Battle Pass XP: iştirak üçün baza + missiya irəliləyişindən qazanılan XP."""
            xp = 40 if is_winner else 20
            xp += update_bp_mission(did, "matches", 1)
            if is_winner:
                xp += update_bp_mission(did, "wins", 1)
            if did in stats_by_id:
                xp += update_bp_mission(did, "kills", s.get("kills", 0))
                xp += update_bp_mission(did, "assists", s.get("assists", 0))
                if did == mvp_id:
                    xp += update_bp_mission(did, "mvp", 1)
            bp_result = add_bp_xp(did, xp)
            if bp_result.get("rewards"):
                new_bp_levels.append((nick, bp_result))

        for p, r in zip(winner_team, results["winners"]):
            did = p["discord_id"]
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
            _award_bp_xp(did, p["nick"], s, True)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
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
            update_streak(did, False)
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
            _award_bp_xp(did, p["nick"], s, False)
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))
            for ti in check_and_grant_titles(did):
                new_titles.append((p["nick"], ti))
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
        if new_bp_levels:
            embed.add_field(
                name="🎫 Pass Level artdı!",
                value="\n".join(f"**{nick}** → Level {bp['new_level']}" for nick, bp in new_bp_levels),
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

        await _start_match_if_ready(log_channel or interaction.channel, interaction.guild)

    @discord.ui.button(label="Komanda A qalib", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="result_a")
    async def team_a_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_a, self.team_b, "Komanda A", "Komanda B")

    @discord.ui.button(label="Komanda B qalib", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="result_b")
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
        while count_active_matches() < MAX_PARALLEL_MATCHES and queue_size() >= 4:
            started = await _start_one_match(channel, guild)
            if not started:
                break


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

    card_path = os.path.join(DATA_DIR or ".", f"match_{match_number}.png")
    await asyncio.to_thread(
        generate_match_card, match_number, selected_map, team_a, team_b,
        captain_a["discord_id"], captain_b["discord_id"], card_path
    )

    mentions = " ".join([f"<@{p['discord_id']}>" for p in team_a + team_b])
    if is_golden:
        mentions += "\n\n🌟 **QIZIL MATÇ!** Bu matçda ELO və Coin dəyişimi 2x-dir!"
    if is_lightning:
        mentions += "\n\n⚡ **İldırım Turu davam edir!** Bu matçda ELO və Coin əlavə 2x-dir!"
    ready_view = TeamReadyView(team_a, team_b)
    sent_message = await channel.send(
        content=mentions,
        file=discord.File(card_path, filename="match.png"),
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
        announce_embed.set_footer(text="Zenith's Academy")
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
            voice_a_channel = await guild.create_voice_channel(f"🔵 M{match_number}-A", category=category)
            voice_b_channel = await guild.create_voice_channel(f"🔴 M{match_number}-B", category=category)
            set_active_match_voice(
                match_number,
                voice_a_channel.id if voice_a_channel else None,
                voice_b_channel.id if voice_b_channel else None
            )
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


class MatchmakingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="2v2", style=discord.ButtonStyle.danger, emoji="🔥", custom_id="mm_join")
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        added = add_to_queue(discord_id, nick, elo)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()
        active_count = count_active_matches()
        if active_count >= MAX_PARALLEL_MATCHES:
            await interaction.response.send_message(
                f"✅ {nick} sıraya qoşuldu! ({size}/4)\n"
                f"⏳ Hazırda {active_count}/{MAX_PARALLEL_MATCHES} matç paralel davam edir — "
                "yer boşalan kimi növbəti matç avtomatik başlayacaq.",
                ephemeral=True
            )
            await update_queue_status_message()
            return

        await interaction.response.send_message(f"✅ {nick} sıraya qoşuldu! ({size}/4)", ephemeral=True)
        await update_queue_status_message()
        await _start_match_if_ready(interaction.channel, interaction.guild)

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


@bot.event
async def on_ready():
    global LOG_CHANNEL_ID, REWARD_CHANNEL_ID
    init_db()

    saved_log = get_meta("log_channel_id")
    if saved_log:
        LOG_CHANNEL_ID = int(saved_log)
    saved_reward = get_meta("reward_channel_id")
    if saved_reward:
        REWARD_CHANNEL_ID = int(saved_reward)
    print(f"[CONFIG] LOG_CHANNEL_ID={LOG_CHANNEL_ID} REWARD_CHANNEL_ID={REWARD_CHANNEL_ID}", flush=True)

    if os.environ.get("RESET_SQUADS_ON_BOOT") == "1":
        n = wipe_squads()
        print(f"[RESET_SQUADS] {n} squad/dəvət sətri silindi.", flush=True)

    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView())
    bot.add_view(RegisterView())
    bot.add_view(TeamReadyView())
    bot.add_view(SquadInviteView())
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
    embed = discord.Embed(
        title=f"👋 Xoş gəldin, {member.name}!",
        description=(
            f"**{member.guild.name}** — Standoff 2 FACEIT 2v2 icması!\n\n"
            "**Necə başlamaq olar:**\n"
            "1️⃣ Qeydiyyat kanalındakı **Qeydiyyat** düyməsini bas (ya da `/register`)\n"
            "2️⃣ Matchmaking kanalında **Sıraya qoşul** ilə 2v2 sıraya yaz\n"
            "3️⃣ `/profile` ilə profilini, ELO-nu və statistikanı izlə\n\n"
            "Sual üçün rəhbərliklə əlaqə saxlaya bilərsən. Uğurlar! 🎮"
        ),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.set_footer(text="Zenith's Academy")
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass


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


class ProfileHubView(discord.ui.View):
    def __init__(self, discord_id, lang="az"):
        super().__init__(timeout=300)
        self.discord_id = discord_id
        self.lang = lang

        button_defs = [
            ("btn.stats", "📊", self.stats_btn),
            ("btn.history", "📜", self.history_btn),
            ("btn.inventory", "🎒", self.inventory_btn),
            ("btn.market", "🛒", self.market_btn),
            ("btn.coins", "💰", self.coins_btn),
            ("btn.achievements", "🏆", self.achievements_btn),
            ("btn.daily", "📅", self.gunluk_btn),
            ("btn.maps", "🗺️", self.maps_btn),
            ("btn.record", "🥇", self.record_btn),
            ("btn.squad", "🤝", self.squad_btn),
            ("btn.share", "🔗", self.share_btn),
            ("btn.chart", "📈", self.elo_chart_btn),
            ("btn.title", "🏅", self.title_btn),
            ("btn.quests", "🧗", self.quests_btn),
            ("btn.synergy", "🔍", self.synergy_btn),
            ("btn.pass", "🎫", self.pass_btn),
            ("btn.lang", "🌐", self.lang_btn),
        ]
        for key, emoji, callback in button_defs:
            btn = discord.ui.Button(label=t(key, lang), style=discord.ButtonStyle.secondary, emoji=emoji)
            btn.callback = callback
            self.add_item(btn)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu yalnız profil sahibi üçündür.", ephemeral=True)
            return False
        return True

    def _display_name(self, interaction: discord.Interaction) -> str:
        member = interaction.guild.get_member(self.discord_id) if interaction.guild else None
        return member.display_name if member else str(self.discord_id)

    async def stats_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_stats(interaction, self.discord_id)

    async def history_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_history(interaction, self.discord_id)

    async def inventory_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_inventory(interaction, self.discord_id)

    async def market_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_market(interaction, self.discord_id)

    async def pass_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_pass(interaction, self.discord_id)

    async def coins_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_coins(interaction, self.discord_id)

    async def achievements_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_achievements(interaction, self.discord_id, self._display_name(interaction))

    async def gunluk_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_gunluk(interaction, self.discord_id)

    async def maps_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_maps(interaction, self.discord_id, self._display_name(interaction))

    async def record_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_record(interaction, self.discord_id, self._display_name(interaction))

    async def squad_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_squad(interaction, self.discord_id, self._display_name(interaction))

    async def share_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        link = f"{PUBLIC_WEB_URL}/u/{self.discord_id}"
        await interaction.response.send_message(
            f"🔗 İctimai profil linkiniz:\n{link}", ephemeral=True
        )

    async def elo_chart_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_elo_chart(interaction, self.discord_id, self._display_name(interaction))

    async def title_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_titles(interaction, self.discord_id, self._display_name(interaction))

    async def quests_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_quests(interaction, self.discord_id, self._display_name(interaction))

    async def synergy_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await _render_synergy(interaction, self.discord_id, self._display_name(interaction))

    async def lang_btn(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            t("lang.select_placeholder", self.lang), view=LanguageSelectView(self.discord_id), ephemeral=True
        )


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
    pass_data = get_pass_data(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"profile_{discord_id}.png")
    await asyncio.to_thread(
        generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path,
        banner_path=banner_path, coins=stats.get("coins", 0), frame_path=frame_path,
        zm_balance=stats.get("zm_balance", 0),
        kills=stats.get("kills", 0), assists=stats.get("assists", 0), deaths=stats.get("deaths", 0),
        theme_colors=theme_colors, title=get_active_title_name(discord_id), lang=player_lang,
        pass_status="premium" if pass_data["is_premium"] else "free", pass_level=pass_data["level"]
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

    message = await channel.send(
        content="🏆 **Zenith's Academy FACEIT Leaderboard** — hər 60 saniyədə avtomatik yenilənir.",
        file=discord.File(LEADERBOARD_IMAGE_PATH, filename="leaderboard.png")
    )

    leaderboard_channel_id = channel.id
    leaderboard_message_id = message.id

    if not refresh_leaderboard.is_running():
        refresh_leaderboard.start()


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


@bot.tree.command(name="full_setup", description="[Admin] FACEIT 2v2 kanallarını silib yenilənmiş formada təzədən qurur")
@staff_check()
async def full_setup(interaction: discord.Interaction):
    global LOG_CHANNEL_ID, REWARD_CHANNEL_ID

    if not interaction.guild:
        await interaction.response.send_message("❌ Bu komanda yalnız serverdə işləyir.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    category = discord.utils.get(guild.categories, name=FULL_SETUP_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(FULL_SETUP_CATEGORY_NAME)

    announce_overwrites = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False)
    }

    async def _recreate_text(name, overwrites=None):
        existing = discord.utils.get(category.text_channels, name=name)
        if existing:
            try:
                await existing.delete(reason="full_setup: yenilənmiş formada yenidən qurulur")
            except discord.Forbidden:
                pass
        return await guild.create_text_channel(name, category=category, overwrites=overwrites or {})

    # Ay sonu mükafat kanalı ən üstdə olsun deyə digərlərindən ƏVVƏL yaradılır
    # (Discord yeni kanallara ardıcıl artan mövqe verir — kateqoriyada birinci yaranan üstdə görünür).
    ch_reward = await _recreate_text("ay-sonu-mukafati", announce_overwrites)
    ch_register = await _recreate_text("faceit-qeydiyyat", announce_overwrites)
    ch_matchmaking = await _recreate_text("matchmaking", announce_overwrites)
    ch_rules = await _recreate_text("faceit-qaydalari", announce_overwrites)
    ch_leaderboard = await _recreate_text("leaderboard", announce_overwrites)
    ch_pass = await _recreate_text(f"pass-{BP_SEASON_NAME.lower()}", announce_overwrites)
    ch_log = await _recreate_text("faceit-log")

    # Köhnə statik "Komanda A/B" səs kanalları artıq lazım deyil — hər matç
    # üçün səs kanalları indi avtomatik, dinamik yaradılır/silinir (bax:
    # _start_one_match/_cleanup_match_voice_channels). Əvvəllər bu komanda
    # yaratmış ola biləcəyi köhnə statik kanallar varsa təmizlənir.
    for stale_name in ("🔵 Komanda A", "🔴 Komanda B"):
        stale = discord.utils.get(category.voice_channels, name=stale_name)
        if stale:
            try:
                await stale.delete(reason="full_setup: statik komanda kanalları artıq istifadə olunmur")
            except discord.Forbidden:
                pass

    LOG_CHANNEL_ID = ch_log.id
    set_meta("log_channel_id", ch_log.id)
    REWARD_CHANNEL_ID = ch_reward.id
    set_meta("reward_channel_id", ch_reward.id)

    await _post_register(ch_register)
    await _post_matchmaking(ch_matchmaking)
    await _post_rules(ch_rules)
    await _post_leaderboard(ch_leaderboard)
    await _post_monthly_reward_card(ch_reward)
    await _post_pass_showcase(ch_pass)

    await interaction.followup.send(
        "✅ Server yenidən quruldu! Köhnə FACEIT kanalları silinib, yenilənmiş formada təzədən yaradıldı.\n\n"
        f"🔪 Ay sonu mükafatı: {ch_reward.mention} (ən üstdə, pinlənmiş kart canlı yenilənir)\n"
        f"📋 Qeydiyyat: {ch_register.mention}\n"
        f"🎮 Matchmaking: {ch_matchmaking.mention}\n"
        f"📜 Qaydalar: {ch_rules.mention}\n"
        f"🏆 Leaderboard: {ch_leaderboard.mention}\n"
        f"🎫 Battle Pass ({BP_SEASON_NAME}): {ch_pass.mention} (pinlənmiş tanıtım kartı)\n"
        f"📰 Faceit log: {ch_log.mention} (hamı görüb yaza bilər)\n"
        f"🔊 Səs kanalları: hər matç üçün avtomatik yaradılır/silinir (statik kanal lazım deyil)\n\n"
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
    embed.set_footer(text="Zenith's Academy")

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
            desc = "Artıq sahibsiniz" if owned else f"{item['price']} coin"
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
        balance = get_coins(self.discord_id)
        if balance < item["price"]:
            await interaction.response.send_message(
                f"❌ Balansınız kifayət etmir. **{item['name']}** — {item['price']} coin, sizdə **{balance}** coin var.",
                ephemeral=True
            )
            return
        spend_coins(self.discord_id, item["price"])
        add_to_inventory(self.discord_id, item["id"])
        new_bal = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -item["price"], f"Market alışı: {item['name']}", "spend", new_bal)
        await interaction.response.send_message(
            f"✅ **{item['name']}** alındı! Qalan balans: **{new_bal}** coin.\nProfil → İnventar düyməsindən aktiv edə bilərsiniz.",
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
            value = "✅ Sahibsiniz" if owned else f"**{item['price']} coin**"
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


async def _render_market(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    balance = get_coins(discord_id)
    azn_balance = get_zm_balance(discord_id)
    embed = discord.Embed(
        title="🛒 Zenith's Academy Market",
        description=f"Balansınız: **{balance} coin**\n💵 **{azn_balance:.2f} AZN**\n\nBir kataqoriya seçin:",
        color=discord.Color.from_rgb(138, 92, 230)
    )
    view = MarketCategoryView(discord_id)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class PassView(discord.ui.View):
    def __init__(self, discord_id, is_premium):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        self.is_premium = is_premium
        if is_premium:
            self.buy_btn.disabled = True
            self.buy_btn.label = "VIP Pass sahibisiniz"

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message(
                "❌ Bu pass yalnız sizin üçündür — Profil → Pass düyməsi ilə özününüzü açın.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Bütün Levellər", style=discord.ButtonStyle.secondary, emoji="📋")
    async def levels_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        pass_data = get_pass_data(self.discord_id)
        card_path = os.path.join(DATA_DIR or ".", f"pass_levels_{self.discord_id}.png")
        await asyncio.to_thread(generate_pass_levels_card, pass_data, card_path)
        await interaction.followup.send(file=discord.File(card_path, filename="pass_levels.png"), ephemeral=True)

    @discord.ui.button(label="Missiyalar", style=discord.ButtonStyle.secondary, emoji="🎯")
    async def missions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        missions = get_active_bp_missions(self.discord_id)
        card_path = os.path.join(DATA_DIR or ".", f"pass_missions_{self.discord_id}.png")
        await asyncio.to_thread(generate_pass_missions_card, missions, card_path)
        await interaction.followup.send(file=discord.File(card_path, filename="pass_missions.png"), ephemeral=True)

    @discord.ui.button(label="Çərçivə/Banner Önizlə", style=discord.ButtonStyle.secondary, emoji="👁️")
    async def preview_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        avatar_bytes = None
        try:
            avatar_url = interaction.user.display_avatar.replace(size=256).url
            resp = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
            avatar_bytes = resp.content
        except Exception:
            avatar_bytes = None

        files = []
        for item_id in ("frame_genesis", "banner_genesis"):
            item = get_item_by_id(item_id)
            if not item:
                continue
            preview_path = os.path.join(DATA_DIR or ".", f"pass_preview_{self.discord_id}_{item_id}.png")
            await asyncio.to_thread(generate_item_preview_card, interaction.user.display_name, avatar_bytes, item, preview_path)
            files.append(discord.File(preview_path, filename=f"{item_id}.png"))

        if not files:
            await interaction.followup.send("❌ Önizləmə hazırlana bilmədi.", ephemeral=True)
            return
        await interaction.followup.send(
            content="🎫 **Genesis VIP Pass** — Level 15 Çərçivə və Level 20 Banner önizləməsi:",
            files=files, ephemeral=True
        )

    @discord.ui.button(label="VIP Pass Al", style=discord.ButtonStyle.success, emoji="💎")
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        if self.is_premium:
            await interaction.response.send_message("✅ Artıq VIP Pass sahibisiniz!", ephemeral=True)
            return
        ok, msg = buy_battle_pass(self.discord_id)
        if ok:
            self.is_premium = True
            button.disabled = True
            button.label = "VIP Pass sahibisiniz"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ {msg}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)


async def _post_pass_showcase(channel):
    """Sezonun (Genesis) tanıtım kartını kanala göndərib pinləyir — statik məzmun,
    canlı yenilənən deyil (yalnız full_setup hər işə düşdükdə təzələnir)."""
    card_path = os.path.join(DATA_DIR or ".", "pass_announcement.png")
    await asyncio.to_thread(generate_pass_announcement, card_path)
    embed = discord.Embed(
        title=f"🎫 Battle Pass — {BP_SEASON_NAME} ({BP_SEASON_NAME_AZ})",
        description=(
            f"Zenith's Academy-nin yeni sezonu **{BP_SEASON_NAME} ({BP_SEASON_NAME_AZ})** başladı!\n\n"
            "Matç oynayaraq, qazanaraq və missiyaları tamamlayaraq XP toplayın, Level artırın "
            "və **35 levelə qədər** mükafatlar qazanın.\n\n"
            f"🆓 **FREE Pass** — hər leveldə coin, milestone-larda (5-35) ELO kartları\n"
            f"💎 **VIP Pass** ({BP_PRICE_AZN} AZN) — Çərçivə (Lv.15), Banner (Lv.20), "
            f"AWM Boom skini (Lv.{BP_MAX_LEVEL}) + AZN/Coin/ELO kart bonusları\n\n"
            "`/pass` komandası ilə öz statusunuzu görüb VIP Pass ala bilərsiniz."
        ),
        color=discord.Color.from_rgb(138, 92, 230)
    )
    embed.set_image(url="attachment://pass_announcement.png")
    message = await channel.send(embed=embed, file=discord.File(card_path, filename="pass_announcement.png"))
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


async def _render_pass(interaction: discord.Interaction, discord_id: int):
    await interaction.response.defer(ephemeral=True)
    pass_data = get_pass_data(discord_id)
    missions = get_active_bp_missions(discord_id)
    card_path = os.path.join(DATA_DIR or ".", f"pass_{discord_id}.png")
    await asyncio.to_thread(generate_pass_card, pass_data, missions, card_path)
    view = PassView(discord_id, pass_data["is_premium"])
    await interaction.followup.send(file=discord.File(card_path, filename="pass.png"), view=view, ephemeral=True)


@bot.tree.command(name="pass", description="Battle Pass statusunuzu göstərir")
async def pass_cmd(interaction: discord.Interaction):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    await _render_pass(interaction, interaction.user.id)


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
    for p, r in zip(winner_team, results["winners"]):
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
        for ti in check_and_grant_titles(p["discord_id"]):
            new_titles.append((p["nick"], ti))
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
        update_streak(p["discord_id"], False)
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
        for ti in check_and_grant_titles(p["discord_id"]):
            new_titles.append((p["nick"], ti))
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

    winner_label = "Komanda A" if qalib.value == "A" else "Komanda B"
    loser_label = "Komanda B" if qalib.value == "A" else "Komanda A"

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

    players = get_all_players(limit=1000)
    for p in players:
        await _sync_rank_role(guild, p["discord_id"], p["elo"])

    await interaction.followup.send(
        f"✅ Rütbə rolları hazırdır.\n"
        f"🆕 Yaradılan rollar: {', '.join(created) if created else 'yoxdur (artıq mövcud idi)'}\n"
        f"🔄 {len(players)} oyunçunun rolu yeniləndi.",
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
            ("/pass", f"Battle Pass statusunuzu (level, XP, missiyalar) göstərir — VIP Pass ({BP_PRICE_AZN} AZN) da düymə ilə buradan alınır"),
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
            ("🏆 Zenith Mükafatları", "Hər ayın 1-də keçən ayın MVP-si, ən inkişaf edəni və ən aktivi elan olunur"),
            ("⚡ İldırım Turu", f"Təsadüfi olaraq {LIGHTNING_ROUND_DURATION_MINUTES} dəqiqəlik əlavə 2x ELO/Coin dövrü elan oluna bilər"),
            ("🎮 Matç Başlama Elanı", "Hər yeni matçda kapitanların adı/ID-si elan kanalına avtomatik göndərilir — lobbi tez qurulsun deyə"),
            ("🗑️ Qeydiyyat təmizliyi",
             f"Qeydiyyatdan {INACTIVE_REGISTRATION_DAYS} gün keçməsinə baxmayaraq heç bir matç oynamayan "
             "oyunçunun qeydiyyatı avtomatik silinir (istəsə yenidən qeydiyyatdan keçə bilər)"),
            ("🔪 Ayın ELO Çempionu",
             "Hər ayın son günü ən yüksək ELO-ya sahib oyunçu Dual Daggers \"Grunge\" bıçağını qazanır"),
            ("🔪 Ay sonu mükafatı kanalı",
             "Serverin ən üstündəki kanalda mükafatın şəkli/qaydaları pinlənir, Top-5 sıralama "
             "həmin mesajda hər 5 dəqiqədən bir avtomatik yenilənir (yeni mesaj yox)"),
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
            ("📰 Zenith Xəbərləri", "Gündəlik hesabatın ardınca AI (Claude) yazılmış qısa icmal göndərilir"),
            ("🎯 Günün Ortaq Çağırışı", "Hər gün hamı üçün eyni ortaq tapşırıq elan olunur, şərti ödəyən bonus coin qazanır"),
            ("🚫 Ləğv et (matç mesajında)", "Asılı qalan matçı ləğv edir, gəlməyənə ELO cəzası verə bilər"),
            ("/full_setup", "Bütün FACEIT kanallarını avtomatik qurur"),
            ("/setup", "Matchmaking mesajını yaradır"),
            ("/setup_register", "Qeydiyyat mesajını yaradır"),
            ("/setup_rules", "Qaydalar mesajını yaradır"),
            ("/setup_leaderboard", "Leaderboard mesajını yaradıb avtomatik yeniləyir"),
            ("/giveaway_create", "Giveaway yaradır — gizli qalib təyin edə, ya da boş buraxıb əsl-random seçim edə bilərsiniz"),
        ],
    },
}


def _build_panel_embed(category_key: str) -> discord.Embed:
    cat = PANEL_CATEGORIES[category_key]
    embed = discord.Embed(title=cat["title"], color=discord.Color.from_rgb(138, 92, 230))
    for name, desc in cat["items"]:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="Zenith's Academy")
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