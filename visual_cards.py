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
