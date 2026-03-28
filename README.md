# 📱 Amazon Depo iPhone Monitor Bot

Amazon Türkiye'nin **Warehouse Deals (Depo)** bölümünü her **5 dakikada** bir otomatik tarar. Belirlenen fiyat eşiğinin altında bir iPhone tespit ettiğinde anında **Telegram bildirimi** gönderir.

---

## 🔥 Fiyat Eşikleri

| Model | Bildirim Eşiği |
|---|---|
| iPhone 17 Pro / Pro Max | < 75.000 ₺ |
| iPhone 17 / 17 Air / 17 Plus | < 60.000 ₺ |
| iPhone 16 Pro / Pro Max | < 65.000 ₺ |
| iPhone 15 Pro / Pro Max | < 60.000 ₺ |

> Eşikler `src/config.py` dosyasından kolayca güncellenir.

---

## ⚙️ Kurulum

### 1. Bu repoyu GitHub'a yükle

```bash
cd /Users/ibrahimoner/Desktop/depo
git init
git add .
git commit -m "feat: initial commit — Amazon Depo iPhone Monitor"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADIN/amazon-depo-monitor.git
git push -u origin main
```

> ⚠️ **Repo'yu Public yapın** — GitHub Actions sınırsız ücretsiz dakika.

---

### 2. Telegram Bot Oluştur

1. Telegram'da **@BotFather**'a mesaj at
2. `/newbot` komutunu gönder
3. Bot adı ve kullanıcı adı belirle
4. Aldığın **token**'ı kaydet (örn: `7123456789:AAF...`)
5. Botu başlatmak için `https://t.me/BOT_KULLANICI_ADI` linkine git ve `/start` gönder
6. **Chat ID**'ni bulmak için:
   - `https://api.telegram.org/botTOKEN/getUpdates` adresine git
   - JSON çıktısındaki `"id"` değerini al (negatif olabilir — kanal ise)

---

### 3. GitHub Secrets Ekle

Repo **Settings → Secrets and variables → Actions → New repository secret**:

| Secret Adı | Değer |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan aldığın token |
| `TELEGRAM_CHAT_ID` | Chat/kanal ID'si |

---

### 4. GitHub Actions İzinlerini Ayarla

Repo **Settings → Actions → General → Workflow permissions**:
- ✅ **Read and write permissions** seç
- ✅ **Allow GitHub Actions to create and approve pull requests** işaretle
- **Save**

---

## 🧪 Test

### Lokal test (bildirim göndermeden):
```bash
pip install -r requirements.txt
python src/scraper.py --dry-run
```

### Test bildirimi gönder:
```bash
export TELEGRAM_BOT_TOKEN="TOKEN_BURAYA"
export TELEGRAM_CHAT_ID="CHAT_ID_BURAYA"
python src/notifier.py
```

### Normal çalıştır:
```bash
python src/scraper.py
```

---

## 📁 Proje Yapısı

```
depo/
├── .github/
│   └── workflows/
│       └── monitor.yml      # GitHub Actions (5 dk'da bir)
├── src/
│   ├── scraper.py           # Ana tarayıcı
│   ├── notifier.py          # Telegram bildirimi
│   └── config.py            # Fiyat eşikleri ve ayarlar
├── state/
│   └── seen_deals.json      # Daha önce bildirilen ürünler
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📊 Nasıl Çalışır?

```
GitHub Actions (cron: */5 * * * *)
        │
        ▼
scraper.py
        │
        ├── Amazon TR Warehouse Deals → iPhone arama
        │   (curl-cffi ile Chrome browser impersonation)
        │
        ├── parse_products() → ASIN, başlık, fiyat, durum
        │
        ├── get_threshold() → Model eşleştir, eşik kontrol et
        │
        └── Fiyat < Eşik + Daha önce bildirilmedi
                │
                ▼
          Telegram bildirimi 🔔
                │
                ▼
          state/seen_deals.json güncelle
                │
                ▼
          git commit & push [skip ci]
```

---

## 💬 Örnek Bildirim

```
🔥 AMAZON DEPO — iPhone FIRSATI!
━━━━━━━━━━━━━━━━━━━━━

📱 Apple iPhone 15 Pro Max 256GB Siyah Titanyum

💰 Fiyat:   52.999 ₺
📊 Eşik:    60.000 ₺
💸 Tasarruf: 7.001 ₺ (%12)
📦 Durum:   İyi — Kutu hasarlı

🛒 Ürünü Hemen Gör →

⏰ 28.03.2026 23:55
```

---

## 🔧 Fiyat Eşiklerini Güncelleme

`src/config.py` dosyasını düzenle:

```python
PRICE_THRESHOLDS = [
    ("iphone 17 pro max", 75_000),   # Buraya yeni eşik gir
    ...
]
```

Commit'le ve push'la — bir sonraki çalışmada yeni eşikler devreye girer.
