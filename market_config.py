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
    {"id": "banner_ambassador", "name": "Calestify Ambassador",
     "type": "banner", "price": 0, "file": "banner_ambassador.png", "exclusive": True},

{"id": "banner_gold", "name": "Qizili Banner", "type": "banner", "price": 200, "file": "banner_gold.png"},
    {"id": "banner_red", "name": "Qirmizi Alov Banner", "type": "banner", "price": 200, "file": "banner_red.png"},
    {"id": "banner_purple", "name": "Benovseyi Elite Banner", "type": "banner", "price": 350, "file": "banner_purple.png"},
    {"id": "banner_cyber_blue", "name": "Cyber Blue Banner", "type": "banner", "price": 400, "file": "banner_cyber_blue.png"},
    {"id": "banner_toxic_green", "name": "Toxic Green Banner", "type": "banner", "price": 400, "file": "banner_toxic_green.png"},
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
