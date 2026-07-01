"""S2-stil Battle Pass vizual kartı — ayrıca fayl."""
import os, math as _math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR2 = os.path.dirname(os.path.abspath(__file__))

PASS_BG2     = (18, 15, 28)
PASS_HEADER  = (10, 8, 20)
PASS_GOLD    = (255, 200, 50)
PASS_PURPLE  = (130, 60, 255)
PASS_TEAL    = (30, 200, 180)
PASS_FREE_BG = (22, 28, 22)
PASS_PREM_BG = (28, 18, 38)
PASS_BORDER  = (60, 50, 85)
WHITE2       = (240, 238, 230)
GRAY2        = (130, 125, 145)

PASS_MILESTONES = [5, 10, 15, 20, 25, 30]

# Bütün 30 level üçün FREE mükafatlar
PASS_FREE_REWARDS = {
    1:  {"label": "50 Coin",   "color": PASS_GOLD},
    2:  {"label": "25 Coin",   "color": PASS_GOLD},
    3:  {"label": "25 Coin",   "color": PASS_GOLD},
    4:  {"label": "25 Coin",   "color": PASS_GOLD},
    5:  {"label": "200 Coin",  "color": PASS_GOLD},
    6:  {"label": "50 Coin",   "color": PASS_GOLD},
    7:  {"label": "50 Coin",   "color": PASS_GOLD},
    8:  {"label": "50 Coin",   "color": PASS_GOLD},
    9:  {"label": "50 Coin",   "color": PASS_GOLD},
    10: {"label": "300 Coin",  "color": PASS_GOLD},
    11: {"label": "75 Coin",   "color": PASS_GOLD},
    12: {"label": "75 Coin",   "color": PASS_GOLD},
    13: {"label": "75 Coin",   "color": PASS_GOLD},
    14: {"label": "75 Coin",   "color": PASS_GOLD},
    15: {"label": "400 Coin",  "color": PASS_GOLD},
    16: {"label": "100 Coin",  "color": PASS_GOLD},
    17: {"label": "100 Coin",  "color": PASS_GOLD},
    18: {"label": "100 Coin",  "color": PASS_GOLD},
    19: {"label": "100 Coin",  "color": PASS_GOLD},
    20: {"label": "500 Coin",  "color": PASS_GOLD},
    21: {"label": "150 Coin",  "color": PASS_GOLD},
    22: {"label": "150 Coin",  "color": PASS_GOLD},
    23: {"label": "150 Coin",  "color": PASS_GOLD},
    24: {"label": "150 Coin",  "color": PASS_GOLD},
    25: {"label": "750 Coin",  "color": PASS_GOLD},
    26: {"label": "200 Coin",  "color": PASS_GOLD},
    27: {"label": "200 Coin",  "color": PASS_GOLD},
    28: {"label": "200 Coin",  "color": PASS_GOLD},
    29: {"label": "200 Coin",  "color": PASS_GOLD},
    30: {"label": "1000 Coin", "color": PASS_GOLD},
}

# Bütün 30 level üçün PREMIUM mükafatlar
PASS_PREM_REWARDS = {
    1:  {"label": "50 Coin",   "color": PASS_GOLD},
    2:  {"label": "25 Coin",   "color": PASS_GOLD},
    3:  {"label": "25 Coin",   "color": PASS_GOLD},
    4:  {"label": "25 Coin",   "color": PASS_GOLD},
    5:  {"label": "S1 Banner", "color": PASS_TEAL},
    6:  {"label": "50 Coin",   "color": PASS_GOLD},
    7:  {"label": "50 Coin",   "color": PASS_GOLD},
    8:  {"label": "50 Coin",   "color": PASS_GOLD},
    9:  {"label": "50 Coin",   "color": PASS_GOLD},
    10: {"label": "ELO Boost", "color": PASS_PURPLE},
    11: {"label": "75 Coin",   "color": PASS_GOLD},
    12: {"label": "75 Coin",   "color": PASS_GOLD},
    13: {"label": "75 Coin",   "color": PASS_GOLD},
    14: {"label": "75 Coin",   "color": PASS_GOLD},
    15: {"label": "1000 Coin", "color": PASS_GOLD},
    16: {"label": "100 Coin",  "color": PASS_GOLD},
    17: {"label": "100 Coin",  "color": PASS_GOLD},
    18: {"label": "100 Coin",  "color": PASS_GOLD},
    19: {"label": "100 Coin",  "color": PASS_GOLD},
    20: {"label": "S1 Frame",  "color": PASS_TEAL},
    21: {"label": "150 Coin",  "color": PASS_GOLD},
    22: {"label": "150 Coin",  "color": PASS_GOLD},
    23: {"label": "150 Coin",  "color": PASS_GOLD},
    24: {"label": "150 Coin",  "color": PASS_GOLD},
    25: {"label": "2000 Coin", "color": PASS_GOLD},
    26: {"label": "200 Coin",  "color": PASS_GOLD},
    27: {"label": "200 Coin",  "color": PASS_GOLD},
    28: {"label": "200 Coin",  "color": PASS_GOLD},
    29: {"label": "200 Coin",  "color": PASS_GOLD},
    30: {"label": "AWM BOOM",  "color": (255, 220, 0)},
}

FONT_PATHS_B = [
    os.path.join(BASE_DIR2, "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_PATHS_R = [
    os.path.join(BASE_DIR2, "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _f(size, bold=False):
    for p in (FONT_PATHS_B if bold else FONT_PATHS_R):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _coin_icon(draw, cx, cy, r, amount, gold=(255, 200, 50)):
    """3D coin görünüşü."""
    shadow = tuple(max(c-60, 0) for c in gold)
    # Kölgə
    draw.ellipse([(cx-r+3, cy-r//3+3), (cx+r+3, cy+r//3+3)], fill=(0,0,0,60))
    # Yan tərəf (3D effekt)
    for i in range(6):
        shade = tuple(max(c-80+i*10, 0) for c in gold)
        draw.ellipse([(cx-r, cy-r//3+i), (cx+r, cy+r//3+i)], fill=shade)
    # Üst səthi
    draw.ellipse([(cx-r, cy-r//3), (cx+r, cy+r//3)], fill=gold)
    # Parıltı
    draw.ellipse([(cx-r+8, cy-r//3+3), (cx-r//2, cy)], fill=(255,240,180,200))
    # Amount text
    txt = str(amount)
    draw.text((cx, cy), txt, font=_f(10, True), fill=(80,50,0), anchor="mm")


def _reward_img(level: int, is_premium: bool, size=(130, 100)):
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    reward = (PASS_PREM_REWARDS if is_premium else PASS_FREE_REWARDS)[level]
    lbl    = reward["label"]
    col    = reward["color"]
    body_h = h - 20  # Label üçün alt boşluq

    # ── AWM BOOM — real şəkil ────────────────────────────────────────────────
    if is_premium and level == 30:
        boom = os.path.join(BASE_DIR2, "assets", "awm_boom.png")
        try:
            sk = Image.open(boom).convert("RGBA")
            sk.thumbnail((w - 4, body_h - 4), Image.LANCZOS)
            ox = (w - sk.width) // 2
            oy = (body_h - sk.height) // 2
            img.paste(sk, (ox, oy), sk)
            # Qızılı glow border
            draw.rounded_rectangle([(1,1),(w-2,body_h+2)], radius=6, outline=(255,220,0), width=2)
            draw.text((w//2, h-8), "AWM BOOM", font=_f(9, True), fill=(255,220,0), anchor="mm")
            return img
        except Exception:
            pass

    # ── COIN mükafatları ──────────────────────────────────────────────────────
    if "Coin" in lbl:
        amount = lbl.replace(" Coin","").replace("Coin","").strip()
        gold   = (255, 200, 50)
        # Arxa panel
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=8,
                               fill=(40,32,8), outline=(100,80,20), width=1)
        # Parıltılı xəttlər (deco)
        for i in range(3):
            y_ = 12 + i*10
            draw.line([(8,y_),(w-8,y_)], fill=(60,48,10), width=1)
        # Böyük coin
        cx, cy = w//2, body_h//2
        _coin_icon(draw, cx, cy-5, min(w,body_h)//3, amount, gold)
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=gold, anchor="mm")
        return img

    # ── S1 BANNER ─────────────────────────────────────────────────────────────
    if "Banner" in lbl:
        # Gradient arxa plan
        for y_ in range(body_h):
            t  = y_ / body_h
            r_ = int(0 + (30-0)*t)
            g_ = int(50 + (120-50)*t)
            b_ = int(30 + (60-30)*t)
            draw.line([(6,y_+4),(w-6,y_+4)], fill=(r_,g_,b_))
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6, outline=PASS_TEAL, width=2)
        # Ulduzlar
        for sx,sy in [(w//4,body_h//4),(3*w//4,body_h//4),(w//2,body_h//2-10)]:
            draw.polygon([(sx,sy-8),(sx+3,sy-2),(sx+9,sy-2),(sx+4,sy+2),
                          (sx+6,sy+8),(sx,sy+4),(sx-6,sy+8),(sx-4,sy+2),
                          (sx-9,sy-2),(sx-3,sy-2)], fill=(255,220,80))
        draw.text((w//2, body_h-14), "SEASON 1", font=_f(9, True), fill=WHITE2, anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_TEAL, anchor="mm")
        return img

    # ── S1 FRAME ──────────────────────────────────────────────────────────────
    if "Frame" in lbl:
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6,
                               fill=(10,25,30), outline=PASS_TEAL, width=2)
        # Avatar yer saxlayıcısı
        aw = w - 24
        ah = body_h - 20
        ax, ay = 12, 10
        draw.rounded_rectangle([(ax,ay),(ax+aw,ay+ah)], radius=4, fill=(15,35,40))
        # Çərçivə kənarları
        t = 6
        for corner_rect in [
            (ax, ay, ax+t, ay+t),
            (ax+aw-t, ay, ax+aw, ay+t),
            (ax, ay+ah-t, ax+t, ay+ah),
            (ax+aw-t, ay+ah-t, ax+aw, ay+ah)
        ]:
            x0,y0,x1,y1 = corner_rect
            draw.rectangle([(x0,y0),(x1,y1)], fill=PASS_TEAL)
        draw.text((w//2, ay+ah//2), "AVATAR", font=_f(8), fill=(50,120,120), anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_TEAL, anchor="mm")
        return img

    # ── ELO BOOST ─────────────────────────────────────────────────────────────
    if "Boost" in lbl:
        # Arxa şimşək fon
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6,
                               fill=(20,10,40), outline=PASS_PURPLE, width=2)
        # Şimşək bolt
        lx, ly = w//2, body_h//2
        bolt = [(lx-8,ly-20),(lx+4,ly-20),(lx-4,ly),(lx+10,ly),(lx-10,ly+20),(lx+2,ly+20),(lx-4,ly),(lx-14,ly)]
        draw.polygon(bolt, fill=PASS_PURPLE)
        draw.polygon(bolt, outline=(200,150,255), width=1)
        # +ELO yazısı
        draw.text((w//2, body_h-10), "+10% ELO", font=_f(8, True), fill=(200,150,255), anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_PURPLE, anchor="mm")
        return img

    # ── Fallback ──────────────────────────────────────────────────────────────
    dim = tuple(max(c//4, 0) for c in col)
    draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6, fill=dim, outline=col, width=2)
    draw.text((w//2, body_h//2), lbl[:10], font=_f(10, True), fill=WHITE2, anchor="mm")
    draw.text((w//2, h-8), lbl, font=_f(9, True), fill=col, anchor="mm")
    return img


def _draw_frame(pass_data: dict, missions: list, glow: float):
    COLS   = 6
    CELL_W = 148
    FREE_H = 140
    BAR_H  = 54
    PREM_H = 195
    MIS_H  = 110
    FOOT_H = 28
    LEFT_W = 128
    W      = LEFT_W + COLS * CELL_W + 6
    H      = 62 + FREE_H + BAR_H + PREM_H + MIS_H + FOOT_H

    img  = Image.new("RGB", (W, H), PASS_BG2)
    draw = ImageDraw.Draw(img)

    level      = pass_data.get("level", 0)
    xp         = pass_data.get("xp", 0)
    is_premium = pass_data.get("is_premium", False)
    MAX_LVL    = 30
    XP_NEED    = 500

    # Header
    draw.rectangle([(0, 0), (W, 62)], fill=PASS_HEADER)
    draw.line([(0, 60), (W, 60)], fill=PASS_GOLD, width=2)
    draw.text((14, 8),  "CALESTIFY",       font=_f(11, True), fill=PASS_GOLD)
    draw.text((14, 24), "SEASON 1 PASS",   font=_f(20, True), fill=WHITE2)
    tier     = "GOLD PASS" if is_premium else "FREE PASS"
    tier_col = PASS_GOLD  if is_premium else (140, 140, 160)
    draw.text((W - 14, 16), tier,          font=_f(13, True), fill=tier_col,  anchor="rm")
    draw.text((W - 14, 34), f"LVL {level}/{MAX_LVL}", font=_f(12, True), fill=PASS_GOLD, anchor="rm")

    y0 = 63

    # Left labels
    draw.rectangle([(0, y0),             (LEFT_W - 3, y0 + FREE_H)],           fill=PASS_FREE_BG)
    draw.rectangle([(0, y0+FREE_H+BAR_H),(LEFT_W - 3, y0+FREE_H+BAR_H+PREM_H)], fill=PASS_PREM_BG)
    draw.line([(LEFT_W - 2, y0), (LEFT_W - 2, y0 + FREE_H + BAR_H + PREM_H)], fill=PASS_BORDER, width=2)

    fl_y = y0 + FREE_H // 2
    draw.text((LEFT_W // 2, fl_y - 8), "FREE", font=_f(14, True), fill=GRAY2,    anchor="mm")
    draw.text((LEFT_W // 2, fl_y + 10),"PASS", font=_f(14, True), fill=GRAY2,    anchor="mm")

    pl_y = y0 + FREE_H + BAR_H + PREM_H // 2
    if is_premium:
        gc = int(80 + 80 * glow)
        draw.rectangle([(0, y0+FREE_H+BAR_H), (3, y0+FREE_H+BAR_H+PREM_H)], fill=(gc, gc//2, 0))
        draw.text((LEFT_W // 2, pl_y - 10), "GOLD", font=_f(14, True), fill=PASS_GOLD, anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 8),  "PASS", font=_f(14, True), fill=PASS_GOLD, anchor="mm")
    else:
        draw.text((LEFT_W // 2, pl_y - 14), "GOLD", font=_f(14, True), fill=(80, 60, 100), anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 4),  "PASS", font=_f(14, True), fill=(80, 60, 100), anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 24), "7 AZN", font=_f(11, True), fill=PASS_GOLD,    anchor="mm")

    # Reward cells
    for ci, lv in enumerate(PASS_MILESTONES):
        cx   = LEFT_W + ci * CELL_W
        done = lv <= level
        is_cur = (lv == level + 1 and lv > 0) or (level == 0 and lv == 5)

        # Free cell
        fc = (30, 42, 30) if done else PASS_FREE_BG
        draw.rectangle([(cx, y0), (cx + CELL_W - 2, y0 + FREE_H)], fill=fc)
        fi = _reward_img(lv, False, (CELL_W - 16, FREE_H - 22))
        img.paste(fi, (cx + 8, y0 + 6), fi)
        if done:
            draw.text((cx + CELL_W // 2, y0 + FREE_H - 10), "ALINDI",
                      font=_f(9, True), fill=(60, 200, 60), anchor="mm")
        draw.line([(cx, y0), (cx, y0 + FREE_H)], fill=PASS_BORDER, width=1)

        # Premium cell
        pc = (42, 28, 65) if (done and is_premium) else PASS_PREM_BG
        draw.rectangle([(cx, y0+FREE_H+BAR_H), (cx+CELL_W-2, y0+FREE_H+BAR_H+PREM_H)], fill=pc)
        pi_h = PREM_H - 28
        pi = _reward_img(lv, True, (CELL_W - 12, pi_h))
        img.paste(pi, (cx + 6, y0 + FREE_H + BAR_H + 6), pi)
        rew  = PASS_PREM_REWARDS[lv]
        rcol = rew["color"] if is_premium else (70, 55, 95)
        draw.text((cx + CELL_W // 2, y0+FREE_H+BAR_H+PREM_H-10), rew["label"],
                  font=_f(9, True), fill=rcol, anchor="mm")
        if done and is_premium:
            draw.text((cx + CELL_W // 2, y0+FREE_H+BAR_H+8), "ALINDI",
                      font=_f(9, True), fill=PASS_GOLD, anchor="mm")
        draw.line([(cx, y0+FREE_H+BAR_H), (cx, y0+FREE_H+BAR_H+PREM_H)], fill=PASS_BORDER, width=1)

        # Glow on current next level
        if is_cur:
            gc2 = int(130 + 120 * glow)
            draw.rectangle([(cx, y0), (cx+CELL_W-2, y0+FREE_H+BAR_H+PREM_H)],
                           outline=(gc2, gc2 // 2, 0), width=2)

    # Progress bar
    bar_y = y0 + FREE_H
    draw.rectangle([(0, bar_y), (W, bar_y + BAR_H)], fill=(12, 10, 22))
    bx, bw = LEFT_W + 10, COLS * CELL_W - 20
    bh = 20
    by = bar_y + (BAR_H - bh) // 2
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=8, fill=(35, 28, 52))
    total_xp = level * XP_NEED + xp
    max_xp   = MAX_LVL * XP_NEED
    filled   = int(bw * min(total_xp / max_xp, 1.0))
    if filled > 6:
        draw.rounded_rectangle([(bx, by), (bx + filled, by + bh)], radius=8, fill=PASS_TEAL)
    draw.text((bx + bw // 2, by + bh // 2), f"{total_xp} / {max_xp} XP",
              font=_f(10, True), fill=WHITE2, anchor="mm")
    # Milestone ticks
    for ci, lv in enumerate(PASS_MILESTONES):
        mx  = LEFT_W + (ci + 1) * CELL_W - CELL_W // 2
        dne = lv <= level
        mc  = PASS_GOLD if dne else (70, 60, 90)
        draw.rectangle([(mx - 1, bar_y + 4), (mx + 1, bar_y + BAR_H - 4)], fill=mc)
        draw.text((mx, bar_y + 2), str(lv), font=_f(8), fill=mc, anchor="mb")

    # Missions
    mis_y0 = y0 + FREE_H + BAR_H + PREM_H + 6
    draw.line([(0, mis_y0 - 3), (W, mis_y0 - 3)], fill=PASS_BORDER, width=1)
    draw.text((14, mis_y0 + 4), "AKTİV MİSSİYALAR", font=_f(11, True), fill=PASS_GOLD)
    mc_w   = (W - LEFT_W) // 3
    act_ms = [m for m in missions if not m["completed"]][:3]
    for mi, m in enumerate(act_ms):
        mx2   = LEFT_W + mi * mc_w
        my2   = mis_y0 + 22
        pct   = min(m["progress"] / m["target"], 1.0) if m["target"] else 1.0
        cat_c = PASS_GOLD if m["cat"] == "seasonal" else (PASS_TEAL if m["cat"] == "weekly" else GRAY2)
        draw.rectangle([(mx2 + 3, my2), (mx2 + mc_w - 5, my2 + 72)], fill=(20, 16, 30), outline=PASS_BORDER, width=1)
        draw.text((mx2 + 8, my2 + 6),  m["desc"][:26],                    font=_f(10), fill=WHITE2)
        draw.text((mx2 + 8, my2 + 20), f"{m['progress']}/{m['target']}  +{m['xp']} XP", font=_f(9), fill=cat_c)
        bw2 = mc_w - 22
        draw.rectangle([(mx2 + 8, my2 + 34), (mx2 + 8 + bw2, my2 + 44)], fill=(35, 28, 52))
        if pct > 0:
            draw.rectangle([(mx2 + 8, my2 + 34), (mx2 + 8 + int(bw2 * pct), my2 + 44)], fill=cat_c)
        draw.text((mx2 + 8 + bw2 // 2, my2 + 58), f"{int(pct*100)}%",
                  font=_f(10, True), fill=WHITE2, anchor="mm")

    # Footer
    draw.rectangle([(0, H - FOOT_H), (W, H)], fill=PASS_HEADER)
    draw.text((14, H - FOOT_H + 8), "Calestify FACEIT  •  Season 1", font=_f(9), fill=GRAY2)
    if not is_premium:
        draw.text((W - 14, H - FOOT_H + 8), "/pass_al ile Premium al — 7 AZN",
                  font=_f(9, True), fill=PASS_GOLD, anchor="rm")

    return img


def generate_pass_gif(pass_data: dict, missions: list, output_path: str):
    FRAMES, DUR = 16, 100
    frames = []
    for fi in range(FRAMES):
        glow = (_math.sin(fi / FRAMES * 2 * _math.pi) + 1) / 2
        frames.append(_draw_frame(pass_data, missions, glow))
    frames[0].save(output_path, save_all=True, append_images=frames[1:],
                   loop=0, duration=[DUR] * FRAMES, optimize=False)
    return output_path


def generate_pass_card(pass_data: dict, missions: list, output_path: str):
    img = _draw_frame(pass_data, missions, 0.85)
    img.save(output_path)
    return output_path


def generate_pass_levels_card(pass_data: dict, output_path: str):
    """1-30 bütün levellərin mükafat siyahısı — ayrıca statik kart."""
    from database import BP_LEVEL_REWARDS
    COLS   = 6
    ROWS   = 5          # 30 level / 6 = 5 sıra
    CW     = 148        # cell width
    FREE_H = 88
    PREM_H = 110
    GAP    = 4
    PAD    = 12
    HEAD   = 56
    FOOT   = 28
    W      = PAD*2 + COLS * CW
    H      = HEAD + ROWS * (FREE_H + PREM_H + GAP + 30) + FOOT

    level      = pass_data.get("level", 0)
    is_premium = pass_data.get("is_premium", False)

    img  = Image.new("RGB", (W, H), PASS_BG2)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([(0,0),(W,HEAD)], fill=PASS_HEADER)
    draw.line([(0,HEAD-2),(W,HEAD-2)], fill=PASS_GOLD, width=2)
    draw.text((PAD, 10), "CALESTIFY", font=_f(11, True), fill=PASS_GOLD)
    draw.text((PAD, 26), "SEASON 1 — BUTUN LEVELLERIN MUKAFATLARI", font=_f(14, True), fill=WHITE2)
    tier = "GOLD PASS" if is_premium else "FREE PASS"
    draw.text((W-PAD, 30), tier, font=_f(12, True), fill=PASS_GOLD if is_premium else GRAY2, anchor="rm")

    # All 30 levels in grid
    for row in range(ROWS):
        for col in range(COLS):
            lv    = row * COLS + col + 1
            if lv > 30:
                break
            cx   = PAD + col * CW
            cy   = HEAD + row * (FREE_H + PREM_H + GAP + 30)
            done = lv <= level

            # Level number bar
            lv_col = PASS_GOLD if lv in {5,10,15,20,25,30} else (60,55,80)
            draw.rectangle([(cx, cy),(cx+CW-2, cy+22)], fill=lv_col if done else (30,25,45))
            draw.text((cx+CW//2, cy+11), f"LVL {lv}", font=_f(9, True),
                      fill=(20,15,5) if done else GRAY2, anchor="mm")

            # FREE cell
            fc = (28,40,28) if done else PASS_FREE_BG
            draw.rectangle([(cx, cy+22),(cx+CW-2, cy+22+FREE_H)], fill=fc)
            fi = _reward_img(lv, False, (CW-12, FREE_H-16))
            img.paste(fi, (cx+6, cy+24), fi)
            if done:
                draw.text((cx+CW//2, cy+22+FREE_H-6), "✓", font=_f(9,True), fill=(60,200,60), anchor="mm")
            draw.line([(cx,cy+22),(cx+CW-2,cy+22)], fill=PASS_BORDER, width=1)

            # PREM cell
            pc = (40,28,62) if (done and is_premium) else (22,15,35)
            draw.rectangle([(cx, cy+22+FREE_H+GAP),(cx+CW-2, cy+22+FREE_H+GAP+PREM_H)], fill=pc)
            pi = _reward_img(lv, True, (CW-12, PREM_H-16))
            img.paste(pi, (cx+6, cy+22+FREE_H+GAP+4), pi)
            if done and is_premium:
                draw.text((cx+CW//2, cy+22+FREE_H+GAP+PREM_H-6), "✓",
                          font=_f(9,True), fill=PASS_GOLD, anchor="mm")

            # Borders
            draw.line([(cx,cy),(cx,cy+22+FREE_H+GAP+PREM_H)], fill=PASS_BORDER, width=1)
            draw.line([(cx,cy+22+FREE_H+GAP),(cx+CW-2,cy+22+FREE_H+GAP)], fill=PASS_BORDER, width=1)

    # Footer
    draw.rectangle([(0,H-FOOT),(W,H)], fill=PASS_HEADER)
    draw.text((PAD, H-FOOT+8), "Calestify Season 1 Pass  •  /pass_al — 7 AZN", font=_f(9), fill=GRAY2)

    img.save(output_path)
    return output_path
