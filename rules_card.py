from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

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

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

FONT_CANDIDATES_REGULAR = [
    os.path.join(FONT_DIR, "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"),
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


def _wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            lines.append("")
            continue
        words = paragraph.split(" ")
        current_line = ""
        for word in words:
            test_line = (current_line + " " + word).strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines


def generate_rules_card(sections, output_path="rules_card.png"):
    """
    sections: [{"title": "...", "body": "...", "accent": (r,g,b)}, ...]
    """
    title_font = _load_font(30, bold=True)
    brand_font = _load_font(14, bold=True)
    sub_font = _load_font(15)
    section_title_font = _load_font(18, bold=True)
    body_font = _load_font(15)

    pad_x = 36
    content_w = WIDTH - pad_x * 2

    # Hündürlüyü əvvəlcədən hesablamaq üçün dummy draw
    dummy_img = Image.new("RGB", (WIDTH, 10))
    dummy_draw = ImageDraw.Draw(dummy_img)

    header_height = 150
    section_gap = 18
    line_height = 24
    section_pad_top = 14
    section_pad_bottom = 18
    section_title_h = 30

    total_h = header_height
    section_heights = []
    for sec in sections:
        lines = _wrap_text(dummy_draw, sec["body"], body_font, content_w - 40)
        sec_h = section_title_h + section_pad_top + len(lines) * line_height + section_pad_bottom
        section_heights.append((sec_h, lines))
        total_h += sec_h + section_gap

    footer_h = 50
    total_h += footer_h

    img = _vertical_gradient(WIDTH, total_h, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, total_h - 1)], outline=BORDER, width=2)

    draw.text((pad_x, 28), "CALESTIFY GAMING COMMUNITY", font=brand_font, fill=GOLD)
    draw.text((pad_x, 50), "FACEIT QAYDALARI", font=title_font, fill=WHITE)
    draw.text((pad_x, 92), "Standoff 2 Competitive — bütün oyunçular bu qaydalara əməl etməlidir", font=sub_font, fill=GRAY)
    draw.line([(pad_x, header_height - 10), (WIDTH - pad_x, header_height - 10)], fill=BORDER, width=1)

    y = header_height
    for sec, (sec_h, lines) in zip(sections, section_heights):
        accent = sec.get("accent", GOLD)
        draw.rounded_rectangle(
            [(pad_x, y), (WIDTH - pad_x, y + sec_h)],
            radius=10, fill=PANEL_ALT
        )
        draw.rounded_rectangle(
            [(pad_x, y), (pad_x + 5, y + sec_h)],
            radius=2, fill=accent
        )
        draw.text((pad_x + 24, y + section_pad_top), sec["title"], font=section_title_font, fill=accent)

        text_y = y + section_pad_top + section_title_h
        for line in lines:
            draw.text((pad_x + 24, text_y), line, font=body_font, fill=WHITE)
            text_y += line_height

        y += sec_h + section_gap

    footer_y = total_h - footer_h
    draw.line([(pad_x, footer_y), (WIDTH - pad_x, footer_y)], fill=BORDER, width=1)
    draw.text((pad_x, footer_y + 16), "Calestify Gaming Community  ·  FACEIT Rules", font=sub_font, fill=GRAY)

    img.save(output_path)
    return output_path


def generate_register_banner(logo_path=None, output_path="register_banner.png"):
    height = 260
    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    brand_font = _load_font(14, bold=True)
    title_font = _load_font(34, bold=True)
    sub_font = _load_font(16)
    value_font = _load_font(16)

    draw.text((36, 28), "CALESTIFY GAMING COMMUNITY", font=brand_font, fill=GOLD)
    draw.text((36, 50), "FACEIT QEYDİYYAT", font=title_font, fill=WHITE)
    draw.text((36, 96), "Standoff 2 Competitive sisteminə qoşulmaq üçün qeydiyyatdan keç", font=sub_font, fill=GRAY)

    draw.line([(36, 132), (WIDTH - 36, 132)], fill=BORDER, width=1)

    info_y = 152
    draw.ellipse([(36, info_y + 4), (46, info_y + 14)], fill=GOLD)
    draw.text((58, info_y), "Aşağıdaki Qeydiyyat düyməsinə bas", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 34), (46, info_y + 44)], fill=GOLD)
    draw.text((58, info_y + 30), "Standoff 2 ID və oyundakı adını daxil et", font=value_font, fill=WHITE)

    draw.ellipse([(36, info_y + 64), (46, info_y + 74)], fill=GOLD)
    draw.text((58, info_y + 60), "Başlanğıc ELO: 1000  ·  Level 1-10 sistemi", font=value_font, fill=WHITE)

    img.save(output_path)
    return output_path
