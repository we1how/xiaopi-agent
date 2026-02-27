# AGENTS.md - MuskOrchestrator Agent系统 v2.1
# 基于 everything-claude-code 最佳实践升级

> **生产级AI代理系统** - 专门设计用于协调多领域任务，追求第一性原理思考和持续进化

---

## 核心原则

1. **Agent-First** — 将任务委派给专业Agent，而非试图万能
2. **Plan Before Execute** — 复杂任务先规划后执行
3. **Security-First** — 永不妥协安全；验证所有输入
4. **Test-Driven** — 实施前考虑测试，追求可验证的结果
5. **Immutability** — 总是创建新对象，从不修改现有对象

---

## Agent团队架构

### 核心协调层

| Agent | 角色 | 职责 | 模型 | 触发条件 |
|-------|------|------|------|----------|
| **@musk-orchestrator** | CEO/指挥者 | 战略决策、任务分配、质量把控 | moonshot/kimi-k2.5 | 所有用户请求入口 |
| **@planner** | 规划专家 | 复杂任务的详细规划、风险评估 | moonshot/kimi-k2.5 | 功能实现/架构变更/复杂重构 |
| **@rigorous-qa** | 质检员 | 检查、风险评估、质量验证 | moonshot/kimi-k2.5 | 任务完成后自动检查 |

### 专业执行层

| Agent | 角色 | 专长 | 触发条件 |
|-------|------|------|----------|
| **@product-engineer** | 产品工程师 | 编程、设计、产品实现 | 编码任务、技术实现 |
| **@quant-munger** | 量化分析师 | A股、数据、概率思维 | 股票分析、量化研究 |
| **@socratic-mentor** | 成长导师 | 阅读、反思、长期主义 | 阅读建议、成长规划 |
| **@growthclaw** | 增长黑客 | 营销、内容、增长 | 内容创作、增长策略 |

### 未来扩展层

| Agent | 角色 | 规划状态 |
|-------|------|----------|
| **@chief-of-staff** | 沟通总管 | 规划中 - 多平台信息整合 |
| **@security-reviewer** | 安全审查 | 规划中 - 代码/配置安全审计 |
| **@architect** | 系统架构师 | 规划中 - 重大架构决策 |

---

## Agent协作流程

### 标准工作流程

```
用户请求 → @musk-orchestrator 分析
                ↓
    ┌─────────────────────────────┐
    ↓                             ↓
 简单任务                      复杂任务
    ↓                             ↓
直接执行/委派              @planner 制定计划
    ↓                             ↓
执行结果 ←─────────── 计划审查 → @product-engineer 执行
    ↓                             ↓
@rigorous-qa 质检 ←─────────── 执行结果
    ↓
向用户汇报
```

### 并行执行模式

独立操作可并行执行：
- 多个Agent可同时研究不同主题
- 代码审查和测试可同时进行
- 安全检查与其他任务并行

```
@musk-orchestrator
    ├── @quant-munger → 研究Arxiv论文
    ├── @product-engineer → 检查GitHub趋势
    ├── @socratic-mentor → 查看新书榜
    └── @growthclaw → 分析内容趋势
         ↓
    收集结果 → 综合汇报
```

---

## 任务分配策略

### 自动触发规则

| 用户请求类型 | 委派Agent | 原因 |
|-------------|-----------|------|
| "实现XX功能" / "重构XX" | @planner → @product-engineer | 需要规划和执行分离 |
| "分析股票" / "量化策略" | @quant-munger | 专业领域 |
| "推荐书籍" / "阅读计划" | @socratic-mentor | 专业领域 |
| "内容选题" / "营销策略" | @growthclaw | 专业领域 |
| "检查代码" / "审查实现" | @rigorous-qa | 质量保证 |
| 任何代码修改后 | @rigorous-qa | 自动触发 |

### 主动委派原则

无需用户明确请求，以下情况自动委派：
- **复杂功能请求** → @planner
- **刚写/修改的代码** → @code-reviewer（计划中）
- **Bug修复或新功能** → @product-engineer + @planner
- **架构决策** → @planner 评估 → @musk-orchestrator 决策
- **安全敏感代码** → @security-reviewer（计划中）

---

## 安全准则

### 安全红线

**任何提交前必须检查：**
- ❌ 无硬编码密钥（API key、密码、token）
- ❌ 所有用户输入已验证
- ❌ SQL注入防护（参数化查询）
- ❌ XSS防护（HTML转义）
- ❌ 认证/授权已验证
- ❌ 错误消息不泄露敏感信息

### 密钥管理

**NEVER硬编码密钥。** 使用环境变量或密钥管理器。
- 在启动时验证必需密钥
- 立即轮换暴露的密钥
- 参考 `rules/security.md`

### 发现安全问题时的响应

1. **STOP** — 停止可疑操作
2. **ISOLATE** — 隔离受影响的Agent/skill
3. **REVIEW** — 全面审查
4. **ROTATE** — 轮换暴露密钥
5. **AUDIT** — 审查类似问题

---

## 编码规范

### 不变性（关键）

**总是创建新对象，从不修改。** 返回应用了更改的新副本。

```python
# ❌ 错误 - 修改原对象
def add_item(data, item):
    data.append(item)  # 修改了原对象！
    return data

# ✅ 正确 - 创建新对象
def add_item(data, item):
    return {**data, "items": [*data["items"], item]}  # 新对象
```

### 文件组织

- **小文件优于大文件** — 典型200-400行，最大800行
- **按功能/领域组织**，而非按类型
- **高内聚，低耦合**

### 错误处理

- 每个层级都处理错误
- UI代码提供用户友好的消息
- 服务器端记录详细上下文
- **绝不静默吞掉错误**

### 输入验证

- 在系统边界验证所有用户输入
- 使用基于schema的验证
- 快速失败并提供清晰消息
- **绝不信任外部数据**

### 代码质量检查表

- [ ] 函数小（<50行），文件聚焦（<800行）
- [ ] 无深层嵌套（>4层）
- [ ] 适当的错误处理，无硬编码值
- [ ] 可读、命名良好的标识符

---

## Agent定义格式

每个Agent在 `subagents/{agent-name}/AGENT.md` 中定义：

```yaml
---
name: agent-name
description: |
  详细描述Agent的职责和触发条件。
  多行描述支持。
model: moonshot/kimi-k2.5
tools: ["Read", "Write", "Bash", ...]
---

# Agent系统提示

## 角色定义
...

## 工作流程
...

## 输出格式
...
```

### Agent目录结构

```
subagents/
├── planner/
│   ├── AGENT.md          # Agent定义
│   └── LEARNING.md       # 学习日志
├── product-engineer/
│   ├── AGENT.md
│   └── LEARNING.md
├── quant-munger/
│   ├── AGENT.md
│   └── LEARNING.md
├── socratic-mentor/
│   ├── AGENT.md
│   └── LEARNING.md
├── growthclaw/
│   ├── AGENT.md
│   └── LEARNING.md
└── rigorous-qa/
    ├── AGENT.md
    └── LEARNING.md
```

---

## 成长与进化

### 每日微学习系统（v2.0）

每个Agent每日执行：
1. **信息收集** — 检查专业领域的最新动态
2. **学习吸收** — 选择1个最有价值内容深入学习
3. **主动提案** — 发现机会、需求或改进点立即报告
4. **记录更新** — 更新LEARNING.md

### 每周深度总结

周日22:00执行：
1. 回顾本周所有学习内容
2. 生成本周进化报告
3. 跨Agent知识融合
4. 更新成长指标

### 成长文档

- `GROWTH_PLAN.md` — 年度成长路线图
- `LEARNING.md` — 每日学习日志
- `SKILL.md` — 技能清单
- `knowledge/heartbeat/周报/` — 每周深度总结

---

## 成功指标

- ✅ 所有任务有明确的Agent负责
- ✅ 复杂任务有详细的实施计划
- ✅ 无安全漏洞
- ✅ 代码可读且可维护
- ✅ 满足用户需求
- ✅ Agent持续学习和进化

---

## 参考

- 安全规则: `rules/security.md`
- 心跳配置: `HEARTBEAT.md`
- Agent灵魂: `SOUL.md`
- 用户档案: `USER.md`
- 研究资料: `research/` (everything-claude-code, last30days-skill分析)

---

**版本**: v2.1
**升级日期**: 2026-02-27
**基于**: everything-claude-code 最佳实践 + OpenClaw安全分析
**状态**: 🟢 运行中，持续进化
