# 多智能体 LLM 交易系统 - 论文研读笔记

> 论文：Toward Expert Investment Teams: A Multi-Agent LLM System with Fine-Grained Trading Tasks
> 阅读者：老板
> 日期：2026-02-28

---

## 核心洞察

### 1. 细粒度任务设计 > 粗粒度角色定义

**论文发现**：
- 抽象指令（如"分析财务状况"）导致 LLM 推理中断
- 细粒度任务（如"计算归一化 MACD"）确保信号有效传递

**对我们的启发**：
Quant-Munger 应该从"分析师/经理"角色转向具体任务链设计：
```
❌ 粗粒度："分析这只股票"
✅ 细粒度：
   1. 计算 5d/10d/20d/30d RoC
   2. 计算 Bollinger Z-score
   3. 计算归一化 MACD
   4. 综合评分输出
```

### 2. 三级层级架构

```
Level 1: 分析师层 (Technical/Quant/Qualitative/News)
    ↓
Level 2: 调整层 (Sector + Macro)
    ↓
Level 3: 决策层 (Portfolio Manager)
```

**应用到 Stock Platform**：
- 当前：单一策略回测
- 升级：多 Agent 协作决策

### 3. 关键技术指标

| 指标 | 计算方法 | 用途 |
|------|----------|------|
| 归一化 MACD | (EMA₁₂ - EMA₂₆) / Pₜ | 跨标的可比性 |
| Bollinger Z-score | (Pₜ - μ₂₀) / σ₂₀ | 波动率评估 |
| KDJ | J = 3D - 2K | 超买超卖 |

### 4. 工程实践要点

- **Temperature = 1**：利用多样性，通过中位数聚合稳定输出
- **50次试验取中位数**：缓解随机性
- **数据隔离**：严格防止 lookahead bias
- **成本扣除**：单边 10bps 交易成本

---

## 行动计划

### 短期（本周）
- [ ] 实现归一化 MACD 计算
- [ ] 添加 Bollinger Z-score 指标
- [ ] 设计细粒度任务模板

### 中期（本月）
- [ ] 重构 Quant-Munger 为三级架构
- [ ] 实现多 Agent 评分聚合
- [ ] 回测验证细粒度 vs 粗粒度效果

### 长期（本季度）
- [ ] 完整多 Agent 交易系统
- [ ] 实时数据接入
- [ ] 模拟交易验证

---

## 与当前系统的关联

**Stock Platform 现有能力**：
- ✅ 基础技术指标（MACD, RSI, KDJ）
- ✅ 基本面数据（ROE, PER, 财务比率）
- ✅ 回测框架

**需要增强**：
- ⏳ 归一化处理（确保跨标的可比性）
- ⏳ 多 Agent 架构
- ⏳ 细粒度任务分解
- ⏳ 中位数聚合机制

**优先级**：P1（立即实施归一化指标）

---

_第一性原理：细粒度任务设计是信号有效传递的关键_
