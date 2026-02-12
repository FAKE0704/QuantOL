#!/bin/bash
# 从生产环境同步 SQLite 数据库到本地开发环境

set -e

# 配置信息
SSH_HOST="113.45.40.20"
SSH_PORT="8086"
SSH_USER="user0704"
REMOTE_PATH="/home/user0704/QuantOL/data"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
DB_NAME="quantdb"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}  从生产环境同步数据库${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# 确认信息
echo "服务器: ${SSH_USER}@${SSH_HOST}:${SSH_PORT}"
echo "远程路径: ${REMOTE_PATH}/${DB_NAME}.sqlite*"
echo "本地路径: ${LOCAL_PATH}/"
echo ""

read -p "确认同步? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消${NC}"
    exit 0
fi

# 创建本地目录
mkdir -p "$LOCAL_PATH"

# 备份本地数据库
for ext in sqlite shm wal; do
    if [ -f "$LOCAL_PATH/${DB_NAME}.$ext" ]; then
        BACKUP_FILE="${LOCAL_PATH}/${DB_NAME}.$ext.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}备份 ${DB_NAME}.$ext...${NC}"
        cp "$LOCAL_PATH/${DB_NAME}.$ext" "$BACKUP_FILE"
    fi
done
echo -e "${GREEN}✓ 备份完成${NC}"

# 同步数据库文件
echo -e "${YELLOW}正在同步数据库文件...${NC}"
rsync -avz -e "ssh -p ${SSH_PORT}" \
    "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/${DB_NAME}.sqlite" \
    "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/${DB_NAME}.sqlite-shm" \
    "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/${DB_NAME}.sqlite-wal" \
    "${LOCAL_PATH}/"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✓ 数据库同步成功！${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo -e "${YELLOW}本地路径: ${LOCAL_PATH}/${NC}"
    echo ""
    echo -e "${YELLOW}同步的文件:${NC}"
    echo "   - ${DB_NAME}.sqlite"
    echo "   - ${DB_NAME}.sqlite-shm"
    echo "   - ${DB_NAME}.sqlite-wal"
    echo ""
    echo -e "${YELLOW}提示: 重启后端服务以使用新数据${NC}"
    echo -e "  pm2 restart quantol-backend-dev"
else
    echo -e "${RED}同步失败！${NC}"
    exit 1
fi
