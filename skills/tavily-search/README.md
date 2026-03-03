# Tavily Search Skill

> 专为LLM优化的AI搜索引擎

## 功能

- 🤖 **AI生成摘要**：自动总结搜索结果
- 🔍 **高质量结果**：专为AI助手优化的结构化数据
- 📊 **使用统计**：跟踪查询和结果

## 使用

```bash
# 命令行使用
cd skills/tavily-search/scripts
python3 tavily_search.py "你的搜索查询" [结果数量]

# Python调用
from scripts.tavily_search import search, format_results

results = search("量化投资策略", max_results=5)
print(format_results(results))
```

## 配置

API Key已存储在：`~/.openclaw/workspace/.credentials/tavily-api-key`

**限额**：1000次/月

## 对比测试

| 查询 | Brave | Tavily |
|------|-------|--------|
| "量化投资策略" | 待测试 | ✅ 已测试成功 |

---
_专为研究而生_ 🔍
