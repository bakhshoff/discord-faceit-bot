"""
Scan sistemi: Claude Haiku Vision ilə skor ekranından K/A/D oxuyur.
Fallback: OCR.space API (ANTHROPIC_API_KEY olmadıqda).

Standoff 2 skor ekranı — sütun yapısı:
  Hər oyunçu sətiri:  #  |  İsim  |  [Para$]  |  K  |  A  |  D  |  Skor  |  Ping
  - Para$ sütunu: bəzən var ($ işarəli), bəzən yox — həm CT, həm T tərəfində ola bilər
  - Skor ≤ ~100, Ping ≤ ~500 (bəzən 100+ olur!)
"""
import os
import re
import json
import base64
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OCR_API_KEY       = os.getenv("OCR_API_KEY", "helloworld")

CLAUDE_PROMPT = """Bu Standoff 2 matç sonu İSTATİSTİKLER ekranıdır.

SÜTUN YAPISI (hər oyunçu sətiri):
  #  |  İsim  |  [Para$]  |  K  |  A  |  D  |  Skor  |  Ping

Qeydlər:
- "Para$" sütunu: bəzən var, bəzən yox (həmişə $ ilə işarələnib, min. 1000+)
- "K" = Kill (öldürmə), "A" = Assist, "D" = Death — ekranda bu başlıqlarla göstərilir
- "Skor" və "Ping" K/A/D-dən SONRA gəlir — bunları SAYMA

NİCK QAYDASI — klan taqlərini sil:
- [CSTFY] Zenith   → "Zenith"
- [56799] PrnHub   → "PrnHub"    ← rəqəmli taq da silinir
- [AZE9] SeeyouSo2 → "SeeyouSo2"
- [S2WRX] Am1n     → "Am1n"
- [IFFAB] 910      → "910"       ← yalnız rəqəmlərdən ibarət nik
- [BTN52] Lawliet  → "Lawliet"
- VXO~KFC          → "VXO~KFC"  ← taq yoxdur, olduğu kimi
- URKA____117      → "URKA____117"

YALNIZCA JSON qaytır (başqa heç nə yazma):
[
  {"nick": "Zenith",    "kills": 39, "assists": 5, "deaths": 15},
  {"nick": "TofiqXS",  "kills": 38, "assists": 1, "deaths": 15},
  {"nick": "VXO~KFC",  "kills": 8,  "assists": 2, "deaths": 15}
]"""


def _strip_clan_tag(nick: str) -> str:
    """
    [TAG], (TAG), {TAG} klan taqlarını adın önündən silir.
    Həm hərfli ([CSTFY]), həm rəqəmli ([56799]), həm qarışıq ([AZE9], [BTN52]) taqları tutur.
    """
    nick = nick.strip()
    nick = re.sub(r'^\s*[\[\(\{][A-Za-z0-9_\-]{1,12}[\]\)\}]\s*', '', nick)
    nick = re.sub(r'\s+', ' ', nick).strip()
    return nick


def _safe_int(v, default: int = 0) -> int:
    try:
        s = str(v).strip().replace(',', '').replace(' ', '')
        return max(0, int(float(s)))
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
        m   = re.search(r'\[[\s\S]*?\]', raw)
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
    OCR.space mətnindən K/A/D çıxarır.

    Hər sətir yapısı (Para$ çıxarılandan sonra):
      [row#]  K  A  D  Skor  Ping
      - row# həmişə 1-5 arası
      - Skor ≤ ~100, Ping 0-500 (100+ ola bilər!)

    Alqoritm:
      1. Para$ məbləğini sil
      2. 0-150 aralığındakı rəqəmləri al (Ping > 150 kimi ekstremal dəyərləri at)
      3. Birinci rəqəm 1-9 aralığındadırsa VƏ ardından ≥3 rəqəm varsa → sıra nömrəsidir, atla
      4. İlk 3 rəqəm = K, A, D
    """
    results, seen = [], set()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 1. Para məbləğini sil (N$ və ya $N, adətən 1000-10000 arası)
        line_no_money = re.sub(r'\b\d{3,6}\s*\$|\$\s*\d{3,6}\b', '', line)

        # 2. Bütün rəqəmləri tap, yalnız 0-150 aralığını saxla
        #    (Para artıq silindi; Ping 151+ aralığını filter edir)
        all_raw = re.findall(r'\b(\d+)\b', line_no_money)
        valid   = [int(n) for n in all_raw if 0 <= int(n) <= 150]

        if len(valid) < 3:
            continue

        # 3. Sıra nömrəsini atla:
        #    Birinci rəqəm 1-9 aralığındadırsa VƏ ardından ≥ 3 rəqəm varsa → sıra nömrəsidir
        if valid[0] <= 9 and len(valid) >= 4:
            valid = valid[1:]

        if len(valid) < 3:
            continue

        k, a, d = valid[0], valid[1], valid[2]

        # 4. K/A/D ağlabatan aralıq yoxlaması
        if k > 60 or a > 30 or d > 30:
            continue

        # 5. Oyunçu adını çıxart
        name_part = re.sub(r'\b\d+\b', '', line_no_money)
        name_part = re.sub(r'[\[\(\{][A-Za-z0-9_\-]{1,12}[\]\)\}]', ' ', name_part)
        name_part = re.sub(r'[^A-Za-z0-9_~.\-\s]', ' ', name_part)
        words = [w for w in name_part.split() if len(w) >= 2]

        if not words:
            # Xüsusi hal: yalnız rəqəmlərdən ibarət nick (məs. "910")
            # Sıra nömrəsini (1-9) və K/A/D/Skor/Ping-i qeyri-olaraq atıb
            # 2-4 rəqəmli, ≤ 999 olan ədədi nick kimi qəbul edirik
            digit_nicks = [n for n in re.findall(r'\b(\d{2,4})\b', line_no_money)
                           if 10 <= int(n) <= 999]
            if not digit_nicks:
                continue
            nick = digit_nicks[0]
        else:
            nick = max(words, key=len)
        if nick.lower() in seen:
            continue
        seen.add(nick.lower())

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

    # Tam substring uyğunluğu
    if a in b or b in a:
        return 0.92

    # Prefix uyğunluğu (ilk N simvol)
    min_len = min(len(a), len(b))
    if min_len >= 3:
        prefix_match = sum(1 for i in range(min_len) if a[i] == b[i])
        ratio = prefix_match / min_len
        if ratio >= 0.80:
            return 0.85
        if ratio >= 0.60:
            return 0.70

    # Karakter bazlı uyğunluq
    longer  = max(a, b, key=len)
    shorter = min(a, b, key=len)
    common  = sum(1 for c in shorter if c in longer)
    return common / len(longer)
