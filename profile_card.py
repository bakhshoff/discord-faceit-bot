from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import os
import io
import math
from i18n import t


def _finalize(img):
    """Whole-image polish pass: 2x upscale+downscale smooths jagged shape edges, then a mild
    sharpen recovers text crispness."""
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(img).enhance(1.15)


WIDTH  = 900
HEIGHT = 540

BG_TOP    = (14, 11, 20)
BG_BOTTOM = (7,  6, 11)
PANEL     = (20, 17, 28)
PANEL2    = (26, 22, 34)
BORDER    = (50, 43, 68)
GOLD      = (138, 92, 230)
SILVER    = (186, 178, 202)
WHITE     = (244, 241, 234)
GRAY      = (150, 142, 168)
GREEN     = (88, 200, 110)
RED       = (210, 65, 58)
BLUE      = (80, 150, 230)
CYAN      = (60, 200, 200)
PURPLE    = (160, 90, 255)

# achievement_id -> (qısa etiket, dairə rəngi) — emoji fontda render olunmadığı üçün
# (DejaVuSans-da rəngli emoji glyph-ı yoxdur) hər nişan kiçik rəngli dairə + qısa hərf/rəqəm
# kimi göstərilir (bax: _draw_badges, generate_profile_card-ın `badges` parametri).
BADGE_DISPLAY = {
    "first_match": ("M1", (95, 208, 122)),
    "win_10":      ("W10", (210, 170, 60)),
    "win_50":      ("W50", (230, 190, 40)),
    "kill_50":     ("K50", (190, 100, 90)),
    "kill_100":    ("K1C", (205, 75, 75)),
    "kill_500":    ("K5C", (220, 50, 50)),
    "mvp_3":       ("M3", (210, 170, 230)),
    "mvp_10":      ("M10", (230, 190, 250)),
    "streak_3":    ("S3", (230, 140, 40)),
    "streak_5":    ("S5", (230, 110, 30)),
    "streak_10":   ("S10", (230, 80, 20)),
    "kd_2":        ("KD", (120, 150, 230)),
    "task_10":     ("T10", (150, 200, 150)),
    "elo_1200":    ("E12", (90, 200, 230)),
    "elo_1500":    ("E15", (160, 120, 255)),
}

FONT_CANDIDATES_REGULAR = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

LEVELS = [
    (0,    800,  1,  (122, 122, 122)),
    (800,  900,  2,  (122, 122, 122)),
    (900,  1000, 3,  (255, 193, 87)),
    (1000, 1100, 4,  (255, 193, 87)),
    (1100, 1200, 5,  (255, 140, 60)),
    (1200, 1300, 6,  (255, 140, 60)),
    (1300, 1450, 7,  (255, 90,  90)),
    (1450, 1600, 8,  (255, 90,  90)),
    (1600, 1800, 9,  (180, 110, 255)),
    (1800, 99999,10, (255, 215, 0)),
]


def _load_font(size, bold=False):
    for path in (FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def get_level_info(elo):
    for low, high, level, color in LEVELS:
        if low <= elo < high:
            return level, color
    return 10, LEVELS[-1][3]


def _make_circular_avatar(avatar_bytes, size):
    img  = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    img  = ImageOps.fit(img, (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _gradient(width, height, top, bottom):
    img  = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        c = tuple(int(top[i] + (bottom[i]-top[i])*t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=c)
    return img


def _section(draw, x, y, w, h, title, title_color=GOLD):
    draw.rectangle([x, y, x+w, y+h], fill=PANEL, outline=BORDER, width=1)
    draw.rectangle([x, y, x+w, y+22], fill=PANEL2)
    draw.text((x+8, y+4), title, font=_load_font(11, bold=True), fill=title_color)


def _stat_box(draw, x, y, w, h, label, value, val_color=WHITE, label_color=GRAY):
    draw.rectangle([x, y, x+w, y+h], fill=PANEL, outline=BORDER, width=1)
    draw.text((x + w//2, y + h//2 - 10), str(value),
              font=_load_font(20, bold=True), fill=val_color, anchor="mm")
    draw.text((x + w//2, y + h - 12), label,
              font=_load_font(10, bold=True), fill=label_color, anchor="mm")


def generate_profile_card(nick, so2_id, elo, wins, losses, avatar_bytes=None,
                          output_path="profile_card.png", banner_path=None,
                          coins=0, frame_path=None, zm_balance=0,
                          kills=0, assists=0, deaths=0,
                          season_wins=0, season_losses=0,
                          season_kills=0, season_assists=0, season_deaths=0,
                          pass_status=None, pass_level=0,
                          theme_colors=None, show_season=False, title=None, lang="az",
                          badges=None):

    # ── Banner kadrları ─────────────────────────────────────────────────────
    # Banner animasiyalı GIF-dirsə (bax: market_assets.py-dəki ANIMATED_BANNER_DEFS),
    # kartın ÖZÜ də animasiyalı GIF kimi çıxarılır — hər banner kadrı üçün bütün kart
    # (avatar/stats/mətn) yenidən çəkilir (bax: _render_frame aşağıda) və nəticə GIF
    # kimi yığılır. Statik banner/bannersiz halda eynən əvvəlki kimi tək PNG qalır.
    MAX_ANIM_FRAMES = 10
    banner_images = []
    durations = []
    if banner_path and os.path.exists(banner_path):
        try:
            raw = Image.open(banner_path)
            is_gif_anim = (
                (getattr(raw, "is_animated", False) or banner_path.lower().endswith(".gif"))
                and getattr(raw, "n_frames", 1) > 1
            )
            if is_gif_anim:
                n = raw.n_frames
                step = max(1, n // MAX_ANIM_FRAMES)
                indices = list(range(0, n, step))[:MAX_ANIM_FRAMES]
                for idx in indices:
                    raw.seek(idx)
                    banner_images.append(raw.convert("RGB"))
                    durations.append(raw.info.get("duration", 70))
            else:
                banner_images.append(raw.convert("RGB"))
        except Exception:
            banner_images = []
    if not banner_images:
        banner_images = [None]  # bannersiz/xəta — gradient fallback-a işarədir

    # ── Kadrdan asılı olmayan hesablamalar (bir dəfə) ────────────────────────
    t_accent = theme_colors.get("accent", GOLD)   if theme_colors else GOLD
    t_panel  = theme_colors.get("panel",  PANEL)  if theme_colors else PANEL
    t_border = theme_colors.get("border", BORDER) if theme_colors else BORDER
    t_text2  = theme_colors.get("text2",  GRAY)   if theme_colors else GRAY

    level, level_color = get_level_info(elo)
    matches        = wins + losses
    wr             = round(wins/matches*100, 1) if matches > 0 else 0.0
    s_matches      = season_wins + season_losses
    s_wr           = round(season_wins/s_matches*100, 1) if s_matches > 0 else 0.0
    kd             = round(kills/deaths, 2) if deaths > 0 else float(kills)
    season_kd      = round(season_kills/season_deaths, 2) if season_deaths > 0 else float(season_kills)

    f_brand  = _load_font(13, bold=True)
    f_title  = _load_font(20, bold=True)
    f_nick   = _load_font(30, bold=True)
    f_id     = _load_font(13)
    f_lvl    = _load_font(18, bold=True)
    f_elo    = _load_font(38, bold=True)
    f_elolbl = _load_font(12, bold=True)
    f_coin   = _load_font(16, bold=True)
    f_small  = _load_font(11)

    av_size, av_x, av_y = 130, 28, 82
    av = None
    if avatar_bytes:
        try:
            av = _make_circular_avatar(avatar_bytes, av_size)
        except Exception:
            av = None

    fr = None
    if frame_path and os.path.exists(frame_path):
        try:
            fr = Image.open(frame_path).convert("RGBA")
        except Exception:
            fr = None

    def _render_frame(banner_img):
        if banner_img is not None:
            bi  = ImageOps.fit(banner_img, (WIDTH, HEIGHT), Image.LANCZOS)
            ov  = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
            img = Image.blend(bi, ov, 0.40)
        else:
            img = _gradient(WIDTH, HEIGHT, BG_TOP, BG_BOTTOM)

        img  = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        draw.rectangle([(0,0),(WIDTH-1,HEIGHT-1)], outline=t_accent, width=2)
        # Üst rəngli şerid
        draw.rectangle([(0,0),(WIDTH,4)], fill=t_accent)

        # ── Header şerid ─────────────────────────────────────────────────────────
        draw.text((28, 18), "Nextlevelaz", font=f_brand, fill=t_accent)
        draw.text((28, 34), t("profile.header", lang), font=f_title, fill=WHITE)

        # Coin + AZN (sağ üst)
        coin_text = str(coins)
        bbox = draw.textbbox((0,0), coin_text, font=f_coin)
        tw = bbox[2]-bbox[0]
        ccd = 14
        draw.ellipse([(WIDTH-28-tw-ccd-6, 20), (WIDTH-28-tw-6, 20+ccd)], fill=t_accent)
        draw.text((WIDTH-28-tw, 18), coin_text, font=f_coin, fill=t_accent)
        zm_val  = round(float(zm_balance or 0), 2)
        zm_text = f"{zm_val:.1f} AZN"
        bbox_zm = draw.textbbox((0,0), zm_text, font=f_coin)
        draw.text((WIDTH-28-(bbox_zm[2]-bbox_zm[0]), 38), zm_text, font=f_coin, fill=(80,200,120))

        # ── Avatar ────────────────────────────────────────────────────────────────
        if av is not None:
            img.paste(av, (av_x, av_y), av)
        else:
            draw.ellipse([(av_x, av_y),(av_x+av_size, av_y+av_size)], fill=PANEL, outline=BORDER, width=2)

        # Çərçivə / level halqası
        if fr is not None:
            fx  = av_x + av_size//2 - fr.width//2
            fy  = av_y + av_size//2 - fr.height//2
            img.alpha_composite(fr, (fx, fy))
        else:
            _ring(draw, av_x, av_y, av_size, level_color)

        # Level badge
        bs = 40
        bx, by = av_x + av_size - bs + 12, av_y + av_size - bs + 12
        draw.ellipse([(bx,by),(bx+bs,by+bs)], fill=level_color, outline=BG_BOTTOM, width=3)
        lt = str(level)
        bbox = draw.textbbox((0,0), lt, font=f_lvl)
        draw.text((bx+bs/2-(bbox[2]-bbox[0])/2, by+bs/2-(bbox[3]-bbox[1])/2-2), lt,
                  font=f_lvl, fill=(20,18,22))

        # ── Nick + ID + Level ─────────────────────────────────────────────────────
        tx = av_x + av_size + 26
        draw.text((tx, 90),  nick[:24],              font=f_nick,   fill=WHITE)
        if title:
            nick_bbox = draw.textbbox((tx, 90), nick[:24], font=f_nick)
            draw.text((nick_bbox[2] + 12, 100), f"« {title[:20]} »", font=f_id, fill=GOLD)
        draw.text((tx, 130), t("profile.so2id", lang, id=so2_id),   font=f_id,     fill=GRAY)
        rank_key = next((k for lo,hi,k in _rank_ranges if lo<=elo<hi), "rank.zenith")
        rank_name = t(rank_key, lang)
        draw.text((tx, 150), t("profile.level_rank", lang, level=level, rank=rank_name), font=f_elolbl, fill=level_color)

        # ── Battle Pass badge ────────────────────────────────────────────────────
        if pass_status in ("free", "premium"):
            is_vip = pass_status == "premium"
            badge_bg   = (40, 28, 0)   if is_vip else (20, 20, 30)
            badge_bdr  = GOLD          if is_vip else (80, 80, 100)
            badge_txt  = f"VIP PASS  Lv.{pass_level}"  if is_vip else f"FREE PASS  Lv.{pass_level}"
            badge_col  = GOLD          if is_vip else (140, 140, 160)
            star_col   = GOLD          if is_vip else (80, 80, 100)

            f_badge = _load_font(11, bold=True)
            tb = draw.textbbox((0,0), badge_txt, font=f_badge)
            bw2 = (tb[2]-tb[0]) + 28
            bh2 = 20
            bx2, by2 = tx, 172

            draw.rounded_rectangle([(bx2, by2),(bx2+bw2, by2+bh2)],
                                   radius=4, fill=badge_bg, outline=badge_bdr, width=1)
            # Star icon (premium: gold, free: muted)
            sx, sy = bx2 + 9, by2 + bh2//2
            star = [(sx,sy-5),(sx+2,sy-2),(sx+5,sy-2),(sx+3,sy),(sx+4,sy+4),
                    (sx,sy+2),(sx-4,sy+4),(sx-3,sy),(sx-5,sy-2),(sx-2,sy-2)]
            draw.polygon(star, fill=star_col)
            draw.text((bx2 + 18, by2 + bh2//2), badge_txt, font=f_badge, fill=badge_col, anchor="lm")

        # ELO (sağda)
        ex = WIDTH - 220
        draw.text((ex, 82),  t("profile.elo", lang),    font=f_elolbl, fill=GRAY)
        draw.text((ex, 98),  str(elo), font=f_elo,    fill=t_accent)
        draw.text((ex, 140), f"{t('profile.kd', lang)}: {kd}", font=f_elolbl, fill=t_text2)

        # ── Ayırıcı 1 ─────────────────────────────────────────────────────────────
        # Ümumi statistika (ÜMUMİ paneli + Kill/Asist/Ölüm/K-D qutuları) qəsdən BURADA
        # çəkilmir — bu, bannerin orta-aşağı hissəsini tamamilə örtürdü. Həmin məlumat
        # "Stats" düyməsinin öz kartında (generate_stats_card, visual_cards.py) onsuz da
        # tam göstərilir. Burada yalnız yuxarıdakı yığcam profil zolağı qalır, qalan
        # bütün kart (aşağı ~2/3) banner üçün tam açıqdır.

        # ── Nişanlar (bax: database.get_player_achievements, BADGE_DISPLAY) ────────
        # Emoji DejaVuSans-da render olunmur (rəngli glyph yoxdur), ona görə hər nişan
        # kiçik rəngli dairə + qısa hərf/rəqəm etiketi kimi göstərilir.
        if badges:
            bx, by, bsize, gap = 28, HEIGHT - 68, 28, 8
            f_badge_lbl = _load_font(9, bold=True)
            for bid in badges:
                label, bcolor = BADGE_DISPLAY.get(bid, (bid[:3].upper(), GRAY))
                if bx > WIDTH - 60:
                    break
                draw.ellipse([(bx, by), (bx + bsize, by + bsize)], fill=bcolor, outline=BG_BOTTOM, width=2)
                draw.text((bx + bsize / 2, by + bsize / 2), label, font=f_badge_lbl, fill=(20, 18, 22), anchor="mm")
                bx += bsize + gap

        # ── Footer ────────────────────────────────────────────────────────────────
        draw.text((28, HEIGHT-26), "Nextlevelaz", font=_load_font(11), fill=GRAY)
        draw.text((WIDTH-28, HEIGHT-26), "/stats → ətraflı statistika", font=_load_font(11), fill=t_text2, anchor="ra")

        img = img.convert("RGB")
        # Animasiyalı GIF-lərdə _finalize-in 2x upscale/downscale AA keçidi (hər kadr üçün
        # ~0.7s) buraxılır — GIF formatı onsuz da 256-rəng palitrəsinə sıxışdırılır (quantize),
        # ona görə əlavə hamarlama dəyəri azdır, sürət isə matçdan sonra /profile-ın tez
        # cavab verməsi üçün vacibdir. Statik (tək kadrlı) kartda keyfiyyət tam saxlanılır.
        if len(banner_images) > 1:
            return img
        return _finalize(img)

    _rank_ranges = [
        (0,900,"rank.spark1"),(900,1000,"rank.spark2"),(1000,1100,"rank.flame1"),(1100,1200,"rank.flame2"),
        (1200,1350,"rank.nova1"),(1350,1500,"rank.nova2"),(1500,1700,"rank.supernova"),(1700,9999,"rank.zenith"),
    ]

    frames = [_render_frame(b) for b in banner_images]

    if len(frames) > 1:
        gif_path = os.path.splitext(output_path)[0] + ".gif"
        frames[0].save(
            gif_path, format="GIF", save_all=True, append_images=frames[1:],
            duration=durations if durations else 70, loop=0
        )
        return gif_path

    frames[0].save(output_path)
    return output_path


def _ring(draw, av_x, av_y, av_size, color):
    pad = 5
    draw.ellipse([(av_x-pad, av_y-pad), (av_x+av_size+pad, av_y+av_size+pad)],
                 outline=color, width=4)


def _tw(draw, text, font):
    bb = draw.textbbox((0,0), text, font=font)
    return bb[2]-bb[0]
