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
    "banner_box_exclusive": ((120, 90, 20), (15, 11, 5)),  # Mystery Box-dan İSTİSNA düşür
}

# item_id -> halqa rəngi
FRAME_DEFS = {
    "frame_gold": (255, 205, 60),
    "frame_box_exclusive": (240, 180, 41),  # Mystery Box-dan İSTİSNA düşür
}

# item_id -> (üst rəng, alt rəng) — animasiyalı (GIF) bannerlər, hərəkətli işıq zolağı ilə
ANIMATED_BANNER_DEFS = {
    "banner_aurora": ((60, 30, 130), (10, 8, 20)),
    "banner_inferno": ((170, 45, 20), (22, 9, 6)),
    "banner_box_exclusive_gif": ((120, 90, 20), (15, 11, 5)),  # Mystery Box-dan İSTİSNA düşür
}

# item_id -> halqa rəngi — animasiyalı (GIF) çərçivələr, nəbz-effekti ilə (bax: _make_animated_frame)
ANIMATED_FRAME_DEFS = {
    "frame_box_exclusive_gif": (240, 180, 41),  # Mystery Box-dan İSTİSNA düşür
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


def _make_animated_banner(top, bottom, n_frames=24):
    """Bir statik qradiyent üzərində soldan-sağa hərəkət edən işıq zolağı effekti olan
    GIF çərçivələri qaytarır (bax: ensure_market_assets — animasiyalı bannerlər üçün)."""
    base = _gradient(BANNER_W, BANNER_H, top, bottom)
    accent = tuple(min(255, c + 90) for c in top)
    sweep_w = 240
    total_span = BANNER_W + sweep_w * 2
    frames = []
    for i in range(n_frames):
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        offset = int((i / n_frames) * total_span) - sweep_w
        for dx in range(-sweep_w, sweep_w, 10):
            x = offset + dx
            brightness = max(0.0, 1 - abs(dx) / sweep_w)
            col = tuple(int(bottom[c] + (accent[c] - bottom[c]) * brightness) for c in range(3))
            draw.line([(x, 0), (x + BANNER_H, BANNER_H)], fill=col, width=5)
        frames.append(frame)
    return frames


def _make_frame(color, size=150):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r1, r2 = size // 2 - 4, size // 2 - 13
    draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline=color + (255,), width=5)
    draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=color + (130,), width=2)
    return img


def _make_animated_frame(color, size=150, n_frames=16):
    """Nəbz vuran (pulse) parıltı effektli animasiyalı çərçivə — bax: ANIMATED_FRAME_DEFS.
    GIF-in qismi şəffaflığı olmadığı (tək 'transparent' indeks) üçün animasiya ALFA ilə
    DEYİL, halqanın parlaqlığı (RGB) ilə verilir — əks halda bütün kadrlar eyni görünür."""
    import math
    cx = cy = size // 2
    r1, r2 = size // 2 - 4, size // 2 - 13
    dim = tuple(int(c * 0.45) for c in color)
    frames = []
    for i in range(n_frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * i / n_frames)
        glow_col = tuple(int(dim[c] + (color[c] - dim[c]) * pulse) for c in range(3))
        draw.ellipse([cx - r1 - 4, cy - r1 - 4, cx + r1 + 4, cy + r1 + 4],
                     outline=glow_col + (255,), width=6)
        draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline=color + (255,), width=5)
        draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=color + (130,), width=2)
        frames.append(img)
    return frames


def ensure_market_assets():
    """Hər bannerin/çərçivənin PNG faylını (yoxdursa) yaradır, {item_id: fayl_yolu} qaytarır."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    paths = {}
    for item_id, (top, bottom) in BANNER_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.png")
        if not os.path.exists(path):
            _make_banner(top, bottom).save(path)
        paths[item_id] = path
    for item_id, (top, bottom) in ANIMATED_BANNER_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.gif")
        if not os.path.exists(path):
            frames = _make_animated_banner(top, bottom)
            frames[0].save(path, format="GIF", save_all=True, append_images=frames[1:], duration=70, loop=0)
        paths[item_id] = path
    for item_id, color in FRAME_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.png")
        if not os.path.exists(path):
            _make_frame(color).save(path)
        paths[item_id] = path
    for item_id, color in ANIMATED_FRAME_DEFS.items():
        path = os.path.join(ASSET_DIR, f"{item_id}.gif")
        if not os.path.exists(path):
            frames = _make_animated_frame(color)
            frames[0].save(
                path, format="GIF", save_all=True, append_images=frames[1:],
                duration=80, loop=0, disposal=2
            )
        paths[item_id] = path
    return paths
