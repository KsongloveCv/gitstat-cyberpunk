#!/bin/bash
# GitStat 停止脚本

LOG_DIR="/tmp/gitstat"
PID_FILE="$LOG_DIR/backend.pid"
BACKEND_PORT=12580

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "停止进程 PID=$PID..."
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
fi

PID_ON_PORT=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
if [ -n "$PID_ON_PORT" ]; then
    echo "停止端口 $BACKEND_PORT 上的进程..."
    kill "$PID_ON_PORT" 2>/dev/null
fi

sleep 1
echo "GitStat 已停止"
