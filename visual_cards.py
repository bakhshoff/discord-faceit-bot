from PIL import Image, ImageDraw, ImageFont
import os
import datetime

WIDTH = 800
BG_TOP    = (18, 16, 22)
BG_BOTTOM = (10, 9, 12)
PANEL     = (24, 22, 28)
BORDER    = (45, 42, 50)
GOLD      = (240, 180, 41)
WHITE     = (244, 241, 234)
GRAY      = (141, 135, 148)
GREEN     = (95, 208, 122)
RED       = (214, 69, 61)
BLUE      = (80, 160, 220)

FONT_R = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_B = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

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
    draw.rectangle([(0, 0), (WIDTH-1, height-1)], outline=BORDER, width=2)

    f_brand = _font(12, True)
    f_title = _font(22, True)
    f_sub   = _font(13, True)
    f_row   = _font(16, True)
    f_sm    = _font(13)

    draw.text((28, 14), "CALESTIFY", font=f_brand, fill=GOLD)
    draw.text((28, 30), "MATC TARIХCESI", font=f_title, fill=WHITE)
    cnt = f"{len(history)} matc"
    draw.text((WIDTH - 28 - _tw(draw, cnt, f_sub), 40), cnt, font=f_sub, fill=GRAY)
    draw.line([(18, HEADER_H - 6), (WIDTH - 18, HEADER_H - 6)], fill=BORDER, width=1)

    if not history:
        draw.text((28, HEADER_H + 16), "Hele hec bir matciniz yoxdur.", font=f_sm, fill=GRAY)
    else:
        for i, h in enumerate(history):
            y = HEADER_H + i * ROW_H
            if i % 2 == 0:
                draw.rectangle([(2, y), (WIDTH-2, y+ROW_H-1)], fill=(21, 19, 25))

            won   = h["won"]
            color = GREEN if won else RED
            _bar(draw, 20, y, ROW_H, color)

            type_lbl = "5v5" if h["match_type"] == "5v5" else "1v1"
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

    draw.text((28, height - FOOTER_H + 4), "Calestify Gaming Community", font=_font(11), fill=GRAY)
    img.save(output_path)
    return output_path


# ── COiN LOGLARI ────────────────────────────────────────────────────────────

def generate_coin_logs_card(logs, current_balance, log_type_filter, output_path):
    ROW_H    = 46
    HEADER_H = 88
    FOOTER_H = 18
    n        = max(1, len(logs))
    height   = min(HEADER_H + n * ROW_H + FOOTER_H, 720)

    img  = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH-1, height-1)], outline=BORDER, width=2)

    f_brand = _font(12, True)
    f_title = _font(22, True)
    f_sub   = _font(13, True)
    f_row   = _font(15, True)
    f_sm    = _font(13)
    f_bal   = _font(18, True)

    if log_type_filter == "earn":
        flbl, fcol = "QAZANMA",   GREEN
    elif log_type_filter == "spend":
        flbl, fcol = "XERCLƏMƏ",  RED
    else:
        flbl, fcol = "HAMISI",    GOLD

    draw.text((28, 14), "CALESTIFY", font=f_brand, fill=GOLD)
    draw.text((28, 30), "COiN LOGLARI", font=f_title, fill=WHITE)

    bw = _tw(draw, flbl, f_sub) + 16
    draw.rectangle([(196, 32), (196+bw, 54)], fill=fcol)
    draw.text((204, 32), flbl, font=f_sub, fill=(18, 16, 22))

    bal_txt = f"Balans: {current_balance} coin"
    draw.text((WIDTH-28-_tw(draw, bal_txt, f_bal), 28), bal_txt, font=f_bal, fill=GOLD)

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

    draw.text((28, height-FOOTER_H+4), "Calestify Gaming Community", font=_font(11), fill=GRAY)
    img.save(output_path)
    return output_path


# ── GÜNDƏLİK TAPŞIRIQLAR ─────────────────────────────────────────────────────

ORANGE = (230, 120, 30)
CYAN   = (60, 200, 200)
PURPLE = (160, 90, 255)


def _progress_bar(draw, x, y, w, h, pct, color, bg=(40, 38, 48)):
    draw.rectangle([x, y, x+w, y+h], fill=bg, outline=(60,58,68), width=1)
    if pct > 0:
        fill_w = max(4, int(w * min(pct, 1.0)))
        draw.rectangle([x, y, x+fill_w, y+h], fill=color)


def generate_tasks_card(active_task, available_tasks, output_path):
    """
    active_task: get_player_active_task() çıxışı (dict) ya da None
    available_tasks: get_active_daily_tasks() çıxışı (list)
    """
    CARD_H  = 160
    PAD     = 18
    HEADER  = 70
    FOOTER  = 34

    n       = 1 if active_task else max(1, len(available_tasks))
    height  = HEADER + n * (CARD_H + 10) + FOOTER

    img  = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(WIDTH-1,height-1)], outline=BORDER, width=2)

    fb = _font(12, True)
    ft = _font(22, True)
    fm = _font(14)
    fs = _font(12)
    fx = _font(11)

    draw.text((PAD, 12), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((PAD, 28), "GÜNDƏLİK TAPŞIRIQLAR", font=ft, fill=WHITE)
    draw.line([(0, HEADER), (WIDTH, HEADER)], fill=BORDER, width=1)

    y = HEADER + 8

    if active_task:
        # Aktiv tapşırıq kartı
        a = active_task
        kp, kt = a["kills_progress"],  max(a["kill_target"],  1) if a["kill_target"]  else 1
        ap, at = a["assists_progress"], max(a["assist_target"],1) if a["assist_target"] else 1
        pct_k  = (a["kills_progress"]  / a["kill_target"])  if a["kill_target"]  else None
        pct_a  = (a["assists_progress"] / a["assist_target"]) if a["assist_target"] else None

        try:
            exp_dt = datetime.datetime.utcfromtimestamp(a["expires_at"]) + datetime.timedelta(hours=4)
            tl_sec = max(0, int(a["expires_at"]) - int(datetime.datetime.utcnow().timestamp()))
            h_left, m_left = tl_sec // 3600, (tl_sec % 3600) // 60
            time_str = f"{h_left}s {m_left}deq qalıb  ·  {exp_dt.strftime('%H:%M')}"
        except Exception:
            time_str = "—"

        cx, cy, cw, ch = PAD, y, WIDTH - PAD*2, CARD_H
        draw.rectangle([cx, cy, cx+cw, cy+ch], fill=PANEL, outline=ORANGE, width=2)
        draw.rectangle([cx, cy, cx+cw, cy+28], fill=(50,30,10))
        draw.text((cx+10, cy+6), "[ AKTiV TAPSIRIQ ]", font=fb, fill=ORANGE)

        draw.text((cx+10, cy+36), a["description"][:60], font=fm, fill=WHITE)
        draw.text((cx+10, cy+58), f"Mukafat: {a['reward_coins']} coin", font=fs, fill=GOLD)
        draw.text((cx+10, cy+76), time_str, font=fx, fill=GRAY)

        bar_w = (cw - 30) // 2
        # Kill progress
        if pct_k is not None:
            draw.text((cx+10, cy+96), f"Kill: {a['kills_progress']}/{a['kill_target']}", font=fx, fill=GREEN)
            _progress_bar(draw, cx+10, cy+110, bar_w, 14, pct_k, GREEN)
        if pct_a is not None:
            draw.text((cx+bar_w+20, cy+96), f"Asist: {a['assists_progress']}/{a['assist_target']}", font=fx, fill=CYAN)
            _progress_bar(draw, cx+bar_w+20, cy+110, bar_w, 14, pct_a, CYAN)

        # Overall — yalnız mövcud hədəflərin ortalaması
        active_pcts = [p for p in [pct_k, pct_a] if p is not None]
        overall     = sum(active_pcts) / len(active_pcts) if active_pcts else 0.0
        _progress_bar(draw, cx+10, cy+130, cw-20, 18, overall, ORANGE)
        pct_txt = f"{int(overall * 100)}%"
        draw.text((cx + cw//2 - _tw(draw, pct_txt, fx)//2, cy+132), pct_txt, font=fx, fill=WHITE)

    else:
        # Mövcud tapşırıqlar siyahısı
        colors = [GREEN, CYAN, PURPLE]
        for i, t in enumerate(available_tasks[:3]):
            cx, cy, cw, ch = PAD, y + i*(CARD_H+10), WIDTH-PAD*2, CARD_H
            col = colors[i % len(colors)]
            draw.rectangle([cx, cy, cx+cw, cy+ch], fill=PANEL, outline=col, width=2)
            draw.rectangle([cx, cy, cx+cw, cy+28], fill=(10,20,10))
            draw.text((cx+10, cy+6), f"[ TAPSIRIQ {i+1} ]", font=fb, fill=col)

            draw.text((cx+10, cy+36), t["description"][:58], font=fm, fill=WHITE)

            details = []
            if t["kill_target"]:  details.append(f"Kill: {t['kill_target']}")
            if t["assist_target"]: details.append(f"Asist: {t['assist_target']}")
            draw.text((cx+10, cy+62), "  ".join(details) if details else "Hədəf yoxdur", font=fs, fill=GRAY)

            draw.text((cx+10, cy+86), f"Mukafat: {t['reward_coins']} coin", font=fs, fill=GOLD)

            try:
                exp = datetime.datetime.utcfromtimestamp(t["expires_at"]) + datetime.timedelta(hours=4)
                tl  = max(0, int(t["expires_at"]) - int(datetime.datetime.utcnow().timestamp()))
                h2, m2 = tl//3600, (tl%3600)//60
                draw.text((cx+10, cy+108), f"{exp.strftime('%H:%M')} biter  ·  {h2}s {m2}deq qalıb", font=fx, fill=GRAY)
            except Exception:
                pass

            # Dekorativ rəngli şerit
            draw.rectangle([cx, cy+ch-8, cx+cw, cy+ch-2], fill=col)

    draw.text((PAD, height-FOOTER+6), "Calestify Gaming Community  ·  /gunluk", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


# ── RANK HESABLAYİCİSİ ────────────────────────────────────────────────────────
RANKS = [
    (0,    900,  "Gümüş I",   (150, 150, 160), "🩶"),
    (900,  1000, "Gümüş II",  (180, 180, 190), "🩶"),
    (1000, 1100, "Qızıl I",   (200, 160, 50),  "🥇"),
    (1100, 1200, "Qızıl II",  (220, 180, 60),  "🥇"),
    (1200, 1350, "Almaz I",   (80,  180, 255),  "💎"),
    (1350, 1500, "Almaz II",  (100, 200, 255),  "💎"),
    (1500, 1700, "Elite",     (160, 90,  255),  "👑"),
    (1700, 9999, "Master",    (255, 200, 0),   "🌟"),
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
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

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
    draw.text((PAD, 14), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((PAD, 30), f"OYUNÇU STATİSTİKASI", font=ft, fill=WHITE)
    draw.line([(0,72),(W,72)], fill=BORDER, width=1)

    # Sol: nick + rank
    draw.text((PAD, 82), nick[:22], font=_font(28, True), fill=WHITE)
    draw.text((PAD, 118), f"SO2 ID: {so2_id}", font=fs, fill=GRAY)
    rc = rank_color
    draw.rectangle([PAD, 140, PAD+160, 168], fill=tuple(c//4 for c in rc), outline=rc, width=2)
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
        draw.rectangle([x+2, by, x+bw-2, by+bh], fill=PANEL, outline=BORDER, width=1)
        draw.text((x+bw//2, by+bh//2-12), str(val), font=_font(22, True), fill=col, anchor="mm")
        draw.text((x+bw//2, by+bh-14),     lbl,       font=_font(10, True), fill=GRAY, anchor="mm")

    # Nailiyyətlər
    ay = 310
    draw.text((PAD, ay), "Nailiyyetler:", font=_font(13, True), fill=GOLD)
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
        draw.text((PAD+120, ay+22), "Hele yoxdur", font=fxi, fill=GRAY)

    draw.text((PAD, H-24), "Calestify Gaming Community", font=fxi, fill=GRAY)
    img.save(output_path)
    return output_path


# ── XƏBƏRDARLIQ KARTI ────────────────────────────────────────────────────────
def generate_warnings_card(nick: str, warnings: list, is_banned: bool, output_path: str):
    ROW_H  = 52
    HEADER = 80
    FOOTER = 30
    n      = max(1, len(warnings))
    H      = HEADER + n * ROW_H + FOOTER + 20

    img  = Image.new("RGB", (800, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(800,y)], fill=c)
    draw.rectangle([(0,0),(799,H-1)], outline=RED if is_banned else BORDER, width=2)

    fb = _font(13, True)
    ft = _font(22, True)
    fs = _font(14)
    fx = _font(12)

    status = "[BANLANDI]" if is_banned else f"{len(warnings)} Xeberdarliq"
    draw.text((20, 12), "CALESTIFY  ·  ADMIN PANEL", font=fb, fill=GOLD)
    draw.text((20, 28), f"{nick} — {status}", font=ft, fill=RED if is_banned else (255,180,0))
    draw.line([(0,72),(800,72)], fill=BORDER, width=1)

    y = 82
    if not warnings:
        draw.text((20, y+10), "Heç bir xəbərdarlıq yoxdur.", font=fs, fill=GRAY)
    else:
        for i, w in enumerate(warnings):
            bg = (35,20,20) if i%2==0 else PANEL
            draw.rectangle([(0,y),(800,y+ROW_H)], fill=bg)
            dt = datetime.datetime.utcfromtimestamp(w["created_at"]) + datetime.timedelta(hours=4)
            draw.text((20, y+6),  f"#{i+1} — {w['reason'][:60]}", font=fs, fill=WHITE)
            draw.text((20, y+28), dt.strftime("%d.%m.%Y %H:%M"), font=fx, fill=GRAY)
            y += ROW_H

    draw.text((20, H-24), "Calestify Gaming Community", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


# ── NAİLİYYƏTLƏR KARTI ───────────────────────────────────────────────────────
def generate_achievements_card(nick: str, achievements: list, output_path: str):
    COLS   = 3
    CELL_H = 70
    HEADER = 72
    FOOTER = 30
    rows   = max(1, (len(achievements) + COLS - 1) // COLS)
    H      = HEADER + rows * CELL_H + FOOTER
    W      = 800

    img  = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    draw.rectangle([(0,0),(W-1,H-1)], outline=GOLD, width=2)

    fb = _font(13, True)
    ft = _font(22, True)
    fs = _font(13)
    fx = _font(11)

    draw.text((20, 12), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((20, 28), f"{nick} — Nailiyyətlər ({len(achievements)})", font=ft, fill=WHITE)
    draw.line([(0,68),(W,68)], fill=BORDER, width=1)

    CW = W // COLS
    for idx, ach in enumerate(achievements):
        row, col = divmod(idx, COLS)
        cx = col * CW
        cy = HEADER + row * CELL_H
        bg = (24,22,30) if (row+col)%2==0 else PANEL
        draw.rectangle([(cx, cy),(cx+CW, cy+CELL_H)], fill=bg, outline=BORDER, width=1)
        draw.text((cx+10, cy+8),  ach['name'], font=fs, fill=GOLD)
        draw.text((cx+10, cy+30), ach.get("description","")[:35], font=fx, fill=GRAY)
        dt = datetime.datetime.utcfromtimestamp(ach["earned_at"]) + datetime.timedelta(hours=4)
        draw.text((cx+10, cy+48), dt.strftime("%d.%m.%Y"), font=fx, fill=(80,80,100))

    if not achievements:
        draw.text((20, HEADER+10), "Hələ heç bir nailiyyət yoxdur.", font=fs, fill=GRAY)

    draw.text((20, H-24), "Calestify Gaming Community", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


# ── OYUNCU MUQAYİSƏ KARTI ────────────────────────────────────────────────────
def generate_compare_card(p1: dict, p2: dict, output_path: str):
    """p1, p2: {nick, elo, wins, losses, kills, deaths, assists, win_streak, peak_elo}"""
    W, H = 860, 400
    PAD  = 20
    img  = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    draw.rectangle([(0,0),(W-1,H-1)], outline=GOLD, width=2)

    fb = _font(13, True); ft = _font(22, True)
    fm = _font(15, True); fs = _font(13); fx = _font(11)

    draw.text((PAD, 12), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((PAD, 28), "OYUNCU MUQAYİSƏSİ", font=ft, fill=WHITE)
    draw.line([(0,70),(W,70)], fill=BORDER, width=1)

    # Orta xətt
    mid = W // 2
    draw.line([(mid, 70),(mid, H-30)], fill=BORDER, width=2)

    # Nick-lər
    draw.text((mid//2, 80), p1["nick"][:16], font=fm, fill=BLUE, anchor="mm")
    draw.text((mid + mid//2, 80), p2["nick"][:16], font=fm, fill=RED, anchor="mm")

    STATS = [
        ("ELO",    "elo",        False),
        ("Pik ELO","peak_elo",   False),
        ("Win %",  None,         False),
        ("K/D",    None,         False),
        ("Kill",   "kills",      False),
        ("Asist",  "assists",    False),
        ("Olum",   "deaths",     True),   # az yaxshidır (reverse)
        ("Streak", "win_streak", False),
        ("Qelebə", "wins",       False),
    ]

    y = 108
    for lbl, key, reverse in STATS:
        if key:
            v1 = p1.get(key, 0)
            v2 = p2.get(key, 0)
        elif lbl == "Win %":
            m1 = p1.get("wins",0)+p1.get("losses",0)
            m2 = p2.get("wins",0)+p2.get("losses",0)
            v1 = round(p1.get("wins",0)/max(m1,1)*100,1)
            v2 = round(p2.get("wins",0)/max(m2,1)*100,1)
        else:  # K/D
            v1 = round(p1.get("kills",0)/max(p1.get("deaths",1),1),2)
            v2 = round(p2.get("kills",0)/max(p2.get("deaths",1),1),2)

        # Rəng: üstün olan yaşıl
        if v1 != v2:
            c1 = GREEN if (v1 > v2) != reverse else RED
            c2 = GREEN if (v2 > v1) != reverse else RED
        else:
            c1 = c2 = GRAY

        draw.text((mid//2,   y), str(v1), font=fs, fill=c1, anchor="mm")
        draw.text((mid,      y), lbl,     font=fx, fill=GRAY, anchor="mm")
        draw.text((mid+mid//2, y), str(v2), font=fs, fill=c2, anchor="mm")
        draw.line([(PAD, y+12),(W-PAD, y+12)], fill=(35,33,42), width=1)
        y += 28

    draw.text((PAD, H-24), "Calestify Gaming Community", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


# ── ELO QRAFİK KARTI ──────────────────────────────────────────────────────────
def generate_elo_graph(nick: str, history: list, peak_elo: int, output_path: str):
    """
    history: [(elo, recorded_at), ...] köhnədən yeniyə
    """
    W, H    = 820, 340
    PAD     = 50
    GW      = W - PAD*2
    GH      = H - PAD - 60

    img  = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y/H
        c = tuple(int(BG_TOP[i]+(BG_BOTTOM[i]-BG_TOP[i])*t) for i in range(3))
        draw.line([(0,y),(W,y)], fill=c)
    draw.rectangle([(0,0),(W-1,H-1)], outline=BORDER, width=2)

    fb = _font(13, True); ft = _font(20, True); fx = _font(10)

    draw.text((PAD, 12), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((PAD, 28), f"{nick} — ELO Tarixi  |  Pik: {peak_elo}", font=ft, fill=WHITE)

    if len(history) < 2:
        draw.text((W//2, H//2), "Kifayet data yoxdur", font=fb, fill=GRAY, anchor="mm")
        img.save(output_path)
        return output_path

    elos = [h[0] for h in history]
    mn, mx = min(elos), max(elos)
    if mn == mx:
        mn -= 50; mx += 50
    rang = mx - mn

    # Qrafik çərçivəsi
    ox, oy = PAD, 60
    draw.rectangle([(ox, oy),(ox+GW, oy+GH)], outline=(50,48,58), width=1)

    # Y xətləri
    for step in range(0, 5):
        yval = mn + rang * step / 4
        ypos = oy + GH - int(GH * step / 4)
        draw.line([(ox, ypos),(ox+GW, ypos)], fill=(40,38,50), width=1)
        draw.text((ox-5, ypos), str(int(yval)), font=fx, fill=GRAY, anchor="rm")

    # Qrafik xətti
    pts = []
    for i, (elo, _) in enumerate(history):
        px = ox + int(GW * i / (len(history)-1))
        py = oy + GH - int(GH * (elo - mn) / rang)
        pts.append((px, py))

    for i in range(len(pts)-1):
        col = GREEN if pts[i+1][1] <= pts[i][1] else RED
        draw.line([pts[i], pts[i+1]], fill=col, width=2)

    # Başlanğıc + Son nöqtə
    draw.ellipse([(pts[0][0]-4, pts[0][1]-4),(pts[0][0]+4, pts[0][1]+4)], fill=GRAY)
    draw.ellipse([(pts[-1][0]-5, pts[-1][1]-5),(pts[-1][0]+5, pts[-1][1]+5)], fill=GOLD)
    draw.text((pts[-1][0]+8, pts[-1][1]), str(elos[-1]), font=fx, fill=GOLD)

    draw.text((PAD, H-24), "Calestify Gaming Community", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


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
    draw.text((20, 12), "CALESTIFY", font=fb, fill=GOLD)
    draw.text((20, 28), f"FEALIYYET PANELİ — Son {days} Gun", font=ft, fill=WHITE)
    draw.line([(0,70),(W,70)], fill=BORDER, width=1)

    # Böyük rəqəmlər
    boxes = [
        (stats["match_count"], "Matc"),
        (stats["player_count"], "Oyuncu"),
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
        draw.text((280, 198 + i*22), f"{cnt} matc", font=fs, fill=GRAY)

    # Saatlıq aktivlik mini-qrafik
    if hourly and len(hourly) > 0:
        gy = 310
        draw.text((20, gy), "Saatliq fealiyyet:", font=fs, fill=WHITE)
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

    draw.text((20, H-24), "Calestify Gaming Community", font=fx, fill=GRAY)
    img.save(output_path)
    return output_path


# ── iNVENTAR ────────────────────────────────────────────────────────────────

def generate_inventory_card(owned_ids, active_banner, active_frame, skin_inv, get_item_by_id_fn, output_path):
    ROW_H    = 46
    SEC_H    = 34
    HEADER_H = 78
    FOOTER_H = 18

    faceit = [(iid, get_item_by_id_fn(iid)) for iid in owned_ids if get_item_by_id_fn(iid)]
    skins  = list(skin_inv[:20])
    total  = max(1, len(faceit) + len(skins))
    secs   = (1 if faceit else 0) + (1 if skins else 0)
    height = HEADER_H + secs * SEC_H + total * ROW_H + FOOTER_H

    img  = _bg(height)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (WIDTH-1, height-1)], outline=BORDER, width=2)

    f_brand = _font(12, True)
    f_title = _font(22, True)
    f_sec   = _font(14, True)
    f_row   = _font(15, True)
    f_sm    = _font(13)

    draw.text((28, 14), "CALESTIFY", font=f_brand, fill=GOLD)
    draw.text((28, 30), "iNVENTAR",  font=f_title, fill=WHITE)
    tot_t = f"{len(faceit)+len(skins)} esya"
    draw.text((WIDTH-28-_tw(draw, tot_t, f_sm), 40), tot_t, font=f_sm, fill=GRAY)
    draw.line([(18, HEADER_H-6), (WIDTH-18, HEADER_H-6)], fill=BORDER, width=1)

    y = HEADER_H

    if not faceit and not skins:
        draw.text((28, y+14), "Inventariniz bosdur.", font=f_sm, fill=GRAY)
    else:
        if faceit:
            draw.rectangle([(0, y), (WIDTH, y+SEC_H)], fill=(28, 26, 34))
            draw.text((28, y+8), "FACEIT MARKET ESYALARI", font=f_sec, fill=GOLD)
            y += SEC_H
            for i, (iid, item) in enumerate(faceit):
                if i % 2 == 0:
                    draw.rectangle([(2, y), (WIDTH-2, y+ROW_H-1)], fill=(21, 19, 25))
                is_ab = iid == active_banner
                is_af = iid == active_frame
                is_a  = is_ab or is_af
                _bar(draw, 20, y, ROW_H, GREEN if is_a else BORDER)
                itype = item.get("type", "")
                tlbl  = "Cercive" if itype == "avatar_frame" else "Banner"
                albl  = "  AKTIV" if is_a else ""
                draw.text((40, y+8),  item.get("name", iid), font=f_row, fill=WHITE)
                draw.text((40, y+28), f"{tlbl}{albl}",       font=f_sm,  fill=GREEN if is_a else GRAY)
                pt = f"{item.get('price','?')} coin"
                draw.text((WIDTH-28-_tw(draw, pt, f_sm), y+18), pt, font=f_sm, fill=GRAY)
                draw.line([(18, y+ROW_H-1), (WIDTH-18, y+ROW_H-1)], fill=BORDER, width=1)
                y += ROW_H

        if skins:
            draw.rectangle([(0, y), (WIDTH, y+SEC_H)], fill=(28, 26, 34))
            draw.text((28, y+8), "STANDOFF 2 SKiNLERi", font=f_sec, fill=BLUE)
            y += SEC_H
            for j, skin in enumerate(skins):
                if j % 2 == 0:
                    draw.rectangle([(2, y), (WIDTH-2, y+ROW_H-1)], fill=(21, 19, 25))
                _bar(draw, 20, y, ROW_H, BLUE)
                draw.text((40, y+8),  skin["skin_name"], font=f_row, fill=WHITE)
                dt  = datetime.datetime.utcfromtimestamp(skin["acquired_at"]) + datetime.timedelta(hours=4)
                draw.text((40, y+28), f"Alinma: {dt.strftime('%d.%m.%Y')}", font=f_sm, fill=GRAY)
                pt = f"{skin['price_paid']} coin"
                draw.text((WIDTH-28-_tw(draw, pt, f_sm), y+18), pt, font=f_sm, fill=GRAY)
                if j < len(skins)-1:
                    draw.line([(18, y+ROW_H-1), (WIDTH-18, y+ROW_H-1)], fill=BORDER, width=1)
                y += ROW_H

    draw.text((28, height-FOOTER_H+4), "Calestify Gaming Community", font=_font(11), fill=GRAY)
    img.save(output_path)
    return output_path
