#!/bin/bash
# 股票策略回测平台停止脚本

set -e

echo "🛑 停止股票策略回测平台服务"
echo "=============================="

# 检查 Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker compose"
fi

# 停止 RSSHub
echo "📡 停止 RSSHub..."
$COMPOSE_CMD down

echo ""
echo "✅ 所有服务已停止"
