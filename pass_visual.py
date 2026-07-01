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
PASS_FREE_REWARDS = {
    5:  {"label": "200 Coin",  "color": PASS_GOLD},
    10: {"label": "300 Coin",  "color": PASS_GOLD},
    15: {"label": "400 Coin",  "color": PASS_GOLD},
    20: {"label": "500 Coin",  "color": PASS_GOLD},
    25: {"label": "750 Coin",  "color": PASS_GOLD},
    30: {"label": "1000 Coin", "color": PASS_GOLD},
}
PASS_PREM_REWARDS = {
    5:  {"label": "S1 Banner",  "color": PASS_TEAL},
    10: {"label": "ELO Boost",  "color": PASS_PURPLE},
    15: {"label": "1000 Coin",  "color": PASS_GOLD},
    20: {"label": "S1 Frame",   "color": PASS_TEAL},
    25: {"label": "2000 Coin",  "color": PASS_GOLD},
    30: {"label": "AWM BOOM",   "color": (255, 220, 0)},
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


def _reward_img(level: int, is_premium: bool, size=(130, 100)):
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if is_premium and level == 30:
        boom = os.path.join(BASE_DIR2, "assets", "awm_boom.png")
        try:
            sk = Image.open(boom).convert("RGBA")
            sk.thumbnail((w, h - 18), Image.LANCZOS)
            ox = (w - sk.width) // 2
            oy = (h - 18 - sk.height) // 2
            img.paste(sk, (ox, oy), sk)
            draw.text((w // 2, h - 8), "AWM BOOM", font=_f(9, True),
                      fill=(255, 220, 0), anchor="mm")
            return img
        except Exception:
            pass

    reward = (PASS_PREM_REWARDS if is_premium else PASS_FREE_REWARDS)[level]
    col    = reward["color"]
    lbl    = reward["label"]
    dim    = tuple(max(c // 4, 0) for c in col)

    if is_premium:
        if "Banner" in lbl:
            draw.rounded_rectangle([(10, 8), (w-10, h-20)], radius=6, fill=dim, outline=col, width=2)
            draw.line([(w//2, 14), (w//2, h-24)], fill=col, width=2)
        elif "Frame" in lbl:
            draw.rounded_rectangle([(8, 6), (w-8, h-20)], radius=4, outline=col, width=3)
            draw.rounded_rectangle([(18, 16), (w-18, h-30)], radius=2, fill=dim, outline=col, width=1)
        elif "Boost" in lbl:
            pts = [(w//2, 8), (w-10, h-20), (10, h-20)]
            draw.polygon(pts, fill=col)
            draw.text((w//2, h//2 - 4), "ELO", font=_f(11, True), fill=(20, 10, 40), anchor="mm")
        else:
            draw.ellipse([(w//2-30, h//2-32), (w//2+30, h//2+8)], fill=col)
            draw.text((w//2, h//2 - 12), "C", font=_f(22, True), fill=(20, 15, 5), anchor="mm")
    else:
        draw.rounded_rectangle([(8, 6), (w-8, h-20)], radius=8, fill=dim, outline=col, width=2)
        draw.ellipse([(w//2-20, h//2-30), (w//2+20, h//2+10)], fill=col)

    draw.text((w // 2, h - 8), lbl, font=_f(9, True), fill=WHITE2, anchor="mm")
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
