#!/bin/bash
# Amazon Depo iPhone Monitor - macOS Otomatik Başlatma Scripti
# Bu script botu 5 dakikada bir çalıştıran bir launchd job kurar.

PLIST="$HOME/Library/LaunchAgents/com.depo.iphone-monitor.plist"
BOT_DIR="/Users/ibrahimoner/Desktop/depo"
LOG_DIR="$BOT_DIR/logs"

mkdir -p "$LOG_DIR"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.depo.iphone-monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$BOT_DIR/src/scraper.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$BOT_DIR</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>TELEGRAM_BOT_TOKEN</key>
        <string>8642556031:AAH4hcajlI-6kQTOP06s1yjTZ_WHBPUhAXw</string>
        <key>TELEGRAM_CHAT_ID</key>
        <string>744380327</string>
        <key>PYTHONPATH</key>
        <string>$BOT_DIR/src</string>
    </dict>

    <!-- Her 300 saniyede (5 dakika) bir çalıştır -->
    <key>StartInterval</key>
    <integer>300</integer>

    <!-- Bilgisayar açıldığında otomatik başlat -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Log dosyaları -->
    <key>StandardOutPath</key>
    <string>$LOG_DIR/monitor.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/monitor_error.log</string>
</dict>
</plist>
EOF

echo "✅ Plist dosyası oluşturuldu: $PLIST"

# Varsa eski job'u durdur
launchctl unload "$PLIST" 2>/dev/null

# Yeni job'u yükle ve başlat
launchctl load "$PLIST"

echo "🚀 Bot başlatıldı! Her 5 dakikada bir çalışacak."
echo "📋 Logları görmek için:"
echo "   tail -f $LOG_DIR/monitor.log"
