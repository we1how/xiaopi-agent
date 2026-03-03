---
name: tavily-search
description: |
  Tavily AI Search - 专为LLM优化的搜索引擎
  提供更结构化、更相关的搜索结果，适合研究分析任务
  每月1000次免费额度
model: moonshot/kimi-k2.5
tools: ["Bash"]
env:
  - TAVILY_API_KEY
---

# Tavily Search Skill

使用 Tavily AI 搜索引擎获取高质量的搜索结果。

## 优势

- **LLM优化**：搜索结果专为AI助手设计，结构化程度高
- **相关性**：比传统搜索引擎更准确
- **效率**：减少结果筛选时间

## 使用限制

- 每月1000次免费调用
- 高频任务建议使用web_search作为fallback

## 示例

```python
from tavily_search import search

results = search("最新量化投资策略", max_results=5)
```

---
_专为研究而生_ 🔍
