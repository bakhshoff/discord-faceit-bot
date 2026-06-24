from PIL import Image, ImageDraw, ImageFont
import os

WIDTH = 900
HEADER_HEIGHT = 110
ROW_HEIGHT = 58
TEAM_HEADER_HEIGHT = 40
FOOTER_HEIGHT = 50
GAP = 24

BG_TOP = (18, 16, 22)
BG_BOTTOM = (10, 9, 12)
PANEL = (22, 20, 26)
PANEL_ALT = (27, 25, 31)
BORDER = (45, 42, 50)
GOLD = (240, 180, 41)
WHITE = (244, 241, 234)
GRAY = (141, 135, 148)
BLUE = (90, 140, 230)
RED_TEAM = (214, 69, 61)
GREEN = (95, 208, 122)

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


def generate_match_card(match_number, selected_map, team_a, team_b, captain_a_id, captain_b_id, output_path="match_card.png"):
    """
    team_a, team_b: [{"discord_id", "nick", "elo"}, ...] (5 nəfər hər biri)
    """
    rows_count = max(len(team_a), len(team_b))
    body_height = TEAM_HEADER_HEIGHT + rows_count * ROW_HEIGHT
    height = HEADER_HEIGHT + body_height + FOOTER_HEIGHT

    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    brand_font = _load_font(14, bold=True)
    title_font = _load_font(26, bold=True)
    map_font = _load_font(16, bold=True)
    team_header_font = _load_font(18, bold=True)
    player_font = _load_font(16)
    id_font = _load_font(12)
    elo_font = _load_font(14, bold=True)
    footer_font = _load_font(13)

    # Header
    draw.text((30, 20), "CALESTIFY", font=brand_font, fill=GOLD)
    draw.text((30, 38), f"MATÇ No{match_number}", font=title_font, fill=WHITE)
    draw.ellipse([(30, 80), (40, 90)], fill=GOLD)
    draw.text((48, 76), selected_map, font=map_font, fill=GRAY)

    draw.line([(0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT)], fill=BORDER, width=2)

    col_width = WIDTH / 2

    # Komanda A başlığı
    draw.rectangle([(0, HEADER_HEIGHT), (col_width, HEADER_HEIGHT + TEAM_HEADER_HEIGHT)], fill=(28, 36, 50))
    draw.ellipse([(30, HEADER_HEIGHT + 14), (44, HEADER_HEIGHT + 28)], fill=BLUE)
    draw.text((54, HEADER_HEIGHT + 9), "KOMANDA A", font=team_header_font, fill=BLUE)

    # Komanda B başlığı
    draw.rectangle([(col_width, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT + TEAM_HEADER_HEIGHT)], fill=(46, 27, 27))
    draw.ellipse([(col_width + 30, HEADER_HEIGHT + 14), (col_width + 44, HEADER_HEIGHT + 28)], fill=RED_TEAM)
    draw.text((col_width + 54, HEADER_HEIGHT + 9), "KOMANDA B", font=team_header_font, fill=RED_TEAM)

    # Orta ayırıcı xətt
    draw.line([(col_width, HEADER_HEIGHT), (col_width, height - FOOTER_HEIGHT)], fill=BORDER, width=2)

    row_start_y = HEADER_HEIGHT + TEAM_HEADER_HEIGHT

    def draw_team_rows(team, captain_id, x_offset):
        y = row_start_y
        for idx, p in enumerate(team):
            if idx % 2 == 0:
                draw.rectangle([(x_offset, y), (x_offset + col_width, y + ROW_HEIGHT)], fill=PANEL_ALT)
            is_captain = p["discord_id"] == captain_id
            name_x = x_offset + 30
            if is_captain:
                draw.regular_polygon((name_x + 6, y + ROW_HEIGHT // 2, 7), n_sides=3, rotation=0, fill=GOLD)
                name_x += 20
            draw.text((name_x, y + 8),  p["nick"][:26],              font=player_font, fill=WHITE)
            draw.text((name_x, y + 28), f"ID: {p.get('so2_id','')}",  font=id_font,    fill=GRAY)
            elo_text = f"{p['elo']}"
            bbox = draw.textbbox((0, 0), elo_text, font=elo_font)
            tw = bbox[2] - bbox[0]
            draw.text((x_offset + col_width - 30 - tw, y + 18), elo_text, font=elo_font, fill=GREEN)
            y += ROW_HEIGHT

    draw_team_rows(team_a, captain_a_id, 0)
    draw_team_rows(team_b, captain_b_id, col_width)

    footer_y = height - FOOTER_HEIGHT
    draw.line([(0, footer_y), (WIDTH, footer_y)], fill=BORDER, width=1)
    draw.regular_polygon((40, footer_y + 25, 6), n_sides=3, rotation=0, fill=GOLD)
    draw.text((55, footer_y + 18), "Kapitan  ·  Hər kapitan öz komandasının hazır düyməsini basmalıdır", font=footer_font, fill=GRAY)

    img.save(output_path)
    return output_path


def generate_result_card(match_number, winner_label, loser_label,
                         winner_team, loser_team,
                         winner_results, loser_results,
                         winner_coins, loser_coins,
                         timestamp_str, output_path="result_card.png"):
    """
    winner_results / loser_results: [{"nick", "old_elo", "new_elo"}, ...]
    winner_coins / loser_coins:     {discord_id: (earned, balance)}
    """
    rows = max(len(winner_team), len(loser_team))
    body_h = TEAM_HEADER_HEIGHT + rows * ROW_HEIGHT
    height = HEADER_HEIGHT + body_h + FOOTER_HEIGHT + 20

    img = _vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, height - 1)], outline=BORDER, width=2)

    brand_font       = _load_font(14, bold=True)
    title_font       = _load_font(26, bold=True)
    sub_font         = _load_font(15)
    team_header_font = _load_font(18, bold=True)
    player_font      = _load_font(14)
    id_font          = _load_font(11)
    elo_font         = _load_font(12, bold=True)
    footer_font      = _load_font(12)

    # ── Header ────────────────────────────────────────────────────────────────
    draw.text((30, 18), "CALESTIFY", font=brand_font, fill=GOLD)
    draw.text((30, 36), f"MATÇ No{match_number}  —  NƏTİCƏ", font=title_font, fill=WHITE)
    draw.text((30, 78), f"🏆  Qalib: {winner_label}   ·   {timestamp_str}", font=sub_font, fill=GRAY)
    draw.line([(0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT)], fill=BORDER, width=2)

    col_w = WIDTH // 2

    # ── Komanda başlıqları ────────────────────────────────────────────────────
    # Winner (green tint)
    draw.rectangle([(0, HEADER_HEIGHT), (col_w, HEADER_HEIGHT + TEAM_HEADER_HEIGHT)],
                   fill=(18, 42, 22))
    draw.text((30, HEADER_HEIGHT + 9), f"🏆  {winner_label}", font=team_header_font, fill=GREEN)

    # Loser (red tint)
    draw.rectangle([(col_w, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT + TEAM_HEADER_HEIGHT)],
                   fill=(46, 22, 22))
    draw.text((col_w + 30, HEADER_HEIGHT + 9), f"❌  {loser_label}", font=team_header_font, fill=RED_TEAM)

    draw.line([(col_w, HEADER_HEIGHT), (col_w, height - FOOTER_HEIGHT)], fill=BORDER, width=2)

    # ── Oyunçu sətirləri ──────────────────────────────────────────────────────
    def draw_rows(team, results, coins_map, x_offset, name_color, elo_color):
        y = HEADER_HEIGHT + TEAM_HEADER_HEIGHT
        for idx, (p, r) in enumerate(zip(team, results)):
            if idx % 2 == 0:
                draw.rectangle([(x_offset, y), (x_offset + col_w, y + ROW_HEIGHT)],
                                fill=PANEL_ALT)
            # Nick + SO2 ID
            draw.text((x_offset + 14, y + 6),  p["nick"][:22],                font=player_font, fill=name_color)
            draw.text((x_offset + 14, y + 24), f"ID: {p.get('so2_id', '')}",  font=id_font,     fill=GRAY)
            # ELO dəyişimi (sağ üst)
            diff = r["new_elo"] - r["old_elo"]
            sign = "+" if diff >= 0 else ""
            elo_txt = f"{r['old_elo']}→{r['new_elo']} ({sign}{diff})"
            bbox = draw.textbbox((0, 0), elo_txt, font=elo_font)
            tw = bbox[2] - bbox[0]
            draw.text((x_offset + col_w - 14 - tw, y + 6), elo_txt, font=elo_font, fill=elo_color)
            # Coin (sağ alt)
            earned = coins_map.get(p["discord_id"], (0,))[0]
            coin_txt = f"+{earned} coin"
            bbox2 = draw.textbbox((0, 0), coin_txt, font=id_font)
            tw2 = bbox2[2] - bbox2[0]
            draw.text((x_offset + col_w - 14 - tw2, y + 38), coin_txt, font=id_font, fill=GOLD)
            y += ROW_HEIGHT

    draw_rows(winner_team, winner_results, winner_coins, 0,       GREEN,    GREEN)
    draw_rows(loser_team,  loser_results,  loser_coins,  col_w,   RED_TEAM, RED_TEAM)

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_y = height - FOOTER_HEIGHT
    draw.line([(0, footer_y), (WIDTH, footer_y)], fill=BORDER, width=1)
    draw.text((30, footer_y + 18), "Calestify Gaming Community  ·  ELO & Coin yeniləndi", font=footer_font, fill=GRAY)

    img.save(output_path)
    return output_path
