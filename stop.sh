#!/bin/bash

# QuantOL PM2 停止脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}正在停止 QuantOL 服务...${NC}"

# 停止所有 PM2 进程
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# 停止 Redis
if [ -f logs/redis.pid ]; then
    PID=$(cat logs/redis.pid)
    if ps -p $PID > /dev/null 2>&1; then
        /usr/bin/redis-cli -p 6379 shutdown 2>/dev/null || kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Redis 服务已停止${NC}"
    fi
    rm logs/redis.pid
fi

# 强制停止残留进程
pkill -f "nginx.*nginx.conf" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true

# 等待进程完全退出
sleep 2

# 确保端口释放
for port in 8000 3000 8501 8087; do
    if lsof -i :$port > /dev/null 2>&1; then
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}所有服务已停止！${NC}"
