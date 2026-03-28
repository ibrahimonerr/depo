"""
Amazon Depo iPhone Monitor — Telegram Notifier
Tespit edilen fırsatları Telegram'a gönderir.
"""

import os
import sys
from datetime import datetime

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _format_price(amount: int) -> str:
    """52999 → '52.999'"""
    return f"{amount:,}".replace(",", ".")


def send_telegram_notification(deal: dict, model: str, threshold: int) -> bool:
    """
    Bir fırsat için Telegram bildirimi gönderir.

    Args:
        deal:      Scraped ürün verisi (asin, title, price, link, condition, ...)
        model:     Eşleşen iPhone model adı (örn. 'iphone 15 pro max')
        threshold: Tanımlı fiyat eşiği (₺)

    Returns:
        True if sent successfully, False otherwise.
    """
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik!")
        return False

    savings     = threshold - deal["price"]
    savings_pct = round((savings / threshold) * 100)
    price_fmt   = _format_price(deal["price"])
    thresh_fmt  = _format_price(threshold)
    savings_fmt = _format_price(savings)

    title_clean = deal["title"].replace("*", "").replace("_", "").replace("`", "")
    
    # Gereksiz kelimeleri temizle
    TO_REMOVE = [
        "Apple ", "iPhone için ", " özellikli ",
        "Siyah", "Beyaz", "Mavi", "Yeşil", "Sarı", "Kırmızı", "Mor", "Pembe",
        "Titanyum", "Naturel", "Doğal", "Çöl", "Altın", "Gümüş", "Uzay", "Gece", "Yıldız",
        "Black", "White", "Blue", "Green", "Yellow", "Red", "Purple", "Pink",
        "Titanium", "Natural", "Desert", "Gold", "Silver", "Space", "Midnight", "Starlight"
    ]
    for word in TO_REMOVE:
        title_clean = title_clean.replace(word, "")
    
    # Fazla boşlukları temizle ve boyutu koru
    title_clean = " ".join(title_clean.split()).strip()[:100]
    
    detected = deal.get("detected_at", datetime.now().strftime("%d.%m.%Y %H:%M"))

    message = (
        f"📱 *{title_clean} — {price_fmt} ₺*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Eşik:  _{thresh_fmt} ₺_\n"
        f"📦 Durum: *{deal.get('condition', 'İkinci El / Depo')}*\n\n"
        f"🛒 [Ürünü Görüntüle]({deal['link']})"
    )

    url = TELEGRAM_API.format(token=token, method="sendMessage")
    try:
        resp = requests.post(
            url,
            json={
                "chat_id":                  chat_id,
                "text":                     message,
                "parse_mode":               "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if resp.ok:
            return True
        print(f"❌ Telegram API hatası: {resp.status_code} — {resp.text[:200]}")
        return False
    except requests.RequestException as e:
        print(f"❌ Telegram bağlantı hatası: {e}")
        return False


def send_test_notification() -> bool:
    """Kurulumu doğrulamak için test bildirimi gönderir."""
    test_deal = {
        "asin":        "TEST000000",
        "title":       "Apple iPhone 15 Pro Max 256GB Siyah Titanyum — [TEST MESAJI]",
        "price":       42_000,
        "link":        "https://www.amazon.com.tr",
        "condition":   "İyi — Kutu hasarlı",
        "detected_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    return send_telegram_notification(test_deal, "iphone 15 pro max", 60_000)


if __name__ == "__main__":
    print("📤 Test bildirimi gönderiliyor...")
    ok = send_test_notification()
    sys.exit(0 if ok else 1)
