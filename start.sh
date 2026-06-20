#!/bin/bash
# GitStat Cyberpunk — macOS 一键启动
# 用法: ./start.sh [scan_path] [--no-browser]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/tmp/gitstat"
PID_FILE="$LOG_DIR/backend.pid"
BACKEND_PORT=12580
SCAN_PATH="${1:-.}"

# --no-browser 参数处理
NO_BROWSER=0
for arg in "$@"; do
    if [ "$arg" = "--no-browser" ]; then
        NO_BROWSER=1
    elif [ "$arg" != "." ]; then
        SCAN_PATH="$arg"
    fi
done

mkdir -p "$LOG_DIR"

ensure_frontend_dist() {
    local index_file="$SCRIPT_DIR/frontend/dist/index.html"
    local needs_build=0

    if [ ! -f "$index_file" ]; then
        needs_build=1
    else
        local asset
        asset=$(grep -o 'src="/assets/[^"]*\.js"' "$index_file" | head -1 | sed 's#src="/##;s#"$##')
        if [ -z "$asset" ] || [ ! -f "$SCRIPT_DIR/frontend/dist/$asset" ]; then
            needs_build=1
        fi
    fi

    if [ "$needs_build" -eq 0 ]; then
        return
    fi

    echo "前端构建产物缺失，正在构建..."
    cd "$SCRIPT_DIR/frontend" || exit 1
    if [ ! -d node_modules ]; then
        npm ci
    fi
    npm run build
    cd "$SCRIPT_DIR" || exit 1
}

ensure_frontend_dist

# 清理旧进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "停止旧进程 PID=$OLD_PID..."
        kill "$OLD_PID" 2>/dev/null
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# 清理端口占用
PID_ON_PORT=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
if [ -n "$PID_ON_PORT" ]; then
    echo "端口 $BACKEND_PORT 被占用，清理..."
    kill "$PID_ON_PORT" 2>/dev/null
    for i in $(seq 1 10); do
        sleep 1
        if [ -z "$(lsof -ti :$BACKEND_PORT 2>/dev/null)" ]; then
            break
        fi
    done
    if [ -n "$(lsof -ti :$BACKEND_PORT 2>/dev/null)" ]; then
        echo "端口 $BACKEND_PORT 仍被占用，无法启动当前服务"
        lsof -nP -iTCP:$BACKEND_PORT -sTCP:LISTEN
        exit 1
    fi
fi

# 启动后端
cd "$SCRIPT_DIR/backend-py"
nohup python3 main.py "$SCAN_PATH" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"
echo "后端启动 PID=$BACKEND_PID 端口=$BACKEND_PORT"

# 等待就绪
READY=0
for i in $(seq 1 15); do
    sleep 1
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "后端进程已退出，检查日志: $LOG_DIR/backend.log"
        tail -20 "$LOG_DIR/backend.log"
        exit 1
    fi
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

# 打开浏览器
if [ $NO_BROWSER -eq 0 ]; then
    open -a "Google Chrome" "http://localhost:$BACKEND_PORT"
fi

echo "GitStat 启动完成!"
