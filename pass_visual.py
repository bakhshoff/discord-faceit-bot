"""S2-stil Battle Pass vizual kartı — ayrıca fayl."""
import os, math as _math
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from database import (
    BP_LEVEL_REWARDS as PASS_FREE_REWARDS, BP_PREMIUM_REWARDS as PASS_PREM_REWARDS,
    BP_MAX_LEVEL, BP_PRICE_AZN, BP_SEASON_NAME, BP_SEASON_NAME_AZ
)

SEASON_LABEL = f"{BP_SEASON_NAME.upper()} ({BP_SEASON_NAME_AZ.upper()})"

BASE_DIR2 = os.path.dirname(os.path.abspath(__file__))


def _finalize(img):
    """Whole-image polish pass: 2x upscale+downscale smooths jagged shape edges, then a mild
    sharpen recovers text crispness."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(img).enhance(1.15)

PASS_BG2     = (16, 13, 26)
PASS_HEADER  = (9, 7, 18)
PASS_GOLD    = (255, 200, 50)
PASS_PURPLE  = (138, 92, 230)
PASS_TEAL    = (30, 200, 180)
PASS_FREE_BG = (22, 28, 22)
PASS_PREM_BG = (28, 18, 38)
PASS_BORDER  = (58, 48, 82)
WHITE2       = (240, 238, 230)
GRAY2        = (150, 142, 168)

PASS_MILESTONES = [5, 10, 15, 20, 25, 30, 35]

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


def _reward_color(reward):
    """reward dict-i database.py-dan gəlir (type/value/label) — 'color' açarı yoxdur,
    ona görə növünə görə uyğun rəng hesablanır."""
    rtype = reward.get("type", "coins")
    if rtype == "coins":
        return PASS_GOLD
    if rtype in ("banner", "avatar_frame"):
        return PASS_TEAL
    if rtype == "boost":
        return PASS_PURPLE
    if rtype == "elo_card":
        v = reward.get("value") or {}
        return (90, 210, 130) if v.get("card_type") == "protect" else PASS_PURPLE
    if rtype == "azn":
        return (110, 220, 140)
    if rtype == "skin":
        return (255, 220, 0)
    return WHITE2


def _reward_img(level: int, is_premium: bool, size=(130, 100)):
    w, h = size
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    reward = (PASS_PREM_REWARDS if is_premium else PASS_FREE_REWARDS).get(level)
    if not reward:
        return img
    lbl    = reward["label"]
    rtype  = reward.get("type", "coins")
    col    = _reward_color(reward)
    body_h = h - 20  # Label üçün alt boşluq

    # ── SKİN (AWM BOOM və s.) — real şəkil ────────────────────────────────────
    if rtype == "skin":
        boom = os.path.join(BASE_DIR2, "assets", "awm_boom.png")
        try:
            sk = Image.open(boom).convert("RGBA")
            sk.thumbnail((w - 4, body_h - 4), Image.LANCZOS)
            ox = (w - sk.width) // 2
            oy = (body_h - sk.height) // 2
            img.paste(sk, (ox, oy), sk)
            # Qızılı glow border
            draw.rounded_rectangle([(1,1),(w-2,body_h+2)], radius=6, outline=(255,220,0), width=2)
            draw.text((w//2, h-8), lbl[:14], font=_f(9, True), fill=(255,220,0), anchor="mm")
            return img
        except Exception:
            pass

    # ── COIN mükafatları ──────────────────────────────────────────────────────
    if rtype == "coins":
        amount = str(reward.get("value", "")).strip()
        gold   = (255, 200, 50)
        # Arxa panel
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=8,
                               fill=(40,32,8), outline=(100,80,20), width=1)
        # Real coin şəkli
        coin_path = os.path.join(BASE_DIR2, "assets", "coin.png")
        coin_loaded = False
        try:
            ci = Image.open(coin_path).convert("RGBA")
            ci_size = min(body_h - 20, w - 20)
            ci.thumbnail((ci_size, ci_size), Image.LANCZOS)
            cx_off = (w - ci.width) // 2
            cy_off = (body_h - ci.height) // 2 - 4
            img.paste(ci, (cx_off, cy_off), ci)
            coin_loaded = True
        except Exception:
            pass
        if not coin_loaded:
            cx, cy = w//2, body_h//2
            _coin_icon(draw, cx, cy-5, min(w,body_h)//3, amount, gold)
        # Miqdar
        draw.text((w//2, body_h - 6), f"x{amount}", font=_f(10, True), fill=gold, anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=gold, anchor="mm")
        return img

    # ── BANNER ────────────────────────────────────────────────────────────────
    if rtype == "banner":
        # Mini profil banner mockup içəridə
        BX, BY, BW, BH = 6, 5, w - 12, body_h - 10
        # Arxa plan: dərin teal-yaşıl gradient
        for y_ in range(BH):
            t = y_ / BH
            r_ = int(8  + (0  - 8 ) * t)
            g_ = int(55 + (90 - 55) * t)
            b_ = int(60 + (55 - 60) * t)
            draw.line([(BX, BY+y_), (BX+BW, BY+y_)], fill=(r_, g_, b_))
        draw.rounded_rectangle([(BX,BY),(BX+BW,BY+BH)], radius=5, outline=PASS_TEAL, width=2)

        # Dekorativ üfüqi scan-line cızıqlar
        for sl in range(BY+10, BY+BH-10, 12):
            draw.line([(BX+8, sl), (BX+BW-8, sl)], fill=(0, 255, 180, 30), width=1)

        # Mərkəz emblem — altıbucaqlı naxış
        cx, cy = BX + BW//2, BY + BH//2 - 8
        R = min(BW, BH) // 4
        import math as _m2
        hex_pts = [(int(cx + R*_m2.cos(_m2.radians(60*i - 30))),
                    int(cy + R*_m2.sin(_m2.radians(60*i - 30)))) for i in range(6)]
        draw.polygon(hex_pts, fill=(0, 130, 110, 180), outline=(0, 220, 180), width=2)

        # Emblem içi: "G" (Genesis) mətni
        draw.text((cx, cy), "G", font=_f(12, True), fill=(0, 255, 200), anchor="mm")

        # Üst sağ küncdə "GENESIS" badge
        draw.rectangle([(BX+BW-52, BY+4), (BX+BW-4, BY+16)], fill=(0,80,70))
        draw.text((BX+BW-28, BY+10), "GENESIS", font=_f(7, True), fill=(0,255,200), anchor="mm")

        # Aşağı band: oyunçu adı yer saxlayıcısı
        nby = BY + BH - 18
        draw.rectangle([(BX+4, nby), (BX+BW-4, BY+BH-3)], fill=(0, 30, 28, 200))
        draw.text((BX + 10, nby + 6), "[ Zenith's Academy — Genesis ]", font=_f(7, True), fill=(0,200,160), anchor="lm")

        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_TEAL, anchor="mm")
        return img

    # ── FRAME ─────────────────────────────────────────────────────────────────
    if rtype == "avatar_frame":
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6,
                               fill=(14, 10, 24), outline=PASS_PURPLE, width=2)

        cx, cy = w//2, (body_h)//2 - 2
        R = max(min(w, body_h)//2 - 10, 20)

        # Real çərçivə asseti varsa onu göstər (item.value -> market_config -> frames/*.png),
        # yoxdursa aşağıdakı çəkilmiş mockup-a keçir.
        real_loaded = False
        item_id = reward.get("value")
        if item_id:
            try:
                from market_config import get_item_by_id
                item = get_item_by_id(item_id)
                if item and item.get("file"):
                    fp = os.path.join(BASE_DIR2, "frames", item["file"])
                    fi = Image.open(fp).convert("RGBA")
                    fi_size = R * 2
                    fi.thumbnail((fi_size, fi_size), Image.LANCZOS)
                    img.paste(fi, (cx - fi.width//2, cy - fi.height//2), fi)
                    real_loaded = True
            except Exception:
                real_loaded = False

        if not real_loaded:
            # Profil çərçivəsi — dairəvi avatar mərkəzdə (fallback mockup)
            R_out = R
            R_in  = max(R_out - 8, 12)

            for rr, alpha in [(R_out+5, 40), (R_out+3, 80), (R_out+1, 140)]:
                ring = Image.new("RGBA", img.size, (0,0,0,0))
                rd = ImageDraw.Draw(ring)
                rd.ellipse([(cx-rr, cy-rr),(cx+rr, cy+rr)], outline=(*PASS_PURPLE, alpha), width=2)
                img = Image.alpha_composite(img, ring)
                draw = ImageDraw.Draw(img)

            draw.ellipse([(cx-R_out, cy-R_out),(cx+R_out, cy+R_out)],
                         fill=(28, 18, 40), outline=PASS_PURPLE, width=3)
            draw.ellipse([(cx-R_in, cy-R_in),(cx+R_in, cy+R_in)],
                         fill=(34, 22, 48))

            hr = R_in // 4
            draw.ellipse([(cx-hr, cy-R_in+4),(cx+hr, cy-R_in+4+hr*2)],
                         fill=(160, 120, 230))
            bw = int(hr * 1.8)
            draw.rounded_rectangle([(cx-bw, cy-hr+4),(cx+bw, cy+R_in-4)],
                                   radius=bw//2, fill=(130, 90, 210))

            import math as _m3
            for ang in [45, 135, 225, 315]:
                ox = int(cx + R_out * _m3.cos(_m3.radians(ang)))
                oy = int(cy + R_out * _m3.sin(_m3.radians(ang)))
                draw.ellipse([(ox-4,oy-4),(ox+4,oy+4)], fill=(200,170,255), outline=(60,30,90), width=1)

            plate_hw = max(min(26, w // 2 - 4), 10)
            draw.rectangle([(cx-plate_hw, body_h-18),(cx+plate_hw, body_h-5)], fill=(50,30,70))
            draw.text((cx, body_h-11), "FRAME", font=_f(7, True), fill=(200,170,255), anchor="mm")

        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_PURPLE, anchor="mm")
        return img

    # ── ELO BOOST ─────────────────────────────────────────────────────────────
    if rtype == "boost":
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6,
                               fill=(20,10,40), outline=PASS_PURPLE, width=2)
        boost_path = os.path.join(BASE_DIR2, "assets", "elo_boost.png")
        boost_loaded = False
        try:
            bi = Image.open(boost_path).convert("RGBA")
            bi_size = min(body_h - 20, w - 16)
            bi.thumbnail((bi_size, bi_size), Image.LANCZOS)
            bx = (w - bi.width) // 2
            by = (body_h - bi.height) // 2 - 4
            img.paste(bi, (bx, by), bi)
            boost_loaded = True
        except Exception:
            pass
        if not boost_loaded:
            lx, ly = w//2, body_h//2
            bolt = [(lx-8,ly-20),(lx+4,ly-20),(lx-4,ly),(lx+10,ly),(lx-10,ly+20),(lx+2,ly+20),(lx-4,ly),(lx-14,ly)]
            draw.polygon(bolt, fill=PASS_PURPLE)
            draw.text((w//2, body_h-10), "+10% ELO", font=_f(8, True), fill=(200,150,255), anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=PASS_PURPLE, anchor="mm")
        return img

    # ── ELO KART PAKETİ (Market ELO Kartları ilə eyni sistem — boost50/boost100/protect) ──
    if rtype == "elo_card":
        v = reward.get("value") or {}
        card_type = v.get("card_type", "boost50")
        qty = v.get("qty", 1)
        is_protect = card_type == "protect"
        panel_col = (90, 210, 130) if is_protect else PASS_PURPLE
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6,
                               fill=(10,30,20) if is_protect else (20,10,40), outline=panel_col, width=2)
        icon_cx, icon_cy = w//2, body_h//2 - 6

        # Real asset varsa göstər (boost50/boost100/protect üçün ayrı fayllar),
        # yoxdursa çəkilmiş fallback ikon.
        asset_name = {
            "boost50": "elo_boost_card.png",
            "boost100": "elo_boost100_card.png",
            "protect": "elo_protect_card.png",
        }.get(card_type, "elo_boost_card.png")
        real_loaded = False
        try:
            ei = Image.open(os.path.join(BASE_DIR2, "assets", asset_name)).convert("RGBA")
            R = min(w, body_h) // 4
            ei_size = int(R * 2.2)
            ei.thumbnail((ei_size, ei_size), Image.LANCZOS)
            img.paste(ei, (icon_cx - ei.width//2, icon_cy - ei.height//2), ei)
            real_loaded = True
        except Exception:
            real_loaded = False

        if not real_loaded and is_protect:
            # Qalxan (shield) formalı ikon — real asset yoxdur, primitiv çəkilir
            R = min(w, body_h) // 4
            shield = [
                (icon_cx, icon_cy - R), (icon_cx + R*0.8, icon_cy - R*0.5),
                (icon_cx + R*0.8, icon_cy + R*0.3), (icon_cx, icon_cy + R*1.1),
                (icon_cx - R*0.8, icon_cy + R*0.3), (icon_cx - R*0.8, icon_cy - R*0.5),
            ]
            draw.polygon(shield, fill=panel_col, outline=(230, 255, 240), width=2)
            draw.text((icon_cx, icon_cy + 2), "✓", font=_f(int(R*0.7), True), fill=(10,30,20), anchor="mm")
        elif not real_loaded:
            R = min(w, body_h) // 4
            bolt = [(icon_cx-R*0.4,icon_cy-R),(icon_cx+R*0.3,icon_cy-R),(icon_cx-R*0.2,icon_cy),
                    (icon_cx+R*0.5,icon_cy),(icon_cx-R*0.5,icon_cy+R),(icon_cx+R*0.1,icon_cy+R*0.15),
                    (icon_cx-R*0.2,icon_cy+R*0.15),(icon_cx-R*0.7,icon_cy)]
            draw.polygon(bolt, fill=panel_col, outline=(230,210,255), width=1)
        # Miqdar badge (sağ üst küncdə, aydın görünsün deyə)
        qty_txt = f"×{qty}"
        qbw = _f(11, True).getlength(qty_txt) if hasattr(_f(11, True), "getlength") else len(qty_txt)*7
        draw.rounded_rectangle([(w-14-qbw, 6), (w-4, 20)], radius=6, fill=panel_col)
        draw.text((w-9-qbw/2, 13), qty_txt, font=_f(11, True), fill=(10,10,15), anchor="mm")
        draw.text((w//2, h-8), lbl[:20], font=_f(8, True), fill=panel_col, anchor="mm")
        return img

    # ── AZN (currency) mükafatı ─────────────────────────────────────────────────
    if rtype == "azn":
        amount = reward.get("value", 0)
        green = (110, 220, 140)
        draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=8,
                               fill=(10,32,18), outline=green, width=1)
        R = min(body_h - 24, w - 24) // 2
        cx2, cy2 = w//2, body_h//2 - 4
        draw.ellipse([(cx2-R,cy2-R),(cx2+R,cy2+R)], fill=(20,60,35), outline=green, width=2)
        draw.text((cx2, cy2), "₼", font=_f(int(R*1.1), True), fill=green, anchor="mm")
        draw.text((w//2, body_h - 6), f"{amount:g} AZN", font=_f(10, True), fill=green, anchor="mm")
        draw.text((w//2, h-8), lbl, font=_f(9, True), fill=green, anchor="mm")
        return img

    # ── Fallback ──────────────────────────────────────────────────────────────
    dim = tuple(max(c//4, 0) for c in col)
    draw.rounded_rectangle([(4,4),(w-4,body_h)], radius=6, fill=dim, outline=col, width=2)
    draw.text((w//2, body_h//2), lbl[:10], font=_f(10, True), fill=WHITE2, anchor="mm")
    draw.text((w//2, h-8), lbl, font=_f(9, True), fill=col, anchor="mm")
    return img


def _draw_frame(pass_data: dict, missions: list, glow: float):
    COLS   = len(PASS_MILESTONES)
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
    claimed    = set(pass_data.get("claimed", []))
    MAX_LVL    = BP_MAX_LEVEL
    XP_NEED    = 500

    # Header
    draw.rectangle([(0, 0), (W, 62)], fill=PASS_HEADER)
    draw.line([(0, 60), (W, 60)], fill=PASS_GOLD, width=2)
    draw.text((14, 8),  "Zenith's Academy",       font=_f(11, True), fill=PASS_GOLD)
    draw.text((14, 24), SEASON_LABEL,   font=_f(18, True), fill=WHITE2)
    tier     = "VIP PASS" if is_premium else "FREE PASS"
    tier_col = PASS_PURPLE  if is_premium else (140, 140, 160)
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
        gc = int(90 + 60 * glow)
        draw.rectangle([(0, y0+FREE_H+BAR_H), (3, y0+FREE_H+BAR_H+PREM_H)], fill=(gc//2, gc//3, gc))
        draw.text((LEFT_W // 2, pl_y - 10), "VIP", font=_f(14, True), fill=PASS_PURPLE, anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 8),  "PASS", font=_f(14, True), fill=PASS_PURPLE, anchor="mm")
    else:
        draw.text((LEFT_W // 2, pl_y - 14), "VIP", font=_f(14, True), fill=(80, 60, 100), anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 4),  "PASS", font=_f(14, True), fill=(80, 60, 100), anchor="mm")
        draw.text((LEFT_W // 2, pl_y + 24), f"{BP_PRICE_AZN} AZN", font=_f(11, True), fill=PASS_PURPLE,    anchor="mm")

    # Reward cells
    for ci, lv in enumerate(PASS_MILESTONES):
        cx   = LEFT_W + ci * CELL_W
        done = lv <= level
        is_claimed = lv in claimed
        pending_claim = done and not is_claimed
        is_cur = (lv == level + 1 and lv > 0) or (level == 0 and lv == 5)

        # Free cell
        if pending_claim:
            fc = (55, 42, 8)
        elif done:
            fc = (30, 42, 30)
        else:
            fc = PASS_FREE_BG
        draw.rectangle([(cx, y0), (cx + CELL_W - 2, y0 + FREE_H)], fill=fc)
        fi = _reward_img(lv, False, (CELL_W - 16, FREE_H - 22))
        img.paste(fi, (cx + 8, y0 + 6), fi)
        if pending_claim:
            draw.text((cx + CELL_W // 2, y0 + FREE_H - 10), "TƏLƏB ET",
                      font=_f(9, True), fill=(255, 200, 50), anchor="mm")
        elif done:
            draw.text((cx + CELL_W // 2, y0 + FREE_H - 10), "ALINDI",
                      font=_f(9, True), fill=(60, 200, 60), anchor="mm")
        draw.line([(cx, y0), (cx, y0 + FREE_H)], fill=PASS_BORDER, width=1)

        # Premium cell
        prem_pending = pending_claim and is_premium
        if prem_pending:
            pc = (55, 42, 8)
        elif done and is_premium:
            pc = (42, 28, 65)
        else:
            pc = PASS_PREM_BG
        draw.rectangle([(cx, y0+FREE_H+BAR_H), (cx+CELL_W-2, y0+FREE_H+BAR_H+PREM_H)], fill=pc)
        pi_h = PREM_H - 28
        pi = _reward_img(lv, True, (CELL_W - 12, pi_h))
        img.paste(pi, (cx + 6, y0 + FREE_H + BAR_H + 6), pi)
        if prem_pending:
            draw.text((cx + CELL_W // 2, y0+FREE_H+BAR_H+8), "TƏLƏB ET",
                      font=_f(9, True), fill=(255, 200, 50), anchor="mm")
        elif done and is_premium:
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
    draw.text((14, H - FOOT_H + 8), f"Zenith's Academy  •  {BP_SEASON_NAME}", font=_f(9), fill=GRAY2)
    if not is_premium:
        draw.text((W - 14, H - FOOT_H + 8), f"\"VIP Pass Al\" düyməsi — {BP_PRICE_AZN} AZN",
                  font=_f(9, True), fill=PASS_PURPLE, anchor="rm")

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
    _finalize(img).save(output_path)
    return output_path


def generate_pass_levels_card(pass_data: dict, output_path: str):
    """1-BP_MAX_LEVEL bütün levellərin mükafat siyahısı — tək statik kart, hər sütunda
    ÜSTDƏ VIP (premium), ALTDA FREE mükafatı (istifadəçinin təsdiqlədiyi düzülüş)."""
    COLS   = 7
    ROWS   = -(-BP_MAX_LEVEL // COLS)  # ceil division
    CW     = 150
    VIP_H  = 108
    FREE_H = 86
    GAP    = 4
    PAD    = 14
    HEAD   = 64
    FOOT   = 30
    W      = PAD * 2 + COLS * CW
    BLOCK_H = 24 + VIP_H + GAP + FREE_H
    H      = HEAD + ROWS * (BLOCK_H + 10) + FOOT

    level      = pass_data.get("level", 0)
    is_premium = pass_data.get("is_premium", False)
    claimed    = set(pass_data.get("claimed", []))

    img  = Image.new("RGB", (W, H), PASS_BG2)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([(0, 0), (W, HEAD)], fill=PASS_HEADER)
    draw.line([(0, HEAD - 2), (W, HEAD - 2)], fill=PASS_PURPLE, width=2)
    draw.text((PAD, 12), "Zenith's Academy", font=_f(12, True), fill=PASS_PURPLE)
    draw.text((PAD, 30), f"{SEASON_LABEL} — BÜTÜN LEVELLƏR (1-{BP_MAX_LEVEL})", font=_f(14, True), fill=WHITE2)
    tier = "VIP PASS" if is_premium else "FREE PASS"
    tier_col = PASS_PURPLE if is_premium else GRAY2
    draw.text((W - PAD, 22), tier, font=_f(13, True), fill=tier_col, anchor="rm")
    draw.text((W - PAD, 40), f"LVL {level}/{BP_MAX_LEVEL}", font=_f(12, True), fill=WHITE2, anchor="rm")

    for row in range(ROWS):
        for col in range(COLS):
            lv = row * COLS + col + 1
            if lv > BP_MAX_LEVEL:
                break
            cx = PAD + col * CW
            cy = HEAD + row * (BLOCK_H + 10)
            done = lv <= level
            is_claimed = lv in claimed
            pending_claim = done and not is_claimed
            is_milestone = lv in PASS_MILESTONES

            # Level number strip
            lv_col = PASS_PURPLE if is_milestone else (60, 55, 80)
            draw.rectangle([(cx, cy), (cx + CW - 2, cy + 22)], fill=lv_col if done else (28, 24, 40))
            draw.text((cx + CW // 2, cy + 11), f"LVL {lv}", font=_f(9, True),
                      fill=(20, 15, 30) if done else GRAY2, anchor="mm")

            # VIP cell (TOP)
            if pending_claim and is_premium:
                vc = (55, 42, 8)
            elif done and is_premium:
                vc = (42, 28, 65)
            else:
                vc = (26, 20, 40)
            draw.rectangle([(cx, cy + 22), (cx + CW - 2, cy + 22 + VIP_H)], fill=vc)
            vi = _reward_img(lv, True, (CW - 12, VIP_H - 22))
            img.paste(vi, (cx + 6, cy + 24), vi)
            if pending_claim and is_premium:
                draw.text((cx + CW - 12, cy + 22 + 10), "!", font=_f(12, True),
                          fill=(255, 200, 50), anchor="mm")
            elif done and is_premium:
                draw.text((cx + CW - 12, cy + 22 + 10), "✓", font=_f(11, True),
                          fill=PASS_PURPLE, anchor="mm")
            draw.line([(cx, cy + 22), (cx + CW - 2, cy + 22)], fill=PASS_BORDER, width=1)

            # Divider between VIP and FREE
            div_y = cy + 22 + VIP_H
            draw.line([(cx, div_y), (cx + CW - 2, div_y)], fill=PASS_BORDER, width=2)

            # FREE cell (BOTTOM)
            if pending_claim:
                fc = (55, 42, 8)
            elif done:
                fc = (26, 34, 26)
            else:
                fc = (20, 24, 20)
            draw.rectangle([(cx, div_y + GAP), (cx + CW - 2, div_y + GAP + FREE_H)], fill=fc)
            fi = _reward_img(lv, False, (CW - 14, FREE_H - 20))
            img.paste(fi, (cx + 7, div_y + GAP + 2), fi)
            if pending_claim:
                draw.text((cx + CW - 12, div_y + GAP + 10), "!", font=_f(11, True),
                          fill=(255, 200, 50), anchor="mm")
            elif done:
                draw.text((cx + CW - 12, div_y + GAP + 10), "✓", font=_f(10, True),
                          fill=(90, 210, 110), anchor="mm")

            draw.line([(cx, cy), (cx, div_y + GAP + FREE_H)], fill=PASS_BORDER, width=1)

            if is_milestone:
                draw.rectangle([(cx, cy), (cx + CW - 2, div_y + GAP + FREE_H)],
                                outline=PASS_PURPLE, width=2)

    draw.rectangle([(0, H - FOOT), (W, H)], fill=PASS_HEADER)
    draw.text((PAD, H - FOOT + 6),
              f"Zenith's Academy {BP_SEASON_NAME} Pass  •  \"VIP Pass Al\" — {BP_PRICE_AZN} AZN  •  "
              "! = tələb edilməli, ✓ = artıq tələb edilib",
              font=_f(9), fill=GRAY2)
    draw.text((W - PAD, H - FOOT + 6), "ÜSTDƏ VIP  •  ALTDA FREE",
              font=_f(9, True), fill=PASS_PURPLE, anchor="ra")

    _finalize(img).save(output_path)
    return output_path


_MISSION_CAT_LABELS = {"daily": "GÜNLÜK", "weekly": "HƏFTƏLİK", "seasonal": "SEZONLUQ"}
_MISSION_CAT_COLORS = {"daily": GRAY2, "weekly": PASS_TEAL, "seasonal": PASS_GOLD}


def generate_pass_missions_card(missions: list, output_path: str):
    """Bütün aktiv missiyaları (günlük/həftəlik/sezonluq) qruplaşdırılmış şəkildə göstərir —
    /pass panelindəki 3-slotlu qısa önizləmədən fərqli olaraq HAMISINI göstərir."""
    PAD  = 16
    HEAD = 58
    FOOT = 26
    ROW_H = 46
    SEC_GAP = 30

    groups = {"daily": [], "weekly": [], "seasonal": []}
    for m in missions:
        groups.setdefault(m["cat"], []).append(m)

    W = 620
    H = HEAD + FOOT
    for cat in ("daily", "weekly", "seasonal"):
        if groups[cat]:
            H += SEC_GAP + len(groups[cat]) * ROW_H

    img  = Image.new("RGB", (W, H), PASS_BG2)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, HEAD)], fill=PASS_HEADER)
    draw.line([(0, HEAD - 2), (W, HEAD - 2)], fill=PASS_PURPLE, width=2)
    draw.text((PAD, 12), "Zenith's Academy", font=_f(12, True), fill=PASS_PURPLE)
    draw.text((PAD, 30), f"{SEASON_LABEL} — MİSSİYALAR", font=_f(14, True), fill=WHITE2)

    y = HEAD + 12
    for cat in ("daily", "weekly", "seasonal"):
        rows = groups[cat]
        if not rows:
            continue
        cat_col = _MISSION_CAT_COLORS[cat]
        draw.text((PAD, y), _MISSION_CAT_LABELS[cat], font=_f(11, True), fill=cat_col)
        draw.line([(PAD + 90, y + 7), (W - PAD, y + 7)], fill=PASS_BORDER, width=1)
        y += 22
        for m in rows:
            done = m["completed"]
            row_bg = (22, 32, 24) if done else (22, 19, 32)
            draw.rounded_rectangle([(PAD, y), (W - PAD, y + ROW_H - 8)], radius=6,
                                   fill=row_bg, outline=(cat_col if not done else (70, 200, 100)), width=1)
            draw.text((PAD + 12, y + 9), m["desc"], font=_f(11, True), fill=WHITE2)

            pct = min(m["progress"] / m["target"], 1.0) if m["target"] else 1.0
            bar_x, bar_y, bar_w, bar_h = PAD + 12, y + 26, 220, 6
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=3, fill=(40, 36, 55))
            if pct > 0:
                draw.rounded_rectangle([(bar_x, bar_y), (bar_x + int(bar_w * pct), bar_y + bar_h)],
                                       radius=3, fill=(90, 210, 110) if done else cat_col)
            draw.text((bar_x + bar_w + 10, bar_y + bar_h // 2), f"{m['progress']}/{m['target']}",
                      font=_f(9), fill=GRAY2, anchor="lm")

            xp_txt = "TAMAMLANDI" if done else f"+{m['xp']} XP"
            xp_col = (90, 210, 110) if done else PASS_GOLD
            draw.text((W - PAD - 12, y + (ROW_H - 8) // 2), xp_txt, font=_f(10, True), fill=xp_col, anchor="rm")
            y += ROW_H
        y += SEC_GAP - 22

    draw.rectangle([(0, H - FOOT), (W, H)], fill=PASS_HEADER)
    draw.text((PAD, H - FOOT + 6), f"Zenith's Academy {BP_SEASON_NAME} Pass",
              font=_f(9), fill=GRAY2)
    draw.text((W - PAD, H - FOOT + 6), "Günlük 00:00 UTC-də, həftəlik həftə başında yenilənir",
              font=_f(9), fill=GRAY2, anchor="ra")

    _finalize(img).save(output_path)
    return output_path


def generate_pass_announcement(output_path: str):
    """Genesis (Yaranış) Battle Pass tanıtım elan kartı — kanal elanı üçün."""
    W, H = 900, 580
    img  = Image.new("RGBA", (W, H), (0,0,0,255))
    draw = ImageDraw.Draw(img)

    # ── Fon gradient (tünd göy-bənövşəyi) ────────────────────────────────────
    for y in range(H):
        t  = y / H
        r_ = int(12 + (20-12)*t)
        g_ = int(10 + (8 -10)*t)
        b_ = int(28 + (18-28)*t)
        draw.line([(0,y),(W,y)], fill=(r_,g_,b_))

    # Çəpinə işıq şüası (dekor)
    import math as _ma
    ray = Image.new("RGBA", (W,H), (0,0,0,0))
    rd  = ImageDraw.Draw(ray)
    for rx in range(0, W+400, 18):
        rd.polygon([(rx,0),(rx+280,0),(rx+280-H,H),(rx-H,H)],
                   fill=(255,200,80,6))
    img = Image.alpha_composite(img, ray)
    draw = ImageDraw.Draw(img)

    # ── Sol üst logo şeridi ───────────────────────────────────────────────────
    draw.rectangle([(0,0),(W,5)], fill=PASS_PURPLE)
    draw.text((28,14), "Zenith's Academy  •  FACEIT  •  STANDOFF 2", font=_f(10,True), fill=PASS_PURPLE)

    # ── Mərkəz başlıq ─────────────────────────────────────────────────────────
    draw.text((W//2, 52),  "BATTLE PASS",  font=_f(52,True), fill=WHITE2, anchor="mm")
    draw.text((W//2, 100), "G E N E S I S",  font=_f(20,True), fill=PASS_PURPLE,  anchor="mm")
    draw.text((W//2, 122), f"( {BP_SEASON_NAME_AZ} )",  font=_f(13,True), fill=PASS_TEAL,  anchor="mm")

    # Başlıq altı xətt
    draw.line([(60,138),(W-60,138)], fill=PASS_BORDER, width=1)

    # ── 3 əsas mükafat kartı ─────────────────────────────────────────────────
    CARD_W, CARD_H = 220, 200
    cards = [
        (5,  False, "LVL 5 — FREE",   "50% Boost Kartı",   PASS_TEAL),
        (15, True,  "LVL 15 — VIP",   "Genesis Çərçivəsi", PASS_TEAL),
        (35, True,  "LVL 35 — VIP",   "AWM BOOM SKIN",     PASS_GOLD),
    ]
    total_cards = len(cards)
    spacing = (W - total_cards * CARD_W) // (total_cards + 1)
    cy0 = 152

    for ci, (lv, prem, badge, name, col) in enumerate(cards):
        cx0 = spacing + ci * (CARD_W + spacing)

        # Kart fon
        glow_c = (*col[:3], 60)
        card_bg = (25, 18, 40) if prem else (18, 28, 25)
        draw.rounded_rectangle([(cx0,cy0),(cx0+CARD_W,cy0+CARD_H)],
                               radius=8, fill=card_bg, outline=col, width=2)

        # Badge şerid
        draw.rounded_rectangle([(cx0+6,cy0+6),(cx0+CARD_W-6,cy0+24)],
                               radius=4, fill=col)
        draw.text((cx0+CARD_W//2, cy0+15), badge, font=_f(9,True),
                  fill=(20,15,10) if col==PASS_GOLD else (10,30,28), anchor="mm")

        # Mükafat ikonu (_reward_img öz içində adını da çəkir, təkrar yazmırıq)
        icon_size = (CARD_W-24, CARD_H-46)
        icon = _reward_img(lv, prem, icon_size)
        img.paste(icon, (cx0+12, cy0+30), icon)

    # ── Free vs VIP müqayisə paneli ───────────────────────────────────────────
    PY = cy0 + CARD_H + 20
    PH = 90
    PX = 40
    PW = (W - PX*2 - 20) // 2

    # FREE panel
    draw.rounded_rectangle([(PX, PY),(PX+PW, PY+PH)],
                           radius=6, fill=(14,28,20), outline=PASS_TEAL, width=2)
    draw.text((PX+PW//2, PY+12), "FREE PASS", font=_f(13,True), fill=PASS_TEAL, anchor="mm")
    for ri, row in enumerate(["Hər leveldə coin mükafatı",
                               "Milestone-larda (5-35) ELO kartları"]):
        draw.text((PX+14, PY+28+ri*16), f"• {row}", font=_f(9), fill=WHITE2)

    # VIP panel
    VX = PX + PW + 20
    draw.rounded_rectangle([(VX, PY),(VX+PW, PY+PH)],
                           radius=6, fill=(28,18,42), outline=PASS_PURPLE, width=2)
    draw.text((VX+PW//2, PY+12), f"VIP PASS — {BP_PRICE_AZN} AZN", font=_f(13,True), fill=PASS_PURPLE, anchor="mm")
    for ri, row in enumerate(["Bütün FREE + AZN/Coin/ELO kart bonusu",
                               f"Çərçivə(15) · Banner(20) · AWM Boom(Lv.{BP_MAX_LEVEL})"]):
        draw.text((VX+14, PY+28+ri*16), f"• {row}", font=_f(9), fill=WHITE2)

    # ── Alt CTA şeridi ────────────────────────────────────────────────────────
    FY = H - 46
    draw.rectangle([(0,FY),(W,H)], fill=(8,6,14))
    draw.line([(0,FY),(W,FY)], fill=PASS_PURPLE, width=2)
    draw.text((W//2, FY+23),
              "/pass  →  Battle Pass-ınızı açın",
              font=_f(16,True), fill=WHITE2, anchor="mm")

    img = img.convert("RGB")
    _finalize(img).save(output_path)
    return output_path
