"""
Amazon Depo iPhone Monitor — Configuration
Kullanıcı tanımlı fiyat eşikleri ve tarama ayarları.
"""

# ── Fiyat Eşikleri (₺) ────────────────────────────────────────────────────────
# Bu değerlerin ALTINDA bir fiyat tespit edilince bildirim gönderilir.
# En spesifik modelden en genele doğru sıralanmıştır (doğru eşleşme için).
PRICE_THRESHOLDS: list[tuple[str, int]] = [
    # iPhone 17 serisi
    ("iphone 17 pro max", 75_000),
    ("iphone 17 pro",     75_000),
    ("iphone 17 plus",    60_000),
    ("iphone air",        72_000),
    ("iphone 17",         60_000),
    # iPhone 16 serisi
    ("iphone 16 pro max", 65_000),
    ("iphone 16 pro",     65_000),
    ("iphone 16 plus",    52_000),
    ("iphone 16",         52_000),
    # iPhone 15 serisi
    ("iphone 15 pro max", 60_000),
    ("iphone 15 pro",     60_000),
    ("iphone 15 plus",    48_000),
    ("iphone 15",         45_000),
    # iPhone 14 serisi (ek güvence)
    ("iphone 14 pro max", 55_000),
    ("iphone 14 pro",     48_000),
    ("iphone 14 plus",    42_000),
    ("iphone 14",         38_000),
    # iPhone 13 serisi
    ("iphone 13 pro max", 45_000),
    ("iphone 13 pro",     38_000),
    ("iphone 13",         32_000),
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
    (
        "https://www.amazon.com.tr/s"
        "?i=warehouse-deals"
        "&k=iphone"
        "&m=A215JX4S9CANSO"
        "&srs=44219324031"
        "&refinements=p_123%3A110955"
    ),
    (
        "https://www.amazon.com.tr/s"
        "?i=warehouse-deals"
        "&k=apple+iphone"
        "&m=A215JX4S9CANSO"
        "&srs=44219324031"
    ),
]

# ── Bildirim Ayarları ─────────────────────────────────────────────────────────
# Bu fiyatın ALTINDAKİ ürünler (aksesuar vb.) direkt yok sayılır.
MIN_PRICE_THRESHOLD: int = 30_000

# Aynı ürün için bu oranda fiyat düşüşü olursa tekrar bildirim gönderilir
RENEW_THRESHOLD_PCT: float = 0.90   # %10 daha ucuzsa yeniden bildir

# Sayfa istekleri arasında bekleme süresi (saniye)
MIN_DELAY: float = 2.5
MAX_DELAY: float = 6.0

# Kullanılabilir Chrome impersonation versiyonları
CHROME_VERSIONS: list[str] = [
    "chrome120", "chrome123", "chrome124",
]
