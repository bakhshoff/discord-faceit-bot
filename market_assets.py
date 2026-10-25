"""Market-in kosmetik əşyaları (banner/çərçivə) üçün PNG-ləri PROSEDURAL yaradır —
xarici dizayn faylına ehtiyac yoxdur. `ensure_market_assets()` idempotentdir: fayl
artıq varsa yenidən yaratmır."""
from PIL import Image, ImageDraw
import os

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_assets_gen")

BANNER_W, BANNER_H = 900, 540

# item_id -> (üst rəng, alt rəng)
BANNER_DEFS = {
    "banner_violet": ((90, 50, 160), (18, 13, 28)),
    "banner_emerald": ((20, 120, 75), (10, 20, 17)),
    "banner_crimson": ((160, 45, 32), (26, 12, 10)),
}

# item_id -> halqa rəngi
FRAME_DEFS = {
    "frame_gold": (255, 205, 60),
}


def _gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=c)
    return img


def _make_banner(top, bottom):
    img = _gradient(BANNER_W, BANNER_H, top, bottom)
    draw = ImageDraw.Draw(img)
    accent = tuple(min(255, c + 55) for c in top)
    for x in range(-BANNER_H, BANNER_W, 64):
        draw.line([(x, 0), (x + BANNER_H, BANNER_H)], fill=accent, width=2)
    return img


def _make_frame(color, size=150):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r1, r2 = size // 2 - 4, size // 2 - 13
    draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline=color + (255,), width=5)
    draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=color + (130,), width=2)
    return img


def ensure_market_assets():
    """Hər bannerin/çərçivənin PNG faylını (yoxdursa) yaradır, {item_id: fayl_yolu} qaytarır."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    paths = {}
    for item_id, (top, bottom) in BANNER_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.png")
        if not os.path.exists(path):
            _make_banner(top, bottom).save(path)
        paths[item_id] = path
    for item_id, color in FRAME_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.png")
        if not os.path.exists(path):
            _make_frame(color).save(path)
        paths[item_id] = path
    return paths
