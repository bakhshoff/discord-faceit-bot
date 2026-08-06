import sys
import io

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
    add_combat_stats, record_match_history,
    save_scan_result, get_scan_result, confirm_scan,
    add_coins, get_coins, spend_coins, get_inventory, owns_item, add_to_inventory,
    set_active_banner, get_active_banner, set_active_frame, get_active_frame,
    set_active_theme, get_active_theme, add_coin_log, get_coin_logs,
    refresh_daily_tasks, get_active_daily_tasks, get_player_active_task,
    assign_task_to_player, update_task_progress,
    check_and_grant_achievements, get_player_achievements,
    update_streak, get_streak_bonus
)
from leaderboard_image import generate_leaderboard_image
from web_server import run_web_server
from profile_card import generate_profile_card
from match_card import generate_match_card
from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
from rules_card import generate_rules_card, generate_register_banner
from scan_system import ocr_scoreboard, match_to_registered, apply_defaults_for_missing
from market_config import MARKET_ITEMS, get_item_by_id
from visual_cards import (
    generate_inventory_card, generate_coin_logs_card,
    generate_tasks_card, generate_achievements_card
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

TEAM_A_VOICE_ID = 1500827030890221678
TEAM_B_VOICE_ID = 1500827032261496913
LOG_CHANNEL_ID = 1500790545172267028

FULL_SETUP_CATEGORY_NAME = "🏆 FACEIT 2v2"

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

LOGO_PATH = "logo.jpg"

GREEN_ACCENT = (95, 208, 122)
GOLD_ACCENT = (240, 180, 41)
RED_ACCENT = (214, 69, 61)

# Matchmaking üçün açıq saatlar (Azərbaycan vaxtı, UTC+4)
QUEUE_OPEN_HOUR = 20   # 20:00
QUEUE_CLOSE_HOUR = 2   # 02:00

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


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
        winner_member = guild.get_member(winner_id) if guild else None
        winner_mention = winner_member.mention if winner_member else f"<@{winner_id}>"

        final_embed = discord.Embed(
            title="🎉 GIVEAWAY BİTDİ 🎉",
            description=f"**Mükafat:** {mukafat}\n\n🏆 Qalib: {winner_mention}\n\nTəbriklər!",
            color=discord.Color.green()
        )
        final_embed.set_footer(text="Calestify Gaming Community")
        try:
            await message.edit(embed=final_embed)
        except discord.HTTPException:
            pass
        await channel.send(f"🎉 Təbriklər {winner_mention}! Sən **{mukafat}** qazandın!")


@tasks.loop(seconds=3600)
async def refresh_tasks_loop():
    refresh_daily_tasks()


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
    def __init__(self, match_number, team_a, team_b, captain_a_id, captain_b_id):
        super().__init__(timeout=None)
        self.match_number = match_number
        self.team_a = team_a
        self.team_b = team_b
        self.captain_a_id = captain_a_id
        self.captain_b_id = captain_b_id
        self.team_a_ready = False
        self.team_b_ready = False

    async def _set_ready(self, interaction: discord.Interaction, is_team_a: bool, button: discord.ui.Button):
        expected_captain_id = self.captain_a_id if is_team_a else self.captain_b_id
        if interaction.user.id != expected_captain_id:
            await interaction.response.send_message("❌ Bu düyməni yalnız öz komandanızın kapitanı basa bilər.", ephemeral=True)
            return

        if is_team_a:
            self.team_a_ready = True
            button.disabled = True
            button.label = "Komanda A Hazırdır ✅"
        else:
            self.team_b_ready = True
            button.disabled = True
            button.label = "Komanda B Hazırdır ✅"

        await interaction.response.edit_message(view=self)

        if self.team_a_ready and self.team_b_ready:
            log_embed = discord.Embed(
                title=f"✅ Matç No{self.match_number} — Hər iki komanda hazır",
                description="Admin/moderator nəticəni aşağıdaki düymələrlə qeyd etməlidir.",
                color=discord.Color.blurple()
            )
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                result_view = MatchResultView(self.match_number, self.team_a, self.team_b)
                await log_channel.send(embed=log_embed, view=result_view)

    @discord.ui.button(label="Komanda A Hazır", style=discord.ButtonStyle.primary, custom_id="ready_a")
    async def team_a_ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set_ready(interaction, True, button)

    @discord.ui.button(label="Komanda B Hazır", style=discord.ButtonStyle.danger, custom_id="ready_b")
    async def team_b_ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set_ready(interaction, False, button)


class MatchResultView(discord.ui.View):
    def __init__(self, match_number, team_a, team_b):
        super().__init__(timeout=None)
        self.match_number = match_number
        self.team_a = team_a
        self.team_b = team_b
        self.finished = False

    async def _finish(self, interaction: discord.Interaction, winner_team, loser_team, winner_label, loser_label):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return

        if self.finished:
            await interaction.response.send_message("⚠️ Bu matçın nəticəsi artıq qeyd olunub.", ephemeral=True)
            return

        winner_ids = [p["discord_id"] for p in winner_team]
        loser_ids = [p["discord_id"] for p in loser_team]

        results = update_team_elo(winner_ids, loser_ids)
        if results is None:
            await interaction.response.send_message("❌ Xəta: oyunçu məlumatları tapılmadı.", ephemeral=True)
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

        # Coin mükafatı, seriya, günlük tapşırıq irəliləyişi, nailiyyətlər
        new_achievements = []
        for p, r in zip(winner_team, results["winners"]):
            did = p["discord_id"]
            streak, _ = update_streak(did, True)
            bonus_coins, _bonus_elo = get_streak_bonus(streak)
            earned = random.randint(5, 10) + bonus_coins
            new_bal = add_coins(did, earned)
            reason = f"Matç No{self.match_number} qələbə" + (f" (seriya {streak})" if bonus_coins else "")
            add_coin_log(did, earned, reason, "earn", new_bal)
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))

        for p, r in zip(loser_team, results["losers"]):
            did = p["discord_id"]
            update_streak(did, False)
            earned = random.randint(0, 5)
            new_bal = add_coins(did, earned)
            add_coin_log(did, earned, f"Matç No{self.match_number} iştirak", "earn", new_bal)
            s = stats_by_id.get(did, {})
            update_task_progress(did, s.get("kills", 0), s.get("assists", 0))
            for ach in check_and_grant_achievements(did):
                new_achievements.append((p["nick"], ach))

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        embed = discord.Embed(
            title=f"✅ Matç No{self.match_number} — Nəticə qeyd edildi",
            description=f"🗓️ {now.strftime('%d.%m.%Y %H:%M')} (AZ vaxtı)\n🏆 Qalib: **{winner_label}**",
            color=discord.Color.gold()
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

        await asyncio.to_thread(
            record_match_history, "2v2", winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]], [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]], [r["new_elo"] for r in results["losers"]],
            self.match_number
        )
        clear_active_match()

        await interaction.response.edit_message(embed=embed, view=self)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel and log_channel.id != interaction.channel.id:
            await log_channel.send(embed=embed)

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
        if not interaction.user.guild_permissions.administrator:
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
        if not interaction.user.guild_permissions.administrator:
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
@app_commands.checks.has_permissions(administrator=True)
async def scan_cmd(interaction: discord.Interaction):
    active = get_active_match()
    if not active:
        await interaction.response.send_message("❌ Aktiv matç yoxdur.", ephemeral=True)
        return

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
    if isinstance(error, app_commands.MissingPermissions):
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

        discord_id, nick, so2_id, elo, wins, losses = player[:6]
        added = add_to_queue(discord_id, nick, elo)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()
        await interaction.response.send_message(f"✅ {nick} sıraya qoşuldu! ({size}/4)", ephemeral=True)
        await update_queue_status_message()

        if size >= 4:
            result = pop_4_and_balance()
            if result is None:
                return
            team_a, team_b, captain_a, captain_b = result
            selected_map = random.choice(MAPS)
            match_number = get_next_match_number()

            set_active_match(
                match_number,
                team_a_json=json.dumps(team_a, ensure_ascii=False),
                team_b_json=json.dumps(team_b, ensure_ascii=False),
                selected_map=selected_map
            )

            card_path = os.path.join(DATA_DIR or ".", f"match_{match_number}.png")
            await asyncio.to_thread(
                generate_match_card, match_number, selected_map, team_a, team_b,
                captain_a["discord_id"], captain_b["discord_id"], card_path
            )

            mentions = " ".join([f"<@{p['discord_id']}>" for p in team_a + team_b])
            ready_view = TeamReadyView(match_number, team_a, team_b, captain_a["discord_id"], captain_b["discord_id"])
            await interaction.channel.send(
                content=mentions,
                file=discord.File(card_path, filename="match.png"),
                view=ready_view
            )

            team_a_channel = bot.get_channel(TEAM_A_VOICE_ID)
            team_b_channel = bot.get_channel(TEAM_B_VOICE_ID)

            for p in team_a:
                member = interaction.guild.get_member(p["discord_id"])
                if member and member.voice and team_a_channel:
                    try:
                        await member.move_to(team_a_channel)
                    except discord.Forbidden:
                        pass

            for p in team_b:
                member = interaction.guild.get_member(p["discord_id"])
                if member and member.voice and team_b_channel:
                    try:
                        await member.move_to(team_b_channel)
                    except discord.Forbidden:
                        pass

            await update_queue_status_message()

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
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        clear_queue()
        await interaction.response.send_message("🧹 Sıra tam təmizləndi.", ephemeral=True)
        await update_queue_status_message()


@bot.event
async def on_ready():
    init_db()
    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView())
    bot.add_view(RegisterView())
    if not check_giveaways.is_running():
        check_giveaways.start()
    refresh_daily_tasks()
    if not refresh_tasks_loop.is_running():
        refresh_tasks_loop.start()
    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"[SYNC] {guild.name} üçün komandalar dərhal sinxronlaşdı.", flush=True)

    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("[SYNC] Qlobal komandalar təmizləndi (dublikatların qarşısı alındı).", flush=True)


@bot.tree.command(name="profile", description="Profilinizi göstərir")
async def profile(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return

    await interaction.response.defer()

    discord_id, nick, so2_id, elo, wins, losses = player[:6]

    avatar_bytes = None
    try:
        avatar_url = interaction.user.display_avatar.replace(size=256).url
        avatar_bytes = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
        avatar_bytes = avatar_bytes.content
    except Exception:
        avatar_bytes = None

    card_path = os.path.join(DATA_DIR or ".", f"profile_{discord_id}.png")
    await asyncio.to_thread(generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path)

    await interaction.followup.send(file=discord.File(card_path, filename="profile.png"))


@bot.tree.command(name="matchresult", description="[Admin] Matç nəticəsini qeyd edir və ELO-nu yeniləyir")
@app_commands.describe(qalib="Qalib oyunçu", məğlub="Məğlub oyunçu")
@app_commands.checks.has_permissions(administrator=True)
async def matchresult(interaction: discord.Interaction, qalib: discord.Member, məğlub: discord.Member):
    if not get_player(qalib.id) or not get_player(məğlub.id):
        await interaction.response.send_message("❌ Hər iki oyunçu əvvəlcə `/register` etməlidir.", ephemeral=True)
        return

    result = update_elo(qalib.id, məğlub.id)

    embed = discord.Embed(title="🏆 Matç nəticəsi qeyd edildi", color=discord.Color.gold())
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
    if isinstance(error, app_commands.MissingPermissions):
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
        "accent": GOLD_ACCENT,
    },
    {
        "title": "Matç tapılanda",
        "body": "Bot avtomatik komandaları (ELO-ya görə balanslaşdırılmış) və kapitanları elan edir, oyunçuları uyğun səs kanallarına köçürür. Oyunçular vaxtında qoşulmalıdır.",
        "accent": GOLD_ACCENT,
    },
    {
        "title": "ELO sistemi",
        "body": "Matç nəticəsi moderator tərəfindən /matchresult ilə qeyd olunur. ELO dəyişimi FACEIT-ə bənzər dinamik sistemlə hesablanır — ELO fərqi nə qədər böyükdürsə, dəyişim də ona uyğun azalır/artır. Qalib ELO qazanır, məğlub ELO itirir.",
        "accent": GOLD_ACCENT,
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
        "accent": GOLD_ACCENT,
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
@app_commands.checks.has_permissions(administrator=True)
async def setup_rules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_rules(interaction.channel)
    await interaction.followup.send("✅ Qaydalar mesajı yaradıldı.", ephemeral=True)


@setup_rules.error
async def setup_rules_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_leaderboard", description="[Admin] Leaderboard mesajını bu kanalda yaradır və avtomatik yeniləməyə başlayır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_leaderboard(interaction.channel)
    await interaction.followup.send("✅ Leaderboard mesajı yaradıldı, avtomatik yenilənəcək.", ephemeral=True)


@setup_leaderboard.error
async def setup_leaderboard_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_register", description="[Admin] Qeydiyyat mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_register(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_register(interaction.channel)
    await interaction.followup.send("✅ Qeydiyyat mesajı yaradıldı.", ephemeral=True)


@setup_register.error
async def setup_register_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup", description="[Admin] Matchmaking mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await _post_matchmaking(interaction.channel)
    await interaction.followup.send("✅ Matchmaking mesajı yaradıldı.", ephemeral=True)


@setup.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="full_setup", description="[Admin] Bütün FACEIT 2v2 kanallarını, mesajlarını və access-lərini avtomatik qurur")
@app_commands.checks.has_permissions(administrator=True)
async def full_setup(interaction: discord.Interaction):
    global LOG_CHANNEL_ID, TEAM_A_VOICE_ID, TEAM_B_VOICE_ID

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
    log_overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    async def _get_or_create_text(name, overwrites=None):
        existing = discord.utils.get(category.text_channels, name=name)
        if existing:
            return existing
        return await guild.create_text_channel(name, category=category, overwrites=overwrites or {})

    async def _get_or_create_voice(name):
        existing = discord.utils.get(category.voice_channels, name=name)
        if existing:
            return existing
        return await guild.create_voice_channel(name, category=category)

    ch_register = await _get_or_create_text("faceit-qeydiyyat", announce_overwrites)
    ch_matchmaking = await _get_or_create_text("matchmaking", announce_overwrites)
    ch_rules = await _get_or_create_text("faceit-qaydalari", announce_overwrites)
    ch_leaderboard = await _get_or_create_text("leaderboard", announce_overwrites)
    ch_log = await _get_or_create_text("faceit-log", log_overwrites)
    vc_a = await _get_or_create_voice("🔵 Komanda A")
    vc_b = await _get_or_create_voice("🔴 Komanda B")

    LOG_CHANNEL_ID = ch_log.id
    TEAM_A_VOICE_ID = vc_a.id
    TEAM_B_VOICE_ID = vc_b.id

    await _post_register(ch_register)
    await _post_matchmaking(ch_matchmaking)
    await _post_rules(ch_rules)
    await _post_leaderboard(ch_leaderboard)

    await interaction.followup.send(
        "✅ Server tam quruldu!\n\n"
        f"📋 Qeydiyyat: {ch_register.mention}\n"
        f"🎮 Matchmaking: {ch_matchmaking.mention}\n"
        f"📜 Qaydalar: {ch_rules.mention}\n"
        f"🏆 Leaderboard: {ch_leaderboard.mention}\n"
        f"🔒 Admin log: {ch_log.mention} (yalnız adminlər görür)\n"
        f"🔊 Səs kanalları: {vc_a.mention}, {vc_b.mention}\n\n"
        "Elan kanallarında adi üzvlər yazı yaza bilmir, yalnız düymələrlə əməliyyat edə bilirlər.",
        ephemeral=True
    )


@full_setup.error
async def full_setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="giveaway_create", description="[Admin] Gizli qalibli giveaway yaradır")
@app_commands.describe(
    mukafat="Mükafatın adı (məs: 1000 Gold)",
    saat="Çəkilişin neçə saat sürəcəyi (0 ola bilər)",
    deqiqe="Çəkilişin neçə dəqiqə sürəcəyi (0 ola bilər)",
    qalib="Gizli qalib (yalnız siz görürsünüz)",
    elan_kanal="Giveaway-in elan olunacağı kanal"
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_create(
    interaction: discord.Interaction,
    mukafat: str,
    saat: int,
    deqiqe: int,
    qalib: discord.Member,
    elan_kanal: discord.TextChannel
):
    total_seconds = saat * 3600 + deqiqe * 60
    if total_seconds <= 0:
        await interaction.response.send_message("❌ Müddət 0-dan böyük olmalıdır.", ephemeral=True)
        return

    end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=total_seconds)
    end_unix = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=f"**Mükafat:** {mukafat}\n\nQoşulmaq üçün 🎉 emojisinə bas!\n\n⏰ Bitmə vaxtı: <t:{end_unix}:R>",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Calestify Gaming Community")

    message = await elan_kanal.send(embed=embed)
    await message.add_reaction("🎉")

    create_giveaway(mukafat, end_unix, qalib.id, elan_kanal.id, message.id)

    await interaction.response.send_message(
        f"✅ Giveaway yaradıldı.\n📍 Kanal: {elan_kanal.mention}\n⏰ Bitmə: <t:{end_unix}:F>",
        ephemeral=True
    )


@giveaway_create.error
async def giveaway_create_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET / COIN
# ═══════════════════════════════════════════════════════════════════════════════

class MarketView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id
        options = []
        for item in MARKET_ITEMS:
            if item.get("exclusive"):
                continue
            owned = owns_item(discord_id, item["id"])
            desc = "Artıq sahibsiniz" if owned else f"{item['price']} coin"
            options.append(discord.SelectOption(label=item["name"][:100], value=item["id"], description=desc[:100]))
        sel = discord.ui.Select(placeholder="Almaq istədiyiniz əşyanı seçin...", options=options[:25])
        sel.callback = self._on_select
        self.add_item(sel)
        self.select_menu = sel

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu market yalnız sizin üçündür — `/market` ilə özününüzü açın.", ephemeral=True)
            return
        item_id = self.select_menu.values[0]
        item = get_item_by_id(item_id)
        if not item:
            await interaction.response.send_message("❌ Əşya tapılmadı.", ephemeral=True)
            return
        if owns_item(self.discord_id, item_id):
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
        add_to_inventory(self.discord_id, item_id)
        new_bal = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -item["price"], f"Market alışı: {item['name']}", "spend", new_bal)
        await interaction.response.send_message(
            f"✅ **{item['name']}** alındı! Qalan balans: **{new_bal}** coin.\n`/equip` ilə taxa bilərsiniz.",
            ephemeral=True
        )


@bot.tree.command(name="market", description="Market — banner, çərçivə və tema satın al")
async def market_cmd(interaction: discord.Interaction):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    balance = get_coins(interaction.user.id)
    embed = discord.Embed(
        title="🛒 Zenith's Academy Market",
        description=f"Balansınız: **{balance} coin**",
        color=discord.Color.gold()
    )
    for item in MARKET_ITEMS:
        if item.get("exclusive"):
            continue
        owned = owns_item(interaction.user.id, item["id"])
        value = "✅ Sahibsiniz" if owned else f"**{item['price']} coin**"
        embed.add_field(name=item["name"], value=value, inline=True)
    view = MarketView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="inventory", description="Sahib olduğunuz əşyaları göstərir")
async def inventory_cmd(interaction: discord.Interaction):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    owned = get_inventory(interaction.user.id)
    active_banner = get_active_banner(interaction.user.id)
    active_frame = get_active_frame(interaction.user.id)
    card_path = os.path.join(DATA_DIR or ".", f"inventory_{interaction.user.id}.png")
    await asyncio.to_thread(generate_inventory_card, owned, active_banner, active_frame, [], get_item_by_id, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="inventory.png"), ephemeral=True)


@bot.tree.command(name="equip", description="Sahib olduğunuz banner/çərçivə/temanı aktiv edir")
@app_commands.describe(əşya="Aktiv etmək istədiyiniz əşyanın ID-si (/inventory-də görə bilərsiniz)")
async def equip_cmd(interaction: discord.Interaction, əşya: str):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    item = get_item_by_id(əşya)
    if not item:
        await interaction.response.send_message("❌ Belə əşya tapılmadı.", ephemeral=True)
        return
    if not owns_item(interaction.user.id, əşya):
        await interaction.response.send_message(f"❌ **{item['name']}** əşyasına sahib deyilsiniz. `/market` ilə ala bilərsiniz.", ephemeral=True)
        return
    if item["type"] == "banner":
        set_active_banner(interaction.user.id, əşya)
    elif item["type"] == "avatar_frame":
        set_active_frame(interaction.user.id, əşya)
    elif item["type"] == "profile_theme":
        set_active_theme(interaction.user.id, əşya)
    else:
        await interaction.response.send_message("❌ Bu əşya növü aktiv edilə bilmir.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ **{item['name']}** aktiv edildi!", ephemeral=True)


@bot.tree.command(name="coins", description="Coin balansınızı və son əməliyyatları göstərir")
async def coins_cmd(interaction: discord.Interaction):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    balance = get_coins(interaction.user.id)
    logs = get_coin_logs(interaction.user.id, limit=15)
    card_path = os.path.join(DATA_DIR or ".", f"coins_{interaction.user.id}.png")
    await asyncio.to_thread(generate_coin_logs_card, logs, balance, None, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="coins.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NAİLİYYƏTLƏR
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="achievements", description="Nailiyyətlərinizi göstərir")
@app_commands.describe(oyunçu="Baxmaq istədiyiniz oyunçu (boş buraxsanız özünüz)")
async def achievements_cmd(interaction: discord.Interaction, oyunçu: discord.Member = None):
    target = oyunçu or interaction.user
    if not get_player(target.id):
        await interaction.response.send_message("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    achievements = get_player_achievements(target.id)
    card_path = os.path.join(DATA_DIR or ".", f"achievements_{target.id}.png")
    await asyncio.to_thread(generate_achievements_card, target.display_name, achievements, card_path)
    await interaction.followup.send(file=discord.File(card_path, filename="achievements.png"), ephemeral=True)


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
            content="✅ Tapşırıq seçildi! `/gunluk` ilə irəliləyişinizi izləyə bilərsiniz.",
            view=self
        )


@bot.tree.command(name="gunluk", description="Günlük tapşırığınızı göstərir və ya seçir")
async def gunluk_cmd(interaction: discord.Interaction):
    if not get_player(interaction.user.id):
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    active = get_player_active_task(interaction.user.id)
    card_path = os.path.join(DATA_DIR or ".", f"tasks_{interaction.user.id}.png")
    if active:
        await asyncio.to_thread(generate_tasks_card, active, [], card_path)
        await interaction.followup.send(file=discord.File(card_path, filename="tasks.png"), ephemeral=True)
        return

    available = get_active_daily_tasks()
    await asyncio.to_thread(generate_tasks_card, None, available, card_path)
    view = TaskSelectView(interaction.user.id, available) if available else None
    await interaction.followup.send(file=discord.File(card_path, filename="tasks.png"), view=view, ephemeral=True)


web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

bot.run(TOKEN)