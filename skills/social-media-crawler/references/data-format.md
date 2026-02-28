# Social Media Crawler 数据格式说明

## 输出数据结构

### 小红书 (Xiaohongshu)

```json
{
  "date": "20260228",
  "platform": "xiaohongshu",
  "keywords": ["投资", "AI"],
  "notes": [
    {
      "note_id": "...",
      "title": "笔记标题",
      "content": "笔记内容",
      "author": "作者昵称",
      "likes": 1234,
      "comments": 56,
      "shares": 78,
      "tags": ["tag1", "tag2"],
      "keyword": "投资"
    }
  ]
}
```

### Twitter/X

```json
{
  "date": "20260228",
  "platform": "twitter",
  "trending_topics": [
    {"name": "#AI", "tweet_volume": 50000}
  ],
  "tweets": [
    {
      "tweet_id": "...",
      "content": "推文内容",
      "author": "用户名",
      "likes": 123,
      "retweets": 45,
      "replies": 6
    }
  ]
}
```

## 数据存储位置

所有数据保存在:
```
~/.openclaw/workspace/data/social-media/
├── xiaohongshu/
│   └── hot_notes_YYYYMMDD.json
├── twitter/
│   └── trending_YYYYMMDD.json
└── report_YYYYMMDD.json
```

## GrowthClaw 使用方式

读取最新数据:
```python
import json
from pathlib import Path

# 获取小红书今日数据
data_dir = Path.home() / ".openclaw/workspace/data/social-media/xiaohongshu"
latest_file = sorted(data_dir.glob("hot_notes_*.json"))[-1]

with open(latest_file) as f:
    data = json.load(f)
    
# 分析热门笔记
top_notes = sorted(data["notes"], key=lambda x: x["likes"], reverse=True)[:5]
```
