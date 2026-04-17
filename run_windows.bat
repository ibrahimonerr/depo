@echo off
TITLE Amazon Depo iPhone Monitor
COLOR 0A

:: Telegram Ayarlarını Buraya Girin
set TELEGRAM_BOT_TOKEN=8642556031:AAH4hcajlI-6kQTOP06s1yjTZ_WHBPUhAXw
set TELEGRAM_CHAT_ID=744380327

echo --------------------------------------------------
echo      AMAZON DEPO IPHONE MONITOR (WINDOWS)
echo --------------------------------------------------
echo.

:: Python kontrolü
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen python.org'dan yukleyin.
    pause
    exit /b
)

:: Gerekli kutuphaneleri yukle
echo [1/2] Kutup haneler kontrol ediliyor/yukleniyor...
python -m pip install --upgrade pip
python -m pip install curl_cffi beautifulsoup4 lxml requests

:: Botu baslat
echo.
echo [2/2] Bot baslatiliyor (80 sn dongu modu aktif)...
echo Durdurmak icin bu pencereyi kapatabilir veya Ctrl+C yapabilirsiniz.
echo.

python src/scraper.py --loop

pause
