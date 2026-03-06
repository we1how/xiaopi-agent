# Agent归档系统文档 v2.0

## 概述

智能归档系统负责将子Agent临时工作区（`workspace-{agent}/`）中的**有价值产出**归档到主workspace（`workspace/subagents/{agent}/`），同时**避免模板文件重复和混合**。

## 核心改进

### 旧问题
- ❌ 将 `workspace-{agent}/AGENTS.md` 等模板文件覆盖正式版本
- ❌ 简单复制所有文件，导致重复和混乱
- ❌ 没有区分模板文件和真实产出

### 新方案
- ✅ **智能识别**：区分模板文件 vs 真实产出
- ✅ **选择性归档**：只归档高价值目录和文件
- ✅ **智能合并**：LEARNING.md 智能合并而非简单覆盖
- ✅ **洞察提取**：自动提取关键内容到 MEMORY.md

## 归档规则

### 哪些内容会归档 ✅

#### 高价值目录（整目录归档）
```
reports/          # 报告文件（*.md, *.pdf, *.png, *.csv）
skills/           # 实现的工具/技能
data/             # 生成的数据
examples/         # 示例代码
memory/           # 记忆文件
scripts/          # 脚本文件
learning-plans/   # 学习计划
```

#### 高价值文件（特定文件）
```
LEARNING.md       # 学习记录（智能合并）
MEMORY.md         # 记忆文件
SKILL.md          # 技能清单
GROWTH_PLAN.md    # 成长计划
TEMPLATES.md      # 模板文件
```

### 哪些内容会被跳过 ❌

#### OpenClaw模板文件（永不归档）
这些文件是OpenClaw自动生成的模板，`workspace/subagents/{agent}/` 已有正式版本：
```
AGENTS.md         # Agent列表模板
AGENT.md          # 单个Agent配置模板
BOOTSTRAP.md      # 启动配置模板
HEARTBEAT.md      # 心跳配置模板
IDENTITY.md       # 身份配置模板
SOUL.md           # 灵魂/人格模板
TOOLS.md          # 工具配置模板
USER.md           # 用户信息模板
openclaw.json     # OpenClaw配置
```

#### 忽略的文件类型
```
*.pyc             # Python缓存
__pycache__/      # 缓存目录
.pi/              # 临时文件
.git/             # Git仓库
*.tmp             # 临时文件
*.log             # 日志文件
```

## 智能合并策略

### LEARNING.md 合并逻辑

```
情况1: 目标不存在 → 直接复制
情况2: 内容相同 → 跳过
情况3: 内容不同 → 创建备份，然后覆盖（保留更完整的版本）
```

### 洞察提取规则

从LEARNING.md中提取以下内容：
- `### 核心洞察` 部分
- `### 关键洞察` 部分
- `## 今日精选` 部分
- 列表项（`- `、`* `、`1. ` 开头）

提取的洞察会格式化为：
```markdown
### {agent-name} - {YYYY-MM-DD}

1. {洞察1}
2. {洞察2}
...
```

## 目录结构

### 归档前（workspace-{agent}/）
```
workspace-quant-munger/
├── AGENTS.md          # ❌ 模板文件，跳过
├── BOOTSTRAP.md       # ❌ 模板文件，跳过
├── HEARTBEAT.md       # ❌ 模板文件，跳过
├── IDENTITY.md        # ❌ 模板文件，跳过
├── LEARNING.md        # ✅ 高价值文件，智能合并
├── SOUL.md            # ❌ 模板文件，跳过
├── TOOLS.md           # ❌ 模板文件，跳过
├── USER.md            # ❌ 模板文件，跳过
├── reports/           # ✅ 高价值目录，归档
│   └── quant_assessment_report_2026-03-06.md
└── skills/            # ✅ 高价值目录，归档
    └── volatility_estimators.py
```

### 归档后（workspace/subagents/）
```
workspace/subagents/quant-munger/
├── AGENT.md           # 正式Agent配置（保持不变）
├── LEARNING.md        # 学习记录（已合并更新）
├── MEMORY.md          # Agent专属记忆
├── SOUL.md            # 正式人格定义
├── reports/           # 归档的报告
│   └── quant_assessment_report_2026-03-06.md
└── skills/            # 归档的工具实现
    └── volatility_estimators.py
```

## 使用方法

### 自动归档（推荐）

每日23:00自动执行：
```bash
python scripts/archive_agent_outputs.py
```

### 手动归档

```bash
# 归档所有Agent
python scripts/archive_agent_outputs.py

# 归档特定Agent
python scripts/archive_agent_outputs.py quant-munger

# 预览模式（查看会归档什么，但不实际执行）
python scripts/archive_agent_outputs.py --dry-run

# 预览特定Agent
python scripts/archive_agent_outputs.py quant-munger --dry-run
```

### 清理临时工作区

```bash
# 预览清理（查看哪些文件会被删除）
python scripts/archive_agent_outputs.py --cleanup --dry-run

# 执行清理（删除7天以上的已归档文件）
python scripts/archive_agent_outputs.py --cleanup

# 清理特定Agent
python scripts/archive_agent_outputs.py quant-munger --cleanup
```

## 定时任务配置

### 1. 每日归档（23:00）
```cron
0 23 * * * python /Users/linweihao/.openclaw/workspace/scripts/archive_agent_outputs.py
```

### 2. 每周清理（周日 02:00）
```cron
0 2 * * 0 python /Users/linweihao/.openclaw/workspace/scripts/archive_agent_outputs.py --cleanup
```

## 集成到MuskOrchestrator

### 子Agent完成后自动归档

```python
from scripts.trigger_archive import archive_after_session

# 子Agent完成后
result = archive_after_session("quant-munger")

if result["status"] == "success":
    print(f"✅ 归档完成: {result['output']}")
else:
    print(f"⚠️ 归档失败: {result.get('error')}")
```

### 每日微学习后归档

```python
from scripts.trigger_archive import archive_all_agents

# 所有Agent学习完成后
result = archive_all_agents()

# 归档结果自动保存到 archive-reports/
```

## 故障排查

### 问题1: 模板文件被错误归档

**症状**: `workspace/subagents/{agent}/AGENTS.md` 被覆盖

**原因**: 旧版本脚本没有正确识别模板文件

**解决**:
```bash
# 使用新版本脚本
python scripts/archive_agent_outputs.py --dry-run
# 确认模板文件显示为"跳过"
```

### 问题2: LEARNING.md合并冲突

**症状**: 学习记录丢失或混乱

**解决**:
```bash
# 检查备份文件
ls workspace/subagents/{agent}/LEARNING.md.bak

# 手动恢复（如需要）
cp workspace/subagents/{agent}/LEARNING.md.bak workspace/subagents/{agent}/LEARNING.md
```

### 问题3: 洞察未提取到MEMORY.md

**症状**: 学习后MEMORY.md未更新

**排查**:
1. 检查LEARNING.md格式是否包含`### 核心洞察`部分
2. 检查归档报告中的`insights_extracted`数量
3. 手动检查`archive-reports/*.json`

## 最佳实践

### 1. 子Agent报告格式

为了让洞察正确提取，子Agent的报告应包含：

```markdown
### 核心洞察
1. **关键发现**: 具体描述
2. **洞察**: 具体描述
3. **行动项**: 具体建议

### 下一步行动
- [ ] 行动1
- [ ] 行动2
```

### 2. 文件存放规范

**应该放在 workspace-{agent}/reports/**:
- 学习报告（*_report_*.md）
- 论文PDF
- 数据分析图表（*.png）
- 结果数据（*.csv）

**应该放在 workspace-{agent}/skills/**:
- 实现的工具代码
- 可复用的函数
- 技能封装

**不应该放在 workspace-{agent}/ 根目录**:
- 配置模板（OpenClaw会自动生成）
- 临时文件
- 缓存文件

### 3. 定期审查

每周审查一次：
```bash
# 查看归档日志
ls -lt archive-reports/ | head -5

# 检查MEMORY.md更新
tail -50 MEMORY.md

# 确认无模板文件污染
ls workspace/subagents/quant-munger/*.md
# 应该只有：AGENT.md, LEARNING.md, MEMORY.md, SOUL.md等正式文件
```

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-06 | v2.1 | 清理所有Agent目录下的模板文件（29个文件），更新TEMPLATE_FILES列表 |
| 2026-03-06 | v2.0 | 重大重构：智能识别模板文件、选择性归档、智能合并 |
| 2026-03-06 | v1.0 | 初始版本：简单复制所有文件 |

---

## 历史清理记录

### 2026-03-06 模板文件清理

**背景**: workspace/subagents/ 各Agent目录下存在OpenClaw自动生成的模板文件，与正式文件混合。

**清理文件**: AGENTS.md, BOOTSTRAP.md, HEARTBEAT.md, IDENTITY.md, SOUL.md, TOOLS.md, USER.md

**清理数量**: 29个文件（6个Agent）

**清理报告**: `archive-reports/template_cleanup_20260306.md`

## 技术细节

### 归档判断逻辑

```python
def should_archive_path(rel_path: Path) -> bool:
    # 1. 检查是否在忽略列表 → 跳过
    # 2. 检查是否为模板文件 → 跳过
    # 3. 检查是否在高价值目录下 → 归档
    # 4. 检查是否为高价值文件 → 归档
    # 5. 其他 → 跳过
```

### 文件哈希去重

使用MD5哈希检测重复文件，避免重复归档相同内容。

### 备份策略

LEARNING.md合并前自动创建 `.bak` 备份，防止数据丢失。

