#!/bin/bash
# install.sh - 安装 MediaCrawler 及依赖

set -e

echo "🚀 安装 Social Media Crawler..."

# 检查目录
WORKSPACE_DIR="$HOME/.openclaw/workspace"
CRAWLER_DIR="$WORKSPACE_DIR/tools/MediaCrawler"

if [ -d "$CRAWLER_DIR" ]; then
    echo "✅ MediaCrawler 已安装，跳过克隆"
else
    echo "📦 克隆 MediaCrawler..."
    mkdir -p "$WORKSPACE_DIR/tools"
    cd "$WORKSPACE_DIR/tools"
    git clone https://github.com/NanmiCoder/MediaCrawler.git
fi

cd "$CRAWLER_DIR"

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "📦 安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# 安装依赖
echo "📦 安装 Python 依赖..."
uv sync

# 安装浏览器驱动
echo "🌐 安装浏览器驱动..."
uv run playwright install chromium

echo "✅ 安装完成！"
echo ""
echo "下一步："
echo "1. 配置账号: python $WORKSPACE_DIR/skills/social-media-crawler/scripts/setup_credentials.py"
echo "2. 测试登录: python $WORKSPACE_DIR/skills/social-media-crawler/scripts/test_login.py --platform xhs"
