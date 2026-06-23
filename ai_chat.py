import os
import time
import sqlite3
import json
from groq import Groq

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "."), "bot_database.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

HISTORY_LIMIT = 20
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Sen Calestify Gaming Community-nin Discord botusun. Standoff 2 mobile oyunu üzrə turnirləri idarə edirsən.

Cəmiyyət haqqında:
- Calestify — Azərbaycanlı Standoff 2 oyunçularının toplumu
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
