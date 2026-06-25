"""
Scan sistemi: OCR.space API ilə skor ekranından K/A/D oxuyur.
Heç bir sistem paketi tələb etmir — sadəcə HTTP sorğusu.
"""
import os
import re
import json
import base64
import requests

OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")  # helloworld = test key


def ocr_scoreboard(image_bytes: bytes) -> list:
    """
    Şəkli OCR.space API-yə göndərir, K/A/D siyahısı qaytarır.
    Returns: [{"nick": str, "kills": int, "assists": int, "deaths": int}]
    """
    try:
        b64 = base64.b64encode(image_bytes).decode()
        mime = "image/jpeg" if image_bytes[:3] == b'\xff\xd8\xff' else "image/png"

        payload = {
            "base64Image": f"data:{mime};base64,{b64}",
            "apikey":       OCR_API_KEY,
            "language":     "eng",
            "isOverlayRequired": False,
            "detectOrientation": True,
            "scale":        True,
            "OCREngine":    2,
        }

        resp = requests.post(
            "https://api.ocr.space/parse/image",
            data=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("IsErroredOnProcessing"):
            raise RuntimeError(data.get("ErrorMessage", ["OCR xətası"])[0])

        full_text = ""
        for result in data.get("ParsedResults", []):
            full_text += result.get("ParsedText", "") + "\n"

        return _parse_ocr_text(full_text)

    except requests.RequestException as e:
        raise RuntimeError(f"OCR.space API xətası: {e}")


def _parse_ocr_text(text: str) -> list:
    """
    OCR mətnini parse edib oyunçu siyahısı qaytarır.

    Dəstəklənən formatlar (hər sətirdə):
      PlayerName 15 3 2
      #1 PlayerName 15 3 2
      15 3 2 PlayerName
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

        name_part = re.sub(r'\b\d+\b', '', line)
        name_part = re.sub(r'[^A-Za-z0-9_#\[\]\.\-]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]
        if not words:
            continue

        nick = max(words, key=len)
        if nick.lower() in seen_nicks:
            continue
        seen_nicks.add(nick.lower())

        k, a, d = int(nums[0]), int(nums[1]), int(nums[2])
        if k > 99 or a > 99 or d > 99:
            continue

        results.append({"nick": nick, "kills": k, "assists": a, "deaths": d})

    return results


def match_to_registered(ocr_results: list, registered_players: list) -> dict:
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
