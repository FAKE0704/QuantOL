#!/bin/bash

# QuantOL 开发模式启动脚本
# 本地访问: http://localhost:3000 或 http://localhost:8087
# 外网访问: http://IP:8087

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

# 创建日志目录
mkdir -p logs

# 检查并启动后端服务
if ! pgrep -f "uvicorn.*server:app" > /dev/null; then
    echo -e "${YELLOW}[1/3] 启动后端服务（热重载模式）...${NC}"
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
    echo -e "${GREEN}[1/3] 后端服务已在运行${NC}"
fi

# 启动前端开发模式（后台运行）
echo -e "${YELLOW}[2/3] 启动前端开发模式 (端口: 3000)...${NC}"
cd landing-page
npm run dev > ../logs/landing-page-dev.log 2>&1 &
LANDING_PID=$!
echo $LANDING_PID > ../logs/landing-page.pid
sleep 5
if ps -p $LANDING_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端开发模式已启动 (PID: $LANDING_PID, 端口: 3000)${NC}"
else
    echo -e "${RED}✗ 前端启动失败，请检查日志: logs/landing-page-dev.log${NC}"
    tail -20 ../logs/landing-page-dev.log
fi
cd ..

# 启动 Nginx 反向代理
echo -e "${YELLOW}[3/3] 启动 Nginx 反向代理 (端口: 8087)...${NC}"

# 检查端口是否被占用
if lsof -Pi :8087 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Nginx 已在运行（端口 8087）${NC}"
else
    nginx -c $(pwd)/nginx.conf -p $(pwd) -g "pid logs/nginx-dev.pid;" > logs/nginx-dev.log 2>&1 &
    sleep 2
    # 检查端口是否成功监听
    if lsof -Pi :8087 -sTCP:LISTEN -t >/dev/null 2>&1; then
        NGINX_PID=$(cat logs/nginx-dev.pid 2>/dev/null)
        echo $NGINX_PID > logs/nginx.pid
        echo -e "${GREEN}✓ Nginx 已启动 (PID: $NGINX_PID, 端口: 8087)${NC}"
    else
        echo -e "${RED}✗ Nginx 启动失败，请检查日志: logs/nginx-dev.log${NC}"
        tail -20 logs/nginx-dev.log
    fi
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ 开发模式启动成功！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}📱 访问地址:${NC}"
echo -e "${YELLOW}   - 本地:   http://localhost:3000 或 http://localhost:8087${NC}"
echo -e "${YELLOW}   - 外网:   http://IP:8087${NC}"
echo -e "${YELLOW}   - 登录:   http://IP:8087/login${NC}"
echo -e "${YELLOW}   - 回测:   http://IP:8087/backtest${NC}"
echo -e "${YELLOW}   - API 文档: http://IP:8087/api/docs${NC}"
echo ""
echo -e "${YELLOW}📝 日志文件:${NC}"
echo -e "   - 后端: logs/fastapi-dev.log"
echo -e "   - 前端: logs/landing-page-dev.log"
echo -e "   - Nginx: logs/nginx-dev.log"
echo ""
echo -e "${YELLOW}🛑 停止服务: ./stop.sh${NC}"
echo -e "${GREEN}======================================${NC}"
