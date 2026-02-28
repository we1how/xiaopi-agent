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

> **原则：国外优先，利用信息差**
> 
> 国外高质量信息源 → 国内应用落地 = 信息差优势

#### @quant-munger 检查清单
**国外（信息差优势）**：
```
□ 检查 Arxiv q-fin（量化金融）新论文 - https://arxiv.org/list/q-fin/recent
□ 检查 SSRN 量化策略工作论文 - https://www.ssrn.com/index.cfm/en/arn Quantitative/
□ 检查 Quantpedia 新策略 - https://quantpedia.com/
□ 检查 Jane Street / Citadel 等技术博客
```

**国内（市场验证）**：
```
□ 检查东方财富/雪球热股讨论
□ 更新市场情绪指标
```

**信息差分析**：国外量化策略在国内市场的适用性评估

---

#### @product-engineer 检查清单
**国外（信息差优势）**：
```
□ 检查 Hacker News Top Stories - https://news.ycombinator.com/
□ 检查 GitHub Trending（Python/AI/Rust） - https://github.com/trending
□ 检查 Product Hunt 今日新品 - https://www.producthunt.com/
□ 检查 Vercel / Stripe 等技术博客更新
```

**国内（本土化）**：
```
□ 检查 Gitee 热门项目
□ 检查掘金/InfoQ 技术趋势
```

**信息差分析**：国外新技术/工具在国内产品的应用场景

---

#### @socratic-mentor 检查清单
**国外（信息差优势）**：
```
□ 检查 Goodreads 新书榜（商业/科技/成长） - https://www.goodreads.com/
□ 检查 Amazon Best Sellers（Business/Investing）
□ 检查 Farnam Street / Wait But Why 等高质量博客
□ 检查 MIT Technology Review / Harvard Business Review
```

**国内（本土化）**：
```
□ 检查豆瓣新书榜（投资/技术/成长类）
□ 检查得到/樊登读书热门
```

**信息差分析**：国外前沿思维模型、认知工具的本土化应用

---

#### @growthclaw 检查清单
**国外（信息差优势）**：
```
□ 检查 Hacker News "Ask HN" / "Show HN" - 产品灵感
□ 检查 Indie Hackers 成功案例 - https://www.indiehackers.com/
□ 检查 Substack 热门技术/商业 Newsletter
□ 检查 Reddit r/SaaS / r/entrepreneur
```

**国内（本土化）**：
```
□ 检查小红书热门话题/低粉爆文
□ 检查即刻圈子热门讨论
□ 检查 B站热门分区
```

**信息差分析**：国外增长案例在国内的可复刻性评估

---

### 信息差价值框架

每个 Agent 每日问自己：

1. **发现了什么国外热点？**
   - 技术/策略/方法论/案例

2. **国内有人讨论吗？**
   - 完全没有 → 高价值信息差
   - 少量讨论 → 早期机会
   - 已经热门 → 验证价值

3. **能应用到我们的场景吗？**
   - Quant: 策略在国内市场回测
   - Product: 工具在项目中试用
   - Mentor: 方法论在个人成长中验证
   - Growth: 案例在内容创作中复刻

4. **什么时候行动？**
   - 立即（高价值+紧急）
   - 本周（高价值+可规划）
   - 记录（有价值+待时机）

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

## 国外情报系统（v2.1 新增）

### 为什么需要国外情报？

**信息差优势**：
- 国外高质量信息源 → 国内应用落地 = 竞争优势
- 技术/策略/方法论领先国内 1-12 个月
- 浓度更高、噪声更少

### 系统架构

```
各 Agent 独立获取国外情报
        ↓
统一汇总到 data/agent-intelligence/
        ↓
musk-orchestrator 生成简报
        ↓
信息差分析 → 主动提案
```

### Agent 国外数据源

| Agent | 国外数据源 | 信息差价值 |
|-------|-----------|-----------|
| **quant-munger** | Arxiv q-fin, SSRN, Quantpedia | 量化策略领先国内 |
| **product-engineer** | HN, GitHub, Product Hunt | 技术趋势领先 1-2 周 |
| **socratic-mentor** | Farnam Street, Wait But Why | 思维模型前沿 |
| **growthclaw** | Indie Hackers, HN Show | 增长案例可复制 |

### 每日执行

```bash
# 1. 各 Agent 获取国外情报
python subagents/quant-munger/scripts/western_intelligence.py
python subagents/product-engineer/scripts/western_intelligence.py
python subagents/socratic-mentor/scripts/western_intelligence.py
python subagents/growthclaw/scripts/western_intelligence.py

# 2. 汇总生成简报
python scripts/western_intelligence_summary.py
```

### 数据存储

```
~/.openclaw/workspace/data/agent-intelligence/
├── quant-munger/
│   └── western_YYYYMMDD.json
├── product-engineer/
│   └── western_YYYYMMDD.json
├── socratic-mentor/
│   └── western_YYYYMMDD.json
└── growthclaw/
    └── western_YYYYMMDD.json
```

---

## 学习源配置

### 量化金融源（Quant-Munger）
**国外（高质量/信息差）**：
- Arxiv q-fin: https://arxiv.org/list/q-fin/recent - 学术前沿
- SSRN Quantitative: https://www.ssrn.com/ - 工作论文
- Quantpedia: https://quantpedia.com/ - 策略库
- Alpha Architect: https://alphaarchitect.com/ - 因子研究
- AQR Papers: https://www.aqr.com/insights/research - 顶级量化研究

**国内（市场验证）**：
- 聚宽: https://www.joinquant.com/
- 东方财富: https://emweb.securities.eastmoney.com/
- 雪球: https://xueqiu.com/

### 技术源（Product-Engineer）
**国外（高质量/信息差）**：
- Hacker News: https://news.ycombinator.com/ - 技术圈风向标
- GitHub Trending: https://github.com/trending/python - 开源趋势
- Product Hunt: https://www.producthunt.com/ - 新产品发现
- Vercel Blog: https://vercel.com/blog - 前端/部署趋势
- Stripe Blog: https://stripe.com/blog - 工程文化
- Netflix Tech Blog: https://netflixtechblog.com/ - 大规模系统

**国内（本土化）**：
- 掘金: https://juejin.cn/
- Gitee: https://gitee.com/explore
- InfoQ: https://www.infoq.cn/

### 阅读源（Socratic-Mentor）
**国外（高质量/信息差）**：
- Goodreads: https://www.goodreads.com/ - 书评社区
- Farnam Street: https://fs.blog/ - 决策/思维模型
- Wait But Why: https://waitbutwhy.com/ - 深度长文
- MIT Technology Review: https://www.technologyreview.com/
- Harvard Business Review: https://hbr.org/
- LessWrong: https://www.lesswrong.com/ - 理性思维

**国内（本土化）**：
- 豆瓣读书: https://book.douban.com/
- 得到: https://www.dedao.cn/
- 微信读书: https://weread.qq.com/

### 营销/增长源（GrowthClaw）
**国外（高质量/信息差）**：
- Indie Hackers: https://www.indiehackers.com/ - 独立开发者案例
- Hacker News "Show HN": https://news.ycombinator.com/show - 产品发布
- Substack: https://substack.com/ - Newsletter趋势
- Reddit r/SaaS: https://www.reddit.com/r/SaaS/ - SaaS讨论
- Marketing Examples: https://marketingexamples.com/ - 案例研究

**国内（本土化）**：
- 小红书: https://www.xiaohongshu.com/
- 即刻: https://web.okjike.com/
- 新榜: https://www.newrank.cn/

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
2. 按Phase 1分配任务给各Agent（国内+国外数据源）
3. 等待各Agent完成学习
4. **汇总国外情报**（运行 `scripts/western_intelligence_summary.py`）
5. 收集主动提案
6. **在当前session直接输出汇总报告**（不要发送到其他channel）

### ⚠️ 重要规范

**输出渠道统一**：
- 所有 Agent 报告直接在当前 session 输出
- **禁止**使用 `message` 工具发送到 Discord/其他渠道
- 避免重复：确保只 spawn 一次子代理

**报告格式**（简洁版）：
```
## 📊 Agent微学习汇总 ({日期})

| Agent | 今日精选 | 核心洞察 |
|-------|----------|----------|
| ⚡ ProductEngineer | {内容} | {洞察} |
| 📊 QuantMunger | {内容} | {洞察} |
...

### 🚀 主动提案
| 提案 | Agent | 建议行动 |
|------|-------|----------|
| {提案} | {Agent} | {行动} |
```

---

# 附录：系统升级记录

## Agent 自我成长系统升级记录 v2.1

> 升级日期：2026-02-28  
> 升级版本：v2.1（国外情报系统 + 信息差优势）

### v2.1 核心升级

**新增：国外高质量情报系统**

| 维度 | v2.0 | v2.1 |
|------|------|------|
| **数据源** | 国内为主 | 国外优先 + 国内验证 |
| **信息质量** | 一般 | 高浓度、高信噪比 |
| **时间优势** | 同步 | 领先 1-12 个月 |
| **Agent覆盖** | 4个 | 4个 + 专属国外脚本 |

**国外数据源矩阵**：
- **Quant-Munger**: Arxiv q-fin, SSRN, Quantpedia
- **Product-Engineer**: HN, GitHub, Product Hunt
- **Socratic-Mentor**: Farnam Street, Wait But Why, LessWrong
- **Growthclaw**: Indie Hackers, HN Show, Substack

**信息差价值**：
1. 量化策略：国外论文 → 国内市场应用
2. 技术工具：HN热门 → 产品技术选型
3. 思维模型：国外博客 → 个人成长方法
4. 增长案例：Indie Hackers → 国内复刻

---

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
