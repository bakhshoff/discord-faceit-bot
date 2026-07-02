"""Referral (Dəvət) sistemi vizual kartı — PIL. Tam yenilənmiş dizayn."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG      = (10, 8, 18)
PANEL   = (20, 18, 30)
PANEL2  = (28, 24, 42)
BORDER  = (52, 46, 72)
GOLD    = (240, 185, 40)
WHITE   = (244, 241, 234)
GRAY    = (120, 115, 138)
GREEN   = (72, 200, 100)
PURPLE  = (155, 85, 255)
TEAL    = (35, 195, 175)
ORANGE  = (255, 140, 40)

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


def _vgrad(img, y0, y1, c1, c2):
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        t = (y - y0) / max(y1 - y0, 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        d.line([(0, y), (img.width, y)], fill=c)


def _load_img(path, w, h):
    try:
        im = Image.open(path).convert("RGB")
        return ImageOps.fit(im, (w, h), Image.LANCZOS)
    except Exception:
        return None


def _bar(draw, x, y, w, h, pct, col, bg=(28, 24, 42)):
    draw.rounded_rectangle([(x, y), (x+w, y+h)], radius=h//2, fill=bg)
    if pct > 0:
        fw = max(h, int(w * min(pct, 1.0)))
        draw.rounded_rectangle([(x, y), (x+fw, y+h)], radius=h//2, fill=col)


# ── ANA KART — tam panel ───────────────────────────────────────────────────────

def generate_referral_card(nick: str, stats: dict, referrals: list,
                            invite_url: str, output_path: str) -> str:
    """
    Bütün məlumatları bir kartda: link, statistika, mükafat roadmap, cədvəl.
    stats:     {total, registered, milestone_3, milestone_10}
    referrals: [{nick, matches, registered, r3, r10}]
    """
    W = 880

    # Dinamik hündürlük
    REF_ROWS = max(1, min(len(referrals), 12))
    HEAD_H   = 90
    LINK_H   = 60
    STAT_H   = 110
    ROAD_H   = 160
    LIST_H   = 34 + REF_ROWS * 44 + 10
    FOOT_H   = 30
    H = HEAD_H + LINK_H + STAT_H + ROAD_H + LIST_H + FOOT_H

    img = Image.new("RGB", (W, H), BG)
    _vgrad(img, 0, H, (14, 10, 24), (8, 6, 16))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W-1, H-1)], outline=BORDER, width=2)

    y = 0

    # ── HEADER ────────────────────────────────────────────────────────────────
    _vgrad(img, 0, HEAD_H, (22, 14, 40), (14, 10, 26))
    draw.line([(0, HEAD_H), (W, HEAD_H)], fill=GOLD, width=2)
    draw.text((28, 18), "CALESTIFY  ·  DAVET SİSTEMİ", font=_f(11, True), fill=GOLD)
    draw.text((28, 40), nick[:24], font=_f(28, True), fill=WHITE)
    coins_earned = stats["registered"] * 200 + stats["milestone_3"] * 500
    draw.text((W-28, 50), f"💰 {coins_earned} coin qazanıldı", font=_f(12, True), fill=GOLD, anchor="rm")
    y = HEAD_H

    # ── DAVET LİNKİ ───────────────────────────────────────────────────────────
    draw.rectangle([(0, y), (W, y+LINK_H)], fill=(18, 14, 32))
    draw.line([(0, y+LINK_H), (W, y+LINK_H)], fill=BORDER, width=1)
    # Link kutusu
    lx1, lx2 = 28, W-28
    draw.rounded_rectangle([(lx1, y+10), (lx2, y+LINK_H-10)],
                           radius=6, fill=(26, 20, 44), outline=TEAL, width=2)
    draw.text((lx1+14, y+LINK_H//2), "🔗", font=_f(16), fill=TEAL, anchor="lm")
    draw.text((lx1+40, y+LINK_H//2), invite_url[:70], font=_f(13, True), fill=TEAL, anchor="lm")
    draw.text((lx2-14, y+LINK_H//2), "⬆ Kopyala", font=_f(10), fill=GRAY, anchor="rm")
    y += LINK_H

    # ── 4 STATİSTİKA QUTU ─────────────────────────────────────────────────────
    pad = 16
    sw  = (W - pad*2 - 3*8) // 4
    sy  = y + 10
    boxes = [
        ("Dəvət",      stats["total"],        TEAL,   "👥"),
        ("Qeydiyyat",  stats["registered"],   GREEN,  "✅"),
        ("3 Matç",     stats["milestone_3"],  ORANGE, "🔥"),
        ("10 Matç",    stats["milestone_10"], PURPLE, "🏅"),
    ]
    for i, (lbl, val, col, ico) in enumerate(boxes):
        bx = pad + i*(sw+8)
        draw.rounded_rectangle([(bx, sy), (bx+sw, sy+STAT_H-20)],
                               radius=8, fill=PANEL, outline=col, width=2)
        draw.text((bx+sw//2, sy+18), ico,     font=_f(18),       fill=col,  anchor="mm")
        draw.text((bx+sw//2, sy+50), str(val),font=_f(28, True), fill=col,  anchor="mm")
        draw.text((bx+sw//2, sy+80), lbl,     font=_f(10, True), fill=GRAY, anchor="mm")
    y += STAT_H

    # ── MÜKAFAT ROADMAP ───────────────────────────────────────────────────────
    draw.line([(0, y), (W, y)], fill=BORDER, width=1)
    draw.text((28, y+10), "MÜKAFAT ROADMAP", font=_f(11, True), fill=GOLD)
    ry = y + 32

    # 3 milestone tile
    TILE_W = (W - 56 - 32) // 3
    TILE_H = ROAD_H - 44
    milestones = [
        (1,  "Qeydiyyat",    "+200 Coin",  None,               GREEN,  stats["registered"] > 0),
        (3,  "3 Matç",       "+500 Coin",  None,               ORANGE, stats["milestone_3"] > 0),
        (10, "10 Matç",      "Ambassador", "banner_ambassador", PURPLE, stats["milestone_10"] > 0),
    ]
    for mi, (req, title, reward, banner_id, col, earned) in enumerate(milestones):
        tx = 28 + mi * (TILE_W + 16)
        bg_fill = (20, 28, 20) if earned else PANEL
        bdr     = col if earned else BORDER
        draw.rounded_rectangle([(tx, ry), (tx+TILE_W, ry+TILE_H)],
                               radius=8, fill=bg_fill, outline=bdr, width=2)

        if banner_id:
            bpath = os.path.join(BASE_DIR, "banners", f"{banner_id}.png")
            bimg  = _load_img(bpath, TILE_W-8, TILE_H-36)
            if bimg:
                img.paste(bimg, (tx+4, ry+4))
                draw.rectangle([(tx, ry+TILE_H-32), (tx+TILE_W, ry+TILE_H)], fill=(12, 8, 24))
        else:
            draw.text((tx+TILE_W//2, ry+TILE_H//2-10), reward,
                      font=_f(20, True), fill=col, anchor="mm")

        draw.text((tx+TILE_W//2, ry+TILE_H-20), f"{'✅ ' if earned else ''}{title}",
                  font=_f(11, True), fill=col if earned else GRAY, anchor="mm")

        # Milestone badge
        draw.ellipse([(tx+TILE_W//2-16, ry-14), (tx+TILE_W//2+16, ry+14)],
                     fill=col if earned else (40, 36, 56), outline=col, width=2)
        draw.text((tx+TILE_W//2, ry), str(req), font=_f(11, True),
                  fill=WHITE if earned else GRAY, anchor="mm")

        # Connector arrow (sonuncu tile-dan sonra yoxdur)
        if mi < 2:
            ax = tx + TILE_W + 8
            draw.text((ax, ry+TILE_H//2), "→", font=_f(16, True), fill=BORDER, anchor="mm")

    y += ROAD_H

    # ── DAVET EDİLƏNLƏR CƏDVƏLİ ──────────────────────────────────────────────
    draw.line([(0, y), (W, y)], fill=BORDER, width=1)
    draw.rectangle([(0, y), (W, y+34)], fill=PANEL2)
    draw.text((28, y+17), "Dəvət edilənlər", font=_f(11, True), fill=GOLD, anchor="lm")
    for cx, lbl in [(420, "Matç"), (510, "Qeydiyyat"), (620, "3 Matç"), (730, "10 Matç")]:
        draw.text((cx, y+17), lbl, font=_f(10, True), fill=GRAY, anchor="mm")
    y += 34

    if not referrals:
        draw.text((28, y+22), "Hələ heç kimi dəvət etməmisiniz.", font=_f(13), fill=GRAY)
        y += 44
    else:
        for i, r in enumerate(referrals[:12]):
            if i % 2 == 0:
                draw.rectangle([(2, y), (W-2, y+43)], fill=(18, 16, 28))
            cy = y + 22
            draw.text((28, cy), r["nick"][:26], font=_f(14, True), fill=WHITE, anchor="lm")
            m = r["matches"]
            draw.text((420, cy), str(m), font=_f(13, True), fill=TEAL, anchor="mm")
            _bar(draw, 440, cy-4, 130, 8, m/10, GOLD)
            for cx, val, col in [
                (510, "✅" if r["registered"] else "·", GREEN  if r["registered"] else GRAY),
                (620, "✅" if r["r3"]         else "·", ORANGE if r["r3"]         else GRAY),
                (730, "🏅" if r["r10"]        else "·", PURPLE if r["r10"]        else GRAY),
            ]:
                draw.text((cx, cy), val, font=_f(13, True), fill=col, anchor="mm")
            draw.line([(18, y+43), (W-18, y+43)], fill=BORDER, width=1)
            y += 44

    # ── FOOTER ────────────────────────────────────────────────────────────────
    fy = H - FOOT_H
    draw.rectangle([(0, fy), (W, H)], fill=(10, 8, 18))
    draw.text((W//2, fy+FOOT_H//2),
              "200 coin (qeydiyyat)  ·  500 coin (3 matç)  ·  Ambassador banner (10 matç)",
              font=_f(10), fill=GRAY, anchor="mm")

    img.save(output_path)
    return output_path


# ── ITEM (BANNER / AVATAR) ÖNİZLƏMƏ KARTI ────────────────────────────────────

def generate_item_preview_card(nick: str, avatar_bytes: bytes | None,
                                item: dict, output_path: str) -> str:
    """
    Market item-ini (banner/avatar frame) profil üzərindən önizlə.
    item: {"id","name","type","file"}
    """
    W, H = 700, 340
    img  = Image.new("RGB", (W, H), BG)
    _vgrad(img, 0, H, (16, 12, 28), (10, 8, 18))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W-1, H-1)], outline=BORDER, width=2)

    is_banner = item.get("type") == "banner"
    item_type = "BANNER ÖNİZLƏMƏ" if is_banner else "AVATAR ÇƏRÇİVƏSİ ÖNİZLƏMƏ"

    # Header
    _vgrad(img, 0, 52, (22, 14, 40), (14, 10, 26))
    draw.line([(0, 52), (W, 52)], fill=GOLD, width=2)
    draw.text((28, 14), "CALESTIFY", font=_f(10, True), fill=GOLD)
    draw.text((28, 28), item_type, font=_f(16, True), fill=WHITE)
    draw.text((W-28, 30), item["name"][:30], font=_f(14, True), fill=TEAL, anchor="rm")

    if is_banner:
        # Banner ekran genişliyinə yayılır
        bpath = os.path.join(BASE_DIR, "banners", item["file"])
        bimg  = _load_img(bpath, W-40, 200)
        if bimg:
            # Yüngül qaranlıq overlay
            ov = Image.new("RGB", bimg.size, (0, 0, 0))
            bimg = Image.blend(bimg, ov, 0.35)
            img.paste(bimg, (20, 62))
            draw.rectangle([(20, 62), (W-20, 262)], outline=TEAL, width=2)
        # Profil simulyasiyası üstündə
        _draw_profile_sim(draw, img, avatar_bytes, nick, 48, 80)
    else:
        # Avatar frame
        _draw_profile_sim(draw, img, avatar_bytes, nick, W//2 - 90, 70,
                          frame_path=os.path.join(BASE_DIR, "frames", item["file"]))

    # Aşağı məlumat
    draw.text((W//2, 288), f"Bu {item['name']} profil arxa planı kimi görünəcək.",
              font=_f(11), fill=GRAY, anchor="mm")
    draw.text((W//2, 310), "Aktivləşdir düyməsinə bas.", font=_f(11, True), fill=GREEN, anchor="mm")

    draw.text((28, H-16), "Calestify Gaming Community", font=_f(10), fill=GRAY)

    img.save(output_path)
    return output_path


def _draw_profile_sim(draw, img, avatar_bytes, nick, ax, ay, frame_path=None):
    """Kiçik profil simulyasiyası (avatar dairəsi + nick)."""
    import io
    av_size = 80
    # Avatar
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            av = ImageOps.fit(av, (av_size, av_size), Image.LANCZOS)
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)
            out  = Image.new("RGBA", (av_size, av_size), (0, 0, 0, 0))
            out.paste(av, mask=mask)
            img.paste(out, (ax, ay), out)
        except Exception:
            draw.ellipse([(ax, ay), (ax+av_size, ay+av_size)], fill=(35, 32, 50))
    else:
        draw.ellipse([(ax, ay), (ax+av_size, ay+av_size)], fill=(35, 32, 50))

    # Frame
    if frame_path:
        fimg = _load_img(frame_path, av_size+16, av_size+16)
        if fimg:
            fimg = fimg.convert("RGBA")
            img.paste(fimg, (ax-8, ay-8), fimg if fimg.mode == "RGBA" else None)

    # Nick
    draw.text((ax + av_size//2, ay + av_size + 14), nick[:16],
              font=_f(12, True), fill=WHITE, anchor="mm")
