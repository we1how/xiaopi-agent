# 量化投资研究资料库

> 系统化记录量化投资相关的论文研读、策略研究和实践经验

---

## 论文研读

### 多智能体 LLM 交易系统

| 文件 | 内容 | 状态 |
|------|------|------|
| [key_insights_summary.md](./key_insights_summary.md) | ⭐ 关键思想提炼（学习用） | ✅ 已整理 |
| [llm_trading_system_paper_notes.md](./llm_trading_system_paper_notes.md) | 论文核心洞察与行动计划 | ✅ 已整理 |
| [multi_agent_trading_sop_v1.md](./multi_agent_trading_sop_v1.md) | 完整实施手册与SOP | ✅ 已整理 |

**论文信息**：
- **标题**: Toward Expert Investment Teams: A Multi-Agent LLM System with Fine-Grained Trading Tasks
- **来源**: arXiv:2602.23330
- **研读日期**: 2026-02-28
- **核心贡献者**: 老板（阅读+总结）
- **当前状态**: 🔍 学习阶段，暂不开发

**核心洞察**：
1. **细粒度任务设计** > 粗粒度角色定义
2. **三级分层架构**（分析师→调整层→PM）
3. **归一化指标**确保跨标的可比性
4. **语义一致性**监测消除黑箱

---

## 快速导航

### 实施路线图
```
Phase 1 (本周): 归一化指标实现
  ├── 归一化 MACD
  ├── Bollinger Z-score
  └── 8周期RoC

Phase 2 (下周): Agent原型
  ├── Technical Agent
  ├── Quantitative Agent
  └── 单Agent回测

Phase 3 (本月): 三级架构
  ├── Sector Agent
  ├── Macro Agent
  ├── PM Agent
  └── 完整流程打通

Phase 4 (下月): 生产优化
  ├── 语义一致性监测
  ├── 50次试验聚合
  └── 夏普比率优化
```

### 关键技术指标

| 指标 | 公式 | 用途 |
|------|------|------|
| **归一化 MACD** | (EMA₁₂ - EMA₂₆) / Pₜ | 跨标的可比性 |
| **Bollinger Z-score** | (Pₜ - μ₂₀) / σ₂₀ | 波动率评估 |
| **KDJ** | J = 3D - 2K | 超买超卖 |

---

## 相关链接

- **原始论文**: arXiv:2602.23330
- **研究笔记**: `research/llm_trading_system_paper_notes.md`
- **完整SOP**: `research/multi_agent_trading_sop_v1.md`
- **Agent学习日志**: `subagents/quant-munger/LEARNING.md`

---

_持续积累，复利增长_
