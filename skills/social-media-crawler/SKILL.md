---
name: social-media-crawler
description: |
  自动化爬取国内外高质量信息源，利用信息差为 GrowthClaw 提供内容洞察。
  
  数据源：
  - 国内：小红书热门笔记（MediaCrawler）
  - 国外：Hacker News、GitHub Trending、Arxiv AI（API/网页抓取）
  
  优势：
  - 聚焦国外高质量、高水平信息源
  - 利用信息差（国外→国内）
  - 内容更集中、浓度更高
  
  使用场景：
  - GrowthClaw 每日微学习获取热点
  - 发现国内外技术/产品趋势差异
  - 内容创作灵感收集
---

# Social Media Crawler

自动化爬取国内外高质量信息源，利用信息差优势。

## 信息源矩阵

| 类型 | 平台 | 内容特点 | 信息差价值 |
|------|------|----------|------------|
| **国内社交** | 小红书 | 真实经验分享 | 国内用户痛点 |
| **国外技术** | Hacker News | 技术圈风向标 | 比国内早1-3天 |
| **国外开源** | GitHub | 新工具发现 | 比国内早1-2周 |
| **国外学术** | Arxiv | 前沿研究 | 比发表早6-12月 |

## 快速开始

### 1. 安装

```bash
cd ~/.openclaw/workspace/skills/social-media-crawler/scripts
bash install.sh
```

### 2. 配置小红书凭证

确保 `~/.openclaw/workspace/.credentials/platform-accounts.md` 已包含账号密码，然后运行：

```bash
python scripts/setup_credentials.py
```

### 3. 测试登录

```bash
# 测试小红书登录（首次需要扫码）
python scripts/test_login.py --platform xhs
```

### 4. 运行爬取

```bash
# 方案A：国内数据源（小红书）
python scripts/daily_crawl.py

# 方案B：国外高质量情报源（HN + GitHub + Arxiv）
python scripts/western_tech_crawler.py

# 方案C：全部运行
python scripts/daily_crawl.py && python scripts/western_tech_crawler.py
```

## 每日自动运行

### 使用 OpenClaw Cron

已配置自动任务，每天 08:30 执行：

```bash
# 查看 cron 任务
openclaw cron list

# 手动触发
openclaw cron run social-media-daily-crawl
```

### 手动配置 Crontab

```bash
# 编辑 crontab
crontab -e

# 添加每日 08:30 执行
30 8 * * * cd ~/.openclaw/workspace/skills/social-media-crawler && python scripts/daily_crawl.py >> logs/crawl.log 2>&1
```

## 数据输出

### 存储位置

```
~/.openclaw/workspace/data/social-media/
├── xiaohongshu/              # 国内：小红书热门
│   └── hot_notes_YYYYMMDD.json
├── western/                  # 国外：高质量情报
│   └── intelligence_YYYYMMDD.json
└── report_YYYYMMDD.json
```

### Western Intelligence 数据结构

```json
{
  "date": "20260228",
  "collected_at": "2026-02-28T08:25:59",
  "sources": {
    "hackernews": {
      "count": 15,
      "items": [
        {
          "title": "...",
          "url": "...",
          "points": 681,
          "comments": 551
        }
      ]
    },
    "github": {
      "count": 10,
      "items": [
        {
          "name": "owner/repo",
          "url": "...",
          "description": "..."
        }
      ]
    },
    "arxiv": {
      "count": 10,
      "items": [
        {
          "title": "...",
          "url": "...",
          "published": "2026-02-27"
        }
      ]
    }
  }
}
```

### 数据格式

详见 [references/data-format.md](references/data-format.md)

### GrowthClaw 读取示例

```python
import json
from pathlib import Path
from datetime import datetime

# 获取今日数据
data_dir = Path.home() / ".openclaw/workspace/data/social-media"
today = datetime.now().strftime("%Y%m%d")

# 小红书数据
xhs_file = data_dir / f"xiaohongshu/hot_notes_{today}.json"
if xhs_file.exists():
    with open(xhs_file) as f:
        xhs_data = json.load(f)
        top_notes = sorted(xhs_data["notes"], key=lambda x: x["likes"], reverse=True)[:5]
        print(f"今日小红书 Top 5 热门笔记: {[n['title'] for n in top_notes]}")

# Twitter 数据
tw_file = data_dir / f"twitter/trending_{today}.json"
if tw_file.exists():
    with open(tw_file) as f:
        tw_data = json.load(f)
        print(f"今日 Twitter 趋势: {[t['name'] for t in tw_data['trending_topics']]}")
```

## 配置说明

### 小红书关键词

编辑 `config/xiaohongshu.yaml`：

```yaml
keywords:
  - 投资
  - AI
  - 副业
  # 添加更多关键词

settings:
  max_notes_per_keyword: 20  # 每个关键词抓取笔记数
```

### Twitter 配置

编辑 `config/twitter.yaml`：

```yaml
trending_categories:
  - technology
  - business
  # 关注的趋势类别

search_keywords:
  - "#AI"
  - "OpenAI"
  # 搜索关键词
```

## 常见问题

### Q: 小红书登录失败？

A: 小红书需要使用二维码登录。运行 `test_login.py` 后会弹出浏览器窗口，扫码即可。登录态会自动保存，后续无需重复扫码。

### Q: Twitter/X 如何获取数据？

A: 本方案使用 **Jina Reader** (r.jina.ai) 获取 Twitter 公开内容，优势：
- ✅ 无需登录，无封号风险
- ✅ 无需 API Key
- ✅ 支持获取公开用户时间线

### Q: 数据在哪里查看？

A: 所有数据保存在 `~/.openclaw/workspace/data/social-media/`，按日期分文件夹存储。

### Q: 如何修改爬取时间？

A: 编辑 OpenClaw Cron 配置或系统 crontab，修改执行时间。

## 技术架构

| 平台 | 技术方案 | 登录要求 | 风险 |
|------|----------|----------|------|
| 小红书 | MediaCrawler (Playwright) | 需扫码一次 | 低 |
| Twitter/X | Jina Reader (r.jina.ai) | 无需登录 | 无 |

- **数据格式**: JSON
- **调度方式**: OpenClaw Cron / 系统 Crontab
- **存储位置**: `~/.openclaw/workspace/data/social-media/`

## 免责声明

本工具仅供学习研究使用。请遵守各平台的服务条款，控制请求频率，避免对平台造成压力。
