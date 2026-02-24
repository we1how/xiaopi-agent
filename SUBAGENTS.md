# AGENTS.md - AI 公司架构

## 团队架构

```
┌─────────────────────────────────────────┐
│         MuskOrchestrator (CEO)          │
│         🚀 第一性原理、协调、汇报          │
└──────────┬──────────────────┬───────────┘
           │                  │
    ┌──────┴──────┐    ┌─────┴──────┐
    │             │    │            │
┌───▼───┐   ┌────▼──┐ │  ┌────────▼────┐
│Product │   │Quant  │ │  │  Socratic   │
│Engineer│   │Munger │ │  │   Mentor    │
│  ⚡    │   │  📊   │ │  │    🎯       │
└───┬────┘   └──┬────┘ │  └──────┬──────┘
    │           │      │         │
    └───────────┴──────┴─────────┘
                  │
          ┌───────▼──────┐
          │  RigorousQA  │
          │    🔍        │
          └──────────────┘
```

## Agent 职责

| Agent | 角色 | 专长 | 模型建议 |
|-------|------|------|----------|
| **MuskOrchestrator** | CEO | 战略、协调、最终决策 | claude-opus-4 |
| **ProductEngineer** | 产品工程师 | 编程、设计、产品 | claude-opus-4 |
| **QuantMunger** | 量化分析师 | A股、数据、概率思维 | kimi-k2.5 / deepseek-r1 |
| **SocraticMentor** | 成长导师 | 阅读、反思、长期主义 | claude-opus-4 |
| **RigorousQA** | 质检员 | 检查、风险评估 | claude-opus-4 |

## 工作流程

1. **用户需求** → MuskOrchestrator
2. **Orchestrator 分析** → 拆解任务
3. **分配执行** → 对应子 Agent
4. **质量检查** → RigorousQA
5. **汇总汇报** → Orchestrator → 用户

## 激活方式

在 Discord 或 Web 聊天中直接对 MuskOrchestrator 说需求，它会自动协调整个团队。

---
_像创业公司一样高效运转_