"""Referral (Dəvət) sistemi vizual kartı — PIL."""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_TOP  = (12, 10, 20)
BG_BOT  = (8, 6, 14)
PANEL   = (22, 20, 32)
PANEL2  = (30, 26, 44)
BORDER  = (55, 48, 75)
GOLD    = (240, 185, 40)
WHITE   = (244, 241, 234)
GRAY    = (130, 125, 148)
GREEN   = (88, 210, 110)
RED     = (200, 60, 55)
PURPLE  = (160, 90, 255)
TEAL    = (40, 200, 180)

FONT_B = [os.path.join(BASE_DIR,"fonts","DejaVuSans-Bold.ttf"),
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "C:/Windows/Fonts/arialbd.ttf"]
FONT_R = [os.path.join(BASE_DIR,"fonts","DejaVuSans.ttf"),
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
        c = tuple(int(BG_TOP[i] + (BG_BOT[i]-BG_TOP[i])*t) for i in range(3))
        d.line([(0,y),(w,y)], fill=c)
    return img


def _progress_bar(draw, x, y, w, h, pct, color, bg=(30,26,44)):
    draw.rounded_rectangle([(x,y),(x+w,y+h)], radius=h//2, fill=bg)
    if pct > 0:
        fw = max(h, int(w * min(pct, 1.0)))
        draw.rounded_rectangle([(x,y),(x+fw,y+h)], radius=h//2, fill=color)


def generate_referral_stats_card(nick: str, stats: dict,
                                  referrals: list, invite_url: str,
                                  output_path: str) -> str:
    """
    stats: {total, registered, milestone_3, milestone_10}
    referrals: [{nick, matches, registered, r3, r10, joined_at}]
    """
    ROW_H  = 48
    HEAD_H = 110
    STAT_H = 140
    SEC_H  = 30
    FOOT_H = 36
    W      = 820
    n      = max(1, len(referrals))
    H      = HEAD_H + STAT_H + SEC_H + n * ROW_H + FOOT_H

    img  = _grad(W, H)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rectangle([(0,0),(W,HEAD_H)], fill=(14,10,26))
    draw.line([(0,HEAD_H),(W,HEAD_H)], fill=GOLD, width=2)
    draw.text((28, 14), "CALESTIFY  •  DAVET SİSTEMİ", font=_f(11,True), fill=GOLD)
    draw.text((28, 36), f"{nick}", font=_f(26,True), fill=WHITE)
    draw.text((28, 72), "Şəxsi dəvət linkiniz:", font=_f(11), fill=GRAY)
    draw.text((28, 88), invite_url[:60], font=_f(12,True), fill=TEAL)

    # ── İstatistika paneli ────────────────────────────────────────────────────
    sy   = HEAD_H + 10
    sw   = (W - 56) // 4
    vals = [
        ("Dəvət edildi", stats["total"],       WHITE,  "👥"),
        ("Qeydiyyat",    stats["registered"],  GREEN,  "✅"),
        ("3 Matç",       stats["milestone_3"], GOLD,   "🔥"),
        ("10 Matç",      stats["milestone_10"],PURPLE, "🏅"),
    ]
    for i, (lbl, val, col, icon) in enumerate(vals):
        bx = 28 + i * (sw + 4)
        draw.rounded_rectangle([(bx, sy),(bx+sw, sy+STAT_H-20)],
                               radius=6, fill=PANEL, outline=BORDER, width=1)
        draw.text((bx+sw//2, sy+20), icon,     font=_f(22),      fill=col, anchor="mm")
        draw.text((bx+sw//2, sy+54), str(val), font=_f(30,True), fill=col, anchor="mm")
        draw.text((bx+sw//2, sy+88), lbl,      font=_f(10,True), fill=GRAY,anchor="mm")

    # Mükafat xülasəsi
    reward_y = sy + STAT_H - 12
    coins_earned = stats["registered"]*200 + stats["milestone_3"]*500
    draw.text((28, reward_y), f"💰 Qazanılan: {coins_earned} coin", font=_f(11,True), fill=GOLD)
    if stats["milestone_10"]:
        draw.text((W-28, reward_y), "🏅 Ambassador banner alındı!", font=_f(11,True), fill=PURPLE, anchor="rm")

    # ── Sütun başlıqları ──────────────────────────────────────────────────────
    sh_y = HEAD_H + STAT_H + 4
    draw.rectangle([(0,sh_y),(W,sh_y+SEC_H)], fill=PANEL2)
    draw.text((28, sh_y+SEC_H//2), "Dəvət olunan oyunçu", font=_f(10,True), fill=GOLD, anchor="lm")
    for xi, lbl in [(380,"Matç"),(460,"Qeydiyyat"),(560,"3 Matç"),(660,"10 Matç")]:
        draw.text((xi, sh_y+SEC_H//2), lbl, font=_f(10,True), fill=GRAY, anchor="mm")

    # ── Oyunçu sıraları ───────────────────────────────────────────────────────
    ry = sh_y + SEC_H
    if not referrals:
        draw.text((28, ry+18), "Hələ heç kimi dəvət etməmisiniz.", font=_f(13), fill=GRAY)
    else:
        for i, r in enumerate(referrals[:20]):
            if i % 2 == 0:
                draw.rectangle([(2,ry),(W-2,ry+ROW_H-1)], fill=(20,18,30))
            draw.text((28, ry+ROW_H//2), r["nick"][:22], font=_f(14,True), fill=WHITE, anchor="lm")

            # Matç sayı + progress bar (0→3→10)
            m = r["matches"]
            draw.text((380, ry+ROW_H//2), str(m), font=_f(14,True), fill=TEAL, anchor="mm")
            # Progress bar (max 10)
            _progress_bar(draw, 400, ry+ROW_H//2-4, 150, 8, m/10, GOLD)

            for xi, val, col in [
                (460, "✅" if r["registered"] else "—", GREEN if r["registered"] else GRAY),
                (560, "✅" if r["r3"]        else "—", GOLD  if r["r3"]        else GRAY),
                (660, "🏅" if r["r10"]       else "—", PURPLE if r["r10"]       else GRAY),
            ]:
                draw.text((xi, ry+ROW_H//2), val, font=_f(13,True), fill=col, anchor="mm")
            draw.line([(18,ry+ROW_H-1),(W-18,ry+ROW_H-1)], fill=BORDER, width=1)
            ry += ROW_H

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = H - FOOT_H
    draw.rectangle([(0,fy),(W,H)], fill=(10,8,18))
    draw.text((28, fy+FOOT_H//2),
              "200 coin (qeydiyyat)  •  500 coin (3 matç)  •  Ambassador banner (10 matç)",
              font=_f(11), fill=GRAY, anchor="lm")

    img.save(output_path)
    return output_path
