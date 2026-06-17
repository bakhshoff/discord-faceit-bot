from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import io
import math

WIDTH = 800
HEIGHT = 380

BG_TOP = (18, 16, 22)
BG_BOTTOM = (10, 9, 12)
PANEL = (24, 22, 28)
BORDER = (45, 42, 50)
GOLD = (240, 180, 41)
WHITE = (244, 241, 234)
GRAY = (141, 135, 148)
GREEN = (95, 208, 122)
RED = (214, 69, 61)

FONT_CANDIDATES_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "DejaVuSans.ttf",
    "arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

# FACEIT-bənzər Level 1-10 sistemi, ELO aralıqlarına uyğunlaşdırılmış
# (başlanğıc ELO 1000 olduğu üçün miqyas FACEIT-dən fərqlidir)
LEVELS = [
    (0, 800, 1, (122, 122, 122)),       # Level 1 - boz
    (800, 900, 2, (122, 122, 122)),     # Level 2 - boz
    (900, 1000, 3, (255, 193, 87)),     # Level 3 - sarı-narıncı
    (1000, 1100, 4, (255, 193, 87)),    # Level 4
    (1100, 1200, 5, (255, 140, 60)),    # Level 5 - narıncı
    (1200, 1300, 6, (255, 140, 60)),    # Level 6
    (1300, 1450, 7, (255, 90, 90)),     # Level 7 - qırmızı
    (1450, 1600, 8, (255, 90, 90)),     # Level 8
    (1600, 1800, 9, (180, 110, 255)),   # Level 9 - bənövşəyi
    (1800, 99999, 10, (255, 215, 0)),   # Level 10 - qızılı
]


def _load_font(size, bold=False):
    candidates = FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def get_level_info(elo):
    for low, high, level, color in LEVELS:
        if low <= elo < high:
            return level, color
    return 10, LEVELS[-1][3]


def _make_circular_avatar(avatar_bytes, size):
    img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    img = ImageOps.fit(img, (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


def _vertical_gradient(width, height, top_color, bottom_color):
    base = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base


def generate_profile_card(nick, so2_id, elo, wins, losses, avatar_bytes=None, output_path="profile_card.png"):
    img = _vertical_gradient(WIDTH, HEIGHT, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Xarici çərçivə
    draw.rectangle([(0, 0), (WIDTH - 1, HEIGHT - 1)], outline=BORDER, width=2)

    title_font = _load_font(22, bold=True)
    brand_font = _load_font(14, bold=True)
    nick_font = _load_font(34, bold=True)
    id_font = _load_font(15)
    level_font = _load_font(20, bold=True)
    stat_value_font = _load_font(30, bold=True)
    stat_label_font = _load_font(13, bold=True)
    elo_font = _load_font(42, bold=True)
    elo_label_font = _load_font(14, bold=True)

    level, level_color = get_level_info(elo)
    matches = wins + losses
    win_rate = round((wins / matches) * 100, 1) if matches > 0 else 0.0

    # Üst marka zolağı
    draw.text((30, 24), "CALESTIFY", font=brand_font, fill=GOLD)
    draw.text((30, 42), "FACEIT PROFILE", font=title_font, fill=WHITE)

    # Avatar (dairəvi)
    avatar_size = 140
    avatar_x, avatar_y = 30, 90
    if avatar_bytes:
        try:
            avatar = _make_circular_avatar(avatar_bytes, avatar_size)
            img.paste(avatar, (avatar_x, avatar_y), avatar)
        except Exception:
            draw.ellipse(
                [(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)],
                fill=PANEL, outline=BORDER, width=2
            )
    else:
        draw.ellipse(
            [(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)],
            fill=PANEL, outline=BORDER, width=2
        )

    # Avatar ətrafında level rəngli halqa
    ring_pad = 6
    draw.ellipse(
        [(avatar_x - ring_pad, avatar_y - ring_pad),
         (avatar_x + avatar_size + ring_pad, avatar_y + avatar_size + ring_pad)],
        outline=level_color, width=4
    )

    # Level nişanı (avatarın aşağı sağ küncündə)
    badge_size = 44
    badge_x = avatar_x + avatar_size - badge_size + 14
    badge_y = avatar_y + avatar_size - badge_size + 14
    draw.ellipse(
        [(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)],
        fill=level_color, outline=BG_BOTTOM, width=3
    )
    level_text = str(level)
    bbox = draw.textbbox((0, 0), level_text, font=level_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (badge_x + badge_size / 2 - tw / 2, badge_y + badge_size / 2 - th / 2 - 3),
        level_text, font=level_font, fill=(20, 18, 22)
    )

    # Nick və ID
    text_x = avatar_x + avatar_size + 30
    draw.text((text_x, 105), nick, font=nick_font, fill=WHITE)
    draw.text((text_x, 150), f"Standoff 2 ID: {so2_id}", font=id_font, fill=GRAY)
    draw.text((text_x, 174), f"Level {level}", font=stat_label_font, fill=level_color)

    # ELO böyük göstərici (sağ üst)
    elo_block_x = WIDTH - 220
    draw.text((elo_block_x, 90), "ELO", font=elo_label_font, fill=GRAY)
    elo_text = str(elo)
    bbox = draw.textbbox((0, 0), elo_text, font=elo_font)
    draw.text((elo_block_x, 108), elo_text, font=elo_font, fill=GOLD)

    # Ayırıcı xətt
    draw.line([(30, 255), (WIDTH - 30, 255)], fill=BORDER, width=1)

    # Statistik bloklar (Matches, Wins, Losses, Win Rate)
    stats = [
        ("MATCHES", str(matches), WHITE),
        ("WINS", str(wins), GREEN),
        ("LOSSES", str(losses), RED),
        ("WIN RATE", f"{win_rate}%", GOLD),
    ]
    block_width = (WIDTH - 60) / 4
    for i, (label, value, color) in enumerate(stats):
        bx = 30 + i * block_width
        draw.text((bx, 280), label, font=stat_label_font, fill=GRAY)
        draw.text((bx, 300), value, font=stat_value_font, fill=color)

    # Alt footer
    draw.text((30, HEIGHT - 32), "Calestify Gaming Community", font=stat_label_font, fill=GRAY)

    img.save(output_path)
    return output_path
