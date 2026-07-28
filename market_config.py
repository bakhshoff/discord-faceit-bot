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
    {"id": "banner_ambassador", "name": "ZenBot Ambassador",
     "type": "banner", "price": 0, "file": "banner_ambassador.png", "exclusive": True},

{"id": "banner_gold", "name": "Qizili Banner", "type": "banner", "price": 200, "file": "banner_gold.png"},
    {"id": "banner_red", "name": "Qirmizi Alov Banner", "type": "banner", "price": 200, "file": "banner_red.png"},
    {"id": "banner_purple", "name": "Benovseyi Elite Banner", "type": "banner", "price": 350, "file": "banner_purple.png"},
    {"id": "banner_cyber_blue", "name": "Cyber Blue Banner", "type": "banner", "price": 400, "file": "banner_cyber_blue.png"},
    {"id": "banner_toxic_green", "name": "Toxic Green Banner", "type": "banner", "price": 400, "file": "banner_toxic_green.png"},
    # Profil Reng Temalari
    {"id": "theme_gold",   "name": "Qizil Tema",       "type": "profile_theme", "price": 400,
     "colors": {"accent":(240,185,40), "panel":(28,22,10), "border":(80,60,10), "text2":(200,160,30)}},
    {"id": "theme_teal",   "name": "Teal Tema",         "type": "profile_theme", "price": 400,
     "colors": {"accent":(40,200,175), "panel":(10,28,26), "border":(15,65,60), "text2":(30,170,150)}},
    {"id": "theme_red",    "name": "Qirmizi Alov Tema", "type": "profile_theme", "price": 400,
     "colors": {"accent":(220,60,50),  "panel":(28,10,10), "border":(70,15,15), "text2":(190,50,40)}},
    {"id": "theme_purple", "name": "Benovseyi Tema",    "type": "profile_theme", "price": 400,
     "colors": {"accent":(160,90,255), "panel":(20,12,32), "border":(55,25,80), "text2":(130,70,220)}},
    {"id": "theme_blue",   "name": "Mavi Tema",         "type": "profile_theme", "price": 400,
     "colors": {"accent":(60,140,255), "panel":(10,18,32), "border":(20,45,80), "text2":(50,120,220)}},

    {"id": "frame_cyan", "name": "Neon Mavi Cercive", "type": "avatar_frame", "price": 300, "file": "frame_cyan.png"},
    {"id": "frame_pink", "name": "Neon Cehrayi Cercive", "type": "avatar_frame", "price": 300, "file": "frame_pink.png"},
    {"id": "frame_green", "name": "Neon Yasil Cercive", "type": "avatar_frame", "price": 300, "file": "frame_green.png"},
    {"id": "frame_purple", "name": "Neon Benovseyi Cercive", "type": "avatar_frame", "price": 450, "file": "frame_purple.png"},
    {"id": "frame_gold", "name": "Neon Qizili Cercive", "type": "avatar_frame", "price": 500, "file": "frame_gold.png"},
]


def get_item_by_id(item_id):
    for item in MARKET_ITEMS:
        if item["id"] == item_id:
            return item
    return None
