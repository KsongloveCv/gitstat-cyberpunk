#!/bin/bash
# GitStat 看门狗 — 定期检查后端是否存活，挂了就拉起来
# 由 macOS launchd 每60秒调用一次

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="/tmp/gitstat"
PID_FILE="$LOG_DIR/backend.pid"
BACKEND_PORT=12580
WATCHDOG_LOG="$LOG_DIR/watchdog.log"

mkdir -p "$LOG_DIR"

TS=$(date '+%Y-%m-%d %H:%M:%S')

ALIVE=0
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        ALIVE=1
    fi
fi

PORT_PID=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    ALIVE=1
    echo "$PORT_PID" > "$PID_FILE"
fi

HEALTH=0
if [ $ALIVE -eq 1 ]; then
    if curl -s --max-time 3 "http://localhost:$BACKEND_PORT/api/stats/overview" > /dev/null 2>&1; then
        HEALTH=1
    fi
fi

if [ $HEALTH -eq 1 ]; then
    echo "$TS 后端正常 PID=$(cat $PID_FILE)" >> "$WATCHDOG_LOG"
    exit 0
fi

echo "$TS 后端异常，正在重启..." >> "$WATCHDOG_LOG"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null
fi
if [ -n "$PORT_PID" ]; then
    kill "$PORT_PID" 2>/dev/null
fi
sleep 2

cd "$SCRIPT_DIR"
bash scripts/start.sh --no-browser >> "$WATCHDOG_LOG" 2>&1

echo "$TS 重启完成" >> "$WATCHDOG_LOG"
exit 0
