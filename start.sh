#!/bin/bash

# QuantOL 启动脚本 - 统一入口
# 本地访问: http://localhost:8087
# 外网访问: 通过 frps 转发

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  QuantOL 量化交易系统${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
        return 1
    fi
    return 0
}

# 检查必要的端口
if ! check_port 3000; then
    echo -e "${RED}错误: 端口 3000 已被占用，请先关闭占用该端口的进程${NC}"
    exit 1
fi

if ! check_port 8501; then
    echo -e "${RED}错误: 端口 8501 已被占用，请先关闭占用该端口的进程${NC}"
    exit 1
fi

if ! check_port 8087; then
    echo -e "${RED}错误: 端口 8087 已被占用，请先关闭占用该端口的进程${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo -e "${GREEN}[1/4] 启动落地页 (Next.js)...${NC}"
cd landing-page
npm run dev > ../logs/landing-page.log 2>&1 &
LANDING_PID=$!
echo -e "${GREEN}✓ 落地页已启动 (PID: $LANDING_PID, 端口: 3000)${NC}"
cd ..

# 等待落地页启动
sleep 3

echo -e "${GREEN}[2/4] 启动 Streamlit 应用...${NC}"
uv run streamlit run main.py --server.port 8501 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}✓ Streamlit 应用已启动 (PID: $STREAMLIT_PID, 端口: 8501)${NC}"

# 等待 Streamlit 启动
sleep 3

echo -e "${GREEN}[3/4] 启动 Nginx 反向代理...${NC}"
nginx -c $(pwd)/nginx.conf -p $(pwd) > logs/nginx.log 2>&1 &
NGINX_PID=$!
echo -e "${GREEN}✓ Nginx 已启动 (PID: $NGINX_PID, 端口: 8087)${NC}"

# 保存 PID 到文件
echo "$LANDING_PID" > logs/landing-page.pid
echo "$STREAMLIT_PID" > logs/streamlit.pid
echo "$NGINX_PID" > logs/nginx.pid

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ 所有服务已成功启动！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}📱 访问地址: http://localhost:8087${NC}"
echo -e "${YELLOW}   - 落地页: http://localhost:8087/${NC}"
echo -e "${YELLOW}   - 应用:   http://localhost:8087/app${NC}"
echo ""
echo -e "${YELLOW}📝 日志文件:${NC}"
echo -e "   - 落地页: logs/landing-page.log"
echo -e "   - Streamlit: logs/streamlit.log"
echo -e "   - Nginx: logs/nginx.log"
echo ""
echo -e "${YELLOW}🛑 停止服务: ./stop.sh${NC}"
echo -e "${GREEN}======================================${NC}"
