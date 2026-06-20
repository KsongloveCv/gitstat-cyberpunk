#!/bin/bash
# Cloudflared 隧道看门狗 — 确保 kangsong.me 隧道始终在线

LOG_DIR="/tmp/gitstat"
CF_LOG="$LOG_DIR/cf-tunnel.log"
WATCHDOG_LOG="$LOG_DIR/cf-watchdog.log"
CF_BIN="${CLOUDFLARED_BIN:-$(command -v cloudflared 2>/dev/null || echo /opt/homebrew/bin/cloudflared)}"

mkdir -p "$LOG_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') 🌐 CF隧道看门狗启动" >> "$WATCHDOG_LOG"

while true; do
    TS=$(date '+%Y-%m-%d %H:%M:%S')

    CF_PID=$(pgrep -f "cloudflared tunnel run gitstat" | head -1)
    if [ -n "$CF_PID" ]; then
        echo "$TS ✅ CF隧道正常 PID=$CF_PID" >> "$WATCHDOG_LOG"
        sleep 120
        continue
    fi

    echo "$TS 🔴 CF隧道丢失，正在重启..." >> "$WATCHDOG_LOG"
    "$CF_BIN" tunnel run gitstat >> "$CF_LOG" 2>&1 &
    echo "$TS ⚡ 启动新隧道 PID=$!" >> "$WATCHDOG_LOG"

    for i in 1 2 3 4 5 6 7 8 9 10; do
        sleep 3
        if pgrep -f "cloudflared tunnel run gitstat" > /dev/null 2>&1; then
            echo "$TS ✅ CF隧道重启成功" >> "$WATCHDOG_LOG"
            break
        fi
    done

    sleep 120
done
