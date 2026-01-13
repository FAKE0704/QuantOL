#!/bin/bash

# QuantOL 停止脚本

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}正在停止 QuantOL 服务...${NC}"

# 从 PID 文件读取并停止进程
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

echo -e "${GREEN}所有服务已停止！${NC}"
