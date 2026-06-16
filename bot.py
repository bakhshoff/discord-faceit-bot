import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import datetime
from dotenv import load_dotenv
from database import (
    init_db, register_player, get_player, update_elo,
    add_to_queue, remove_from_queue, queue_size, clear_queue,
    is_in_queue, pop_10_and_balance, get_leaderboard
)
from leaderboard_image import generate_leaderboard_image

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

TEAM_A_VOICE_ID = 1500827030890221678
TEAM_B_VOICE_ID = 1500827032261496913

LOGO_PATH = "logo.jpg"

# Matchmaking üçün açıq saatlar (Azərbaycan vaxtı, UTC+4)
QUEUE_OPEN_HOUR = 20   # 20:00
QUEUE_CLOSE_HOUR = 2   # 02:00

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_queue_open():
    az_time = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    hour = az_time.hour
    if QUEUE_OPEN_HOUR > QUEUE_CLOSE_HOUR:
        return hour >= QUEUE_OPEN_HOUR or hour < QUEUE_CLOSE_HOUR
    return QUEUE_OPEN_HOUR <= hour < QUEUE_CLOSE_HOUR


leaderboard_channel_id = None
leaderboard_message_id = None


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

        discord_id, nick, so2_id, elo, wins, losses = player
        added = add_to_queue(discord_id, nick, elo)
        if not added:
            await interaction.response.send_message("⚠️ Siz artıq sıradasınız.", ephemeral=True)
            return

        size = queue_size()
        await interaction.response.send_message(f"✅ {nick} sıraya qoşuldu! ({size}/10)", ephemeral=True)

        if size >= 10:
            result = pop_10_and_balance()
            if result is None:
                return
            team_a, team_b, captain_a, captain_b = result

            embed = discord.Embed(title="🎮 Matç tapıldı! 5v5", color=discord.Color.purple())
            embed.add_field(
                name="🔵 Komanda A",
                value="\n".join([f"{'👑 ' if p['discord_id']==captain_a['discord_id'] else ''}{p['nick']} (ELO: {p['elo']})" for p in team_a]),
                inline=True
            )
            embed.add_field(
                name="🔴 Komanda B",
                value="\n".join([f"{'👑 ' if p['discord_id']==captain_b['discord_id'] else ''}{p['nick']} (ELO: {p['elo']})" for p in team_b]),
                inline=True
            )
            mentions = " ".join([f"<@{p['discord_id']}>" for p in team_a + team_b])
            await interaction.channel.send(content=mentions, embed=embed)

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

    @discord.ui.button(label="Sıradan çıx", style=discord.ButtonStyle.secondary, emoji="🚪", custom_id="mm_leave")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        removed = remove_from_queue(interaction.user.id)
        if removed:
            await interaction.response.send_message("✅ Sıradan çıxdınız.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Siz sırada deyilsiniz.", ephemeral=True)

    @discord.ui.button(label="Queue-dən hamını çıxart - Admins Only", style=discord.ButtonStyle.danger, emoji="🧹", custom_id="mm_clear")
    async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu düymə yalnız adminlər üçündür.", ephemeral=True)
            return
        clear_queue()
        await interaction.response.send_message("🧹 Sıra tam təmizləndi.", ephemeral=True)


@bot.event
async def on_ready():
    init_db()
    print(f"{bot.user} giriş etdi və hazırdır!")
    bot.add_view(MatchmakingView())
    bot.add_view(RegisterView())
    await bot.tree.sync()


@bot.tree.command(name="profile", description="Profilinizi göstərir")
async def profile(interaction: discord.Interaction):
    player = get_player(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Qeydiyyatdan keçməmisiniz. `/register` istifadə edin.", ephemeral=True)
        return
    discord_id, nick, so2_id, elo, wins, losses = player
    embed = discord.Embed(title=f"📊 {nick} — Profil", color=discord.Color.blue())
    embed.add_field(name="ELO", value=elo, inline=True)
    embed.add_field(name="Qalib", value=wins, inline=True)
    embed.add_field(name="Məğlub", value=losses, inline=True)
    embed.add_field(name="Standoff 2 ID", value=so2_id, inline=False)
    await interaction.response.send_message(embed=embed)


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


@bot.tree.command(name="setup_rules", description="[Admin] FACEIT qaydaları mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Calestify FACEIT Qaydaları",
        description="Calestify FACEIT sistemi rəqabətli Standoff 2 matçları üçündür. Qeydiyyat, ELO və profil statistikaları bot tərəfindən qeyd olunur. Qaydalara əməl etməyən oyunçular cəza ala bilər.",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="✅ Qeydiyyat qaydası",
        value="Oynamaq üçün əvvəlcə qeydiyyatdan keçmək lazımdır. Qeydiyyat kanalında **Qeydiyyat** düyməsinə basıb Standoff 2 ID və oyundakı adınızı yazın.",
        inline=False
    )
    embed.add_field(
        name="🔥 Sıraya qoşulmaq",
        value="Matchmaking kanalında **5v5** düyməsinə basaraq sıraya qoşula bilərsiniz. Sıradan çıxmaq üçün **Sıradan çıx** düyməsindən istifadə edin. Eyni anda birdən çox sıraya qoşulmaq olmaz.",
        inline=False
    )
    embed.add_field(
        name="🎮 Matç tapılanda",
        value="Bot avtomatik komandaları (ELO-ya görə balanslaşdırılmış) və kapitanları elan edir, oyunçuları uyğun səs kanallarına köçürür. Oyunçular vaxtında qoşulmalıdır.",
        inline=False
    )
    embed.add_field(
        name="📊 ELO sistemi",
        value="Matç nəticəsi moderator tərəfindən `/matchresult` ilə qeyd olunur. ELO dəyişimi FACEIT-ə bənzər dinamik sistemlə hesablanır — ELO fərqi nə qədər böyükdürsə, dəyişim də ona uyğun azalır/artır. Qalib ELO qazanır, məğlub ELO itirir.",
        inline=False
    )
    embed.add_field(
        name="❌ Qadağandır",
        value="Smurf hesabla oynamaq\nBaşqasının hesabı ilə oynamaq\nNəticəni dəyişdirməyə çalışmaq\nKomanda yoldaşlarını bilərəkdən sabotaj etmək\nTəhqir, toxic davranış və mübahisə yaratmaq\nModerator qərarına qarşı spam etmək\nMatç zamanı oyundan səbəbsiz çıxmaq",
        inline=False
    )
    embed.add_field(
        name="⚠️ Cəza sistemi",
        value="Qayda pozuntusuna görə moderatorlar aşağıdakı cəzaları tətbiq edə bilər:\nELO silinməsi\nMatç nəticəsinin ləğvi\nMüvəqqəti FACEIT banı\nDaimi FACEIT banı\nServer qaydalarına görə əlavə cəza",
        inline=False
    )
    embed.add_field(
        name="🔨 Moderator qərarı",
        value="Son qərar moderatorlara aiddir. Mübahisəli hallarda oyunçuların davranışı nəzərə alınacaq.",
        inline=False
    )
    embed.add_field(
        name="📌 Vacib qeyd",
        value="Bu sistem serious və ədalətli oyun üçündür. Qaydaları bilməmək cəzadan azad etmir. Matçə qoşulan hər oyunçu bu qaydaları qəbul etmiş sayılır.",
        inline=False
    )
    embed.set_footer(text="Calestify Gaming Community • FACEIT Rules")

    file = None
    if os.path.exists(LOGO_PATH):
        file = discord.File(LOGO_PATH, filename="logo.jpg")
        embed.set_image(url="attachment://logo.jpg")

    if file:
        await interaction.channel.send(embed=embed, file=file)
    else:
        await interaction.channel.send(embed=embed)

    await interaction.response.send_message("✅ Qaydalar mesajı yaradıldı.", ephemeral=True)


@setup_rules.error
async def setup_rules_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup_leaderboard", description="[Admin] Leaderboard mesajını bu kanalda yaradır və avtomatik yeniləməyə başlayır")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leaderboard(interaction: discord.Interaction):
    global leaderboard_channel_id, leaderboard_message_id

    rows = get_leaderboard(20)
    generate_leaderboard_image(rows, LEADERBOARD_IMAGE_PATH)

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
    embed = discord.Embed(
        title="✅ FACEIT Qeydiyyat",
        description="FACEIT sistemində oynamaq üçün əvvəlcə qeydiyyatdan keçməlisən.\n\nAşağıdakı **Qeydiyyat** düyməsinə bas və məlumatlarını yaz:\n\n🆔 **Standoff 2 ID**\n🪪 **Faceit adı / oyundakı ad**\n\nQeydiyyatdan sonra `#🎮│faceit-matchmaking` kanalında 5v5 sırasına qoşula bilərsən.",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="📌 Vacib",
        value="Yazdığın ad screenshot-dakı oyun adı ilə eyni olmalıdır.",
        inline=False
    )
    embed.set_footer(text="Calestify FACEIT Matchmaking")

    file = None
    if os.path.exists(LOGO_PATH):
        file = discord.File(LOGO_PATH, filename="logo.jpg")
        embed.set_image(url="attachment://logo.jpg")

    view = RegisterView()
    if file:
        await interaction.channel.send(embed=embed, view=view, file=file)
    else:
        await interaction.channel.send(embed=embed, view=view)

    await interaction.response.send_message("✅ Qeydiyyat mesajı yaradıldı.", ephemeral=True)


@setup_register.error
async def setup_register_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


@bot.tree.command(name="setup", description="[Admin] Matchmaking mesajını bu kanalda yaradır")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 FACEIT Matchmaking",
        description="Aşağıdakı butonlardan istifadə et.\n\n🔥 **5v5** — 10 oyunçu lazımdır\n\nSay tamamlananda bot avtomatik komandaları yaradacaq, ELO-ya görə balanslaşdıracaq və matç elanını göndərəcək.",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="✅ Qeydiyyat",
        value="Qeydiyyatdan keçmək üçün `#faceit-qeydiyyat` kanalına keç.",
        inline=False
    )
    embed.add_field(
        name="🌙 İş saatı",
        value=f"Matchmaking yalnız gecə işləyir.\n🇦🇿 Azərbaycan vaxtı: **{QUEUE_OPEN_HOUR}:00 - 0{QUEUE_CLOSE_HOUR}:00**",
        inline=False
    )
    embed.add_field(
        name="📌 Qeyd",
        value="Oynamaq üçün uyğun butona bas. Sıradan çıxmaq üçün **Sıradan çıx** butonundan istifadə et.",
        inline=False
    )
    embed.set_footer(text="Calestify FACEIT Matchmaking")

    file = None
    if os.path.exists(LOGO_PATH):
        file = discord.File(LOGO_PATH, filename="logo.jpg")
        embed.set_image(url="attachment://logo.jpg")

    view = MatchmakingView()
    if file:
        await interaction.channel.send(embed=embed, view=view, file=file)
    else:
        await interaction.channel.send(embed=embed, view=view)

    await interaction.response.send_message("✅ Matchmaking mesajı yaradıldı.", ephemeral=True)


@setup.error
async def setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komandanı yalnız adminlər istifadə edə bilər.", ephemeral=True)


bot.run(TOKEN)
