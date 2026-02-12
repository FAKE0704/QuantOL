#!/bin/bash
# QuantOL PM2 重启脚本

echo "======================================="
echo "  重启 QuantOL 服务"
echo "======================================="
pm2 restart all
echo "✓ 所有服务已重启"
pm2 status
