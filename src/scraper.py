"""
Amazon Depo iPhone Monitor — Main Scraper
Amazon Türkiye Warehouse Deals bölümünü tarar, fiyat eşiği altındaki
iPhone ürünleri için Telegram bildirimi gönderir.

Kullanım:
    python src/scraper.py               # Normal çalışma
    python src/scraper.py --dry-run     # Bildirim gönderme, sadece logla
    python src/scraper.py --test        # Test bildirimi gönder ve çık
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import (
    CHROME_VERSIONS, FETCH_RETRIES, MAX_DELAY, MAX_PAGES,
    MIN_DELAY, MIN_PRICE_THRESHOLD, RENEW_THRESHOLD_PCT,
    RETRY_DELAY, SEARCH_URLS, get_threshold,
)
from notifier import send_telegram_notification, send_test_notification

STATE_FILE = ROOT / "state" / "seen_deals.json"


# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── State ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
                # Migrate: eski list formatı
                if isinstance(data.get("seen"), list):
                    data["seen"] = {
                        asin: {"price": 0, "seen_at": datetime.now().isoformat()}
                        for asin in data["seen"]
                    }
                # Migrate: eski int formatı → yeni dict formatı
                migrated = {}
                for asin, val in data.get("seen", {}).items():
                    if isinstance(val, int):
                        migrated[asin] = {"price": val, "seen_at": datetime.now().isoformat()}
                    else:
                        migrated[asin] = val
                data["seen"] = migrated
                return data
        except (json.JSONDecodeError, IOError):
            log("⚠️  State dosyası bozuk, sıfırlanıyor...")
    return {"seen": {}, "last_run": None, "deals_found_total": 0}


def save_state(state: dict) -> None:
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def cleanup_state(state: dict) -> int:
    """24 saatten eski kayıtları state'den temizler; tekrar taramaları sağlar."""
    now = datetime.now()
    to_remove = []
    for asin, info in state["seen"].items():
        try:
            seen_at = datetime.fromisoformat(info.get("seen_at", ""))
            if (now - seen_at).total_seconds() > 86_400:  # 24 saat
                to_remove.append(asin)
        except (ValueError, TypeError):
            to_remove.append(asin)
    for asin in to_remove:
        del state["seen"][asin]
    return len(to_remove)


# ── Price Parsing ─────────────────────────────────────────────────────────────

def parse_price(text: str) -> int | None:
    """
    Amazon TR fiyat formatını parse eder.
    '68.874,05 TL', '₺52.999', '52.999' → int
    """
    if not text:
        return None
    # Sembol ve boşlukları kaldır
    cleaned = re.sub(r"[₺TL$€\s]", "", text)
    # Binler ayracı noktası: 68.874 → 68874 (son ,xx ondalığını da kaldır)
    cleaned = re.sub(r",\d+$", "", cleaned)   # ,05 ondalık kısmı kaldır
    cleaned = cleaned.replace(".", "")         # binler ayracı noktaları kaldır
    try:
        val = int(float(cleaned))
        return val if val >= 1_000 else None
    except (ValueError, TypeError):
        return None


# ── HTML Parsing ──────────────────────────────────────────────────────────────

def parse_products(html: str) -> list[dict]:
    """Amazon TR arama sayfasından ürünleri çıkarır."""
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select('[data-component-type="s-search-result"]')
    log(f"   📦 {len(cards)} ürün kartı bulundu")

    products: list[dict] = []

    for card in cards:
        try:
            asin = (card.get("data-asin") or "").strip()
            if not asin:
                continue

            # ── Başlık: h2 içindeki span veya aria-label
            title = ""
            h2 = card.select_one("h2")
            if h2:
                span = h2.select_one("span")
                title = span.get_text(strip=True) if span else ""
                if not title:
                    title = h2.get("aria-label", "").strip()
            if not title:
                continue

            # ── Fiyat: çok katmanlı fallback
            price: int | None = None
            price_text = ""

            # 1. a-offscreen (genellikle gizli ama tam değer içerir)
            for sel in ["span.a-offscreen", "span.a-price-whole"]:
                el = card.select_one(sel)
                if el:
                    cand = parse_price(el.get_text(strip=True))
                    if cand:
                        price = cand
                        price_text = el.get_text(strip=True)
                        break

            # 2. "TL" içeren .a-color-base span'ı
            if not price:
                for el in card.find_all("span", class_="a-color-base"):
                    txt = el.get_text(strip=True)
                    if "TL" in txt and any(c.isdigit() for c in txt):
                        cand = parse_price(txt)
                        if cand:
                            price = cand
                            price_text = txt
                            break

            # 3. Kartın metin satırlarından TL içereni bul (uzunluk limitini artırdık)
            if not price:
                lines = card.get_text(separator="\n").split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # TL ile biten veya içeren, sadece rakam/nokta/virgül içeren fiyat satırı
                    if "TL" in line and any(c.isdigit() for c in line) and len(line) < 50:
                        cand = parse_price(line)
                        if cand and cand >= MIN_PRICE_THRESHOLD:
                            price = cand
                            price_text = line
                            break

            if not price:
                continue

            # ── Ürün linki
            link_el = (
                card.select_one("h2 a.a-link-normal")
                or card.select_one("a.a-link-normal[href*='/dp/']")
            )
            if not link_el:
                continue
            href = link_el.get("href", "")
            if not href:
                continue
            full_link = (
                f"https://www.amazon.com.tr{href}" if href.startswith("/") else href
            )
            # Temiz URL
            dp_match = re.search(r"/dp/([A-Z0-9]{10})", full_link)
            if dp_match:
                full_link = f"https://www.amazon.com.tr/dp/{dp_match.group(1)}"

            # ── Durum / Depo notuna odaklan (Yeni gibi, Çok iyi vb.)
            condition = "İkinci El / Depo Ürünü"
            kws = [
                "yeni gibi", "çok iyi", "iyi", "kabul edilebilir", "mükemmel",
                "hasar", "yenile", "az kullanılmış", "İkinci El",
                "like new", "very good", "good", "acceptable", "renewed",
            ]
            for line in card.get_text(separator="\n").split("\n"):
                line = line.strip()
                if any(kw.lower() in line.lower() for kw in kws) and len(line) < 80:
                    condition = line
                    break

            # ── Görsel
            img_el = card.select_one("img.s-image")
            image_url = img_el.get("src") if img_el else None

            products.append(
                {
                    "asin":        asin,
                    "title":       title,
                    "price":       price,
                    "price_text":  price_text,
                    "link":        full_link,
                    "condition":   condition,
                    "image_url":   image_url,
                    "detected_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                }
            )

        except Exception as exc:
            log(f"   ⚠️  Kart işleme hatası: {exc}")
            continue

    return products


# ── HTTP Fetcher ──────────────────────────────────────────────────────────────

def warmup_session(session) -> bool:
    """
    Amazon ana sayfasını ziyaret ederek geçerli session cookie'leri alır.
    Bu olmadan warehouse search 503 verebilir.
    """
    try:
        log("🍪 Session ısındırılıyor (ana sayfa)...")
        resp = session.get(
            "https://www.amazon.com.tr",
            timeout=20,
            headers={
                "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
            },
            verify=False
        )
        if resp.status_code == 200:
            log("   ✅ Session hazır")
            return True
        log(f"   ⚠️  Ana sayfa HTTP {resp.status_code}")
        return False
    except Exception as exc:
        log(f"   ⚠️  Session warmup hatası: {exc}")
        return False


def fetch_page(url: str, session) -> str | None:
    """Sayfayı browser impersonation + session cookie ile çeker. 503 alınırsa retry yapar."""
    for attempt in range(FETCH_RETRIES + 1):
        try:
            resp = session.get(
                url,
                timeout=25,
                headers={
                    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Referer":         "https://www.amazon.com.tr/",
                },
                verify=False
            )
            if resp.status_code == 200:
                return resp.text
            if resp.status_code == 503 and attempt < FETCH_RETRIES:
                log(f"   ⚠️  HTTP 503 — {int(RETRY_DELAY)}s sonra tekrar deneniyor ({attempt + 1}/{FETCH_RETRIES})...")
                time.sleep(RETRY_DELAY)
                continue
            log(f"   ❌ HTTP {resp.status_code}")
            return None
        except Exception as exc:
            if attempt < FETCH_RETRIES:
                log(f"   ⚠️  Fetch hatası, tekrar deneniyor: {exc}")
                time.sleep(RETRY_DELAY)
                continue
            log(f"   ❌ Fetch hatası: {exc}")
            return None
    return None



def is_blocked(html: str) -> bool:
    """CAPTCHA veya bot-engel sayfası döndü mü?"""
    lower = html.lower()
    return (
        "captcha" in lower
        or "robot check" in lower
        or "automated access" in lower
        or len(html) < 5_000
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    log("🚀 Amazon Depo iPhone Monitor başlatıldı")
    if dry_run:
        log("⚠️  DRY-RUN modu — bildirim gönderilmeyecek")

    if not dry_run:
        if not os.environ.get("TELEGRAM_BOT_TOKEN"):
            log("❌ TELEGRAM_BOT_TOKEN eksik!")
            sys.exit(1)
        if not os.environ.get("TELEGRAM_CHAT_ID"):
            log("❌ TELEGRAM_CHAT_ID eksik!")
            sys.exit(1)

    state = load_state()
    cleaned = cleanup_state(state)
    if cleaned:
        log(f"🧹 {cleaned} eski kayıt temizlendi (24 saat geçti)")
    log(f"📋 Kayıtlı {len(state['seen'])} ürün var")

    # Session oluştur (Windows SSL hatalarını önlemek için verify=False)
    session = cffi.Session(impersonate=random.choice(CHROME_VERSIONS), verify=False)
    log(f"🌐 Impersonation: {session.impersonate}")

    # Session warmup: ana sayfayı ziyaret ederek cookie al
    warmup_session(session)
    delay = random.uniform(2.0, 4.0)
    log(f"⏸️  {delay:.1f}s bekleniyor...")
    time.sleep(delay)

    all_products: list[dict] = []
    blocked_urls = 0

    for i, url in enumerate(SEARCH_URLS):
        for page in range(1, MAX_PAGES + 1):
            page_url = f"{url}&page={page}" if page > 1 else url
            log(f"\n🔍 [{i + 1}/{len(SEARCH_URLS)}] Sayfa {page}/{MAX_PAGES} taranıyor...")
            log(f"   {page_url[:90]}...")

            html = fetch_page(page_url, session)

            if not html:
                log("   ⛔ Sayfa alınamadı")
                blocked_urls += 1
                break  # Bu URL için sayfa taramasını durdur

            if is_blocked(html):
                log("   ⛔ Bot koruması/CAPTCHA tespit edildi")
                blocked_urls += 1
                break

            products = parse_products(html)
            all_products.extend(products)

            if len(products) == 0:
                log(f"   ℹ️  Sayfa {page} boş — daha fazla sayfa yok")
                break

            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            log(f"   ⏸️  {delay:.1f}s bekleniyor...")
            time.sleep(delay)

    if blocked_urls >= len(SEARCH_URLS):
        log("\n⛔ Tüm URL'ler erişilemez. Bir sonraki çalışmada tekrar denenecek.")
        save_state(state)
        return

    # ASIN bazında deduplikasyon
    seen: set[str] = set()
    unique = []
    for p in all_products:
        if p["asin"] not in seen:
            seen.add(p["asin"])
            unique.append(p)

    log(f"\n📦 {len(unique)} benzersiz ürün analiz ediliyor...")

    new_deals = 0

    for product in unique:
        # ── 1. Minimum fiyat kontrolü (Aksesuar filtreleme)
        if product["price"] < MIN_PRICE_THRESHOLD:
            continue

        # ── 2. Model ve Üst Eşik Kontrolü
        model, threshold = get_threshold(product["title"])
        if threshold is None:
            continue

        if product["price"] >= threshold:
            continue

        asin       = product["asin"]
        info       = state["seen"].get(asin)
        last_price = info["price"] if info else None

        if last_price is None:
            reason = "yeni fırsat"
        elif product["price"] < last_price * RENEW_THRESHOLD_PCT:
            reason = f"fiyat düştü {last_price:,}₺ → {product['price']:,}₺"
        else:
            continue

        log(
            f"\n🔥 FIRSAT → {product['title'][:65]}\n"
            f"   💰 {product['price']:,}₺ | eşik: {threshold:,}₺ | {reason}"
        )

        if not dry_run:
            ok = send_telegram_notification(product, model, threshold)
            if ok:
                state["seen"][asin] = {"price": product["price"], "seen_at": datetime.now().isoformat()}
                state["deals_found_total"] = state.get("deals_found_total", 0) + 1
                new_deals += 1
                log("   ✅ Bildirim gönderildi")
                time.sleep(1)
            else:
                log("   ❌ Bildirim gönderilemedi!")
        else:
            log("   [DRY-RUN] Bildirim atlandı")
            new_deals += 1

    log(f"\n✅ Tamamlandı — {new_deals} yeni fırsat bildirildi")
    log(f"📊 Toplam bildirim: {state.get('deals_found_total', 0)}")
    save_state(state)
    log("💾 State kaydedildi")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amazon Depo iPhone Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Bildirim göndermeden logla")
    parser.add_argument("--test",    action="store_true", help="Test bildirimi gönder ve çık")
    parser.add_argument("--loop",    action="store_true", help="5 dakikada bir sürekli çalıştır")
    args = parser.parse_args()

    if args.test:
        log("📤 Test bildirimi gönderiliyor...")
        ok = send_test_notification()
        log("✅ Başarılı!" if ok else "❌ Başarısız!")
        sys.exit(0 if ok else 1)

    if args.loop:
        INTERVAL = 80  # 1 dk 20 sn
        log(f"🔄 Loop modu aktif — her {INTERVAL} saniyede bir taranacak")
        log("⛔ Durdurmak için Ctrl+C yapın\n")
        run = 1
        while True:
            log(f"━━━ Tarama #{run} ━━━")
            try:
                main(dry_run=args.dry_run)
            except Exception as exc:
                log(f"❌ Beklenmeyen hata: {exc}")
            log(f"⏳ Sonraki tarama {INTERVAL // 60} dakika sonra...\n")
            time.sleep(INTERVAL)
            run += 1
    else:
        main(dry_run=args.dry_run)
