# HEARTBEAT.md - Agent自我成长系统

> 每周执行一次，触发所有Agent的持续学习

---

## 执行频率
- **主要检查**：每周日 10:00
- **补充检查**：周三 20:00（如有紧急热点）

---

## 学习流程

### Phase 1: 信息收集（每个Agent独立执行）

#### @quant-munger 检查清单
```
□ 检查Arxiv量化金融新论文（q-fin标签）
□ 检查GitHub Trending量化项目
□ 检查东方财富/雪球热股讨论
□ 更新市场情绪指标
```

#### @product-engineer 检查清单
```
□ 检查GitHub Trending Python/AI项目
□ 检查Hacker News热门技术话题
□ 检查Streamlit/Gradio新组件
□ 记录感兴趣的新工具
```

#### @socratic-mentor 检查清单
```
□ 检查豆瓣新书榜（投资/技术/成长类）
□ 检查Goodreads热门书评
□ 检查个人书单进度
□ 规划下周阅读计划
```

#### @growthclaw 检查清单
```
□ 检查小红书热门话题
□ 检查Twitter Trending
□ 检查B站热门分区
□ 记录内容灵感
```

### Phase 2: 学习吸收

每个Agent根据收集的信息：
1. 选择1-2个最有价值的内容深入学习
2. 提取可应用的知识点
3. 更新自己的 LEARNING.md

### Phase 3: 主动提案

如发现以下情况，立即向 @musk-orchestrator 报告：

**需要新Skill**
```
报告格式：
- 发现：[描述]
- 需求：[需要学习/安装什么]
- 价值：[能带来什么提升]
- 建议：[具体行动]
```

**发现机会**
```
报告格式：
- 机会：[描述]
- 紧迫性：[高/中/低]
- 行动建议：[下一步]
```

**需要协作**
```
报告格式：
- 任务：[描述]
- 需要协助：[哪个Agent]
- 预期产出：[结果]
```

### Phase 4: 周报告生成

每个Agent在周日22:00前生成周报：
```markdown
## Agent周报 {日期}

### 本周学习
- [学习内容1]
- [学习内容2]

### 关键洞察
- [洞察1]
- [洞察2]

### 主动提案
- [提案1]
- [提案2]

### 下周计划
- [计划1]
- [计划2]
```

---

## 学习源配置

### 量化金融源
- Arxiv: https://arxiv.org/list/q-fin/recent
- Quantpedia: https://quantpedia.com/
- 聚宽: https://www.joinquant.com/

### 技术源
- GitHub Trending: https://github.com/trending/python
- Hacker News: https://news.ycombinator.com/
- Python Weekly: https://www.pythonweekly.com/

### 阅读源
- 豆瓣读书: https://book.douban.com/
- Goodreads: https://www.goodreads.com/
- 得到: https://www.dedao.cn/

### 营销源
- 新榜: https://www.newrank.cn/
- 千瓜数据: https://www.qian-gua.com/
- 微博热搜: https://s.weibo.com/top/summary

---

## 成长指标追踪

每月最后一个周日汇总：
```json
{
  "quant-munger": {
    "papers_read": 0,
    "strategies_developed": 0,
    "experiments_conducted": 0
  },
  "product-engineer": {
    "projects_completed": 0,
    "technologies_learned": 0,
    "code_reuse_rate": 0
  },
  "socratic-mentor": {
    "books_read": 0,
    "articles_written": 0,
    "mental_models_added": 0
  },
  "growthclaw": {
    "content_published": 0,
    "engagement_rate": 0,
    "growth_experiments": 0
  }
}
```

---

## 执行指令

当收到heartbeat时：
1. 读取本文件
2. 按Phase 1分配任务给各Agent
3. 等待各Agent完成学习
4. 收集主动提案
5. 汇总周报给用户

---

_持续学习，持续进化_ 🚀
