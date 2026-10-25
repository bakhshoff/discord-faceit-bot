from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
import datetime

WIDTH = 800
BG_TOP    = (16, 13, 24)
BG_BOTTOM = (8, 7, 12)
PANEL     = (22, 18, 30)
BORDER    = (52, 44, 70)
GOLD      = (138, 92, 230)
SILVER    = (186, 178, 202)
WHITE     = (244, 241, 234)
GRAY      = (150, 142, 168)
GREEN     = (95, 208, 122)
RED       = (214, 69, 61)

FONT_R = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_B = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def _finalize(img):
    """Whole-image polish pass: 2x upscale+downscale smooths jagged shape edges (PIL doesn't
    anti-alias rectangles/lines/ellipses natively), then a mild sharpen recovers text crispness."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(img).enhance(1.15)


def _font(size, bold=False):
    for p in (FONT_B if bold else FONT_R):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _bg(height):
    img = Image.new("RGB", (WIDTH, height), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (WIDTH, y)], fill=c)
    return img

def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]

def _bar(draw, x, y, h, color):
    draw.rectangle([(x, y + 8), (x + 10, y + h - 8)], fill=color)


# ── MATC TARIXCESi ──────────────────────────────────────────────────────────

def generate_match_history_card(history, output_path):
    ROW_H    = 52
    HEADER_H = 78
    FOOTER_H = 18
    n        = max(1, len(history))
    height   = HEADER_H + n * ROW_H + FOOTER_H

    img  = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH-1, height-1)], radius=10, outline=BORDER, width=2)

    f_brand = _font(12, True)
    f_title = _font(22, True)
    f_sub   = _font(13, True)
    f_row   = _font(16, True)
    f_sm    = _font(13)

    draw.text((28, 14), "Nextlevelaz", font=f_brand, fill=GOLD)
    draw.text((28, 30), "MATÇ TARİXÇƏSİ", font=f_title, fill=WHITE)
    cnt = f"{len(history)} matç"
    draw.text((WIDTH - 28 - _tw(draw, cnt, f_sub), 40), cnt, font=f_sub, fill=GRAY)
    draw.line([(18, HEADER_H - 6), (WIDTH - 18, HEADER_H - 6)], fill=BORDER, width=1)

    if not history:
        draw.text((28, HEADER_H + 16), "Hələ heç bir matçınız yoxdur.", font=f_sm, fill=GRAY)
    else:
        for i, h in enumerate(history):
            y = HEADER_H + i * ROW_H
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH-2, y+ROW_H-1)], fill=(21, 19, 25))

            won   = h["won"]
            color = GREEN if won else RED
            _bar(draw, 20, y, ROW_H, color)

            type_lbl = h["match_type"]
            no_lbl   = f"  #{h['match_number']}" if h.get("match_number") else ""
            res_lbl  = "QALİB" if won else "MƏĞLUB"

            draw.text((40, y + 8),  f"{type_lbl}{no_lbl}", font=f_row, fill=WHITE)
            draw.text((40, y + 28), res_lbl,               font=f_sm,  fill=color)

            chg   = h["elo_change"]
            sign  = "+" if chg >= 0 else ""
            chg_c = GREEN if chg >= 0 else RED
            draw.text((260, y + 8),  f"{h['elo_before']} -> {h['elo_after']}", font=f_row, fill=WHITE)
            draw.text((260, y + 28), f"({sign}{chg})",                         font=f_sm,  fill=chg_c)

            dt  = datetime.datetime.utcfromtimestamp(h["played_at"]) + datetime.timedelta(hours=4)
            ds  = dt.strftime("%d.%m.%Y")
            ts  = dt.strftime("%H:%M")
            draw.text((WIDTH-28-_tw(draw, ds, f_sm), y+8),  ds, font=f_sm, fill=GRAY)
            draw.text((WIDTH-28-_tw(draw, ts, f_sm), y+28), ts, font=f_sm, fill=GRAY)

            if i < len(history) - 1:
                draw.line([(18, y+ROW_H-1), (WIDTH-18, y+ROW_H-1)], fill=BORDER, width=1)

    draw.text((28, height - FOOTER_H + 4), "Nextlevelaz", font=_font(11), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── COiN LOGLARI ────────────────────────────────────────────────────────────

def generate_coin_logs_card(logs, current_balance, log_type_filter, output_path, azn_balance=None):
    ROW_H    = 46
    HEADER_H = 88
    FOOTER_H = 18
    n        = max(1, len(logs))
    height   = min(HEADER_H + n * ROW_H + FOOTER_H, 720)

    img  = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH-1, height-1)], radius=10, outline=BORDER, width=2)

    f_brand = _font(12, True)
    f_title = _font(22, True)
    f_sub   = _font(13, True)
    f_row   = _font(15, True)
    f_sm    = _font(13)
    f_bal   = _font(18, True)

    if log_type_filter == "earn":
        flbl, fcol = "QAZANMA",   GREEN
    elif log_type_filter == "spend":
        flbl, fcol = "XƏRCLƏMƏ",  RED
    else:
        flbl, fcol = "HAMISI",    GOLD

    draw.text((28, 14), "Nextlevelaz", font=f_brand, fill=GOLD)
    draw.text((28, 30), "COİN LOGLARI", font=f_title, fill=WHITE)

    bw = _tw(draw, flbl, f_sub) + 16
    draw.rectangle([(196, 32), (196+bw, 54)], fill=fcol)
    draw.text((204, 32), flbl, font=f_sub, fill=(18, 16, 22))

    bal_txt = f"Balans: {current_balance} coin"
    draw.text((WIDTH-28-_tw(draw, bal_txt, f_bal), 24), bal_txt, font=f_bal, fill=GOLD)

    if azn_balance is not None:
        f_azn = _font(13, True)
        azn_txt = f"{azn_balance:.2f} AZN"
        draw.text((WIDTH-28-_tw(draw, azn_txt, f_azn), 48), azn_txt, font=f_azn, fill=SILVER)

    draw.line([(18, HEADER_H-6), (WIDTH-18, HEADER_H-6)], fill=BORDER, width=1)

    if not logs:
        draw.text((28, HEADER_H+14), "Bu filtrdə heç bir qeyd yoxdur.", font=f_sm, fill=GRAY)
    else:
        for i, log in enumerate(logs):
            y = HEADER_H + i * ROW_H
            if y + ROW_H > height - FOOTER_H:
                break
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH-2, y+ROW_H-1)], fill=(21, 19, 25))

            chg    = log["change"]
            is_e   = log["log_type"] == "earn"
            color  = GREEN if is_e else RED
            sign   = "+" if chg >= 0 else ""
            _bar(draw, 20, y, ROW_H, color)

            draw.text((40, y+8),  f"{sign}{chg} coin", font=f_row, fill=color)
            reason = log["reason"]
            if len(reason) > 48:
                reason = reason[:45] + "..."
            draw.text((40, y+28), reason, font=f_sm, fill=GRAY)

            if log.get("balance_after") is not None:
                bat = f"{log['balance_after']} coin"
                draw.text((WIDTH-28-_tw(draw, bat, f_sm), y+8), bat, font=f_sm, fill=GRAY)
            dt  = datetime.datetime.utcfromtimestamp(log["created_at"]) + datetime.timedelta(hours=4)
            dts = dt.strftime("%d.%m %H:%M")
            draw.text((WIDTH-28-_tw(draw, dts, f_sm), y+28), dts, font=f_sm, fill=GRAY)

            if i < len(logs)-1:
                draw.line([(18, y+ROW_H-1), (WIDTH-18, y+ROW_H-1)], fill=BORDER, width=1)

    draw.text((28, height-FOOTER_H+4), "Nextlevelaz", font=_font(11), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── GÜNDƏLİK TAPŞIRIQLAR ─────────────────────────────────────────────────────

CYAN   = (60, 200, 200)






# ── RANK HESABLAYİCİSİ ────────────────────────────────────────────────────────
RANKS = [
    (0,    900,  "Qığılcım I",  (150, 150, 160), "⚡"),
    (900,  1000, "Qığılcım II", (180, 180, 190), "⚡"),
    (1000, 1100, "Alov I",      (255, 140, 60),  "🔥"),
    (1100, 1200, "Alov II",     (255, 110, 40),  "🔥"),
    (1200, 1350, "Nova I",      (80,  180, 255), "💫"),
    (1350, 1500, "Nova II",     (100, 200, 255), "💫"),
    (1500, 1700, "Supernova",   (160, 90,  255), "🌌"),
    (1700, 9999, "Zenit",       (255, 200, 0),   "👑"),
]

def get_rank(elo: int) -> tuple:
    for lo, hi, name, color, emoji in RANKS:
        if lo <= elo < hi:
            return name, color, emoji
    return RANKS[-1][2], RANKS[-1][3], RANKS[-1][4]


# ── OYUNÇU STATS KARTI (/stats @oyuncu) ──────────────────────────────────────
def generate_stats_card(player_data: dict, achievements: list, output_path: str):
    """
    player_data: {nick, so2_id, elo, wins, losses, kills, assists, deaths,
                  win_streak, max_streak, coins, zm_balance}
    achievements: list of {icon, name}
    """
    W, H  = 820, 420
    PAD   = 20
    img   = Image.new("RGB", (W, H), BG_TOP)
    draw  = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    draw.rounded_rectangle([(0,0),(W-1,H-1)], radius=10, outline=BORDER, width=2)

    fb  = _font(13, True)
    ft  = _font(26, True)
    fm  = _font(16, True)
    fs  = _font(14)
    fx2 = _font(12)
    fxi = _font(11)

    nick   = player_data.get("nick", "?")
    so2_id = player_data.get("so2_id", "?")
    elo    = player_data.get("elo", 1000)
    wins   = player_data.get("wins", 0)
    losses = player_data.get("losses", 0)
    kills  = player_data.get("kills", 0)
    deaths = player_data.get("deaths", 0)
    assists= player_data.get("assists", 0)
    streak = player_data.get("win_streak", 0)
    max_s  = player_data.get("max_streak", 0)
    kd     = round(kills/max(deaths,1), 2)
    wr     = round(wins/max(wins+losses,1)*100, 1)

    rank_name, rank_color, rank_emoji = get_rank(elo)

    # Header
    draw.text((PAD, 14), "Nextlevelaz", font=fb, fill=GOLD)
    draw.text((PAD, 30), "OYUNÇU STATİSTİKASI", font=ft, fill=WHITE)
    draw.line([(0,72),(W,72)], fill=BORDER, width=1)

    # Sol: nick + rank
    draw.text((PAD, 82), nick[:22], font=_font(28, True), fill=WHITE)
    draw.text((PAD, 118), f"SO2 ID: {so2_id}", font=fs, fill=GRAY)
    rc = rank_color
    draw.rounded_rectangle([PAD, 140, PAD+160, 168], radius=6, fill=tuple(c//4 for c in rc), outline=rc, width=2)
    draw.text((PAD+8, 144), rank_name, font=fx2, fill=rc)

    # Streak
    streak_col = (255,140,0) if streak >= 3 else GRAY
    draw.text((PAD, 178), f"Streak: {streak}  |  Max: {max_s}", font=fs, fill=streak_col)

    # Sağ: ELO böyük
    draw.text((W-180, 82), "ELO", font=_font(14, True), fill=GRAY)
    draw.text((W-180, 98), str(elo), font=_font(46, True), fill=GOLD)

    # Stats blokları
    bw, bh, by = (W-PAD*2)//5, 80, 210
    stats = [
        ("MATÇ",    wins+losses, WHITE),
        ("QƏLƏBƏ",  wins,        GREEN),
        ("KİLL",    kills,       (100, 220, 255)),
        ("K/D",     kd,          GOLD),
        ("WIN %",   f"{wr}%",   GREEN),
    ]
    for i,(lbl,val,col) in enumerate(stats):
        x = PAD + i*bw
        draw.rounded_rectangle([x+2, by, x+bw-2, by+bh], radius=6, fill=PANEL, outline=BORDER, width=1)
        draw.text((x+bw//2, by+bh//2-12), str(val), font=_font(22, True), fill=col, anchor="mm")
        draw.text((x+bw//2, by+bh-14),     lbl,       font=_font(10, True), fill=GRAY, anchor="mm")

    # Nailiyyətlər
    ay = 310
    draw.text((PAD, ay), "Nailiyyətlər:", font=_font(13, True), fill=GOLD)
    if achievements:
        ax = PAD
        for ach in achievements[:10]:
            txt = ach['name']  # Emoji-siz yalnız ad
            draw.text((ax, ay+22), txt, font=fxi, fill=WHITE)
            try:
                ax += int(_font(11).getlength(txt)) + 14
            except Exception:
                ax += len(txt) * 7 + 14
            if ax > W - 100:
                break
    else:
        draw.text((PAD+120, ay+22), "Hələ yoxdur", font=fxi, fill=GRAY)

    draw.text((PAD, H-24), "Nextlevelaz", font=fxi, fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── XƏBƏRDARLIQ KARTI ────────────────────────────────────────────────────────


# ── NAİLİYYƏTLƏR KARTI ───────────────────────────────────────────────────────


# ── OYUNCU MUQAYİSƏ KARTI ────────────────────────────────────────────────────


# ── ELO QRAFİK KARTI ──────────────────────────────────────────────────────────


# ── FƏALİYYƏT PANELİ KARTI ────────────────────────────────────────────────────
def generate_activity_card(stats: dict, output_path: str, hourly: dict = None):
    W, H = 720, 420 if hourly else 320
    img  = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    draw.rectangle([(0,0),(W-1,H-1)], outline=GOLD, width=2)

    fb = _font(13, True); ft = _font(22, True); fm = _font(15); fs = _font(13); fx = _font(11)

    days = stats["days"]
    draw.text((20, 12), "Nextlevelaz", font=fb, fill=GOLD)
    draw.text((20, 28), f"FƏALİYYƏT PANELİ — Son {days} Gün", font=ft, fill=WHITE)
    draw.line([(0,70),(W,70)], fill=BORDER, width=1)

    # Böyük rəqəmlər
    boxes = [
        (stats["match_count"], "Matç"),
        (stats["player_count"], "Oyunçu"),
        (stats["total_kills"], "Kill"),
    ]
    bw = (W - 40) // 3
    for i, (val, lbl) in enumerate(boxes):
        x = 20 + i * bw
        draw.rectangle([x+4, 80, x+bw-4, 160], fill=PANEL, outline=BORDER, width=1)
        draw.text((x+bw//2, 110), str(val), font=_font(28, True), fill=GOLD, anchor="mm")
        draw.text((x+bw//2, 148), lbl, font=_font(11, True), fill=GRAY, anchor="mm")

    # Top aktiv oyunçular
    draw.text((20, 175), "Ən aktiv oyunçular:", font=fb, fill=WHITE)
    medals = ["1.", "2.", "3.", "4.", "5."]
    for i, (nick, cnt) in enumerate(stats.get("top_active", [])[:5]):
        draw.text((20, 198 + i*22), f"{medals[i]} {nick[:20]}", font=fs, fill=WHITE)
        draw.text((280, 198 + i*22), f"{cnt} matç", font=fs, fill=GRAY)

    # Saatlıq aktivlik mini-qrafik
    if hourly and len(hourly) > 0:
        gy = 310
        draw.text((20, gy), "Saatlıq fəaliyyət:", font=fs, fill=WHITE)
        gy += 22
        max_cnt = max(hourly.values()) if hourly else 1
        bar_w   = (W - 40) // 24
        for hour in range(24):
            cnt = hourly.get(hour, 0)
            bh  = int(50 * cnt / max_cnt) if max_cnt else 0
            bx  = 20 + hour * bar_w
            col = GREEN if cnt == max_cnt else (CYAN if cnt > max_cnt // 2 else PANEL)
            draw.rectangle([(bx+1, gy+50-bh), (bx+bar_w-1, gy+50)], fill=col)
            if hour % 4 == 0:
                draw.text((bx, gy+54), str(hour), font=_font(9), fill=GRAY)

    draw.text((20, H-24), "Nextlevelaz", font=fx, fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── BATTLE PASS KARTI (ANİMASİYALI GIF) ──────────────────────────────────────









# ── iNVENTAR ────────────────────────────────────────────────────────────────



# ── COiN TRANSFERi KARTI ────────────────────────────────────────────────────



# ── OYUNCU AXTARISI KARTI ───────────────────────────────────────────────────



# ── SKiN KATALOQ KARTI ──────────────────────────────────────────────────────



# ── ELO KARTLARI (AZN market) ─────────────────────────────────────────────────



# ── HƏFTƏLİK MVP KARTI ───────────────────────────────────────────────────────



# ── AYIN ELO ÇEMPİONU MÜKAFAT KARTI ──────────────────────────────────────────



# ── SƏRBƏST ELAN KARTI (/elan) ───────────────────────────────────────────────

def _wrap_text(draw, text, font, max_width):
    """Admin-in yazdığı sərbəst mətni (manual sətir keçidləri saxlanılır) verilmiş enə uyğun
    sözlərə görə sətirlərə bölür."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if not cur or _tw(draw, trial, font) <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def generate_announcement_card(title, body, output_path):
    """/elan admin komandası ilə yaradılan sərbəst mətnli, vizual server elanı kartı.
    Hündürlük mətnin uzunluğuna görə dinamik hesablanır (digər kartlarla eyni prinsip)."""
    PAD = 36
    title_font = _font(30, True)
    body_font = _font(16)
    brand_font = _font(13, True)
    footer_font = _font(11)

    dummy = Image.new("RGB", (WIDTH, 10))
    dd = ImageDraw.Draw(dummy)
    max_text_width = WIDTH - PAD * 2
    title_lines = _wrap_text(dd, title, title_font, max_text_width) or [""]
    body_lines = _wrap_text(dd, body, body_font, max_text_width) or [""]

    HEADER_H = 64
    TITLE_LINE_H = 40
    BODY_LINE_H = 26
    FOOTER_H = 40
    content_h = (HEADER_H + len(title_lines) * TITLE_LINE_H + 32
                 + len(body_lines) * BODY_LINE_H + FOOTER_H + PAD)
    H = max(content_h, 260)

    img = _bg(H)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH - 1, H - 1)], outline=GOLD, width=2)
    draw.rectangle([(0, 0), (WIDTH - 1, 6)], fill=GOLD)

    draw.ellipse([(PAD, 26), (PAD + 8, 34)], fill=GOLD)
    draw.text((PAD + 18, 22), "Nextlevelaz — ELAN", font=brand_font, fill=GOLD)
    draw.line([(PAD, HEADER_H - 16), (WIDTH - PAD, HEADER_H - 16)], fill=BORDER, width=1)

    y = HEADER_H
    for line in title_lines:
        draw.text((PAD, y), line, font=title_font, fill=WHITE)
        y += TITLE_LINE_H
    y += 12
    draw.line([(PAD, y), (WIDTH - PAD, y)], fill=BORDER, width=1)
    y += 20

    for line in body_lines:
        draw.text((PAD, y), line, font=body_font, fill=SILVER)
        y += BODY_LINE_H

    footer_y = H - FOOTER_H + 8
    draw.line([(PAD, footer_y - 12), (WIDTH - PAD, footer_y - 12)], fill=BORDER, width=1)
    draw.text((PAD, footer_y), "Nextlevelaz — FACEIT Standoff 2", font=footer_font, fill=GRAY)

    _finalize(img).save(output_path)
    return output_path


# ── MERC KARTI ──────────────────────────────────────────────────────────────



# ── XƏRİTƏ STATİSTİKASI ───────────────────────────────────────────────────────

def generate_map_stats_card(nick, map_stats, output_path):
    """map_stats: {map_name: {"wins": int, "losses": int}}"""
    ROW_H = 44
    HEADER = 70
    FOOTER = 20
    maps = sorted(map_stats.items(), key=lambda kv: kv[1]["wins"] + kv[1]["losses"], reverse=True)
    n = max(1, len(maps))
    height = HEADER + n * ROW_H + FOOTER

    img = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH - 1, height - 1)], radius=10, outline=BORDER, width=2)

    draw.text((28, 14), "Nextlevelaz", font=_font(12, True), fill=GOLD)
    draw.text((28, 30), "XƏRİTƏ STATİSTİKASI", font=_font(22, True), fill=WHITE)
    draw.line([(18, HEADER - 6), (WIDTH - 18, HEADER - 6)], fill=BORDER, width=1)

    y = HEADER
    if not maps:
        draw.text((28, y + 14), "Hələ xəritə statistikası yoxdur.", font=_font(13), fill=GRAY)
    else:
        for i, (map_name, s) in enumerate(maps):
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH - 2, y + ROW_H - 1)], fill=(21, 19, 25))
            total = s["wins"] + s["losses"]
            wr = round(s["wins"] / total * 100, 1) if total else 0.0
            col = GREEN if wr >= 50 else RED
            _bar(draw, 20, y, ROW_H, col)
            draw.text((40, y + 8), map_name, font=_font(15, True), fill=WHITE)
            draw.text((40, y + 26), f"{s['wins']}Q / {s['losses']}M", font=_font(12), fill=GRAY)
            wr_txt = f"{wr}%"
            draw.text((WIDTH - 28 - _tw(draw, wr_txt, _font(15, True)), y + 14), wr_txt, font=_font(15, True), fill=col)
            y += ROW_H

    draw.text((28, height - FOOTER + 2), "Nextlevelaz", font=_font(10), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── ŞƏXSİ REKORD ──────────────────────────────────────────────────────────────



# ── ELO İNKİŞAF QRAFİKİ ─────────────────────────────────────────────────────

def generate_elo_chart_card(nick, history, output_path):
    """history: xronoloji sırada [{"match_number": int, "elo_after": int}, ...]"""
    H = 320
    img = _bg(H)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH - 1, H - 1)], radius=10, outline=GOLD, width=2)

    draw.text((28, 14), "Nextlevelaz", font=_font(12, True), fill=GOLD)
    draw.text((28, 30), f"{nick} — ELO İNKİŞAFI", font=_font(20, True), fill=WHITE)
    draw.line([(18, 64), (WIDTH - 18, 64)], fill=BORDER, width=1)

    if not history:
        draw.text((28, 100), "Hələ heç bir matç oynanılmayıb.", font=_font(14), fill=GRAY)
        draw.text((28, H - 22), "Nextlevelaz", font=_font(10), fill=GRAY)
        _finalize(img).save(output_path)
        return output_path

    PAD_L, PAD_R, PAD_T, PAD_B = 55, 30, 80, 40
    plot_w = WIDTH - PAD_L - PAD_R
    plot_h = H - PAD_T - PAD_B

    elos = [h["elo_after"] for h in history]
    min_e, max_e = min(elos), max(elos)
    if min_e == max_e:
        min_e -= 10
        max_e += 10
    pad_range = (max_e - min_e) * 0.1
    min_e -= pad_range
    max_e += pad_range

    def xy(i, elo):
        x = PAD_L + (i / max(len(history) - 1, 1)) * plot_w
        y = PAD_T + plot_h - ((elo - min_e) / (max_e - min_e)) * plot_h
        return x, y

    for gi in range(5):
        gy = PAD_T + plot_h * gi / 4
        draw.line([(PAD_L, gy), (WIDTH - PAD_R, gy)], fill=BORDER, width=1)
        val = int(max_e - (max_e - min_e) * gi / 4)
        draw.text((PAD_L - 8, gy), str(val), font=_font(10), fill=GRAY, anchor="rm")

    points = [xy(i, h["elo_after"]) for i, h in enumerate(history)]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=GOLD, width=3)
    for x, y in points:
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=GOLD, outline=WHITE, width=1)

    label_idxs = sorted(set([0, len(history) // 2, len(history) - 1]))
    for i in label_idxs:
        x, _ = points[i]
        draw.text((x, PAD_T + plot_h + 16), f"#{history[i]['match_number']}", font=_font(10), fill=GRAY, anchor="mm")

    gain = elos[-1] - elos[0]
    gain_txt = f"{'+' if gain >= 0 else ''}{gain} ELO ({len(history)} matç)"
    gain_color = GREEN if gain >= 0 else RED
    draw.text((WIDTH - 28, 40), gain_txt, font=_font(14, True), fill=gain_color, anchor="rm")

    draw.text((28, H - 22), "Nextlevelaz", font=_font(10), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── QUESTLƏR ─────────────────────────────────────────────────────────────────



# ── SQUAD (DUO) ───────────────────────────────────────────────────────────────



# ── GİZLİ SİNERGİYA ──────────────────────────────────────────────────────────




# ── XƏRİTƏ USTALARI ─────────────────────────────────────────────────────────



# ── NAİLİYYƏT STİKERİ (/stickerlerim) ────────────────────────────────────────



# ── ÜMUMI SÖHBƏT AKTİVLİK LÖVHƏSİ ────────────────────────────────────────────

def generate_chat_activity_card(rows, output_path):
    """rows: [{"nick": str, "weekly_xp": int}, ...] XP-yə görə azalan sırada.
    Hündürlük sətir sayına görə dinamik hesablanır (digər kartlarla eyni prinsip)."""
    PAD = 28
    HEADER_H = 90
    ROW_H = 38
    FOOTER_H = 30
    n_rows = max(len(rows), 1)
    height = HEADER_H + n_rows * ROW_H + FOOTER_H

    img = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH - 1, height - 1)], radius=14, outline=GOLD, width=2)

    draw.text((28, 16), "Nextlevelaz", font=_font(12, True), fill=GOLD)
    draw.text((28, 34), "HƏFTƏLİK AKTİVLİK LÖVHƏSİ", font=_font(26, True), fill=WHITE)
    draw.text((28, 68), "Ümumi söhbətdə yazdığın hər mesaja görə XP qazanırsan", font=_font(12), fill=GRAY)
    draw.line([(18, HEADER_H - 8), (WIDTH - 18, HEADER_H - 8)], fill=BORDER, width=1)

    y = HEADER_H
    if rows:
        medal_colors = [GOLD, SILVER, (176, 120, 60)]
        for i, r in enumerate(rows):
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH - 2, y + ROW_H - 1)], fill=PANEL)
            col = medal_colors[i] if i < 3 else GRAY
            draw.text((PAD, y + ROW_H // 2), f"#{i + 1}", font=_font(15, True), fill=col, anchor="lm")
            draw.text((PAD + 50, y + ROW_H // 2), r["nick"][:28], font=_font(15, True), fill=WHITE, anchor="lm")
            draw.text((WIDTH - PAD, y + ROW_H // 2), f"{r['weekly_xp']} XP",
                      font=_font(15, True), fill=GREEN, anchor="rm")
            y += ROW_H
    else:
        draw.text((WIDTH // 2, y + ROW_H // 2), "Bu həftə hələ heç kim yazmayıb.",
                  font=_font(14), fill=GRAY, anchor="mm")
        y += ROW_H

    draw.text((28, height - FOOTER_H + 6), "Nextlevelaz — hər Bazar 23:59 həftənin ən aktivi elan olunur",
              font=_font(10), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path


# ── SEZON SONU MÜKAFATI ─────────────────────────────────────────────────────

def generate_season_reward_card(mode_label, season_number, top3, output_path, preview=False):
    """top3: [{"nick", "elo_gained", "wins", "losses", "reward"}, ...] — sıralı (0-cı = 1-ci yer),
    ən çoxu 3 element. preview=True olanda hələ heç bir sezon bağlanmadan kanalın necə görünəcəyini
    göstərən nümunə kart kimi işarələnir (başlıq fərqli olur)."""
    RANK_COLORS = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
    RANK_MEDALS = ["🥇", "🥈", "🥉"]

    PAD = 28
    HEADER_H = 92
    ROW_H = 96
    FOOTER_H = 26
    entries = top3[:3]
    n = max(len(entries), 1)
    height = HEADER_H + n * ROW_H + FOOTER_H

    img = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (WIDTH - 1, height - 1)], radius=14, outline=GOLD, width=2)

    title = f"{mode_label} SEZON MÜKAFATLARI — NÜMUNƏ" if preview else f"{mode_label} SEZON #{season_number} — YEKUN NƏTİCƏ"
    subtitle = "Sezon bağlananda Top-3 bu formada elan olunacaq" if preview else "Sezon bağlandı, Top-3 Gold mükafatı qazandı!"
    draw.text((PAD, 16), "Nextlevelaz", font=_font(12, True), fill=GOLD)
    draw.text((PAD, 34), title, font=_font(24, True), fill=WHITE)
    draw.text((PAD, 68), subtitle, font=_font(12), fill=GRAY)
    draw.line([(18, HEADER_H - 8), (WIDTH - 18, HEADER_H - 8)], fill=BORDER, width=1)

    y = HEADER_H
    if entries:
        for i, p in enumerate(entries):
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH - 2, y + ROW_H - 1)], fill=PANEL)
            accent = RANK_COLORS[i]
            _bar(draw, 20, y, ROW_H, accent)

            draw.text((48, y + ROW_H // 2), RANK_MEDALS[i], font=_font(36), fill=WHITE, anchor="lm")
            draw.text((108, y + 24), p["nick"][:22], font=_font(22, True), fill=WHITE, anchor="lm")

            chg = p.get("elo_gained", 0)
            sign = "+" if chg >= 0 else ""
            chg_color = GREEN if chg >= 0 else RED
            draw.text((108, y + 58), f"{sign}{chg} ELO", font=_font(14, True), fill=chg_color, anchor="lm")
            wl_txt = f"{p.get('wins', 0)}Q / {p.get('losses', 0)}M"
            draw.text((108 + _tw(draw, f"{sign}{chg} ELO  ", _font(14, True)), y + 58), wl_txt,
                      font=_font(14), fill=GRAY, anchor="lm")

            reward = p.get("reward", 0)
            reward_txt = f"+{reward} Gold" if reward else "-"
            draw.text((WIDTH - PAD, y + ROW_H // 2), reward_txt, font=_font(22, True), fill=accent, anchor="rm")

            y += ROW_H
    else:
        draw.text((WIDTH // 2, y + ROW_H // 2), "Bu sezon qeydə alınmış statistika yoxdur.",
                  font=_font(14), fill=GRAY, anchor="mm")
        y += ROW_H

    draw.text((PAD, height - FOOTER_H + 6), "Nextlevelaz — yeni sezon başladı, uğurlar!",
              font=_font(10), fill=GRAY)
    _finalize(img).save(output_path)
    return output_path
