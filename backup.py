import sqlite3
import json
import os
import time

import database

BACKUP_DIR = os.environ.get("DATA_DIR", ".")
BACKUP_PATH = os.path.join(BACKUP_DIR, "backup.json")


def export_backup():
    """Verilənlər bazasının bütün cədvəllərini JSON faylına yazır. Sürətli, lokal əməliyyatdır."""
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tables = ["players", "inventory", "giveaways", "match_counter",
              "match_history", "skins", "skin_inventory", "coin_logs"]
    data = {"exported_at": int(time.time())}

    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data[table] = [dict(row) for row in rows]
        except sqlite3.OperationalError:
            data[table] = []

    conn.close()

    tmp_path = BACKUP_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, BACKUP_PATH)

    return BACKUP_PATH


def restore_from_backup(backup_path=None):
    """
    JSON backup-dan verilənlər bazasını bərpa edir.
    DİQQƏT: mövcud cədvəllərin məzmununu silib backup-dakı ilə əvəz edir.
    Yalnız fəlakət bərpası üçün əl ilə çağırılmalıdır.
    """
    path = backup_path or BACKUP_PATH
    if not os.path.exists(path):
        return False, "Backup faylı tapılmadı."

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()

    try:
        if "players" in data:
            cursor.execute("DELETE FROM players")
            for row in data["players"]:
                cursor.execute(
                    """INSERT INTO players
                       (discord_id, so2_nick, so2_id, elo, wins, losses, coins, active_banner)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("discord_id"), row.get("so2_nick"), row.get("so2_id"),
                     row.get("elo", 1000), row.get("wins", 0), row.get("losses", 0),
                     row.get("coins", 0), row.get("active_banner"))
                )

        if "inventory" in data:
            cursor.execute("DELETE FROM inventory")
            for row in data["inventory"]:
                cursor.execute(
                    "INSERT INTO inventory (discord_id, item_id, acquired_at) VALUES (?, ?, ?)",
                    (row.get("discord_id"), row.get("item_id"), row.get("acquired_at"))
                )

        if "giveaways" in data:
            cursor.execute("DELETE FROM giveaways")
            for row in data["giveaways"]:
                cursor.execute(
                    """INSERT INTO giveaways
                       (id, mukafat, end_unix, winner_id, channel_id, message_id, finished)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("id"), row.get("mukafat"), row.get("end_unix"), row.get("winner_id"),
                     row.get("channel_id"), row.get("message_id"), row.get("finished", 0))
                )

        if "match_counter" in data:
            cursor.execute("DELETE FROM match_counter")
            for row in data["match_counter"]:
                cursor.execute(
                    "INSERT INTO match_counter (id, last_number) VALUES (?, ?)",
                    (row.get("id"), row.get("last_number", 0))
                )

        if "match_history" in data:
            cursor.execute("DELETE FROM match_history")
            for row in data["match_history"]:
                cursor.execute(
                    """INSERT INTO match_history
                       (id, match_type, played_at, match_number, winner_ids, loser_ids,
                        winner_elo_before, winner_elo_after, loser_elo_before, loser_elo_after)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("id"), row.get("match_type"), row.get("played_at"), row.get("match_number"),
                     row.get("winner_ids"), row.get("loser_ids"),
                     row.get("winner_elo_before"), row.get("winner_elo_after"),
                     row.get("loser_elo_before"), row.get("loser_elo_after"))
                )

        if "skins" in data:
            cursor.execute("DELETE FROM skins")
            for row in data["skins"]:
                cursor.execute(
                    """INSERT INTO skins (id, name, price, image_url, active, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (row.get("id"), row.get("name"), row.get("price"), row.get("image_url"),
                     row.get("active", 1), row.get("created_at"))
                )

        if "skin_inventory" in data:
            cursor.execute("DELETE FROM skin_inventory")
            for row in data["skin_inventory"]:
                cursor.execute(
                    """INSERT INTO skin_inventory
                       (id, discord_id, skin_id, skin_name, price_paid, image_url, acquired_at, delivered)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("id"), row.get("discord_id"), row.get("skin_id"), row.get("skin_name"),
                     row.get("price_paid"), row.get("image_url"), row.get("acquired_at"), row.get("delivered", 0))
                )

        if "coin_logs" in data:
            cursor.execute("DELETE FROM coin_logs")
            for row in data["coin_logs"]:
                cursor.execute(
                    """INSERT INTO coin_logs
                       (id, discord_id, change, reason, log_type, balance_after, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (row.get("id"), row.get("discord_id"), row.get("change"), row.get("reason"),
                     row.get("log_type"), row.get("balance_after"), row.get("created_at"))
                )

        conn.commit()
        result = (True, "Bərpa tamamlandı.")
    except Exception as e:
        conn.rollback()
        result = (False, f"Xəta: {e}")
    finally:
        conn.close()

    return result


def push_backup_to_github(repo_dir, github_token, github_repo, branch="main"):
    """
    backup.json-u GitHub-un Contents API-si ilə birbaşa repo-ya yazır.
    Heç bir yerli git alətinə ehtiyac yoxdur (Railway konteynerində git mövcud deyil).
    repo_dir: istifadə olunmur, geriyə uyğunluq üçün saxlanılıb.
    github_token: Personal Access Token
    github_repo: "username/repo-name" formatında
    """
    if not os.path.exists(BACKUP_PATH):
        return False, "Backup faylı mövcud deyil."

    try:
        import base64
        import requests

        with open(BACKUP_PATH, "rb") as f:
            content_bytes = f.read()
        encoded_content = base64.b64encode(content_bytes).decode("utf-8")

        api_url = f"https://api.github.com/repos/{github_repo}/contents/backup.json"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        }

        get_resp = requests.get(api_url, headers=headers, params={"ref": branch})
        sha = None
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")
        elif get_resp.status_code != 404:
            return False, f"GitHub-dan oxuma xətası: {get_resp.status_code} {get_resp.text[:200]}"

        payload = {
            "message": f"Auto backup {int(time.time())}",
            "content": encoded_content,
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload)
        if put_resp.status_code in (200, 201):
            return True, "Backup GitHub-a göndərildi."
        else:
            return False, f"Push xətası: {put_resp.status_code} {put_resp.text[:200]}"

    except Exception as e:
        return False, f"Xəta: {e}"
