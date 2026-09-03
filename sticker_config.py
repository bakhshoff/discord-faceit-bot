# Nailiyyətə görə açılan "sticker"lər — real Discord Sticker API-si İSTİFADƏ OLUNMUR (guild
# sticker slot limiti/format məhdudiyyətləri var), əvəzinə hər sticker PIL ilə generasiya
# olunan branded "badge" şəklidir və bot adından paylaşılır (bax: bot.py-dəki /stickerlerim).
STICKER_ITEMS = [
    {"id": "sticker_champion",    "name": "Şampion",     "achievement_id": "win_50",   "label": "50 QƏLƏBƏ"},
    {"id": "sticker_headhunter",  "name": "Ovçu",        "achievement_id": "kill_500", "label": "500 KILL"},
    {"id": "sticker_mvp",         "name": "MVP Ustası",  "achievement_id": "mvp_10",   "label": "10x MVP"},
    {"id": "sticker_unstoppable", "name": "Dayanılmaz",  "achievement_id": "streak_10", "label": "10 SERİYA"},
    {"id": "sticker_master",      "name": "Master",      "achievement_id": "elo_1500", "label": "1500 ELO"},
]


def get_sticker_by_achievement(achievement_id):
    return next((s for s in STICKER_ITEMS if s["achievement_id"] == achievement_id), None)


def get_sticker_by_id(sticker_id):
    return next((s for s in STICKER_ITEMS if s["id"] == sticker_id), None)
