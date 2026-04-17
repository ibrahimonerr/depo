#!/bin/bash
# Amazon Depo iPhone Monitor - Mac Baslatici

# Dosyanin bulundugu dizine git
cd "$(dirname "$0")"

# Telegram Ayarlarini Buraya Girin
export TELEGRAM_BOT_TOKEN="8642556031:AAH4hcajlI-6kQTOP06s1yjTZ_WHBPUhAXw"
export TELEGRAM_CHAT_ID="744380327"

echo "--------------------------------------------------"
echo "     AMAZON DEPO IPHONE MONITOR (macOS)"
echo "--------------------------------------------------"
echo ""

# Python kontrolü
if ! command -v python3 &> /dev/null
then
    echo "[HATA] python3 bulunamadi! Lutfen yukleyin."
    exit 1
fi

# Gerekli kutuphaneleri yukle
echo "[1/2] Kutup haneler kontrol ediliyor..."
python3 -m pip install --upgrade pip > /dev/null
python3 -m pip install curl_cffi beautifulsoup4 lxml requests > /dev/null

# Botu baslat (Caffeinate ile uykuyu engelliyoruz)
echo "[2/2] Bot baslatiliyor (5 dk dongu modu aktif)..."
echo "INFO: Caffeinate aktif, bot calisirken Mac uykuya dalmayacak."
echo "Durdurmak icin bu pencereyi kapatabilir veya Ctrl+C yapabilirsiniz."
echo ""

caffeinate -ism python3 src/scraper.py --loop
