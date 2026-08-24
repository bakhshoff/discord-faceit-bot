"""Standoff 2-nin rəsmi help.standoff2.com saytındakı 'Updates Description' bölməsini
izləyir, yeni yenilik məqaləsi aşkarlananda tam mətnini çəkib Azərbaycan dilində qısa
elan mətninə çevirir. Sayt Intercom Help Center (Next.js) üzərində qurulub — səhifənin
HTML-i daxilindəki <script id="__NEXT_DATA__"> JSON blokunda strukturlaşdırılmış data
var, ayrıca HTML parser (BeautifulSoup və s.) lazım deyil.
"""
import re
import json
import os
import requests

UPDATES_COLLECTION_URL = "https://help.standoff2.com/en/collections/2971735-updates-description"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_TAG_RE = re.compile(r"<[^>]+>")


def _extract_next_data(html: str) -> dict:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("__NEXT_DATA__ tapılmadı — sayt strukturu dəyişmiş ola bilər")
    return json.loads(m.group(1))


def get_latest_update_articles(limit=5):
    """Kolleksiya səhifəsindəki ən son yenilik məqalələrini qaytarır:
    [{"id", "title", "url", "last_updated_date"}, ...] (yenidən köhnəyə doğru)."""
    resp = requests.get(UPDATES_COLLECTION_URL, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    data = _extract_next_data(resp.text)
    summaries = data["props"]["pageProps"]["collection"]["articleSummaries"]
    out = []
    for s in summaries[:limit]:
        out.append({
            "id": s["id"], "title": s["title"], "url": s["url"],
            "last_updated_date": s.get("lastUpdatedDate"),
        })
    return out


def fetch_article_text(url: str):
    """Bir məqalənin başlığını və tam sadə-mətn məzmununu qaytarır: (title, text)."""
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    data = _extract_next_data(resp.text)
    article = data["props"]["pageProps"]["articleContent"]
    title = article.get("title", "")
    parts = []
    for block in article.get("blocks", []):
        text = (block.get("text") or "").strip()
        if text:
            parts.append(_TAG_RE.sub("", text))
    return title, "\n".join(parts)


NEWS_TRANSLATE_SYSTEM_PROMPT = """Sen Zenith's Academy-nin (Standoff 2 Azərbaycan icması) rəsmi
xəbər redaktorusan. Sənə Standoff 2 oyununun rəsmi yenilik (patch notes) məqaləsinin İngiliscə
mətni verilir. Bunu Azərbaycan dilinə tərcümə edib, Discord elanı üçün yığcam, oxunaqlı formada
YENİDƏN YAZ:
- Başlıq (# ilə YOX, sadə qalın mətn kimi düşün, ayrıca göndəriləcək)
- Əsas yenilikləri maddə-maddə (əgər çox uzundursa yalnız ən vacib 6-8 maddəni seç)
- Qısa, canlı, həvəsləndirici dil — quru tərcümə yox
- Emoji istifadə etmə
- Discord mesajı üçün formatla: hər maddə "•" ilə başlasın, maddələr arası boş sətir olmasın
Yalnız yekun Azərbaycan mətnini qaytar, başqa şərh əlavə etmə."""


def summarize_article_az(title: str, text: str):
    """Məqalə mətnini Azərbaycan dilində Discord elanına uyğun qısa mətnə çevirir.
    Xəta/açar yoxdursa None qaytarır (çağıran tərəf bunu emal etməlidir)."""
    from ai_chat import client, MODEL
    if not client:
        return None
    truncated = text[:6000]
    prompt = f"Başlıq: {title}\n\nMətn:\n{truncated}"
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": NEWS_TRANSLATE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None
