#!/bin/bash
# QuantOL PM2 启动脚本
# 生产环境启动脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  QuantOL 量化交易系统 (PM2)${NC}"
echo -e "${GREEN}  生产环境启动${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 创建日志目录
mkdir -p logs

# 检查前端是否已克隆
if [ ! -d "/home/user0704/QuantOL-frontend" ]; then
    echo -e "${YELLOW}⚠️  前端仓库未找到，正在克隆...${NC}"
    git clone https://github.com/FAKE0704/QuantOL-frontend.git /home/user0704/QuantOL-frontend
    cd /home/user0704/QuantOL-frontend
    npm ci
    npm run build
    cd /home/user0704/QuantOL
fi

# 启动 PM2 生产环境
echo -e "${GREEN}启动 PM2 生产环境...${NC}"
pm2 start ecosystem.config.js --env production

# 等待服务启动
sleep 5

# 保存 PM2 进程列表
pm2 save

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ 所有服务已成功启动！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${YELLOW}📱 访问地址: http://localhost:8087${NC}"
echo -e "${YELLOW}📊 PM2 监控: pm2 monit${NC}"
echo -e "${YELLOW}📝 PM2 日志: pm2 logs${NC}"
echo -e "${YELLOW}🔄 重启服务: pm2 restart all${NC}"
echo -e "${YELLOW}🛑 停止服务: ./scripts/stop.sh${NC}"
echo ""
