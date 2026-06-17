# Market məhsulları konfiqurasiyası.
# Yeni banner/avatar əlavə etmək üçün bu siyahıya yeni sətir əlavə edin.
#
# id: unikal identifikator (hərflər, rəqəmlər, alt xətt - boşluq olmasın)
# name: istifadəçiyə görünən ad
# type: "banner" və ya "avatar_frame"
# price: qiymət (coin)
# file: şəkil faylının adı (bannerlər üçün banners/ qovluğunda, çərçivələr üçün frames/ qovluğunda olmalıdır)

MARKET_ITEMS = [
    {
        "id": "banner_gold",
        "name": "Qızılı Banner",
        "type": "banner",
        "price": 200,
        "file": "banner_gold.png",
    },
    {
        "id": "banner_red",
        "name": "Qırmızı Alov Banner",
        "type": "banner",
        "price": 200,
        "file": "banner_red.png",
    },
    {
        "id": "banner_purple",
        "name": "Bənövşəyi Elite Banner",
        "type": "banner",
        "price": 350,
        "file": "banner_purple.png",
    },
]


def get_item_by_id(item_id):
    for item in MARKET_ITEMS:
        if item["id"] == item_id:
            return item
    return None
