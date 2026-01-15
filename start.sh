#!/bin/bash

# QuantOL 启动脚本 - 统一入口
# 本地访问: http://localhost:8087
# 外网访问: http://quantol.auto-world-lab.cn (通过frp转发)

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
if ! check_port 6379; then
    echo -e "${RED}错误: 端口 6379 已被占用，请先关闭占用该端口的进程${NC}"
    exit 1
fi

if ! check_port 8000; then
    echo -e "${RED}错误: 端口 8000 已被占用，请先关闭占用该端口的进程${NC}"
    exit 1
fi

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

echo -e "${GREEN}[1/6] 启动 Redis 服务...${NC}"
# 检查Redis是否已在运行
if ! pgrep -f "redis-server.*6379" > /dev/null; then
    /usr/bin/redis-server --daemonize yes --port 6379 --dir $(pwd)/logs --logfile redis.log
    REDIS_PID=$(pgrep redis-server)
    echo -e "${GREEN}✓ Redis 服务已启动 (PID: $REDIS_PID, 端口: 6379)${NC}"
    # 保存 Redis PID
    if [ -n "$REDIS_PID" ]; then
        echo "$REDIS_PID" > logs/redis.pid
    fi
else
    REDIS_PID=$(pgrep -f "redis-server.*6379")
    echo -e "${GREEN}✓ Redis 服务已在运行 (PID: $REDIS_PID, 端口: 6379)${NC}"
    if [ -n "$REDIS_PID" ]; then
        echo "$REDIS_PID" > logs/redis.pid
    fi
fi

# 保存 Redis PID
if [ -n "$REDIS_PID" ]; then
    echo "$REDIS_PID" > logs/redis.pid
fi

# 等待 Redis 启动
sleep 1

echo -e "${GREEN}[2/6] 启动 API 服务 (FastAPI)...${NC}"
uv run uvicorn src.api.server:app --host 0.0.0.0 --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo -e "${GREEN}✓ API 服务已启动 (PID: $FASTAPI_PID, 端口: 8000)${NC}"

# 等待 FastAPI 启动
sleep 2

echo -e "${GREEN}[3/6] 启动落地页 (Next.js)...${NC}"
cd landing-page
# 确保端口 3000 是空闲的（多次尝试清理）
for i in {1..3}; do
    if lsof -ti:3000 >/dev/null 2>&1; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null
        echo "  清理端口 3000 (尝试 $i/3)"
        sleep 2
    else
        break
    fi
done
# 生产模式：每次启动都重新构建以确保使用最新代码
echo "  构建生产版本..."
if npm run build > ../logs/landing-page-build.log 2>&1; then
    echo "  构建成功"
else
    echo -e "${RED}✗ 构建失败，请检查日志: logs/landing-page-build.log${NC}"
    cat ../logs/landing-page-build.log | tail -20
    exit 1
fi
npm start > ../logs/landing-page.log 2>&1 &
LANDING_PID=$!
# 等待并验证 Next.js 是否真的启动了
sleep 5
# 使用 curl 直接测试端口响应（最可靠的检查）
if curl -s http://localhost:3000 >/dev/null 2>&1 && ps -p $LANDING_PID >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 落地页已启动 (PID: $LANDING_PID, 端口: 3000)${NC}"
else
    echo -e "${RED}✗ 落地页启动失败，请检查日志: logs/landing-page.log${NC}"
    tail -20 ../logs/landing-page.log
    exit 1
fi
cd ..

echo -e "${GREEN}[4/6] 启动 Streamlit 应用...${NC}"
uv run streamlit run main.py --server.port 8501 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}✓ Streamlit 应用已启动 (PID: $STREAMLIT_PID, 端口: 8501)${NC}"

# 等待 Streamlit 启动
sleep 3

echo -e "${GREEN}[5/6] 启动 Nginx 反向代理...${NC}"
nginx -c $(pwd)/nginx.conf -p $(pwd) > logs/nginx.log 2>&1 &
NGINX_PID=$!
echo -e "${GREEN}✓ Nginx 已启动 (PID: $NGINX_PID, 端口: 8087)${NC}"

# 保存 PID 到文件
echo "$FASTAPI_PID" > logs/fastapi.pid
echo "$LANDING_PID" > logs/landing-page.pid
echo "$STREAMLIT_PID" > logs/streamlit.pid
echo "$NGINX_PID" > logs/nginx.pid

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ 所有服务已成功启动！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}📱 访问地址: http://localhost:8087${NC}"
echo -e "${YELLOW}   - 外网:   http://quantol.auto-world-lab.cn${NC}"
echo -e "${YELLOW}   - 登录:   http://quantol.auto-world-lab.cn/login${NC}"
echo -e "${YELLOW}   - 控制台: http://quantol.auto-world-lab.cn/dashboard${NC}"
echo -e "${YELLOW}   - 回测:   http://quantol.auto-world-lab.cn/backtest${NC}"
echo -e "${YELLOW}   - API 文档: http://quantol.auto-world-lab.cn/api/docs${NC}"
echo ""
echo -e "${YELLOW}📝 日志文件:${NC}"
echo -e "   - Redis:    logs/redis.log"
echo -e "   - API 服务: logs/fastapi.log"
echo -e "   - 落地页:   logs/landing-page.log"
echo -e "   - Streamlit: logs/streamlit.log"
echo -e "   - Nginx:    logs/nginx.log"
echo ""
echo -e "${YELLOW}🛑 停止服务: ./stop.sh${NC}"
echo -e "${GREEN}======================================${NC}"
