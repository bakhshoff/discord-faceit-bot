"""
Matç sonu xülasə kartı — PIL vizual.
Göstərir: skor, hər oyunçu K/A/D + ELO±, MVP / Top Fragger / Best Assist badge-ləri.
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_TOP    = (12, 10, 18)
BG_BOT    = (8,  7, 12)
PANEL     = (22, 20, 30)
PANEL2    = (28, 26, 38)
BORDER    = (48, 44, 60)
GOLD      = (240, 185, 40)
WHITE     = (244, 241, 234)
GRAY      = (130, 125, 145)
GREEN     = (88, 210, 110)
RED       = (210, 65, 58)
BLUE      = (80, 155, 230)
PURPLE    = (160, 90, 255)
TEAL      = (40, 200, 180)

FONT_B = [os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf"),
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "C:/Windows/Fonts/arialbd.ttf"]
FONT_R = [os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf"),
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "C:/Windows/Fonts/arial.ttf"]


def _f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for p in (FONT_B if bold else FONT_R):
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()


def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _grad(w, h):
    img = Image.new("RGB", (w, h), BG_TOP)
    d   = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def generate_match_recap_card(
    match_number: int,
    map_name: str,
    score_a: int,
    score_b: int,
    winner_label: str,          # "Komanda A" or "Komanda B"
    team_a: list,               # [{"nick","kills","assists","deaths","old_elo","new_elo"}, ...]
    team_b: list,
    output_path: str
) -> str:
    W       = 960
    ROW_H   = 46
    HEAD_H  = 100
    SCORE_H = 70
    SEC_H   = 32
    FOOT_H  = 34
    BADGE_H = 52

    n_players = max(len(team_a), len(team_b))
    H = HEAD_H + SCORE_H + SEC_H + n_players * ROW_H + BADGE_H + FOOT_H

    img  = _grad(W, H)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W-1, H-1)], outline=BORDER, width=2)

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (W, HEAD_H)], fill=(14, 12, 22))
    draw.text((28, 14), "CALESTIFY", font=_f(12, True), fill=GOLD)
    draw.text((28, 32), f"MATÇ XÜLASƏSI — No{match_number}", font=_f(26, True), fill=WHITE)
    draw.text((28, 66), f"Xəritə: {map_name}", font=_f(14), fill=GRAY)
    draw.line([(0, HEAD_H), (W, HEAD_H)], fill=BORDER, width=1)

    # ── Skor paneli ────────────────────────────────────────────────────────────
    sy = HEAD_H
    cx = W // 2
    a_win = winner_label == "Komanda A"
    b_win = winner_label == "Komanda B"

    draw.rectangle([(0, sy), (W, sy + SCORE_H)], fill=PANEL)
    # Komanda A
    a_col = GREEN if a_win else GRAY
    draw.text((cx // 2, sy + SCORE_H // 2), "KOMANDA A", font=_f(13, True), fill=a_col, anchor="mm")
    # Skor rəqəmləri
    sc_a = str(score_a)
    sc_b = str(score_b)
    draw.text((cx - 40, sy + SCORE_H // 2), sc_a, font=_f(36, True), fill=a_col, anchor="rm")
    draw.text((cx, sy + SCORE_H // 2),      ":",  font=_f(28, True), fill=GRAY,  anchor="mm")
    b_col = GREEN if b_win else GRAY
    draw.text((cx + 40, sy + SCORE_H // 2), sc_b, font=_f(36, True), fill=b_col, anchor="lm")
    # Komanda B
    draw.text((cx + (W - cx) // 2, sy + SCORE_H // 2), "KOMANDA B", font=_f(13, True), fill=b_col, anchor="mm")
    # KAZANAN badge
    win_x = (cx // 2) if a_win else (cx + (W - cx) // 2)
    draw.text((win_x, sy + SCORE_H - 8), "KAZANAN", font=_f(10, True), fill=GOLD, anchor="ms")

    # ── Sütun başlıqları ──────────────────────────────────────────────────────
    hy = sy + SCORE_H
    draw.rectangle([(0, hy), (W, hy + SEC_H)], fill=PANEL2)
    draw.line([(0, hy), (W, hy)], fill=BORDER, width=1)
    cols_left  = [28,  200, 290, 340, 390, 470]
    cols_right = [W//2 + 28, W//2 + 200, W//2 + 290, W//2 + 340, W//2 + 390, W//2 + 470]
    hdrs = ["Oyunçu", "K", "A", "D", "K/D", "ELO±"]

    for side_cols in (cols_left, cols_right):
        for xi, (hdr, x) in enumerate(zip(hdrs, side_cols)):
            align = "lm" if xi == 0 else "mm"
            draw.text((x, hy + SEC_H // 2), hdr, font=_f(10, True), fill=GOLD, anchor=align)
    draw.line([(W//2, hy), (W//2, hy + SEC_H)], fill=BORDER, width=1)

    # ── Oyunçu sıraları ───────────────────────────────────────────────────────
    ry = hy + SEC_H

    def _draw_team(players, base_x, is_winner):
        y = ry
        for i, p in enumerate(players):
            bg = (20, 28, 20) if is_winner else (28, 20, 20)
            if i % 2 == 0:
                draw.rectangle([(base_x, y), (base_x + W//2 - 1, y + ROW_H - 1)], fill=bg)

            kd     = round(p["kills"] / max(p["deaths"], 1), 2)
            elo_d  = p["new_elo"] - p["old_elo"]
            elo_s  = f"+{elo_d}" if elo_d >= 0 else str(elo_d)
            ec     = GREEN if elo_d > 0 else (RED if elo_d < 0 else GRAY)

            offsets = [28, 200, 290, 340, 390, 470]
            nick_f = _f(14, True)
            # Nick (kırp)
            nick_disp = p["nick"][:18]
            draw.text((base_x + offsets[0], y + ROW_H//2), nick_disp, font=nick_f, fill=WHITE, anchor="lm")
            for xi, (val, col) in enumerate([
                (str(p["kills"]),   GREEN),
                (str(p["assists"]), TEAL),
                (str(p["deaths"]),  RED),
                (str(kd),          GOLD),
                (elo_s,            ec),
            ]):
                draw.text((base_x + offsets[xi+1], y + ROW_H//2), val,
                          font=_f(13, True), fill=col, anchor="mm")
            y += ROW_H

    _draw_team(team_a, 0,      a_win)
    _draw_team(team_b, W // 2, b_win)

    # Orta çizgi
    draw.line([(W//2, ry), (W//2, ry + n_players * ROW_H)], fill=BORDER, width=1)

    # ── Badge bölməsi ─────────────────────────────────────────────────────────
    by = ry + n_players * ROW_H
    draw.rectangle([(0, by), (W, by + BADGE_H)], fill=PANEL)
    draw.line([(0, by), (W, by)], fill=BORDER, width=1)

    all_players = team_a + team_b
    if all_players:
        mvp         = max(all_players, key=lambda p: p["kills"] * 2 + p["assists"] - p["deaths"])
        top_fragger = max(all_players, key=lambda p: p["kills"])
        best_assist = max(all_players, key=lambda p: p["assists"])

        badges = [
            ("🏆 MVP",         mvp["nick"],         GOLD),
            ("🔫 Top Fragger", top_fragger["nick"],  RED),
            ("🤝 Best Assist",  best_assist["nick"],  TEAL),
        ]
        bw = W // len(badges)
        for bi, (badge_lbl, badge_nick, badge_col) in enumerate(badges):
            bx = bi * bw + bw // 2
            draw.text((bx, by + 14), badge_lbl,         font=_f(11, True), fill=badge_col, anchor="mm")
            draw.text((bx, by + 36), badge_nick[:18],   font=_f(13, True), fill=WHITE,      anchor="mm")
        for bi in range(1, len(badges)):
            draw.line([(bi * bw, by + 6), (bi * bw, by + BADGE_H - 6)], fill=BORDER, width=1)

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = by + BADGE_H
    draw.rectangle([(0, fy), (W, H)], fill=(10, 8, 16))
    draw.text((28, fy + FOOT_H // 2), "Calestify Gaming Community  •  Season 1",
              font=_f(11), fill=GRAY, anchor="lm")
    draw.text((W - 28, fy + FOOT_H // 2), f"Xəritə: {map_name}  •  Matç No{match_number}",
              font=_f(11), fill=GRAY, anchor="rm")

    img.save(output_path)
    return output_path
