"""
Scan sistemi: pytesseract OCR ilə skor ekranından K/A/D oxuyur.
"""
import re
import io
from PIL import Image, ImageEnhance, ImageFilter

try:
    import pytesseract
    import shutil
    import os as _os

    for _path in ("/usr/bin/tesseract", "/usr/local/bin/tesseract",
                  "/opt/homebrew/bin/tesseract"):
        if _os.path.isfile(_path):
            pytesseract.pytesseract.tesseract_cmd = _path
            break
    else:
        _found = shutil.which("tesseract")
        if _found:
            pytesseract.pytesseract.tesseract_cmd = _found

    TESSERACT_OK = True
except Exception:
    TESSERACT_OK = False


def _preprocess(image_bytes: bytes) -> Image.Image:
    """OCR keyfiyyətini artırmaq üçün şəkli hazırlayır."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 2x böyüt — kiçik şrift üçün vacibdir
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)

    # Boz çalara çevir
    img = img.convert("L")

    # Kontrast artır
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    return img


def ocr_scoreboard(image_bytes: bytes) -> list[dict]:
    """
    Şəkildən oyunçu adı + K/A/D oxuyur.
    Returns: [{"nick": str, "kills": int, "assists": int, "deaths": int}]
    """
    if not TESSERACT_OK:
        raise RuntimeError("pytesseract qurulmayıb.")

    img  = _preprocess(image_bytes)
    text = pytesseract.image_to_string(
        img,
        config="--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_#[]().-/ "
    )
    return _parse_ocr_text(text)


def _parse_ocr_text(text: str) -> list[dict]:
    """
    OCR mətnini parse edib oyunçu siyahısı qaytarır.

    Dəstəklənən formatlar (hər sətirdə):
      PlayerName 15 3 2
      #1 PlayerName 15 3 2
      15 3 2 PlayerName
      PlayerName: 15/3/2
    """
    results = []
    seen_nicks = set()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        nums = re.findall(r'\b(\d{1,3})\b', line)
        if len(nums) < 3:
            continue

        # Rəqəmləri çıxarıb adı tap
        name_part = re.sub(r'\b\d+\b', '', line)
        name_part = re.sub(r'[^A-Za-z0-9_#\[\]\.\-]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]
        if not words:
            continue

        nick = max(words, key=len)

        # Eyni ad iki dəfə əlavə olunmasın
        if nick.lower() in seen_nicks:
            continue
        seen_nicks.add(nick.lower())

        k, a, d = int(nums[0]), int(nums[1]), int(nums[2])

        # Ağlabatan həddlər: kill/asist/death 0-99 arasında olmalıdır
        if k > 99 or a > 99 or d > 99:
            continue

        results.append({"nick": nick, "kills": k, "assists": a, "deaths": d})

    return results


def match_to_registered(ocr_results: list[dict], registered_players: list[dict]) -> dict:
    """
    OCR nəticələrini qeydiyyatlı oyunçularla uyğunlaşdırır.
    registered_players: [{"discord_id", "nick", ...}]
    Returns: {discord_id|"unknown_nick": {"nick", "kills", "assists", "deaths", "matched", "ocr_nick"}}
    """
    matched  = {}
    used_ids = set()

    for gr in ocr_results:
        g_nick     = gr["nick"].lower().strip()
        best_id    = None
        best_score = 0

        for rp in registered_players:
            if rp["discord_id"] in used_ids:
                continue
            score = _similarity(g_nick, rp["nick"].lower().strip())
            if score > best_score:
                best_score = score
                best_id    = rp["discord_id"]

        if best_id and best_score >= 0.55:
            reg_nick = next(p["nick"] for p in registered_players if p["discord_id"] == best_id)
            matched[best_id] = {
                "nick":     reg_nick,
                "ocr_nick": gr["nick"],
                "kills":    gr["kills"],
                "assists":  gr["assists"],
                "deaths":   gr["deaths"],
                "matched":  True,
            }
            used_ids.add(best_id)
        else:
            matched[f"unknown_{gr['nick']}"] = {
                "nick":     gr["nick"],
                "ocr_nick": gr["nick"],
                "kills":    gr["kills"],
                "assists":  gr["assists"],
                "deaths":   gr["deaths"],
                "matched":  False,
            }

    return matched


def apply_defaults_for_missing(team_players: list, scan_results: dict) -> dict:
    """Scan-da tapılmayan qeydiyyatlı oyunçulara 0/0/5 verir."""
    scanned_ids = {k for k in scan_results if isinstance(k, int)}
    for p in team_players:
        if p["discord_id"] not in scanned_ids:
            scan_results[p["discord_id"]] = {
                "nick":     p["nick"],
                "ocr_nick": "",
                "kills":    0,
                "assists":  0,
                "deaths":   5,
                "matched":  True,
            }
    return scan_results


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.88
    longer  = max(a, b, key=len)
    shorter = min(a, b, key=len)
    common  = sum(1 for c in shorter if c in longer)
    return common / len(longer)
