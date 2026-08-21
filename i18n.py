"""
Sadə çoxdilli lüğət sistemi. Hazırda tam lokallaşdırılan səth: profil kartı
(profile_card.py) və ProfileHubView düymələri (bot.py). Digər komandalar
hələ yalnız Azərbaycan dilindədir — eyni `t()` funksiyası ilə addım-addım
genişləndirilə bilər.
"""

STRINGS = {
    "az": {
        "profile.header": "FACEIT PROFİLİ",
        "profile.total": "ÜMUMİ",
        "profile.season": "SEZON",
        "profile.match_line": "Matç: {matches}   Qələbə: {wins}   Məğlubiyyət: {losses}",
        "profile.winrate": "Win Rate: {wr}%",
        "profile.kill": "KİLL",
        "profile.assist": "ASİST",
        "profile.death": "ÖLÜM",
        "profile.kd": "K/D",
        "profile.season_kd": "SEZON K/D",
        "profile.level_rank": "Level {level}  |  {rank}",
        "profile.so2id": "SO2 ID: {id}",
        "profile.elo": "ELO",
        "rank.spark1": "Qığılcım I", "rank.spark2": "Qığılcım II",
        "rank.flame1": "Alov I", "rank.flame2": "Alov II",
        "rank.nova1": "Nova I", "rank.nova2": "Nova II",
        "rank.supernova": "Supernova", "rank.zenith": "Zenit",
        "btn.stats": "Stats", "btn.history": "Tarixçə", "btn.inventory": "İnventar",
        "btn.market": "Market", "btn.coins": "Coin", "btn.achievements": "Nailiyyətlər",
        "btn.daily": "Gündəlik", "btn.maps": "Xəritələr", "btn.record": "Rekord",
        "btn.squad": "Squad", "btn.share": "Paylaş", "btn.chart": "Qrafik",
        "btn.title": "Ləqəb", "btn.lang": "Dil", "btn.quests": "Questlər", "btn.synergy": "Sinergiya",
        "btn.pass": "Pass",
        "lang.changed": "✅ Dil dəyişdirildi: {lang_name}",
        "lang.select_placeholder": "Dili seçin...",
    },
    "en": {
        "profile.header": "FACEIT PROFILE",
        "profile.total": "TOTAL",
        "profile.season": "SEASON",
        "profile.match_line": "Matches: {matches}   Wins: {wins}   Losses: {losses}",
        "profile.winrate": "Win Rate: {wr}%",
        "profile.kill": "KILLS",
        "profile.assist": "ASSISTS",
        "profile.death": "DEATHS",
        "profile.kd": "K/D",
        "profile.season_kd": "SEASON K/D",
        "profile.level_rank": "Level {level}  |  {rank}",
        "profile.so2id": "SO2 ID: {id}",
        "profile.elo": "ELO",
        "rank.spark1": "Spark I", "rank.spark2": "Spark II",
        "rank.flame1": "Flame I", "rank.flame2": "Flame II",
        "rank.nova1": "Nova I", "rank.nova2": "Nova II",
        "rank.supernova": "Supernova", "rank.zenith": "Zenith",
        "btn.stats": "Stats", "btn.history": "History", "btn.inventory": "Inventory",
        "btn.market": "Market", "btn.coins": "Coins", "btn.achievements": "Achievements",
        "btn.daily": "Daily", "btn.maps": "Maps", "btn.record": "Record",
        "btn.squad": "Squad", "btn.share": "Share", "btn.chart": "Chart",
        "btn.title": "Title", "btn.lang": "Language", "btn.quests": "Quests", "btn.synergy": "Synergy",
        "btn.pass": "Pass",
        "lang.changed": "✅ Language changed: {lang_name}",
        "lang.select_placeholder": "Select language...",
    },
    "ru": {
        "profile.header": "ПРОФИЛЬ FACEIT",
        "profile.total": "ОБЩЕЕ",
        "profile.season": "СЕЗОН",
        "profile.match_line": "Матчи: {matches}   Победы: {wins}   Поражения: {losses}",
        "profile.winrate": "Процент побед: {wr}%",
        "profile.kill": "УБИЙСТВА",
        "profile.assist": "ПОМОЩЬ",
        "profile.death": "СМЕРТИ",
        "profile.kd": "K/D",
        "profile.season_kd": "СЕЗОН K/D",
        "profile.level_rank": "Уровень {level}  |  {rank}",
        "profile.so2id": "SO2 ID: {id}",
        "profile.elo": "ELO",
        "rank.spark1": "Искра I", "rank.spark2": "Искра II",
        "rank.flame1": "Пламя I", "rank.flame2": "Пламя II",
        "rank.nova1": "Нова I", "rank.nova2": "Нова II",
        "rank.supernova": "Сверхновая", "rank.zenith": "Зенит",
        "btn.stats": "Статистика", "btn.history": "История", "btn.inventory": "Инвентарь",
        "btn.market": "Магазин", "btn.coins": "Монеты", "btn.achievements": "Достижения",
        "btn.daily": "Ежедневно", "btn.maps": "Карты", "btn.record": "Рекорд",
        "btn.squad": "Отряд", "btn.share": "Поделиться", "btn.chart": "График",
        "btn.title": "Титул", "btn.lang": "Язык", "btn.quests": "Квесты", "btn.synergy": "Синергия",
        "btn.pass": "Пропуск",
        "lang.changed": "✅ Язык изменён: {lang_name}",
        "lang.select_placeholder": "Выберите язык...",
    },
}

LANG_NAMES = {"az": "Azərbaycan", "en": "English", "ru": "Русский"}


def t(key, lang="az", **kwargs):
    table = STRINGS.get(lang) or STRINGS["az"]
    text = table.get(key) or STRINGS["az"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
