from PIL import Image, ImageDraw, ImageFont
import os
import io
import random
import requests

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(os.environ.get("DATA_DIR", BASE_DIR), "skin_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

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
            pass
    return ImageFont.load_default()

# ── Rarity sistemi ─────────────────────────────────────────────────────────────
RARITIES = {
    "common":    {"label": "ADİ",      "color": (148, 148, 148), "bg": (32, 32, 36),  "glow": (190, 190, 190), "weight": 40, "stars": 1},
    "uncommon":  {"label": "UNCOMMON", "color": (70, 110, 255),  "bg": (18, 26, 70),  "glow": (100, 140, 255), "weight": 25, "stars": 2},
    "rare":      {"label": "NADİR",    "color": (148, 80, 255),  "bg": (35, 15, 75),  "glow": (180, 100, 255), "weight": 18, "stars": 3},
    "epic":      {"label": "EPİK",     "color": (210, 50, 170),  "bg": (65, 12, 55),  "glow": (255, 80, 200),  "weight": 12, "stars": 4},
    "legendary": {"label": "ƏFSANƏVI", "color": (255, 195, 0),   "bg": (60, 45, 0),   "glow": (255, 225, 60),  "weight": 5,  "stars": 5},
}

# ── Real Standoff 2 skinləri (Fandom Wiki CDN) ────────────────────────────────
CRATE_ITEMS = [
    # ── LEGENDARY ──────────────────────────────────────────────────────────────
    {"weapon": "AKR",          "skin": "Scylla",
     "rarity": "legendary",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/2/25/AKR_Scylla.jpg/revision/latest?cb=20240721162157"},
    {"weapon": "AWM",          "skin": "Poseidon",
     "rarity": "legendary",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/6/6d/AWM_Poseidon.jpg/revision/latest?cb=20240721161407"},
    {"weapon": "Karambit",     "skin": "DragonGlass",
     "rarity": "legendary",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/3/34/Karambit_DragonGlass.PNG/revision/latest?cb=20180918203118"},
    {"weapon": "Karambit",     "skin": "Ancient",
     "rarity": "legendary",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/3/35/Karambit_Ancient.png/revision/latest?cb=20181211210757"},
    {"weapon": "AWM",          "skin": "Daemon",
     "rarity": "legendary",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/d/dc/AWM_Daemon.png/revision/latest?cb=20181211210724"},

    # ── EPIC ───────────────────────────────────────────────────────────────────
    {"weapon": "AKR12",        "skin": "Carving",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/c/ca/AKR12_Carving.jpg/revision/latest?cb=20240721161225"},
    {"weapon": "AKR12",        "skin": "Railgun",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/0/08/AKR12_Railgun.PNG/revision/latest?cb=20180813195154"},
    {"weapon": "AWM",          "skin": "Phoenix",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/5/5b/AWM_Phoenix.PNG/revision/latest?cb=20180812172938"},
    {"weapon": "Desert Eagle", "skin": "RedDragon",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/6/6a/Desert_Eagle_RedDragon.PNG/revision/latest?cb=20180918193529"},
    {"weapon": "Karambit",     "skin": "Acid",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/9/96/Karambit_Acid.png/revision/latest?cb=20181211210733"},
    {"weapon": "M4",           "skin": "Pro",
     "rarity": "epic",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/9/94/M4_Pro.PNG/revision/latest?cb=20180918193909"},

    # ── RARE ───────────────────────────────────────────────────────────────────
    {"weapon": "AKR",          "skin": "Tiger",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/0/09/AKR_Tiger.PNG/revision/latest?cb=20180918173337"},
    {"weapon": "AWM",          "skin": "Gear",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/d/da/AWM_Gear.PNG/revision/latest?cb=20180918201124"},
    {"weapon": "Desert Eagle", "skin": "Predator",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/6/61/Desert_Eagle_Predator.PNG/revision/latest?cb=20180812173759"},
    {"weapon": "Desert Eagle", "skin": "Winner",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/e/ef/Desert_Eagle_Winner.PNG/revision/latest?cb=20180918190233"},
    {"weapon": "P90",          "skin": "Fissure",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/b/bc/P90_Fissure.PNG/revision/latest?cb=20180827162752"},
    {"weapon": "SM1014",       "skin": "Necromancer",
     "rarity": "rare",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/3/39/SM1014_Necromancer.PNG/revision/latest?cb=20180918201643"},

    # ── UNCOMMON ───────────────────────────────────────────────────────────────
    {"weapon": "AKR",          "skin": "Sport",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/0/0f/AKR_Sport.PNG/revision/latest?cb=20180918200158"},
    {"weapon": "AWM",          "skin": "Scratch",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/9/9b/AWM_Scratch.PNG/revision/latest?cb=20180918194254"},
    {"weapon": "FAMAS",        "skin": "Fury",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/e/e0/FAMAS_Fury.PNG/revision/latest?cb=20180918202209"},
    {"weapon": "UMP45",        "skin": "Shark",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/f/f3/UMP45_Shark.PNG/revision/latest?cb=20180918192900"},
    {"weapon": "UMP45",        "skin": "Winged",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/e/e9/UMP45_Winged.PNG/revision/latest?cb=20180918200644"},
    {"weapon": "M40",          "skin": "Quake",
     "rarity": "uncommon",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/f/f9/M40_Quake.PNG/revision/latest?cb=20180918194652"},

    # ── COMMON ─────────────────────────────────────────────────────────────────
    {"weapon": "AKR12",        "skin": "Desert Camouflage",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/7/7c/AKR12_DesertCamouflage.PNG/revision/latest?cb=20180812160317"},
    {"weapon": "AKR",          "skin": "Treasure Hunter",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/7/70/AKR_TreasureHunter.PNG/revision/latest?cb=20180813221317"},
    {"weapon": "AKR12",        "skin": "Mechanic",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/1/19/AKR12_Mechanic.PNG/revision/latest?cb=20180918191704"},
    {"weapon": "G22",          "skin": "Pattern",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/4/4e/G22_Pattern.PNG/revision/latest?cb=20180815152611"},
    {"weapon": "G22",          "skin": "Desert Camouflage",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/8/80/G22_Desert_Camouflage.PNG/revision/latest?cb=20180812145713"},
    {"weapon": "Desert Eagle", "skin": "Blood",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/0/01/Desert_Eagle_Blood.PNG/revision/latest?cb=20180812155105"},
    {"weapon": "G22",          "skin": "Bird",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/f/fe/G22_Bird.png/revision/latest?cb=20181211210710"},
    {"weapon": "M40",          "skin": "Pro",
     "rarity": "common",
     "img": "https://static.wikia.nocookie.net/standoff-2/images/5/56/M40_Pro.PNG/revision/latest?cb=20180918192434"},
]


def pick_winner() -> dict:
    weights = [RARITIES[i["rarity"]]["weight"] for i in CRATE_ITEMS]
    return random.choices(CRATE_ITEMS, weights=weights, k=1)[0]


def build_reel(winner: dict, reel_size: int = 24, winner_idx: int = 17) -> list:
    others = [i for i in CRATE_ITEMS if i is not winner]
    weights = [RARITIES[i["rarity"]]["weight"] for i in others]
    filler = random.choices(others, weights=weights, k=reel_size)
    reel = list(filler)
    reel[winner_idx] = winner
    return reel


# ── Resim indirme / önbellek ──────────────────────────────────────────────────
def _fetch_skin_image(url: str, target_w: int, target_h: int):
    """URL-dən skini endirir, cache-ə saxlayır, PIL Image qaytarır."""
    cache_name = url.split("/")[-2].replace("%20", "_") + ".png"
    cache_path = os.path.join(CACHE_DIR, cache_name)
    try:
        if os.path.exists(cache_path):
            img = Image.open(cache_path).convert("RGBA")
        else:
            resp = requests.get(url, timeout=8,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            img.save(cache_path)

        # Fit inside target box keeping aspect ratio
        img.thumbnail((target_w, target_h), Image.LANCZOS)
        result = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        ox = (target_w  - img.width)  // 2
        oy = (target_h  - img.height) // 2
        result.paste(img, (ox, oy), img)
        return result
    except Exception:
        return None


# ── GIF animasiya ─────────────────────────────────────────────────────────────
CARD_STEP  = 120
CARD_W     = 115
CARD_H     = 220
IMG_W      = CARD_W - 10
IMG_H      = 120
CANVAS_W   = 7 * CARD_STEP    # 840
CANVAS_H   = 310
REEL_Y     = (CANVAS_H - CARD_H) // 2

WINNER_IDX    = 17
TARGET_OFFSET = WINNER_IDX * CARD_STEP + CARD_W // 2 - CANVAS_W // 2
TOTAL_FRAMES  = 54


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 4


def _draw_card(canvas: Image.Image, x: int, y: int, item: dict,
               rarity_info: dict, skin_img, highlight: bool = False):
    draw = ImageDraw.Draw(canvas)
    r = rarity_info
    bw = 4 if highlight else 2
    bc = r["glow"] if highlight else r["color"]

    # Drop shadow
    draw.rectangle([x + 4, y + 4, x + CARD_W + 4, y + CARD_H + 4],
                   fill=(0, 0, 0))
    # Card background
    draw.rectangle([x, y, x + CARD_W, y + CARD_H],
                   fill=r["bg"], outline=bc, width=bw)
    # Top rarity stripe
    draw.rectangle([x + bw, y + bw, x + CARD_W - bw, y + bw + 5],
                   fill=r["color"])

    # Skin image
    img_y = y + 16
    if skin_img:
        canvas.paste(skin_img, (x + (CARD_W - IMG_W) // 2, img_y), skin_img)
    else:
        # Fallback: silhouette placeholder
        draw.rectangle([x + 8, img_y + 10, x + CARD_W - 8, img_y + IMG_H - 10],
                       fill=tuple(max(0, c - 20) for c in r["bg"]),
                       outline=r["color"], width=1)

    # Weapon + skin name
    fn_bold = _font(11, bold=True)
    fn_reg  = _font(10)
    fn_tiny = _font(9, bold=True)
    cx = x + CARD_W // 2
    ty = y + 16 + IMG_H + 6
    draw.text((cx, ty),      item["weapon"], font=fn_bold, fill=(230, 228, 220), anchor="mm")
    draw.text((cx, ty + 14), f"| {item['skin']} |", font=fn_reg,  fill=r["color"],       anchor="mm")

    # Stars
    stars = "★" * r["stars"] + "☆" * (5 - r["stars"])
    draw.text((cx, ty + 28), stars, font=fn_tiny, fill=r["glow"], anchor="mm")

    # Bottom label bar
    bar_y = y + CARD_H - 22
    draw.rectangle([x + bw, bar_y, x + CARD_W - bw, y + CARD_H - bw], fill=r["color"])
    draw.text((cx, bar_y + 10), r["label"], font=fn_tiny,
              fill=(10, 8, 16), anchor="mm")


def _draw_frame(reel: list, skin_images: dict, offset: int,
                highlight_winner: bool) -> Image.Image:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), (12, 10, 16))
    draw = ImageDraw.Draw(img)

    # Subtle vertical grid
    for gx in range(0, CANVAS_W, CARD_STEP):
        draw.line([(gx, 0), (gx, CANVAS_H)], fill=(22, 20, 28), width=1)

    for ci, item in enumerate(reel):
        x = ci * CARD_STEP - offset
        if -CARD_STEP - 5 <= x <= CANVAS_W + 5:
            is_win = (ci == WINNER_IDX and highlight_winner)
            skin_img = skin_images.get(id(item))
            _draw_card(img, x, REEL_Y, item,
                       RARITIES[item["rarity"]], skin_img, highlight=is_win)

    # Edge fade (depth effect)
    fade_w = 100
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for px in range(fade_w):
        a = int(210 * (1 - px / fade_w))
        ov_draw.line([(px, 0), (px, CANVAS_H)], fill=(12, 10, 16, a))
        ov_draw.line([(CANVAS_W - 1 - px, 0), (CANVAS_W - 1 - px, CANVAS_H)],
                     fill=(12, 10, 16, a))
    img = img.convert("RGBA")
    img.alpha_composite(overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Center golden indicator arrows + lines
    cx   = CANVAS_W // 2
    half = CARD_W // 2 + 4
    tri  = 13
    draw.polygon([(cx - tri, 0), (cx + tri, 0), (cx, tri)], fill=(255, 200, 0))
    draw.polygon([(cx - tri, CANVAS_H), (cx + tri, CANVAS_H), (cx, CANVAS_H - tri)],
                 fill=(255, 200, 0))
    draw.rectangle([cx - half, 0, cx - half + 2, CANVAS_H], fill=(255, 200, 0))
    draw.rectangle([cx + half - 2, 0, cx + half, CANVAS_H], fill=(255, 200, 0))

    return img


def generate_crate_gif(winner: dict, reel: list, output_path: str):
    # Pre-fetch all unique skin images
    unique = {id(item): item for item in reel}
    skin_images = {}
    for key, item in unique.items():
        skin_images[key] = _fetch_skin_image(item["img"], IMG_W, IMG_H)

    frames    = []
    durations = []

    for fi in range(TOTAL_FRAMES):
        t      = fi / (TOTAL_FRAMES - 1)
        eased  = _ease_out(t)
        offset = int(eased * TARGET_OFFSET)
        hl     = fi >= TOTAL_FRAMES - 5
        frames.append(_draw_frame(reel, skin_images, offset, hl))

        if   t < 0.55: durations.append(33)
        elif t < 0.72: durations.append(52)
        elif t < 0.86: durations.append(90)
        else:          durations.append(160)

    # Hold final frame
    for _ in range(2):
        frames.append(frames[-1])
        durations.append(800)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=durations,
        optimize=False,
    )


def generate_result_card(winner: dict, output_path: str):
    W, H = 520, 210
    r    = RARITIES[winner["rarity"]]

    img  = Image.new("RGB", (W, H), (12, 10, 16))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W - 1, H - 1)], outline=r["glow"], width=3)
    draw.rectangle([(0, 0), (W, 7)],          fill=r["color"])
    draw.rectangle([(0, H - 7), (W, H)],      fill=r["color"])

    # Skin image on the left
    skin_img = _fetch_skin_image(winner["img"], 160, 150)
    if skin_img:
        img_rgba = img.convert("RGBA")
        img_rgba.paste(skin_img, (20, (H - 150) // 2), skin_img)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    # Text on the right
    fn_big   = _font(24, bold=True)
    fn_med   = _font(16)
    fn_small = _font(12, bold=True)
    fn_tiny  = _font(10)
    tx = 200
    draw.text((tx, 42),  "🎉  QAZANDINIz!",         font=fn_small, fill=r["glow"])
    draw.text((tx, 68),  winner["weapon"],             font=fn_big,   fill=(240, 237, 228))
    draw.text((tx, 100), f"| {winner['skin']} |",     font=fn_med,   fill=r["color"])
    stars = "★" * r["stars"] + "☆" * (5 - r["stars"])
    draw.text((tx, 128), stars,                        font=fn_small, fill=r["glow"])
    draw.text((tx, 152), r["label"],                   font=fn_tiny,  fill=r["color"])

    img.save(output_path)
