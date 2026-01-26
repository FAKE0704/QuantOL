#!/bin/bash
# QuantOL PM2 快捷重启脚本

echo "正在重启所有 PM2 服务..."
pm2 restart all
echo "所有服务已重启"
echo ""
echo "查看状态: ./status.sh 或 pm2 status"
