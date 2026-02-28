#!/bin/bash
# twitter_crawl.sh - 使用 MediaCrawler 的环境运行 Twitter 爬取

cd /Users/linweihao/.openclaw/workspace/tools/MediaCrawler

# 使用 uv 运行 Python 脚本
uv run python /Users/linweihao/.openclaw/workspace/skills/social-media-crawler/scripts/twitter_crawler.py
