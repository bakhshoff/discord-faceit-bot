from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os


def _finalize(img):
    """Whole-image polish pass: 2x upscale+downscale smooths jagged shape edges, then a mild
    sharpen recovers text crispness."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(img).enhance(1.15)


BG_TOP = (16, 13, 24)
BG_BOTTOM = (8, 7, 12)
PANEL = (22, 18, 30)
PANEL_ALT = (28, 23, 38)
BORDER = (52, 44, 70)
GOLD = (138, 92, 230)
WHITE = (244, 241, 234)
GRAY = (150, 142, 168)

FONT_CANDIDATES_REGULAR = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
]
FONT_CANDIDATES_BOLD = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
]


def _font(size, bold=False):
    for p in (FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _vertical_gradient(width, height, top, bottom):
    img = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        draw.line([(0, y), (width, y)],
                  fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


BOX_W = 240
BOX_H = 64
ROW_H = 30       # bir komandanın sətir hündürlüyü (qutu daxilində 2 sətir var)
COL_GAP = 70
ROUND1_GAP = 26  # round-1 qutuları arası şaquli boşluq
MARGIN = 40
HEADER_H = 70


def _team_label(team):
    if team is None:
        return "?"
    if team.get("is_bye"):
        return "BYE"
    return team.get("label") or "?"


def generate_tournament_bracket_image(bracket_data, output_path):
    """`bracket_data`: database.get_tournament_bracket(...) nəticəsi
    ({"tournament": {...}, "rounds": [[match,...], ...]}). Hündürlük/en round/matç sayına
    görə DİNAMİK hesablanır (mövcud kartlarla eyni prinsip)."""
    tournament = bracket_data["tournament"]
    rounds = bracket_data["rounds"]
    num_rounds = len(rounds)

    # Round 1-in y-mərkəzlərini əvvəlcə hesablayırıq, sonrakı raundlar bunların
    # ortalamasından (standart bracket rekursiyası) çıxır.
    round1_count = len(rounds[0]) if rounds else 1
    centers = [HEADER_H + MARGIN + i * (BOX_H + ROUND1_GAP) + BOX_H / 2 for i in range(round1_count)]
    all_centers = [centers]
    for r in range(1, num_rounds):
        prev = all_centers[-1]
        this_centers = [(prev[2 * i] + prev[2 * i + 1]) / 2 for i in range(len(prev) // 2)]
        all_centers.append(this_centers)

    width = MARGIN * 2 + num_rounds * BOX_W + (num_rounds - 1) * COL_GAP
    height = HEADER_H + MARGIN * 2 + round1_count * (BOX_H + ROUND1_GAP)

    img = _vertical_gradient(width, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=GOLD, width=2)
    draw.rectangle([(0, 0), (width - 1, 5)], fill=GOLD)

    title_font = _font(22, True)
    name_font = _font(13, True)
    status_font = _font(11)
    draw.polygon([(MARGIN, 30), (MARGIN + 14, 30), (MARGIN + 11, 42), (MARGIN + 3, 42)], fill=GOLD)
    draw.text((MARGIN + 24, 20), tournament['name'], font=title_font, fill=WHITE)
    status_label = {"signup": "Qeydiyyat", "active": "Davam edir", "completed": "Tamamlandı",
                     "cancelled": "Ləğv edildi"}.get(tournament["status"], tournament["status"])
    draw.text((width - MARGIN, 26), status_label, font=status_font, fill=GRAY, anchor="ra")

    for r, matches in enumerate(rounds):
        x0 = MARGIN + r * (BOX_W + COL_GAP)
        for i, m in enumerate(matches):
            cy = all_centers[r][i]
            y0 = cy - BOX_H / 2
            winner_id = m["winner_team_id"]
            a_label, b_label = _team_label(m["team_a"]), _team_label(m["team_b"])
            a_col = GOLD if (winner_id and winner_id == m["team_a_id"]) else WHITE
            b_col = GOLD if (winner_id and winner_id == m["team_b_id"]) else WHITE
            box_fill = PANEL_ALT if m["status"] == "completed" else PANEL
            draw.rounded_rectangle([(x0, y0), (x0 + BOX_W, y0 + BOX_H)], radius=6,
                                   fill=box_fill, outline=BORDER, width=1)
            draw.line([(x0, y0 + BOX_H / 2), (x0 + BOX_W, y0 + BOX_H / 2)], fill=BORDER, width=1)
            draw.text((x0 + 10, y0 + BOX_H / 4), a_label[:26], font=name_font, fill=a_col, anchor="lm")
            draw.text((x0 + 10, y0 + BOX_H * 3 / 4), b_label[:26], font=name_font, fill=b_col, anchor="lm")

            # Bracket bağlayıcı xətlər (növbəti raunda) — "⊐" forması
            if r < num_rounds - 1:
                next_cy = all_centers[r + 1][i // 2]
                mid_x = x0 + BOX_W + COL_GAP / 2
                draw.line([(x0 + BOX_W, cy), (mid_x, cy)], fill=BORDER, width=2)
                if i % 2 == 0:
                    partner_cy = all_centers[r][i + 1] if i + 1 < len(matches) else cy
                    draw.line([(mid_x, cy), (mid_x, partner_cy)], fill=BORDER, width=2)
                    draw.line([(mid_x, next_cy), (x0 + BOX_W + COL_GAP, next_cy)], fill=BORDER, width=2)

    if tournament["status"] == "completed" and tournament.get("winner_team_id"):
        draw.text((width // 2, height - MARGIN // 2), "Qalib elan edildi", font=name_font, fill=GOLD, anchor="mm")

    _finalize(img).save(output_path)
    return output_path


SIGNUP_W = 700
SIGNUP_PAD = 30
SIGNUP_HEADER_H = 90
SIGNUP_ROW_H = 26
SIGNUP_FOOTER_H = 50

TEAM_SIZE_LABELS = {1: "Solo (1v1)", 2: "2v2", 5: "5v5"}


def generate_tournament_signup_card(tournament, participants, output_path):
    """Qeydiyyat kartı — iştirakçı sayına görə DİNAMİK hündürlük (digər kartlarla eyni prinsip)."""
    n_rows = max(len(participants), 1)
    height = SIGNUP_HEADER_H + n_rows * SIGNUP_ROW_H + SIGNUP_FOOTER_H

    img = _vertical_gradient(SIGNUP_W, height, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (SIGNUP_W - 1, height - 1)], outline=GOLD, width=2)
    draw.rectangle([(0, 0), (SIGNUP_W - 1, 5)], fill=GOLD)

    title_font = _font(24, True)
    sub_font = _font(13)
    row_font = _font(13)

    draw.text((SIGNUP_PAD, 18), tournament["name"], font=title_font, fill=WHITE)
    size_label = TEAM_SIZE_LABELS.get(tournament["team_size"], str(tournament["team_size"]))
    draw.text((SIGNUP_PAD, 52),
              f"Format: {size_label}  ·  İştirakçı: {len(participants)}",
              font=sub_font, fill=GRAY)
    draw.line([(SIGNUP_PAD, SIGNUP_HEADER_H - 10), (SIGNUP_W - SIGNUP_PAD, SIGNUP_HEADER_H - 10)],
              fill=BORDER, width=1)

    y = SIGNUP_HEADER_H
    if participants:
        for i, p in enumerate(participants):
            draw.text((SIGNUP_PAD, y), f"{i + 1}. {p['nick']}", font=row_font, fill=WHITE)
            y += SIGNUP_ROW_H
    else:
        draw.text((SIGNUP_PAD, y), "Hələ iştirakçı yoxdur.", font=row_font, fill=GRAY)
        y += SIGNUP_ROW_H

    draw.line([(SIGNUP_PAD, height - SIGNUP_FOOTER_H + 6), (SIGNUP_W - SIGNUP_PAD, height - SIGNUP_FOOTER_H + 6)],
              fill=BORDER, width=1)
    draw.text((SIGNUP_PAD, height - SIGNUP_FOOTER_H + 16),
              "Aşağıdakı düymələrlə qoşulun və ya ayrılın.", font=sub_font, fill=GRAY)

    _finalize(img).save(output_path)
    return output_path
