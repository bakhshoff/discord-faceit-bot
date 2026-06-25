"""
Scan sistemi: Gemini Vision ekran görüntüsündən K/A/D oxuyur.
"""
import os
import json
import base64
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_PROMPT = """Bu bir Standoff 2 oyununun skor ekranıdır.
Ekrandakı hər oyunçu üçün:
- oyunçu adı (nick)
- kill sayı
- asist sayı
- ölüm (death) sayı

məlumatlarını tap və YALNIZCA aşağıdakı JSON formatında ver, başqa heç nə yazma:
[
  {"nick": "OyuncuAdi1", "kills": 15, "assists": 3, "deaths": 2},
  {"nick": "OyuncuAdi2", "kills": 8, "assists": 5, "deaths": 4}
]

Qeydlər:
- Əgər asist sütunu görünmürsə, assists üçün 0 yaz
- Oyunçu adını tam olaraq ekranda göründüyü kimi yaz
- Rəqəmləri dəqiq oxu
- Yalnız JSON qaytır, izahat yazma
"""


def analyze_with_gemini(image_bytes: bytes) -> list[dict]:
    """
    Ekran görüntüsünü Gemini-yə göndərir, K/A/D siyahısı qaytarır.
    Returns: [{"nick": str, "kills": int, "assists": int, "deaths": int}, ...]
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        mime   = "image/jpeg" if image_bytes[:3] == b'\xff\xd8\xff' else "image/png"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                GEMINI_PROMPT,
                types.Part.from_bytes(data=image_bytes, mime_type=mime),
            ]
        )
        raw = response.text.strip()

        # JSON blokunu çıxar (``` bloku ola bilər)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        parsed = json.loads(raw)
        result = []
        for item in parsed:
            result.append({
                "nick":    str(item.get("nick", "")).strip(),
                "kills":   int(item.get("kills",   0)),
                "assists": int(item.get("assists",  0)),
                "deaths":  int(item.get("deaths",   0)),
            })
        return result
    except Exception as e:
        raise RuntimeError(f"Gemini Vision xətası: {e}")


def match_to_registered(gemini_results: list[dict], registered_players: list[dict]) -> dict:
    """
    Gemini nəticələrini qeydiyyatlı oyunçularla uyğunlaşdırır.
    registered_players: [{"discord_id", "nick", "so2_id", ...}]
    Returns: {discord_id: {"nick", "kills", "assists", "deaths", "matched", "gemini_nick"}}
    """
    matched = {}
    used_ids = set()

    for gr in gemini_results:
        g_nick = gr["nick"].lower().strip()
        best_id, best_score = None, 0

        for rp in registered_players:
            if rp["discord_id"] in used_ids:
                continue
            r_nick = rp["nick"].lower().strip()
            score  = _similarity(g_nick, r_nick)
            if score > best_score:
                best_score = score
                best_id    = rp["discord_id"]

        if best_id and best_score >= 0.55:
            matched[best_id] = {
                "nick":        next(p["nick"] for p in registered_players if p["discord_id"] == best_id),
                "gemini_nick": gr["nick"],
                "kills":       gr["kills"],
                "assists":     gr["assists"],
                "deaths":      gr["deaths"],
                "matched":     True,
            }
            used_ids.add(best_id)
        else:
            # Uyğun tapılmadı - unknown olaraq saxla
            matched[f"unknown_{gr['nick']}"] = {
                "nick":        gr["nick"],
                "gemini_nick": gr["nick"],
                "kills":       gr["kills"],
                "assists":     gr["assists"],
                "deaths":      gr["deaths"],
                "matched":     False,
            }

    return matched


def apply_defaults_for_missing(team_players: list, scan_results: dict) -> dict:
    """Scan-da adı olmayan qeydiyyatlı oyunçulara 0/0/5 verir."""
    scanned_ids = {k for k in scan_results if isinstance(k, int)}
    for p in team_players:
        if p["discord_id"] not in scanned_ids:
            scan_results[p["discord_id"]] = {
                "nick":        p["nick"],
                "gemini_nick": "",
                "kills":       0,
                "assists":     0,
                "deaths":      5,
                "matched":     True,
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
