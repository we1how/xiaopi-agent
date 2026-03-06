# Agent归档系统 - 前后对比

## 问题背景

### 旧归档方案的问题

```
workspace-quant-munger/                    workspace/subagents/quant-munger/
├── AGENTS.md     ──────┐                   ├── AGENT.md      ◀── 正式配置
├── BOOTSTRAP.md  ──────┤                   ├── LEARNING.md   ◀── 正式学习记录
├── HEARTBEAT.md  ──────┼── ❌ 全部复制    ├── SOUL.md       ◀── 正式人格定义
├── LEARNING.md   ──────┤    导致混合      ├── ...
├── SOUL.md       ──────┤                   └── （被模板文件覆盖！）
└── reports/
    └── report.md

问题：
1. AGENTS.md 覆盖 AGENT.md（文件名不同，内容冲突）
2. 模板文件和正式文件混合
3. 无法区分哪些是有价值的产出
```

## 新归档方案

### 智能识别与选择性归档

```
workspace-quant-munger/                    workspace/subagents/quant-munger/
├── AGENTS.md     ──────┐                   ├── AGENT.md      ◀── 保持不变
├── BOOTSTRAP.md  ──────┤                   ├── LEARNING.md   ◀── 智能合并 ✅
├── HEARTBEAT.md  ──────┼── ❌ 跳过        ├── SOUL.md       ◀── 保持不变
├── IDENTITY.md   ──────┤    （模板文件）   ├── reports/      ◀── 新增归档 ✅
├── LEARNING.md   ──────┼── ✅ 智能合并    │   └── report.md
├── SOUL.md       ──────┤                   └── skills/       ◀── 新增归档 ✅
├── TOOLS.md      ──────┘                       └── tool.py
├── USER.md       ──────┘
│
├── reports/      ──────┐
│   └── report.md ──────┼── ✅ 归档
│                       │    （高价值目录）
├── skills/       ──────┤
│   └── tool.py   ──────┘
│
└── data/         ──────┐
    └── result.csv ─────┘── ✅ 归档
```

## 归档规则详解

### 规则1：模板文件跳过 ❌

OpenClaw自动生成的模板文件，不应覆盖正式版本：

| 模板文件 | 状态 | 原因 |
|---------|------|------|
| AGENTS.md | ❌ 跳过 | 模板，workspace/subagents/有正式AGENT.md |
| BOOTSTRAP.md | ❌ 跳过 | 启动配置模板 |
| HEARTBEAT.md | ❌ 跳过 | 心跳配置模板 |
| IDENTITY.md | ❌ 跳过 | 身份配置模板 |
| SOUL.md | ❌ 跳过 | 人格模板（会覆盖正式SOUL.md） |
| TOOLS.md | ❌ 跳过 | 工具配置模板 |
| USER.md | ❌ 跳过 | 用户信息模板 |

### 规则2：高价值文件归档 ✅

| 文件 | 处理方式 | 说明 |
|------|---------|------|
| LEARNING.md | 智能合并 | 提取新内容追加，创建备份 |
| MEMORY.md | 直接复制 | Agent专属记忆 |
| SKILL.md | 直接复制 | 技能清单 |
| GROWTH_PLAN.md | 直接复制 | 成长计划 |

### 规则3：高价值目录归档 ✅

```
reports/     ──►  报告文件（*.md, *.pdf, *.png, *.csv）
skills/      ──►  工具实现（*.py, *.js等）
data/        ──►  生成数据（*.csv, *.json等）
examples/    ──►  示例代码
memory/      ──►  记忆文件
scripts/     ──►  脚本文件
```

## 实际效果对比

### 执行前

```bash
$ ls workspace/subagents/quant-munger/
AGENT.md        # 正式配置
LEARNING.md     # 旧学习记录
MEMORY.md       # 旧记忆
SOUL.md         # 正式人格

$ ls workspace-quant-munger/
AGENTS.md       # 模板（不应复制）
BOOTSTRAP.md    # 模板（不应复制）
LEARNING.md     # 新学习记录（应合并）
reports/        # 报告（应归档）
    └── quant_assessment_report_2026-03-06.md
```

### 执行后（旧脚本）

```bash
$ ls workspace/subagents/quant-munger/
AGENT.md        # 保留
AGENTS.md       # ❌ 错误！模板文件混入
BOOTSTRAP.md    # ❌ 错误！模板文件混入
LEARNING.md     # ❌ 被覆盖！内容可能丢失
MEMORY.md       # 保留
SOUL.md         # 保留
reports/        # 归档成功
    └── quant_assessment_report_2026-03-06.md

问题：
- AGENTS.md 和 AGENT.md 并存，造成混淆
- LEARNING.md 被简单覆盖，可能丢失历史内容
```

### 执行后（新脚本）

```bash
$ ls workspace/subagents/quant-munger/
AGENT.md        # ✅ 保持不变
LEARNING.md     # ✅ 智能合并（保留历史+新增内容）
LEARNING.md.bak # ✅ 自动备份
MEMORY.md       # ✅ 保持不变
SOUL.md         # ✅ 保持不变
reports/        # ✅ 成功归档
    └── quant_assessment_report_2026-03-06.md

优势：
- 无模板文件混入
- LEARNING.md 完整保留
- 有备份可恢复
```

## 使用示例

### 每日自动归档

```bash
$ python scripts/archive_agent_outputs.py

📦 Agent智能归档脚本
==================================================
发现Agent: growthclaw, product-engineer, socratic-mentor, quant-munger

🔄 处理 growthclaw...
  ✅ 归档: 0 个文件
  ✅ 合并: 1 个文件 (LEARNING.md)
  ⚪ 跳过: 7 个文件（模板/忽略）
  ✅ 洞察: 提取 10 条

🔄 处理 quant-munger...
  ✅ 归档: 2 个文件 (reports/)
  ✅ 合并: 1 个文件 (LEARNING.md)
  ⚪ 跳过: 8 个文件（模板/忽略）
  ✅ 洞察: 提取 8 条

📄 归档报告保存到: archive-reports/archive_20260306_135311.json
==================================================
归档完成！共提取 20 条洞察到 MEMORY.md
```

### 预览模式

```bash
$ python scripts/archive_agent_outputs.py --dry-run

【预览模式 - 不会实际修改文件】

🔄 处理 quant-munger...
  ✅ 归档: 2 个文件
     - reports/quant_assessment_report_2026-03-06.md
     - skills/volatility_estimators.py
  ⚪ 跳过: 8 个文件（模板/忽略）
     - AGENTS.md (模板)
     - BOOTSTRAP.md (模板)
     - HEARTBEAT.md (模板)
     - ...

预览完成！去掉 --dry-run 执行实际归档
```

## 关键改进点

| 维度 | 旧方案 | 新方案 |
|------|--------|--------|
| **模板文件** | ❌ 全部复制，造成混合 | ✅ 智能识别，跳过模板 |
| **LEARNING.md** | ❌ 简单覆盖，可能丢失内容 | ✅ 智能合并，保留历史 |
| **备份机制** | ❌ 无备份 | ✅ 自动创建.bak备份 |
| **洞察提取** | ❌ 无 | ✅ 自动提取到MEMORY.md |
| **选择性归档** | ❌ 全量复制 | ✅ 只归档高价值内容 |
| **预览模式** | ❌ 无 | ✅ --dry-run预览 |

## 推荐工作流

### 1. 子Agent生成内容

```
workspace-quant-munger/
├── LEARNING.md          # 写入新学习记录
└── reports/
    └── daily_report.md  # 生成报告
```

### 2. 自动归档（每日23:00）

```bash
python scripts/archive_agent_outputs.py

处理结果：
- 跳过模板文件（AGENTS.md, BOOTSTRAP.md等）
- 智能合并 LEARNING.md
- 归档 reports/daily_report.md
- 提取洞察到 MEMORY.md
```

### 3. 清理临时文件（每周日02:00）

```bash
python scripts/archive_agent_outputs.py --cleanup

清理结果：
- 删除7天前的已归档报告
- 保留LEARNING.md作为备份
- workspace-quant-munger/ 保持精简
```

## 总结

新归档系统解决了核心问题：
1. **避免模板文件混合** - 智能识别并跳过
2. **保护正式配置** - 不再覆盖AGENT.md等文件
3. **智能合并学习记录** - 保留历史+新增内容
4. **自动提取洞察** - 关键内容进入MEMORY.md

**一句话**：只归档有价值的产出，不碰模板文件。
