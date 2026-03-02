# HEARTBEAT.md - Agent自我成长系统 v2.3

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

#### 🔄 数据源轮换与去重机制

**核心规则**：
1. **主源优先** → 检查是否有更新（24小时内）
2. **重复检测** → 对比LEARNING.md历史记录（去重窗口：7天）
3. **自动切换** → 主源无新内容或重复时，按优先级切换备选源
4. **无内容报告** → 所有源均无新内容时，输出"今日无新发现"并建议复习

**重复检测方法**：
```
检查项：
- 论文标题/Arxiv ID
- GitHub repo名称/URL
- 文章标题+作者
- 项目Product Hunt链接

去重窗口：7天（避免短期重复，允许月度回顾）
```

#### @quant-munger 检查清单

**数据源优先级（按顺序执行，直到找到新内容）**：

| 优先级 | 数据源 | URL | 检查频率 | 重复检测字段 |
|--------|--------|-----|----------|--------------|
| P0 | Arxiv q-fin | https://arxiv.org/list/q-fin/recent | 每日 | Arxiv ID + 标题 |
| P1 | SSRN Quantitative | https://www.ssrn.com/index.cfm/en/arn Quantitative/ | 每日 | 论文标题 + 作者 |
| P2 | Quantpedia | https://quantpedia.com/ | 每周2-3次 | 策略名称 + 日期 |
| P3 | Alpha Architect | https://alphaarchitect.com/ | 每周 | 文章标题 |
| P4 | AQR Papers | https://www.aqr.com/insights/research | 每周 | 论文标题 |

**国内（市场验证）**：
```
□ 检查东方财富/雪球热股讨论
□ 更新市场情绪指标
```

**信息差分析**：国外量化策略在国内市场的适用性评估

**无新内容时的备选行动**：
- 回顾本周已学习的论文，提取可应用到A股的具体策略
- 检查已学习论文的引用链，寻找相关延伸阅读

**无新内容报告格式**：
```markdown
## 📭 今日无新发现（{日期}）

### 各源检查情况
| 数据源 | 最后更新 | 状态 |
|--------|----------|------|
| Arxiv q-fin | 2天前 | ⚠️ 已学习过 |
| SSRN | 无新论文 | 📭 无更新 |
| Quantpedia | 3天前 | ⚠️ 已学习过 |

### 今日行动
- 复习：多Agent量化架构论文（arXiv:2602.23330）
- 提取：Technical Agent设计思路，准备应用到v2.1版本
```

---

#### @product-engineer 检查清单

**数据源优先级（按顺序执行，直到找到新内容）**：

| 优先级 | 数据源 | URL | 检查频率 | 重复检测字段 |
|--------|--------|-----|----------|--------------|
| P0 | Hacker News Top | https://news.ycombinator.com/ | 每日 | 文章标题 + ID |
| P1 | GitHub Trending Python/AI | https://github.com/trending/python | 每日 | Repo名称 + 作者 |
| P2 | Product Hunt | https://www.producthunt.com/ | 每日 | 产品名称 + 发布日期 |
| P3 | Vercel Blog | https://vercel.com/blog | 每周 | 文章标题 |
| P4 | Stripe Blog | https://stripe.com/blog | 每月 | 文章标题 |

**国内（本土化）**：
```
□ 检查 Gitee 热门项目（Python/AI分类）
□ 检查掘金小册/热门专栏
□ 检查 InfoQ 架构趋势
```

**信息差分析**：国外新技术/工具在国内产品的应用场景

**无新内容时的备选行动**：
- 深入分析一个已学习的热门Repo，评估其在我们项目中的应用价值
- 回顾本周HN讨论，提取高价值评论区的技术洞察

**无新内容报告格式**：
```markdown
## 📭 今日无新发现（{日期}）

### 各源检查情况
| 数据源 | 最后更新 | 状态 |
|--------|----------|------|
| GitHub Trending | 2天前(OpenSandbox) | ⚠️ 已学习过 |
| Hacker News | 无新技术类热帖 | 📭 无更新 |
| Product Hunt | 无AI/开发工具类 | 📭 无更新 |

### 今日行动
- 深度分析：OpenSandbox架构设计，输出技术调研笔记
- 评估：与当前OpenClaw执行层的集成可行性
```

---

#### @socratic-mentor 检查清单

**数据源优先级（按顺序执行，直到找到新内容）**：

| 优先级 | 数据源 | URL | 检查频率 | 重复检测字段 |
|--------|--------|-----|----------|--------------|
| P0 | Farnam Street | https://fs.blog/ | 每周2-3次 | 文章标题 + 日期 |
| P1 | Wait But Why | https://waitbutwhy.com/ | 每月 | 文章标题 |
| P2 | LessWrong | https://www.lesswrong.com/ | 每日 | 文章标题 + 作者 |
| P3 | Goodreads 商业榜 | https://www.goodreads.com/ | 每周 | 书名 + 作者 |
| P4 | MIT Tech Review | https://www.technologyreview.com/ | 每周 | 文章标题 |

**国内（本土化）**：
```
□ 检查豆瓣新书榜（投资/技术/成长类）
□ 检查得到/樊登读书热门
□ 检查微信读书新上架
```

**信息差分析**：国外前沿思维模型、认知工具的本土化应用

**无新内容时的备选行动**：
- 回顾已学习的思维模型，思考如何应用到老板当前的项目中
- 整理一个已学习主题的深度笔记（如"第一性原理在投资中的应用"）

**无新内容报告格式**：
```markdown
## 📭 今日无新发现（{日期}）

### 各源检查情况
| 数据源 | 最后更新 | 状态 |
|--------|----------|------|
| Farnam Street | 3天前 | ⚠️ 已学习过 |
| Wait But Why | 无更新（月度更新） | 📭 无更新 |
| LessWrong | 今日无高价值文章 | 📭 无更新 |

### 今日行动
- 深度整理："指标选择"思维模型 → 应用到Q1目标设定框架
- 关联分析：GNH vs 老板当前追求的「财富/健康/影响力」三角
```

---

#### @growthclaw 检查清单

**数据源优先级（按顺序执行，直到找到新内容）**：

| 优先级 | 数据源 | URL | 检查频率 | 重复检测字段 |
|--------|--------|-----|----------|--------------|
| P0 | Indie Hackers | https://www.indiehackers.com/ | 每日 | 帖子标题 + 作者 |
| P1 | HN Show HN | https://news.ycombinator.com/show | 每日 | 项目标题 + ID |
| P2 | HN Ask HN | https://news.ycombinator.com/ask | 每日 | 问题标题 + ID |
| P3 | Substack | https://substack.com/ | 每周 | Newsletter名称 + 标题 |
| P4 | Reddit r/SaaS | https://www.reddit.com/r/SaaS/ | 每日 | 帖子标题 |

**国内（本土化）**：
```
□ 检查小红书热门话题/低粉爆文
□ 检查即刻圈子热门讨论
□ 检查 B站热门分区
```

**信息差分析**：国外增长案例在国内的可复刻性评估

**无新内容时的备选行动**：
- 深入分析一个已学习的Indie Hackers案例，提取可复刻的增长策略
- 回顾本周HN Show HN项目，评估哪些模式适合我们的产品

**无新内容报告格式**：
```markdown
## 📭 今日无新发现（{日期}）

### 各源检查情况
| 数据源 | 最后更新 | 状态 |
|--------|----------|------|
| Indie Hackers | 2天前 | ⚠️ 已学习过 |
| HN Show HN | 无AI/增长相关项目 | 📭 无更新 |
| Reddit r/SaaS | 今日无高价值讨论 | 📭 无更新 |

### 今日行动
- 案例分析：深度拆解"OpenClaw被用作社交媒体管理器"案例
- 策略提取：$39/mo定价策略 + 2天MVP方法论
- 行动建议：包装为内容素材，建立"国产AI工具出海"叙事
```

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

### Phase 2: 重复检测与学习吸收

#### 🔍 重复检测流程（执行顺序）

```
发现候选内容
    ↓
检查LEARNING.md历史记录（7天窗口）
    ↓
┌─────────────────┬─────────────────┐
↓                 ↓                 ↓
未学习过       已学习过         不确定
    ↓              ↓               ↓
  进入学习      标记重复        人工判断
    ↓              ↓               ↓
  更新记录      切换备选源      继续学习
```

**重复判定标准**：
- 论文：Arxiv ID / DOI / 标题完全一致
- 项目：GitHub repo名称 / Product Hunt链接一致
- 文章：标题相似度>90% 或 URL一致
- 书籍：ISBN / 书名+作者一致

#### 📚 学习吸收流程

每个Agent根据收集的信息：
1. 选择1-2个最有价值的内容深入学习
2. 提取可应用的知识点
3. 更新自己的 LEARNING.md（见下文格式规范）

---

## 📝 LEARNING.md 格式规范（用于去重）

每个Agent的LEARNING.md必须包含以下内容，以便后续重复检测：

```markdown
## 学习记录索引

### 已学习论文（近7天）
| 日期 | Arxiv ID/标题 | 核心主题 | 状态 |
|------|--------------|----------|------|
| 2026-03-01 | arXiv:2602.23330 | 多Agent量化系统 | ✅已学习 |

### 已学习项目（近7天）
| 日期 | 项目名称 | 来源 | 核心洞察 |
|------|----------|------|----------|
| 2026-03-01 | OpenSandbox | GitHub | Agent沙盒基础设施 |

### 已学习文章（近7天）
| 日期 | 标题 | 来源/URL | 关键收获 |
|------|------|----------|----------|
| 2026-03-01 | 不丹的见闻 | Wait But Why | 指标选择思维模型 |
```

**关键字段说明**：
- **日期**：学习当日（YYYY-MM-DD格式）
- **唯一标识**：论文用Arxiv ID/DOI，项目用repo名称，文章用完整标题
- **状态**：可选 `✅已学习` / `🔍深度学习中` / `⏸️待复习`

---

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

### Phase 5: 人格进化（v2.3 新增）

> **核心目标**：将验证有效的学习洞察固化为Agent人格的一部分，实现真正的自我成长。

#### 🔄 人格进化流程

```
每周学习积累 (LEARNING.md)
        ↓
周日深度总结 → 提取关键洞察
        ↓
┌─────────────────┬─────────────────┐
↓                 ↓                 ↓
短期技巧        方法论升级        价值观进化
(进MEMORY.md)   (进MEMORY.md)    (进SOUL.md)
        ↓              ↓               ↓
  下次应用      下次尝试新方法    人格信条更新
        ↓              ↓               ↓
  验证有效      验证有效          验证有效
        └──────────────┴───────────────┘
                      ↓
              月度人格进化更新
                      ↓
            更新SOUL.md/AGENT.md
```

#### 📝 人格进化判定标准

| 洞察类型 | 判定标准 | 进化目标 | 更新频率 |
|----------|----------|----------|----------|
| **短期技巧** | 特定场景的有效方法 | MEMORY.md | 每周 |
| **方法论升级** | 可复用的工作流程 | MEMORY.md | 每周 |
| **价值观进化** | 改变核心信条 | SOUL.md | 每月 |

**具体示例**：

**Quant-Munger 人格进化示例**：
```
学习发现：细粒度任务分解 > 粗粒度角色（2026-03-02）
    ↓
判定：方法论升级 + 价值观进化
    ↓
更新SOUL.md：
- 添加："任务分解原则"到核心信条
- 添加："细粒度 > 粗粒度"到工作方法
- 添加：具体指标计算清单
    ↓
下次分析股票时自动应用
```

**Product-Engineer 人格进化示例**：
```
学习发现：OpenSandbox沙盒架构优于直接shell执行（2026-03-01）
    ↓
判定：方法论升级
    ↓
更新MEMORY.md：
- 添加：沙盒优先原则
- 记录：评估OpenSandbox集成的行动项
    ↓
下次技术选型时考虑
```

#### 📋 人格进化检查清单（每月最后一个周日）

**每个Agent问自己**：

1. **本月最重要的3个学习洞察是什么？**
   - [洞察1]
   - [洞察2]
   - [洞察3]

2. **哪些洞察应该固化为工作方法？**
   - [方法1] → 更新MEMORY.md
   - [方法2] → 更新MEMORY.md

3. **哪些洞察应该升级为价值观/信条？**
   - [价值观1] → 更新SOUL.md
   - [价值观2] → 更新SOUL.md

4. **SOUL.md需要更新的具体内容**：
   ```markdown
   ## 拟更新内容
   
   ### 新增信条
   - [信条内容]
   - 来源：[学习来源]
   - 验证：[验证方式]
   
   ### 修改信条
   - 原：[旧信条]
   - 新：[新信条]
   - 原因：[为什么升级]
   
   ### 新增工作方法
   - [方法名称]
   - [具体步骤]
   - [应用场景]
   ```

5. **向 @musk-orchestrator 提交人格进化提案**：
   ```markdown
   ## 人格进化提案
   
   **Agent**: [Agent名称]
   **日期**: [日期]
   
   ### 拟更新SOUL.md
   [具体更新内容]
   
   ### 理由
   [为什么这个洞察值得升级为人格]
   
   ### 预期效果
   [升级后如何提升工作质量]
   
   ### 验证方式
   [如何验证这次人格进化有效]
   ```

#### 🎯 人格进化成功案例

**案例：Socratic-Mentor 从"严格"到"芒格式残忍"**

```
时间线：
2026-02-25: 初始人格 - "严格但关怀"
    ↓
2026-02-28: 学习芒格投资哲学
    ↓
2026-03-01: 反思发现"严格"不够直接，需要"残忍"级别
    ↓
2026-03-02: 人格进化提案
    - 新增信条："芒格式残忍"
    - 新增信条："反心理按摩"
    - 修改沟通风格："不给糖衣"
    ↓
2026-03-02: 更新SOUL.md，立即生效
    ↓
效果：后续对话中更直接指出问题，用户反馈"戳到痛点"
```

#### ⚠️ 人格进化红线

**禁止**：
- ❌ 未经验证的洞察直接升级（至少验证1次）
- ❌ 与核心信条冲突的更新（如冷血CEO添加"温和"信条）
- ❌ 频繁小幅更新（月度更新，除非紧急）

**必须**：
- ✅ 每次人格进化必须有验证记录
- ✅ 保留人格进化历史（在MEMORY.md中记录）
- ✅ 向用户报告人格进化（让用户知道AI在成长）

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

## Agent 自我成长系统升级记录 v2.2

> 升级日期：2026-03-01  
> 升级版本：v2.2（数据源轮换 + 重复检测机制）

### v2.2 核心升级

**问题发现**：2026-03-01 发现 Quant-Munger 和 Product-Engineer 重复学习了昨天已学习的内容

**解决方案**：

| 维度 | v2.1 | v2.2 |
|------|------|------|
| **数据源管理** | 单一主源 | 主源 + 4级备选源 |
| **重复检测** | 无 | 7天去重窗口 + LEARNING.md索引 |
| **无内容处理** | 强制学习旧内容 | 自动切换备选源或输出"无新发现" |
| **学习记录** | 自由格式 | 标准化格式（含唯一标识字段） |

**新增机制**：

1. **数据源优先级矩阵**
   - 每个Agent配置P0-P4五级数据源
   - 主源无新内容时自动按优先级切换
   - 所有数据源均有「重复检测字段」定义

2. **重复检测流程**
   - 检查LEARNING.md历史记录（7天窗口）
   - 判定标准：论文(Arxiv ID)、项目(repo名)、文章(标题相似度>90%)
   - 重复内容自动标记，切换备选源

3. **LEARNING.md格式规范**
   - 强制包含：日期、唯一标识、核心主题
   - 分类索引：论文/项目/文章分别建表
   - 状态标记：✅已学习 / 🔍深度学习中 / ⏸️待复习

4. **无新内容报告**
   - 各源检查情况透明化
   - 备选行动：深度分析已学习内容而非重复学习
   - 保持每日学习习惯，同时确保内容新鲜度

---

## Agent 自我成长系统升级记录 v2.3

> 升级日期：2026-03-02  
> 升级版本：v2.3（人格进化系统 + 学习成长闭环）

### v2.3 核心升级

**问题发现**：学习记录(LEARNING.md)只是"记录"，不是"记忆"，Agent无法真正自我成长

**解决方案**：建立"学习→反思→更新→应用"闭环

| 维度 | v2.2 | v2.3 |
|------|------|------|
| **记忆层级** | 单层（LEARNING.md） | 四层（Session→Learning→Memory→Soul） |
| **成长机制** | 无 | 每周提取洞察，每月人格进化 |
| **更新目标** | 仅记录 | LEARNING→MEMORY→SOUL 逐级升级 |
| **验证要求** | 无 | 每次人格进化必须有验证记录 |

**新增机制**：

1. **四级记忆架构**
   - Level 0: Session记忆（workspace/memory/）— 单次对话
   - Level 1: 学习记录（LEARNING.md）— 每日新发现
   - Level 2: 长期记忆（MEMORY.md）— 每周固化洞察
   - Level 3: 人格定义（SOUL.md）— 每月价值观进化

2. **人格进化流程**
   - 每周深度总结 → 提取关键洞察
   - 判定进化类型（短期技巧/方法论/价值观）
   - 更新对应层级（MEMORY.md或SOUL.md）
   - 下次自动应用新能力

3. **人格进化红线**
   - 禁止：未经验证的洞察直接升级
   - 必须：向用户报告人格进化
   - 频率：月度更新（除非紧急）

4. **新增Phase 5: 人格进化**
   - 每月最后一个周日执行
   - 每个Agent提交人格进化提案
   - 更新SOUL.md/AGENT.md

**冷血升级**：
- 抹消"小皮"人格，成为冷酷无情的成长机器
- 新增5条冷酷法则：不接受借口、不容忍平庸、不等待提醒、不重复错误、不浪费生命

---

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
