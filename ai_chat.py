import os
import time
import sqlite3
import json
from groq import Groq

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "."), "bot_database.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

HISTORY_LIMIT = 20
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Sen Zenith's Academy-nin Discord botusun. Standoff 2 mobile oyunu üzrə turnirləri idarə edirsən.

Cəmiyyət haqqında:
- Zenith's Academy — Azərbaycanlı Standoff 2 oyunçularının toplumu
- ELO sistemi, 1v1 və 5v5 turnir matçları keçirilir
- Oyunçular coin qazanır, market vasitəsilə bannerlər, çərçivələr, skinlər ala bilər
- 250 coin = 0.5 AZN olaraq çevrilə bilər

Davranış qaydaları:
- Azərbaycan dilində cavab ver (kimsə başqa dildə yazsа o dildə cavab ver)
- Mehriban, şən, lakin peşəkar ol
- Oyunçuların adını xatırla və şəxsi yanaş
- Qısa və aydın cavablar ver (çox uzun yazma)
- Oyun strategiyası, rank yüksəltmə, coin qazanma haqqında kömək et

İstifadəçi haqqında bildiklərin:
{ai_memory}

Əgər söhbət əsnasında istifadəçi haqqında yeni vacib məlumat öyrənsən (sevdiyi silah, oyun stili, məqsədi, adı, yaşı, bacarıqları və s.), cavabının sonuna bu formatla əlavə et:
##YADDAŞ## [qısa faktlar, vergüllə ayrılmış]

Bu ##YADDAŞ## hissəsi istifadəçiyə görsənmir, yalnız sistem üçündür."""


def get_chat_history(discord_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_history WHERE discord_id = ? ORDER BY created_at DESC LIMIT ?",
        (discord_id, HISTORY_LIMIT)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def add_to_history(discord_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (discord_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (discord_id, role, content, int(time.time()))
    )
    cursor.execute(
        """DELETE FROM chat_history WHERE discord_id = ? AND id NOT IN (
            SELECT id FROM chat_history WHERE discord_id = ? ORDER BY created_at DESC LIMIT ?
        )""",
        (discord_id, discord_id, HISTORY_LIMIT)
    )
    conn.commit()
    conn.close()


def get_ai_memory(discord_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ai_memory FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else "Hələ heç nə bilinmir."


def update_ai_memory(discord_id: int, new_facts: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ai_memory FROM players WHERE discord_id = ?", (discord_id,))
    row = cursor.fetchone()
    existing = row[0] if row and row[0] else ""
    updated = (existing + ", " + new_facts).strip(", ") if existing and existing != "Hələ heç nə bilinmir." else new_facts
    if len(updated) > 1000:
        updated = updated[-1000:]
    cursor.execute("UPDATE players SET ai_memory = ? WHERE discord_id = ?", (updated, discord_id))
    conn.commit()
    conn.close()


def ask_groq(discord_id: int, username: str, user_message: str, player_data=None) -> str:
    if not client:
        return "❌ Groq API key qurulmayıb."

    memory = get_ai_memory(discord_id)
    history = get_chat_history(discord_id)

    player_info = ""
    if player_data:
        nick, so2_id, elo, wins, losses, coins = player_data[1], player_data[2], player_data[3], player_data[4], player_data[5], player_data[6]
        matches = wins + losses
        wr = round(wins / matches * 100, 1) if matches > 0 else 0
        player_info = f"\nOyunçu statistikası: Nick={nick}, ELO={elo}, Wins={wins}, Losses={losses}, Win Rate={wr}%, Coins={coins}"

    system = SYSTEM_PROMPT.format(ai_memory=memory + player_info)

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.8,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Xəta: {e}"

    if "##YADDAŞ##" in reply:
        parts = reply.split("##YADDAŞ##")
        reply = parts[0].strip()
        facts = parts[1].strip()
        if facts:
            update_ai_memory(discord_id, facts)

    add_to_history(discord_id, "user", user_message)
    add_to_history(discord_id, "assistant", reply)

    return reply


COACH_SYSTEM_PROMPT = """Sen Zenith's Academy-nin Standoff 2 oyun köməkçisisən.
Oyunçuya bir matçdan sonra qısa, konkret, 1-2 cümləlik məsləhət ver.
Azərbaycan dilində yaz. Emoji istifadə etmə. Ümumi sözlər yox, verilən
statistikaya əsaslanan konkret müşahidə et (məs. çox ölüb az kill edibsə,
mövqe seçimini qeyd et; yaxşı nəticə olubsa, təbrik edib nə davam etdirməli
olduğunu de)."""


def generate_match_coach_tip(nick, kills, assists, deaths, elo_before, elo_after, won) -> str:
    """Qısa, tək-mərhələli AI Coach məsləhəti qaytarır. Xəta/açar yoxdursa None."""
    if not client:
        return None
    kd = round(kills / max(deaths, 1), 2)
    elo_diff = elo_after - elo_before
    prompt = (
        f"Oyunçu: {nick}\n"
        f"Nəticə: {'Qələbə' if won else 'Məğlubiyyət'}\n"
        f"K/A/D: {kills}/{assists}/{deaths} (K/D {kd})\n"
        f"ELO dəyişimi: {'+' if elo_diff >= 0 else ''}{elo_diff} ({elo_before} → {elo_after})"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COACH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


NEWS_SYSTEM_PROMPT = """Sen Zenith's Academy-nin (Standoff 2 Azərbaycan icması) rəsmi
"Zenith Xəbərləri" bülleteni yazarısan. Verilmiş gündəlik statistikaya əsasən,
real idman jurnalisti üslubunda, canlı və maraqlı bir paraqraf (3-5 cümlə) yaz.
Azərbaycan dilində yaz. Emoji istifadə etmə. Quru rəqəm sadalama yox, hekayə kimi yaz."""


def generate_daily_news(stats: dict) -> str:
    """Gündəlik statistikadan Claude ilə qısa "xəbər bülleteni" mətni yaradır. Xəta/açar yoxdursa None."""
    if not ANTHROPIC_API_KEY:
        return None
    top = stats.get("top_player")
    prompt = (
        f"Bugünkü statistika:\n"
        f"Matç sayı: {stats.get('match_count', 0)}\n"
        f"Yeni qeydiyyat: {stats.get('new_players', 0)}\n"
        f"Ümumi kill: {stats.get('total_kills', 0)}\n"
        f"Ən aktiv oyunçu: {(top[0] + ' (' + str(top[1]) + ' matç)') if top else 'yoxdur'}"
    )
    try:
        import anthropic as _ant
        client_a = _ant.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client_a.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[
                {"role": "user", "content": f"{NEWS_SYSTEM_PROMPT}\n\n{prompt}"}
            ]
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


INTEL_SYSTEM_PROMPT = """Sen Zenith's Academy-nin Standoff 2 taktiki köməkçisisən.
Oyunçuya matç başlamazdan əvvəl, rəqib komandanın seçilmiş xəritədəki tarixi
performansına əsasən, 1-2 cümləlik qısa "kəşfiyyat" qeydi ver. Azərbaycan dilində
yaz. Emoji istifadə etmə. Konkret və taktiki ol, ümumi sözlər yazma."""


def generate_intel_briefing(nick, opponent_map_stats: dict, selected_map: str) -> str:
    """Rəqib komandanın xəritə statistikasına əsaslanan qısa taktiki DM mətni. Xəta/açar yoxdursa None."""
    if not client:
        return None
    wins = opponent_map_stats.get("wins", 0)
    losses = opponent_map_stats.get("losses", 0)
    total = wins + losses
    if total == 0:
        win_rate_text = "rəqib komandanın bu xəritədə əvvəlki məlumatı yoxdur"
    else:
        wr = round(wins / total * 100, 1)
        win_rate_text = f"rəqib komanda {selected_map} xəritəsində tarixən {wr}% qalib gəlib ({wins}Q/{losses}M)"
    prompt = f"Oyunçu: {nick}\nXəritə: {selected_map}\n{win_rate_text}"
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": INTEL_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None
