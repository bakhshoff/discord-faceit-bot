from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

WIDTH         = 900
ROW_HEIGHT    = 42
HEADER_HEIGHT = 90
FOOTER_HEIGHT = 50

BG_COLOR     = (15, 15, 20)
ROW_ALT      = (22, 22, 28)
GOLD         = (255, 200, 50)
WHITE        = (255, 255, 255)
GREEN        = (120, 230, 120)
GRAY         = (150, 150, 160)
LIGHT_GRAY   = (220, 220, 220)
FOOTER_GRAY  = (110, 110, 120)
LINE_COLOR   = (60, 60, 70)

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


def _banner_row_bg(banner_path, width, row_h, dark_blend=0.62):
    """Banner şəklini sıranın ölçüsündə yükləyib qaranlıq overlay tətbiq edir."""
    try:
        banner = Image.open(banner_path).convert("RGB")
        # Sıraya uyğun crop (gen, hündürlük)
        bw, bh = banner.size
        scale = max(width / bw, row_h / bh)
        new_bw = int(bw * scale)
        new_bh = int(bh * scale)
        banner = banner.resize((new_bw, new_bh), Image.LANCZOS)
        # Mərkəzdən kəs
        left = (new_bw - width) // 2
        top  = (new_bh - row_h) // 2
        banner = banner.crop((left, top, left + width, top + row_h))
        # Qaranlıq overlay
        dark = Image.new("RGB", (width, row_h), (8, 8, 12))
        return Image.blend(banner, dark, dark_blend)
    except Exception:
        return None


def generate_leaderboard_image(rows, output_path="leaderboard.png",
                                banner_dir=None, banner_files=None):
    """
    rows: [(nick, so2_id, elo, wins, losses) veya
           (nick, so2_id, elo, wins, losses, active_banner), ...]
    banner_dir:   banners/ qovluğunun tam yolu
    banner_files: {banner_id: filename} dict-i
    """
    height = HEADER_HEIGHT + ROW_HEIGHT * max(len(rows), 1) + FOOTER_HEIGHT
    img  = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font  = _load_font(28, bold=True)
    sub_font    = _load_font(16)
    header_font = _load_font(16, bold=True)
    row_font    = _load_font(16)

    # Başlıq
    draw.text((30, 20), "CALESTIFY FACEIT LEADERBOARD", font=title_font, fill=GOLD)
    draw.text((30, 58), "Top 20 players by ELO", font=sub_font, fill=GRAY)
    draw.line([(0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT)], fill=LINE_COLOR, width=2)

    # Sütun başlıqları
    columns = ["#", "Player", "SO2 ID", "ELO", "M", "W", "L"]
    col_x   = [30, 90, 430, 600, 670, 730, 790]
    for i, col in enumerate(columns):
        draw.text((col_x[i], HEADER_HEIGHT + 12), col, font=header_font, fill=GOLD)

    y = HEADER_HEIGHT + 40

    if not rows:
        draw.text((30, y), "Hele qeydiyyatdan kecen oyuncu yoxdur.", font=row_font, fill=LIGHT_GRAY)
        y += ROW_HEIGHT
    else:
        for idx, row in enumerate(rows):
            # 5 və ya 6 elementli tuple dəstəyi
            if len(row) >= 6:
                nick, so2_id, elo, wins, losses, active_banner = row[0], row[1], row[2], row[3], row[4], row[5]
            else:
                nick, so2_id, elo, wins, losses = row[0], row[1], row[2], row[3], row[4]
                active_banner = None

            row_top = y - 6
            row_bot = y + ROW_HEIGHT - 6
            row_h   = row_bot - row_top

            # Arxa plan: banner varsa banner, yoxdursa standart rəng
            banner_drawn = False
            if active_banner and banner_dir and banner_files:
                fname = banner_files.get(active_banner)
                if fname:
                    bpath = os.path.join(banner_dir, fname)
                    row_bg = _banner_row_bg(bpath, WIDTH, row_h)
                    if row_bg is not None:
                        img.paste(row_bg, (0, row_top))
                        # İncə sol akzent zolağı (banner rəngini vurğulamaq üçün)
                        draw = ImageDraw.Draw(img)
                        draw.rectangle([(0, row_top), (4, row_bot)], fill=GOLD)
                        banner_drawn = True

            if not banner_drawn and idx % 2 == 0:
                draw.rectangle([(0, row_top), (WIDTH, row_bot)], fill=ROW_ALT)

            # Yenidən draw al (paste-dən sonra)
            draw = ImageDraw.Draw(img)

            matches = wins + losses
            # Banner olan oyunçunun adı üçün yüngül parıltı effekti
            nick_color = GOLD if active_banner else WHITE
            draw.text((col_x[0], y), f"#{idx + 1}", font=row_font, fill=GOLD)
            draw.text((col_x[1], y), str(nick)[:22],    font=row_font, fill=nick_color)
            draw.text((col_x[2], y), str(so2_id)[:15],  font=row_font, fill=(140, 170, 230))
            draw.text((col_x[3], y), str(elo),           font=row_font, fill=GREEN)
            draw.text((col_x[4], y), str(matches),       font=row_font, fill=LIGHT_GRAY)
            draw.text((col_x[5], y), str(wins),          font=row_font, fill=LIGHT_GRAY)
            draw.text((col_x[6], y), str(losses),        font=row_font, fill=LIGHT_GRAY)
            y += ROW_HEIGHT

    draw.text((30, y + 10), "Auto-updated by Calestify FACEIT Bot", font=sub_font, fill=FOOTER_GRAY)
    img.save(output_path)
    return output_path
