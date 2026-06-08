#!/bin/bash

# QuantOL 停止脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}停止 QuantOL 服务...${NC}"

# 停止前端
if pgrep -f "next dev" > /dev/null; then
    echo "停止前端服务..."
    pkill -f "next dev"
fi

# 停止后端
if pgrep -f "uvicorn.*server:app" > /dev/null; then
    echo "停止后端服务..."
    pkill -f "uvicorn.*server:app"
fi

# 停止 Nginx
if pgrep -f "nginx" > /dev/null; then
    echo "停止 Nginx..."
    pkill -f "nginx"
fi

# 清理 PID 文件
rm -f logs/*.pid 2>/dev/null

echo -e "${GREEN}✓ 所有服务已停止${NC}"
