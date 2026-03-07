# 文件存放规范指南

> **必读**：所有Agent产出文件必须按此规范存放，否则将被视为错误

---

## 1. 目录结构规范

### 1.1 核心原则

**所有Agent产出必须存放在 `workspace/subagents/{agent}/` 下**

禁止随意创建目录，禁止存放在 `workspace-{agent}/` 作为最终位置

### 1.2 标准目录结构

```
workspace/subagents/{agent}/
├── AGENT.md                    # Agent配置（必需）
├── LEARNING.md                 # 学习记录（必需，实时同步）
├── MEMORY.md                   # 长期记忆（可选）
├── SKILL.md                    # 技能清单（可选）
├── GROWTH_PLAN.md             # 成长计划（可选）
├── reports/                    # 报告目录（所有报告放这里）
│   ├── YYYY-MM-DD_报告名称.md
│   └── 其他报告...
├── skills/                     # 技能实现（代码放这里）
│   └── *.py
├── scripts/                    # 脚本工具
│   └── *.py
└── data/                       # 生成的数据（可选）
    └── *.csv
```

### 1.3 禁止存放的位置

❌ **错误示例**：
- `workspace-{agent}/报告.md` ← 临时工作区，会被清理
- `workspace/reports/` ← 全局报告目录，除非是多Agent联合报告
- `workspace/随机目录/` ← 混乱

✅ **正确示例**：
- `workspace/subagents/quant-munger/reports/2026-03-06_量化分析报告.md`
- `workspace/subagents/product-engineer/skills/data_fetcher.py`

---

## 2. 报告命名规范

### 2.1 标准格式

```
{日期}_{主题}_{类型}.md
```

**示例**：
- `2026-03-06_事件驱动策略_量化分析.md`
- `2026-03-05_贝叶斯推断_学习计划.md`
- `2026-02-28_股票策略_风险评估.md`

### 2.2 类型后缀

| 类型 | 后缀 | 示例 |
|------|------|------|
| 分析报告 | `_分析.md` | `2026-03-06_事件驱动_分析.md` |
| 评估报告 | `_评估.md` | `2026-03-06_风险评估_评估.md` |
| 学习计划 | `_学习.md` | `2026-03-06_贝叶斯推断_学习.md` |
| 技术方案 | `_方案.md` | `2026-03-06_技术实现_方案.md` |
| 反思报告 | `_反思.md` | `2026-03-06_策略反思_反思.md` |

---
## 3. 实时同步要求

### 3.1 什么时候同步

**必须立即同步**（任务完成后5分钟内）：
1. 生成报告文件时
2. 更新LEARNING.md时
3. 生成数据文件时

**不需要同步**（OpenClaw自动生成）：
- AGENT.md（已存在）
- SOUL.md（已删除）
- 模板文件（不归档）

### 3.2 同步方法

**方法1：使用同步脚本（推荐）**

```python
# 在子Agent代码中，生成报告后立即调用
import sys
sys.path.insert(0, '/Users/linweihao/.openclaw/workspace/scripts')
from sync_agent_report import sync_report

# 生成报告后（仅同步报告，不同步LEARNING.md）
report_path = "/path/to/report.md"
result = sync_report("quant-munger", report_path)
print(result["message"])
```

**方法2：手动复制**

```bash
# 报告文件
cp report.md /Users/linweihao/.openclaw/workspace/subagents/{agent}/reports/

# ⚠️ LEARNING.md 禁止直接覆盖！
# 如需更新，请手动编辑或使用git合并
```

### 3.2.1 LEARNING.md 特殊处理规则

**🚨 重要：LEARNING.md 禁止直接覆盖！**

原因：LEARNING.md包含历史学习记录，直接覆盖会导致数据丢失。

**正确做法**：
1. **子Agent只写入 `workspace-{agent}/LEARNING.md`**（临时工作区）
2. **MuskOrchestrator定期合并**到 `workspace/subagents/{agent}/LEARNING.md`
3. **禁止自动同步脚本覆盖LEARNING.md**

**更新LEARNING.md的方法**：
```bash
# 方法1：手动编辑（推荐）
vim workspace/subagents/{agent}/LEARNING.md

# 方法2：使用Git合并（如果有冲突）
cd workspace/subagents/{agent}
git checkout LEARNING.md  # 恢复版本
git merge  # 合并更新

# 方法3：追加模式（子Agent生成新内容后）
cat workspace-{agent}/LEARNING.md.new >> workspace/subagents/{agent}/LEARNING.md
```

### 3.3 同步检查清单

子Agent完成任务后必须执行：

- [ ] 报告文件已复制到 `subagents/{agent}/reports/`
- [ ] LEARNING.md已复制到 `subagents/{agent}/`
- [ ] 文件名符合规范（日期+主题+类型）
- [ ] 文件内容完整，无损坏
- [ ] 向MuskOrchestrator确认同步完成

---

## 4. 常见错误与纠正

### 4.1 错误1：报告留在workspace-{agent}/

**错误**：
```
workspace-quant-munger/
└── 量化分析报告.md  ← 错误！这里只是临时工作区
```

**纠正**：
```bash
# 立即移动到正确位置
mv workspace-quant-munger/量化分析报告.md \
   workspace/subagents/quant-munger/reports/2026-03-06_量化分析.md
```

### 4.2 错误2：LEARNING.md不同步

**错误**：
- 子Agent更新了 `workspace-quant-munger/LEARNING.md`
- 但没有同步到 `workspace/subagents/quant-munger/LEARNING.md`
- 导致主workspace看到的是旧版本

**纠正**：
```bash
# 强制同步
python /Users/linweihao/.openclaw/workspace/scripts/sync_agent_report.py quant-munger
```

### 4.3 错误3：命名不规范

**错误**：
- `report.md` ← 无日期，无主题
- `量化分析报告.md` ← 无日期
- `2026-03-06-report-final-v2.md` ← 混乱命名

**纠正**：
- `2026-03-06_事件驱动策略_量化分析.md`

---

## 5. MuskOrchestrator职责

### 5.1 任务分配时

必须在任务描述中明确：
```
任务：XXX分析报告

输出要求：
1. 报告保存到：workspace/subagents/{agent}/reports/
2. 文件名格式：YYYY-MM-DD_XXX_分析.md
3. 完成后立即调用同步脚本
4. 确认同步完成后再汇报
```

### 5.2 任务完成后

必须检查：
- [ ] 报告是否在正确位置
- [ ] 文件名是否符合规范
- [ ] LEARNING.md是否已同步
- [ ] 如果不符合，立即要求重新存放

### 5.3 定期审计

每周检查一次：
```bash
# 检查是否有文件散落在workspace-xx/
find /Users/linweihao/.openclaw -name "workspace-*" -type d -exec ls -la {}/reports/ \;

# 检查reports目录规范性
ls /Users/linweihao/.openclaw/workspace/subagents/*/reports/
```

---

## 6. 自动化保障

### 6.1 每日自动归档

每天23:00运行归档脚本，自动修正错误：
```bash
python /Users/linweihao/.openclaw/workspace/scripts/archive_agent_outputs.py
```

### 6.2 实时同步触发

子Agent可以在代码中调用：
```python
# 在任务最后添加
import subprocess
subprocess.run([
    "python", 
    "/Users/linweihao/.openclaw/workspace/scripts/sync_agent_report.py",
    "quant-munger"
])
```

---

## 7. 惩罚机制

**如果再次放错位置**：
1. 第一次：警告，立即纠正
2. 第二次：要求重新执行整个任务
3. 第三次：禁止该Agent独立生成文件，必须由MuskOrchestrator审核

---

## 8. 快速参考

### 8.1 正确路径速查表

| 文件类型 | 正确路径 |
|---------|---------|
| 报告 | `workspace/subagents/{agent}/reports/YYYY-MM-DD_主题_类型.md` |
| LEARNING.md | `workspace/subagents/{agent}/LEARNING.md` |
| 技能代码 | `workspace/subagents/{agent}/skills/*.py` |
| 脚本工具 | `workspace/subagents/{agent}/scripts/*.py` |
| 数据文件 | `workspace/subagents/{agent}/data/*.csv` |

### 8.2 一键同步命令

```bash
# 同步特定Agent
python workspace/scripts/sync_agent_report.py quant-munger

# 同步所有Agent
python workspace/scripts/sync_agent_report.py
```

---

**生效日期**：2026-03-06  
**版本**：v1.0  
**必须遵守**：是

---

*此规范由MuskOrchestrator制定，所有Agent必须严格执行*
