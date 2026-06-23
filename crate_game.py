from PIL import Image, ImageDraw, ImageFont
import os
import random
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES_BOLD = [
    os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_CANDIDATES_REGULAR = [
    os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

def _font(size, bold=False):
    for path in (FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()

# ── Rarity sistemi ────────────────────────────────────────────────────────────
RARITIES = {
    "common":    {"label": "ADI",      "color": (148, 148, 148), "bg": (38, 38, 42),   "glow": (180, 180, 180), "weight": 45, "stars": 1},
    "uncommon":  {"label": "UNCOMMON", "color": (82, 122, 255),  "bg": (20, 28, 70),   "glow": (100, 140, 255), "weight": 25, "stars": 2},
    "rare":      {"label": "NADİR",    "color": (148, 80, 255),  "bg": (40, 18, 80),   "glow": (180, 100, 255), "weight": 16, "stars": 3},
    "epic":      {"label": "EPİK",     "color": (220, 60, 180),  "bg": (70, 15, 60),   "glow": (255, 80, 200),  "weight": 10, "stars": 4},
    "legendary": {"label": "ƏFSANƏVI", "color": (255, 200, 0),   "bg": (65, 48, 0),    "glow": (255, 220, 60),  "weight": 4,  "stars": 5},
}

CRATE_ITEMS = [
    # Legendary
    {"name": "AK-47",        "skin": "Redline",        "rarity": "legendary"},
    {"name": "AWP",          "skin": "Dragon Lore",    "rarity": "legendary"},
    {"name": "M4A1-S",       "skin": "Hyper Beast",    "rarity": "legendary"},
    # Epic
    {"name": "Desert Eagle", "skin": "Blaze",          "rarity": "epic"},
    {"name": "USP-S",        "skin": "Kill Confirmed", "rarity": "epic"},
    {"name": "Glock-18",     "skin": "Fade",           "rarity": "epic"},
    {"name": "M4A4",         "skin": "Howl",           "rarity": "epic"},
    # Rare
    {"name": "AK-47",        "skin": "Vulcan",         "rarity": "rare"},
    {"name": "AWP",          "skin": "Asiimov",        "rarity": "rare"},
    {"name": "P90",          "skin": "Death by Kitty", "rarity": "rare"},
    {"name": "MAC-10",       "skin": "Neon Rider",     "rarity": "rare"},
    {"name": "MP5-SD",       "skin": "Phosphor",       "rarity": "rare"},
    # Uncommon
    {"name": "FAMAS",        "skin": "Meltdown",       "rarity": "uncommon"},
    {"name": "Galil AR",     "skin": "Chatterbox",     "rarity": "uncommon"},
    {"name": "Nova",         "skin": "Bloomstick",     "rarity": "uncommon"},
    {"name": "MP7",          "skin": "Skulls",         "rarity": "uncommon"},
    {"name": "SG 553",       "skin": "Integrale",      "rarity": "uncommon"},
    # Common
    {"name": "P250",         "skin": "Sand Dune",      "rarity": "common"},
    {"name": "Tec-9",        "skin": "Isaac",          "rarity": "common"},
    {"name": "Five-SeveN",   "skin": "Kami",           "rarity": "common"},
    {"name": "UMP-45",       "skin": "Urban DDPAT",    "rarity": "common"},
    {"name": "PP-Bizon",     "skin": "High Roller",    "rarity": "common"},
    {"name": "SSG 08",       "skin": "Slashed",        "rarity": "common"},
    {"name": "MP9",          "skin": "Setting Sun",    "rarity": "common"},
]

def pick_winner() -> dict:
    population = []
    weights = []
    for item in CRATE_ITEMS:
        population.append(item)
        weights.append(RARITIES[item["rarity"]]["weight"])
    return random.choices(population, weights=weights, k=1)[0]

def build_reel(winner: dict, reel_size: int = 24, winner_idx: int = 17) -> list:
    """Reel yaradır: winner-i winner_idx mövqeyinə qoyur, qalanları random doldurur."""
    population = [i for i in CRATE_ITEMS if i != winner]
    weights = [RARITIES[i["rarity"]]["weight"] for i in population]
    filler = random.choices(population, weights=weights, k=reel_size)
    reel = list(filler)
    reel[winner_idx] = winner
    return reel

# ── GIF generasiyası ──────────────────────────────────────────────────────────
CARD_STEP = 114      # card + gap
CARD_W    = 110
CARD_H    = 210
CANVAS_W  = 7 * CARD_STEP   # 798
CANVAS_H  = 310
REEL_Y    = (CANVAS_H - CARD_H) // 2   # vertical center

WINNER_IDX   = 17
TARGET_OFFSET = WINNER_IDX * CARD_STEP + CARD_W // 2 - CANVAS_W // 2

TOTAL_FRAMES = 52


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 4


def _draw_card(draw, x, y, item, rarity_info, highlight=False):
    r = rarity_info
    border_w = 3 if not highlight else 5
    border_col = r["glow"] if highlight else r["color"]
    # Shadow
    draw.rectangle([x + 3, y + 3, x + CARD_W + 3, y + CARD_H + 3], fill=(0, 0, 0, 100))
    # Card bg
    draw.rectangle([x, y, x + CARD_W, y + CARD_H], fill=r["bg"], outline=border_col, width=border_w)

    # Rarity stripe at top
    stripe_h = 6
    draw.rectangle([x + border_w, y + border_w, x + CARD_W - border_w, y + border_w + stripe_h], fill=r["color"])

    # Weapon icon placeholder (stylised gun silhouette shape via rectangles)
    ic_x, ic_y, ic_w, ic_h = x + 12, y + 28, CARD_W - 24, 80
    draw.rectangle([ic_x, ic_y + ic_h // 2 - 6, ic_x + ic_w, ic_y + ic_h // 2 + 6], fill=r["color"], outline=r["glow"], width=1)
    draw.rectangle([ic_x + 4, ic_y + ic_h // 2 - 14, ic_x + ic_w - 20, ic_y + ic_h // 2 - 6], fill=r["color"])
    draw.rectangle([ic_x + ic_w - 14, ic_y + ic_h // 2 + 6, ic_x + ic_w + 2, ic_y + ic_h // 2 + 18], fill=r["color"])

    # Weapon name (top line)
    fn_bold_14 = _font(13, bold=True)
    fn_reg_11  = _font(11)
    fn_tiny    = _font(10, bold=True)

    center_x = x + CARD_W // 2
    draw.text((center_x, y + 122), item["name"],  font=fn_bold_14, fill=(230, 230, 230), anchor="mm")
    draw.text((center_x, y + 140), f"| {item['skin']} |", font=fn_reg_11,  fill=r["color"],  anchor="mm")

    # Stars
    stars = r["stars"]
    star_str = "★" * stars + "☆" * (5 - stars)
    draw.text((center_x, y + 158), star_str, font=fn_tiny, fill=r["glow"], anchor="mm")

    # Rarity label bar at bottom
    bar_y = y + CARD_H - 26
    draw.rectangle([x + border_w, bar_y, x + CARD_W - border_w, y + CARD_H - border_w], fill=r["color"])
    draw.text((center_x, bar_y + 12), r["label"], font=fn_tiny, fill=(15, 12, 20), anchor="mm")


def _draw_frame(reel, offset, highlight_winner=False):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), (14, 12, 18))
    draw = ImageDraw.Draw(img)

    # Subtle grid lines
    for gx in range(0, CANVAS_W, CARD_STEP):
        draw.line([(gx, 0), (gx, CANVAS_H)], fill=(25, 22, 30), width=1)

    for ci, item in enumerate(reel):
        x = ci * CARD_STEP - offset
        if -CARD_STEP <= x <= CANVAS_W + CARD_STEP:
            is_center = ci == WINNER_IDX and highlight_winner
            _draw_card(draw, x, REEL_Y, item, RARITIES[item["rarity"]], highlight=is_center)

    # Center indicator: two golden triangles top & bottom + side lines
    cx = CANVAS_W // 2
    half = CARD_W // 2 + 3
    tri_size = 14
    # top arrow
    draw.polygon([(cx - tri_size, 0), (cx + tri_size, 0), (cx, tri_size)], fill=(255, 200, 0))
    # bottom arrow
    draw.polygon([(cx - tri_size, CANVAS_H), (cx + tri_size, CANVAS_H), (cx, CANVAS_H - tri_size)], fill=(255, 200, 0))
    # side lines
    draw.rectangle([cx - half, 0, cx - half + 2, CANVAS_H], fill=(255, 200, 0))
    draw.rectangle([cx + half - 2, 0, cx + half, CANVAS_H], fill=(255, 200, 0))

    # Fade masks (left & right edges for depth)
    fade_w = 90
    for px in range(fade_w):
        alpha = int(200 * (1 - px / fade_w))
        draw.line([(px, 0), (px, CANVAS_H)], fill=(14, 12, 18, alpha))
        draw.line([(CANVAS_W - 1 - px, 0), (CANVAS_W - 1 - px, CANVAS_H)], fill=(14, 12, 18, alpha))

    return img


def generate_crate_gif(winner: dict, reel: list, output_path: str):
    frames = []
    durations = []

    for fi in range(TOTAL_FRAMES):
        t = fi / (TOTAL_FRAMES - 1)
        eased = _ease_out(t)
        offset = int(eased * TARGET_OFFSET)
        highlight = fi >= TOTAL_FRAMES - 4
        frame = _draw_frame(reel, offset, highlight_winner=highlight)
        frames.append(frame)

        # Duration: fast start → slow end
        if t < 0.55:
            durations.append(35)
        elif t < 0.75:
            durations.append(55)
        elif t < 0.88:
            durations.append(90)
        else:
            durations.append(160)

    # 2 extra hold frames at end
    for _ in range(2):
        frames.append(frames[-1])
        durations.append(700)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=durations,
        optimize=False,
    )


def generate_result_card(winner: dict, output_path: str):
    """Qazanılan skini göstərən statik kart."""
    W, H = 500, 200
    r = RARITIES[winner["rarity"]]

    img = Image.new("RGB", (W, H), (14, 12, 18))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W - 1, H - 1)], outline=r["glow"], width=3)
    draw.rectangle([(0, 0), (W, 8)], fill=r["color"])
    draw.rectangle([(0, H - 8), (W, H)], fill=r["color"])

    fn_big   = _font(28, bold=True)
    fn_med   = _font(18)
    fn_small = _font(13, bold=True)
    fn_tiny  = _font(11)

    cx = W // 2
    draw.text((cx, 50), "🎉  QAZANDINIz!", font=fn_small, fill=r["glow"], anchor="mm")
    draw.text((cx, 90), winner["name"], font=fn_big, fill=(240, 238, 230), anchor="mm")
    draw.text((cx, 125), f"| {winner['skin']} |", font=fn_med, fill=r["color"], anchor="mm")
    stars = "★" * r["stars"] + "☆" * (5 - r["stars"])
    draw.text((cx, 152), stars, font=fn_small, fill=r["glow"], anchor="mm")
    draw.text((cx, 175), r["label"], font=fn_tiny, fill=r["color"], anchor="mm")

    img.save(output_path)
