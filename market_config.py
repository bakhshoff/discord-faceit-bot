# Market mehsullari konfiqurasiyasi.
# Yeni banner/avatar elave etmek ucun bu siyahiya yeni setir elave edin.
#
# id: unikal identifikator
# name: istifadeciye gorunen ad
# type: "banner" ve ya "avatar_frame"
# price: qiymet (coin)
# file: sekil faylinin adi

MARKET_ITEMS = [
    # Xüsusi — yalnız referral sistemi ilə əldə edilə bilər, marketdə satılmır
    {"id": "banner_ambassador", "name": "Zenith's Academy Ambassador",
     "type": "banner", "price": 0, "file": "banner_ambassador.png", "exclusive": True},
    # Xüsusi — yalnız Genesis Battle Pass (VIP) ilə əldə edilə bilər, marketdə satılmır
    {"id": "banner_genesis", "name": "Genesis Banneri",
     "type": "banner", "price": 0, "file": "banner_genesis.png", "exclusive": True},
    {"id": "frame_genesis", "name": "Genesis Çərçivəsi",
     "type": "avatar_frame", "price": 0, "file": "frame_genesis.png", "exclusive": True},

{"id": "banner_venom", "name": "Venom Banner", "type": "banner", "price_azn": 2, "file": "banner_venom.png"},
    {"id": "banner_ragnar", "name": "Ragnar Banner", "type": "banner", "price_azn": 2, "file": "banner_ragnar.png"},
    {"id": "banner_gold", "name": "Qızılı Banner", "type": "banner", "price": 200, "file": "banner_gold.png"},
    {"id": "banner_red", "name": "Qırmızı Alov Banner", "type": "banner", "price": 200, "file": "banner_red.png"},
    {"id": "banner_purple", "name": "Bənövşəyi Elite Banner", "type": "banner", "price": 350, "file": "banner_purple.png"},
    {"id": "banner_cyber_blue", "name": "Cyber Blue Banner", "type": "banner", "price": 400, "file": "banner_cyber_blue.png"},
    {"id": "banner_toxic_green", "name": "Toxic Green Banner", "type": "banner", "price": 400, "file": "banner_toxic_green.png"},
    # Profil Rəng Temaları
    {"id": "theme_gold",   "name": "Qızıl Tema",       "type": "profile_theme", "price": 400,
     "colors": {"accent":(240,185,40), "panel":(28,22,10), "border":(80,60,10), "text2":(200,160,30)}},
    {"id": "theme_teal",   "name": "Teal Tema",         "type": "profile_theme", "price": 400,
     "colors": {"accent":(40,200,175), "panel":(10,28,26), "border":(15,65,60), "text2":(30,170,150)}},
    {"id": "theme_red",    "name": "Qırmızı Alov Tema", "type": "profile_theme", "price": 400,
     "colors": {"accent":(220,60,50),  "panel":(28,10,10), "border":(70,15,15), "text2":(190,50,40)}},
    {"id": "theme_purple", "name": "Bənövşəyi Tema",    "type": "profile_theme", "price": 400,
     "colors": {"accent":(160,90,255), "panel":(20,12,32), "border":(55,25,80), "text2":(130,70,220)}},
    {"id": "theme_blue",   "name": "Mavi Tema",         "type": "profile_theme", "price": 400,
     "colors": {"accent":(60,140,255), "panel":(10,18,32), "border":(20,45,80), "text2":(50,120,220)}},

    {"id": "frame_cyan", "name": "Neon Mavi Çərçivə", "type": "avatar_frame", "price": 300, "file": "frame_cyan.png"},
    {"id": "frame_pink", "name": "Neon Çəhrayı Çərçivə", "type": "avatar_frame", "price": 300, "file": "frame_pink.png"},
    {"id": "frame_green", "name": "Neon Yaşıl Çərçivə", "type": "avatar_frame", "price": 300, "file": "frame_green.png"},
    {"id": "frame_purple", "name": "Neon Bənövşəyi Çərçivə", "type": "avatar_frame", "price": 450, "file": "frame_purple.png"},
    {"id": "frame_gold", "name": "Neon Qızılı Çərçivə", "type": "avatar_frame", "price": 500, "file": "frame_gold.png"},
]


def get_item_by_id(item_id):
    for item in MARKET_ITEMS:
        if item["id"] == item_id:
            return item
    return None


# ── ELO Kartları (AZN balansı ilə satın alınır — pul-qazanma mexanizmi) ─────────
# card_type: "boost50" (qələbədə +50% ELO), "boost100" (qələbədə +100% ELO),
# "protect" (məğlubiyyətdə ELO itkisinin qarşısını alır). Hər kart tək-istifadəlikdir,
# növbəti uyğun matç nəticəsində avtomatik istifadə olunur (bax: apply_elo_modifiers).
# 100% qiymətləri 50%-ə nisbətən düz 2x təyin olunub (2x effekt üçün 2x qiymət balansı).
# Qeyd: bütün qiymətlər 2026-08-18-də 50% ENDİRİMLƏ (ilkin qiymətin yarısı) təyin olunub.
ELO_CARD_PACKS = [
    {"id": "boost50_10",   "card_type": "boost50",  "qty": 10,  "price_azn": 0.5,
     "label": "50% ELO Boost — 10 ədəd"},
    {"id": "boost50_50",   "card_type": "boost50",  "qty": 50,  "price_azn": 2,
     "label": "50% ELO Boost — 50 ədəd"},
    {"id": "boost50_100",  "card_type": "boost50",  "qty": 100, "price_azn": 4,
     "label": "50% ELO Boost — 100 ədəd"},

    {"id": "boost100_10",  "card_type": "boost100", "qty": 10,  "price_azn": 1,
     "label": "100% ELO Boost — 10 ədəd"},
    {"id": "boost100_50",  "card_type": "boost100", "qty": 50,  "price_azn": 4,
     "label": "100% ELO Boost — 50 ədəd"},
    {"id": "boost100_100", "card_type": "boost100", "qty": 100, "price_azn": 8,
     "label": "100% ELO Boost — 100 ədəd"},

    {"id": "protect_10",   "card_type": "protect",  "qty": 10,  "price_azn": 1,
     "label": "ELO Qoruma — 10 ədəd"},
    {"id": "protect_50",   "card_type": "protect",  "qty": 50,  "price_azn": 4.5,
     "label": "ELO Qoruma — 50 ədəd"},
    {"id": "protect_100",  "card_type": "protect",  "qty": 100, "price_azn": 8.5,
     "label": "ELO Qoruma — 100 ədəd"},
]


def get_elo_card_pack(pack_id):
    for pack in ELO_CARD_PACKS:
        if pack["id"] == pack_id:
            return pack
    return None
