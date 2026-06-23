import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import datetime
import random
import asyncio
import threading
from dotenv import load_dotenv
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
    exchange_coins_to_azn
)
from leaderboard_image import generate_leaderboard_image
from web_server import run_web_server
from profile_card import generate_profile_card
from visual_cards import generate_match_history_card, generate_coin_logs_card, generate_inventory_card
from match_card import generate_match_card
from matchmaking_visuals import generate_matchmaking_banner, generate_queue_status_card
from rules_card import generate_rules_card, generate_register_banner
from market_config import MARKET_ITEMS, get_item_by_id
import backup
import requests

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DATA_DIR = os.environ.get("DATA_DIR")
if DATA_DIR and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

TEAM_A_VOICE_ID = 1517460739059617883
TEAM_B_VOICE_ID = 1517460822148911124
LOG_CHANNEL_ID = 1517460644440313926

MAPS = ["Rust", "Province", "Sandstone", "Dune", "Hanami", "Prison", "Breeze"]

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
    _base = os.path.dirname(os.path.abspath(__file__))
    _bdir = os.path.join(_base, "banners")
    _bfiles = {}
    for _r in rows:
        _bid = _r[5] if len(_r) > 5 else None
        if _bid:
            _it = get_item_by_id(_bid)
            if _it: _bfiles[_bid] = _it["file"]
    await asyncio.to_thread(generate_leaderboard_image, rows, LEADERBOARD_IMAGE_PATH, _bdir, _bfiles)
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
        label="Faceit adı / oyundakı ad",
        placeholder="Oyundakı adınızı yazın",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        success = register_player(interaction.user.id, str(self.nick), str(self.so2_id))
        if success:
            await asyncio.to_thread(backup.export_backup)
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
    def __init__(self, discord_id):
        super().__init__(timeout=120)
        self.discord_id = discord_id
        for item in MARKET_ITEMS:
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
            discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance = player
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


class ExchangeConfirmView(discord.ui.View):
    def __init__(self, discord_id, times):
        super().__init__(timeout=60)
        self.discord_id = discord_id
        self.times = times

    @discord.ui.button(label="Çevir", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_coins = self.times * 250
        total_azn = round(self.times * 0.5, 2)
        success = True
        for _ in range(self.times):
            ok, _, _ = exchange_coins_to_azn(interaction.user.id)
            if not ok:
                success = False
                break
        if success:
            new_coins = get_coins(interaction.user.id)
            new_zm = get_zm_balance(interaction.user.id)
            add_coin_log(interaction.user.id, -total_coins, f"Exchange: {total_coins} coin → {total_azn} AZN", "spend", new_coins)
            await asyncio.to_thread(backup.export_backup)
            await interaction.response.edit_message(
                content=f"✅ **{total_coins} coin** → **{total_azn} AZN** çevrildi!\n"
                        f"🪙 Yeni coin: **{new_coins}** | 💵 Yeni AZN: **{new_zm:.1f}**",
                view=None
            )
        else:
            await interaction.response.edit_message(content="❌ Kifayət qədər coin yox idi, əməliyyat dayandırıldı.", view=None)

    @discord.ui.button(label="Ləğv et", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Çevirmə ləğv edildi.", view=None)


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
        lines = []
        for item in MARKET_ITEMS:
            owned = owns_item(self.discord_id, item["id"])
            status = " ✅ Sahibsiniz" if owned else f" — 🪙 {item['price']}"
            lines.append(f"**{item['name']}**{status}")

        embed = discord.Embed(
            title="🛒 Calestify Market",
            description="\n".join(lines),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Balansınız: 🪙 {coins}")
        await interaction.response.send_message(embed=embed, view=MarketItemView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="Standoff Market", style=discord.ButtonStyle.success, emoji="🔫", custom_id="profile_skinmarket", row=0)
    async def open_skin_market(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        skins = get_active_skins()
        if not skins:
            await interaction.response.send_message("🔫 Hələ mağazada skin yoxdur. Tezliklə əlavə olunacaq.", ephemeral=True)
            return

        lines = []
        for skin in skins[:25]:
            lines.append(f"**{skin['name']}** — 🪙 {skin['price']}")

        embed = discord.Embed(
            title="🔫 Standoff 2 Skin Market",
            description="\n".join(lines),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Balansınız: 🪙 {coins}  ·  Skin alınca envantara düşür, oyunda rəhbərlik təhvil verir.")
        await interaction.response.send_message(embed=embed, view=SkinBuyView(self.discord_id), ephemeral=True)

    @discord.ui.button(label="ZM Market", style=discord.ButtonStyle.danger, emoji="⚡", custom_id="profile_zmmarket", row=1)
    async def open_zm_market(self, interaction: discord.Interaction, button: discord.ui.Button):
        zm_balance = get_zm_balance(self.discord_id)
        boosts = get_all_active_boosts(self.discord_id)
        lines = [f"**{item['name']}** — {item['price_azn']} AZN" for item in ZM_MARKET_ITEMS]
        embed = discord.Embed(title="⚡ ZM Market", description="\n".join(lines), color=discord.Color.purple())
        embed.add_field(name="💼 Balansınız", value=f"{zm_balance} AZN", inline=True)
        if boosts:
            bls = []
            for b in boosts:
                tl = max(0, b["expires_at"] - int(datetime.datetime.utcnow().timestamp()))
                h, mn = tl // 3600, (tl % 3600) // 60
                bn = "🛡 ELO Qoruma" if b["boost_type"]=="protection" else ("🚀 50% Boost" if b["boost_type"]=="boost_50" else "⚡ 100% Boost")
                bls.append(f"{bn} — {h}s {mn}dəq qalıb")
            embed.add_field(name="⚡ Aktiv güclənmələr", value="\n".join(bls), inline=False)
        embed.set_footer(text="ZM almaq üçün WhatsApp düyməsinə basın.")
        await interaction.response.send_message(embed=embed, view=ZMMarketView(self.discord_id, zm_balance), ephemeral=True)

    @discord.ui.button(label="İnventar", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="profile_inventory", row=1)
    async def open_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        owned_ids = get_inventory(self.discord_id)
        skin_inv = get_skin_inventory(self.discord_id)
        active = get_active_banner(self.discord_id)
        active_f = get_active_frame(self.discord_id)
        path = os.path.join(DATA_DIR or ".", f"inventory_{self.discord_id}.png")
        await asyncio.to_thread(generate_inventory_card, owned_ids, active, active_f, skin_inv, get_item_by_id, path)
        view = InventoryActivateView(self.discord_id) if owned_ids else None
        await interaction.followup.send(file=discord.File(path, filename="inventory.png"), view=view, ephemeral=True)

    @discord.ui.button(label="Loglar", style=discord.ButtonStyle.secondary, emoji="🪙", custom_id="profile_logs", row=1)
    async def open_logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        logs = get_coin_logs(self.discord_id, limit=15)
        balance = get_coins(self.discord_id)
        path = os.path.join(DATA_DIR or ".", f"logs_{self.discord_id}.png")
        await asyncio.to_thread(generate_coin_logs_card, logs, balance, None, path)
        view = CoinLogsView(self.discord_id)
        await interaction.followup.send(file=discord.File(path, filename="logs.png"), view=view, ephemeral=True)

    @discord.ui.button(label="Matç Tarixçəsi", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="profile_history", row=2)
    async def open_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        history = get_player_match_history(self.discord_id, limit=10)
        path = os.path.join(DATA_DIR or ".", f"history_{self.discord_id}.png")
        await asyncio.to_thread(generate_match_history_card, history, path)
        await interaction.followup.send(file=discord.File(path, filename="history.png"), ephemeral=True)

    @discord.ui.button(label="Coin → AZN", style=discord.ButtonStyle.primary, emoji="💱", custom_id="profile_exchange", row=2)
    async def open_exchange(self, interaction: discord.Interaction, button: discord.ui.Button):
        coins = get_coins(self.discord_id)
        times = coins // 250
        azn_val = round(times * 0.5, 2)
        if times == 0:
            await interaction.response.send_message(
                f"❌ Çevirmək üçün ən az **250 coin** lazımdır.\nBalansınız: 🪙 **{coins}**",
                ephemeral=True
            )
            return
        embed = discord.Embed(
            title="💱 Coin → AZN Çevirici",
            color=discord.Color.gold()
        )
        embed.add_field(name="📊 Kurs", value="250 🪙 = 0.5 AZN", inline=False)
        embed.add_field(name="🪙 Coin balansınız", value=str(coins), inline=True)
        embed.add_field(name="💱 Maksimum çevirmə", value=f"{times}x (= {azn_val} AZN)", inline=True)
        embed.add_field(name="💵 Alacağınız AZN", value=f"{azn_val:.1f} AZN", inline=False)
        embed.set_footer(text=f"Həmişə maksimum miqdar çevrilir: {times * 250} coin → {azn_val} AZN")
        await interaction.response.send_message(
            embed=embed,
            view=ExchangeConfirmView(self.discord_id, times),
            ephemeral=True
        )

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
        embed = discord.Embed(
            title=f"✅ Matç No{self.match_number} — Nəticə qeyd edildi",
            description=f"🗓️ {now.strftime('%d.%m.%Y %H:%M')} (AZ vaxtı)\n🏆 Qalib: **{winner_label}**",
            color=discord.Color.gold()
        )
        embed.add_field(
            name=f"✅ {winner_label}",
            value="\n".join([f"{p['nick']} — {r['old_elo']} → **{r['new_elo']}** ({'+' if r['new_elo']-r['old_elo']>=0 else ''}{r['new_elo']-r['old_elo']}) | 🪙 +{winner_coins[p['discord_id']][0]}"
                              for p, r in zip(winner_team, results["winners"])]),
            inline=False
        )
        embed.add_field(
            name=f"❌ {loser_label}",
            value="\n".join([f"{p['nick']} — {r['old_elo']} → **{r['new_elo']}** ({'+' if r['new_elo']-r['old_elo']>=0 else ''}{r['new_elo']-r['old_elo']}) | 🪙 +{loser_coins[p['discord_id']][0]}"
                              for p, r in zip(loser_team, results["losers"])]),
            inline=False
        )

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

        discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance = player
        added = add_to_queue(discord_id, nick, elo)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()
        await interaction.response.send_message(f"✅ {nick} sıraya qoşuldu! ({size}/10)", ephemeral=True)
        await update_queue_status_message()

        if size >= 10:
            result = pop_10_and_balance()
            if result is None:
                return
            team_a, team_b, captain_a, captain_b = result
            selected_map = random.choice(MAPS)
            match_number = get_next_match_number()

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
    if not push_backup_task.is_running():
        push_backup_task.start()
    await bot.tree.sync()


@bot.tree.command(name="profile", description="Profilinizi göstərir")
async def profile(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return

    await interaction.response.defer()

    discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance = player

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

    await asyncio.to_thread(
        generate_profile_card, nick, so2_id, elo, wins, losses, avatar_bytes, card_path,
        banner_full_path, coins, frame_full_path, zm_balance
    )

    boosts = get_all_active_boosts(discord_id)
    if boosts:
        boost_embed = discord.Embed(title="⚡ Aktiv Güclənmələr", color=discord.Color.orange())
        for b in boosts:
            tl = max(0, b["expires_at"] - int(datetime.datetime.utcnow().timestamp()))
            h, mn = tl // 3600, (tl % 3600) // 60
            if b["boost_type"] == "protection":
                bn = "🛡 ELO Qoruma"
            elif b["boost_type"] == "boost_50":
                bn = "🚀 50% ELO Boost"
            else:
                bn = "⚡ 100% ELO Boost"
            edt = datetime.datetime.utcfromtimestamp(b["expires_at"]) + datetime.timedelta(hours=4)
            boost_embed.add_field(name=bn, value=f"{h} saat {mn} dəq qalıb\n⏰ {edt.strftime('%d.%m.%Y %H:%M')}", inline=True)
        await interaction.followup.send(file=discord.File(card_path, filename="profile.png"), embed=boost_embed, view=PlayerProfileView(discord_id))
    else:
        await interaction.followup.send(file=discord.File(card_path, filename="profile.png"), view=PlayerProfileView(discord_id))


@bot.tree.command(name="matchresult", description="[Admin] Matç nəticəsini qeyd edir və ELO-nu yeniləyir")
@app_commands.describe(qalib="Qalib oyunçu", məğlub="Məğlub oyunçu")
@app_commands.checks.has_permissions(administrator=True)
async def matchresult(interaction: discord.Interaction, qalib: discord.Member, məğlub: discord.Member):
    if not get_player(qalib.id) or not get_player(məğlub.id):
        await interaction.response.send_message("❌ Hər iki oyunçu əvvəlcə `/register` etməlidir.", ephemeral=True)
        return

    result = update_elo(qalib.id, məğlub.id)

    winner_earned = random.randint(5, 10)
    loser_earned = random.randint(0, 5)
    w_balance = add_coins(qalib.id, winner_earned)
    l_balance = add_coins(məğlub.id, loser_earned)
    add_coin_log(qalib.id, winner_earned, "1v1 matç qələbə", "earn", w_balance)
    add_coin_log(məğlub.id, loser_earned, "1v1 matç iştirak", "earn", l_balance)
    await asyncio.to_thread(backup.export_backup)

    await asyncio.to_thread(
        record_match_history,
        "1v1",
        [qalib.id], [məğlub.id],
        [result["winner_old_elo"]], [result["winner_new_elo"]],
        [result["loser_old_elo"]], [result["loser_new_elo"]]
    )

    embed = discord.Embed(title="🏆 Matç nəticəsi qeyd edildi", color=discord.Color.gold())
    embed.add_field(
        name=f"✅ Qalib: {qalib.display_name}",
        value=f"{result['winner_old_elo']} → **{result['winner_new_elo']}** ELO (+{result['winner_new_elo'] - result['winner_old_elo']}) | 🪙 +{winner_earned}",
        inline=False
    )
    embed.add_field(
        name=f"❌ Məğlub: {məğlub.display_name}",
        value=f"{result['loser_old_elo']} → **{result['loser_new_elo']}** ELO ({result['loser_new_elo'] - result['loser_old_elo']}) | 🪙 +{loser_earned}",
        inline=False
    )
    await interaction.response.send_message(embed=embed)


@matchresult.error
async def matchresult_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


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


@bot.tree.command(name="setup_leaderboard", description="[Admin] Leaderboard mesajını bu kanalda yaradır və avtomatik yeniləməyə başlayır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leaderboard(interaction: discord.Interaction):
    global leaderboard_channel_id, leaderboard_message_id

    rows = get_leaderboard(20)
    _base = os.path.dirname(os.path.abspath(__file__))
    _bdir = os.path.join(_base, "banners")
    _bfiles = {}
    for _r in rows:
        _bid = _r[5] if len(_r) > 5 else None
        if _bid:
            _it = get_item_by_id(_bid)
            if _it: _bfiles[_bid] = _it["file"]
    await asyncio.to_thread(generate_leaderboard_image, rows, LEADERBOARD_IMAGE_PATH, _bdir, _bfiles)

    message = await interaction.channel.send(
        content="🏆 **Calestify FACEIT Leaderboard** — hər 60 saniyədə avtomatik yenilənir.",
        file=discord.File(LEADERBOARD_IMAGE_PATH, filename="leaderboard.png")
    )

    leaderboard_channel_id = interaction.channel.id
    leaderboard_message_id = message.id

    if not refresh_leaderboard.is_running():
        refresh_leaderboard.start()

    await interaction.response.send_message("✅ Leaderboard mesajı yaradıldı, avtomatik yenilənəcək.", ephemeral=True)


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
        self.add_item(self.value_input)

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

        success = admin_set_player_field(self.discord_id, self.field, value)
        if not success:
            await interaction.response.send_message("❌ Xəta baş verdi.", ephemeral=True)
            return

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

    @discord.ui.button(label="🔫 Skin envanteri / Sil", style=discord.ButtonStyle.danger, row=3)
    async def manage_skins(self, interaction: discord.Interaction, button: discord.ui.Button):
        skin_inv = get_skin_inventory(self.discord_id)
        if not skin_inv:
            await interaction.response.send_message("🎒 Bu oyunçunun skin envanteri boşdur.", ephemeral=True)
            return
        lines = []
        for s in skin_inv[:25]:
            dt = datetime.datetime.utcfromtimestamp(s["acquired_at"]) + datetime.timedelta(hours=4)
            lines.append(f"🔫 **{s['skin_name']}** — 🪙 {s['price_paid']}  ·  {dt.strftime('%d.%m %H:%M')}")
        embed = discord.Embed(
            title="🔫 Oyunçunun Skin Envanteri",
            description="\n".join(lines),
            color=discord.Color.orange()
        )
        embed.set_footer(text="Oyunda təhvil verdikdən sonra aşağıdakı düymə ilə silin.")
        await interaction.response.send_message(embed=embed, view=SkinDeleteView(self.discord_id, interaction.user.id), ephemeral=True)


@bot.tree.command(name="admin_panel", description="[Admin] Oyunçunun datalarını manuel idarə et")
@app_commands.describe(uzv="Datalarını dəyişmək istədiyiniz Discord üzvü")
@app_commands.checks.has_permissions(administrator=True)
async def admin_panel(interaction: discord.Interaction, uzv: discord.Member):
    player = get_player(uzv.id)
    if not player:
        await interaction.response.send_message("❌ Bu üzv qeydiyyatdan keçməyib.", ephemeral=True)
        return

    discord_id, nick, so2_id, elo, wins, losses, coins, active_banner, active_frame, zm_balance = player
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
    if not skins:
        await interaction.response.send_message("Mağazada heç bir skin yoxdur.", ephemeral=True)
        return
    lines = [f"ID **{s['id']}** — {s['name']} — 🪙 {s['price']}" for s in skins]
    embed = discord.Embed(title="🔫 Marketdəki Skinlər", description="\n".join(lines), color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@skin_siyahi.error
async def skin_siyahi_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

bot.run(TOKEN)
