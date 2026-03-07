#!/bin/bash
# 股票策略回测平台启动脚本
# 自动启动 RSSHub + Streamlit 应用

set -e

echo "🚀 股票策略回测平台启动脚本"
echo "=============================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "请先安装 Docker:"
    echo "  - macOS: brew install --cask docker"
    echo "  - 或访问: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker 守护进程未运行${NC}"
    echo "正在启动 Docker Desktop..."
    open /Applications/Docker.app || true

    # 等待 Docker 启动
    echo "等待 Docker 启动..."
    for i in {1..30}; do
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker 已启动${NC}"
            break
        fi
        sleep 2
    done

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 启动超时，请手动启动 Docker Desktop${NC}"
        exit 1
    fi
fi

# 检查 Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${YELLOW}⚠️  Docker Compose 未安装，尝试使用 docker compose 插件${NC}"
    COMPOSE_CMD="docker compose"
fi

# 启动 RSSHub
echo ""
echo "📡 启动 RSSHub 服务..."

# 检查 RSSHub 是否已在运行
if curl -s http://localhost:1200 &> /dev/null; then
    echo -e "${GREEN}✅ RSSHub 已在运行${NC}"
else
    $COMPOSE_CMD up -d rsshub

    # 等待 RSSHub 启动
    echo "等待 RSSHub 启动..."
    for i in {1..30}; do
        if curl -s http://localhost:1200 &> /dev/null; then
            echo -e "${GREEN}✅ RSSHub 启动成功！${NC}"
            break
        fi
        sleep 1
    done

    if ! curl -s http://localhost:1200 &> /dev/null; then
        echo -e "${RED}❌ RSSHub 启动失败${NC}"
        echo "请查看日志: $COMPOSE_CMD logs rsshub"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}==============================${NC}"
echo -e "${GREEN}✅ 所有服务已就绪！${NC}"
echo -e "${GREEN}==============================${NC}"
echo ""
echo "📊 正在启动 Streamlit 应用..."
echo ""

# 启动 Streamlit
streamlit run app.py
