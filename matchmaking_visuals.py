from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os


def _finalize(img):
    """Whole-image polish pass: 2x upscale+downscale smooths jagged shape edges, then a mild
    sharpen recovers text crispness."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(img).enhance(1.15)


WIDTH = 900

BG_TOP = (16, 13, 24)
BG_BOTTOM = (8, 7, 12)
PANEL_ALT = (20, 17, 28)
BORDER = (52, 44, 70)
GOLD = (138, 92, 230)
SILVER = (186, 178, 202)
WHITE = (244, 241, 234)
GRAY = (150, 142, 168)
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

    draw.text((36, 28), "Zenith's Academy", font=brand_font, fill=GOLD)
    draw.text((36, 50), "FACEIT MATCHMAKING", font=title_font, fill=WHITE)
    draw.text((36, 98), "Standoff 2 · Competitive 2v2", font=sub_font, fill=GRAY)

    draw.line([(36, 140), (WIDTH - 36, 140)], fill=BORDER, width=1)

    info_y = 160
    draw.ellipse([(36, info_y + 4), (46, info_y + 14)], fill=GOLD)
    draw.text((58, info_y), "Format: 2v2  ·  4 oyunçu lazımdır", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 34), (46, info_y + 44)], fill=GOLD)
    draw.text((58, info_y + 30), "7/24 açıq  ·  istənilən vaxt qoşula bilərsən", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 64), (46, info_y + 74)], fill=GOLD)
    draw.text((58, info_y + 60), "ELO-ya görə avtomatik balanslaşdırma və xəritə seçimi", font=value_font, fill=WHITE)

    _finalize(img).save(output_path)
    return output_path


def generate_queue_status_card(players, output_path="queue_status.png", avg_wait_min=None):
    """Sıradakı oyunçu sayını/proqres barını göstərir, amma kimlərin sırada olduğunu QƏSDƏN
    açmır (oyunçular güclü/zəif rəqibə görə sıraya girib-girməmək kimi davranışlar sərgiləməsin)."""
    size = len(players)
    header_height = 90
    body_height = 54
    footer_height = 40
    height = header_height + body_height + footer_height

    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    title_font = _load_font(24, bold=True)
    count_font = _load_font(24, bold=True)
    sub_font = _load_font(13)
    body_font = _load_font(15)

    draw.text((30, 22), "SIRA STATUSU", font=title_font, fill=WHITE)
    wait_txt = f"Real vaxtda yenilenir  |  Orta gozleme: ~{avg_wait_min} deq" if avg_wait_min else "Real vaxtda yenilenir"
    draw.text((30, 54), wait_txt, font=sub_font, fill=GRAY)

    count_text = f"{size}/4"
    count_color = GREEN if size >= 4 else GOLD
    bbox = draw.textbbox((0, 0), count_text, font=count_font)
    tw = bbox[2] - bbox[0]
    draw.text((WIDTH - 30 - tw, 28), count_text, font=count_font, fill=count_color)

    # Progress bar
    bar_x, bar_y, bar_w, bar_h = 30, 70, WIDTH - 60, 8
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=4, fill=PANEL_ALT)
    fill_w = int(bar_w * min(size / 4, 1.0))
    if fill_w > 0:
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h)], radius=4, fill=count_color)

    draw.line([(0, header_height), (WIDTH, header_height)], fill=BORDER, width=1)

    body_text = ("Hələ heç kim sırada deyil." if size == 0
                 else f"{size} nəfər sıradadır — kimliklər məxfi saxlanılır.")
    draw.text((WIDTH // 2, header_height + body_height // 2), body_text,
              font=body_font, fill=GRAY, anchor="mm")

    footer_y = height - footer_height
    draw.line([(0, footer_y), (WIDTH, footer_y)], fill=BORDER, width=1)
    draw.text((30, footer_y + 12), "Zenith's Academy", font=sub_font, fill=GRAY)

    _finalize(img).save(output_path)
    return output_path
