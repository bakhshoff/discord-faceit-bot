"""
Turnir bracket kartı — PIL vizual.
Single-elimination, max 8 komanda (3 raund).
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG      = (12, 10, 20)
PANEL   = (22, 20, 32)
BORDER  = (55, 50, 75)
GOLD    = (240, 185, 40)
WHITE   = (244, 241, 234)
GRAY    = (130, 125, 148)
GREEN   = (70, 200, 100)
RED     = (200, 60, 55)
BLUE    = (80, 150, 225)
PURPLE  = (160, 90, 255)

FONT_B = [os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf"),
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "C:/Windows/Fonts/arialbd.ttf"]
FONT_R = [os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf"),
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "C:/Windows/Fonts/arial.ttf"]


def _f(size, bold=False):
    for p in (FONT_B if bold else FONT_R):
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()


def generate_tournament_card(tournament: dict, teams: list, matches: list, output_path: str) -> str:
    """
    tournament: {name, status, prize_coins, max_teams}
    teams:      [{id, team_name, captain_id, elo_avg}]
    matches:    [{round, match_num, team_a_name, team_b_name, winner_name, status}]
                status: 'pending' | 'active' | 'finished'
    """
    n_teams  = len(teams)
    if n_teams == 0: n_teams = 2
    # Raund sayı
    n_rounds = max(1, math.ceil(math.log2(n_teams))) if n_teams > 1 else 1

    SLOT_W   = 180
    SLOT_H   = 40
    SLOT_GAP = 18
    COL_W    = SLOT_W + 60
    HEAD_H   = 90
    FOOT_H   = 36
    PAD      = 30

    # Hər raundda neçə matç?
    def matches_in_round(r, total_teams):
        return max(1, total_teams // (2 ** r))

    max_matches = matches_in_round(1, n_teams if n_teams >= 2 else 2)
    col_h = max_matches * (SLOT_H * 2 + SLOT_GAP) + SLOT_GAP

    W = PAD * 2 + n_rounds * COL_W
    H = HEAD_H + col_h + FOOT_H

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

    # Header
    draw.rectangle([(0,0),(W,HEAD_H)], fill=(16,12,28))
    draw.line([(0,HEAD_H),(W,HEAD_H)], fill=GOLD, width=2)
    draw.text((PAD, 14), "CALESTIFY", font=_f(11,True), fill=GOLD)
    draw.text((PAD, 32), tournament.get("name","TURNIR"), font=_f(24,True), fill=WHITE)
    prize = tournament.get("prize_coins", 0)
    status_lbl = {"registration":"Qeydiyyat","active":"Aktiv","finished":"Bitdi"}.get(
        tournament.get("status",""), "")
    draw.text((PAD, 64), f"Mükafat: {prize} coin   Komanda: {n_teams}   {status_lbl}",
              font=_f(12), fill=GRAY)

    # Bracket
    # matches dict-i raund+match_num indexi ilə
    match_map = {}
    for m in matches:
        match_map[(m["round"], m["match_num"])] = m

    for rnd in range(1, n_rounds + 1):
        n_m    = matches_in_round(rnd, n_teams if n_teams >= 2 else 2)
        spacing = col_h / n_m
        col_x  = PAD + (rnd - 1) * COL_W

        for mi in range(1, n_m + 1):
            slot_y = HEAD_H + (mi - 1) * spacing + spacing / 2 - SLOT_H

            m = match_map.get((rnd, mi), {})
            name_a = m.get("team_a_name", "TBD")
            name_b = m.get("team_b_name", "TBD")
            winner = m.get("winner_name")
            mstatus = m.get("status", "pending")

            for ti, (name, y_off) in enumerate([(name_a, 0), (name_b, SLOT_H + 4)]):
                sy = int(slot_y) + y_off
                is_w = (name == winner and mstatus == "finished")
                is_l = (winner and name != winner and name not in ("TBD","?") and mstatus == "finished")
                bg_c  = (18, 40, 20) if is_w else ((30, 18, 18) if is_l else PANEL)
                bdr_c = GREEN if is_w else (RED if is_l else BORDER)
                t_col = GREEN if is_w else (GRAY if is_l else WHITE)

                draw.rounded_rectangle([(col_x, sy),(col_x+SLOT_W, sy+SLOT_H-2)],
                                       radius=5, fill=bg_c, outline=bdr_c, width=2)
                draw.text((col_x+10, sy+SLOT_H//2-1), name[:20],
                          font=_f(12,True), fill=t_col, anchor="lm")
                if is_w:
                    draw.text((col_x+SLOT_W-8, sy+SLOT_H//2-1), "W",
                              font=_f(10,True), fill=GREEN, anchor="rm")

            # Raund etiketi (ilk matç üçün)
            if mi == 1:
                rlbl = f"R{rnd}" if rnd < n_rounds else "FİNAL"
                draw.text((col_x + SLOT_W//2, HEAD_H + 8), rlbl,
                          font=_f(10,True), fill=GOLD, anchor="mm")

            # Birləşdirici xətt (sonrakı raundla)
            if rnd < n_rounds:
                mid_y = int(slot_y) + SLOT_H + 2
                draw.line([(col_x+SLOT_W, mid_y), (col_x+COL_W, mid_y)],
                          fill=BORDER, width=1)

    # Footer
    draw.rectangle([(0,H-FOOT_H),(W,H)], fill=(10,8,18))
    draw.text((PAD, H-FOOT_H+FOOT_H//2), "Calestify Gaming Community  •  Tournament",
              font=_f(11), fill=GRAY, anchor="lm")

    img.save(output_path)
    return output_path


def generate_tournament_registration_card(tournament: dict, teams: list, output_path: str) -> str:
    """Qeydiyyat mərhələsindəki turnir kartı — qeydiyyatlı komandaları göstərir."""
    ROW_H   = 48
    HEAD_H  = 90
    FOOT_H  = 32
    W       = 700
    H       = HEAD_H + max(1, len(teams)) * ROW_H + FOOT_H + 20

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

    # Header
    draw.rectangle([(0,0),(W,HEAD_H)], fill=(16,12,28))
    draw.line([(0,HEAD_H),(W,HEAD_H)], fill=GOLD, width=2)
    draw.text((28, 14), "CALESTIFY", font=_f(11,True), fill=GOLD)
    draw.text((28, 32), tournament.get("name","TURNIR"), font=_f(22,True), fill=WHITE)
    max_t = tournament.get("max_teams", 8)
    draw.text((28, 64), f"Qeydiyyat — {len(teams)}/{max_t} komanda",
              font=_f(12), fill=GRAY)
    draw.text((W-28, 64), f"Mükafat: {tournament.get('prize_coins',0)} coin",
              font=_f(12,True), fill=GOLD, anchor="rm")

    y = HEAD_H + 10
    if not teams:
        draw.text((28, y+14), "Hələ heç bir komanda qeydiyyatdan keçməyib.",
                  font=_f(13), fill=GRAY)
    else:
        for i, t in enumerate(teams):
            if i % 2 == 0:
                draw.rectangle([(2,y),(W-2,y+ROW_H-1)], fill=(20,18,30))
            draw.text((28, y+ROW_H//2), f"{i+1}.", font=_f(13,True), fill=GRAY, anchor="lm")
            draw.text((58, y+ROW_H//2), t.get("team_name","?")[:24],
                      font=_f(15,True), fill=WHITE, anchor="lm")
            draw.text((W-28, y+ROW_H//2), f"Ort. ELO: {int(t.get('elo_avg',0))}",
                      font=_f(12), fill=BLUE, anchor="rm")
            draw.line([(18,y+ROW_H-1),(W-18,y+ROW_H-1)], fill=BORDER, width=1)
            y += ROW_H

    draw.rectangle([(0,H-FOOT_H),(W,H)], fill=(10,8,18))
    draw.text((28, H-FOOT_H+FOOT_H//2), "/turnir_qeydi ilə komandanı qeydiyyatdan kec",
              font=_f(11), fill=GRAY, anchor="lm")
    img.save(output_path)
    return output_path


def generate_prize_card(tournament: dict, item_names: list, skin_names: list, output_path: str) -> str:
    """
    Turnir mükafat fondu vizual kartı.
    item_names: [{"name":"Qizili Banner","type":"banner"}, ...]
    skin_names: [{"name":"AWM BOOM"}, ...]
    """
    W     = 700
    ROW_H = 52
    HEAD_H = 90
    SEC_H  = 30
    FOOT_H = 34
    PAD    = 28

    prize_rows = []
    if tournament.get("prize_coins", 0):
        prize_rows.append(("coin",   f"{tournament['prize_coins']} Coin",  GOLD))
    if tournament.get("prize_azn", 0):
        prize_rows.append(("azn",    f"{tournament['prize_azn']:.2f} AZN", GREEN))
    for it in item_names:
        typ  = it.get("type", "item")
        icon = "🖼" if typ == "banner" else ("🔲" if typ == "avatar_frame" else "🎨")
        prize_rows.append(("item", f"{icon} {it['name']}", PURPLE))
    for sk in skin_names:
        prize_rows.append(("skin", f"🔫 {sk['name']}", BLUE))

    if not prize_rows:
        prize_rows.append(("empty", "Henuz mukafat teyin edilmeyib", GRAY))

    H = HEAD_H + SEC_H + max(1, len(prize_rows)) * ROW_H + FOOT_H

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

    # Header
    draw.rectangle([(0,0),(W,HEAD_H)], fill=(16,12,28))
    draw.line([(0,HEAD_H),(W,HEAD_H)], fill=GOLD, width=2)
    draw.text((PAD, 14), "CALESTIFY", font=_f(11,True), fill=GOLD)
    draw.text((PAD, 32), tournament.get("name","TURNIR"), font=_f(22,True), fill=WHITE)
    draw.text((PAD, 64), "MUKAFAT FONDU", font=_f(13,True), fill=GOLD)
    st_map = {"registration":"Qeydiyyat","active":"Aktiv","finished":"Bitdi"}
    draw.text((W-PAD, 64), st_map.get(tournament.get("status",""), ""),
              font=_f(12), fill=GRAY, anchor="rm")

    # Section header
    sh_y = HEAD_H
    draw.rectangle([(0,sh_y),(W,sh_y+SEC_H)], fill=(24,20,40))
    draw.text((PAD, sh_y+SEC_H//2), "Mükafat növü", font=_f(10,True), fill=GRAY, anchor="lm")
    draw.text((W-PAD, sh_y+SEC_H//2), "Dəyər / Əşya", font=_f(10,True), fill=GRAY, anchor="rm")

    y = sh_y + SEC_H
    for i, (ptype, label, col) in enumerate(prize_rows):
        if i % 2 == 0:
            draw.rectangle([(2,y),(W-2,y+ROW_H-1)], fill=(20,18,32))
        # Sol rəngli şerid
        draw.rectangle([(0,y),(6,y+ROW_H-1)], fill=col)
        # Icon / tip
        icons = {"coin":"🪙","azn":"💵","item":"🎨","skin":"🔫","empty":"—"}
        draw.text((PAD, y+ROW_H//2), icons.get(ptype, "•"),
                  font=_f(14), fill=col, anchor="lm")
        draw.text((PAD+30, y+ROW_H//2), label[:42],
                  font=_f(15,True), fill=WHITE if ptype != "empty" else GRAY, anchor="lm")
        draw.line([(18,y+ROW_H-1),(W-18,y+ROW_H-1)], fill=BORDER, width=1)
        y += ROW_H

    # Footer
    draw.rectangle([(0,H-FOOT_H),(W,H)], fill=(10,8,18))
    draw.text((PAD, H-FOOT_H+FOOT_H//2),
              "/turnir_mukafat ile mukafat deyis",
              font=_f(11), fill=GRAY, anchor="lm")

    img.save(output_path)
    return output_path
