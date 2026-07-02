"""
Scan sistemi: Claude Haiku Vision ilə skor ekranından K/A/D oxuyur.
Fallback: OCR.space API (ANTHROPIC_API_KEY olmadıqda).

Standoff 2 skor ekranı sütun sırası:
  Sol komanda: # | İsim | Para($) | K | A | D | Skor | Ping
  Sağ komanda: # | İsim | K | A | D | Skor | Ping
"""
import os
import re
import json
import base64
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OCR_API_KEY       = os.getenv("OCR_API_KEY", "helloworld")

CLAUDE_PROMPT = """Bu Standoff 2 mobil oyununun matç sonu istatistik ekranıdır.

SÜTUN SIRASİ:
- Sol komanda (CT/SAVUNMA): # | İsim | Para($) | K | A | D | Skor | Ping
- Sağ komanda (T/SALDIRI): # | İsim | K | A | D | Skor | Ping

Hər oyunçu üçün çıxar:
1. nick — ad mötərizə içi KİLAN TAGi olmadan (məs. [CSTFY] Zenith → "Zenith", [56799] PrnHub → "PrnHub")
   - Adın ÖNÜNDƏ [...] (TAG) {GRP} formatında varsa SİL
   - Xüsusi simvolları (~, _, -, .) saxla
2. K — "K" başlıqlı sütun (kill sayı, sol komandada Para($)-dan SONRA gəlir)
3. A — "A" başlıqlı sütun (assist)
4. D — "D" başlıqlı sütun (death)

DİQQƏT:
- Para (pul miqdarı, $ işarəli, məs. 6900$, 10000$) — BU K DEYİL, SAYMA
- "Skor" sütunu — K/A/D-dən SONRA gəlir, onu da SAYMA
- "Ping" sütunu — ən sonda, SAYMA
- Yalnız K, A, D sütunlarını çıxart

YALNIZCA bu JSON formatında qaytar, başqa heç nə yazma:
[
  {"nick": "Zenith",         "kills": 39, "assists": 5,  "deaths": 15},
  {"nick": "NyxZero",        "kills": 24, "assists": 1,  "deaths": 12},
  {"nick": "XyRo~",          "kills": 11, "assists": 6,  "deaths": 14},
  {"nick": "TofiqXS",        "kills": 38, "assists": 1,  "deaths": 15},
  {"nick": "AzE_-Elfat1Ha-", "kills": 10, "assists": 4,  "deaths": 17}
]"""


def _strip_clan_tag(nick: str) -> str:
    """[TAG], (TAG), {TAG} kimi klan taglarını adın önündən silir.
    Həm hərfli ([CSTFY]), həm rəqəmli ([56799]) tagları tutir."""
    nick = nick.strip()
    # Mötərizə içi klan tag — ad başında (hərf, rəqəm, alt xətt, tire 1-12 simvol)
    nick = re.sub(r'^\s*[\[\(\{][A-Za-z0-9_\-]{1,12}[\]\)\}]\s*', '', nick)
    nick = re.sub(r'\s+', ' ', nick).strip()
    return nick


def _safe_int(v, default: int = 0) -> int:
    """Dəyəri təhlükəsiz şəkildə int-ə çevirir."""
    try:
        return max(0, int(str(v).strip().replace(',', '').replace('.', '')))
    except Exception:
        return default


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
        # JSON bloku tap
        m = re.search(r'\[[\s\S]*?\]', raw)
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
    """
    OCR.space mətnindən K/A/D məlumatı çıxarır.

    Sütun sırası:
      Sol komanda: Para($) K A D Skor Ping  → Para-nı sil, ilk 3 = K/A/D
      Sağ komanda: K A D Skor Ping          → ilk 3 = K/A/D
    """
    results, seen = [], set()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Para sütununu sil (N$ və ya $N formatı, adətən 1000-10000 arası)
        # Məs: "6900$", "10000$", "$6900"
        line_no_money = re.sub(r'\b\d{3,6}\s*\$|\$\s*\d{3,6}\b', '', line)

        # Sətirdəki bütün rəqəmlər
        all_nums = re.findall(r'\b(\d+)\b', line_no_money)
        if len(all_nums) < 3:
            continue

        # Ad hissəsini tap (rəqəmləri silərək)
        name_part = re.sub(r'\b\d+\b', '', line_no_money)
        # Klan tagları sil
        name_part = re.sub(r'[\[\(\{][A-Za-z0-9_\-]{1,12}[\]\)\}]', ' ', name_part)
        # Oyun adı üçün icazəli simvollar: hərf, rəqəm, _, ~, -, .
        name_part = re.sub(r'[^A-Za-z0-9_~.\-\s]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]
        if not words:
            continue

        nick = max(words, key=len)
        nick_lower = nick.lower()
        if nick_lower in seen:
            continue
        seen.add(nick_lower)

        # Rəqəmləri filtr: yalnız 0-99 arası (K/A/D/Skor/Ping üçün məntiqli)
        valid_nums = [int(n) for n in all_nums if int(n) <= 99]
        if len(valid_nums) < 3:
            continue

        # Sıra nömrəsi (# 1-5) idarəsi:
        # Əgər 6 və ya daha çox rəqəm varsa: # + K + A + D + Skor + Ping = 6
        # Birinci rəqəm sıra nömrəsidir — atla.
        # 5 rəqəm varsa: K + A + D + Skor + Ping — atlamaq lazım deyil.
        if len(valid_nums) >= 6:
            valid_nums = valid_nums[1:]   # sıra nömrəsini at

        k, a, d = valid_nums[0], valid_nums[1], valid_nums[2]

        # Ağlabatan K/A/D aralığı yoxla
        if k > 60 or a > 30 or d > 30:
            continue

        results.append({"nick": nick, "kills": k, "assists": a, "deaths": d})

    return results


def match_to_registered(ocr_results: list, registered_players: list) -> dict:
    """OCR nəticələrini qeydiyyatlı oyunçularla uyğunlaşdırır."""
    matched, used_ids = {}, set()

    for gr in ocr_results:
        raw_nick = _strip_clan_tag(gr["nick"])
        g_nick   = raw_nick.lower().strip()

        best_id, best_score = None, 0.0
        for rp in registered_players:
            if rp["discord_id"] in used_ids:
                continue
            rp_clean = _strip_clan_tag(rp["nick"]).lower().strip()
            score    = _similarity(g_nick, rp_clean)
            if score > best_score:
                best_score, best_id = score, rp["discord_id"]

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
                "nick":     raw_nick or gr["nick"],
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
                "nick":    p["nick"],
                "ocr_nick": "",
                "kills":   0,
                "assists": 0,
                "deaths":  5,
                "matched": True,
            }
    return scan_results


def _similarity(a: str, b: str) -> float:
    """İki nickinin oxşarlığını 0.0-1.0 arası qiymətləndirir."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.92

    # Prefix uyğunluğu (ilk N simvol)
    min_len = min(len(a), len(b))
    if min_len >= 4:
        prefix_match = sum(1 for i in range(min_len) if a[i] == b[i])
        if prefix_match / min_len >= 0.80:
            return 0.85

    # Karakter bazlı uyğunluq
    longer  = max(a, b, key=len)
    shorter = min(a, b, key=len)
    common  = sum(1 for c in shorter if c in longer)
    return common / len(longer)
