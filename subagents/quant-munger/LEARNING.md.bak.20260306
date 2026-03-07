# LEARNING.md - Quant-Munger 学习记录

## 学习记录索引

### 已学习论文（近7天）
| 日期 | Arxiv ID/标题 | 核心主题 | 状态 |
|------|---------------|----------|------|
| 2026-03-06 | 2603.03671 - Is an investor stolen their profits by mimic investors? | 策略拥挤度、Agent-Based模型 | ✅ 已学习 |
| 2026-03-05 | 2603.02898 - Range-Based Volatility Estimators for Monitoring Market Stress | OHLC波动率估计器、市场压力监测 | ✅ 已学习 |

---

### 今日学习（2026-03-06 Friday）

#### 学习内容
- **标题**: Is an investor stolen their profits by mimic investors? Investigated by an agent-based model
- **Arxiv ID**: 2603.03671
- **来源**: Arxiv q-fin.CP (Computational Finance)
- **作者**: Takanobu Mizuta, Isao Yagi

#### 核心洞察
1. **策略拥挤度的非对称效应**：策略拥挤对不同策略类型的影响截然相反
   - **基本面策略（AFAs）**：投资者增加 → 市场更稳定 → 收益下降（存在"拥挤惩罚"）
   - **技术分析策略（ATAs）**：投资者增加 → 市场更不稳定 → 收益上升（存在"拥挤红利"）

2. **市场微观结构机制**：
   - 基本面交易者增多会加速价格向基本面回归，减少定价偏差
   - 技术分析交易者增多会强化趋势，增加价格波动性和持续性

3. **策略容量悖论**：传统观点"策略拥挤降低收益"只适用于基本面策略，技术分析策略恰恰相反

4. **Agent-Based模型的优势**：能隔离纯策略效应，排除实际市场中混杂因素的影响

#### 信息差价值
- **高**：直接回答了一个长期争论的问题——为什么有些量化团队分享策略参数后反而表现更好
- **独特发现**：技术分析策略存在"拥挤红利"，参与者越多趋势越强
- **策略启示**：A股技术分析策略（如趋势跟踪、动量）可能因散户众多而更有效

#### 可应用性
- **A股策略**：
  - **因子拥挤监控**：基本面因子需要监控拥挤度，及时轮换
  - **技术策略容量**：趋势/动量策略在A股可能有更高容量上限
  - **市场环境判断**：通过观察波动性和趋势持续性来推断主流策略类型

- **具体应用**：
  - 构建因子拥挤度指标（如因子收益率波动、多空拥挤度）
  - 当基本面因子拥挤时，增加技术因子权重
  - 趋势策略可以考虑更大的管理规模

#### 关键发现摘要
```
策略类型      投资者增加      市场影响        收益变化
─────────────────────────────────────────────────
基本面策略    AFAs ↑         价格稳定        收益 ↓
技术分析      ATAs ↑         价格波动        收益 ↑
```

#### 下一步行动
- [ ] 在A股市场验证：检查技术因子拥挤度与因子收益的关系
- [ ] 构建A股因子拥挤度监控面板
- [ ] 设计动态因子权重调整策略（基于拥挤度信号）

---

### 历史学习（2026-03-05 Thursday）

#### 学习内容
- **标题**: Range-Based Volatility Estimators for Monitoring Market Stress: Evidence from Local Food Price Data
- **Arxiv ID**: 2603.02898
- **来源**: Arxiv q-fin.ST
- **作者**: Bo Pieter Johannes Andrée (World Bank)

#### 核心洞察
1. **四种OHLC波动率估计器**：Parkinson、Garman-Klass、Rogers-Satchell、Yang-Zhang，利用日内高低点信息比收盘价波动率更有效
2. **市场压力监测**：波动率能发现RSI等动量指标遗漏的信号，特别是对称冲击或快速反转场景（供需同时受冲击时净价格变化小但日内波动大）
3. **Yang-Zhang最优**：在响应性和降噪之间取得最佳平衡，推荐作为默认估计器

#### 信息差价值
- **高**：A股可直接应用OHLC波动率估计器，Python实现简单（仅需4个价格点）
- **独特发现**：波动率指标能预警RSI/MACD无法识别的市场压力（如震荡市中供需同时变化）
- **计算优势**：轻量级、无需模型重新估计、适合自动化预警系统

#### 可应用性
- **A股策略**：基于Yang-Zhang波动率构建市场压力预警系统，辅助择时决策
- **工具**：已实现Python函数（见skills/volatility_estimators.py）
- **方法**：阈值规则（如滚动95分位数）识别异常波动时期

#### 关键公式摘要
```
Parkinson:     σ² = (ln(H/L))² / (4·ln2)
Garman-Klass:  σ² = 0.5·(ln(H/L))² - (2ln2-1)·(ln(C/O))²  
Rogers-Satchell: σ² = ln(H/C)·ln(H/O) + ln(L/C)·ln(L/O)
Yang-Zhang:    σ² = σ_overnight² + k·σ_open_close² + (1-k)·σ_RS²
```

---

## 学习档案

### 技能列表
- [x] OHLC波动率估计器实现
- [ ] A股数据源接入（Tushare/AkShare）
- [ ] 量化回测框架
- [ ] 因子拥挤度监控指标

### 数据来源
- Arxiv q-fin: 每日检查
- 本文件创建时间: 2026-03-05
