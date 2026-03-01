# 股票策略平台 - 架构演进方案

> 将多智能体LLM交易系统的核心思想应用到现有项目
> 目标：渐进式改造，而非推倒重来

---

## 当前架构分析

```
┌─────────────────────────────────────────┐
│           Streamlit UI (app.py)          │
├─────────────────────────────────────────┤
│  用户选择策略 → 传入参数 → 运行回测      │
├─────────────────────────────────────────┤
│      BacktestEngine (backtest_engine.py) │
│         ↓                               │
│    策略类 (如 SmaCross)                  │
│         ↓                               │
│    内部计算指标 + 交易决策 (一体式)       │
└─────────────────────────────────────────┘
```

**问题**：策略类同时负责"指标计算"和"交易决策"，耦合度高，难以引入LLM增强

---

## 演进方案：三层架构

### 目标架构

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                         │
├─────────────────────────────────────────────────────────┤
│  Level 3: 决策层 (DecisionEngine)                        │
│  - 整合多维度信号                                        │
│  - 仓位管理 + 最终决策                                    │
│  - 可接入LLM做逻辑推理                                    │
├─────────────────────────────────────────────────────────┤
│  Level 2: 校准层 (SignalCalibrator)                      │
│  - 行业对标                                             │
│  - 宏观环境调整                                         │
│  - 信号标准化 (Z-score/RoC)                              │
├─────────────────────────────────────────────────────────┤
│  Level 1: 信号层 (SignalExtractor)                       │
│  - 技术指标计算 (Technical)                              │
│  - 量价分析 (Volume/Price)                               │
│  - 趋势识别 (Trend)                                      │
│  → 输出标准化信号字典                                    │
├─────────────────────────────────────────────────────────┤
│              Data Layer (data_loader.py)                 │
│              原始OHLCV数据                               │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: 细粒度改造（立即可做）

### 1.1 创建信号提取模块

```python
# signals/extractor.py - 新增文件
import pandas as pd
import numpy as np
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class TechnicalSignals:
    """技术指标信号（标准化输出）"""
    # 动量类 (Rate of Change, 已归一化)
    roc_5d: float      # 5日变动率
    roc_10d: float
    roc_20d: float

    # 波动类 (Z-score)
    bollinger_z: float    # 布林带Z-score
    volatility_20d: float # 20日波动率

    # 趋势类 (归一化)
    macd_normalized: float    # MACD/收盘价
    rsi: float                # 0-100

    # 量价类
    volume_z: float           # 成交量Z-score
    obv_trend: float          # OBV趋势方向

    # 综合评分
    trend_strength: float     # 0-1, 趋势强度

class SignalExtractor:
    """Level 1: 信号提取层"""

    def extract(self, data: pd.DataFrame) -> TechnicalSignals:
        """
        从原始数据提取标准化技术指标

        原则：
        1. 所有指标必须归一化（消除价格偏见）
        2. 使用Z-score/RoC实现跨标的可比性
        3. 禁止返回原始价格数据
        """
        close = data['Close']
        volume = data['Volume']
        current_price = close.iloc[-1]

        # 动量指标 (RoC = 变化率，天然归一化)
        roc_5d = (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] if len(close) >= 6 else 0
        roc_10d = (close.iloc[-1] - close.iloc[-11]) / close.iloc[-11] if len(close) >= 11 else 0
        roc_20d = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21] if len(close) >= 21 else 0

        # 布林带Z-score (标准化位置)
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        bollinger_z = (close.iloc[-1] - sma_20.iloc[-1]) / std_20.iloc[-1] if std_20.iloc[-1] != 0 else 0

        # 波动率 (标准化)
        volatility_20d = std_20.iloc[-1] / current_price if current_price != 0 else 0

        # MACD归一化 (除以价格消除量级差异)
        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd = (exp1.iloc[-1] - exp2.iloc[-1]) / current_price

        # RSI (0-100，天然标准化)
        rsi = self._calculate_rsi(close, 14)

        # 成交量Z-score
        vol_sma = volume.rolling(20).mean()
        vol_std = volume.rolling(20).std()
        volume_z = (volume.iloc[-1] - vol_sma.iloc[-1]) / vol_std.iloc[-1] if vol_std.iloc[-1] != 0 else 0

        # OBV趋势
        obv_trend = self._calculate_obv_trend(data)

        # 趋势强度 (ADX简化版)
        trend_strength = self._calculate_trend_strength(close)

        return TechnicalSignals(
            roc_5d=round(roc_5d, 4),
            roc_10d=round(roc_10d, 4),
            roc_20d=round(roc_20d, 4),
            bollinger_z=round(bollinger_z, 4),
            volatility_20d=round(volatility_20d, 4),
            macd_normalized=round(macd, 6),
            rsi=round(rsi, 2),
            volume_z=round(volume_z, 4),
            obv_trend=round(obv_trend, 4),
            trend_strength=round(trend_strength, 4)
        )

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

    def _calculate_obv_trend(self, data: pd.DataFrame) -> float:
        """计算OBV趋势方向 (-1 到 1)"""
        close = data['Close']
        volume = data['Volume']
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])

        # 计算最近10日OBV趋势
        if len(obv) >= 10:
            obv_series = pd.Series(obv[-10:])
            slope = np.polyfit(range(10), obv_series, 1)[0]
            # 归一化到 -1 到 1
            max_slope = obv_series.mean() * 0.1  # 启发式归一化
            return max(-1, min(1, slope / max_slope)) if max_slope != 0 else 0
        return 0

    def _calculate_trend_strength(self, close: pd.Series) -> float:
        """计算趋势强度 (0-1)"""
        if len(close) < 20:
            return 0.5

        # 使用DMI/ADX简化版
        high = close.rolling(2).max()
        low = close.rolling(2).min()

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)

        atr = tr.rolling(14).mean()
        plus_di = 100 * plus_dm.rolling(14).mean() / atr
        minus_di = 100 * minus_dm.rolling(14).mean() / atr

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        adx = dx.rolling(14).mean()

        # ADX 0-100 映射到 0-1
        return min(1, adx.iloc[-1] / 100) if not pd.isna(adx.iloc[-1]) else 0.5
```

### 1.2 改造现有策略使用信号层

```python
# strategies/sma_cross.py - 改造示例

from backtesting import Strategy
from backtesting.lib import crossover
from dataclasses import asdict
import sys
sys.path.append('..')
from signals.extractor import SignalExtractor  # 新增依赖

class SmaCrossV2(Strategy):
    """
    细粒度版本的双均线策略

    改造点：
    1. 指标计算分离到 SignalExtractor
    2. 策略只负责基于信号的决策
    3. 可输出决策理由（语义一致性）
    """

    n_short = 10
    n_long = 20

    def init(self):
        # 初始化信号提取器
        self.extractor = SignalExtractor()

        # 为可视化保留原始指标
        close = pd.Series(self.data.Close)
        self.sma_short = self.I(
            lambda: close.rolling(self.n_short).mean(),
            name=f'SMA({self.n_short})'
        )
        self.sma_long = self.I(
            lambda: close.rolling(self.n_long).mean(),
            name=f'SMA({self.n_long})'
        )

        # 存储信号历史（用于分析）
        self.signal_history = []

    def next(self):
        # Level 1: 提取标准化信号
        data_slice = pd.DataFrame({
            'Open': self.data.Open,
            'High': self.data.High,
            'Low': self.data.Low,
            'Close': self.data.Close,
            'Volume': self.data.Volume
        })

        signals = self.extractor.extract(data_slice)

        # Level 2: 信号校准（简化版）
        # 基于趋势强度调整信号权重
        calibrated = self._calibrate(signals)

        # Level 3: 决策
        decision = self._make_decision(calibrated)

        # 执行交易
        if decision['action'] == 'buy' and not self.position:
            self.buy()
            self._log_decision(decision, signals)
        elif decision['action'] == 'sell' and self.position:
            self.sell()
            self._log_decision(decision, signals)

    def _calibrate(self, signals: TechnicalSignals) -> Dict:
        """Level 2: 信号校准"""
        # 基于趋势强度调整置信度
        confidence = signals.trend_strength

        # 动量信号校准
        mom_score = (signals.roc_5d + signals.roc_10d * 0.5 + signals.roc_20d * 0.25)

        # 波动率调整（高波动降低置信度）
        vol_adjustment = 1 - min(1, signals.volatility_20d * 10)

        return {
            'momentum': mom_score,
            'confidence': confidence * vol_adjustment,
            'bb_position': signals.bollinger_z,  # -3 到 3
            'macd_signal': signals.macd_normalized,
            'rsi': signals.rsi
        }

    def _make_decision(self, calibrated: Dict) -> Dict:
        """Level 3: 决策"""
        # 均线交叉判断（保留原始逻辑）
        if crossover(self.sma_short, self.sma_long):
            # 附加条件：趋势确认
            if calibrated['confidence'] > 0.3 and calibrated['rsi'] < 70:
                return {
                    'action': 'buy',
                    'reason': f"金叉+趋势确认(置信度{calibrated['confidence']:.2f})+RSI未超买"
                }

        elif crossover(self.sma_long, self.sma_short):
            if calibrated['confidence'] > 0.3 or calibrated['rsi'] > 70:
                return {
                    'action': 'sell',
                    'reason': f"死叉+趋势确认或RSI超买({calibrated['rsi']:.1f})"
                }

        return {'action': 'hold', 'reason': '无明确信号'}

    def _log_decision(self, decision: Dict, signals: TechnicalSignals):
        """记录决策日志（语义一致性）"""
        self.signal_history.append({
            'date': self.data.index[-1],
            'action': decision['action'],
            'reason': decision['reason'],
            'signals': asdict(signals)
        })
```

---

## Phase 2: 添加LLM推理能力（可选增强）

### 2.1 创建LLM决策模块

```python
# llm/trading_analyst.py - 新增文件

from typing import Dict, Any
import json

class LLMTradingAnalyst:
    """
    LLM交易分析师

    职责：
    1. 基于预计算信号做逻辑推理
    2. 生成可解释的交易理由
    3. 不做计算，只做判断
    """

    def __init__(self, model: str = "claude-3.5-haiku"):
        self.model = model
        # 这里接入实际的LLM API

    def analyze(self, signals: Dict, context: Dict) -> Dict[str, Any]:
        """
        基于信号做交易分析

        Args:
            signals: 预计算的技术指标
            context: 上下文（持仓状态、市场环境等）

        Returns:
            {
                'recommendation': 'buy'|'sell'|'hold',
                'confidence': 0.0-1.0,
                'reasoning': '详细的分析理由',
                'risk_factors': ['风险1', '风险2']
            }
        """

        # 构造细粒度提示词
        prompt = self._build_prompt(signals, context)

        # 调用LLM（伪代码）
        # response = call_llm(prompt, temperature=0.3)  # 低温度保证一致性

        # 示例返回结构
        return {
            'recommendation': 'hold',
            'confidence': 0.6,
            'reasoning': self._simulate_reasoning(signals),
            'risk_factors': ['波动率偏高', '成交量萎缩']
        }

    def _build_prompt(self, signals: Dict, context: Dict) -> str:
        """构建细粒度提示词"""

        return f"""你是一位技术分析专家。请基于以下预计算的指标做出交易决策。

## 输入数据（已标准化）

### 动量指标 (Rate of Change)
- 5日变动率: {signals.get('roc_5d', 0):.2%}
- 10日变动率: {signals.get('roc_10d', 0):.2%}
- 20日变动率: {signals.get('roc_20d', 0):.2%}

### 位置指标 (Z-score)
- 布林带Z-score: {signals.get('bollinger_z', 0):.2f}
  - 解释: <-2为超卖, >2为超买, 当前{'超卖' if signals.get('bollinger_z', 0) < -2 else '超买' if signals.get('bollinger_z', 0) > 2 else '中性'}

### 趋势指标
- 趋势强度: {signals.get('trend_strength', 0):.2f} (0-1)
- MACD(归一化): {signals.get('macd_normalized', 0):.4f}
- RSI: {signals.get('rsi', 50):.1f}

### 量价指标
- 成交量Z-score: {signals.get('volume_z', 0):.2f}
- OBV趋势: {signals.get('obv_trend', 0):.2f} (-1到1)

### 波动率
- 20日波动率: {signals.get('volatility_20d', 0):.2%}

## 当前状态
- 持仓状态: {'持有' if context.get('has_position') else '空仓'}
- 持仓盈亏: {context.get('position_pnl', 0):.2%}

## 要求

1. 基于上述指标，给出交易建议: buy / sell / hold
2. 说明置信度 (0-1)
3. 用中文给出详细的分析理由，必须引用具体指标数值
4. 列出主要风险因素

## 输出格式 (JSON)
{{
    "recommendation": "buy|sell|hold",
    "confidence": 0.8,
    "reasoning": "详细分析...",
    "risk_factors": ["风险1", "风险2"]
}}
"""

    def _simulate_reasoning(self, signals: Dict) -> str:
        """模拟推理过程（实际应调用LLM）"""
        parts = []

        # 动量分析
        if signals.get('roc_5d', 0) > 0.02:
            parts.append(f"5日涨幅{signals['roc_5d']:.1%}显示短期动能向上")
        elif signals.get('roc_5d', 0) < -0.02:
            parts.append(f"5日跌幅{signals['roc_5d']:.1%}显示短期动能向下")

        # RSI分析
        rsi = signals.get('rsi', 50)
        if rsi > 70:
            parts.append(f"RSI{rsi:.1f}处于超买区间")
        elif rsi < 30:
            parts.append(f"RSI{rsi:.1f}处于超卖区间")

        # 布林带
        bb = signals.get('bollinger_z', 0)
        if abs(bb) > 2:
            parts.append(f"布林带Z-score{bb:.2f}显示价格处于极端位置")

        return "；".join(parts) if parts else "指标显示中性，建议观望"
```

---

## Phase 3: 回测引擎改造

```python
# backtest_engine.py - 关键改造点

class BacktestEngine:
    def __init__(self, ...):
        # ... 原有代码

        # 新增：支持策略工厂模式
        self.use_signals = False  # 是否使用细粒度信号
        self.llm_analyst = None   # 可选的LLM分析师

    def run_with_signals(self, **strategy_params) -> Dict:
        """
        基于细粒度信号的回测（新接口）

        与标准run()的区别：
        1. 预计算所有指标
        2. 支持信号可视化
        3. 记录决策理由
        """
        # 1. 预计算全量信号
        signal_extractor = SignalExtractor()
        all_signals = []

        for i in range(len(self.data)):
            if i < 20:  # 跳过初始化期
                continue
            data_slice = self.data.iloc[:i+1]
            signals = signal_extractor.extract(data_slice)
            all_signals.append({
                'date': self.data.index[i],
                **asdict(signals)
            })

        self.signal_df = pd.DataFrame(all_signals)
        self.signal_df.set_index('date', inplace=True)

        # 2. 运行回测
        results = self.run(**strategy_params)

        # 3. 附加信号分析结果
        results['signal_summary'] = self._analyze_signals()

        return results

    def _analyze_signals(self) -> Dict:
        """分析回测期间的信号统计"""
        if self.signal_df is None:
            return {}

        return {
            'avg_trend_strength': self.signal_df['trend_strength'].mean(),
            'avg_volatility': self.signal_df['volatility_20d'].mean(),
            'rsi_distribution': {
                'oversold': (self.signal_df['rsi'] < 30).sum(),
                'overbought': (self.signal_df['rsi'] > 70).sum(),
                'neutral': ((self.signal_df['rsi'] >= 30) & (self.signal_df['rsi'] <= 70)).sum()
            }
        }
```

---

## 实施路线图

### 阶段1：基础建设（1-2天）
- [ ] 创建 `signals/` 目录
- [ ] 实现 `SignalExtractor` 基础版本
- [ ] 添加单元测试验证指标计算正确性

### 阶段2：策略改造（2-3天）
- [ ] 改造 `SmaCross` → `SmaCrossV2`（细粒度版本）
- [ ] 添加 `strategy_v2.py` 作为新策略基类
- [ ] 对比回测：原策略 vs 细粒度策略

### 阶段3：可视化增强（1天）
- [ ] 在Streamlit中添加信号面板
- [ ] 显示实时指标值和Z-score
- [ ] 添加决策理由展示

### 阶段4：LLM集成（可选，2-3天）
- [ ] 实现 `LLMTradingAnalyst` 骨架
- [ ] 添加OpenRouter/Anthropic API接入
- [ ] 实现LLM辅助策略（混合决策）

---

## 关键设计决策

### 1. 为什么保留原策略？

```python
# 新旧策略并存
strategies/
├── sma_cross.py          # 原策略（向后兼容）
├── sma_cross_v2.py       # 细粒度版本
└── base.py               # 共享基类
```

- 原策略性能已知，可作为基准
- 细粒度版本需要验证有效性
- 用户可自由选择

### 2. 指标计算性能优化

```python
# 避免每次next()重复计算
class OptimizedExtractor:
    def __init__(self):
        self._cache = {}

    def extract(self, data: pd.DataFrame) -> TechnicalSignals:
        # 使用增量计算，只算最新值
        # 缓存中间结果（如SMA序列）
        pass
```

### 3. 数据隔离（防未来函数）

```python
def next(self):
    # 强制只使用历史数据
    current_idx = len(self.data.Close) - 1
    available_data = self.data.iloc[:current_idx+1]

    # 计算指标时必须使用 available_data
    signals = self.extractor.extract(available_data)
```

---

## 预期收益

| 维度 | 改进点 | 预期效果 |
|------|--------|----------|
| **可解释性** | 决策理由输出 | 用户理解策略逻辑 |
| **可调试性** | 信号分离 | 定位问题是计算还是决策 |
| **可扩展性** | 分层架构 | 容易添加新信号源 |
| **可比性** | 标准化指标 | 跨标的策略回测更公平 |
| **智能化** | LLM可选 | 渐进引入AI能力 |

---

## 不做什么（控制范围）

1. **不做多Agent** - 单Agent+细粒度输入已足够
2. **不做高频** - 保持日线级别
3. **不做自动交易** - 仅回测和分析
4. **不做模型训练** - 仅使用预训练LLM做推理

---

_渐进演进，验证有效后再深入_
