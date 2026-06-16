from PIL import Image, ImageDraw, ImageFont
import os

WIDTH = 900
ROW_HEIGHT = 42
HEADER_HEIGHT = 90
FOOTER_HEIGHT = 50

BG_COLOR = (15, 15, 20)
ROW_ALT_COLOR = (22, 22, 28)
GOLD = (255, 200, 50)
WHITE = (255, 255, 255)
GREEN = (120, 230, 120)
GRAY = (150, 150, 160)
LIGHT_GRAY = (220, 220, 220)
FOOTER_GRAY = (110, 110, 120)
LINE_COLOR = (60, 60, 70)

# DejaVu Sans Azərbaycan hərflərini (ə, ç, ş, ğ, ı) düzgün göstərir,
# Arial isə bunları dəstəkləməyə bilər — ona görə DejaVu prioritetlidir
FONT_CANDIDATES_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "DejaVuSans.ttf",
    "arial.ttf",
    "Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
    "Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _load_font(size, bold=False):
    candidates = FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generate_leaderboard_image(rows, output_path="leaderboard.png"):
    """
    rows: [(nick, elo, wins, losses), ...] ELO-ya görə sıralanmış
    """
    height = HEADER_HEIGHT + ROW_HEIGHT * max(len(rows), 1) + FOOTER_HEIGHT
    img = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font = _load_font(28, bold=True)
    sub_font = _load_font(16)
    header_font = _load_font(16, bold=True)
    row_font = _load_font(16)

    draw.text((30, 20), "CALESTIFY FACEIT LEADERBOARD", font=title_font, fill=GOLD)
    draw.text((30, 58), "Top 20 players by ELO", font=sub_font, fill=GRAY)
    draw.line([(0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT)], fill=LINE_COLOR, width=2)

    columns = ["#", "Player", "ELO", "M", "W", "L"]
    col_x = [30, 90, 480, 580, 660, 740]
    for i, col in enumerate(columns):
        draw.text((col_x[i], HEADER_HEIGHT + 12), col, font=header_font, fill=GOLD)

    y = HEADER_HEIGHT + 40
    if not rows:
        draw.text((30, y), "Hələ qeydiyyatdan keçən oyunçu yoxdur.", font=row_font, fill=LIGHT_GRAY)
        y += ROW_HEIGHT
    else:
        for idx, (nick, elo, wins, losses) in enumerate(rows):
            if idx % 2 == 0:
                draw.rectangle([(0, y - 6), (WIDTH, y + ROW_HEIGHT - 6)], fill=ROW_ALT_COLOR)
            matches = wins + losses
            draw.text((col_x[0], y), f"#{idx + 1}", font=row_font, fill=GOLD)
            draw.text((col_x[1], y), str(nick)[:28], font=row_font, fill=WHITE)
            draw.text((col_x[2], y), str(elo), font=row_font, fill=GREEN)
            draw.text((col_x[3], y), str(matches), font=row_font, fill=LIGHT_GRAY)
            draw.text((col_x[4], y), str(wins), font=row_font, fill=LIGHT_GRAY)
            draw.text((col_x[5], y), str(losses), font=row_font, fill=LIGHT_GRAY)
            y += ROW_HEIGHT

    draw.text((30, y + 10), "Auto-updated by Calestify FACEIT Bot", font=sub_font, fill=FOOTER_GRAY)

    img.save(output_path)
    return output_path
