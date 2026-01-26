#!/bin/bash

# QuantOL PM2 启动脚本
# 本地访问: http://localhost:8087
# 外网访问: http://quantol.auto-world-lab.cn

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  QuantOL 量化交易系统 (PM2)${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 创建日志目录
mkdir -p logs

# 检查 Redis
echo -e "${GREEN}[1/5] 检查 Redis 服务...${NC}"
if ! pgrep -f "redis-server.*6379" > /dev/null; then
    /usr/bin/redis-server --daemonize yes --port 6379 --dir $(pwd)/logs --logfile redis.log
    REDIS_PID=$(pgrep -f "redis-server.*6379")
    echo -e "${GREEN}✓ Redis 服务已启动 (PID: $REDIS_PID)${NC}"
    if [ -n "$REDIS_PID" ]; then
        echo "$REDIS_PID" > logs/redis.pid
    fi
else
    REDIS_PID=$(pgrep -f "redis-server.*6379")
    echo -e "${GREEN}✓ Redis 服务已在运行 (PID: $REDIS_PID)${NC}"
    if [ -n "$REDIS_PID" ]; then
        echo "$REDIS_PID" > logs/redis.pid
    fi
fi

# 等待 Redis 就绪
sleep 1

# 构建 Next.js（首次启动或代码更新时）
echo -e "${GREEN}[2/5] 构建 Next.js 应用...${NC}"
cd landing-page
if npm run build > ../logs/landing-page-build.log 2>&1; then
    echo -e "${GREEN}✓ Next.js 构建成功${NC}"
else
    echo -e "${RED}✗ Next.js 构建失败，请检查日志${NC}"
    cat ../logs/landing-page-build.log | tail -20
    exit 1
fi
cd ..

# 启动所有 PM2 进程
echo -e "${GREEN}[3/5] 启动 PM2 进程...${NC}"
pm2 start ecosystem.config.js

# 等待服务启动
echo -e "${GREEN}[4/5] 等待服务就绪...${NC}"
sleep 5

# 保存 PM2 进程列表（用于开机自启）
echo -e "${GREEN}[5/5] 保存 PM2 配置...${NC}"
pm2 save

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ 所有服务已成功启动！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}📱 访问地址: http://localhost:8087${NC}"
echo -e "${YELLOW}   - 外网:   http://quantol.auto-world-lab.cn${NC}"
echo -e "${YELLOW}   - 控制台: http://quantol.auto-world-lab.cn/dashboard${NC}"
echo ""
echo -e "${YELLOW}📊 PM2 监控: pm2 monit${NC}"
echo -e "${YELLOW}📝 PM2 日志: pm2 logs${NC}"
echo -e "${YELLOW}🔄 重启服务: pm2 restart all${NC}"
echo -e "${YELLOW}🛑 停止服务: ./stop.sh${NC}"
echo -e "${GREEN}======================================${NC}"
