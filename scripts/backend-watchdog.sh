#!/bin/bash
# GitStat 后端看门狗 — 长驻进程，检测 /health 并在异常时重启

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/start.sh"
LOG_DIR="/tmp/gitstat"
PID_FILE="$LOG_DIR/backend.pid"
BACKEND_PORT=12580
WATCHDOG_LOG="$LOG_DIR/watchdog.log"

mkdir -p "$LOG_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') 🐕 看门狗启动" >> "$WATCHDOG_LOG"

while true; do
    TS=$(date '+%Y-%m-%d %H:%M:%S')

    if curl -s --max-time 5 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        PORT_PID=$(lsof -ti :$BACKEND_PORT 2>/dev/null | head -1)
        echo "$TS ✅ 后端正常 PID=$PORT_PID" >> "$WATCHDOG_LOG"
        [ -n "$PORT_PID" ] && echo "$PORT_PID" > "$PID_FILE"
        sleep 60
        continue
    fi

    echo "$TS 🔴 后端异常，正在重启..." >> "$WATCHDOG_LOG"
    [ -f "$PID_FILE" ] && kill "$(cat "$PID_FILE")" 2>/dev/null
    PORT_PID=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
    [ -n "$PORT_PID" ] && kill "$PORT_PID" 2>/dev/null
    rm -f "$PID_FILE"
    sleep 2

    bash "$START_SCRIPT" "$HOME" --no-browser >> "$WATCHDOG_LOG" 2>&1 &
    echo "$TS ⚡ 调用 start.sh 重启后端" >> "$WATCHDOG_LOG"

    for i in $(seq 1 20); do
        sleep 3
        if curl -s --max-time 3 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
            PORT_PID=$(lsof -ti :$BACKEND_PORT 2>/dev/null | head -1)
            echo "$TS ✅ 重启成功 PID=$PORT_PID" >> "$WATCHDOG_LOG"
            [ -n "$PORT_PID" ] && echo "$PORT_PID" > "$PID_FILE"
            break
        fi
    done

    if ! curl -s --max-time 3 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        echo "$TS ⚠️ start.sh 重启超时，检查 $LOG_DIR/backend.log" >> "$WATCHDOG_LOG"
    fi

    sleep 60
done
