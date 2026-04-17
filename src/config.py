"""
Amazon Depo iPhone Monitor — Configuration
Kullanıcı tanımlı fiyat eşikleri ve tarama ayarları.
"""

# ── Fiyat Eşikleri (₺) ────────────────────────────────────────────────────────
# Bu değerlerin ALTINDA bir fiyat tespit edilince bildirim gönderilir.
# En spesifik modelden en genele doğru sıralanmıştır (doğru eşleşme için).
PRICE_THRESHOLDS: list[tuple[str, int]] = [
    # iPhone 17 serisi
    ("iphone 17 pro max", 80_000),
    ("iphone 17 pro",     80_000),
    ("iphone 17 air",     60_000),
    ("iphone 17",         60_000),
    # iPhone 16 Pro serisi
    ("iphone 16 pro max", 60_000),
    ("iphone 16 pro",     60_000),
    # iPhone Air (Genel)
    ("iphone air",        60_000),
]


def get_threshold(title: str) -> tuple:
    """iPhone model adına göre fiyat eşiğini döndürür."""
    title_lower = title.lower()
    for model, threshold in PRICE_THRESHOLDS:
        if model in title_lower:
            return model, threshold
    return None, None


# ── Amazon Depo Arama URL'leri ────────────────────────────────────────────────
# Seller ID (Amazon Warehouse TR): A215JX4S9CANSO
# Kategori referansı: srs=44219324031
# Apple marka filtresi: refinements=p_123%3A110955
SEARCH_URLS: list[str] = [
    # 1. Genel iPhone Araması (Apple Marka Filtreli - En Kararlı)
    "https://www.amazon.com.tr/s?i=warehouse-deals&k=iphone&m=A215JX4S9CANSO&srs=44219324031&refinements=p_123%3A110955",
    
    # 2. Nokta Atışı Model Aramaları (iPhone 17 Serisi)
    "https://www.amazon.com.tr/s?k=iphone+17+pro+max&i=warehouse-deals&m=A215JX4S9CANSO&srs=44219324031",
    "https://www.amazon.com.tr/s?k=iphone+17+pro&i=warehouse-deals&m=A215JX4S9CANSO&srs=44219324031",
    "https://www.amazon.com.tr/s?k=iphone+17&i=warehouse-deals&m=A215JX4S9CANSO&srs=44219324031",
]

# ── Bildirim Ayarları ─────────────────────────────────────────────────────────
# Bu fiyatın ALTINDAKİ ürünler (aksesuar vb.) direkt yok sayılır.
MIN_PRICE_THRESHOLD: int = 45_000

# Aynı ürün için bu oranda fiyat düşüşü olursa tekrar bildirim gönderilir
RENEW_THRESHOLD_PCT: float = 0.90   # %10 daha ucuzsa yeniden bildir

# Sayfa istekleri arasında bekleme süresi (saniye)
MIN_DELAY: float = 3.0
MAX_DELAY: float = 7.0

# HTTP hata durumunda tekrar deneme sayısı ve bekleme süresi (saniye)
FETCH_RETRIES: int   = 2
RETRY_DELAY:   float = 15.0

# Her URL için kaç sayfa taransın (Hız için 1 sayfa önerilir)
MAX_PAGES: int = 1

# Kullanılabilir Chrome impersonation versiyonları
CHROME_VERSIONS: list[str] = [
    "chrome120", "chrome123", "chrome124",
]
