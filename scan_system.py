"""
Scan sistemi: Claude Haiku Vision ilə skor ekranından K/A/D oxuyur.
Fallback: OCR.space API (ANTHROPIC_API_KEY olmadıqda).
"""
import os
import re
import json
import base64
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OCR_API_KEY       = os.getenv("OCR_API_KEY", "helloworld")

CLAUDE_PROMPT = """Bu bir Standoff 2 mobil oyununun matç sonu skor ekranıdır.
Ekranda görünən hər oyunçu üçün:
- oyunçu adı (nick) — tam olaraq ekranda göründüyü kimi
- kill sayı (öldürmə)
- asist sayı
- ölüm sayı

məlumatlarını çıxar və YALNIZCA aşağıdakı JSON formatında qaytar, başqa heç nə yazma:
[
  {"nick": "OyuncuAdi1", "kills": 15, "assists": 3, "deaths": 2},
  {"nick": "OyuncuAdi2", "kills": 8,  "assists": 1, "deaths": 5}
]

Qeydlər:
- Asist sütunu görünmürsə 0 yaz
- Rəqəmləri dəqiq oxu
- Yalnız JSON qaytır"""


def ocr_scoreboard(image_bytes: bytes) -> list:
    """
    Skor şəklini Claude Haiku-ya göndərir, K/A/D siyahısı qaytarır.
    ANTHROPIC_API_KEY yoxdursa OCR.space-ə fallback edir.
    """
    if ANTHROPIC_API_KEY:
        return _claude_ocr(image_bytes)
    return _ocrspace_ocr(image_bytes)


def _claude_ocr(image_bytes: bytes) -> list:
    try:
        import anthropic as _ant

        client = _ant.Anthropic(api_key=ANTHROPIC_API_KEY)
        mime   = "image/jpeg" if image_bytes[:3] == b'\xff\xd8\xff' else "image/png"
        b64    = base64.standard_b64encode(image_bytes).decode()

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image",
                     "source": {"type": "base64", "media_type": mime, "data": b64}},
                    {"type": "text", "text": CLAUDE_PROMPT}
                ]
            }]
        )
        raw = msg.content[0].text.strip()
        m   = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        parsed = json.loads(raw)
        return [{"nick":    str(p.get("nick",    "")).strip(),
                 "kills":   int(p.get("kills",   0)),
                 "assists": int(p.get("assists",  0)),
                 "deaths":  int(p.get("deaths",   0))}
                for p in parsed if p.get("nick")]
    except Exception as e:
        raise RuntimeError(f"Claude Vision xətası: {e}")


def _ocrspace_ocr(image_bytes: bytes) -> list:
    try:
        mime  = "image/jpeg" if image_bytes[:3] == b'\xff\xd8\xff' else "image/png"
        b64   = base64.b64encode(image_bytes).decode()
        resp  = requests.post(
            "https://api.ocr.space/parse/image",
            data={"base64Image": f"data:{mime};base64,{b64}",
                  "apikey": OCR_API_KEY,
                  "language": "eng",
                  "OCREngine": 2,
                  "scale": True},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("IsErroredOnProcessing"):
            raise RuntimeError(data.get("ErrorMessage", ["OCR xətası"])[0])
        text = "\n".join(r.get("ParsedText", "") for r in data.get("ParsedResults", []))
        return _parse_ocr_text(text)
    except requests.RequestException as e:
        raise RuntimeError(f"OCR.space xətası: {e}")


def _parse_ocr_text(text: str) -> list:
    results, seen = [], set()
    for line in text.splitlines():
        line = line.strip()
        nums = re.findall(r'\b(\d{1,3})\b', line)
        if len(nums) < 3:
            continue
        name_part = re.sub(r'\b\d+\b', '', line)
        name_part = re.sub(r'[^A-Za-z0-9_#\[\]\.\-]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]
        if not words:
            continue
        nick = max(words, key=len)
        if nick.lower() in seen:
            continue
        seen.add(nick.lower())
        k, a, d = int(nums[0]), int(nums[1]), int(nums[2])
        if k > 99 or a > 99 or d > 99:
            continue
        results.append({"nick": nick, "kills": k, "assists": a, "deaths": d})
    return results


def match_to_registered(ocr_results: list, registered_players: list) -> dict:
    matched, used_ids = {}, set()
    for gr in ocr_results:
        g_nick = gr["nick"].lower().strip()
        best_id, best_score = None, 0
        for rp in registered_players:
            if rp["discord_id"] in used_ids:
                continue
            score = _similarity(g_nick, rp["nick"].lower().strip())
            if score > best_score:
                best_score, best_id = score, rp["discord_id"]
        if best_id and best_score >= 0.55:
            reg_nick = next(p["nick"] for p in registered_players if p["discord_id"] == best_id)
            matched[best_id] = {"nick": reg_nick, "ocr_nick": gr["nick"],
                                 "kills": gr["kills"], "assists": gr["assists"],
                                 "deaths": gr["deaths"], "matched": True}
            used_ids.add(best_id)
        else:
            matched[f"unknown_{gr['nick']}"] = {
                "nick": gr["nick"], "ocr_nick": gr["nick"],
                "kills": gr["kills"], "assists": gr["assists"],
                "deaths": gr["deaths"], "matched": False}
    return matched


def apply_defaults_for_missing(team_players: list, scan_results: dict) -> dict:
    scanned_ids = {k for k in scan_results if isinstance(k, int)}
    for p in team_players:
        if p["discord_id"] not in scanned_ids:
            scan_results[p["discord_id"]] = {
                "nick": p["nick"], "ocr_nick": "",
                "kills": 0, "assists": 0, "deaths": 5, "matched": True}
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
    return sum(1 for c in shorter if c in longer) / len(longer)
