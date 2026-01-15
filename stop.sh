#!/bin/bash

# QuantOL 停止脚本

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}正在停止 QuantOL 服务...${NC}"

# 停止 Redis（仅在通过我们脚本启动时）
if [ -f logs/redis.pid ]; then
    PID=$(cat logs/redis.pid)
    # 只停止我们启动的Redis实例（端口6379）
    if ps -p $PID > /dev/null 2>&1 && ps -p $PID | grep -q "redis-server.*6379"; then
        /usr/bin/redis-cli -p 6379 shutdown 2>/dev/null || kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Redis 服务已停止 (PID: $PID)${NC}"
    fi
    rm logs/redis.pid
fi

# 注意：不强制关闭所有redis-server进程，因为可能是系统服务
# 如果需要关闭系统Redis服务，请使用: sudo systemctl stop redis-server

# 从 PID 文件读取并停止进程
if [ -f logs/fastapi.pid ]; then
    PID=$(cat logs/fastapi.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ API 服务已停止 (PID: $PID)${NC}"
    fi
    rm logs/fastapi.pid
fi

if [ -f logs/landing-page.pid ]; then
    PID=$(cat logs/landing-page.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ 落地页已停止 (PID: $PID)${NC}"
    fi
    rm logs/landing-page.pid
fi

if [ -f logs/streamlit.pid ]; then
    PID=$(cat logs/streamlit.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ Streamlit 应用已停止 (PID: $PID)${NC}"
    fi
    rm logs/streamlit.pid
fi

if [ -f logs/nginx.pid ]; then
    PID=$(cat logs/nginx.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✓ Nginx 已停止 (PID: $PID)${NC}"
    fi
    rm logs/nginx.pid
fi

# 强制停止 nginx（可能有多个进程）
pkill -f "nginx.*nginx.conf" 2>/dev/null && echo -e "${GREEN}✓ Nginx 进程已清理${NC}"

# 强制停止 FastAPI（可能有残留进程）
pkill -f "uvicorn.*8000" 2>/dev/null && echo -e "${GREEN}✓ FastAPI 进程已清理${NC}"

# 强制停止 Streamlit（进程可能无法正常响应 SIGTERM）
pkill -f "streamlit run" 2>/dev/null
pkill -f "streamlit" 2>/dev/null && echo -e "${GREEN}✓ Streamlit 进程已清理${NC}"

# 强制停止 Next.js（可能有残留进程）
pkill -f "next dev" 2>/dev/null
pkill -f "next start" 2>/dev/null
pkill -f "next-server" 2>/dev/null
pkill -f "node.*landing-page" 2>/dev/null
pkill -f "npm.*start" 2>/dev/null

# 等待进程完全退出
sleep 2

# 确认清理成功
if ! pgrep -f "next" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Next.js 进程已清理${NC}"
fi

# 等待进程完全停止
sleep 1

# 再次检查端口占用情况
for port in 8000 3000 8501 8087; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 仍被占用，正在强制清理...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null && sleep 1
    fi
done

echo -e "${GREEN}所有服务已停止！${NC}"
