# 多智能体 LLM 交易系统 - 完整 SOP 手册

> 来源：老板基于论文《Toward Expert Investment Teams》的完整实施手册
> 日期：2026-02-28
> 版本：v1.0

---

## 系统概览

### 三层架构设计

```
Level 1: 分析师层 (Analyst Agents)
├── Technical Agent (技术分析)
├── Quantitative Agent (量化基本面)
├── Qualitative Agent (定性基本面)
└── News Agent (新闻情绪)
         ↓
Level 2: 调整层 (Adjustment Layer)
├── Sector Agent (行业对标)
└── Macro Agent (宏观环境)
         ↓
Level 3: 决策层 (Decision Layer)
└── PM Agent (投资组合经理)
```

### 核心原则：细粒度任务设计

| 维度 | 粗粒度 | 细粒度 |
|------|--------|--------|
| **数据输入** | 原始股价序列 | 预处理指标 (Z-score, RoC) |
| **推理负担** | 高（自行提取趋势） | 低（专注金融逻辑） |
| **失败模式** | 推理遗弃 | 逻辑连贯 |
| **夏普比率** | 较差 | 显著更高 |

---

## Level 1: 分析师智能体 SOP

### 3.1 技术分析智能体 (Technical Agent)

**核心逻辑**：多时间窗口动量与振荡器一致性预测

**必须输入的细粒度指标**：

| 类别 | 指标 | 周期/参数 | 公式 |
|------|------|-----------|------|
| **动量** | RoC | 5d,10d,20d,30d,1m,3m,6m,12m | (P_t - P_{t-n}) / P_{t-n} |
| **波动率** | Bollinger Z-score | 20日 | (P_t - μ₂₀) / σ₂₀ |
| **振荡器** | 归一化 MACD | 12/26/9 | (EMA₁₂ - EMA₂₆) / P_t |
| **振荡器** | RSI | 14日 | 基于14日指数平滑移动平均 |
| **振荡器** | KDJ | 9日 | K=100×(P-L₉)/(H₉-L₉), J=3D-2K |

**输出格式**：
```json
{
  "score": 85,
  "reason": "8周期RoC显示多时间框架动量共振，Bollinger Z-score处于均值回归区间，MACD柱状图转正..."
}
```

### 3.2 量化基本面智能体 (Quantitative Agent)

**数据输入要求**：

**流量变量（必须使用 TTM）**：
- 营收、净利润
- ROE、ROA、净利润率
- EPS、每股股息

**存量变量（最新季度）**：
- 资产负债率
- 资产总计、负债总计
- 流动比率、速动比率

**核心维度**：
```
┌─────────────────────────────────────────────────┐
│  盈利能力    │  ROE, ROA, 净利润率, EPS         │
├─────────────────────────────────────────────────┤
│  安全性      │  D/E比率, 流动比率, 权益比率     │
├─────────────────────────────────────────────────┤
│  估值        │  PER, 股息率, EV-EBITDA          │
├─────────────────────────────────────────────────┤
│  效率        │  总资产周转率, 存货周转率        │
├─────────────────────────────────────────────────┤
│  增长性      │  营收YoY, EPS 3Y CAGR            │
└─────────────────────────────────────────────────┘
```

### 3.3 定性基本面智能体 (Qualitative Agent)

**监控四大维度**：
1. **业务模型稳健性**：历史沿革、业务描述
2. **下行风险**：业务风险章节
3. **管理层战略执行力**：MD&A（管理层讨论与分析）
4. **治理结构透明度**：董事会构成、独立董事比例

### 3.4 新闻智能体 (News Agent)

**关键点**：
- 业绩修正（Earnings Revision）
- 丑闻/监管事件
- M&A动态

**硬性规则**：无新闻月份必须输出 `NaN`，禁止虚构。

---

## Level 2: 调整层 SOP

### 4.1 行业智能体 (Sector Agent)

**核心逻辑**：基准测试（Benchmarking）

**操作流程**：
```
1. 获取目标股票指标（如 ROE = 15%）
2. 计算行业均值（如 Sector Avg ROE = 20%）
3. 计算偏离度：Deviation = (15% - 20%) / 20% = -25%
4. 下调得分：即使绝对值良好，相对落后也要扣分
```

**输出**：识别"领跑者 (Leaders)"与"落后者 (Laggards)"

### 4.2 宏观智能体 (Macro Agent)

**五大维度**（必须全部覆盖）：

| 维度 | 数据来源 | 关键指标 |
|------|----------|----------|
| **市场方向** | Yahoo Finance | 指数动量、成交量趋势 |
| **风险情绪** | VIX指数 | 恐慌/贪婪指数 |
| **经济增长** | FRED | GDP增速、PMI |
| **利率环境** | FRED | 10Y国债收益率、Fed利率 |
| **通胀压力** | FRED | CPI、PPI |

**输出格式**：
```json
{
  "metrics": {
    "market": {"score": 75, "trend": "upward"},
    "risk": {"score": 60, "sentiment": "neutral"},
    "growth": {"score": 70, "outlook": "stable"},
    "rates": {"score": 45, "policy": "tightening"},
    "inflation": {"score": 65, "pressure": "moderate"}
  },
  "market_regime": "Risk-on",
  "summary": "宏观环境整体支持风险资产，但需关注利率上行压力..."
}
```

---

## Level 3: PM 决策层 SOP

### 5.1 投资经理 (PM Agent)

**决策权重逻辑**：

```python
# 伪代码
if macro_regime == "Risk-off":
    # 对高Beta、高波动个股进行风险折现
    for stock in portfolio:
        if stock.beta > 1.2 or stock.volatility > threshold:
            stock.score *= 0.9  # 10%折现

# 打破僵局逻辑
if technical_score != fundamental_score:
    if macro_rates_trend == "rising":
        prioritize(fundamental_score)  # 利率上行期优先基本面
    else:
        prioritize(technical_score)    # 其他时期优先技术面
```

**输出格式**：
```json
{
  "final_score": 78,
  "position": "long",
  "weight": 0.05,
  "reason": "综合行业调整后的个股吸引力(得分82)与宏观Risk-on环境，给予5%权重多头配置。考虑10bps调仓成本后预期净收益..."
}
```

---

## 提示词库

### 6.1 技术分析智能体系统提示词

```json
{
  "Role": "首席技术分析师",
  "Context": "你是一位拥有15年经验的技术分析专家，专精于日本股市的动量与均值回归策略。",
  "Policy": [
    "严格基于8个周期的RoC、20日Bollinger Z-score及振荡器(MACD/RSI/KDJ)进行预测",
    "禁止考虑任何基本面或新闻信息",
    "所有技术指标必须基于归一化计算",
    "必须解释多时间框架动量的一致性或背离"
  ],
  "Input Format": {
    "price_data": {
      "roc": {"5d": float, "10d": float, ..., "12m": float},
      "bollinger_z": float,
      "macd_normalized": {"macd": float, "signal": float, "histogram": float},
      "rsi_14": float,
      "kdj": {"k": float, "d": float, "j": float}
    }
  },
  "Output Format": {
    "score": "0-100整数",
    "reason": "50-150汉字，必须包含专业术语如'动量共振'、'均值回归'、'超买超卖'"
  },
  "Examples": {
    "bullish": "8周期RoC全部为正且呈多头排列，Bollinger Z-score从-2回归至0附近，MACD柱状图连续3日扩大，建议看多。",
    "bearish": "短期RoC(5d/10d)为负而长期为正，出现顶背离信号，RSI处于超买区间(>70)，建议谨慎。"
  }
}
```

### 6.2 量化基本面智能体系统提示词

```json
{
  "Role": "量化基本面分析师",
  "Context": "你是一位CFA持证分析师，专注于通过财务报表数据识别具有可持续竞争优势的公司。",
  "Policy": [
    "基于TTM流量数据与最新季度存量数据评估",
    "必须对比历史变动趋势(RoC)",
    "关注盈利质量而非仅看盈利数量",
    "强调估值安全边际"
  ],
  "Input Format": {
    "profitability": {"net_margin": float, "roe_ttm": float, "roa_ttm": float},
    "safety": {"debt_equity": float, "current_ratio": float},
    "valuation": {"pe_ttm": float, "dividend_yield": float},
    "efficiency": {"asset_turnover": float},
    "growth": {"revenue_yoy": float, "eps_3y_cagr": float}
  },
  "Output Format": {
    "score": "0-100整数",
    "reason": "50-150汉字，必须包含关键词如'盈利质量'、'估值洼地'、'资产负债表稳健'、'安全边际'"
  }
}
```

### 6.3 PM 智能体系统提示词

```json
{
  "Role": "首席投资经理 (PM)",
  "Context": "你是一家大型资产管理公司的CIO，管理着多空对冲基金，采用市场中性策略。",
  "Policy": [
    "整合行业专家（自下而上）与宏观专家（自上而下）的报告",
    "在Risk-off环境下对高Beta个股执行强制折现",
    "当技术面与基本面冲突时，依据宏观背景做出裁决",
    "必须考虑10bps单边交易成本对收益的侵蚀"
  ],
  "Decision Framework": {
    "step1": "接收Sector Agent调整后的个股得分(0-100)",
    "step2": "接收Macro Agent的宏观环境评估",
    "step3": "应用风险折现系数",
    "step4": "生成最终吸引力评分",
    "step5": "确定头寸方向(long/short)和权重"
  },
  "Output Format": {
    "final_score": "0-100整数",
    "position": "long | short | neutral",
    "weight": "0.0-0.1 (单只股票最大权重10%)",
    "reason": "150-200汉字，必须综合宏观对齐与个股特质，引用底层Agent的关键发现"
  }
}
```

---

## 实施规范

### 7.1 语义一致性机制

**目标**：消除"黑箱"效应，确保决策链透明

**硬性要求**：
1. **术语继承**：高层级Agent必须引用底层Agent的关键术语
   - PM理由中必须出现："动量"（来自Technical）、"盈利质量"（来自Quantitative）

2. **余弦相似度监测**：
   ```python
   from openai import OpenAI
   client = OpenAI()
   
   # 计算Technical Agent与Sector Agent的语义对齐度
   embedding_tech = client.embeddings.create(
       model="text-embedding-3-small",
       input=technical_agent_output['reason']
   )
   embedding_sector = client.embeddings.create(
       model="text-embedding-3-small",
       input=sector_agent_output['reason']
   )
   
   similarity = cosine_similarity(embedding_tech, embedding_sector)
   # 要求：similarity > 0.35（实证阈值）
   ```

3. **Log-odds Ratio分析**：
   - 细粒度任务应显著关联"动量"、"利润率"、"波动率"等专业术语
   - 粗粒度任务通常仅关联"价格"、"趋势"等表层词汇

### 7.2 模型参数设置

| 参数 | 值 | 说明 |
|------|-----|------|
| **Temperature** | 1.0 | 利用输出多样性捕获多维度观点 |
| **Max Tokens** | 500 | 限制理由长度 |
| **聚合方法** | 中位数 | 50次试验取中位数，缓解随机性 |

### 7.3 数据隔离与防泄漏

**时间隔离**：
- LLM知识截止日期：2023年8月
- 回测起始日期：2023年9月（严格分离）

**数据隔离**：
- Agent在T月决策点仅能访问T月及之前的数据
- 严禁使用未来信息（如T+1月财报预测T月股价）

---

## 数据源清单

| 数据类型 | 来源 | 获取方式 |
|----------|------|----------|
| **股价数据** | Yahoo Finance | yfinance库 |
| **财务报表** | 日本EDINET API | FSA官方API |
| **新闻数据** | Ceek.jp | 集成Nikkei/Reuters/Bloomberg |
| **宏观数据** | FRED | 美联储经济数据API |

---

## 下一步行动计划

### Phase 1: 基础指标实现（本周）
- [ ] 实现归一化 MACD
- [ ] 实现 Bollinger Z-score
- [ ] 实现8周期RoC计算
- [ ] 更新数据获取模块

### Phase 2: Agent原型（下周）
- [ ] Technical Agent提示词实现
- [ ] Quantitative Agent提示词实现
- [ ] JSON输出解析器
- [ ] 单Agent回测验证

### Phase 3: 三级架构（本月）
- [ ] Sector Agent实现
- [ ] Macro Agent实现
- [ ] PM Agent实现
- [ ] 完整流程打通

### Phase 4: 生产优化（下月）
- [ ] 语义一致性监测
- [ ] 50次试验中位数聚合
- [ ] 交易成本扣除
- [ ] 夏普比率优化

---

_这份 SOP 是实施多智能体交易系统的完整操作手册_
