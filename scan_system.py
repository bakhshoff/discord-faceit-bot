"""
Oyun statistika scan sistemi.
Admin /scan əmri ilə oyun skorbordunu yapışdırır,
bot oyunçu adlarını + K/A/D-ni parse edir.
"""
import re


def parse_scoreboard(text: str, registered: dict) -> dict:
    """
    text: admin-in yapışdırdığı skor mətni
    registered: {so2_nick.lower(): discord_id} - qeydiyyatlı oyunçular

    Dəstəklənən formatlar (hər sətirdə oyunçu):
      PlayerName 15 3 2
      PlayerName: 15/3/2
      15 3 2 PlayerName
      #1 PlayerName 15 3 2
    Qaytarır: {discord_id: {nick, kills, assists, deaths, matched}}
    """
    results = {}
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    num_pat  = r'\d+'
    name_pat = r"[A-Za-z0-9_\[\]\.#\-]{2,24}"

    for line in lines:
        # Rəqəmləri tap
        nums = re.findall(num_pat, line)
        if len(nums) < 3:
            continue
        # Ad tapılması: rəqəmləri çıxarıb qalan hissəni al
        name_candidate = re.sub(r'\d+', '', line)
        name_candidate = re.sub(r'[^A-Za-z0-9_\[\]\.#\-]', ' ', name_candidate).strip()
        words = [w for w in name_candidate.split() if len(w) >= 2]
        if not words:
            continue
        # Ən uzun sözü ad kimi götür
        nick = max(words, key=len)
        kills, assists, deaths = int(nums[0]), int(nums[1]), int(nums[2])

        # Qeydiyyatlı oyunçu ilə uyğunlaşdır
        matched_id = None
        best_score = 0
        for reg_nick, did in registered.items():
            score = _similarity(nick.lower(), reg_nick.lower())
            if score > best_score and score >= 0.6:
                best_score = score
                matched_id = did

        key = matched_id if matched_id else f"unknown_{nick}"
        results[key] = {
            "nick": nick,
            "kills": kills,
            "assists": assists,
            "deaths": deaths,
            "matched": matched_id is not None,
        }

    return results


def _similarity(a: str, b: str) -> float:
    """Sadə oxşarlıq: ən uzun ümumi alt-sətir / uzunluq."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # Prefix/contains check
    if a in b or b in a:
        return 0.85
    # Ortak hərflər
    common = sum(1 for c in a if c in b)
    return common / max(len(a), len(b))


def apply_defaults_for_missing(team_players: list, scan_results: dict) -> dict:
    """
    Scan-da adı çıxmayan qeydiyyatlı oyunçulara 0/0/5 verir.
    team_players: [{"discord_id", "nick", ...}]
    scan_results: {discord_id/unknown_xxx: {...}}
    """
    scanned_ids = {k for k in scan_results if isinstance(k, int)}
    for p in team_players:
        if p["discord_id"] not in scanned_ids:
            scan_results[p["discord_id"]] = {
                "nick": p["nick"],
                "kills": 0,
                "assists": 0,
                "deaths": 5,
                "matched": True,
            }
    return scan_results
