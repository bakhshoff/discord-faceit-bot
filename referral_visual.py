"""Referral (Dəvət) sistemi vizual kartı — PIL."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_TOP  = (12, 10, 20)
BG_BOT  = (8,  6, 14)
PANEL   = (22, 20, 32)
PANEL2  = (30, 26, 44)
BORDER  = (55, 48, 75)
GOLD    = (240, 185, 40)
WHITE   = (244, 241, 234)
GRAY    = (130, 125, 148)
GREEN   = (88,  210, 110)
RED     = (200, 60,  55)
PURPLE  = (160, 90,  255)
TEAL    = (40,  200, 180)

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


def _grad(w, h):
    img = Image.new("RGB", (w, h), BG_TOP)
    d   = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def _progress_bar(draw, x, y, w, h, pct, color, bg=(30, 26, 44)):
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=h//2, fill=bg)
    if pct > 0:
        fw = max(h, int(w * min(pct, 1.0)))
        draw.rounded_rectangle([(x, y), (x+fw, y+h)], radius=h//2, fill=color)


def _load_preview(path: str, w: int, h: int):
    """Şəkil yükləyib ölçüsünü dəyişir. Xəta olsa None qaytarır."""
    try:
        img = Image.open(path).convert("RGB")
        img = ImageOps.fit(img, (w, h), Image.LANCZOS)
        return img
    except Exception:
        return None


def generate_referral_stats_card(nick: str, stats: dict,
                                  referrals: list, invite_url: str,
                                  output_path: str) -> str:
    """
    stats:    {total, registered, milestone_3, milestone_10}
    referrals:[{nick, matches, registered, r3, r10, joined_at}]
    """
    ROW_H   = 48
    HEAD_H  = 110
    STAT_H  = 130
    PRIZE_H = 190      # Mükafat önizləmə bölməsi
    SEC_H   = 30
    FOOT_H  = 36
    W       = 920
    n       = max(1, len(referrals))
    H       = HEAD_H + STAT_H + PRIZE_H + SEC_H + n * ROW_H + FOOT_H

    img  = _grad(W, H)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W-1, H-1)], outline=BORDER, width=2)

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (W, HEAD_H)], fill=(14, 10, 26))
    draw.line([(0, HEAD_H), (W, HEAD_H)], fill=GOLD, width=2)
    draw.text((28, 14), "CALESTIFY  •  DAVET SİSTEMİ", font=_f(11, True), fill=GOLD)
    draw.text((28, 36), f"{nick}", font=_f(26, True), fill=WHITE)
    draw.text((28, 72), "Şəxsi dəvət linkiniz:", font=_f(11), fill=GRAY)
    # Link (kopyalana bilər, aydın görsənsin)
    link_bg_w = min(W - 56, len(invite_url) * 8 + 24)
    draw.rounded_rectangle([(28, 87), (28 + link_bg_w, 107)], radius=4, fill=(28, 22, 44), outline=TEAL, width=1)
    draw.text((36, 97), invite_url[:60], font=_f(12, True), fill=TEAL, anchor="lm")

    # ── Statistika 4 qutu ─────────────────────────────────────────────────────
    sy  = HEAD_H + 10
    sw  = (W - 56) // 4
    vals = [
        ("Dəvət edildi", stats["total"],        WHITE,  "👥"),
        ("Qeydiyyat",    stats["registered"],   GREEN,  "✅"),
        ("3 Matç",       stats["milestone_3"],  GOLD,   "🔥"),
        ("10 Matç",      stats["milestone_10"], PURPLE, "🏅"),
    ]
    for i, (lbl, val, col, icon) in enumerate(vals):
        bx = 28 + i * (sw + 4)
        draw.rounded_rectangle([(bx, sy), (bx+sw, sy+STAT_H-16)],
                               radius=6, fill=PANEL, outline=BORDER, width=1)
        draw.text((bx+sw//2, sy+18),  icon,     font=_f(22),       fill=col, anchor="mm")
        draw.text((bx+sw//2, sy+52),  str(val), font=_f(30, True), fill=col, anchor="mm")
        draw.text((bx+sw//2, sy+86),  lbl,      font=_f(10, True), fill=GRAY, anchor="mm")

    coins_earned = stats["registered"] * 200 + stats["milestone_3"] * 500
    rew_y = sy + STAT_H - 8
    draw.text((28, rew_y), f"💰 Qazanılan: {coins_earned} coin", font=_f(11, True), fill=GOLD)
    if stats["milestone_10"]:
        draw.text((W-28, rew_y), "🏅 Ambassador banner alındı!", font=_f(11, True), fill=PURPLE, anchor="rm")

    # ── Mükafat önizləmə bölməsi ──────────────────────────────────────────────
    py = HEAD_H + STAT_H + 4
    draw.rectangle([(0, py), (W, py + PRIZE_H)], fill=(16, 12, 28))
    draw.line([(0, py), (W, py)], fill=BORDER, width=1)
    draw.line([(0, py+PRIZE_H), (W, py+PRIZE_H)], fill=BORDER, width=1)
    draw.text((28, py+12), "MÜKAFAT ÖNİZLƏMƏLƏRİ", font=_f(11, True), fill=GOLD)

    PREV_W, PREV_H = 200, 130

    # 1) 200 coin panel
    _draw_prize_tile(draw, img, 28, py+34, PREV_W, PREV_H,
                     "✅  Qeydiyyat", "+200 Coin", None, GOLD, GREEN)

    # 2) 500 coin panel
    _draw_prize_tile(draw, img, 28 + PREV_W + 18, py+34, PREV_W, PREV_H,
                     "🔥  3 Matç", "+500 Coin", None, GOLD, (255, 140, 40))

    # 3) Ambassador banner önizləmə
    banner_path = os.path.join(BASE_DIR, "banners", "banner_ambassador.png")
    banner_prev = _load_preview(banner_path, PREV_W, PREV_H)
    _draw_prize_tile(draw, img, 28 + (PREV_W + 18)*2, py+34, PREV_W, PREV_H,
                     "🏅  10 Matç", "Ambassador Banner", banner_prev, PURPLE, PURPLE)

    # 4) Məlumat mətni
    tx = 28 + (PREV_W + 18) * 3
    draw.text((tx, py+40), "Calestify Ambassador", font=_f(13, True), fill=PURPLE)
    draw.text((tx, py+62), "banneri yalnız bu", font=_f(11), fill=GRAY)
    draw.text((tx, py+78), "yolla əldə edilir —", font=_f(11), fill=GRAY)
    draw.text((tx, py+94), "marketdə satılmır.", font=_f(11), fill=GRAY)
    draw.rounded_rectangle([(tx, py+112), (tx+180, py+134)],
                           radius=4, fill=(40, 20, 60), outline=PURPLE, width=1)
    draw.text((tx+90, py+123), "XÜSUSİ  •  NADIR", font=_f(9, True), fill=PURPLE, anchor="mm")

    # ── Sütun başlıqları ──────────────────────────────────────────────────────
    sh_y = py + PRIZE_H
    draw.rectangle([(0, sh_y), (W, sh_y+SEC_H)], fill=PANEL2)
    draw.text((28, sh_y+SEC_H//2), "Dəvət olunan oyunçu", font=_f(10, True), fill=GOLD, anchor="lm")
    for xi, lbl in [(400, "Matç"), (490, "Qeydiyyat"), (600, "3 Matç"), (710, "10 Matç")]:
        draw.text((xi, sh_y+SEC_H//2), lbl, font=_f(10, True), fill=GRAY, anchor="mm")

    # ── Oyunçu sıraları ───────────────────────────────────────────────────────
    ry = sh_y + SEC_H
    if not referrals:
        draw.text((28, ry+18), "Hələ heç kimi dəvət etməmisiniz.", font=_f(13), fill=GRAY)
    else:
        for i, r in enumerate(referrals[:20]):
            if i % 2 == 0:
                draw.rectangle([(2, ry), (W-2, ry+ROW_H-1)], fill=(20, 18, 30))
            draw.text((28, ry+ROW_H//2), r["nick"][:24], font=_f(14, True), fill=WHITE, anchor="lm")
            m = r["matches"]
            draw.text((400, ry+ROW_H//2), str(m), font=_f(14, True), fill=TEAL, anchor="mm")
            _progress_bar(draw, 420, ry+ROW_H//2-4, 140, 8, m/10, GOLD)
            for xi, val, col in [
                (490, "✅" if r["registered"] else "—", GREEN  if r["registered"] else GRAY),
                (600, "✅" if r["r3"]         else "—", GOLD   if r["r3"]         else GRAY),
                (710, "🏅" if r["r10"]        else "—", PURPLE if r["r10"]        else GRAY),
            ]:
                draw.text((xi, ry+ROW_H//2), val, font=_f(13, True), fill=col, anchor="mm")
            draw.line([(18, ry+ROW_H-1), (W-18, ry+ROW_H-1)], fill=BORDER, width=1)
            ry += ROW_H

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = H - FOOT_H
    draw.rectangle([(0, fy), (W, H)], fill=(10, 8, 18))
    draw.text((28, fy+FOOT_H//2),
              "200 coin (qeydiyyat)  •  500 coin (3 matç)  •  Ambassador banner (10 matç)",
              font=_f(11), fill=GRAY, anchor="lm")

    img.save(output_path)
    return output_path


def _draw_prize_tile(draw, img, x, y, w, h,
                     title, subtitle, preview_img, border_col, text_col):
    """Mükafat önizləmə kadrı çəkir."""
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=6,
                           fill=(18, 14, 30), outline=border_col, width=2)
    if preview_img:
        # Şəkil var — alt yarıya yapışdır
        ph = h - 40
        pimg = preview_img.resize((w-8, ph), Image.LANCZOS)
        img.paste(pimg, (x+4, y+4))
        # Başlıq şeridi altta
        draw.rectangle([(x, y+h-36), (x+w, y+h)], fill=(12, 8, 24, 200))
        draw.text((x+w//2, y+h-18), title, font=_f(10, True), fill=border_col, anchor="mm")
    else:
        # Şəkil yox — mərkəzdə mətn
        draw.text((x+w//2, y+30), title,    font=_f(11, True), fill=GRAY,     anchor="mm")
        draw.text((x+w//2, y+64), subtitle, font=_f(18, True), fill=text_col, anchor="mm")
        draw.text((x+w//2, y+h-16), "MÜKAFAT", font=_f(9, True), fill=border_col, anchor="mm")
