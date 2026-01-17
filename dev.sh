#!/bin/bash

# QuantOL 开发模式启动脚本

cd "$(dirname "$0")"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  QuantOL 开发模式${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查并启动后端服务
if ! pgrep -f "uvicorn.*server:app" > /dev/null; then
    echo -e "${YELLOW}[1/2] 启动后端服务（热重载模式）...${NC}"
    uv run uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload > logs/fastapi-dev.log 2>&1 &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > logs/fastapi.pid
    sleep 3
    if ps -p $FASTAPI_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务启动成功 (PID: $FASTAPI_PID, 端口: 8000)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败，请检查日志: logs/fastapi-dev.log${NC}"
        tail -20 logs/fastapi-dev.log
    fi
else
    echo -e "${GREEN}[1/2] 后端服务已在运行${NC}"
fi

# 启动前端开发模式
echo -e "${YELLOW}[2/2] 启动前端开发模式 (http://localhost:3000)...${NC}"
cd landing-page
npm run dev
