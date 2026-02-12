#!/bin/bash
# QuantOL PM2 停止脚本

echo "======================================="
echo "  停止 QuantOL 服务"
echo "======================================="
pm2 stop all
echo "✓ 所有服务已停止"
