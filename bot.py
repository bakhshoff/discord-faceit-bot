import sys
print(f"[STARTUP] Python {sys.version}", flush=True)

try:
    import discord
    from discord.ext import commands, tasks
    from discord import app_commands
    import os
    import datetime
    import random
    import asyncio
    import threading
    from dotenv import load_dotenv
    print("[STARTUP] Core imports OK", flush=True)
except Exception as _e:
    print(f"[STARTUP] Core import FAILED: {_e}", flush=True)
    sys.exit(1)
try:
    from database import (
        init_db, register_player, get_player, update_elo,
        add_to_queue, remove_from_queue, queue_size, clear_queue,
        is_in_queue, pop_10_and_balance, get_leaderboard,
        update_team_elo, get_next_match_number,
        create_giveaway, get_due_giveaways, mark_giveaway_finished,
        get_queue_list, add_coins, get_coins, spend_coins,
        get_inventory, owns_item, add_to_inventory,
        set_active_banner, get_active_banner,
        set_active_frame, get_active_frame,
        record_match_history, get_player_match_history, get_total_match_count,
        admin_set_player_field,
        add_skin, get_active_skins, get_skin_by_id, remove_skin,
        add_skin_to_inventory, get_skin_inventory, get_skin_inventory_entry,
        remove_skin_from_inventory, add_coin_log, get_coin_logs,
        get_zm_balance, add_zm, spend_zm, add_boost, get_active_boost, get_all_active_boosts,
        add_combat_stats, get_combat_stats, get_all_players,
        get_or_create_current_season, get_season_by_number, get_season_leaderboard,
        add_season_stat, get_season_stat, close_season,
        set_active_match, clear_active_match, get_active_match,
        save_scan_result, get_scan_result, confirm_scan,
        refresh_daily_tasks, get_active_daily_tasks,
        get_player_active_task, assign_task_to_player,
        update_task_progress, fail_expired_tasks,
        full_reset,
        update_streak, get_streak_bonus,
        add_warning, get_warnings, clear_warnings, ban_player, unban_player, is_banned,
        check_and_grant_achievements, get_player_achievements,
        place_prediction, resolve_predictions, get_predictions,
        get_season_leaderboard,
        record_elo_history, get_elo_history, get_peak_elo,
        transfer_coins, get_activity_stats, get_hourly_activity,
        update_personal_record, get_personal_record,
        temp_ban, check_and_lift_bans,
        check_daily_login, check_milestones,
        log_admin_action, get_admin_logs,
        set_discount, get_discount, get_all_discounts, clear_expired_discounts,
        buy_battle_pass, has_battle_pass, get_pass_data, add_bp_xp,
        get_active_bp_missions, update_bp_mission, BP_SEASON_ID, BP_MAX_LEVEL,
        get_lang, set_lang,
        claim_bp_rewards, get_unclaimed_bp_levels
    )
    from i18n import t as _t
    from leaderboard_image import generate_leaderboard_image, generate_season_leaderboard_image
    from web_server import run_web_server
    from profile_card import generate_profile_card
    from visual_cards import (generate_match_history_card, generate_coin_logs_card,
                               generate_inventory_card, generate_tasks_card,
                               generate_stats_card, generate_warnings_card,
                               generate_achievements_card, get_rank,
                               generate_compare_card, generate_elo_graph,
                               generate_activity_card,
                               generate_transfer_card, generate_search_results_card,
                               generate_skin_catalog_card, generate_bet_card)
    from pass_visual import generate_pass_gif, generate_pass_card, generate_pass_levels_card, generate_pass_announcement
    from match_card import generate_match_card, generate_result_card
    from match_recap import generate_match_recap_card
    from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
    from rules_card import generate_rules_card, generate_register_banner
    from market_config import MARKET_ITEMS, get_item_by_id
    import backup
    from ai_chat import ask_groq
    from scan_system import ocr_scoreboard, match_to_registered, apply_defaults_for_missing
    import requests
    print("[STARTUP] All module imports OK", flush=True)
except Exception as _e:
    print(f"[STARTUP] Module import FAILED: {_e}", flush=True)
    import traceback; traceback.print_exc()
    sys.exit(1)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DATA_DIR = os.environ.get("DATA_DIR")
if DATA_DIR and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

TEAM_A_VOICE_ID   = 1517460739059617883
TEAM_B_VOICE_ID   = 1517460822148911124
LOG_CHANNEL_ID    = 1517460644440313926
GENERAL_CHAT_ID   = int(os.getenv("GENERAL_CHAT_ID",   "0"))
RESULTS_CHANNEL_ID = int(os.getenv("RESULTS_CHANNEL_ID", "0"))

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

# Aktiv matç gözləmə siyahısı (matç kilidlənmişkən yığılan komandalar)
queued_match = None

LOGO_PATH = "logo.jpg"

GREEN_ACCENT = (95, 208, 122)
GOLD_ACCENT = (240, 180, 41)
RED_ACCENT = (214, 69, 61)

# Matchmaking üçün açıq saatlar (Azərbaycan vaxtı, UTC+4)
QUEUE_OPEN_HOUR = 20   # 20:00
QUEUE_CLOSE_HOUR = 2   # 02:00

ZM_MARKET_ITEMS = [
    {"id": "boost_50_1d", "name": "1 Günlük 50% ELO Boost", "boost_type": "boost_50", "multiplier": 1.5, "duration": 86400, "price_azn": 2},
    {"id": "boost_100_1d", "name": "1 Günlük 100% ELO Boost", "boost_type": "boost_100", "multiplier": 2.0, "duration": 86400, "price_azn": 4},
    {"id": "boost_50_1w", "name": "1 Həftəlik 50% ELO Boost", "boost_type": "boost_50", "multiplier": 1.5, "duration": 604800, "price_azn": 10},
    {"id": "boost_100_1w", "name": "1 Həftəlik 100% ELO Boost", "boost_type": "boost_100", "multiplier": 2.0, "duration": 604800, "price_azn": 22},
    {"id": "prot_1d", "name": "1 Günlük ELO Qoruma", "boost_type": "protection", "multiplier": 0.0, "duration": 86400, "price_azn": 5},
    {"id": "prot_1w", "name": "1 Həftəlik ELO Qoruma", "boost_type": "protection", "multiplier": 0.0, "duration": 604800, "price_azn": 30},
]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_queue_open():
    return True


leaderboard_channel_id        = None
leaderboard_message_id        = None
season_lb_channel_id          = None
season_lb_message_id          = None
queue_status_channel_id       = None
queue_status_message_id       = None

LEADERBOARD_IMAGE_PATH        = "leaderboard.png"
SEASON_LEADERBOARD_IMAGE_PATH = "season_leaderboard.png"


@tasks.loop(seconds=60)
async def refresh_leaderboard():
    global leaderboard_message_id, season_lb_message_id

    # ── Ümumi leaderboard ────────────────────────────────────────────────────
    if leaderboard_channel_id and leaderboard_message_id:
        channel = bot.get_channel(leaderboard_channel_id)
        if channel:
            rows = get_leaderboard(20)
            _base  = os.path.dirname(os.path.abspath(__file__))
            _bdir  = os.path.join(_base, "banners")
            _bfiles = {}
            for _r in rows:
                _bid = _r[5] if len(_r) > 5 else None
                if _bid:
                    _it = get_item_by_id(_bid)
                    if _it: _bfiles[_bid] = _it["file"]
            lb_path = os.path.join(DATA_DIR or ".", LEADERBOARD_IMAGE_PATH)
            await asyncio.to_thread(generate_leaderboard_image, rows, lb_path, _bdir, _bfiles)
            try:
                msg = await channel.fetch_message(leaderboard_message_id)
                await msg.edit(attachments=[discord.File(lb_path, filename="leaderboard.png")])
            except discord.NotFound:
                pass

    # ── Sezon leaderboard ─────────────────────────────────────────────────────
    if season_lb_channel_id and season_lb_message_id:
        s_channel = bot.get_channel(season_lb_channel_id)
        if s_channel:
            season   = get_or_create_current_season()
            s_rows   = get_season_leaderboard(season["id"])
            slb_path = os.path.join(DATA_DIR or ".", SEASON_LEADERBOARD_IMAGE_PATH)
            await asyncio.to_thread(
                generate_season_leaderboard_image,
                s_rows, season["season_number"],
                season["start_date"], season["end_date"], slb_path
            )
            try:
                s_msg = await s_channel.fetch_message(season_lb_message_id)
                await s_msg.edit(attachments=[discord.File(slb_path, filename="season_lb.png")])
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


@tasks.loop(minutes=20)
async def push_backup_task():
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repo = os.environ.get("GITHUB_REPO")
    if not github_token or not github_repo:
        return
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    success, msg = await asyncio.to_thread(
        backup.push_backup_to_github, repo_dir, github_token, github_repo
    )
    if not success:
        print(f"[Backup] GitHub push xetasi: {msg}")


class RegisterModal(discord.ui.Modal, title="FACEIT Qeydiyyat"):
    so2_id = discord.ui.TextInput(
        label="Standoff 2 ID",
        placeholder="Məsələn: 123456789",
        required=True,
        max_length=50
    )
    nick = discord.ui.TextInput(
        label="Oyundakı adınız (dəqiq eyni olmalıdır!)",
        placeholder="⚠️ Oyunda göründüyü kimi yazın — böyük/kiçik hərfə qədər!",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        success = register_player(interaction.user.id, str(self.nick), str(self.so2_id))
        if success:
            await asyncio.to_thread(backup.export_backup)
            embed = discord.Embed(
                title="✅ Qeydiyyat tamamlandı!",
                description=(
                    f"**Nick:** `{self.nick}`\n"
                    f"**ID:** `{self.so2_id}`\n"
                    f"**Başlanğıc ELO:** 1000"
                ),
                color=discord.Color.green()
            )
            embed.add_field(
                name="⚠️ Vacib Xəbərdarlıq",
                value=(
                    "Matç nəticəsi scan ediləndə bot oyundakı adınızla qeydiyyat adınızı uyğunlaşdırır.\n"
                    "**Ad eyni olmazsa** sizə avtomatik olaraq **0 kill · 0 asist · 5 ölüm** veriləcək!\n\n"
                    "Adınızı dəyişdirmisinizsə admindən `/admin_panel` vasitəsilə yeniləməsini xahiş edin."
                ),
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Siz artıq qeydiyyatdan keçmisiniz! `/profile` ilə baxa bilərsiniz.",
                ephemeral=True
            )


class _RegisterConfirmView(discord.ui.View):
    """Qeydiyyat xəbərdarlığından sonra 'Anladım, davam et' düyməsi."""
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Anladım, davam et →", style=discord.ButtonStyle.success, emoji="✅")
    async def proceed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal())


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
        # Qeydiyyatdan əvvəl xəbərdarlıq göstər
        warn_embed = discord.Embed(
            title="📋 Qeydiyyatdan əvvəl oxuyun!",
            description=(
                "Qeydiyyat formasında **oyundakı adınızı** dəqiq daxil etməlisiniz.\n\n"
                "🔴 **Niyə vacibdir?**\n"
                "Hər matçdan sonra bot skor ekranını scan edir və oyundakı adınızla qeydiyyat adınızı müqayisə edir.\n\n"
                "⚠️ **Ad eyni olmazsa:**\n"
                "Sizə avtomatik **0 kill · 0 asist · 5 ölüm** statistikası veriləcək!\n\n"
                "✅ **Doğru:** Oyunda `xXSlayerXx` adınızdırsa, formada da `xXSlayerXx` yazın — böyük/kiçik hərfə qədər dəqiq!"
            ),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=warn_embed, view=_RegisterConfirmView(), ephemeral=True)


class MarketItemDetailView(discord.ui.View):
    def __init__(self, discord_id, item):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        self.item = item

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu market menyusu sizə aid deyil.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🛒 Al", style=discord.ButtonStyle.success)
    async def buy_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if owns_item(self.discord_id, self.item["id"]):
            await interaction.response.send_message("⚠️ Bu əşyaya artıq sahibsiniz.", ephemeral=True)
            return
        success = spend_coins(self.discord_id, self.item["price"])
        if not success:
            current = get_coins(self.discord_id)
            await interaction.response.send_message(
                f"❌ Kifayət qədər coin yoxdur. Lazımdır: 🪙 {self.item['price']}, balansınız: 🪙 {current}",
                ephemeral=True
            )
            return
        add_to_inventory(self.discord_id, self.item["id"])
        new_balance = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -self.item["price"], f"Market alışı: {self.item['name']}", "spend", new_balance)
        await asyncio.to_thread(backup.export_backup)
        button.disabled = True
        button.label = "✅ Alındı"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"✅ **{self.item['name']}** alındı! İnventarınıza əlavə olundu.\nAktiv etmək üçün `/profile` açıb inventardan seçin.",
            ephemeral=True
        )


class MarketItemView(discord.ui.View):
    def __init__(self, discord_id, item_type=None):
        """item_type: None = hamısı, 'banner' = yalnız bannerlər, 'avatar_frame' = yalnız çərçivələr"""
        super().__init__(timeout=120)
        self.discord_id = discord_id
        items = [i for i in MARKET_ITEMS if item_type is None or i.get("type") == item_type]
        for item in items:
            owned = owns_item(discord_id, item["id"])
            label = f"👁 {item['name']} — {item['price']} 🪙" if not owned else f"{item['name']} (Sahibsiniz)"
            style = discord.ButtonStyle.primary if not owned else discord.ButtonStyle.secondary
            button = discord.ui.Button(label=label, style=style, custom_id=f"view_{item['id']}", disabled=owned)
            button.callback = self._make_callback(item)
            self.add_item(button)

    def _make_callback(self, item):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.discord_id:
                await interaction.response.send_message("❌ Bu market menyusu sizə aid deyil.", ephemeral=True)
                return
            if owns_item(self.discord_id, item["id"]):
                await interaction.response.send_message("⚠️ Bu əşyaya artıq sahibsiniz.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            player = get_player(self.discord_id)
            if not player:
                await interaction.followup.send("❌ Profiliniz tapılmadı.", ephemeral=True)
                return
            discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance, *_ = player
            avatar_bytes = None
            try:
                avatar_url = interaction.user.display_avatar.replace(size=256).url
                resp = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
                avatar_bytes = resp.content
            except Exception:
                avatar_bytes = None
            preview_banner_path = None
            preview_frame_path = None
            base_dir = os.path.dirname(os.path.abspath(__file__))
            if item.get("type") == "avatar_frame":
                preview_frame_path = os.path.join(base_dir, "frames", item["file"])
                if active_banner:
                    bitem = get_item_by_id(active_banner)
                    if bitem:
                        preview_banner_path = os.path.join(base_dir, "banners", bitem["file"])
            else:
                preview_banner_path = os.path.join(base_dir, "banners", item["file"])
                if active_frame:
                    fitem = get_item_by_id(active_frame)
                    if fitem:
                        preview_frame_path = os.path.join(base_dir, "frames", fitem["file"])
            preview_path = os.path.join(DATA_DIR or ".", f"preview_{discord_id}_{item['id']}.png")
            await asyncio.to_thread(
                generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, preview_path,
                preview_banner_path, coins, preview_frame_path, zm_balance
            )
            type_label = "Çərçivə" if item.get("type") == "avatar_frame" else "Banner"
            embed = discord.Embed(
                title=f"🛍 {item['name']}",
                description=(
                    f"📦 Növ: {type_label}\n"
                    f"💰 Qiymət: 🪙 {item['price']}\n"
                    f"👛 Balansınız: 🪙 {coins}\n\n"
                    f"⬇️ Aşağıda bu əşya ilə profilinizin önizləməsi:"
                ),
                color=discord.Color.gold()
            )
            embed.set_image(url="attachment://preview.png")
            await interaction.followup.send(
                embed=embed,
                file=discord.File(preview_path, filename="preview.png"),
                view=MarketItemDetailView(self.discord_id, item),
                ephemeral=True
            )
        return callback


class InventoryActivateView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

        owned_ids = get_inventory(discord_id)
        active_banner = get_active_banner(discord_id)
        active_frame = get_active_frame(discord_id)

        for item_id in owned_ids:
            item = get_item_by_id(item_id)
            if not item:
                continue
            if item.get("type") == "avatar_frame":
                is_active = item_id == active_frame
            else:
                is_active = item_id == active_banner
            label = f"{item['name']} ✅" if is_active else f"Aktiv et: {item['name']}"
            style = discord.ButtonStyle.secondary if is_active else discord.ButtonStyle.success
            button = discord.ui.Button(label=label, style=style, disabled=is_active)
            button.callback = self._make_callback(item_id, item["name"], item.get("type"))
            self.add_item(button)

    def _make_callback(self, item_id, item_name, item_type):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.discord_id:
                await interaction.response.send_message("❌ Bu inventar sizə aid deyil.", ephemeral=True)
                return
            if item_type == "avatar_frame":
                set_active_frame(self.discord_id, item_id)
            else:
                set_active_banner(self.discord_id, item_id)
            await asyncio.to_thread(backup.export_backup)
            await interaction.response.send_message(f"✅ **{item_name}** aktiv edildi. `/profile` ilə yoxlaya bilərsiniz.", ephemeral=True)
        return callback

# ==================== STANDOFF MARKET (SKIN) ====================

class SkinDetailView(discord.ui.View):
    """Bir skinin şəklini göstərir və altında Al düyməsi verir."""
    def __init__(self, discord_id, skin_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        self.skin_id = skin_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu market menyusu sizə aid deyil.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🛒 Al", style=discord.ButtonStyle.success)
    async def buy_skin(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_skin = get_skin_by_id(self.skin_id)
        if not current_skin or not current_skin["active"]:
            await interaction.response.send_message("⚠️ Bu skin artıq mağazada yoxdur.", ephemeral=True)
            return

        success = spend_coins(self.discord_id, current_skin["price"])
        if not success:
            current = get_coins(self.discord_id)
            await interaction.response.send_message(
                f"❌ Kifayət qədər coin yoxdur. Lazımdır: 🪙 {current_skin['price']}, balansınız: 🪙 {current}",
                ephemeral=True
            )
            return

        add_skin_to_inventory(self.discord_id, current_skin["id"], current_skin["name"],
                              current_skin["price"], current_skin["image_url"])
        new_balance = get_coins(self.discord_id)
        add_coin_log(self.discord_id, -current_skin["price"],
                     f"Skin alışı: {current_skin['name']}", "spend", new_balance)
        await asyncio.to_thread(backup.export_backup)

        button.disabled = True
        button.label = "✅ Alındı"
        embed = discord.Embed(
            title="✅ Skin alındı!",
            description=f"**{current_skin['name']}** envantarınıza əlavə olundu.\n🪙 Qalan balans: {new_balance}\n\nSkin oyunda rəhbərlik tərəfindən təhvil veriləcək.",
            color=discord.Color.green()
        )
        if current_skin["image_url"]:
            embed.set_image(url=current_skin["image_url"])
        await interaction.response.edit_message(embed=embed, view=self)

        # Log kanalına bildiriş (rəhbərlik üçün)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🛍️ Skin alışı",
                description=f"{interaction.user.mention} ({interaction.user.display_name})\nSkin: **{current_skin['name']}**\n🪙 {current_skin['price']} coin",
                color=discord.Color.blue()
            )
            if current_skin["image_url"]:
                log_embed.set_thumbnail(url=current_skin["image_url"])
            await log_channel.send(embed=log_embed)


class SkinBuyView(discord.ui.View):
    """Mağazadakı skinlər üçün 'Bax' düymələri — hər skinin şəklini göstərir."""
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

        skins = get_active_skins()
        # Discord bir view-da maksimum 25 düymə saxlaya bilər
        for skin in skins[:25]:
            label = f"👁 {skin['name']} — {skin['price']} 🪙"
            if len(label) > 80:
                label = label[:77] + "..."
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"viewskin_{skin['id']}")
            button.callback = self._make_callback(skin)
            self.add_item(button)

    def _make_callback(self, skin):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.discord_id:
                await interaction.response.send_message("❌ Bu market menyusu sizə aid deyil.", ephemeral=True)
                return

            current_skin = get_skin_by_id(skin["id"])
            if not current_skin or not current_skin["active"]:
                await interaction.response.send_message("⚠️ Bu skin artıq mağazada yoxdur.", ephemeral=True)
                return

            coins = get_coins(self.discord_id)
            embed = discord.Embed(
                title=f"🔫 {current_skin['name']}",
                description=f"💰 Qiymət: 🪙 {current_skin['price']}\n👛 Balansınız: 🪙 {coins}",
                color=discord.Color.blue()
            )
            if current_skin["image_url"]:
                embed.set_image(url=current_skin["image_url"])
            else:
                embed.description += "\n\n_(Bu skin üçün şəkil əlavə olunmayıb)_"

            await interaction.response.send_message(
                embed=embed,
                view=SkinDetailView(self.discord_id, current_skin["id"]),
                ephemeral=True
            )
        return callback


# ==================== COIN LOGLARI (filtrli) ====================

class ZMMarketView(discord.ui.View):
    def __init__(self, discord_id, zm_balance):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        self.zm_balance = zm_balance
        for item in ZM_MARKET_ITEMS:
            emoji = "🛡" if item["boost_type"] == "protection" else "🚀"
            label = f"{emoji} {item['name']} — {item['price_azn']} AZN"
            if len(label) > 80:
                label = label[:77] + "..."
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.success, custom_id=f"zm_{item['id']}")
            btn.callback = self._make_callback(item)
            self.add_item(btn)
        self.add_item(discord.ui.Button(
            label="💰 ZM Al (WhatsApp)",
            style=discord.ButtonStyle.link,
            url="https://wa.me/994507037045"
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu menyu sizə aid deyil.", ephemeral=True)
            return False
        return True

    def _make_callback(self, item):
        async def callback(interaction: discord.Interaction):
            zm = get_zm_balance(self.discord_id)
            if zm < item["price_azn"]:
                await interaction.response.send_message(
                    f"❌ Kifayət qədər AZN yoxdur.\n"
                    f"Lazımdır: {item['price_azn']} AZN | Balansınız: {zm} AZN\n"
                    f"💰 ZM almaq üçün WhatsApp düyməsinə basın.",
                    ephemeral=True
                )
                return
            success = spend_zm(self.discord_id, item["price_azn"])
            if not success:
                await interaction.response.send_message("❌ Xəta baş verdi.", ephemeral=True)
                return
            add_boost(self.discord_id, item["boost_type"], item["multiplier"], item["duration"])
            await asyncio.to_thread(backup.export_backup)
            expires_dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=item["duration"])
            expires_az = expires_dt + datetime.timedelta(hours=4)
            new_zm = get_zm_balance(self.discord_id)
            if item["boost_type"] == "protection":
                effect = "🛡 ELO itirməyəcəksiniz (müddət ərzindəki bütün matçlarda)"
            elif item["boost_type"] == "boost_50":
                effect = "🚀 ELO qazancınız x1.5 olacaq"
            else:
                effect = "⚡ ELO qazancınız x2 olacaq"
            await interaction.response.send_message(
                f"✅ **{item['name']}** aktivləşdirildi!\n"
                f"{effect}\n"
                f"⏰ Bitmə vaxtı: {expires_az.strftime('%d.%m.%Y %H:%M')} (AZ)\n"
                f"💼 Qalan AZN balansınız: {new_zm} AZN",
                ephemeral=True
            )
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="⚡ ZM Market Alışı",
                    description=f"{interaction.user.mention}\n**{item['name']}**\n{item['price_azn']} AZN",
                    color=discord.Color.purple()
                )
                await log_channel.send(embed=log_embed)
        return callback


class CoinLogsView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu loglar sizə aid deyil.", ephemeral=True)
            return False
        return True

    async def _refresh(self, interaction: discord.Interaction, log_type):
        logs = get_coin_logs(self.discord_id, log_type=log_type, limit=15)
        balance = get_coins(self.discord_id)
        path = os.path.join(DATA_DIR or ".", f"logs_{self.discord_id}.png")
        await asyncio.to_thread(generate_coin_logs_card, logs, balance, log_type, path)
        await interaction.response.edit_message(
            attachments=[discord.File(path, filename="logs.png")],
            view=self
        )

    @discord.ui.button(label="Hamısı", style=discord.ButtonStyle.primary, emoji="📋")
    async def show_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._refresh(interaction, None)

    @discord.ui.button(label="Qazanma", style=discord.ButtonStyle.success, emoji="🟢")
    async def show_earn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._refresh(interaction, "earn")

    @discord.ui.button(label="Xərcləmə", style=discord.ButtonStyle.danger, emoji="🔴")
    async def show_spend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._refresh(interaction, "spend")


# ── Dizayn Market alt-menüsü (Avatar + Çərçivə) ──────────────────────────────
class DizaynMarketView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="Avatar (Bannerlər)", style=discord.ButtonStyle.primary, emoji="🖼️", row=0)
    async def open_banners(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        banners = [i for i in MARKET_ITEMS if i.get("type") == "banner"]
        lines = [f"**{i['name']}**" + (" ✅" if owns_item(self.discord_id, i["id"]) else f" — 🪙 {i['price']}") for i in banners]
        embed = discord.Embed(title="🖼️ Avatar Bannerlər", description="\n".join(lines), color=discord.Color.gold())
        embed.set_footer(text=f"Balansınız: 🪙 {coins}")
        await interaction.response.send_message(embed=embed, view=MarketItemView(self.discord_id, item_type="banner"), ephemeral=True)

    @discord.ui.button(label="Çərçivə", style=discord.ButtonStyle.secondary, emoji="🔲", row=0)
    async def open_frames(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        frames = [i for i in MARKET_ITEMS if i.get("type") == "avatar_frame"]
        lines = [f"**{i['name']}**" + (" ✅" if owns_item(self.discord_id, i["id"]) else f" — 🪙 {i['price']}") for i in frames]
        embed = discord.Embed(title="🔲 Çərçivələr", description="\n".join(lines), color=discord.Color.blurple())
        embed.set_footer(text=f"Balansınız: 🪙 {coins}")
        await interaction.response.send_message(embed=embed, view=MarketItemView(self.discord_id, item_type="avatar_frame"), ephemeral=True)


# ── Market ana alt-menüsü ─────────────────────────────────────────────────────
class MarketSubView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="Premium Market", style=discord.ButtonStyle.danger, emoji="⚡", row=0)
    async def open_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        zm = get_zm_balance(self.discord_id)
        boosts = get_all_active_boosts(self.discord_id)
        lines = [f"**{i['name']}** — {i['price_azn']} AZN" for i in ZM_MARKET_ITEMS]
        embed = discord.Embed(title="⚡ Premium Market", description="\n".join(lines), color=discord.Color.purple())
        embed.add_field(name="💼 AZN Balansınız", value=f"{zm} AZN", inline=True)
        if boosts:
            bls = []
            for b in boosts:
                tl = max(0, b["expires_at"] - int(datetime.datetime.utcnow().timestamp()))
                h, mn = tl // 3600, (tl % 3600) // 60
                bn = "🛡 ELO Qoruma" if b["boost_type"] == "protection" else ("🚀 50% Boost" if b["boost_type"] == "boost_50" else "⚡ 100% Boost")
                bls.append(f"{bn} — {h}s {mn}dəq")
            embed.add_field(name="Aktiv güclənmələr", value="\n".join(bls), inline=False)
        embed.set_footer(text="AZN almaq üçün WhatsApp düyməsinə basın.")
        await interaction.response.send_message(embed=embed, view=ZMMarketView(self.discord_id, zm), ephemeral=True)

    @discord.ui.button(label="Skin Market", style=discord.ButtonStyle.success, emoji="🔫", row=0)
    async def open_skins(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        skins = get_active_skins()
        if not skins:
            await interaction.response.send_message("🔫 Hələ mağazada skin yoxdur.", ephemeral=True)
            return
        lines = [f"**{s['name']}** — 🪙 {s['price']}" for s in skins[:25]]
        embed = discord.Embed(title="🔫 Skin Market", description="\n".join(lines), color=discord.Color.blue())
        embed.set_footer(text=f"🪙 {coins}  ·  Skin alınca envantara düşür")
        await interaction.response.send_message(embed=embed, view=SkinBuyView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="Dizayn Market", style=discord.ButtonStyle.primary, emoji="🎨", row=0)
    async def open_dizayn(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        embed = discord.Embed(
            title="🎨 Dizayn Market",
            description="**Avatar Bannerlər** — profil arxa planını dəyişir\n**Çərçivələr** — avatar ətrafına çərçivə əlavə edir",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Balansınız: 🪙 {coins}")
        await interaction.response.send_message(embed=embed, view=DizaynMarketView(self.discord_id), ephemeral=True)


# ── İnventar alt-menüsü ───────────────────────────────────────────────────────
class InventarSubView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.primary, emoji="🖼️", row=0)
    async def inv_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        owned = [i for i in get_inventory(self.discord_id)
                 if get_item_by_id(i) and get_item_by_id(i).get("type") == "banner"]
        active = get_active_banner(self.discord_id)
        if not owned:
            await interaction.response.send_message("🖼️ Heç bir banneriniz yoxdur.", ephemeral=True)
            return
        lines = [f"{'▶️' if i == active else '⬜'} **{get_item_by_id(i)['name']}**" for i in owned]
        embed = discord.Embed(title="🖼️ Avatar Bannerlərim", description="\n".join(lines), color=discord.Color.gold())
        embed.set_footer(text="Aktivləşdirmək üçün aşağıdan seçin")
        view = InventoryActivateView(self.discord_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Çərçivə", style=discord.ButtonStyle.secondary, emoji="🔲", row=0)
    async def inv_frame(self, interaction: discord.Interaction, button: discord.ui.Button):
        owned = [i for i in get_inventory(self.discord_id)
                 if get_item_by_id(i) and get_item_by_id(i).get("type") == "avatar_frame"]
        active = get_active_frame(self.discord_id)
        if not owned:
            await interaction.response.send_message("🔲 Heç bir çərçivəniz yoxdur.", ephemeral=True)
            return
        lines = [f"{'▶️' if i == active else '⬜'} **{get_item_by_id(i)['name']}**" for i in owned]
        embed = discord.Embed(title="🔲 Çərçivələrim", description="\n".join(lines), color=discord.Color.blurple())
        view = InventoryActivateView(self.discord_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Skin", style=discord.ButtonStyle.success, emoji="🔫", row=0)
    async def inv_skin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        skin_inv = get_skin_inventory(self.discord_id)
        if not skin_inv:
            await interaction.followup.send("🔫 Heç bir skininiz yoxdur.", ephemeral=True)
            return
        lines = [f"**{s['skin_name']}** — {'✅ Təhvil verildi' if s['delivered'] else '⏳ Gözləyir'}" for s in skin_inv]
        embed = discord.Embed(title="🔫 Skin Envanterim", description="\n".join(lines[:20]), color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Premium", style=discord.ButtonStyle.danger, emoji="⚡", row=0)
    async def inv_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        boosts = get_all_active_boosts(self.discord_id)
        if not boosts:
            await interaction.response.send_message("⚡ Aktiv Premium güclənməniiz yoxdur.", ephemeral=True)
            return
        lines = []
        for b in boosts:
            tl = max(0, b["expires_at"] - int(datetime.datetime.utcnow().timestamp()))
            h, mn = tl // 3600, (tl % 3600) // 60
            bn = "🛡 ELO Qoruma" if b["boost_type"] == "protection" else ("🚀 50% Boost" if b["boost_type"] == "boost_50" else "⚡ 100% Boost")
            exp = datetime.datetime.utcfromtimestamp(b["expires_at"]) + datetime.timedelta(hours=4)
            lines.append(f"**{bn}** — {h}s {mn}dəq qalıb\n⏰ {exp.strftime('%d.%m %H:%M')}")
        embed = discord.Embed(title="⚡ Premium Envanterim", description="\n\n".join(lines), color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Əsas profil menyusu ───────────────────────────────────────────────────────
class PlayerProfileView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu profil sizə aid deyil.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Market", style=discord.ButtonStyle.primary, emoji="🛒", custom_id="profile_market", row=0)
    async def open_market(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        zm    = get_zm_balance(self.discord_id)
        embed = discord.Embed(
            title="🛒 Market",
            description="**⚡ Premium Market** — AZN ilə ELO boost, qoruma\n**🔫 Skin Market** — Standoff 2 skinləri\n**🎨 Dizayn Market** — Avatar bannerlər, çərçivələr",
            color=discord.Color.gold()
        )
        embed.add_field(name="🪙 Coin", value=str(coins), inline=True)
        embed.add_field(name="💵 AZN",  value=f"{zm} AZN", inline=True)
        await interaction.response.send_message(embed=embed, view=MarketSubView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="İnventar", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="profile_inventory", row=0)
    async def open_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        owned_ids = get_inventory(self.discord_id)
        skin_cnt  = len(get_skin_inventory(self.discord_id))
        boost_cnt = len(get_all_active_boosts(self.discord_id))
        banner_cnt = sum(1 for i in owned_ids if get_item_by_id(i) and get_item_by_id(i).get("type") == "banner")
        frame_cnt  = sum(1 for i in owned_ids if get_item_by_id(i) and get_item_by_id(i).get("type") == "avatar_frame")
        embed = discord.Embed(
            title="🎒 İnventar",
            description=f"🖼️ Avatar: **{banner_cnt}**\n🔲 Çərçivə: **{frame_cnt}**\n🔫 Skin: **{skin_cnt}**\n⚡ Premium: **{boost_cnt}** aktiv",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=InventarSubView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="Matç Tarixçəsi", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="profile_history", row=0)
    async def open_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        history = get_player_match_history(self.discord_id, limit=10)
        path = os.path.join(DATA_DIR or ".", f"history_{self.discord_id}.png")
        await asyncio.to_thread(generate_match_history_card, history, path)
        await interaction.followup.send(file=discord.File(path, filename="history.png"), ephemeral=True)

    @discord.ui.button(label="Loglar", style=discord.ButtonStyle.secondary, emoji="🪙", custom_id="profile_logs", row=1)
    async def open_logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        logs    = get_coin_logs(self.discord_id, limit=15)
        balance = get_coins(self.discord_id)
        path    = os.path.join(DATA_DIR or ".", f"logs_{self.discord_id}.png")
        await asyncio.to_thread(generate_coin_logs_card, logs, balance, None, path)
        await interaction.followup.send(file=discord.File(path, filename="logs.png"),
                                        view=CoinLogsView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="Nick Dəyiş", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="profile_nick_change", row=1)
    async def change_nick(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        current_nick = player[1] if player else ""
        await interaction.response.send_modal(NickChangeModal(self.discord_id, current_nick))

    @discord.ui.button(label="Nailiyyətlər", style=discord.ButtonStyle.primary, emoji="🏅", custom_id="profile_achievements", row=2)
    async def open_achievements(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.discord_id)
        if not player:
            await interaction.followup.send("❌", ephemeral=True); return

        achs  = get_player_achievements(self.discord_id)
        path  = os.path.join(DATA_DIR or ".", f"achievements_{self.discord_id}.png")

        if achs:
            try:
                await asyncio.to_thread(generate_achievements_card, player[1], achs, path)
                await interaction.followup.send(file=discord.File(path, filename="achievements.png"), ephemeral=True)
                return
            except Exception:
                pass

        # Nailiyyət yoxdursa və ya kart xəta versə — mövcud nailiyyətlər siyahısı
        from database import get_player_achievements as _gpa
        ALL_ACH = [
            ("🎮", "İlk Matç",       "Birinci matçını oyna"),
            ("🏆", "10 Qələbə",      "10 matç qazanmaq"),
            ("👑", "50 Qələbə",      "50 matç qazanmaq"),
            ("🔫", "50 Kill",        "Cəmi 50 kill etmək"),
            ("💀", "100 Kill",       "Cəmi 100 kill etmək"),
            ("🎯", "500 Kill",       "Cəmi 500 kill etmək"),
            ("⭐", "MVP x3",         "3 dəfə MVP seçilmək"),
            ("🌟", "MVP Ustası",     "10 dəfə MVP seçilmək"),
            ("🔥", "Seriya 3",       "3 ardıcıl qələbə"),
            ("💥", "Seriya 5",       "5 ardıcıl qələbə"),
            ("⚡", "Seriya 10",      "10 ardıcıl qələbə"),
            ("🗡️", "KD 2.0+",       "K/D nisbəti 2.0 keçmək"),
            ("🎯", "Tapşırıq x10",  "10 tapşırıq tamamlamaq"),
            ("💎", "1200 ELO",       "1200 ELO-ya çatmaq"),
            ("👑", "1500 ELO",       "1500 ELO-ya çatmaq"),
        ]
        owned_ids = {a["id"] for a in achs}
        embed = discord.Embed(title="🏅 Nailiyyətlər", color=discord.Color.gold())
        owned_txt  = "\n".join(f"✅ {ico} **{n}**" for ico,n,_ in ALL_ACH if n in [a["name"] for a in achs]) or "—"
        locked_txt = "\n".join(f"🔒 {ico} {n} — _{d}_" for ico,n,d in ALL_ACH if n not in [a["name"] for a in achs])
        if owned_txt != "—":
            embed.add_field(name=f"Qazanıldı ({len(achs)})", value=owned_txt, inline=False)
        embed.add_field(name="Kilidli", value=locked_txt[:1000] or "Hamısı qazanılıb!", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Tapşırıqlar", style=discord.ButtonStyle.success, emoji="🎯", custom_id="profile_tasks", row=2)
    async def open_tasks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        refresh_daily_tasks()
        fail_expired_tasks()
        active = get_player_active_task(self.discord_id)
        tasks  = get_active_daily_tasks()

        if not active and not tasks:
            await interaction.followup.send("⏳ Aktiv tapşırıq yoxdur, tezliklə yenilənir.", ephemeral=True)
            return

        path = os.path.join(DATA_DIR or ".", f"tasks_{self.discord_id}.png")
        card_ok = False
        try:
            await asyncio.to_thread(generate_tasks_card, active, tasks, path)
            card_ok = True
        except Exception:
            pass

        view = TaskSelectView(self.discord_id, tasks) if not active and tasks else None

        if card_ok:
            await interaction.followup.send(
                file=discord.File(path, filename="tasks.png"),
                view=view, ephemeral=True
            )
        else:
            # Embed fallback
            import datetime as _dt
            if active:
                exp = _dt.datetime.utcfromtimestamp(active["expires_at"]) + _dt.timedelta(hours=4)
                kp, kt = active["kills_progress"], active["kill_target"]
                ap, at = active["assists_progress"], active["assist_target"]
                embed = discord.Embed(title="🎯 Aktiv Tapşırıq", color=discord.Color.orange())
                embed.add_field(name="Tapşırıq", value=active["description"], inline=False)
                if kt: embed.add_field(name="Kill",  value=f"{kp}/{kt}", inline=True)
                if at: embed.add_field(name="Asist", value=f"{ap}/{at}", inline=True)
                embed.add_field(name="🪙", value=f"{active['reward_coins']} coin", inline=True)
                embed.set_footer(text=f"Bitmə: {exp.strftime('%H:%M')}")
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="📋 Günlük Tapşırıqlar", color=discord.Color.gold())
                for t in tasks:
                    embed.add_field(name=t["description"],
                                    value=f"Kill: {t['kill_target']}  Asist: {t['assist_target']}  🪙 {t['reward_coins']}",
                                    inline=False)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Ayarlar", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="profile_settings", row=2)
    async def open_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang  = get_lang(self.discord_id)
        embed = discord.Embed(
            title=_t(lang, 'settings_title'),
            description=_t(lang, 'settings_desc'),
            color=discord.Color.blurple()
        )
        embed.add_field(name="Dil / Dil", value=_t(lang, 'current_lang'), inline=False)
        await interaction.response.send_message(embed=embed, view=SettingsView(self.discord_id), ephemeral=True)


class SettingsView(discord.ui.View):
    def __init__(self, discord_id: int):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="🇦🇿 Azərbaycanca", style=discord.ButtonStyle.primary)
    async def set_az(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        set_lang(self.discord_id, 'az')
        await interaction.response.edit_message(
            content=_t('az', 'lang_set_az'),
            embed=None, view=None)

    @discord.ui.button(label="🇹🇷 Türkçe", style=discord.ButtonStyle.secondary)
    async def set_tr(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        set_lang(self.discord_id, 'tr')
        await interaction.response.edit_message(
            content=_t('tr', 'lang_set_tr'),
            embed=None, view=None)


class NickChangeModal(discord.ui.Modal, title="Nick Dəyişdir"):
    new_nick = discord.ui.TextInput(
        label="Yeni oyun adı (oyundakı ilə eyni olmalı!)",
        placeholder="⚠️ Böyük/kiçik hərfə qədər dəqiq yazın",
        required=True,
        min_length=2,
        max_length=50
    )

    def __init__(self, discord_id: int, current_nick: str):
        super().__init__()
        self.discord_id   = discord_id
        self.new_nick.default = current_nick

    async def on_submit(self, interaction: discord.Interaction):
        new = str(self.new_nick).strip()
        admin_set_player_field(self.discord_id, "so2_nick", new)
        await asyncio.to_thread(backup.export_backup)
        embed = discord.Embed(
            title="✅ Nick yeniləndi",
            description=f"Yeni adınız: **{new}**",
            color=discord.Color.green()
        )
        embed.add_field(
            name="⚠️ Xatırlatma",
            value="Scan sistemi oyundakı adınızla bu adı uyğunlaşdırır.\n"
                  "Ad oyundakı adla eyni olmalıdır, əks halda **0/0/5** veriləcək!",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


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
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    embed=discord.Embed(
                        title=f"✅ Matç No{self.match_number} — Hər iki komanda hazır",
                        description=(
                            "Oyun başlayır! Matç bitdikdən sonra:\n"
                            "1. Kapitan skor şəklini **#results** kanalına göndərir\n"
                            "2. Rəhbər `/scan` yazır"
                        ),
                        color=discord.Color.green()
                    )
                )

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

        winner_coins = {}
        for discord_id in winner_ids:
            earned = random.randint(5, 10)
            new_balance = add_coins(discord_id, earned)
            add_coin_log(discord_id, earned, f"Matç No{self.match_number} qələbə", "earn", new_balance)
            winner_coins[discord_id] = (earned, new_balance)

        loser_coins = {}
        for discord_id in loser_ids:
            earned = random.randint(0, 5)
            new_balance = add_coins(discord_id, earned)
            add_coin_log(discord_id, earned, f"Matç No{self.match_number} iştirak", "earn", new_balance)
            loser_coins[discord_id] = (earned, new_balance)

        await asyncio.to_thread(backup.export_backup)

        await asyncio.to_thread(
            record_match_history,
            "5v5",
            winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]],
            [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]],
            [r["new_elo"] for r in results["losers"]],
            self.match_number
        )

        self.finished = True
        for child in self.children:
            child.disabled = True

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        ts = now.strftime("%d.%m.%Y %H:%M")

        winner_results_list = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                                for p, r in zip(winner_team, results["winners"])]
        loser_results_list  = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                                for p, r in zip(loser_team,  results["losers"])]

        result_img_path = os.path.join(DATA_DIR or ".", f"result_{self.match_number}.png")
        await asyncio.to_thread(
            generate_result_card,
            self.match_number, winner_label, loser_label,
            winner_team, loser_team,
            winner_results_list, loser_results_list,
            winner_coins, loser_coins,
            ts, result_img_path
        )

        # Sezon statistikası yenilə
        season = get_or_create_current_season()
        for p, r in zip(winner_team, results["winners"]):
            elo_diff = r["new_elo"] - r["old_elo"]
            add_season_stat(p["discord_id"], season["id"], wins=1, elo_gained=max(0, elo_diff))
        for p, r in zip(loser_team, results["losers"]):
            elo_diff = r["new_elo"] - r["old_elo"]
            add_season_stat(p["discord_id"], season["id"], losses=1, elo_gained=max(0, elo_diff))

        # Mərc nəticələrini həll et + coin_log yaz
        pred_winners = resolve_predictions(self.match_number, winner_label)
        for pw in pred_winners:
            new_bal = get_coins(pw["discord_id"])
            add_coin_log(pw["discord_id"], pw["payout"],
                         f"Merc qalibiyyeti — Matc No{self.match_number} (+{pw['payout']} coin)",
                         "earn", new_bal)
            member = interaction.guild.get_member(pw["discord_id"]) if interaction.guild else None
            if member:
                try:
                    await member.send(
                        f"🎲 **Matç No{self.match_number}** — Mərc qazandınız!\n"
                        f"Mərc: {pw['bet']} coin → Qazanc: **+{pw['payout']} coin** 🎉"
                    )
                except discord.Forbidden:
                    pass

        # Matç kilidini aç
        clear_active_match()

        await interaction.response.edit_message(
            content=f"✅ **Matç No{self.match_number}** nəticəsi qeyd edildi — 🏆 **{winner_label}**",
            view=self
        )
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(file=discord.File(result_img_path, filename="result.png"))
            # Matç xülasəsi kartı
            try:
                active_map = "?"
                _am = get_active_match()
                if _am: active_map = _am.get("selected_map", "?")
                recap_a = [{"nick": p["nick"], "kills": 0, "assists": 0, "deaths": 0,
                             "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                            for p, r in zip(winner_team, results["winners"])]
                recap_b = [{"nick": p["nick"], "kills": 0, "assists": 0, "deaths": 0,
                             "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                            for p, r in zip(loser_team, results["losers"])]
                if winner_label == "Komanda A":
                    r_team_a, r_team_b = recap_a, recap_b
                    sc_a, sc_b = 13, 0
                else:
                    r_team_a, r_team_b = recap_b, recap_a
                    sc_a, sc_b = 0, 13
                recap_path = os.path.join(DATA_DIR or ".", f"recap_{self.match_number}.png")
                await asyncio.to_thread(
                    generate_match_recap_card,
                    self.match_number, active_map, sc_a, sc_b,
                    winner_label, r_team_a, r_team_b, recap_path)
                await log_channel.send(file=discord.File(recap_path, filename="recap.png"))
            except Exception as _re:
                print(f"[RECAP]: {_re}", flush=True)

        # Gözləyən matç varsa avtomatik başlat
        if queue_size() >= 10:
            mm_ch = interaction.guild.get_channel(
                queue_status_channel_id or interaction.channel_id
            ) if interaction.guild else None
            if mm_ch:
                await _start_match(mm_ch, interaction.guild)

    @discord.ui.button(label="Komanda A qalib", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="result_a")
    async def team_a_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_a, self.team_b, "Komanda A", "Komanda B")

    @discord.ui.button(label="Komanda B qalib", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="result_b")
    async def team_b_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, self.team_b, self.team_a, "Komanda B", "Komanda A")


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
    # Orta gözləmə vaxtı: son 10 matçın başlama aralığından hesablanır
    try:
        from database import _get_conn as _gq
        _cq = _gq(); _curq = _cq.cursor()
        _curq.execute("SELECT played_at FROM match_history ORDER BY played_at DESC LIMIT 10")
        _rows = [r[0] for r in _curq.fetchall()]
        _cq.close()
        if len(_rows) >= 2:
            _diffs = [_rows[i]-_rows[i+1] for i in range(len(_rows)-1)]
            _avg   = int(sum(_diffs)/len(_diffs)/60)
            _avg   = max(5, min(_avg, 120))
        else:
            _avg   = None
    except Exception:
        _avg = None
    await asyncio.to_thread(generate_queue_status_card, players, image_path, _avg)
    try:
        message = await channel.fetch_message(queue_status_message_id)
        await message.edit(attachments=[discord.File(image_path, filename="queue_status.png")])
    except discord.NotFound:
        pass


class VetoView(discord.ui.View):
    """Xəritə Veto: kapitanlar növbə ilə ban edir, 1 xəritə qalır."""
    def __init__(self, match_number, team_a, team_b, captain_a_id, captain_b_id, channel, guild):
        super().__init__(timeout=120)
        self.match_number  = match_number
        self.team_a        = team_a
        self.team_b        = team_b
        self.captain_a_id  = captain_a_id
        self.captain_b_id  = captain_b_id
        self.channel       = channel
        self.guild         = guild
        self.remaining     = list(MAPS)      # qalan xəritələr
        self.turn          = 0               # 0=A banlar, 1=B banlar
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for m in self.remaining:
            btn = discord.ui.Button(label=m, style=discord.ButtonStyle.danger)
            async def _cb(inter: discord.Interaction, map_name=m):
                await self._handle_ban(inter, map_name)
            btn.callback = _cb
            self.add_item(btn)

    async def _handle_ban(self, interaction: discord.Interaction, map_name: str):
        expected = self.captain_a_id if self.turn % 2 == 0 else self.captain_b_id
        cap_label = "A" if self.turn % 2 == 0 else "B"
        if interaction.user.id != expected:
            await interaction.response.send_message(
                f"❌ İndi Kapitan {cap_label}-nin növbəsidir.", ephemeral=True)
            return
        self.remaining.remove(map_name)
        self.turn += 1

        if len(self.remaining) == 1:
            # 1 xəritə qaldı — seçildi
            selected = self.remaining[0]
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(
                content=f"🗺️ **{selected}** seçildi! Matç başlayır...",
                view=self
            )
            try:
                await _launch_match(self.match_number, selected, self.team_a, self.team_b,
                                    self.captain_a_id, self.captain_b_id, self.channel, self.guild)
            except Exception as e:
                print(f"[Veto] _launch_match xetasi: {e}", flush=True)
        else:
            next_cap_id = self.captain_a_id if self.turn % 2 == 0 else self.captain_b_id
            next_cap    = "A" if self.turn % 2 == 0 else "B"
            self._build_buttons()
            bans_done = len(MAPS) - len(self.remaining)
            await interaction.response.edit_message(
                content=(f"🗺️ **{map_name}** ban edildi! ({bans_done}/{len(MAPS)-1} ban)\n"
                         f"Sıra: <@{next_cap_id}> (Kapitan **{next_cap}**) ban edir."),
                view=self
            )

    async def on_timeout(self):
        selected = random.choice(self.remaining) if self.remaining else random.choice(MAPS)
        try:
            await _launch_match(self.match_number, selected, self.team_a, self.team_b,
                                self.captain_a_id, self.captain_b_id, self.channel, self.guild)
        except Exception as e:
            print(f"[Veto] timeout _launch_match xetasi: {e}", flush=True)


async def _start_match(channel, guild):
    """10 oyunçu toplananda çağırılır. Əvvəlcə xəritə səsverməsi, sonra matç."""
    result = pop_10_and_balance()
    if result is None:
        return
    team_a, team_b, captain_a, captain_b = result
    match_number = get_next_match_number()
    all_ids = {p["discord_id"] for p in team_a + team_b}
    mentions = " ".join([f"<@{p['discord_id']}>" for p in team_a + team_b])

    veto_embed = discord.Embed(
        title=f"Matç No{match_number} — Xəritə Veto",
        description=(
            f"Kapitanlar növbə ilə xəritəni BAN edir.\n"
            f"7 xəritədən 6 ban edilir, 1 qalır.\n\n"
            f"Kapitan A: <@{captain_a['discord_id']}>\n"
            f"Kapitan B: <@{captain_b['discord_id']}>\n\n"
            f"İlk ban: <@{captain_a['discord_id']}> (Kapitan **A**)"
        ),
        color=discord.Color.red()
    )
    veto_view = VetoView(match_number, team_a, team_b,
                         captain_a["discord_id"], captain_b["discord_id"], channel, guild)
    await channel.send(content=mentions, embed=veto_embed, view=veto_view)

    # 2. Balans Skoru — log kanalına vizual embed
    avg_a  = sum(p["elo"] for p in team_a) / max(len(team_a), 1)
    avg_b  = sum(p["elo"] for p in team_b) / max(len(team_b), 1)
    diff   = abs(avg_a - avg_b)
    score  = max(0, int(100 - diff / 3))
    bar_f  = int(score / 10)
    bar    = "=" * bar_f + "-" * (10 - bar_f)
    color  = 0x57F287 if score >= 80 else (0xFEE75C if score >= 60 else 0xED4245)
    log_ch = bot.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        b_embed = discord.Embed(
            title=f"Matc No{match_number} — Balans Skoru: {score}/100",
            description=f"`[{bar}]` {score}%",
            color=color
        )
        b_embed.add_field(name="Komanda A orta ELO", value=f"{avg_a:.0f}", inline=True)
        b_embed.add_field(name="Komanda B orta ELO", value=f"{avg_b:.0f}", inline=True)
        b_embed.add_field(name="ELO Ferqi",          value=f"{diff:.0f}", inline=True)
        b_embed.set_footer(text="80+ Mukemmel · 60-79 Yaxshi · 60- Qeyri-balansl")
        await log_ch.send(embed=b_embed)


async def _send_match_summary(guild, match_number, winner_label,
                               winner_team, loser_team,
                               winner_results, loser_results,
                               all_stats: dict, mvp_nick=None):
    """Bütün 10 oyunçuya matç icmalını DM ilə göndərir."""
    if not guild:
        return
    all_team = [(p, r, True)  for p, r in zip(winner_team, winner_results)] + \
               [(p, r, False) for p, r in zip(loser_team,  loser_results)]
    for p, r, won in all_team:
        did  = p["discord_id"]
        s    = all_stats.get(did, {})
        k, a, d = s.get("kills",0), s.get("assists",0), s.get("deaths",0)
        kd   = round(k/max(d,1), 2)
        diff = r["new_elo"] - r["old_elo"]
        sign = "+" if diff >= 0 else ""
        streak_now, _ = (0, 0) if not won else (0, 0)  # placeholder — streak bot yaddaşında
        result_line = "QELEBƏ" if won else "MEGLUBIYET"
        is_mvp = (p["nick"] == mvp_nick) if mvp_nick else False

        lines = [
            f"**Matç No{match_number} — {result_line}**",
            f"Qalib: {winner_label}",
            "",
            f"Sizin stat: K:{k}  A:{a}  D:{d}  KD:{kd}",
            f"ELO: {r['old_elo']} → {r['new_elo']} ({sign}{diff})",
        ]
        if is_mvp:
            lines.append("Siz bu matçda MVP-siniz! (+5 coin +3 ELO)")
        pr = get_personal_record(did)
        if k > 0 and k >= pr["best_kills"]:
            lines.append(f"Yeni rekord: {k} kill bir matçda!")
        if kd > 0 and kd >= pr["best_kd"] and kd > 1:
            lines.append(f"Yeni KD rekordu: {kd}!")
        try:
            member = guild.get_member(did)
            if member:
                await member.send("\n".join(lines))
        except discord.Forbidden:
            pass


def _apply_mvp(all_players: list, stats: dict):
    """
    Kill + asist toplamı ən çox olan oyunçuya MVP mükafatı verir.
    all_players: [{"discord_id", "nick", ...}]
    stats: {discord_id: {"kills", "assists", "deaths"}}
    Returns: (mvp_player_dict, ka_total) or (None, 0)
    """
    best, best_score = None, -1
    for p in all_players:
        did = p["discord_id"]
        s   = stats.get(did, {})
        ka  = s.get("kills", 0) + s.get("assists", 0)
        if ka > best_score:
            best_score = ka
            best       = p
    if best and best_score >= 0:
        coin_bal = add_coins(best["discord_id"], 5)
        add_coin_log(best["discord_id"], 5, "MVP mükafatı", "earn", coin_bal)
        # +3 ELO birbaşa
        from database import _get_conn as _gc
        conn = _gc(); cur = conn.cursor()
        cur.execute("UPDATE players SET elo = elo + 3 WHERE discord_id = ?", (best["discord_id"],))
        conn.commit(); conn.close()
        return best, best_score
    return None, 0


def _build_match_active_embed(match_number, selected_map, team_a, team_b,
                               captain_a_id=None, captain_b_id=None):
    """Aktiv matç embedi — logs kanalına göndərilir."""
    embed = discord.Embed(
        title=f"🎮 MATÇ No{match_number} — DAVAM EDİR",
        color=0x5865F2
    )
    embed.add_field(name="🗺️ Xəritə", value=f"**{selected_map}**", inline=True)
    embed.add_field(name="⏱️ Status", value="🟡 Oyun davam edir...", inline=True)
    embed.add_field(name="​", value="​", inline=True)

    def fmt(team, cap_id):
        lines = []
        for p in team:
            prefix = "⭐" if p["discord_id"] == cap_id else "▸"
            lines.append(f"{prefix} {p['nick']} — `{p['elo']} ELO`")
        return "\n".join(lines)

    embed.add_field(name="🔵 KOMANDA A", value=fmt(team_a, captain_a_id) or "—", inline=True)
    embed.add_field(name="🔴 KOMANDA B", value=fmt(team_b, captain_b_id) or "—", inline=True)
    embed.set_footer(text="⭐ = Kapitan  ·  Matç bitdikdən sonra kapitan nəticəni #results kanalına göndərsin.")
    return embed


def _build_match_result_embed(match_number, selected_map, winner_label,
                               winner_team, loser_team,
                               winner_results, loser_results,
                               winner_stats, loser_stats, timestamp_str,
                               mvp_nick=None, mvp_ka=0):
    """Tamamlanmış matç embedi — aktiv mesajı edit etmək üçün."""
    w_color = 0x57F287
    desc = f"🗺️ {selected_map}  ·  📅 {timestamp_str}"
    if mvp_nick:
        desc += f"\n⭐ **MVP: {mvp_nick}** — {mvp_ka} K+A  (+5🪙 +3 ELO)"
    embed = discord.Embed(
        title=f"✅ MATÇ No{match_number} — TAMAMLANDI",
        description=desc,
        color=w_color
    )
    embed.add_field(name="🏆 Qalib", value=f"**{winner_label}**", inline=True)
    embed.add_field(name="​", value="​", inline=True)
    embed.add_field(name="​", value="​", inline=True)

    all_stats = {**winner_stats, **loser_stats}

    def player_line(p, r, stats):
        diff = r["new_elo"] - r["old_elo"]
        sign = "+" if diff >= 0 else ""
        s    = stats.get(p["discord_id"], {})
        kd   = round(s.get("kills", 0) / max(s.get("deaths", 1), 1), 2)
        mvp_tag = " ⭐" if mvp_nick and p["nick"] == mvp_nick else ""
        return (f"**{p['nick']}**{mvp_tag}\n"
                f"K:{s.get('kills',0)} A:{s.get('assists',0)} D:{s.get('deaths',0)} · KD:{kd}\n"
                f"ELO: {r['old_elo']}→{r['new_elo']} ({sign}{diff})")

    w_lines = "\n\n".join(player_line(p, r, winner_stats)
                           for p, r in zip(winner_team, winner_results))
    l_lines = "\n\n".join(player_line(p, r, loser_stats)
                           for p, r in zip(loser_team, loser_results))

    loser_label = "Komanda B" if winner_label == "Komanda A" else "Komanda A"
    embed.add_field(name=f"🏆 {winner_label}", value=w_lines or "—", inline=True)
    embed.add_field(name=f"❌ {loser_label}",  value=l_lines or "—", inline=True)
    return embed


async def _edit_log_match_message(embed):
    """Logs kanalındakı aktiv matç mesajını edit edir."""
    active = get_active_match()
    if not active:
        return
    msg_id = active.get("log_message_id")
    ch_id  = active.get("log_channel_id")
    if not msg_id or not ch_id:
        return
    try:
        ch  = bot.get_channel(ch_id)
        if ch:
            msg = await ch.fetch_message(msg_id)
            await msg.edit(embed=embed, view=None)
    except Exception:
        pass


async def _launch_match(match_number, selected_map, team_a, team_b, captain_a_id, captain_b_id, channel, guild):
    """Xəritə seçildikdən sonra matçı başladır."""
    import json as _j

    card_path = os.path.join(DATA_DIR or ".", f"match_{match_number}.png")
    await asyncio.to_thread(
        generate_match_card, match_number, selected_map, team_a, team_b,
        captain_a_id, captain_b_id, card_path
    )

    season = get_or_create_current_season()
    for p in team_a + team_b:
        player = get_player(p["discord_id"])
        if player:
            add_season_stat(p["discord_id"], season["id"], elo_start=player[3])

    mentions   = " ".join(f"<@{p['discord_id']}>" for p in team_a + team_b)
    ready_view = TeamReadyView(match_number, team_a, team_b, captain_a_id, captain_b_id)

    # Matchmaking kanalında mention
    await channel.send(content=f"🎮 **Matç No{match_number} — {selected_map}!** {mentions}")

    # Log kanalında: matç kartı + hazır düymələri + aktiv matç embedi
    log_ch     = bot.get_channel(LOG_CHANNEL_ID)
    log_msg_id = None
    if log_ch:
        active_embed = _build_match_active_embed(match_number, selected_map, team_a, team_b,
                                                  captain_a_id, captain_b_id)
        log_msg = await log_ch.send(
            content=mentions,
            embed=active_embed,
            file=discord.File(card_path, filename="match.png"),
            view=ready_view
        )
        log_msg_id = log_msg.id

    set_active_match(
        match_number,
        team_a_json=_j.dumps(team_a, ensure_ascii=False),
        team_b_json=_j.dumps(team_b, ensure_ascii=False),
        log_message_id=log_msg_id,
        log_channel_id=LOG_CHANNEL_ID,
        selected_map=selected_map
    )

    # Kapitanlara DM + #general-chat bildirişi
    general_ch = bot.get_channel(GENERAL_CHAT_ID)
    for captain_id in (captain_a_id, captain_b_id):
        m = guild.get_member(captain_id)
        if m:
            team_label = "A" if captain_id == captain_a_id else "B"
            try:
                await m.send(_t(captain_id, 'match_start_dm',
                                num=match_number, team=team_label, channel="#results"))
            except discord.Forbidden:
                pass
            if general_ch:
                await general_ch.send(
                    f"📢 {m.mention} — **Matç No{match_number}** kapitanısınız!\n"
                    f"Matç bitdikdən sonra skor şəklini **#results** kanalına göndərin."
                )

    # Ses kanallarına köçür
    for p in team_a:
        mbr = guild.get_member(p["discord_id"])
        if mbr and mbr.voice:
            try: await mbr.move_to(bot.get_channel(TEAM_A_VOICE_ID))
            except discord.Forbidden: pass
    for p in team_b:
        mbr = guild.get_member(p["discord_id"])
        if mbr and mbr.voice:
            try: await mbr.move_to(bot.get_channel(TEAM_B_VOICE_ID))
            except discord.Forbidden: pass

    await update_queue_status_message()


class MatchmakingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="5v5", style=discord.ButtonStyle.danger, emoji="🔥", custom_id="mm_join")
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

        discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance, *_ = player

        # Ban yoxlaması
        if is_banned(discord_id):
            await interaction.response.send_message(
                "🔴 Siz banlanmısınız. Rəhbərliylə əlaqə saxlayın.", ephemeral=True)
            return

        added = add_to_queue(discord_id, nick, elo, so2_id)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()

        # Sıra dolu (10 nəfər var, lakin aktiv matç davam edir)
        if size >= 10 and get_active_match():
            await interaction.response.send_message(
                "⏳ Sıra doludur (10/10). Aktiv matç bitdikdən sonra növbəti matç avtomatik başlayacaq.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(_t(discord_id, 'queue_joined', pos=size), ephemeral=True)

        # 8/10 bildirişi
        if size == 8:
            general_ch = bot.get_channel(GENERAL_CHAT_ID)
            if general_ch:
                await general_ch.send(
                    "🎮 **Sırada 8/10 oyunçu var!** 2 nəfər daha lazımdır — `#matchmaking` kanalına keçin!"
                )

        await update_queue_status_message()

        if size >= 10:
            await _start_match(interaction.channel, interaction.guild)

    @discord.ui.button(label="Sıradan çıx", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="mm_leave")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = remove_from_queue(interaction.user.id)
        if removed:
            await interaction.response.send_message(_t(interaction.user.id, 'queue_left'), ephemeral=True)
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


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN SİSTEMİ  (Gemini Vision + Manuel Düzəliş)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_scan_embed(match_number, parsed, winner_label):
    """Scan nəticəsi embedi qurur."""
    lines = []
    for key, s in parsed.items():
        if isinstance(key, int) or (isinstance(key, str) and not key.startswith("unknown_")):
            mark = "✅"
        else:
            mark = "⚠️"
        g_nick = s.get("gemini_nick", "")
        arrow  = f" ← *{g_nick}*" if g_nick and g_nick != s["nick"] else ""
        lines.append(f"{mark} **{s['nick']}**{arrow}  K:{s['kills']} A:{s['assists']} D:{s['deaths']}")

    embed = discord.Embed(
        title=f"🔍 Matç No{match_number} — Gemini Scan",
        description="\n".join(lines) or "Heç bir oyunçu tapılmadı.",
        color=discord.Color.orange()
    )
    embed.add_field(name="🏆 Qalib", value=f"Komanda **{winner_label}**", inline=True)
    embed.set_footer(text="✅ uyğun  ⚠️ tapılmadı (0/0/5 veriləcək)  |  Düzəliş üçün oyunçunu seçin")
    return embed


class StatEditModal(discord.ui.Modal, title="Stat Düzəliş"):
    kills_inp   = discord.ui.TextInput(label="Kill",   required=True, max_length=4)
    assists_inp = discord.ui.TextInput(label="Asist",  required=True, max_length=4)
    deaths_inp  = discord.ui.TextInput(label="Ölüm",   required=True, max_length=4)

    def __init__(self, player_key, player_nick, current, view_ref):
        super().__init__(title=f"{player_nick[:20]} — Düzəliş")
        self.player_key = player_key
        self.view_ref   = view_ref
        self.kills_inp.default   = str(current["kills"])
        self.assists_inp.default = str(current["assists"])
        self.deaths_inp.default  = str(current["deaths"])

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.view_ref.parsed[self.player_key]["kills"]   = int(self.kills_inp.value)
            self.view_ref.parsed[self.player_key]["assists"] = int(self.assists_inp.value)
            self.view_ref.parsed[self.player_key]["deaths"]  = int(self.deaths_inp.value)
        except ValueError:
            await interaction.response.send_message("❌ Rəqəm daxil edin.", ephemeral=True)
            return
        embed = _build_scan_embed(self.view_ref.match_number,
                                  self.view_ref.parsed,
                                  self.view_ref.winner_label)
        await interaction.response.edit_message(embed=embed, view=self.view_ref)


class ScanEditView(discord.ui.View):
    def __init__(self, match_number, parsed, winner_label, all_players):
        super().__init__(timeout=600)
        self.match_number  = match_number
        self.parsed        = parsed   # mutable dict
        self.winner_label  = winner_label
        self.all_players   = all_players

        # Oyunçu seçimi dropdown
        options = []
        for key, s in parsed.items():
            label = s["nick"][:25]
            val   = str(key)
            options.append(discord.SelectOption(label=label, value=val,
                                                description=f"K:{s['kills']} A:{s['assists']} D:{s['deaths']}"))
        if options:
            sel = discord.ui.Select(placeholder="Düzəltmək üçün oyunçu seçin...",
                                    options=options[:25], min_values=1, max_values=1)
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
        stats = self.parsed.get(key) or self.parsed.get(raw_key)
        if not stats:
            await interaction.response.send_message("❌ Tapılmadı.", ephemeral=True)
            return
        modal = StatEditModal(key, stats["nick"], stats, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Qalib A", style=discord.ButtonStyle.primary, emoji="🔵", row=1)
    async def set_winner_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        self.winner_label = "A"
        embed = _build_scan_embed(self.match_number, self.parsed, self.winner_label)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Qalib B", style=discord.ButtonStyle.danger, emoji="🔴", row=1)
    async def set_winner_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        self.winner_label = "B"
        embed = _build_scan_embed(self.match_number, self.parsed, self.winner_label)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Təsdiqlə ✅", style=discord.ButtonStyle.success, row=2)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)
            return
        if self.winner_label not in ("A", "B"):
            await interaction.response.send_message("❌ Əvvəlcə Qalib A/B seçin.", ephemeral=True)
            return

        active = get_active_match()
        team_a = active.get("team_a", []) if active else []
        team_b = active.get("team_b", []) if active else []
        sel_map = (active or {}).get("selected_map", "?")

        winner_team = team_a if self.winner_label == "A" else team_b
        loser_team  = team_b if self.winner_label == "A" else team_a
        winner_label_full = f"Komanda {self.winner_label}"

        winner_ids = [p["discord_id"] for p in winner_team]
        loser_ids  = [p["discord_id"] for p in loser_team]

        results = update_team_elo(winner_ids, loser_ids) if (winner_ids and loser_ids) else None

        import json as _j
        scan_json = _j.dumps({str(k): v for k, v in self.parsed.items()}, ensure_ascii=False)
        scan_id   = save_scan_result(self.match_number, scan_json, self.winner_label)
        confirm_scan(scan_id)

        season = get_or_create_current_season()
        winner_coins, loser_coins, winner_stats, loser_stats = {}, {}, {}, {}

        for key, stats in self.parsed.items():
            try: did = int(key)
            except: continue
            add_combat_stats(did, stats["kills"], stats["assists"], stats["deaths"])
            add_season_stat(did, season["id"], kills=stats["kills"],
                            assists=stats["assists"], deaths=stats["deaths"])
            completed, reward = update_task_progress(did, stats["kills"], stats["assists"])
            if completed and reward:
                bal = add_coins(did, reward)
                add_coin_log(did, reward, "Günlük tapşırıq tamamlandı", "earn", bal)
            (winner_stats if did in winner_ids else loser_stats)[did] = stats

        if results:
            for p, r in zip(winner_team, results["winners"]):
                did    = p["discord_id"]
                streak, _ = update_streak(did, True)
                s_coins, s_elo = get_streak_bonus(streak)
                earned = random.randint(5, 10) + s_coins
                if s_elo:
                    from database import _get_conn as _gc2
                    _c2 = _gc2(); _cur2 = _c2.cursor()
                    _cur2.execute("UPDATE players SET elo=elo+? WHERE discord_id=?", (s_elo, did))
                    _c2.commit(); _c2.close()
                bal    = add_coins(did, earned)
                add_coin_log(did, earned, f"Matç No{self.match_number} qələbə" + (f" (streak {streak})" if s_coins else ""), "earn", bal)
                winner_coins[did] = (earned, bal)
                add_season_stat(did, season["id"], wins=1, elo_gained=max(0, r["new_elo"]-r["old_elo"]))
                record_elo_history(did, r["new_elo"])
                check_and_grant_achievements(did)
                s = self.parsed.get(did, {})
                update_personal_record(did, s.get("kills",0), s.get("assists",0), s.get("deaths",0), self.match_number)
                # Battle Pass XP — qələbə
                _bp_xp = 200 + s.get("kills",0)*10 + s.get("assists",0)*5
                _bp_res = add_bp_xp(did, _bp_xp)
                update_bp_mission(did, "wins", 1)
                update_bp_mission(did, "matches", 1)
                update_bp_mission(did, "kills", s.get("kills",0))
                update_bp_mission(did, "assists", s.get("assists",0))
            for p, r in zip(loser_team, results["losers"]):
                did    = p["discord_id"]
                update_streak(did, False)
                earned = random.randint(0, 5)
                bal    = add_coins(did, earned)
                add_coin_log(did, earned, f"Matç No{self.match_number} iştirak", "earn", bal)
                loser_coins[did] = (earned, bal)
                add_season_stat(did, season["id"], losses=1,
                                elo_gained=max(0, r["new_elo"] - r["old_elo"]))
                record_elo_history(did, r["new_elo"])
                check_and_grant_achievements(did)
                s = self.parsed.get(did, {})
                update_personal_record(did, s.get("kills",0), s.get("assists",0), s.get("deaths",0), self.match_number)
                # Battle Pass XP — məğlubiyyət
                _bp_xp = 100 + s.get("kills",0)*10 + s.get("assists",0)*5
                add_bp_xp(did, _bp_xp)
                update_bp_mission(did, "matches", 1)
                update_bp_mission(did, "kills", s.get("kills",0))
                update_bp_mission(did, "assists", s.get("assists",0))

            winner_results = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                              for p, r in zip(winner_team, results["winners"])]
            loser_results  = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                              for p, r in zip(loser_team, results["losers"])]
            await asyncio.to_thread(record_match_history, "5v5",
                winner_ids, loser_ids,
                [r["old_elo"] for r in results["winners"]],
                [r["new_elo"] for r in results["winners"]],
                [r["old_elo"] for r in results["losers"]],
                [r["new_elo"] for r in results["losers"]],
                self.match_number)

            # MVP hesabla
            all_pl = winner_team + loser_team
            all_st = {**winner_stats, **loser_stats}
            mvp_p, mvp_ka = _apply_mvp(all_pl, all_st)
            mvp_nick = mvp_p["nick"] if mvp_p else None

            # Logs mesajını edit et
            now_az = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
            result_embed = _build_match_result_embed(
                self.match_number, sel_map, winner_label_full,
                winner_team, loser_team,
                winner_results, loser_results,
                winner_stats, loser_stats,
                now_az.strftime("%d.%m.%Y %H:%M"),
                mvp_nick=mvp_nick, mvp_ka=mvp_ka
            )
            await _edit_log_match_message(result_embed)

            # Nəticə kartı log kanalına
            result_img = os.path.join(DATA_DIR or ".", f"result_{self.match_number}.png")
            loser_label_full = "Komanda B" if self.winner_label == "A" else "Komanda A"
            await asyncio.to_thread(generate_result_card,
                self.match_number, winner_label_full, loser_label_full,
                winner_team, loser_team,
                winner_results, loser_results,
                winner_coins, loser_coins,
                now_az.strftime("%d.%m.%Y %H:%M"), result_img)
            log_ch = bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                await log_ch.send(file=discord.File(result_img, filename="result.png"))

        # Matç icmalı DM-ləri göndər
        if interaction.guild and results:
            w_res = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                     for p, r in zip(winner_team, results["winners"])]
            l_res = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                     for p, r in zip(loser_team, results["losers"])]
            asyncio.create_task(_send_match_summary(
                interaction.guild, self.match_number, winner_label_full,
                winner_team, loser_team, w_res, l_res,
                {**winner_stats, **loser_stats}, mvp_nick=mvp_nick
            ))

        # Mərc nəticələrini həll et
        pred_winners = resolve_predictions(self.match_number, winner_label_full)
        for pw in pred_winners:
            new_bal = get_coins(pw["discord_id"])
            add_coin_log(pw["discord_id"], pw["payout"],
                         f"Merc qalibiyyeti — Matc No{self.match_number} (+{pw['payout']} coin)",
                         "earn", new_bal)
            member = interaction.guild.get_member(pw["discord_id"]) if interaction.guild else None
            if member:
                try:
                    await member.send(
                        f"🎲 **Matç No{self.match_number}** — Mərc qazandınız!\n"
                        f"Mərc: {pw['bet']} coin → Qazanc: **+{pw['payout']} coin** 🎉"
                    )
                except discord.Forbidden:
                    pass

        clear_active_match()
        await asyncio.to_thread(backup.export_backup)

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"✅ **Matç No{self.match_number}** tamamlandı — 🏆 **{winner_label_full}**",
            embed=None, view=self)

        # Matç xülasəsi kartı
        log_ch_r = bot.get_channel(LOG_CHANNEL_ID)
        if log_ch_r and results:
            try:
                sel_map = self.view_ref.parsed[0].get("map", "?") if hasattr(self, "view_ref") else "?"
                w_team = winner_team if winner_label_full == "Komanda A" else loser_team
                l_team = loser_team  if winner_label_full == "Komanda A" else winner_team
                w_res  = results["winners"] if winner_label_full == "Komanda A" else results["losers"]
                l_res  = results["losers"]  if winner_label_full == "Komanda A" else results["winners"]
                rc_a = [{"nick": p["nick"],
                          "kills": self.stats.get(p["discord_id"], {}).get("kills", 0),
                          "assists": self.stats.get(p["discord_id"], {}).get("assists", 0),
                          "deaths": self.stats.get(p["discord_id"], {}).get("deaths", 0),
                          "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                         for p, r in zip(w_team, w_res)]
                rc_b = [{"nick": p["nick"],
                          "kills": self.stats.get(p["discord_id"], {}).get("kills", 0),
                          "assists": self.stats.get(p["discord_id"], {}).get("assists", 0),
                          "deaths": self.stats.get(p["discord_id"], {}).get("deaths", 0),
                          "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                         for p, r in zip(l_team, l_res)]
                sc_w = 13; sc_l = int(winner_label_full.split()[-1][-2:]) if "13" not in winner_label_full else 0
                rc_path = os.path.join(DATA_DIR or ".", f"recap_{self.match_number}.png")
                await asyncio.to_thread(
                    generate_match_recap_card,
                    self.match_number, getattr(self, "selected_map", "?"),
                    sc_w, sc_l, winner_label_full, rc_a, rc_b, rc_path)
                await log_ch_r.send(file=discord.File(rc_path, filename="recap.png"))
            except Exception as _re:
                print(f"[SCAN RECAP]: {_re}", flush=True)

        if queue_size() >= 10 and interaction.guild:
            await _start_match(interaction.channel, interaction.guild)

    @discord.ui.button(label="Ləğv et ❌", style=discord.ButtonStyle.secondary, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Scan ləğv edildi.", embed=None, view=None)


@bot.tree.command(name="scan", description="[Admin] Kanalın son şəklini scan et (şəkli reply edib /scan yaz)")
@app_commands.describe(qalib="Qalib komanda (A və ya B)")
@app_commands.checks.has_permissions(administrator=True)
async def scan_cmd(interaction: discord.Interaction, qalib: str = "A"):
    active = get_active_match()
    if not active:
        await interaction.response.send_message("❌ Aktiv matç yoxdur.", ephemeral=True)
        return

    qalib = qalib.strip().upper()
    if qalib not in ("A", "B"):
        await interaction.response.send_message("❌ Qalib A və ya B olmalıdır.", ephemeral=True)
        return

    await interaction.response.defer()

    # Kanalın son 20 mesajında şəkil tap
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
            "❌ Son 20 mesajda şəkil tapılmadı.\n"
            "Kapitan şəkli göndərsin, siz həmin şəklə reply edib `/scan` yazın.",
            ephemeral=True)
        return

    await interaction.followup.send("🔍 Claude Vision analiz edir...", ephemeral=True)
    try:
        ocr_results = await asyncio.to_thread(ocr_scoreboard, img_bytes)
    except Exception as e:
        await interaction.followup.send(f"❌ OCR xətası: {e}", ephemeral=True)
        return

    match_number = active["match_number"]
    team_a = active.get("team_a", [])
    team_b = active.get("team_b", [])
    all_players = team_a + team_b

    parsed = match_to_registered(ocr_results, all_players)
    parsed = apply_defaults_for_missing(all_players, parsed)

    embed = _build_scan_embed(match_number, parsed, qalib)
    view  = ScanEditView(match_number, parsed, qalib, all_players)
    await interaction.followup.send(embed=embed, view=view)


@scan_cmd.error
async def scan_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər üçündür.", ephemeral=True)


@bot.tree.command(name="ping", description="Bot cavab verir?")
async def ping_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! Gecikmə: `{round(bot.latency * 1000)}ms`", ephemeral=True)


@bot.tree.command(name="scan_test", description="Scan sistemini test et — kanalın son şəkli istifadə edilir")
async def scan_test_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Yalnız adminlər üçündür.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

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
        await interaction.followup.send("❌ Son 20 mesajda şəkil tapılmadı.", ephemeral=True)
        return

    try:
        ocr_results = await asyncio.to_thread(ocr_scoreboard, img_bytes)
    except Exception as e:
        await interaction.followup.send(f"❌ OCR xətası: {e}", ephemeral=True)
        return

    if not ocr_results:
        await interaction.followup.send(
            "⚠️ Heç bir oyunçu tapılmadı. Şəkil aydın və yaxın çəkilmiş olmalıdır.",
            ephemeral=True)
        return

    lines = [f"👤 **{r['nick']}** — K:{r['kills']} A:{r['assists']} D:{r['deaths']}"
             for r in ocr_results]
    embed = discord.Embed(
        title="🧪 Scan Test — OCR Nəticəsi",
        description="\n".join(lines),
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"{len(ocr_results)} oyunçu oxundu  ·  Data yazılmadı")
    await interaction.followup.send(embed=embed, ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MANUEL STAT GİRİŞİ
# ═══════════════════════════════════════════════════════════════════════════════

class ManuelPlayerStatModal(discord.ui.Modal, title="Stat Giriş"):
    kills_inp   = discord.ui.TextInput(label="Kill",  placeholder="0", required=True, max_length=3)
    assists_inp = discord.ui.TextInput(label="Asist", placeholder="0", required=True, max_length=3)
    deaths_inp  = discord.ui.TextInput(label="Ölüm",  placeholder="0", required=True, max_length=3)

    def __init__(self, player: dict, view_ref):
        super().__init__(title=f"{player['nick'][:22]} — Stat")
        self.player   = player
        self.view_ref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        try:
            k = int(self.kills_inp.value)
            a = int(self.assists_inp.value)
            d = int(self.deaths_inp.value)
        except ValueError:
            await interaction.response.send_message("❌ Yalnız rəqəm daxil edin.", ephemeral=True)
            return
        did = self.player["discord_id"]
        self.view_ref.stats[did] = {"kills": k, "assists": a, "deaths": d}
        # Düymənin rəngini dəyiş (✓ işarəsi)
        for item in self.view_ref.children:
            if getattr(item, "_player_id", None) == did:
                item.style = discord.ButtonStyle.success
                item.label = f"✓ {self.player['nick'][:16]}"
                break
        embed = self.view_ref.build_embed()
        await interaction.response.edit_message(embed=embed, view=self.view_ref)


class ManuelMatchStatView(discord.ui.View):
    def __init__(self, match_number: int, team_a: list, team_b: list):
        super().__init__(timeout=600)
        self.match_number = match_number
        self.team_a  = team_a
        self.team_b  = team_b
        self.stats   = {}        # {discord_id: {kills, assists, deaths}}
        self.winner  = None      # "A" veya "B"
        self.done    = False

        # Oyunçu düymələri — A komandası row 0, B komandası row 1
        for row_idx, team in enumerate([team_a, team_b]):
            for p in team:
                btn = discord.ui.Button(
                    label=p["nick"][:20],
                    style=discord.ButtonStyle.secondary,
                    row=row_idx
                )
                btn._player_id = p["discord_id"]
                async def _cb(inter, player=p):
                    if not inter.user.guild_permissions.administrator:
                        await inter.response.send_message("❌", ephemeral=True)
                        return
                    await inter.response.send_modal(ManuelPlayerStatModal(player, self))
                btn.callback = _cb
                self.add_item(btn)

        # Qalib düymələri — row 2
        btn_a = discord.ui.Button(label="Qalib: Komanda A", style=discord.ButtonStyle.primary,  emoji="🔵", row=2)
        btn_b = discord.ui.Button(label="Qalib: Komanda B", style=discord.ButtonStyle.danger,   emoji="🔴", row=2)

        async def _win_a(inter):
            if not inter.user.guild_permissions.administrator:
                await inter.response.send_message("❌", ephemeral=True); return
            self.winner = "A"
            await inter.response.edit_message(embed=self.build_embed(), view=self)
        async def _win_b(inter):
            if not inter.user.guild_permissions.administrator:
                await inter.response.send_message("❌", ephemeral=True); return
            self.winner = "B"
            await inter.response.edit_message(embed=self.build_embed(), view=self)

        btn_a.callback = _win_a
        btn_b.callback = _win_b
        self.add_item(btn_a)
        self.add_item(btn_b)

        # Sisteme ver — row 3
        btn_submit = discord.ui.Button(label="Sisteme Ver ✅", style=discord.ButtonStyle.success, row=3)
        btn_cancel = discord.ui.Button(label="Ləğv et ❌",     style=discord.ButtonStyle.secondary, row=3)

        async def _submit(inter):
            if not inter.user.guild_permissions.administrator:
                await inter.response.send_message("❌", ephemeral=True); return
            if self.done:
                await inter.response.send_message("⚠️ Artıq göndərildi.", ephemeral=True); return
            if self.winner is None:
                await inter.response.send_message("❌ Əvvəlcə qalib komandanı seçin.", ephemeral=True); return
            missing = [p["nick"] for p in self.team_a + self.team_b
                       if p["discord_id"] not in self.stats]
            if missing:
                await inter.response.send_message(
                    f"⚠️ Bu oyunçuların statı daxil edilməyib: **{', '.join(missing)}**\n"
                    f"Onlar üçün 0/0/5 verilsin? Evet üçün yenidən Sisteme Ver düyməsinə basın.",
                    ephemeral=True)
                for p in self.team_a + self.team_b:
                    if p["discord_id"] not in self.stats:
                        self.stats[p["discord_id"]] = {"kills": 0, "assists": 0, "deaths": 5}
                return
            await self._finalize(inter)

        async def _cancel(inter):
            self.done = True
            for c in self.children:
                c.disabled = True
            await inter.response.edit_message(content="❌ Ləğv edildi.", embed=None, view=self)

        btn_submit.callback = _submit
        btn_cancel.callback = _cancel
        self.add_item(btn_submit)
        self.add_item(btn_cancel)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"📝 Matç No{self.match_number} — Manuel Stat",
            color=discord.Color.orange()
        )

        def fmt_team(team, label):
            lines = []
            for p in team:
                s = self.stats.get(p["discord_id"])
                if s:
                    lines.append(f"✅ **{p['nick']}** — K:{s['kills']} A:{s['assists']} D:{s['deaths']}")
                else:
                    lines.append(f"⬜ **{p['nick']}** — ?")
            return "\n".join(lines)

        embed.add_field(name="🔵 Komanda A", value=fmt_team(self.team_a, "A"), inline=True)
        embed.add_field(name="🔴 Komanda B", value=fmt_team(self.team_b, "B"), inline=True)
        entered = len(self.stats)
        total   = len(self.team_a) + len(self.team_b)
        winner_txt = f"Komanda **{self.winner}**" if self.winner else "Seçilməyib"
        embed.set_footer(text=f"Stat: {entered}/{total}  |  Qalib: {winner_txt}")
        return embed

    async def _finalize(self, interaction):
        self.done = True
        for c in self.children:
            c.disabled = True

        winner_team = self.team_a if self.winner == "A" else self.team_b
        loser_team  = self.team_b if self.winner == "A" else self.team_a
        winner_label = f"Komanda {self.winner}"
        loser_label  = f"Komanda {'B' if self.winner == 'A' else 'A'}"

        winner_ids = [p["discord_id"] for p in winner_team]
        loser_ids  = [p["discord_id"] for p in loser_team]

        results = update_team_elo(winner_ids, loser_ids)
        if results is None:
            await interaction.response.edit_message(content="❌ ELO yenilənmədi.", view=self)
            return

        winner_coins, loser_coins = {}, {}
        for did in winner_ids:
            earned = random.randint(5, 10)
            bal    = add_coins(did, earned)
            add_coin_log(did, earned, f"Matç No{self.match_number} qələbə", "earn", bal)
            winner_coins[did] = (earned, bal)
        for did in loser_ids:
            earned = random.randint(0, 5)
            bal    = add_coins(did, earned)
            add_coin_log(did, earned, f"Matç No{self.match_number} iştirak", "earn", bal)
            loser_coins[did] = (earned, bal)

        season = get_or_create_current_season()
        for p, r in zip(winner_team, results["winners"]):
            did = p["discord_id"]
            s   = self.stats[did]
            add_combat_stats(did, s["kills"], s["assists"], s["deaths"])
            add_season_stat(did, season["id"], kills=s["kills"], assists=s["assists"],
                            deaths=s["deaths"], wins=1, elo_gained=max(0, r["new_elo"]-r["old_elo"]))
            completed, reward = update_task_progress(did, s["kills"], s["assists"])
            if completed and reward:
                bal2 = add_coins(did, reward)
                add_coin_log(did, reward, "Günlük tapşırıq tamamlandı", "earn", bal2)
        for p, r in zip(loser_team, results["losers"]):
            did = p["discord_id"]
            s   = self.stats[did]
            add_combat_stats(did, s["kills"], s["assists"], s["deaths"])
            add_season_stat(did, season["id"], kills=s["kills"], assists=s["assists"],
                            deaths=s["deaths"], losses=1, elo_gained=max(0, r["new_elo"]-r["old_elo"]))
            completed, reward = update_task_progress(did, s["kills"], s["assists"])
            if completed and reward:
                bal2 = add_coins(did, reward)
                add_coin_log(did, reward, "Günlük tapşırıq tamamlandı", "earn", bal2)

        await asyncio.to_thread(
            record_match_history, "5v5",
            winner_ids, loser_ids,
            [r["old_elo"] for r in results["winners"]],
            [r["new_elo"] for r in results["winners"]],
            [r["old_elo"] for r in results["losers"]],
            [r["new_elo"] for r in results["losers"]],
            self.match_number
        )
        # Mərc nəticələrini həll et
        _wlabel_m = f"Komanda {self.winner}"
        pred_winners_m = resolve_predictions(self.match_number, _wlabel_m)
        for pw in pred_winners_m:
            new_bal = get_coins(pw["discord_id"])
            add_coin_log(pw["discord_id"], pw["payout"],
                         f"Merc qalibiyyeti — Matc No{self.match_number} (+{pw['payout']} coin)",
                         "earn", new_bal)

        clear_active_match()
        await asyncio.to_thread(backup.export_backup)

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        ts  = now.strftime("%d.%m.%Y %H:%M")

        winner_results = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                          for p, r in zip(winner_team, results["winners"])]
        loser_results  = [{"nick": p["nick"], "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                          for p, r in zip(loser_team, results["losers"])]

        # MVP hesabla
        w_stats_d = {p["discord_id"]: self.stats[p["discord_id"]] for p in winner_team if p["discord_id"] in self.stats}
        l_stats_d = {p["discord_id"]: self.stats[p["discord_id"]] for p in loser_team  if p["discord_id"] in self.stats}
        mvp_p2, mvp_ka2 = _apply_mvp(winner_team + loser_team, {**w_stats_d, **l_stats_d})
        mvp_nick2 = mvp_p2["nick"] if mvp_p2 else None

        # Logs mesajını edit et
        sel_map = active.get("selected_map", "?") if (active := get_active_match()) else "?"
        result_embed = _build_match_result_embed(
            self.match_number, sel_map, winner_label,
            winner_team, loser_team,
            winner_results, loser_results,
            w_stats_d, l_stats_d, ts,
            mvp_nick=mvp_nick2, mvp_ka=mvp_ka2
        )
        await _edit_log_match_message(result_embed)

        result_img = os.path.join(DATA_DIR or ".", f"result_{self.match_number}.png")
        await asyncio.to_thread(
            generate_result_card,
            self.match_number, winner_label, loser_label,
            winner_team, loser_team,
            winner_results, loser_results,
            winner_coins, loser_coins,
            ts, result_img
        )

        await interaction.response.edit_message(
            content=f"✅ Matç No{self.match_number} tamamlandı — 🏆 **{winner_label}**",
            embed=None, view=self
        )
        log_ch = bot.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(file=discord.File(result_img, filename="result.png"))
            # Matç xülasəsi kartı
            try:
                rc_a = [{"nick": p["nick"],
                          "kills": self.stats.get(p["discord_id"], {}).get("kills", 0),
                          "assists": self.stats.get(p["discord_id"], {}).get("assists", 0),
                          "deaths": self.stats.get(p["discord_id"], {}).get("deaths", 0),
                          "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                         for p, r in zip(winner_team, results["winners"])]
                rc_b = [{"nick": p["nick"],
                          "kills": self.stats.get(p["discord_id"], {}).get("kills", 0),
                          "assists": self.stats.get(p["discord_id"], {}).get("assists", 0),
                          "deaths": self.stats.get(p["discord_id"], {}).get("deaths", 0),
                          "old_elo": r["old_elo"], "new_elo": r["new_elo"]}
                         for p, r in zip(loser_team, results["losers"])]
                _sel_map = get_active_match().get("selected_map", "?") if get_active_match() else "?"
                rc_path  = os.path.join(DATA_DIR or ".", f"recap_{self.match_number}.png")
                await asyncio.to_thread(
                    generate_match_recap_card,
                    self.match_number, _sel_map, 13, 0,
                    winner_label, rc_a, rc_b, rc_path)
                await log_ch.send(file=discord.File(rc_path, filename="recap.png"))
            except Exception as _re:
                print(f"[MANUEL RECAP]: {_re}", flush=True)

        if queue_size() >= 10 and interaction.guild:
            await _start_match(interaction.channel, interaction.guild)


@bot.tree.command(name="manuel_stat", description="[Admin] Aktiv matçın statlarını manuel daxil et")
@app_commands.checks.has_permissions(administrator=True)
async def manuel_stat_cmd(interaction: discord.Interaction):
    active = get_active_match()
    if not active:
        await interaction.response.send_message("❌ Aktiv matç yoxdur.", ephemeral=True)
        return

    team_a = active.get("team_a", [])
    team_b = active.get("team_b", [])

    if not team_a or not team_b:
        await interaction.response.send_message(
            "❌ Matç oyunçu məlumatları tapılmadı. Yeni matç başladıqda bu funksiya işləyəcək.",
            ephemeral=True)
        return

    view  = ManuelMatchStatView(active["match_number"], team_a, team_b)
    embed = view.build_embed()
    await interaction.response.send_message(embed=embed, view=view)


@manuel_stat_cmd.error
async def manuel_stat_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər üçündür.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SEZON KOMANDası
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="sezon", description="Sezon leaderboardunu göstərir")
@app_commands.describe(nomre="Sezon nömrəsi (boş buraxsanız cari sezon)")
async def sezon_cmd(interaction: discord.Interaction, nomre: int = 0):
    await interaction.response.defer()
    import datetime as dt

    if nomre == 0:
        season = get_or_create_current_season()
    else:
        season = get_season_by_number(nomre)
        if not season:
            await interaction.followup.send(f"❌ Sezon {nomre} tapılmadı.", ephemeral=True)
            return

    rows = get_season_leaderboard(season["id"])
    lb_path = os.path.join(DATA_DIR or ".", f"season_lb_{season['season_number']}.png")
    await asyncio.to_thread(
        generate_season_leaderboard_image, rows,
        season["season_number"], season["start_date"], season["end_date"], lb_path
    )

    await interaction.followup.send(
        file=discord.File(lb_path, filename="season_lb.png"),
        view=SezonNavView(season["season_number"], season["id"]))


@bot.tree.command(name="sezon_elan", description="[Admin] Sezon sonu elanını yenidən göndər")
@app_commands.describe(nomre="Sezon nömrəsi", kanal="Hansı kanala (boş = faceit-logs)")
@app_commands.checks.has_permissions(administrator=True)
async def sezon_elan_cmd(interaction: discord.Interaction, nomre: int, kanal: discord.TextChannel = None):
    await interaction.response.defer(ephemeral=True)
    season = get_season_by_number(nomre)
    if not season:
        await interaction.followup.send(f"❌ Sezon {nomre} tapılmadı.", ephemeral=True)
        return

    rows   = get_season_leaderboard(season["id"])
    target = kanal or bot.get_channel(LOG_CHANNEL_ID)
    if not target:
        await interaction.followup.send("❌ Kanal tapılmadı.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🏆 SEZON {season['season_number']} TAMAMLANDI!",
        description=f"Sezon: {season['start_date']}  —  {season['end_date']}",
        color=discord.Color.gold()
    )
    medals  = ["🥇", "🥈", "🥉"]
    rewards = [500, 300, 150]
    for i, r in enumerate(rows[:3]):
        nick       = r[0]
        elo_gained = r[2]
        embed.add_field(
            name=f"{medals[i]} {nick}",
            value=f"+{elo_gained} ELO  ·  +{rewards[i]} coin mükafat",
            inline=False
        )
    if not rows:
        embed.description += "\n\nBu sezonda matç oynanılmadı."

    import datetime as _dt
    embed.set_footer(text=f"Calestify FACEIT  ·  {_dt.datetime.utcnow().strftime('%d.%m.%Y')}")

    await target.send(embed=embed)
    await interaction.followup.send(f"✅ Sezon {nomre} elanı #{target.name} kanalına göndərildi.", ephemeral=True)


@sezon_elan_cmd.error
async def sezon_elan_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="pass_elan", description="[Admin] Season 1 Battle Pass tanıtım elanını kanala göndər")
@app_commands.describe(kanal="Elanın göndəriləcəyi kanal (boş = bu kanal)")
@app_commands.checks.has_permissions(administrator=True)
async def pass_elan_cmd(interaction: discord.Interaction, kanal: discord.TextChannel = None):
    target = kanal or interaction.channel
    await interaction.response.defer(ephemeral=True)

    card_path = os.path.join(DATA_DIR or ".", "pass_announcement.png")
    try:
        await asyncio.to_thread(generate_pass_announcement, card_path)
    except Exception as e:
        print(f"[PASS_ELAN] Kart xətası: {e}", flush=True)
        await interaction.followup.send(f"❌ Kart yaradılmadı: {e}", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 SEASON 1 BATTLE PASS — AKTİVDİR!",
        description=(
            "**Calestify FACEIT**-də Season 1 Battle Pass başladı!\n\n"
            "**FREE PASS** — hamı üçün pulsuz açılır\n"
            "**VIP PASS** — 7 AZN, əlavə xüsusi mükafatlar\n\n"
            "XP qazanmaq üçün matç oynayın, missiyaları tamamlayın!\n"
            "Level 30-da **AWM BOOM** skini VIP oyunçuları gözləyir."
        ),
        color=0xFFCC00
    )
    embed.add_field(name="📋 Açmaq üçün",   value="`/pass`",           inline=True)
    embed.add_field(name="💰 VIP qiyməti",   value="**7 AZN**",        inline=True)
    embed.add_field(name="🏆 Level 30 mükafat", value="AWM BOOM skin", inline=True)
    embed.set_footer(text="Calestify Gaming Community  •  Season 1")

    await target.send(file=discord.File(card_path, filename="pass_season1.png"), embed=embed)
    await interaction.followup.send(f"✅ Pass elanı #{target.name} kanalına göndərildi.", ephemeral=True)


@pass_elan_cmd.error
async def pass_elan_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GÜNDƏLİK TAPŞIRIQLAR
# ═══════════════════════════════════════════════════════════════════════════════

class TaskSelectView(discord.ui.View):
    def __init__(self, discord_id, tasks):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        for t in tasks:
            label = f"🎯 {t['description'][:60]}"
            btn   = discord.ui.Button(label=label[:80], style=discord.ButtonStyle.primary,
                                      custom_id=f"task_{t['id']}")
            async def _cb(inter: discord.Interaction, task=t):
                if inter.user.id != self.discord_id:
                    await inter.response.send_message("❌ Bu sizin üçün deyil.", ephemeral=True)
                    return
                existing = get_player_active_task(inter.user.id)
                if existing:
                    await inter.response.send_message("⚠️ Artıq aktiv tapşırığınız var.", ephemeral=True)
                    return
                ok = assign_task_to_player(inter.user.id, task["id"])
                if ok:
                    await inter.response.edit_message(
                        content=f"✅ Tapşırıq qəbul edildi!\n**{task['description']}**\nMükafat: 🪙 **{task['reward_coins']} coin**",
                        embed=None, view=None)
                else:
                    await inter.response.send_message("❌ Bu tapşırıq artıq seçilib.", ephemeral=True)
            btn.callback = _cb
            self.add_item(btn)


@bot.tree.command(name="gunluk", description="Günlük tapşırıqları göstərir")
async def gunluk_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    refresh_daily_tasks()
    fail_expired_tasks()
    active = get_player_active_task(interaction.user.id)
    tasks  = get_active_daily_tasks()

    if not active and not tasks:
        await interaction.followup.send("⏳ Hazırda aktiv tapşırıq yoxdur.", ephemeral=True)
        return

    path = os.path.join(DATA_DIR or ".", f"tasks_{interaction.user.id}.png")
    await asyncio.to_thread(generate_tasks_card, active, tasks, path)

    view = TaskSelectView(interaction.user.id, tasks) if not active and tasks else None
    await interaction.followup.send(file=discord.File(path, filename="tasks.png"), view=view, ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# XƏBƏRDARLIQ / BAN SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="warn", description="[Admin] Oyunçuya xəbərdarlıq ver")
@app_commands.describe(uzv="Xəbərdarlıq veriləcək üzv", sebeb="Xəbərdarlıq səbəbi")
@app_commands.checks.has_permissions(administrator=True)
async def warn_cmd(interaction: discord.Interaction, uzv: discord.Member, sebeb: str):
    await interaction.response.defer(ephemeral=True)
    count = add_warning(uzv.id, sebeb, interaction.user.id)
    warns = get_warnings(uzv.id)
    banned = is_banned(uzv.id)
    path  = os.path.join(DATA_DIR or ".", f"warns_{uzv.id}.png")
    await asyncio.to_thread(generate_warnings_card, uzv.display_name, warns, banned, path)
    try:
        await uzv.send(_t(uzv.id, 'warn_dm', count=count, reason=sebeb))
    except discord.Forbidden:
        pass
    if count >= 3 and not banned:
        ban_player(uzv.id, "3 xəbərdarlıq avtomatik ban", interaction.user.id)
        await interaction.followup.send(
            f"🔴 {uzv.mention} **avtomatik banlandı** (3 xəbərdarlıq tamamlandı).",
            file=discord.File(path, filename="warns.png"), ephemeral=False)
    else:
        await interaction.followup.send(
            f"⚠️ {uzv.mention} xəbərdarlıq #{count} verildi.",
            file=discord.File(path, filename="warns.png"), ephemeral=False)


@warn_cmd.error
async def warn_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="ban", description="[Admin] Oyunçunu banla — /ban @uzv Səbəb 2h (müvvəqəti) və ya saatsız (daimi)")
@app_commands.describe(uzv="Banlanacaq üzv", sebeb="Səbəb", muddet="Müvvəqəti müddət: 1h, 30m, 2d (boş=daimi)")
@app_commands.checks.has_permissions(administrator=True)
async def ban_cmd(interaction: discord.Interaction, uzv: discord.Member,
                  sebeb: str, muddet: str = ""):
    seconds = 0
    label   = "DAİMİ"
    if muddet:
        import re as _re
        for val, unit in _re.findall(r'(\d+)([hdm])', muddet.lower()):
            mult = {"h": 3600, "d": 86400, "m": 60}.get(unit, 0)
            seconds += int(val) * mult
        if seconds > 0:
            label = muddet.upper()

    if seconds > 0:
        until = temp_ban(uzv.id, seconds, sebeb, interaction.user.id)
        import datetime as _dt
        exp_str = (_dt.datetime.utcfromtimestamp(until) + _dt.timedelta(hours=4)).strftime("%d.%m %H:%M")
        msg    = f"🔴 {uzv.mention} **{label}** banlandı (bitmə: {exp_str}). Səbəb: {sebeb}"
        dm_msg = _t(uzv.id, 'ban_temp_dm', label=label, reason=sebeb, exp=exp_str)
    else:
        ban_player(uzv.id, sebeb, interaction.user.id)
        msg    = f"🔴 {uzv.mention} DAİMİ banlandı. Səbəb: {sebeb}"
        dm_msg = _t(uzv.id, 'ban_perm_dm', reason=sebeb)

    remove_from_queue(uzv.id)
    try:
        await uzv.send(dm_msg)
    except discord.Forbidden:
        pass
    await interaction.response.send_message(msg, ephemeral=False)


@ban_cmd.error
async def ban_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="unban", description="[Admin] Oyunçunun banını aç")
@app_commands.describe(uzv="Banı açılacaq üzv")
@app_commands.checks.has_permissions(administrator=True)
async def unban_cmd(interaction: discord.Interaction, uzv: discord.Member):
    unban_player(uzv.id)
    clear_warnings(uzv.id)
    try:
        await uzv.send(_t(uzv.id, 'unban_dm'))
    except discord.Forbidden:
        pass
    await interaction.response.send_message(f"✅ {uzv.mention} banı açıldı, xəbərdarlıqlar silindi.", ephemeral=False)


@unban_cmd.error
async def unban_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="xeberdarliqlar", description="Oyunçunun xəbərdarlıqlarını göstər")
@app_commands.describe(uzv="Üzv (boş = özünüz)")
@app_commands.checks.has_permissions(administrator=True)
async def warns_cmd(interaction: discord.Interaction, uzv: discord.Member = None):
    target = uzv or interaction.user
    await interaction.response.defer(ephemeral=True)
    warns  = get_warnings(target.id)
    banned = is_banned(target.id)
    path   = os.path.join(DATA_DIR or ".", f"warns_{target.id}.png")
    await asyncio.to_thread(generate_warnings_card, target.display_name, warns, banned, path)
    await interaction.followup.send(file=discord.File(path, filename="warns.png"), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NAVİQASİYA VİEW SİNİFLƏRİ
# ═══════════════════════════════════════════════════════════════════════════════

class StatsNavView(discord.ui.View):
    def __init__(self, target_id: int):
        super().__init__(timeout=300)
        self.target_id = target_id

    @discord.ui.button(label="ELO Qrafik", emoji="📈", style=discord.ButtonStyle.secondary)
    async def show_elo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.target_id)
        if not player:
            await interaction.followup.send("❌ Oyunçu tapılmadı.", ephemeral=True); return
        history = get_elo_history(self.target_id, limit=30)
        peak    = get_peak_elo(self.target_id)
        path    = os.path.join(DATA_DIR or ".", f"elo_graph_{self.target_id}.png")
        try:
            await asyncio.to_thread(generate_elo_graph, player[1], history, peak, path)
            await interaction.followup.send(file=discord.File(path, filename="elo_graph.png"),
                                            view=EloGrafikView(self.target_id), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Qrafik yaradıla bilmədi: {e}", ephemeral=True)

    @discord.ui.button(label="Nailiyyətlər", emoji="🏅", style=discord.ButtonStyle.secondary)
    async def show_ach(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.target_id)
        if not player:
            await interaction.followup.send("❌", ephemeral=True); return
        achs = get_player_achievements(self.target_id)
        path = os.path.join(DATA_DIR or ".", f"achievements_{self.target_id}.png")
        await asyncio.to_thread(generate_achievements_card, player[1], achs, path)
        await interaction.followup.send(file=discord.File(path, filename="achievements.png"),
                                        view=NailiyyetNavView(self.target_id), ephemeral=True)


class EloGrafikView(discord.ui.View):
    def __init__(self, target_id: int):
        super().__init__(timeout=300)
        self.target_id = target_id

    async def _regen(self, interaction: discord.Interaction, limit: int):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.target_id)
        if not player:
            await interaction.followup.send("❌", ephemeral=True); return
        history = get_elo_history(self.target_id, limit=limit)
        peak    = get_peak_elo(self.target_id)
        path    = os.path.join(DATA_DIR or ".", f"elo_graph_{self.target_id}.png")
        await asyncio.to_thread(generate_elo_graph, player[1], history, peak, path)
        lbl = f"Son {limit}" if limit < 200 else "Bütün tarix"
        await interaction.followup.send(
            content=f"📊 **{lbl}** — {player[1]}",
            file=discord.File(path, filename="elo_graph.png"),
            view=EloGrafikView(self.target_id), ephemeral=True)

    @discord.ui.button(label="Son 10 Matç", emoji="📉", style=discord.ButtonStyle.secondary)
    async def last10(self, i, b): await self._regen(i, 10)

    @discord.ui.button(label="Son 30 Matç", emoji="📊", style=discord.ButtonStyle.primary)
    async def last30(self, i, b): await self._regen(i, 30)

    @discord.ui.button(label="Hamısı", emoji="📈", style=discord.ButtonStyle.secondary)
    async def all_hist(self, i, b): await self._regen(i, 200)


class NailiyyetNavView(discord.ui.View):
    def __init__(self, target_id: int):
        super().__init__(timeout=300)
        self.target_id = target_id

    @discord.ui.button(label="Statistika", emoji="📊", style=discord.ButtonStyle.secondary)
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.target_id)
        if not player:
            await interaction.followup.send("❌", ephemeral=True); return
        p = player
        pdata = {
            "nick": p[1], "so2_id": p[2], "elo": p[3], "wins": p[4], "losses": p[5],
            "coins": p[6], "zm_balance": p[9] if len(p)>9 else 0,
            "kills": p[11] if len(p)>11 else 0, "assists": p[12] if len(p)>12 else 0,
            "deaths": p[13] if len(p)>13 else 0, "win_streak": p[14] if len(p)>14 else 0,
            "max_streak": p[15] if len(p)>15 else 0,
        }
        achs = get_player_achievements(self.target_id)
        path = os.path.join(DATA_DIR or ".", f"stats_{self.target_id}.png")
        await asyncio.to_thread(generate_stats_card, pdata, achs, path)
        await interaction.followup.send(file=discord.File(path, filename="stats.png"),
                                        view=StatsNavView(self.target_id), ephemeral=True)


class SezonNavView(discord.ui.View):
    def __init__(self, season_number: int, season_id: int):
        super().__init__(timeout=300)
        self.season_number = season_number
        self.season_id     = season_id

    @discord.ui.button(label="Şəxsi Statistikam", emoji="📊", style=discord.ButtonStyle.secondary)
    async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(interaction.user.id)
        ss     = get_season_stat(interaction.user.id, self.season_id)
        if not player:
            await interaction.followup.send("❌ Qeydiyyat yoxdur.", ephemeral=True); return
        s_matches = (ss["wins"] + ss["losses"]) if ss else 0
        s_wr  = round(ss["wins"]/s_matches*100, 1) if s_matches else 0
        s_kd  = round(ss["kills"]/max(ss["deaths"],1), 2) if ss else 0
        embed = discord.Embed(
            title=f"📊 Sezon {self.season_number} — {player[1]}",
            color=discord.Color.teal()
        )
        embed.add_field(name="Matç",   value=str(s_matches),            inline=True)
        embed.add_field(name="Qələbə", value=str(ss["wins"] if ss else 0), inline=True)
        embed.add_field(name="Win%",   value=f"{s_wr}%",                inline=True)
        embed.add_field(name="Kill",   value=str(ss["kills"] if ss else 0),   inline=True)
        embed.add_field(name="K/D",    value=str(s_kd),                 inline=True)
        embed.add_field(name="Asist",  value=str(ss["assists"] if ss else 0), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Liderboard", emoji="🏆", style=discord.ButtonStyle.primary)
    async def show_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        season = get_season_by_number(self.season_number)
        if not season:
            await interaction.followup.send("❌", ephemeral=True); return
        rows   = get_season_leaderboard(season["id"])
        path   = os.path.join(DATA_DIR or ".", f"season_lb_{self.season_number}.png")
        await asyncio.to_thread(
            generate_season_leaderboard_image, rows,
            season["season_number"], season["start_date"], season["end_date"], path)
        await interaction.followup.send(file=discord.File(path, filename="season_lb.png"),
                                        view=SezonNavView(self.season_number, self.season_id), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# /STATS — BAŞQASININ STATİSTİKASI
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="stats", description="Oyunçunun statistikasını vizual göstər")
@app_commands.describe(uzv="Oyunçu (boş = özünüz)")
async def stats_cmd(interaction: discord.Interaction, uzv: discord.Member = None):
    target = uzv or interaction.user
    await interaction.response.defer()
    player = get_player(target.id)
    if not player:
        await interaction.followup.send("❌ Bu oyunçu qeydiyyatdan keçməyib.", ephemeral=True)
        return
    p = player
    player_data = {
        "nick": p[1], "so2_id": p[2], "elo": p[3], "wins": p[4], "losses": p[5],
        "coins": p[6], "zm_balance": p[9] if len(p) > 9 else 0,
        "kills":      p[11] if len(p) > 11 else 0,
        "assists":    p[12] if len(p) > 12 else 0,
        "deaths":     p[13] if len(p) > 13 else 0,
        "win_streak": p[14] if len(p) > 14 else 0,
        "max_streak": p[15] if len(p) > 15 else 0,
    }
    achs = get_player_achievements(target.id)
    pr   = get_personal_record(target.id)
    path = os.path.join(DATA_DIR or ".", f"stats_{target.id}.png")
    try:
        await asyncio.to_thread(generate_stats_card, player_data, achs, path)
        rec_embed = None
        if pr["best_kills"] > 0 or pr["best_kd"] > 0:
            rec_embed = discord.Embed(title="🏆 Şəxsi Rekordlar", color=discord.Color.gold())
            rec_embed.add_field(name="Max Kill (1 matçda)", value=str(pr["best_kills"]), inline=True)
            rec_embed.add_field(name="Max K/D (1 matçda)",  value=str(pr["best_kd"]),   inline=True)
            if pr["best_match"]:
                rec_embed.add_field(name="Matç No", value=str(pr["best_match"]), inline=True)
        await interaction.followup.send(
            file=discord.File(path, filename="stats.png"),
            embed=rec_embed,
            view=StatsNavView(target.id))
    except Exception as e:
        # Kart yaradıla bilmədisə embed fallback
        p2 = player_data
        kd = round(p2["kills"]/max(p2["deaths"],1), 2)
        wr = round(p2["wins"]/max(p2["wins"]+p2["losses"],1)*100, 1)
        rank_name, _, rank_emoji = get_rank(p2["elo"])
        embed = discord.Embed(title=f"📊 {p2['nick']} — Statistika", color=discord.Color.blurple())
        embed.add_field(name="ELO",     value=str(p2["elo"]),   inline=True)
        embed.add_field(name="Rank",    value=f"{rank_emoji} {rank_name}", inline=True)
        embed.add_field(name="Streak",  value=f"🔥 {p2['win_streak']} (Max:{p2['max_streak']})", inline=True)
        embed.add_field(name="Qələbə", value=str(p2["wins"]),  inline=True)
        embed.add_field(name="Win%",   value=f"{wr}%",          inline=True)
        embed.add_field(name="K/D",    value=str(kd),           inline=True)
        embed.add_field(name="Kill",   value=str(p2["kills"]),  inline=True)
        embed.add_field(name="Asist",  value=str(p2["assists"]),inline=True)
        embed.add_field(name="Ölüm",   value=str(p2["deaths"]), inline=True)
        await interaction.followup.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
# NAİLİYYƏTLƏR
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="nailiyyetler", description="Nailiyyətlərinizi vizual görün")
@app_commands.describe(uzv="Oyunçu (boş = özünüz)")
async def nailiyyetler_cmd(interaction: discord.Interaction, uzv: discord.Member = None):
    target = uzv or interaction.user
    await interaction.response.defer(ephemeral=True)
    player = get_player(target.id)
    if not player:
        await interaction.followup.send("❌ Qeydiyyat yoxdur.", ephemeral=True)
        return
    achs = get_player_achievements(target.id)
    path = os.path.join(DATA_DIR or ".", f"achievements_{target.id}.png")
    await asyncio.to_thread(generate_achievements_card, player[1], achs, path)
    await interaction.followup.send(file=discord.File(path, filename="achievements.png"),
                                    view=NailiyyetNavView(target.id), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MATÇ MƏRCİ
# ═══════════════════════════════════════════════════════════════════════════════

class PredictionView(discord.ui.View):
    def __init__(self, match_number: int):
        super().__init__(timeout=60)
        self.match_number = match_number

    @discord.ui.button(label="Komanda A 🔵", style=discord.ButtonStyle.primary)
    async def bet_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_bet_modal(interaction, "Komanda A")

    @discord.ui.button(label="Komanda B 🔴", style=discord.ButtonStyle.danger)
    async def bet_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_bet_modal(interaction, "Komanda B")

    async def _show_bet_modal(self, interaction: discord.Interaction, team: str):
        modal = BetModal(self.match_number, team)
        await interaction.response.send_modal(modal)


class BetModal(discord.ui.Modal):
    amount = discord.ui.TextInput(label="Mərc miqdarı (coin)", placeholder="50", required=True, max_length=5)

    def __init__(self, match_number, team):
        super().__init__(title=f"{team} üçün mərc")
        self.match_number = match_number
        self.team         = team

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.amount.value)
            if bet < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Düzgün məbləğ daxil edin.", ephemeral=True)
            return
        ok, msg = place_prediction(interaction.user.id, self.match_number, self.team, bet)
        color = discord.Color.green() if ok else discord.Color.red()
        embed = discord.Embed(description=f"{'✅' if ok else '❌'} {msg}", color=color)
        if ok:
            embed.add_field(name="Komanda", value=self.team, inline=True)
            embed.add_field(name="Mərc",   value=f"🪙 {bet}", inline=True)
            embed.set_footer(text="Düz tapsan 2x qazanırsan!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="merc", description="Aktiv matçın qalibi üçün coin mərc et")
async def merc_cmd(interaction: discord.Interaction):
    active = get_active_match()
    if not active:
        await interaction.response.send_message("❌ Aktiv matç yoxdur.", ephemeral=True)
        return
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisən.", ephemeral=True)
        return
    coins     = get_coins(interaction.user.id)
    bet_path  = os.path.join(DATA_DIR or ".", f"bet_{active['match_number']}.png")
    await interaction.response.defer(ephemeral=True)
    try:
        await asyncio.to_thread(generate_bet_card, active["match_number"], coins, bet_path)
        await interaction.followup.send(
            file=discord.File(bet_path, filename="bet.png"),
            view=PredictionView(active["match_number"]), ephemeral=True)
    except Exception as e:
        embed = discord.Embed(
            title=f"🎲 Matç No{active['match_number']} — Mərc",
            description=f"Qalibə mərc et, düz tapsan **2x** qazanırsın!\n\n🪙 Balansınız: **{coins} coin**",
            color=discord.Color.gold())
        await interaction.followup.send(embed=embed, view=PredictionView(active["match_number"]), ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# /MUQAYİSƏ  /ELO_GRAFİK  /GONDER  /FƏALİYYƏT
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="muqayise", description="İki oyunçunun statistikasını müqayisə et")
@app_commands.describe(oyuncu1="Birinci oyunçu", oyuncu2="İkinci oyunçu")
async def muqayise_cmd(interaction: discord.Interaction,
                       oyuncu1: discord.Member, oyuncu2: discord.Member):
    await interaction.response.defer()

    def _pdata(p):
        if not p: return None
        kd = round(p[11]/max(p[13],1), 2) if len(p) > 13 else 0
        return {
            "nick":       p[1], "so2_id": p[2], "elo": p[3],
            "wins":       p[4], "losses": p[5],
            "kills":      p[11] if len(p)>11 else 0,
            "assists":    p[12] if len(p)>12 else 0,
            "deaths":     p[13] if len(p)>13 else 0,
            "win_streak": p[14] if len(p)>14 else 0,
            "peak_elo":   p[16] if len(p)>16 else p[3],
        }

    p1 = _pdata(get_player(oyuncu1.id))
    p2 = _pdata(get_player(oyuncu2.id))

    if not p1 or not p2:
        await interaction.followup.send("❌ Hər iki oyunçu qeydiyyatda olmalıdır.", ephemeral=True)
        return

    path = os.path.join(DATA_DIR or ".", f"compare_{oyuncu1.id}_{oyuncu2.id}.png")
    try:
        await asyncio.to_thread(generate_compare_card, p1, p2, path)
        await interaction.followup.send(file=discord.File(path, filename="compare.png"))
    except Exception as e:
        await interaction.followup.send(f"❌ Kart yaradıla bilmədi: {e}", ephemeral=True)


@bot.tree.command(name="elo_grafik", description="ELO dəyişim qrafikini göstər")
@app_commands.describe(uzv="Oyunçu (boş = özünüz)")
async def elo_grafik_cmd(interaction: discord.Interaction, uzv: discord.Member = None):
    target = uzv or interaction.user
    await interaction.response.defer(ephemeral=True)
    player = get_player(target.id)
    if not player:
        await interaction.followup.send("❌ Qeydiyyat yoxdur.", ephemeral=True); return
    history  = get_elo_history(target.id, limit=30)
    peak     = get_peak_elo(target.id)
    path     = os.path.join(DATA_DIR or ".", f"elo_graph_{target.id}.png")
    try:
        await asyncio.to_thread(generate_elo_graph, player[1], history, peak, path)
        await interaction.followup.send(file=discord.File(path, filename="elo_graph.png"),
                                        view=EloGrafikView(target.id), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Qrafik yaradıla bilmədi: {e}", ephemeral=True)


@bot.tree.command(name="gonder", description="Başqa oyunçuya coin göndər (20% komissiya)")
@app_commands.describe(uzv="Göndəriləcək oyunçu", miktar="Coin miqdarı")
async def gonder_cmd(interaction: discord.Interaction, uzv: discord.Member, miktar: int):
    if uzv.id == interaction.user.id:
        await interaction.response.send_message("❌ Özünüzə göndərə bilməzsiniz.", ephemeral=True)
        return
    if miktar < 1:
        await interaction.response.send_message("❌ Miqdar ən az 1 olmalıdır.", ephemeral=True)
        return

    commission = int(miktar * 0.20)
    receiver   = miktar - commission
    from_bal   = get_coins(interaction.user.id)

    await interaction.response.defer(ephemeral=True)
    card_path = os.path.join(DATA_DIR or ".", f"transfer_{interaction.user.id}.png")
    try:
        await asyncio.to_thread(
            generate_transfer_card,
            interaction.user.display_name, uzv.display_name,
            miktar, commission, receiver, from_bal, card_path)
        view = _GonderConfirmView(interaction.user.id, uzv.id, miktar, receiver, commission)
        await interaction.followup.send(file=discord.File(card_path, filename="transfer.png"),
                                        view=view, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(title="💸 Coin Transfer — Təsdiq", color=discord.Color.gold())
        embed.add_field(name="Göndərən",       value=interaction.user.display_name, inline=True)
        embed.add_field(name="Alan",           value=uzv.display_name,              inline=True)
        embed.add_field(name="Sizdən çıxır",   value=f"🪙 {miktar}",              inline=True)
        embed.add_field(name="Komissiya (20%)",value=f"🪙 {commission}",           inline=True)
        embed.add_field(name="Alan alır",      value=f"🪙 {receiver}",             inline=True)
        view = _GonderConfirmView(interaction.user.id, uzv.id, miktar, receiver, commission)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class _GonderConfirmView(discord.ui.View):
    def __init__(self, from_id, to_id, amount, receiver, commission):
        super().__init__(timeout=60)
        self.from_id    = from_id
        self.to_id      = to_id
        self.amount     = amount
        self.receiver   = receiver
        self.commission = commission

    @discord.ui.button(label="Gondər ✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.from_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        ok, msg, comm, recv = transfer_coins(self.from_id, self.to_id, self.amount)
        if not ok:
            await interaction.response.edit_message(content=f"❌ {msg}", embed=None, view=None)
            return
        add_coin_log(self.from_id, -self.amount,  f"Transfer -> <@{self.to_id}>", "spend", get_coins(self.from_id))
        add_coin_log(self.to_id,    recv,          f"Transfer <- <@{self.from_id}>", "earn",  get_coins(self.to_id))
        await asyncio.to_thread(backup.export_backup)
        await interaction.response.edit_message(
            content=_t(self.from_id, 'coin_transfer_ok', recv=recv, to=self.to_id, comm=comm),
            embed=None, view=None)

    @discord.ui.button(label="Legv et ❌", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Transfer ləğv edildi.", embed=None, view=None)


@bot.tree.command(name="ferealiyyet", description="[Admin] Son 7 günün fəaliyyət paneli")
@app_commands.describe(gun="Analiz dövri (gün, default 7)")
@app_commands.checks.has_permissions(administrator=True)
async def ferealiyyet_cmd(interaction: discord.Interaction, gun: int = 7):
    await interaction.response.defer(ephemeral=True)
    stats  = await asyncio.to_thread(get_activity_stats, gun)
    hourly = await asyncio.to_thread(get_hourly_activity, gun)
    path   = os.path.join(DATA_DIR or ".", "activity.png")
    try:
        await asyncio.to_thread(generate_activity_card, stats, path, hourly)
        await interaction.followup.send(file=discord.File(path, filename="activity.png"), ephemeral=True)
    except Exception as e:
        embed = discord.Embed(title=f"Son {gun} gun fealiyyeti", color=discord.Color.blurple())
        embed.add_field(name="Matc", value=str(stats["match_count"]), inline=True)
        embed.add_field(name="Oyuncu", value=str(stats["player_count"]), inline=True)
        for nick, cnt in stats.get("top_active", [])[:5]:
            embed.add_field(name=nick, value=f"{cnt} matc", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)


@ferealiyyet_cmd.error
async def ferealiyyet_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BATTLE PASS KOMANDALARı
# ═══════════════════════════════════════════════════════════════════════════════

class PassView(discord.ui.View):
    def __init__(self, discord_id: int):
        super().__init__(timeout=180)
        self.discord_id = discord_id

    @discord.ui.button(label="Bütün Levellər", style=discord.ButtonStyle.primary, emoji="📋")
    async def show_levels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌ Bu sizin pass-iniz deyil.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            pd   = get_pass_data(self.discord_id)
            path = os.path.join(DATA_DIR or ".", f"pass_levels_{self.discord_id}.png")
            await asyncio.to_thread(generate_pass_levels_card, pd, path)
            await interaction.followup.send(
                file=discord.File(path, filename="pass_levels.png"), ephemeral=True)
        except Exception as e:
            print(f"[LEVELS BTN]: {e}", flush=True)
            await interaction.followup.send(f"❌ {str(e)[:80]}", ephemeral=True)

    @discord.ui.button(label="Missiyalar", style=discord.ButtonStyle.secondary, emoji="🎯")
    async def show_missions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        missions = get_active_bp_missions(self.discord_id)
        pd       = get_pass_data(self.discord_id)
        embed    = discord.Embed(title=f"Missiyalar  |  LVL {pd['level']}/30", color=0x8C50FF)
        cats     = {"daily": "Gundelik", "weekly": "Hefte", "seasonal": "Sezon"}
        for cat, cat_label in cats.items():
            ms = [m for m in missions if m["cat"] == cat]
            if not ms: continue
            lines = [f"{'✅' if m['completed'] else '○'} {m['desc'][:28]} ({m['progress']}/{m['target']}) +{m['xp']} XP"
                     for m in ms]
            embed.add_field(name=cat_label, value="\n".join(lines), inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Mükafatı Al", style=discord.ButtonStyle.success, emoji="🎁")
    async def claim_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        unclaimed = get_unclaimed_bp_levels(self.discord_id)
        if not unclaimed:
            await interaction.followup.send(
                "✅ Bütün mövcud mükafatlar artıq tələb edilib!", ephemeral=True); return
        result = claim_bp_rewards(self.discord_id, unclaimed)
        if result["coins_earned"] > 0:
            new_bal = get_coins(self.discord_id)
            add_coin_log(self.discord_id, result["coins_earned"],
                         f"Pass mükafatı — Level {unclaimed[0]}-{unclaimed[-1]}", "earn", new_bal)
        lines = [f"✅ Level {lv}" for lv in result["claimed"]]
        if result["coins_earned"]:
            lines.append(f"\n🪙 **+{result['coins_earned']} coin** əlavə edildi!")
        for it in result["items_earned"]:
            lines.append(f"🎮 {it['label']} (Level {it['level']}, {it['track'].upper()})")
        embed = discord.Embed(
            title="🎁 Mükafatlar Tələb Edildi!",
            description="\n".join(lines[:20]),
            color=discord.Color.gold())
        await interaction.followup.send(embed=embed, ephemeral=True)
        await asyncio.to_thread(backup.export_backup)

    @discord.ui.button(label="Premium Al — 7 AZN", style=discord.ButtonStyle.primary, emoji="⭐")
    async def buy_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        ok, msg = buy_battle_pass(self.discord_id)
        color   = discord.Color.green() if ok else discord.Color.red()
        await interaction.response.send_message(
            embed=discord.Embed(description=f"{'✅' if ok else '❌'} {msg}", color=color),
            ephemeral=True)
        if ok:
            await asyncio.to_thread(backup.export_backup)


@bot.tree.command(name="pass", description="Season Pass kartını göstər")
async def pass_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        # Free pass yarat (hamı üçün avtomatik)
        from database import ensure_free_pass as _efp
        _efp(interaction.user.id)
    except Exception:
        pass

    if not has_battle_pass(interaction.user.id):
        embed = discord.Embed(
            title="CALESTIFY SEASON 1 PASS",
            description=(
                "**Pass hele alinmayib!**\n\n"
                "**Ne qazanirsiniz:**\n"
                "- Gundelik +25 coin bonus\n"
                "- 30 levelde AWM | Boom Skin\n"
                "- Ekskluziv banner + cercive\n"
                "- MVP bonusu 2x\n"
                "- Queue 30 deq erkən acilar\n\n"
                f"**Qiymet: 7 AZN**\n"
                "`/pass_al` ile alin!"
            ),
            color=0x8C50FF
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        pd       = get_pass_data(interaction.user.id)
        missions = get_active_bp_missions(interaction.user.id)
    except Exception as e:
        await interaction.followup.send(f"❌ Xeta: {e}", ephemeral=True); return

    path_gif = os.path.join(DATA_DIR or ".", f"pass_{interaction.user.id}.gif")
    path_png = os.path.join(DATA_DIR or ".", f"pass_{interaction.user.id}.png")
    try:
        await asyncio.to_thread(generate_pass_gif, pd, missions, path_gif)
        await interaction.followup.send(
            file=discord.File(path_gif, filename="pass.gif"),
            view=PassView(interaction.user.id), ephemeral=True)
    except Exception as e1:
        print(f"[PASS GIF]: {e1}", flush=True)
        try:
            await asyncio.to_thread(generate_pass_card, pd, missions, path_png)
            await interaction.followup.send(
                file=discord.File(path_png, filename="pass.png"),
                view=PassView(interaction.user.id), ephemeral=True)
        except Exception as e2:
            print(f"[PASS PNG]: {e2}", flush=True)
            embed = discord.Embed(
                title=f"Season 1 Pass — LVL {pd.get('level',0)}/30",
                description=f"XP: {pd.get('xp',0)}/500  |  {'GOLD' if pd.get('is_premium') else 'FREE'} PASS\n`/pass_missiyalar` ile missiyalari gor.",
                color=0x8C50FF
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="pass_al", description="Season Pass al (5 AZN)")
async def pass_al_cmd(interaction: discord.Interaction):
    ok, msg = buy_battle_pass(interaction.user.id)
    if ok:
        embed = discord.Embed(
            title="Season Pass alindi!",
            description=(
                "Season 1 Pass-iniz aktivdir!\n\n"
                "`/pass` - Pass kartinizi acin\n"
                "`/pass_missiyalar` - Missiyalarinizia baxin"
            ),
            color=0x57F287
        )
        await asyncio.to_thread(backup.export_backup)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)


@bot.tree.command(name="pass_missiyalar", description="Battle Pass missiyalarını göstər")
async def pass_missiyalar_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not has_battle_pass(interaction.user.id):
        await interaction.followup.send("❌ Pass-iniz yoxdur. `/pass_al` ile alin.", ephemeral=True)
        return

    missions = get_active_bp_missions(interaction.user.id)
    pd       = get_pass_data(interaction.user.id)

    embed = discord.Embed(
        title=f"Missiyalar  |  LVL {pd['level']}/{BP_MAX_LEVEL}",
        color=0x8C50FF
    )
    cats = {"daily": "Gundelik", "weekly": "Hefte", "seasonal": "Sezon"}
    for cat, cat_label in cats.items():
        ms = [m for m in missions if m["cat"] == cat]
        if not ms:
            continue
        lines = []
        for m in ms:
            icon = "✅" if m["completed"] else "○"
            pct  = int(m["progress"]/m["target"]*100) if m["target"] else 100
            lines.append(f"{icon} {m['desc'][:30]} ({m['progress']}/{m['target']}) +{m['xp']} XP")
        embed.add_field(name=f"{cat_label} Missiyalar", value="\n".join(lines) or "—", inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    if not is_dm and not is_mentioned:
        return

    text = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not text:
        return

    player = get_player(message.author.id)
    async with message.channel.typing():
        reply = await asyncio.to_thread(ask_groq, message.author.id, message.author.display_name, text, player)

    await message.reply(reply, mention_author=False)


@bot.event
async def on_ready():
    init_db()
    get_or_create_current_season()
    refresh_daily_tasks()
    fail_expired_tasks()
    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView())
    bot.add_view(RegisterView())
    if not check_giveaways.is_running():
        check_giveaways.start()
    if not push_backup_task.is_running():
        push_backup_task.start()
    if not daily_task_refresh.is_running():
        daily_task_refresh.start()
    if not season_end_check.is_running():
        season_end_check.start()
    if not weekly_stats_task.is_running():
        weekly_stats_task.start()
    if not ban_check_task.is_running():
        ban_check_task.start()
    if not anti_afk_check.is_running():
        anti_afk_check.start()
    check_and_lift_bans()
    await bot.tree.sync()


@tasks.loop(minutes=5)
async def ban_check_task():
    check_and_lift_bans()


@tasks.loop(hours=6)
async def daily_task_refresh():
    refresh_daily_tasks()
    fail_expired_tasks()


@tasks.loop(hours=12)
async def season_end_check():
    """Sezon bitibsə mükafatları paylayır, yeni sezon açır."""
    import datetime as _dt
    season = get_or_create_current_season()
    try:
        end_dt = _dt.datetime.strptime(season["end_date"], "%Y-%m-%d")
    except Exception:
        return
    if _dt.datetime.utcnow() < end_dt:
        return

    # Sezon bitti — mükafat paylaması
    log_ch = bot.get_channel(LOG_CHANNEL_ID)
    rows   = get_season_leaderboard(season["id"], limit=3)

    if rows and log_ch:
        embed = discord.Embed(
            title=f"🏆 SEZON {season['season_number']} TAMAMLANDI!",
            description="Ən çox ELO qazanan ilk 3 oyunçu mükafatlandırıldı!",
            color=discord.Color.gold()
        )
        medals = ["🥇", "🥈", "🥉"]
        rewards = [500, 300, 150]
        for i, r in enumerate(rows[:3]):
            nick, _, elo_gained = r[0], r[1], r[2]
            did = next((p["discord_id"] for p in get_all_players(200) if p["nick"] == nick), None)
            if did:
                bal = add_coins(did, rewards[i])
                add_coin_log(did, rewards[i], f"Sezon {season['season_number']} Top {i+1}", "earn", bal)
            embed.add_field(name=f"{medals[i]} {nick}", value=f"+{elo_gained} ELO  ·  +{rewards[i]}🪙", inline=False)
        await log_ch.send(embed=embed)

    close_season(season["id"])
    get_or_create_current_season()


TOP3_CHANNEL_ID = 1519835276124360785


@tasks.loop(hours=3)
async def weekly_stats_task():
    """Hər 3 saatda Top 3 ELO xatırlatması."""
    ch = bot.get_channel(TOP3_CHANNEL_ID)
    if not ch:
        return
    rows = get_leaderboard(limit=3)
    if not rows:
        return
    import datetime as _dt
    embed = discord.Embed(
        title="TOP 3 — ELO SIRALAMA",
        color=discord.Color.gold()
    )
    medals = ["1.", "2.", "3."]
    for i, r in enumerate(rows[:3]):
        nick, elo = r[0], r[2]
        kd = round(r[6]/max(r[7],1), 2) if len(r) > 7 else 0
        embed.add_field(name=f"{medals[i]} {nick}", value=f"ELO: {elo}  ·  K/D: {kd}", inline=False)
    embed.set_footer(text=f"Calestify FACEIT  ·  {(_dt.datetime.utcnow()+_dt.timedelta(hours=4)).strftime('%d.%m.%Y %H:%M')}")
    await ch.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
# ANTİ-AFK SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

_afk_warned: set = set()   # Xəbərdar edilmiş discord_id-lər (DM göndərilib)

class AfkConfirmView(discord.ui.View):
    """Sırada olduğunu təsdiq etmək üçün düymə."""
    def __init__(self, discord_id: int):
        super().__init__(timeout=120)
        self.discord_id = discord_id

    @discord.ui.button(label="Sıradayam ✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        _afk_warned.discard(self.discord_id)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="✅ Sırada olduğunuz təsdiqləndi! Matç başlayana qədər gözləyin.",
            view=self)

    @discord.ui.button(label="Sıradan çıx 🚪", style=discord.ButtonStyle.secondary)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.discord_id:
            await interaction.response.send_message("❌", ephemeral=True); return
        remove_from_queue(self.discord_id)
        _afk_warned.discard(self.discord_id)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="✅ Sıradan çıxdınız.", view=self)
        await update_queue_status_message()

    async def on_timeout(self):
        if is_in_queue(self.discord_id) and self.discord_id in _afk_warned:
            remove_from_queue(self.discord_id)
            _afk_warned.discard(self.discord_id)
            await update_queue_status_message()
            # Log kanalına bildiriş
            log_ch = bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                p = get_player(self.discord_id)
                nick = p[1] if p else str(self.discord_id)
                await log_ch.send(
                    f"⏰ **{nick}** AFK olaraq sıradan çıxarıldı (2 dəqiqə cavab vermədi).")


@tasks.loop(seconds=60)
async def anti_afk_check():
    """Hər 60 saniyədə sıradakı AFK oyunçuları yoxlayır."""
    import time
    now = int(time.time())
    AFK_WARN_AFTER  = 8 * 60   # 8 dəq sonra xəbərdar et
    queue = get_queue_list()
    for p in queue:
        did = p["discord_id"]
        joined = p.get("joined_at", now)
        idle   = now - joined
        if idle >= AFK_WARN_AFTER and did not in _afk_warned:
            _afk_warned.add(did)
            member = None
            for guild in bot.guilds:
                member = guild.get_member(did)
                if member: break
            if not member:
                continue
            try:
                await member.send(
                    f"⏰ **Calestify FACEIT** — Sırada **{idle//60} dəqiqədir** gözləyirsən!\n"
                    f"Hələ orada olduğunu təsdiqlə, əks halda 2 dəqiqə sonra sıradan çıxarılacaqsan.",
                    view=AfkConfirmView(did))
            except discord.Forbidden:
                # DM bağlıdırsa birbaşa sıradan çıxar
                remove_from_queue(did)
                _afk_warned.discard(did)
                await update_queue_status_message()


@anti_afk_check.before_loop
async def before_anti_afk():
    await bot.wait_until_ready()


@bot.tree.command(name="profile", description="Profilinizi göstərir")
async def profile(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return

    await interaction.response.defer()

    discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance, *_ = player

    avatar_bytes = None
    try:
        avatar_url = interaction.user.display_avatar.replace(size=256).url
        avatar_bytes = await asyncio.to_thread(requests.get, avatar_url, timeout=10)
        avatar_bytes = avatar_bytes.content
    except Exception:
        avatar_bytes = None

    card_path = os.path.join(DATA_DIR or ".", f"profile_{discord_id}.png")
    banner_full_path = None
    if active_banner:
        item = get_item_by_id(active_banner)
        if item:
            banner_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banners", item["file"])

    frame_full_path = None
    if active_frame:
        fitem = get_item_by_id(active_frame)
        if fitem:
            frame_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", fitem["file"])

    combat = get_combat_stats(discord_id)
    season = get_or_create_current_season()
    ss     = get_season_stat(discord_id, season["id"])

    # Gündəlik giriş bonusu
    login_coins, login_streak, is_new_login = check_daily_login(discord_id)
    if is_new_login and login_coins > 0:
        new_bal = add_coins(discord_id, login_coins)
        add_coin_log(discord_id, login_coins, f"Gundelik giris bonusu (streak {login_streak})", "earn", new_bal)

    # Milestone yoxlaması
    total_matches = player[4] + player[5]
    milestones = check_milestones(discord_id, total_matches)

    # Pass statusu
    _pd = get_pass_data(discord_id)
    _pass_status = None
    _pass_level  = 0
    if _pd:
        _pass_level  = _pd.get("level", 0)
        _pass_status = "premium" if _pd.get("is_premium") else "free"

    await asyncio.to_thread(
        generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path,
        banner_full_path, coins, frame_full_path, zm_balance,
        combat["kills"], combat["assists"], combat["deaths"],
        ss["wins"], ss["losses"], ss["kills"], ss["assists"], ss["deaths"],
        _pass_status, _pass_level
    )

    active_task = get_player_active_task(discord_id)
    boosts      = get_all_active_boosts(discord_id)
    peak_elo    = get_peak_elo(discord_id)

    # Profil kartını göndər
    boost_embed = None
    if boosts or peak_elo > elo:
        boost_embed = discord.Embed(color=discord.Color.purple())
        if peak_elo > elo:
            boost_embed.add_field(name="Pik ELO", value=f"**{peak_elo}**", inline=True)
        for b in boosts:
            tl = max(0, b["expires_at"] - int(datetime.datetime.utcnow().timestamp()))
            h, mn = tl // 3600, (tl % 3600) // 60
            bn  = "ELO Qoruma" if b["boost_type"] == "protection" else ("50% Boost" if b["boost_type"] == "boost_50" else "100% Boost")
            edt = datetime.datetime.utcfromtimestamp(b["expires_at"]) + datetime.timedelta(hours=4)
            boost_embed.add_field(name=bn, value=f"{h}s {mn}dəq  ·  {edt.strftime('%H:%M')}", inline=True)

    await interaction.followup.send(
        file=discord.File(card_path, filename="profile.png"),
        embed=boost_embed,
        view=PlayerProfileView(discord_id)
    )

    # Login bonusu + milestone bildirişi
    notifs = []
    if is_new_login and login_coins > 0:
        streak_sfx = _t(discord_id, 'daily_streak', streak=login_streak) if login_streak > 1 else ""
        notifs.append(_t(discord_id, 'daily_bonus', coins=login_coins) + streak_sfx)
    for ms in milestones:
        notifs.append(f"🎯 Milestone: {ms['matches']} matç → +{ms['coins']} coin!")
    if notifs:
        await interaction.followup.send("\n".join(notifs), ephemeral=True)

    # Aktiv tapşırıq varsa vizual kart ayrıca göndər
    if active_task:
        task_path = os.path.join(DATA_DIR or ".", f"tasks_{discord_id}.png")
        try:
            await asyncio.to_thread(generate_tasks_card, active_task, [], task_path)
            await interaction.followup.send(
                file=discord.File(task_path, filename="active_task.png"),
                ephemeral=False
            )
        except Exception:
            pass


@bot.tree.command(name="setup_rules", description="[Admin] FACEIT qaydaları mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_rules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    sections = [
        {
            "title": "Qeydiyyat qaydası",
            "body": "Oynamaq üçün əvvəlcə qeydiyyatdan keçmək lazımdır. Qeydiyyat kanalında Qeydiyyat düyməsinə basıb Standoff 2 ID və oyundakı adınızı yazın.",
            "accent": GREEN_ACCENT,
        },
        {
            "title": "Sıraya qoşulmaq",
            "body": "Matchmaking kanalında 5v5 düyməsinə basaraq sıraya qoşula bilərsiniz. Sıradan çıxmaq üçün Sıradan çıx düyməsindən istifadə edin. Eyni anda birdən çox sıraya qoşulmaq olmaz.",
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

    card_path = os.path.join(DATA_DIR or ".", "rules_card.png")
    await asyncio.to_thread(generate_rules_card, sections, card_path)

    await interaction.channel.send(file=discord.File(card_path, filename="rules_card.png"))
    await interaction.followup.send("✅ Qaydalar mesajı yaradıldı.", ephemeral=True)


@setup_rules.error
async def setup_rules_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_leaderboard", description="[Admin] Ümumi + Sezon leaderboard yaradır, 60s-də bir yenilənir")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leaderboard(interaction: discord.Interaction):
    global leaderboard_channel_id, leaderboard_message_id
    global season_lb_channel_id, season_lb_message_id

    await interaction.response.defer(ephemeral=True)

    _base  = os.path.dirname(os.path.abspath(__file__))
    _bdir  = os.path.join(_base, "banners")

    # ── Ümumi leaderboard ────────────────────────────────────────────────────
    rows = get_leaderboard(20)
    _bfiles = {}
    for _r in rows:
        _bid = _r[5] if len(_r) > 5 else None
        if _bid:
            _it = get_item_by_id(_bid)
            if _it: _bfiles[_bid] = _it["file"]
    lb_path = os.path.join(DATA_DIR or ".", LEADERBOARD_IMAGE_PATH)
    await asyncio.to_thread(generate_leaderboard_image, rows, lb_path, _bdir, _bfiles)

    lb_embed = discord.Embed(
        title="🏆 CALESTIFY FACEIT — ÜMUMİ LEADERBOARD",
        description="Bütün zamanların ELO sıralaması · Hər 60 saniyədə yenilənir",
        color=discord.Color.gold()
    )
    lb_msg = await interaction.channel.send(
        embed=lb_embed,
        file=discord.File(lb_path, filename="leaderboard.png")
    )
    leaderboard_channel_id = interaction.channel.id
    leaderboard_message_id = lb_msg.id

    # ── Sezon leaderboard ────────────────────────────────────────────────────
    season   = get_or_create_current_season()
    s_rows   = get_season_leaderboard(season["id"])
    slb_path = os.path.join(DATA_DIR or ".", SEASON_LEADERBOARD_IMAGE_PATH)
    await asyncio.to_thread(
        generate_season_leaderboard_image,
        s_rows, season["season_number"],
        season["start_date"], season["end_date"], slb_path
    )

    import datetime as _dt
    try:
        end_dt    = _dt.datetime.strptime(season["end_date"], "%Y-%m-%d")
        now_dt    = _dt.datetime.utcnow() + _dt.timedelta(hours=4)
        days_left = max(0, (end_dt - now_dt).days)
    except Exception:
        days_left = "?"

    slb_embed = discord.Embed(
        title=f"🌟 SEZON {season['season_number']} LEADERBOARD",
        description=(
            f"📅 {season['start_date']}  →  {season['end_date']}\n"
            f"⏰ Sezona **{days_left} gün** qalıb · Hər 60 saniyədə yenilənir"
        ),
        color=discord.Color.teal()
    )
    slb_embed.add_field(
        name="🎁 Sezon Sonu Mükafatları",
        value="🥇🥈🥉 Ən çox ELO qazanan Top 3 → Ekstra coin\n🗡️ Ən yüksək KD Top 3 → Ekstra coin",
        inline=False
    )
    slb_msg = await interaction.channel.send(
        embed=slb_embed,
        file=discord.File(slb_path, filename="season_lb.png")
    )
    season_lb_channel_id = interaction.channel.id
    season_lb_message_id = slb_msg.id

    if not refresh_leaderboard.is_running():
        refresh_leaderboard.start()

    await interaction.followup.send(
        "✅ Ümumi + Sezon leaderboard yaradıldı. Hər 60 saniyədə avtomatik yenilənəcək.",
        ephemeral=True
    )


@setup_leaderboard.error
async def setup_leaderboard_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_register", description="[Admin] Qeydiyyat mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_register(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    banner_path = os.path.join(DATA_DIR or ".", "register_banner.png")
    await asyncio.to_thread(generate_register_banner, LOGO_PATH, banner_path)

    view = RegisterView()
    await interaction.channel.send(file=discord.File(banner_path, filename="register_banner.png"), view=view)

    await interaction.followup.send("✅ Qeydiyyat mesajı yaradıldı.", ephemeral=True)


@setup_register.error
async def setup_register_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup", description="[Admin] Matchmaking mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    banner_path = os.path.join(DATA_DIR or ".", "matchmaking_banner.png")
    await asyncio.to_thread(generate_matchmaking_banner, QUEUE_OPEN_HOUR, QUEUE_CLOSE_HOUR, LOGO_PATH, banner_path)

    view = MatchmakingView()
    await interaction.channel.send(file=discord.File(banner_path, filename="matchmaking_banner.png"), view=view)

    global queue_status_channel_id, queue_status_message_id
    status_image_path = os.path.join(DATA_DIR or ".", QUEUE_STATUS_IMAGE_PATH)
    await asyncio.to_thread(generate_queue_status_card, [], status_image_path)
    status_message = await interaction.channel.send(file=discord.File(status_image_path, filename="queue_status.png"))
    queue_status_channel_id = interaction.channel.id
    queue_status_message_id = status_message.id

    await interaction.followup.send("✅ Matchmaking mesajı yaradıldı.", ephemeral=True)


@setup.error
async def setup_error(interaction: discord.Interaction, error):
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


@bot.tree.command(name="giveaway_bitir", description="[Admin] Mövcud bir giveaway mesajını manuel olaraq bitmiş elan edir")
@app_commands.describe(
    mukafat="Mükafatın adı (elan mesajında göstərilir)",
    qalib="Qalib seçilən üzv",
    elan_kanal="Giveaway mesajının olduğu kanal"
)
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_bitir(
    interaction: discord.Interaction,
    mukafat: str,
    qalib: discord.Member,
    elan_kanal: discord.TextChannel
):
    final_embed = discord.Embed(
        title="🎉 GIVEAWAY BİTDİ 🎉",
        description=f"**Mükafat:** {mukafat}\n\n🏆 Qalib: {qalib.mention}\n\nTəbriklər!",
        color=discord.Color.green()
    )
    final_embed.set_footer(text="Calestify Gaming Community")
    await elan_kanal.send(embed=final_embed)
    await elan_kanal.send(f"🎉 Təbriklər {qalib.mention}! Sən **{mukafat}** qazandın!")

    await interaction.response.send_message(f"✅ Giveaway manuel olaraq bitirildi. Qalib: {qalib.mention}", ephemeral=True)


@giveaway_bitir.error
async def giveaway_bitir_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="backup_indi", description="[Admin] Verilənləri dərhal JSON-a yedəkləyir və GitHub-a göndərir")
@app_commands.checks.has_permissions(administrator=True)
async def backup_indi(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await asyncio.to_thread(backup.export_backup)

    github_token = os.environ.get("GITHUB_TOKEN")
    github_repo = os.environ.get("GITHUB_REPO")
    if not github_token or not github_repo:
        await interaction.followup.send(
            "✅ Lokal JSON backup yaradıldı (/data/backup.json).\n⚠️ GITHUB_TOKEN/GITHUB_REPO təyin olunmadığı üçün GitHub-a göndərilmədi.",
            ephemeral=True
        )
        return

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    success, msg = await asyncio.to_thread(
        backup.push_backup_to_github, repo_dir, github_token, github_repo
    )
    status = "✅" if success else "❌"
    await interaction.followup.send(f"{status} {msg}", ephemeral=True)


@backup_indi.error
async def backup_indi_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


class AdminEditModal(discord.ui.Modal):
    def __init__(self, discord_id, field, current_value, title_text):
        super().__init__(title=title_text)
        self.discord_id = discord_id
        self.field = field
        self.value_input = discord.ui.TextInput(
            label="Yeni dəyər",
            default=str(current_value),
            required=True,
            max_length=50
        )
        self.reason_input = discord.ui.TextInput(
            label="Səbəb / Qeyd (opsional)",
            required=False,
            max_length=200,
            placeholder="Nə üçün dəyişdirirsiniz?"
        )
        self.add_item(self.value_input)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw_value = str(self.value_input.value).strip()

        if self.field in ("elo", "coins", "zm_balance", "wins", "losses"):
            try:
                value = int(raw_value)
            except ValueError:
                await interaction.response.send_message("❌ Bu sahə üçün rəqəm daxil edin.", ephemeral=True)
                return
            if value < 0:
                await interaction.response.send_message("❌ Mənfi dəyər ola bilməz.", ephemeral=True)
                return
        else:
            value = raw_value

        # Coin dəyişikliyini loga yaz (admin tənzimləməsi)
        old_coins = None
        if self.field == "coins":
            p = get_player(self.discord_id)
            old_coins = p[6] if p else None

        old_player = get_player(self.discord_id)
        old_val    = old_player[{"so2_nick":1,"so2_id":2,"elo":3,"wins":4,"losses":5,"coins":6,"zm_balance":9,
                                  "kills":11,"assists":12,"deaths":13}.get(self.field, 0)] if old_player else None
        reason     = str(self.reason_input.value).strip() if self.reason_input.value else None

        success = admin_set_player_field(self.discord_id, self.field, value)
        if not success:
            await interaction.response.send_message("❌ Xəta baş verdi.", ephemeral=True)
            return

        # Admin logu
        log_admin_action("edit", self.discord_id, self.field, old_val, value, reason, interaction.user.id)

        if self.field == "coins" and old_coins is not None:
            diff = value - old_coins
            if diff != 0:
                log_type = "earn" if diff > 0 else "spend"
                add_coin_log(self.discord_id, diff, "Admin tənzimləməsi", log_type, value)

        await asyncio.to_thread(backup.export_backup)

        player = get_player(self.discord_id)
        await interaction.response.send_message(
            f"✅ Yeniləndi.\n**Yeni məlumatlar:** Nick: {player[1]} | ID: {player[2]} | ELO: {player[3]} | Wins: {player[4]} | Losses: {player[5]} | Coins: {player[6]}",
            ephemeral=True
        )


class AddSkinModal(discord.ui.Modal, title="Yeni Skin Əlavə Et"):
    skin_name = discord.ui.TextInput(
        label="Skin adı",
        placeholder="Məsələn: AK-47 | Redline",
        required=True,
        max_length=80
    )
    skin_price = discord.ui.TextInput(
        label="Qiymət (coin)",
        placeholder="Məsələn: 500",
        required=True,
        max_length=10
    )
    skin_image = discord.ui.TextInput(
        label="Şəkil URL (istəyə bağlı)",
        placeholder="https://...",
        required=False,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = int(str(self.skin_price).strip())
        except ValueError:
            await interaction.response.send_message("❌ Qiymət rəqəm olmalıdır.", ephemeral=True)
            return
        if price <= 0:
            await interaction.response.send_message("❌ Qiymət 0-dan böyük olmalıdır.", ephemeral=True)
            return

        image_url = str(self.skin_image).strip() or None
        skin_id = add_skin(str(self.skin_name).strip(), price, image_url)
        await asyncio.to_thread(backup.export_backup)

        embed = discord.Embed(
            title="✅ Skin əlavə edildi",
            description=f"**{self.skin_name}**\n🪙 {price} coin\nID: {skin_id}",
            color=discord.Color.green()
        )
        if image_url:
            embed.set_thumbnail(url=image_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SkinDeleteView(discord.ui.View):
    """Bir oyunçunun skin envanterindən manuel silmə (oyunda təhvil verildikdə)."""
    def __init__(self, target_discord_id, admin_id):
        super().__init__(timeout=180)
        self.target_discord_id = target_discord_id
        self.admin_id = admin_id

        skin_inv = get_skin_inventory(target_discord_id)
        for s in skin_inv[:25]:
            label = f"Sil: {s['skin_name']}"
            if len(label) > 80:
                label = label[:77] + "..."
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.danger, custom_id=f"delskin_{s['id']}")
            button.callback = self._make_callback(s)
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu yalnız adminlər üçündür.", ephemeral=True)
            return False
        return True

    def _make_callback(self, skin_entry):
        async def callback(interaction: discord.Interaction):
            entry = get_skin_inventory_entry(skin_entry["id"])
            if not entry:
                await interaction.response.send_message("⚠️ Bu skin artıq envanterdə yoxdur.", ephemeral=True)
                return
            remove_skin_from_inventory(skin_entry["id"])
            await asyncio.to_thread(backup.export_backup)
            await interaction.response.send_message(
                f"✅ **{skin_entry['skin_name']}** oyunçunun envanterindən silindi (oyunda təhvil verildi).",
                ephemeral=True
            )

            # Log kanalına bildiriş
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📦 Skin təhvil verildi",
                    description=f"<@{self.target_discord_id}> oyunçusunun envanterindən **{skin_entry['skin_name']}** silindi.\nAdmin: {interaction.user.mention}",
                    color=discord.Color.orange()
                )
                await log_channel.send(embed=log_embed)
        return callback


class AdminPanelView(discord.ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=180)
        self.discord_id = discord_id

    @discord.ui.button(label="Nick dəyiş", style=discord.ButtonStyle.secondary, row=0)
    async def edit_nick(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "so2_nick", player[1], "Nick dəyiş"))

    @discord.ui.button(label="Standoff 2 ID dəyiş", style=discord.ButtonStyle.secondary, row=0)
    async def edit_so2_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "so2_id", player[2], "Standoff 2 ID dəyiş"))

    @discord.ui.button(label="ELO dəyiş", style=discord.ButtonStyle.primary, row=1)
    async def edit_elo(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "elo", player[3], "ELO dəyiş"))

    @discord.ui.button(label="Coin dəyiş", style=discord.ButtonStyle.primary, row=1)
    async def edit_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "coins", player[6], "Coin dəyiş"))

    @discord.ui.button(label="ZM (AZN) dəyiş", style=discord.ButtonStyle.primary, row=1)
    async def edit_zm(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "zm_balance", player[9], "ZM (AZN) dəyiş"))

    @discord.ui.button(label="Wins dəyiş", style=discord.ButtonStyle.secondary, row=2)
    async def edit_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "wins", player[4], "Wins dəyiş"))

    @discord.ui.button(label="Losses dəyiş", style=discord.ButtonStyle.secondary, row=2)
    async def edit_losses(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "losses", player[5], "Losses dəyiş"))

    @discord.ui.button(label="Kill dəyiş",   style=discord.ButtonStyle.secondary, row=2)
    async def edit_kills(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = get_player(self.discord_id)
        kills  = player[10] if len(player) > 10 else 0
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "kills", kills, "Kill dəyiş"))

    @discord.ui.button(label="Asist dəyiş", style=discord.ButtonStyle.secondary, row=2)
    async def edit_assists(self, interaction: discord.Interaction, button: discord.ui.Button):
        player   = get_player(self.discord_id)
        assists  = player[11] if len(player) > 11 else 0
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "assists", assists, "Asist dəyiş"))

    @discord.ui.button(label="Ölüm dəyiş",  style=discord.ButtonStyle.secondary, row=2)
    async def edit_deaths(self, interaction: discord.Interaction, button: discord.ui.Button):
        player  = get_player(self.discord_id)
        deaths  = player[12] if len(player) > 12 else 0
        await interaction.response.send_modal(AdminEditModal(self.discord_id, "deaths", deaths, "Ölüm dəyiş"))

    @discord.ui.button(label="⚠️ Warn ver", style=discord.ButtonStyle.danger, row=3)
    async def give_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        modal = WarnReasonModal(self.discord_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔴 Ban", style=discord.ButtonStyle.danger, row=3)
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        ban_player(self.discord_id, "Admin paneldən ban", interaction.user.id)
        remove_from_queue(self.discord_id)
        await interaction.response.send_message(f"🔴 <@{self.discord_id}> banlandı.", ephemeral=False)

    @discord.ui.button(label="✅ Unban", style=discord.ButtonStyle.success, row=3)
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        unban_player(self.discord_id)
        clear_warnings(self.discord_id)
        await interaction.response.send_message(f"✅ <@{self.discord_id}> banı açıldı.", ephemeral=False)

    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.secondary, row=3)
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        player = get_player(self.discord_id)
        if not player:
            await interaction.followup.send("❌", ephemeral=True); return
        p = player
        player_data = {
            "nick": p[1], "so2_id": p[2], "elo": p[3], "wins": p[4], "losses": p[5],
            "coins": p[6], "zm_balance": p[9] if len(p) > 9 else 0,
            "kills":      p[11] if len(p) > 11 else 0,
            "assists":    p[12] if len(p) > 12 else 0,
            "deaths":     p[13] if len(p) > 13 else 0,
            "win_streak": p[14] if len(p) > 14 else 0,
            "max_streak": p[15] if len(p) > 15 else 0,
        }
        achs = get_player_achievements(self.discord_id)
        path = os.path.join(DATA_DIR or ".", f"stats_{self.discord_id}.png")
        try:
            await asyncio.to_thread(generate_stats_card, player_data, achs, path)
            await interaction.followup.send(file=discord.File(path, filename="stats.png"), ephemeral=True)
        except Exception:
            kd = round(player_data["kills"]/max(player_data["deaths"],1),2)
            embed = discord.Embed(title=f"📊 {player_data['nick']}", color=discord.Color.blurple())
            embed.add_field(name="ELO", value=str(player_data["elo"]), inline=True)
            embed.add_field(name="K/D", value=str(kd), inline=True)
            embed.add_field(name="Streak", value=str(player_data["win_streak"]), inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔫 Skin Envanteri", style=discord.ButtonStyle.danger, row=4)
    async def manage_skins(self, interaction: discord.Interaction, button: discord.ui.Button):
        skin_inv = get_skin_inventory(self.discord_id)
        if not skin_inv:
            await interaction.response.send_message("🎒 Bu oyunçunun skin envanteri boşdur.", ephemeral=True)
            return
        lines = []
        for s in skin_inv[:25]:
            dt = datetime.datetime.utcfromtimestamp(s["acquired_at"]) + datetime.timedelta(hours=4)
            lines.append(f"🔫 **{s['skin_name']}** — 🪙 {s['price_paid']}  ·  {dt.strftime('%d.%m %H:%M')}")
        embed = discord.Embed(title="🔫 Oyunçunun Skin Envanteri", description="\n".join(lines), color=discord.Color.orange())
        embed.set_footer(text="Oyunda təhvil verdikdən sonra aşağıdakı düymə ilə silin.")
        await interaction.response.send_message(embed=embed, view=SkinDeleteView(self.discord_id, interaction.user.id), ephemeral=True)


class WarnReasonModal(discord.ui.Modal, title="Xəbərdarlıq Səbəbi"):
    reason = discord.ui.TextInput(label="Səbəb", required=True, max_length=200)

    def __init__(self, discord_id):
        super().__init__()
        self.discord_id = discord_id

    async def on_submit(self, interaction: discord.Interaction):
        count = add_warning(self.discord_id, str(self.reason), interaction.user.id)
        await interaction.response.send_message(
            f"⚠️ <@{self.discord_id}> — Xəbərdarlıq #{count}: {self.reason}",
            ephemeral=False
        )
        if count >= 3:
            ban_player(self.discord_id, "3 xəbərdarlıq", interaction.user.id)
            await interaction.followup.send(f"🔴 <@{self.discord_id}> 3 warn — avtomatik ban.", ephemeral=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SKIN MARKET İDARƏSİ
# ═══════════════════════════════════════════════════════════════════════════════

class SkinEditModal(discord.ui.Modal, title="Skin Düzəliş"):
    name_inp  = discord.ui.TextInput(label="Skin adı",    required=True,  max_length=80)
    price_inp = discord.ui.TextInput(label="Qiymət (coin)", required=True, max_length=6)
    img_inp   = discord.ui.TextInput(label="Şəkil URL (boş = dəyişmə)", required=False, max_length=300)

    def __init__(self, skin: dict):
        super().__init__(title=f"Skin Düzəliş — {skin['name'][:30]}")
        self.skin_id          = skin["id"]
        self.name_inp.default  = skin["name"]
        self.price_inp.default = str(skin["price"])
        self.img_inp.default   = skin.get("image_url") or ""

    async def on_submit(self, interaction: discord.Interaction):
        import sqlite3 as _sq
        from database import _get_conn
        try:
            price = int(self.price_inp.value)
        except ValueError:
            await interaction.response.send_message("❌ Qiymət rəqəm olmalıdır.", ephemeral=True)
            return
        conn   = _get_conn()
        cursor = conn.cursor()
        img    = self.img_inp.value.strip() or None
        if img:
            cursor.execute("UPDATE skins SET name=?, price=?, image_url=? WHERE id=?",
                           (self.name_inp.value, price, img, self.skin_id))
        else:
            cursor.execute("UPDATE skins SET name=?, price=? WHERE id=?",
                           (self.name_inp.value, price, self.skin_id))
        conn.commit(); conn.close()
        await interaction.response.send_message(
            f"✅ **{self.name_inp.value}** yeniləndi — 🪙 {price}", ephemeral=True)


class SkinManageView(discord.ui.View):
    def __init__(self, skins: list):
        super().__init__(timeout=180)
        self._skins = {str(s["id"]): s for s in skins}
        options = [discord.SelectOption(
            label=f"#{s['id']} {s['name'][:40]}",
            value=str(s["id"]),
            description=f"🪙 {s['price']}"
        ) for s in skins[:25]]
        sel = discord.ui.Select(placeholder="Düzəltmək üçün skin seçin...",
                                options=options, min_values=1, max_values=1)
        sel.callback    = self._on_select
        self.select_menu = sel
        self.add_item(sel)

    async def _on_select(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        skin = self._skins.get(self.select_menu.values[0])
        if not skin:
            await interaction.response.send_message("❌ Tapılmadı.", ephemeral=True); return
        await interaction.response.send_modal(SkinEditModal(skin))

    @discord.ui.button(label="Skin sil (deaktiv)", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def deactivate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌", ephemeral=True); return
        if not self.select_menu.values:
            await interaction.response.send_message("❌ Əvvəlcə skin seçin.", ephemeral=True); return
        skin_id = int(self.select_menu.values[0])
        skin    = self._skins.get(str(skin_id))
        remove_skin(skin_id)
        await interaction.response.send_message(
            f"🗑️ **{skin['name'] if skin else skin_id}** marketdən götürüldü (deaktiv).", ephemeral=True)


class ResetConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Bəli, sıfırla ✅", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)
            return
        # Əvvəl cavab ver ki timeout olmasın
        await interaction.response.edit_message(
            content="⏳ Sıfırlanır...", embed=None, view=None
        )
        try:
            await asyncio.to_thread(full_reset)
            await asyncio.to_thread(refresh_daily_tasks)
            await asyncio.to_thread(get_or_create_current_season)
            await asyncio.to_thread(backup.export_backup)
            await interaction.edit_original_response(
                content=(
                    "✅ **Tam sıfırlama tamamlandı.**\n"
                    "Bütün qeydiyyatlar, statistika, tarixçə, inventar silindi.\n"
                    "Hamı yenidən qeydiyyatdan keçməlidir."
                )
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Xəta: {e}")

    @discord.ui.button(label="Xeyr, ləğv et ❌", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Sıfırlama ləğv edildi.", embed=None, view=None)


@bot.tree.command(name="elan", description="[Admin] Yeniliklər + sıfırlama elanı göndər")
@app_commands.describe(kanal="Elanın göndəriləcəyi kanal (boş = bu kanal)")
@app_commands.checks.has_permissions(administrator=True)
async def elan_cmd(interaction: discord.Interaction,
                   kanal: discord.TextChannel = None):
    target = kanal or interaction.channel
    await interaction.response.defer(ephemeral=True)

    now_az = (datetime.datetime.utcnow() + datetime.timedelta(hours=4)).strftime("%d.%m.%Y %H:%M")

    # ── Əsas elan embedi ──────────────────────────────────────────────────────
    embed = discord.Embed(
        title="📢 CALESTIFY FACEIT — TAM YENİLƏMƏ",
        description=(
            "Salam **Calestify** cəmiyyəti!\n\n"
            "Bot sistemimiz köklü şəkildə yeniləndi — yeni funksiyalar, vizual kartlar, "
            "rəqabət mexanizmləri və daha çox. Aşağıda hamısını oxuyun!"
        ),
        color=0x5865F2
    )

    embed.add_field(
        name="🗺️ XƏRİTƏ VETO SİSTEMİ",
        value=(
            "Artıq random xəritə seçilmir — **kapitanlar növbə ilə ban edir!**\n"
            "7 xəritədən 6-sı ban edilir, 1-i qalır.\n"
            "Kapitan A banlar → Kapitan B banlar → növbəylə...\n"
            "_120 saniyə timeout-da qalan xəritələrdən random seçilir._"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 OYUNÇU MÜQAYİSƏSİ",
        value=(
            "`/muqayise @oyuncu1 @oyuncu2` — İki oyunçunun statistikası yan-yana:\n"
            "ELO · Pik ELO · Win% · K/D · Kill · Asist · Streak\n"
            "_Üstün olan yaşıl, aşağı olan qırmızı rənglə göstərilir._"
        ),
        inline=False
    )

    embed.add_field(
        name="📈 ELO QRAFİK + PİK ELO",
        value=(
            "`/elo_grafik` — ELO-nuzun zaman üzrə dəyişimini vizual qrafik şəklində görün.\n"
            "Hər matçdan sonra ELO avtomatik qeydə alınır.\n"
            "**Pik ELO** — Tarixi ən yüksək ELO profildə ayrıca göstərilir."
        ),
        inline=False
    )

    embed.add_field(
        name="💸 COİN TRANSFER",
        value=(
            "`/gonder @oyuncu miktar` — Başqa oyunçuya coin göndərin.\n"
            "• Göndərəndən tam məbləğ çıxır\n"
            "• Alan oyunçu **80%** alır (20% komissiya tutulur)\n"
            "_Göndərməzdən əvvəl təsdiq paneli açılır._"
        ),
        inline=False
    )

    embed.add_field(
        name="🔥 SERIYA BONUSU (WIN STREAK)",
        value=(
            "Art-arda qazandığınız matçlara görə **bonus coin + ELO** qazanırsınız:\n"
            "3 qələbə → +5 coin +1 ELO  ·  5 qələbə → +10 coin +2 ELO\n"
            "7 qələbə → +15 coin +3 ELO  ·  10 qələbə → +20 coin +5 ELO\n"
            "_Məğlubiyyətdə seriya sıfırlanır._"
        ),
        inline=False
    )

    embed.add_field(
        name="💎 RANK + NAİLİYYƏT SİSTEMİ",
        value=(
            "**Rank:** ELO-ya görə avtomatik — Gümüş → Qızıl → Almaz → Elite → Master\n"
            "**Nailiyyətlər:** 15 fərqli badge — ilk matç, kill, MVP, streak, ELO hədəfləri\n"
            "`/nailiyyetler` — Kartınızı görün · `/stats` — Tam vizual statistika"
        ),
        inline=False
    )

    embed.add_field(
        name="🎲 MATÇ MƏRCİ + GÜNLÜK TAPŞIRIQLAR",
        value=(
            "**Mərc:** `/merc` — Matç qalibi üçün coin mərc et, düz tapsan **2x** qazanırsan\n"
            "**Tapşırıqlar:** `/gunluk` — 24 saatlıq kill/asist tapşırıqları, coin mükafatı\n"
            "_Tapşırıq progressi profildə vizual kart şəklində görünür._"
        ),
        inline=False
    )

    embed.add_field(
        name="📋 FƏALİYYƏT + SEZON",
        value=(
            "`/ferealiyyet` — Son N gündə matç sayı, ən aktiv oyunçular, toplam kill\n"
            "`/sezon` — Cari sezon leaderboard (ELO qazancı + K/D)\n"
            "**Sezon sonu:** Top 3 avtomatik +500/300/150 coin mükafatı alır"
        ),
        inline=False
    )

    embed.add_field(
        name="⚠️ VACİB — SCAN + QEYDIYYAT",
        value=(
            "**Scan sistemi:** Matç sonunda skor şəkli **Claude AI** ilə oxunur.\n"
            "Qeydiyyatdakı adınız oyundakı adla **tam eyni** olmalıdır!\n"
            "Uyğun gəlməsə → **0 kill · 0 asist · 5 ölüm** avtomatik yazılır.\n"
            "`/profile` → **Nick Dəyiş** düyməsi ilə istənilən vaxt yeniləyin."
        ),
        inline=False
    )

    embed.add_field(
        name="📋 KOMANDALAR",
        value=(
            "`/register` · `/profile` · `/stats [@oyuncu]`\n"
            "`/muqayise @p1 @p2` · `/elo_grafik` · `/nailiyyetler`\n"
            "`/gunluk` · `/merc` · `/gonder @oyuncu miktar`\n"
            "`/sezon [N]` · `/ferealiyyet` · `/ping`"
        ),
        inline=False
    )

    embed.set_footer(text=f"Calestify Gaming Community  ·  {now_az}")

    await target.send(content="@everyone", embed=embed)
    await interaction.followup.send(f"✅ Elan **#{target.name}** kanalına göndərildi.", ephemeral=True)


@elan_cmd.error
async def elan_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="matc_legv", description="[Admin] Matç nəticəsini ləğv et — ELO/coin/K/A/D geri alınır")
@app_commands.describe(matc_no="Ləğv ediləcək matç nömrəsi")
@app_commands.checks.has_permissions(administrator=True)
async def matc_legv_cmd(interaction: discord.Interaction, matc_no: int):
    import json as _j
    await interaction.response.defer(ephemeral=True)

    from database import _get_conn
    conn   = _get_conn()
    cursor = conn.cursor()

    # Match history yoxla
    cursor.execute(
        "SELECT winner_ids, loser_ids, winner_elo_before, winner_elo_after, "
        "loser_elo_before, loser_elo_after FROM match_history WHERE match_number=? ORDER BY id DESC LIMIT 1",
        (matc_no,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        await interaction.followup.send(f"❌ Matç No{matc_no} tapılmadı.", ephemeral=True)
        return

    winner_ids   = _j.loads(row[0])
    loser_ids    = _j.loads(row[1])
    w_elo_before = _j.loads(row[2])
    w_elo_after  = _j.loads(row[3])
    l_elo_before = _j.loads(row[4])
    l_elo_after  = _j.loads(row[5])
    all_ids      = winner_ids + loser_ids

    # Scan nəticəsindən K/A/D al
    cursor.execute(
        "SELECT scan_data FROM scan_results WHERE match_number=? AND confirmed=1 ORDER BY id DESC LIMIT 1",
        (matc_no,)
    )
    scan_row = cursor.fetchone()
    kd_map   = {}
    if scan_row:
        try:
            raw = _j.loads(scan_row[0])
            for k, v in raw.items():
                try: kd_map[int(k)] = v
                except: pass
        except Exception:
            pass

    lines = []

    # ELO + coin + win/loss geri al
    for did, before, after in zip(winner_ids, w_elo_before, w_elo_after):
        diff = after - before
        cursor.execute("UPDATE players SET elo=elo-?, wins=MAX(0,wins-1), coins=MAX(0,coins-7) WHERE discord_id=?", (diff, did))
        lines.append(f"<@{did}>: ELO {after}→{before}, -7🪙")
    for did, before, after in zip(loser_ids, l_elo_before, l_elo_after):
        diff = after - before
        cursor.execute("UPDATE players SET elo=elo-?, losses=MAX(0,losses-1), coins=MAX(0,coins-3) WHERE discord_id=?", (diff, did))
        lines.append(f"<@{did}>: ELO {after}→{before}, -3🪙")

    # K/A/D geri al
    for did in all_ids:
        s = kd_map.get(did, {})
        k = s.get("kills", 0)
        a = s.get("assists", 0)
        d = s.get("deaths", 0)
        if k or a or d:
            cursor.execute(
                "UPDATE players SET kills=MAX(0,kills-?), assists=MAX(0,assists-?), deaths=MAX(0,deaths-?) WHERE discord_id=?",
                (k, a, d, did)
            )

    # Season stats geri al
    cursor.execute("SELECT id FROM seasons WHERE status='active' ORDER BY id DESC LIMIT 1")
    s_row = cursor.fetchone()
    if s_row:
        season_id = s_row[0]
        for did, before, after in zip(winner_ids, w_elo_before, w_elo_after):
            diff = max(0, after - before)
            s    = kd_map.get(did, {})
            cursor.execute("""UPDATE season_stats SET
                elo_gained=MAX(0,elo_gained-?), kills=MAX(0,kills-?),
                assists=MAX(0,assists-?), deaths=MAX(0,deaths-?), wins=MAX(0,wins-1)
                WHERE discord_id=? AND season_id=?""",
                (diff, s.get("kills",0), s.get("assists",0), s.get("deaths",0), did, season_id))
        for did, before, after in zip(loser_ids, l_elo_before, l_elo_after):
            s = kd_map.get(did, {})
            cursor.execute("""UPDATE season_stats SET
                kills=MAX(0,kills-?), assists=MAX(0,assists-?),
                deaths=MAX(0,deaths-?), losses=MAX(0,losses-1)
                WHERE discord_id=? AND season_id=?""",
                (s.get("kills",0), s.get("assists",0), s.get("deaths",0), did, season_id))

    # Qeydləri sil
    cursor.execute("DELETE FROM match_history WHERE match_number=?", (matc_no,))
    cursor.execute("DELETE FROM scan_results WHERE match_number=?", (matc_no,))
    conn.commit()
    conn.close()
    await asyncio.to_thread(backup.export_backup)

    embed = discord.Embed(
        title=f"✅ Matç No{matc_no} tam ləğv edildi",
        description="\n".join(lines) or "—",
        color=discord.Color.orange()
    )
    embed.set_footer(text="ELO · Coin · K/A/D · Match history — hamısı geri alındı")
    await interaction.followup.send(embed=embed, ephemeral=False)


@matc_legv_cmd.error
async def matc_legv_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="tam_sifirla", description="[Admin] Bütün oyunçuların statistikasını sıfırla")
@app_commands.checks.has_permissions(administrator=True)
async def tam_sifirla_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚠️ TAM SİFIRLAMA",
        description=(
            "Bu əməliyyat **geri alına bilməz!**\n\n"
            "**Silinəcək:**\n"
            "• Bütün ELO → 1000-ə sıfırlanır\n"
            "• Bütün qeydiyyatlar (hamı yenidən qeyd olmalı)\n"
            "• Coin, AZN, statistika, inventar, skinlər\n"
            "• Matç tarixçəsi, sezonlar, loglar, tapşırıqlar\n\n"
            "**Saxlanılır:**\n"
            "• Heç nə — tam boş başlanğıc"
        ),
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, view=ResetConfirmView(), ephemeral=True)


@tam_sifirla_cmd.error
async def tam_sifirla_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="admin_market", description="[Admin] Skin marketini idarə et")
@app_commands.checks.has_permissions(administrator=True)
async def admin_market_cmd(interaction: discord.Interaction):
    skins = get_active_skins()
    embed = discord.Embed(
        title="🔫 Skin Market İdarəsi",
        description=f"Aktivdə **{len(skins)}** skin var.\nDropdown-dan seçib düzəldin, ya da yeni skin əlavə edin.",
        color=discord.Color.blue()
    )
    for s in skins[:10]:
        embed.add_field(name=f"#{s['id']} {s['name']}", value=f"🪙 {s['price']}", inline=True)
    if len(skins) > 10:
        embed.set_footer(text=f"+ {len(skins)-10} daha... dropdown-da hamısı görünür")

    view = SkinManageView(skins)

    @discord.ui.button(label="+ Yeni Skin", style=discord.ButtonStyle.success, emoji="➕")
    async def add_new(btn_inter: discord.Interaction, button: discord.ui.Button):
        await btn_inter.response.send_modal(AddSkinModal())

    view.add_item(discord.ui.Button(label="➕ Yeni Skin", style=discord.ButtonStyle.success,
                                    custom_id="admin_add_skin_btn", row=2))

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@admin_market_cmd.error
async def admin_market_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yalnız adminlər.", ephemeral=True)


@bot.tree.command(name="endirim", description="[Admin] Market məhsuluna müddətli endirim tət et")
@app_commands.describe(item_id="Məhsul ID-si (məs: banner_gold)", faiz="Endirim faizi (5-90)", saat="Neçə saat aktiv olsun")
@app_commands.checks.has_permissions(administrator=True)
async def endirim_cmd(interaction: discord.Interaction, item_id: str, faiz: int, saat: int):
    if not (5 <= faiz <= 90):
        await interaction.response.send_message("❌ Faiz 5-90 arasında olmalıdır.", ephemeral=True)
        return
    set_discount(item_id, "market", faiz, saat)
    await interaction.response.send_message(
        f"✅ **{item_id}** üçün **{faiz}%** endirim {saat} saat aktiv edildi.", ephemeral=False)


@endirim_cmd.error
async def endirim_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌", ephemeral=True)


@bot.tree.command(name="mehsul_ver", description="[Admin] Oyunçuya market məhsulu ver (pulsuz)")
@app_commands.describe(uzv="Məhsul veriləcək üzv", item_id="Məhsul ID-si (məs: frame_gold)")
@app_commands.checks.has_permissions(administrator=True)
async def mehsul_ver_cmd(interaction: discord.Interaction, uzv: discord.Member, item_id: str):
    item = get_item_by_id(item_id)
    if not item:
        await interaction.response.send_message(f"❌ `{item_id}` tapılmadı.", ephemeral=True)
        return
    player = get_player(uzv.id)
    if not player:
        await interaction.response.send_message("❌ Oyunçu qeydiyyatda deyil.", ephemeral=True)
        return
    if owns_item(uzv.id, item_id):
        await interaction.response.send_message(f"⚠️ {uzv.display_name} artıq bu məhsula sahibdir.", ephemeral=True)
        return
    add_to_inventory(uzv.id, item_id)
    await asyncio.to_thread(backup.export_backup)
    try:
        await uzv.send(f"Admin tərəfindən sizə **{item['name']}** verildi!")
    except discord.Forbidden:
        pass
    await interaction.response.send_message(
        f"✅ **{item['name']}** {uzv.mention}-a verildi.", ephemeral=False)


@mehsul_ver_cmd.error
async def mehsul_ver_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌", ephemeral=True)


# ── /ara, /toplu_bildiris, ELO admin log ─────────────────────────────────────

@bot.tree.command(name="ara", description="Oyunçu adına görə ax")
@app_commands.describe(nick="Oyun adı (qismən yazın kifayətdir)")
async def ara_cmd(interaction: discord.Interaction, nick: str):
    await interaction.response.defer(ephemeral=True)
    from database import _get_conn as _gac
    conn = _gac(); cur = conn.cursor()
    cur.execute("SELECT discord_id, so2_nick, so2_id, elo FROM players WHERE so2_nick LIKE ? ORDER BY elo DESC LIMIT 10",
                (f"%{nick}%",))
    rows = cur.fetchall(); conn.close()
    if not rows:
        await interaction.followup.send("❌ Heç bir oyunçu tapılmadı.", ephemeral=True)
        return
    search_path = os.path.join(DATA_DIR or ".", f"search_{interaction.user.id}.png")
    try:
        await asyncio.to_thread(generate_search_results_card, nick, rows, search_path)
        await interaction.followup.send(file=discord.File(search_path, filename="search.png"), ephemeral=True)
    except Exception as e:
        embed = discord.Embed(title=f"Axtaris: '{nick}' — {len(rows)} netice", color=discord.Color.blurple())
        for did, snick, so2_id, elo in rows:
            embed.add_field(name=snick, value=f"SO2 ID: {so2_id}  ·  ELO: {elo}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="toplu_bildiris", description="[Admin] Bütün qeydiyyatlı oyunçulara DM göndər")
@app_commands.describe(mesaj="Göndəriləcək mesaj mətni")
@app_commands.checks.has_permissions(administrator=True)
async def toplu_bildiris_cmd(interaction: discord.Interaction, mesaj: str):
    await interaction.response.defer(ephemeral=True)
    players = get_all_players(limit=500)
    sent, fail = 0, 0
    for p in players:
        member = interaction.guild.get_member(p["discord_id"])
        if not member:
            continue
        try:
            await member.send(f"📢 **Calestify FACEIT bildirisi:**\n{mesaj}")
            sent += 1
        except discord.Forbidden:
            fail += 1
    await interaction.followup.send(
        f"✅ {sent} oyunçuya göndərildi · {fail} oyunçuya göndərilmədi (DM bağlı).", ephemeral=True)


@toplu_bildiris_cmd.error
async def toplu_bildiris_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌", ephemeral=True)


@bot.tree.command(name="elo_tarixce", description="[Admin] Oyunçunun admin dəyişiklik tarixçəsi")
@app_commands.describe(uzv="Oyunçu")
@app_commands.checks.has_permissions(administrator=True)
async def elo_tarixce_cmd(interaction: discord.Interaction, uzv: discord.Member):
    await interaction.response.defer(ephemeral=True)
    logs = get_admin_logs(uzv.id, limit=10)
    if not logs:
        await interaction.followup.send("❌ Bu oyunçu üçün admin loqu yoxdur.", ephemeral=True)
        return
    embed = discord.Embed(title=f"{uzv.display_name} — Admin Dəyişiklik Tarixçəsi", color=discord.Color.orange())
    for lg in logs:
        dt  = datetime.datetime.utcfromtimestamp(lg["created_at"]) + datetime.timedelta(hours=4)
        val = f"{lg['old']} → {lg['new']}"
        if lg.get("reason"):
            val += f"\nSəbəb: {lg['reason']}"
        val += f"\nAdmin: <@{lg['admin_id']}> · {dt.strftime('%d.%m.%Y %H:%M')}"
        embed.add_field(name=f"{lg['action']} — {lg['field']}", value=val, inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)


@elo_tarixce_cmd.error
async def elo_tarixce_error(i, e):
    if isinstance(e, app_commands.MissingPermissions):
        await i.response.send_message("❌", ephemeral=True)


@bot.tree.command(name="admin_panel", description="[Admin] Oyunçunun datalarını manuel idarə et")
@app_commands.describe(uzv="Datalarını dəyişmək istədiyiniz Discord üzvü")
@app_commands.checks.has_permissions(administrator=True)
async def admin_panel(interaction: discord.Interaction, uzv: discord.Member):
    player = get_player(uzv.id)
    if not player:
        await interaction.response.send_message("❌ Bu üzv qeydiyyatdan keçməyib.", ephemeral=True)
        return

    discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance, *_ = player
    matches = wins + losses
    win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0

    embed = discord.Embed(
        title=f"🛠️ Admin Panel — {uzv.display_name}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Nick", value=nick, inline=True)
    embed.add_field(name="Standoff 2 ID", value=so2_id, inline=True)
    embed.add_field(name="ELO", value=str(elo), inline=True)
    embed.add_field(name="Wins", value=str(wins), inline=True)
    embed.add_field(name="Losses", value=str(losses), inline=True)
    embed.add_field(name="Win Rate", value=f"{win_rate}%", inline=True)
    embed.add_field(name="Coins", value=str(coins), inline=True)
    embed.add_field(name="ZM (AZN)", value=str(zm_balance), inline=True)
    embed.set_footer(text=f"Discord ID: {discord_id}")

    await interaction.response.send_message(embed=embed, view=AdminPanelView(uzv.id), ephemeral=True)


@admin_panel.error
async def admin_panel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="skin_elave", description="[Admin] Standoff markete yeni skin əlavə edir")
@app_commands.checks.has_permissions(administrator=True)
async def skin_elave(interaction: discord.Interaction):
    await interaction.response.send_modal(AddSkinModal())


@skin_elave.error
async def skin_elave_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="skin_sil", description="[Admin] Standoff marketdən skini götürür (deaktiv edir)")
@app_commands.describe(skin_id="Götürüləcək skinin ID-si")
@app_commands.checks.has_permissions(administrator=True)
async def skin_sil(interaction: discord.Interaction, skin_id: int):
    skin = get_skin_by_id(skin_id)
    if not skin:
        await interaction.response.send_message("❌ Bu ID ilə skin tapılmadı.", ephemeral=True)
        return
    remove_skin(skin_id)
    await asyncio.to_thread(backup.export_backup)
    await interaction.response.send_message(f"✅ **{skin['name']}** marketdən götürüldü (artıq satışda deyil).", ephemeral=True)


@skin_sil.error
async def skin_sil_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="skin_siyahi", description="[Admin] Marketdəki bütün skinləri ID-ləri ilə göstərir")
@app_commands.checks.has_permissions(administrator=True)
async def skin_siyahi(interaction: discord.Interaction):
    skins = get_active_skins()
    await interaction.response.defer(ephemeral=True)
    catalog_path = os.path.join(DATA_DIR or ".", "skin_catalog.png")
    try:
        await asyncio.to_thread(generate_skin_catalog_card, skins, catalog_path)
        await interaction.followup.send(file=discord.File(catalog_path, filename="skins.png"), ephemeral=True)
    except Exception as e:
        if not skins:
            await interaction.followup.send("Mağazada heç bir skin yoxdur.", ephemeral=True); return
        lines = [f"ID **{s['id']}** — {s['name']} — 🪙 {s['price']}" for s in skins]
        embed = discord.Embed(title="🔫 Marketdəki Skinlər", description="\n".join(lines), color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)


@skin_siyahi.error
async def skin_siyahi_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────

web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

bot.run(TOKEN)
