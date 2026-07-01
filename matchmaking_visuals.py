from PIL import Image, ImageDraw, ImageFont
import os

WIDTH = 900

BG_TOP = (18, 16, 22)
BG_BOTTOM = (10, 9, 12)
PANEL_ALT = (22, 20, 26)
BORDER = (45, 42, 50)
GOLD = (240, 180, 41)
WHITE = (244, 241, 234)
GRAY = (141, 135, 148)
GREEN = (95, 208, 122)
RED = (214, 69, 61)

FONT_CANDIDATES_REGULAR = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
    "arialbd.ttf",
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


def generate_matchmaking_banner(open_hour, close_hour, logo_path=None, output_path="matchmaking_banner.png"):
    height = 280
    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    brand_font = _load_font(14, bold=True)
    title_font = _load_font(36, bold=True)
    sub_font = _load_font(16)
    label_font = _load_font(14, bold=True)
    value_font = _load_font(16)

    draw.text((36, 28), "CALESTIFY GAMING COMMUNITY", font=brand_font, fill=GOLD)
    draw.text((36, 50), "FACEIT MATCHMAKING", font=title_font, fill=WHITE)
    draw.text((36, 98), "Standoff 2 · Competitive 5v5", font=sub_font, fill=GRAY)

    draw.line([(36, 140), (WIDTH - 36, 140)], fill=BORDER, width=1)

    info_y = 160
    draw.ellipse([(36, info_y + 4), (46, info_y + 14)], fill=GOLD)
    draw.text((58, info_y), "Format: 5v5  ·  10 oyunçu lazımdır", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 34), (46, info_y + 44)], fill=GOLD)
    draw.text((58, info_y + 30), "7/24 açıq  ·  istənilən vaxt qoşula bilərsən", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 64), (46, info_y + 74)], fill=GOLD)
    draw.text((58, info_y + 60), "ELO-ya görə avtomatik balanslaşdırma və xəritə seçimi", font=value_font, fill=WHITE)

    img.save(output_path)
    return output_path


def generate_queue_status_card(players, output_path="queue_status.png", avg_wait_min=None):
    size = len(players)
    row_height = 38
    header_height = 90
    footer_height = 40
    rows_to_show = max(size, 1)
    height = header_height + rows_to_show * row_height + footer_height

    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    title_font = _load_font(24, bold=True)
    count_font = _load_font(24, bold=True)
    sub_font = _load_font(13)
    row_font = _load_font(16)
    elo_font = _load_font(15, bold=True)

    draw.text((30, 22), "SIRA STATUSU", font=title_font, fill=WHITE)
    wait_txt = f"Real vaxtda yenilenir  |  Orta gozleme: ~{avg_wait_min} deq" if avg_wait_min else "Real vaxtda yenilenir"
    draw.text((30, 54), wait_txt, font=sub_font, fill=GRAY)

    count_text = f"{size}/10"
    count_color = GREEN if size >= 10 else GOLD
    bbox = draw.textbbox((0, 0), count_text, font=count_font)
    tw = bbox[2] - bbox[0]
    draw.text((WIDTH - 30 - tw, 28), count_text, font=count_font, fill=count_color)

    # Progress bar
    bar_x, bar_y, bar_w, bar_h = 30, 70, WIDTH - 60, 8
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=4, fill=PANEL_ALT)
    fill_w = int(bar_w * min(size / 10, 1.0))
    if fill_w > 0:
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h)], radius=4, fill=count_color)

    draw.line([(0, header_height), (WIDTH, header_height)], fill=BORDER, width=1)

    y = header_height + 10
    if size == 0:
        draw.text((30, y + 5), "Hələ heç kim sırada deyil.", font=row_font, fill=GRAY)
    else:
        for idx, p in enumerate(players):
            if idx % 2 == 0:
                draw.rectangle([(0, y - 4), (WIDTH, y + row_height - 4)], fill=PANEL_ALT)
            draw.text((30, y), f"{idx + 1}.", font=row_font, fill=GRAY)
            draw.text((70, y), p["nick"][:34], font=row_font, fill=WHITE)
            elo_text = str(p["elo"])
            bbox = draw.textbbox((0, 0), elo_text, font=elo_font)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH - 30 - tw, y + 1), elo_text, font=elo_font, fill=GREEN)
            y += row_height

    footer_y = height - footer_height
    draw.line([(0, footer_y), (WIDTH, footer_y)], fill=BORDER, width=1)
    draw.text((30, footer_y + 12), "Calestify Gaming Community", font=sub_font, fill=GRAY)

    img.save(output_path)
    return output_path
