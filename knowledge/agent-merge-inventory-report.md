# Agent文件三源合并盘点报告

> 生成时间：2026-03-02  
> 目的：整合 ~/.openclaw/agents/、workspace/subagents/、workspace-*/ 三处Agent定义

---

## 📊 文件分布总览

### 位置1: ~/.openclaw/agents/ (OpenClaw系统配置)
```
agents/
├── AGENTS.md                    # 团队架构文档
├── main/
│   └── SOUL.md                  # 主Agent人格
├── musk-orchestrator/
│   └── SOUL.md
├── product-engineer/
│   └── SOUL.md
├── quant-munger/
│   └── SOUL.md
├── rigorous-qa/
│   └── SOUL.md
└── socratic-mentor/
    └── SOUL.md
```
**特点**：只有SOUL.md，没有LEARNING.md等学习记录文件

---

### 位置2: ~/.openclaw/workspace/subagents/ (我们的学习记录区)
```
subagents/
├── growthclaw/
│   ├── AGENT.md                 # Agent定义
│   ├── GROWTH_PLAN.md          # 成长计划
│   ├── LEARNING.md             # 学习记录 ⭐重要
│   ├── SKILL.md                # 技能清单
│   ├── SOUL.md                 # Agent人格（专业版）
│   └── TEMPLATES.md            # 内容模板
├── musk-orchestrator/
│   └── SOUL.md
├── planner/
│   └── AGENT.md
├── product-engineer/
│   ├── AGENT.md
│   ├── GROWTH_PLAN.md
│   ├── LEARNING.md             # 学习记录 ⭐重要
│   └── SOUL.md
├── quant-munger/
│   ├── AGENT.md
│   ├── GROWTH_PLAN.md
│   ├── LEARNING.md             # 学习记录 ⭐重要
│   └── SOUL.md
├── rigorous-qa/
│   ├── AGENT.md
│   ├── GROWTH_PLAN.md
│   └── SOUL.md
└── socratic-mentor/
    ├── AGENT.md
    ├── GROWTH_PLAN.md
    ├── LEARNING.md             # 学习记录 ⭐重要
    └── SOUL.md
```
**特点**：完整Agent定义（SOUL+AGENT），有GROWTH_PLAN和LEARNING记录

---

### 位置3: ~/.openclaw/workspace-*/ (孤立Workspace)
```
workspace-growthclaw/
├── AGENTS.md                    # 通用团队架构（旧版）
├── BOOTSTRAP.md
├── HEARTBEAT.md
├── IDENTITY.md
├── LEARNING.md                  # 学习记录 ⭐需要合并
├── SOUL.md                      # 通用模板（英文）
├── TOOLS.md
└── USER.md

workspace-musk-orchestrator/
├── AGENTS.md
├── BOOTSTRAP.md
├── HEARTBEAT.md
├── IDENTITY.md
├── SOUL.md
├── TOOLS.md
├── USER.md
├── output/
│   └── oversold_bounce_strategy_growth_analysis.md  # 产出文件 ⭐需要迁移
├── oversold_rebound_implementation_plan.md          # 计划文件 ⭐需要迁移
└── subagents/
    └── growthclaw/
        └── LEARNING.md          # 嵌套学习记录 ⭐需要合并

workspace-product-engineer/
├── AGENTS.md
├── BOOTSTRAP.md
├── HEARTBEAT.md
├── IDENTITY.md
├── LEARNING.md                  # 学习记录 ⭐需要合并
├── SOUL.md
├── TOOLS.md
├── USER.md
├── experiments/
│   └── context-compression-report.md  # 实验报告 ⭐需要迁移
└── subagents/
    └── product-engineer/
        └── LEARNING.md          # 嵌套学习记录 ⭐需要合并

workspace-quant-munger/
├── AGENTS.md
├── BOOTSTRAP.md
├── HEARTBEAT.md
├── IDENTITY.md
├── LEARNING.md                  # 学习记录 ⭐需要合并
├── SOUL.md
├── TOOLS.md
├── USER.md
├── quant_analysis_oversold_bounce.md  # 分析报告 ⭐需要迁移
├── stock-platform/
│   └── data/
│       └── README.md            # 数据文档 ⭐需要迁移
└── subagents/
    └── quant-munger/
        └── LEARNING.md          # 嵌套学习记录 ⭐需要合并

workspace-socratic-mentor/
├── AGENTS.md
├── BOOTSTRAP.md
├── HEARTBEAT.md
├── IDENTITY.md
├── LEARNING.md                  # 学习记录 ⭐需要合并
├── SOUL.md
├── TOOLS.md
├── USER.md
└── subagents/
    └── socratic-mentor/
        └── LEARNING.md          # 嵌套学习记录 ⭐需要合并
```
**特点**：
1. 每个agent一个完整workspace（类似everything-claude-code架构）
2. 包含AGENTS.md、BOOTSTRAP.md等全局文件（可能过时）
3. 有LEARNING.md学习记录
4. 有subagents/*/LEARNING.md嵌套记录
5. 有output/、experiments/等产出文件
6. SOUL.md是通用英文模板（非专业定义）

---

## 🔍 关键差异对比

### SOUL.md 对比

| Agent | agents/版本 | subagents/版本 | workspace-*/版本 |
|-------|-------------|----------------|------------------|
| Growthclaw | 无 | ✅ 专业中文定义 | ❌ 通用英文模板 |
| Product-Engineer | 中文，较简短 | ✅ 详细专业定义 | ❌ 通用英文模板 |
| Quant-Munger | 中文，较简短 | ✅ 详细专业定义 | ❌ 通用英文模板 |
| Socratic-Mentor | 中文，较简短 | ✅ 详细专业定义 | ❌ 通用英文模板 |
| Musk-Orchestrator | 无 | ✅ 详细专业定义 | ❌ 通用英文模板 |
| Rigorous-QA | 简短 | ✅ 详细专业定义 | 无对应workspace |

**结论**：subagents/版本最完整专业，应以它为准

---

## 📦 需要迁移的内容

### 高价值文件（必须保留）

#### 1. 学习记录 (LEARNING.md)
| 来源 | 文件路径 | 重要性 |
|------|----------|--------|
| subagents/ | growthclaw/LEARNING.md | ⭐⭐⭐ |
| subagents/ | product-engineer/LEARNING.md | ⭐⭐⭐ |
| subagents/ | quant-munger/LEARNING.md | ⭐⭐⭐ |
| subagents/ | socratic-mentor/LEARNING.md | ⭐⭐⭐ |
| workspace-growthclaw/ | LEARNING.md | ⭐⭐ 待对比合并 |
| workspace-product-engineer/ | LEARNING.md | ⭐⭐ 待对比合并 |
| workspace-quant-munger/ | LEARNING.md | ⭐⭐ 待对比合并 |
| workspace-socratic-mentor/ | LEARNING.md | ⭐⭐ 待对比合并 |
| workspace-musk-orchestrator/subagents/growthclaw/ | LEARNING.md | ⭐ 嵌套，需检查 |
| workspace-product-engineer/subagents/product-engineer/ | LEARNING.md | ⭐ 嵌套，需检查 |
| workspace-quant-munger/subagents/quant-munger/ | LEARNING.md | ⭐ 嵌套，需检查 |
| workspace-socratic-mentor/subagents/socratic-mentor/ | LEARNING.md | ⭐ 嵌套，需检查 |

#### 2. 成长计划 (GROWTH_PLAN.md)
仅存在于subagents/，无需迁移

#### 3. 技能清单 (SKILL.md)
仅存在于subagents/growthclaw/，无需迁移

#### 4. 内容模板 (TEMPLATES.md)
仅存在于subagents/growthclaw/，无需迁移

#### 5. 产出文件 (需要迁移到主workspace)
| 来源 | 文件 | 建议迁移位置 |
|------|------|--------------|
| workspace-musk-orchestrator/output/ | oversold_bounce_strategy_growth_analysis.md | workspace/knowledge/research/quant/ |
| workspace-musk-orchestrator/ | oversold_rebound_implementation_plan.md | workspace/stock-platform/docs/ |
| workspace-product-engineer/experiments/ | context-compression-report.md | workspace/knowledge/research/engineering/ |
| workspace-quant-munger/ | quant_analysis_oversold_bounce.md | workspace/knowledge/research/quant/ |
| workspace-quant-munger/stock-platform/data/ | README.md | workspace/stock-platform/data/ |

#### 6. Agent定义文件
| 来源 | 文件 | 合并策略 |
|------|------|----------|
| subagents/*/ | AGENT.md | 复制到agents/*/AGENT.md |
| subagents/*/ | SOUL.md | 覆盖agents/*/SOUL.md |
| subagents/*/ | GROWTH_PLAN.md | 暂不迁移（非运行时必需）|

---

## ⚠️ 冲突文件处理

### 冲突1: SOUL.md
- **agents/**: 简短中文版本（可能已过时）
- **subagents/**: 详细专业中文版本 ⭐以此为准
- **workspace-/**: 通用英文模板（可废弃）

**处理策略**：subagents/版本覆盖agents/版本

### 冲突2: LEARNING.md（多份）
需要对比合并：
1. subagents/版本（主）
2. workspace-*/版本（待合并）
3. workspace-*/subagents/*/版本（嵌套，可能重复）

**处理策略**：
- 以subagents/版本为基础
- 将workspace-*/版本内容追加合并
- 检查并去重

### 冲突3: 全局文件 (AGENTS.md, BOOTSTRAP.md等)
- **workspace/**: 当前主workspace的版本（最新）
- **workspace-*/**: 旧版孤立workspace的版本

**处理策略**：检查差异，如有新内容合并到workspace/版本

---

## 🎯 迁移计划

### Phase 1: 准备阶段
1. ✅ 完成本盘点报告
2. ⏳ 创建备份分支（git备份）
3. ⏳ 验证各文件内容差异

### Phase 2: 合并Agent定义
1. ⏳ 将subagents/*/SOUL.md 复制到 agents/
2. ⏳ 将subagents/*/AGENT.md 复制到 agents/
3. ⏳ 验证agents/配置可被OpenClaw正确加载

### Phase 3: 合并学习记录
1. ⏳ 对比合并多份LEARNING.md
2. ⏳ 更新格式规范（v2.2索引格式）
3. ⏳ 去重整理

### Phase 4: 迁移产出文件
1. ⏳ 将workspace-*/中的重要产出文件迁移到workspace/正确位置
2. ⏳ 更新文件引用路径

### Phase 5: 更新关联系统
1. ⏳ 检查cron任务配置
2. ⏳ 检查HEARTBEAT.md引用路径
3. ⏳ 检查代码中硬编码路径
4. ⏳ 检查脚本引用

### Phase 6: 用户检验
1. ⏳ 提交给用户检验
2. ⏳ 根据反馈调整
3. ⏳ 确认无误后清理subagents/和workspace-*/

---

## 📋 文件清单总结

### 需要创建的（agents/缺失的）
- [ ] agents/growthclaw/ (整个文件夹)
- [ ] agents/rigorous-qa/AGENT.md

### 需要覆盖的（agents/已有但过时的）
- [ ] agents/*/SOUL.md (全部6个Agent)
- [ ] agents/AGENTS.md (对比workspace版本)

### 需要合并的（多份LEARNING.md）
- [ ] growthclaw: subagents/ + workspace-growthclaw/ + 嵌套版本
- [ ] product-engineer: subagents/ + workspace-product-engineer/ + 嵌套版本
- [ ] quant-munger: subagents/ + workspace-quant-munger/ + 嵌套版本
- [ ] socratic-mentor: subagents/ + workspace-socratic-mentor/ + 嵌套版本
- [ ] musk-orchestrator: workspace-musk-orchestrator/subagents/

### 需要迁移的（产出文件）
- [ ] 5个产出文件到workspace/正确位置

### 可以废弃的（确认后清理）
- [ ] workspace-*/AGENTS.md (对比后)
- [ ] workspace-*/BOOTSTRAP.md (对比后)
- [ ] workspace-*/HEARTBEAT.md (对比后)
- [ ] workspace-*/IDENTITY.md (对比后)
- [ ] workspace-*/SOUL.md (通用模板)
- [ ] workspace-*/TOOLS.md (对比后)
- [ ] workspace-*/USER.md (对比后)

---

## ⚡ 预计工作量

| 任务 | 预计时间 | 复杂度 |
|------|----------|--------|
| 文件对比分析 | 30分钟 | 中 |
| Agent定义合并 | 20分钟 | 低 |
| LEARNING.md合并 | 1-2小时 | 高（需仔细去重）|
| 产出文件迁移 | 30分钟 | 低 |
| 关联系统检查 | 1小时 | 中 |
| 测试验证 | 30分钟 | 中 |
| **总计** | **3-4小时** | - |

---

## 🚀 下一步行动

等待用户确认本盘点报告后，开始Phase 2-5的执行。

关键决策点：
1. 是否确认以subagents/版本为SOUL.md真相源？
2. 是否同意废弃workspace-*/中的通用英文SOUL.md？
3. 产出文件迁移目标位置是否正确？
