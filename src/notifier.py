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


def _model_to_display(model: str) -> str:
    """
    'iphone 17 pro max' → 'iPhone 17 Pro Max'
    model parametresinden temiz, okunabilir başlık üretir.
    """
    words = model.split()
    result = []
    for w in words:
        if w.lower() == "iphone":
            result.append("iPhone")
        else:
            result.append(w.capitalize())
    return " ".join(result)


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

    # Başlık: "iPhone 17 Pro Max" gibi temiz model adı (Amazon açıklaması değil)
    model_display = _model_to_display(model)

    condition = deal.get("condition", "İkinci El / Depo")
    cart_link = f"https://www.amazon.com.tr/gp/aws/cart/add.html?ASIN.1={deal['asin']}&Quantity.1=1"

    message = (
        f"📱 *{model_display} — {price_fmt} ₺*\n"
        f"\n"
        f"📦 {condition}\n"
        f"💸 {savings_fmt} ₺ tasarruf (%{savings_pct})\n"
        f"🎯 Eşik: {thresh_fmt} ₺\n"
        f"\n"
        f"[🛒 Ürünü Görüntüle]({deal['link']})  ·  [⚡ Sepete Ekle]({cart_link})"
    )

    url = TELEGRAM_API.format(token=token, method="sendMessage")
    try:
        resp = requests.post(
            url,
            json={
                "chat_id":                  chat_id,
                "text":                     message,
                "parse_mode":               "Markdown",
                "disable_web_page_preview": True,
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
        "title":       "Apple iPhone 15 Pro Max 256GB Siyah Titanyum",
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
