# HEARTBEAT.md - Agent自我成长系统 v2.0

> 📌 当前版本：v2.0（每日微学习 + 周总结）  
> 📖 升级记录见文末附录

---

## 执行频率

### Cron 任务配置（已更新）

| 任务名 | 触发时间 | 内容 |
|--------|---------|------|
| Agent-Daily-Micro-Learning | 工作日 **07:00** | 每日微学习（4 个 Agent 并行） |
| Agent-Daily-Micro-Learning-Weekend | 周末 **07:00** | 周末版微学习 |
| Agent-Weekly-Deep-Review | 周日 **22:00** | 深度总结 + 跨 Agent 知识融合 |

### 补充检查
- 周三 20:00（如有紧急热点）

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

# 附录：系统升级记录

## Agent 自我成长系统升级记录 v2.0

> 升级日期：2026-02-26  
> 升级版本：v2.0（每日微学习 + 周总结）

---

### 一、升级前后对比

| 维度 | 升级前（v1.0） | 升级后（v2.0） |
|------|---------------|---------------|
| **频率** | 每周一次（周日 10:00） | 每日 + 每周 |
| **单次时长** | 30-60 分钟 | 10-15 分钟/天 |
| **学习深度** | 广泛扫描（10+ 来源） | 聚焦 1 个最高价值内容 |
| **记录方式** | 周报形式 | 每天 3-5 行极简记录 |
| **响应速度** | 7 天周期 | 即时发现热点可立即提案 |
| **触发时间** | 周日 10:00 | 工作日 **07:00** / 周末 **07:00** + 周日 **22:00** 深度总结 |
| **目标** | 系统性学习 | 每天进步 1%，持续复利 |

---

### 二、新版核心优势

#### 1. 更快响应市场变化
- **旧版**：一周后才知道这周发生了什么
- **新版**：每天上午就能掌握最新趋势，发现机会立即行动

#### 2. 降低认知负担
- **旧版**：一次要看 10+ 来源，信息过载
- **新版**：每天只选 1 个最有价值的内容，聚焦吸收

#### 3. 建立每日习惯
- **旧版**：周日才想起学习，容易拖延
- **新版**：像刷牙一样每天自动执行，形成肌肉记忆

#### 4. 复利效应显著
- 每天进步 1%，一年就是 **37 倍成长**
- 即使每天只学一个知识点，一年就是 365 个知识点

#### 5. 即时提案机制
- 发现高价值内容可立即触发 Phase 3
- 不错过任何窗口期

---

### 三、Cron 任务配置（已调整时间）

| 任务名 | 触发时间 | 内容 |
|--------|---------|------|
| Agent-Daily-Micro-Learning | 工作日 **07:00** | 每日微学习（4 个 Agent 并行） |
| Agent-Daily-Micro-Learning-Weekend | 周末 **07:00** | 周末版微学习 |
| Agent-Weekly-Deep-Review | 周日 **22:00** | 深度总结 + 跨 Agent 知识融合 |

> **时间调整记录**：2026-02-26 将原定 08:30（工作日）/ 09:00（周末）统一调整为 **07:00**

---

### 四、文件更新清单

- ✅ `/HEARTBEAT.md` - 全新 v2.0 版本（含本附录）
- ✅ `/SOUL.md` - 更新「Agent 成长机制」部分
- ✅ `/subagents/quant-munger/LEARNING.md` - 已有基础框架
- ✅ `/subagents/product-engineer/LEARNING.md` - 已有基础框架
- ✅ `/subagents/socratic-mentor/LEARNING.md` - 已有基础框架
- ✅ `/subagents/growthclaw/LEARNING.md` - 已有基础框架
- ✅ Cron 任务 - 新增每日微学习（工作日+周末）+ 更新周日深度总结时间

---

### 五、下一步行动

1. **观察一周**：看看每日微学习的实际效果和 Agent 的适应情况
2. **调优频率**：根据反馈调整触发时间或内容深度
3. **丰富数据源**：根据各 Agent 的反馈，补充更有价值的学习源
4. **建立反馈循环**：让用户能方便地标记「这个学习内容很有用/没用」

---

_每天进步 1%，一年就是 37 倍成长_ 🚀

**升级完成时间**：2026-02-26  
**系统状态**：✅ 运行中
