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
Ekranda görünən hər oyunçu üçün aşağıdakı məlumatları çıxar:

1. oyunçu adı (nick) — ÖNƏMLİ QEYDLƏR:
   - Adın ÖNÜNDƏ mötərizə içərisindəki klan tagi varsa (məs. [CLAN], (TAG), {GRP}) — onu SİL, yalnız əsas adı yaz
   - Adın içindəki rəqəmlər (məs. Player123) saxla
   - Böyük/kiçik hərfə qədər dəqiq yaz

2. K sütunu (kill/öldürmə sayı) — sol sütun
3. A sütunu (assist/köməkçi) — orta sütun
4. D sütunu (death/ölüm) — sağ sütun

YALNIZCA aşağıdakı JSON formatında qaytar, başqa heç nə yazma:
[
  {"nick": "OyuncuAdi1", "kills": 15, "assists": 3, "deaths": 2},
  {"nick": "OyuncuAdi2", "kills": 8,  "assists": 1, "deaths": 5}
]

Əlavə qeydlər:
- K, A, D sütunlarını sırası ilə oxu — qarışdırma
- Asist sütunu görünmürsə 0 yaz
- Rəqəmləri tam dəqiq oxu, təxmin etmə
- Yalnız JSON qaytır, izah yazma"""


def _strip_clan_tag(nick: str) -> str:
    """[TAG], (TAG), {TAG} kimi klan taglarını adın önündən silir."""
    nick = nick.strip()
    # Mötərizə içi klan tag — önündə
    nick = re.sub(r'^\s*[\[\(\{][^\]\)\}]{1,10}[\]\)\}]\s*', '', nick)
    # Ardıcıl boşluqları tək boşluğa endir
    nick = re.sub(r'\s+', ' ', nick).strip()
    return nick


def ocr_scoreboard(image_bytes: bytes) -> list:
    """Skor şəklini Claude Haiku-ya göndərir, K/A/D siyahısı qaytarır."""
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
        results = []
        for p in parsed:
            if not p.get("nick"):
                continue
            nick = _strip_clan_tag(str(p["nick"]))
            if not nick:
                continue
            results.append({
                "nick":    nick,
                "kills":   _safe_int(p.get("kills",   0)),
                "assists": _safe_int(p.get("assists",  0)),
                "deaths":  _safe_int(p.get("deaths",   0)),
            })
        return results
    except Exception as e:
        raise RuntimeError(f"Claude Vision xətası: {e}")


def _safe_int(v) -> int:
    try:
        return max(0, int(str(v).strip()))
    except Exception:
        return 0


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
    """OCR.space mətnindən K/A/D sətirini ayrıştırır."""
    results, seen = [], set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Sətirdəki bütün rəqəm qruplarını tap
        nums = re.findall(r'\b(\d{1,3})\b', line)
        if len(nums) < 3:
            continue

        # Rəqəmləri silərək ad hissəsini al
        name_part = re.sub(r'\b\d+\b', '', line)
        # Klan tagları sil
        name_part = re.sub(r'[\[\(\{][^\]\)\}]{1,10}[\]\)\}]', ' ', name_part)
        # Xüsusi simvolları sil
        name_part = re.sub(r'[^A-Za-z0-9_#.\-]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]
        if not words:
            continue

        nick = max(words, key=len)
        if nick.lower() in seen:
            continue
        seen.add(nick.lower())

        # K/A/D sırası: sətirin sağında olan 3 rəqəm (sonuncular)
        k = _safe_int(nums[-3])
        a = _safe_int(nums[-2])
        d = _safe_int(nums[-1])
        if k > 99 or a > 99 or d > 99:
            continue
        results.append({"nick": nick, "kills": k, "assists": a, "deaths": d})
    return results


def match_to_registered(ocr_results: list, registered_players: list) -> dict:
    """OCR nəticələrini qeydiyyatlı oyunçularla uyğunlaşdırır."""
    matched, used_ids = {}, set()
    for gr in ocr_results:
        # Klan tagını əvvəlcə sil
        raw_nick  = _strip_clan_tag(gr["nick"])
        g_nick    = raw_nick.lower().strip()
        best_id, best_score = None, 0

        for rp in registered_players:
            if rp["discord_id"] in used_ids:
                continue
            # Qeydiyyatlı oyunçunun adından da klan tag çıxarılır
            rp_clean = _strip_clan_tag(rp["nick"]).lower().strip()
            score    = _similarity(g_nick, rp_clean)
            if score > best_score:
                best_score, best_id = score, rp["discord_id"]

        if best_id and best_score >= 0.55:
            reg_nick = next(p["nick"] for p in registered_players if p["discord_id"] == best_id)
            matched[best_id] = {
                "nick":    reg_nick,
                "ocr_nick": gr["nick"],
                "kills":   gr["kills"],
                "assists": gr["assists"],
                "deaths":  gr["deaths"],
                "matched": True,
            }
            used_ids.add(best_id)
        else:
            matched[f"unknown_{gr['nick']}"] = {
                "nick":    raw_nick,
                "ocr_nick": gr["nick"],
                "kills":   gr["kills"],
                "assists": gr["assists"],
                "deaths":  gr["deaths"],
                "matched": False,
            }
    return matched


def apply_defaults_for_missing(team_players: list, scan_results: dict) -> dict:
    scanned_ids = {k for k in scan_results if isinstance(k, int)}
    for p in team_players:
        if p["discord_id"] not in scanned_ids:
            scan_results[p["discord_id"]] = {
                "nick":    p["nick"],
                "ocr_nick": "",
                "kills":   0,
                "assists": 0,
                "deaths":  5,
                "matched": True,
            }
    return scan_results


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.90
    # Prefix uyğunluğu
    prefix_len = min(len(a), len(b))
    if prefix_len >= 3:
        common_prefix = sum(1 for i in range(prefix_len) if a[i] == b[i])
        if common_prefix / prefix_len >= 0.75:
            return 0.80
    longer  = max(a, b, key=len)
    shorter = min(a, b, key=len)
    return sum(1 for c in shorter if c in longer) / len(longer)
