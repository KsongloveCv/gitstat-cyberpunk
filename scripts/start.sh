#!/bin/bash
# GitStat Cyberpunk — 启动脚本
# 用法: ./scripts/start.sh [scan_path] [--no-browser]

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="/tmp/gitstat"
PID_FILE="$LOG_DIR/backend.pid"
BACKEND_PORT=12580
SCAN_PATH="${1:-.}"

NO_BROWSER=0
for arg in "$@"; do
    if [ "$arg" = "--no-browser" ]; then
        NO_BROWSER=1
    elif [ "$arg" != "." ]; then
        SCAN_PATH="$arg"
    fi
done

mkdir -p "$LOG_DIR"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "停止旧进程 PID=$OLD_PID..."
        kill "$OLD_PID" 2>/dev/null
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

PID_ON_PORT=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
if [ -n "$PID_ON_PORT" ]; then
    echo "端口 $BACKEND_PORT 被占用，清理..."
    kill "$PID_ON_PORT" 2>/dev/null
    sleep 2
fi

cd "$SCRIPT_DIR/backend-py"
nohup python3 main.py "$SCAN_PATH" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"
echo "后端启动 PID=$BACKEND_PID 端口=$BACKEND_PORT"

READY=0
for i in $(seq 1 15); do
    sleep 1
    if curl -s --max-time 2 "http://localhost:$BACKEND_PORT/api/stats/overview" > /dev/null 2>&1; then
        READY=1
        echo "后端就绪! (${i}s)"
        break
    fi
done

if [ $READY -eq 0 ]; then
    echo "后端启动超时，检查日志: $LOG_DIR/backend.log"
    tail -20 "$LOG_DIR/backend.log"
    exit 1
fi

if [ $NO_BROWSER -eq 0 ]; then
    open -a "Google Chrome" "http://localhost:$BACKEND_PORT"
fi

echo "GitStat 启动完成!"
