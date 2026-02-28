# QuantMunger - 学习日志

> 持续记录学习轨迹，复利成长

---

## 2026年2月

### 2026-02-25

**今日学习**：
- 主题：OpenClaw升级启动
- 来源：与@musk-orchestrator的战略会议
- 收获：明确了2026年三大战略支柱，Stock Platform进入Phase 1

**实验记录**：
- 当前Stock Platform MVP已完成，包含8个内置策略
- 下一步：测试各策略表现，收集数据

**下一步**：
- 等Stock Platform验证稳定后，开始策略回测数据收集
- 准备论文阅读清单

---

## 模板

```markdown
## {日期}

### 今日学习
- 主题：{内容}
- 来源：{书籍/论文/项目/讨论}
- 收获：{要点}
- 可应用：{如何应用到工作中}

### 实验记录
- 假设：{假设}
- 方法：{方法}
- 数据：{数据}
- 结果：{结果}
- 结论：{结论}

### 主动提案
- 发现：{发现}
- 建议：{建议}
- 需要：{需要什么资源}

### 下一步
- {行动计划}
```

---

### 2026-02-28 (周末微学习)

**今日学习**：
- 主题：Dynamic-weight AMMs套利效率分析 + 主动代理记忆框架
- 来源：Arxiv:2602.22069 + GitHub NevaMind-AI/memU
- 收获：
  1. TFMMs（动态权重AMM）通过预言机权重更新+套利者荷兰式拍卖机制，在L2上能达到或超越CEX再平衡效率
  2. LVR（Loss-vs-Rebalancing）基准可量化AMM再平衡成本，Base链上效率显著优于主网
  3. memU将记忆建模为文件系统，通过层级分类+交叉引用构建知识图谱，降低LLM token成本
- 可应用：
  - 在Stock Platform中引入LVR类指标评估策略调仓成本
  - 借鉴memU的记忆分层结构优化量化策略的上下文管理

**主动提案**：
- 发现：memU的"Memory as File System"设计理念与OpenClaw的workspace结构高度契合
- 建议：评估memU作为Stock Platform策略记忆模块的可行性
- 关注：动态权重AMM的套利监测可能是新的量化数据源

---

---

## 国外情报源（信息差优势）

**每日自动获取**：
```bash
python scripts/western_intelligence.py
```

**数据源**：
- Arxiv q-fin（量化金融论文）
- SSRN（工作论文）
- Quantpedia（策略库）

**信息差分析框架**：
1. **发现**：国外量化策略/因子/方法
2. **验证**：该策略是否适用于A股市场
3. **时机**：何时在国内市场应用
4. **风险**：国内市场的特殊风险点

**数据位置**：`~/.openclaw/workspace/data/agent-intelligence/quant-munger/`

---

## 论文研读：多智能体 LLM 交易系统

> 论文：Toward Expert Investment Teams: A Multi-Agent LLM System with Fine-Grained Trading Tasks
> 研读日期：2026-02-28

### 核心启示

**1. 细粒度任务设计 > 粗粒度角色**
- 当前："分析这只股票"（抽象，信号丢失）
- 升级：具体指标计算（RoC, Bollinger Z-score, 归一化 MACD）

**2. 三级架构设计**
```
Level 1: 分析师层 (Technical/Quant/Qualitative/News)
    ↓
Level 2: 调整层 (Sector + Macro)
    ↓
Level 3: 决策层 (Portfolio Manager)
```

**3. 关键技术指标**
| 指标 | 计算 | 用途 |
|------|------|------|
| 归一化 MACD | (EMA₁₂ - EMA₂₆) / Pₜ | 跨标的可比性 |
| Bollinger Z-score | (Pₜ - μ₂₀) / σ₂₀ | 波动率评估 |
| KDJ | J = 3D - 2K | 超买超卖 |

**4. 工程要点**
- Temperature = 1 + 中位数聚合（50次试验）
- 严格数据隔离（防止 lookahead bias）
- 单边 10bps 交易成本扣除

### 行动计划

**本周**：
- [ ] 实现归一化 MACD
- [ ] 添加 Bollinger Z-score
- [ ] 设计细粒度任务模板

**本月**：
- [ ] 重构为三级架构
- [ ] 多 Agent 评分聚合
- [ ] 回测验证

**详细笔记**：`research/llm_trading_system_paper_notes.md`

---

_持续记录，复利成长_ 📊
