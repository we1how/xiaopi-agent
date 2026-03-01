#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号提取器 - Level 1: 信号层

职责：
1. 从原始OHLCV数据提取标准化技术指标
2. 所有指标归一化（消除价格偏见）
3. 使用Z-score/RoC实现跨标的可比性

禁止：
- 返回原始价格数据
- 在提取层做交易决策
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TechnicalSignals:
    """
    技术指标信号（标准化输出）

    所有字段已归一化，可直接用于：
    - 跨标的比较
    - LLM输入（细粒度任务设计）
    - 量化策略决策
    """

    # ========== 动量类 (Rate of Change) ==========
    # 使用变动率而非绝对价格，天然归一化
    roc_5d: float = 0.0      # 5日变动率 (-1 ~ +1)
    roc_10d: float = 0.0     # 10日变动率
    roc_20d: float = 0.0     # 20日变动率

    # ========== 位置类 (Z-score) ==========
    # 标准化位置，0=均值，+2=上沿，-2=下沿
    bollinger_z: float = 0.0      # 布林带Z-score
    price_z: float = 0.0          # 价格Z-score（相对于20日）

    # ========== 波动类 (标准化) ==========
    volatility_20d: float = 0.0   # 20日波动率（标准差/价格）
    atr_14d: float = 0.0          # ATR(14)/价格

    # ========== 趋势类 (归一化) ==========
    macd_normalized: float = 0.0  # MACD/收盘价 (-0.1 ~ +0.1)
    macd_signal: float = 0.0      # MACD信号线/收盘价
    macd_histogram: float = 0.0   # MACD柱状图/收盘价

    rsi: float = 50.0             # RSI (0-100)
    rsi_divergence: float = 0.0   # RSI背离度（价格与RSI变化差异）

    trend_strength: float = 0.5   # 趋势强度 (0-1)
    trend_direction: int = 0      # 趋势方向: 1=上升, -1=下降, 0=震荡

    # ========== 量价类 ==========
    volume_z: float = 0.0         # 成交量Z-score
    obv_trend: float = 0.0        # OBV趋势 (-1 ~ +1)
    money_flow: float = 0.0       # 资金流向 (-1 ~ +1)

    # ========== 综合评分 ==========
    composite_score: float = 0.0  # 综合评分 (-1 ~ +1)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（便于序列化和LLM输入）"""
        return asdict(self)

    def to_prompt_format(self) -> str:
        """
        转换为LLM提示词格式

        输出细粒度的指标描述，用于论文中的"细粒度任务设计"
        """
        lines = [
            "## 技术指标（已标准化）",
            "",
            "### 动量指标 (Rate of Change)",
            f"- 5日变动率: {self.roc_5d:+.2%}",
            f"- 10日变动率: {self.roc_10d:+.2%}",
            f"- 20日变动率: {self.roc_20d:+.2%}",
            "",
            "### 位置指标 (Z-score)",
            f"- 布林带Z-score: {self.bollinger_z:+.2f} " +
            f"({'超卖' if self.bollinger_z < -2 else '超买' if self.bollinger_z > 2 else '中性'})",
            f"- 价格Z-score: {self.price_z:+.2f}",
            "",
            "### 趋势指标",
            f"- 趋势强度: {self.trend_strength:.1%}",
            f"- 趋势方向: {'上升' if self.trend_direction > 0 else '下降' if self.trend_direction < 0 else '震荡'}",
            f"- RSI: {self.rsi:.1f} " +
            f"({'超卖' if self.rsi < 30 else '超买' if self.rsi > 70 else '中性'})",
            f"- MACD(归一化): {self.macd_normalized:+.4f}",
            "",
            "### 波动率",
            f"- 20日波动率: {self.volatility_20d:.2%}",
            f"- ATR(14): {self.atr_14d:.2%}",
            "",
            "### 量价指标",
            f"- 成交量Z-score: {self.volume_z:+.2f}",
            f"- OBV趋势: {self.obv_trend:+.2f}",
            f"- 资金流向: {self.money_flow:+.2f}",
            "",
            "### 综合评分",
            f"- 综合得分: {self.composite_score:+.2f} " +
            f"({'看多' if self.composite_score > 0.3 else '看空' if self.composite_score < -0.3 else '中性'})",
        ]
        return "\n".join(lines)


class SignalExtractor:
    """
    信号提取器

    Level 1: 信号层
    职责：计算标准化技术指标，不做任何交易决策
    """

    def __init__(self):
        # 可配置的参数
        self.min_periods = 20  # 最小数据周期

    def extract(self, data: pd.DataFrame) -> TechnicalSignals:
        """
        从原始数据提取标准化技术指标

        Args:
            data: DataFrame with columns [Open, High, Low, Close, Volume]
                  Index should be datetime

        Returns:
            TechnicalSignals: 标准化信号对象

        Note:
            - 如果数据不足，返回默认值
            - 所有计算只使用历史数据（防止未来函数）
        """
        if len(data) < self.min_periods:
            return TechnicalSignals()  # 返回默认值

        # 提取序列
        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']
        open_price = data['Open']
        current_price = close.iloc[-1]

        # 防止除零
        if current_price == 0:
            return TechnicalSignals()

        signals = TechnicalSignals()

        # ========== 动量指标 ==========
        signals.roc_5d = self._calc_roc(close, 5)
        signals.roc_10d = self._calc_roc(close, 10)
        signals.roc_20d = self._calc_roc(close, 20)

        # ========== 位置指标 ==========
        signals.bollinger_z = self._calc_bollinger_z(close)
        signals.price_z = self._calc_price_z(close)

        # ========== 波动指标 ==========
        signals.volatility_20d = self._calc_volatility(close)
        signals.atr_14d = self._calc_atr_normalized(high, low, close)

        # ========== 趋势指标 ==========
        signals.macd_normalized, signals.macd_signal, signals.macd_histogram = \
            self._calc_macd_normalized(close)
        signals.rsi = self._calc_rsi(close)
        signals.rsi_divergence = self._calc_rsi_divergence(close, signals.rsi)
        signals.trend_strength, signals.trend_direction = \
            self._calc_trend_strength(close, high, low)

        # ========== 量价指标 ==========
        signals.volume_z = self._calc_volume_z(volume)
        signals.obv_trend = self._calc_obv_trend(close, volume)
        signals.money_flow = self._calc_money_flow(close, high, low, volume)

        # ========== 综合评分 ==========
        signals.composite_score = self._calc_composite_score(signals)

        return signals

    def extract_series(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        提取时间序列信号（用于回测期间全程记录）

        Args:
            data: 完整历史数据

        Returns:
            DataFrame: 每个时间点的信号值
        """
        signals_list = []

        for i in range(self.min_periods, len(data) + 1):
            slice_data = data.iloc[:i]
            signals = self.extract(slice_data)
            signals_list.append({
                'date': data.index[i-1],
                **signals.to_dict()
            })

        return pd.DataFrame(signals_list).set_index('date')

    # ========== 内部计算方法 ==========

    def _calc_roc(self, series: pd.Series, period: int) -> float:
        """计算变动率 Rate of Change"""
        if len(series) <= period:
            return 0.0
        prev = series.iloc[-period - 1]
        curr = series.iloc[-1]
        return (curr - prev) / prev if prev != 0 else 0.0

    def _calc_bollinger_z(self, close: pd.Series, period: int = 20) -> float:
        """计算布林带Z-score"""
        if len(close) < period:
            return 0.0
        sma = close.rolling(period).mean().iloc[-1]
        std = close.rolling(period).std().iloc[-1]
        current = close.iloc[-1]
        return (current - sma) / std if std != 0 else 0.0

    def _calc_price_z(self, close: pd.Series, period: int = 20) -> float:
        """计算价格Z-score（相对于近期均值）"""
        return self._calc_bollinger_z(close, period)

    def _calc_volatility(self, close: pd.Series, period: int = 20) -> float:
        """计算标准化波动率（标准差/均值）"""
        if len(close) < period:
            return 0.0
        std = close.rolling(period).std().iloc[-1]
        mean = close.rolling(period).mean().iloc[-1]
        return std / mean if mean != 0 else 0.0

    def _calc_atr_normalized(self, high: pd.Series, low: pd.Series,
                             close: pd.Series, period: int = 14) -> float:
        """计算归一化ATR"""
        if len(close) < period + 1:
            return 0.0

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR
        atr = tr.rolling(period).mean().iloc[-1]

        # 归一化
        return atr / close.iloc[-1] if close.iloc[-1] != 0 else 0.0

    def _calc_macd_normalized(self, close: pd.Series,
                              fast: int = 12, slow: int = 26, signal: int = 9):
        """计算归一化MACD指标"""
        if len(close) < slow:
            return 0.0, 0.0, 0.0

        exp1 = close.ewm(span=fast).mean()
        exp2 = close.ewm(span=slow).mean()

        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        # 归一化（除以当前价格）
        price = close.iloc[-1]
        if price == 0:
            return 0.0, 0.0, 0.0

        macd_norm = macd_line.iloc[-1] / price
        signal_norm = signal_line.iloc[-1] / price
        hist_norm = histogram.iloc[-1] / price

        return macd_norm, signal_norm, hist_norm

    def _calc_rsi(self, close: pd.Series, period: int = 14) -> float:
        """计算RSI"""
        if len(close) < period + 1:
            return 50.0

        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        result = rsi.iloc[-1]
        return result if not pd.isna(result) else 50.0

    def _calc_rsi_divergence(self, close: pd.Series, current_rsi: float,
                             lookback: int = 5) -> float:
        """
        计算RSI背离度

        正值：价格创新低但RSI未创新低（底背离，看多信号）
        负值：价格创新高但RSI未创新高（顶背离，看空信号）
        """
        if len(close) < lookback + 1:
            return 0.0

        # 计算历史RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))

        # 最近n天的价格和RSI
        recent_close = close.iloc[-lookback:]
        recent_rsi = rsi_series.iloc[-lookback:]

        # 价格变化方向
        price_change = (recent_close.iloc[-1] - recent_close.iloc[0]) / recent_close.iloc[0]
        rsi_change = (recent_rsi.iloc[-1] - recent_rsi.iloc[0])

        # 背离 = RSI变化 - 价格变化（标准化后）
        # 正值表示RSI强于价格（潜在底背离）
        divergence = rsi_change - price_change * 100

        return max(-50, min(50, divergence))  # 限制范围

    def _calc_trend_strength(self, close: pd.Series, high: pd.Series,
                             low: pd.Series, period: int = 14) -> tuple:
        """
        计算趋势强度和方向

        Returns:
            (trend_strength: 0-1, trend_direction: -1/0/1)
        """
        if len(close) < period + 1:
            return 0.5, 0

        # 使用ADX计算趋势强度
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(period).mean()
        plus_di = 100 * plus_dm.rolling(period).mean() / atr
        minus_di = 100 * minus_dm.rolling(period).mean() / atr

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        adx = dx.rolling(period).mean()

        trend_strength = adx.iloc[-1] / 100
        if pd.isna(trend_strength):
            trend_strength = 0.5

        # 趋势方向
        if plus_di.iloc[-1] > minus_di.iloc[-1]:
            trend_direction = 1
        elif plus_di.iloc[-1] < minus_di.iloc[-1]:
            trend_direction = -1
        else:
            trend_direction = 0

        return min(1.0, trend_strength), trend_direction

    def _calc_volume_z(self, volume: pd.Series, period: int = 20) -> float:
        """计算成交量Z-score"""
        if len(volume) < period:
            return 0.0

        mean = volume.rolling(period).mean().iloc[-1]
        std = volume.rolling(period).std().iloc[-1]
        current = volume.iloc[-1]

        return (current - mean) / std if std != 0 else 0.0

    def _calc_obv_trend(self, close: pd.Series, volume: pd.Series,
                        lookback: int = 10) -> float:
        """
        计算OBV趋势方向

        Returns: -1 ~ +1
        """
        if len(close) < 2:
            return 0.0

        # 计算OBV
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])

        # 计算最近lookback的趋势
        if len(obv) < lookback:
            return 0.0

        obv_recent = obv[-lookback:]
        x = np.arange(lookback)
        y = np.array(obv_recent)

        # 线性回归斜率
        slope = np.polyfit(x, y, 1)[0]

        # 归一化（相对于OBV均值）
        obv_mean = np.mean(obv_recent)
        if obv_mean == 0:
            return 0.0

        normalized_slope = slope / abs(obv_mean)

        return max(-1, min(1, normalized_slope))

    def _calc_money_flow(self, close: pd.Series, high: pd.Series,
                         low: pd.Series, volume: pd.Series, period: int = 14) -> float:
        """
        计算资金流向 (MFI简化版)

        Returns: -1 ~ +1
        """
        if len(close) < period:
            return 0.0

        # 典型价格
        tp = (high + low + close) / 3

        # 原始资金流
        raw_money_flow = tp * volume

        # 正负资金流
        positive_flow = raw_money_flow.where(tp > tp.shift(), 0).rolling(period).sum()
        negative_flow = raw_money_flow.where(tp < tp.shift(), 0).rolling(period).sum()

        # 资金流比率
        money_flow_ratio = positive_flow / negative_flow

        # MFI
        mfi = 100 - (100 / (1 + money_flow_ratio))

        current_mfi = mfi.iloc[-1]
        if pd.isna(current_mfi):
            return 0.0

        # 映射到 -1 ~ +1
        return (current_mfi - 50) / 50

    def _calc_composite_score(self, signals: TechnicalSignals) -> float:
        """
        计算综合评分

        融合多维度信号到单一分数 (-1 ~ +1)
        """
        score = 0.0

        # 动量贡献 (30%)
        momentum = (signals.roc_5d * 0.5 +
                   signals.roc_10d * 0.3 +
                   signals.roc_20d * 0.2)
        score += momentum * 0.3

        # 位置贡献 (20%)
        # 超卖是正向信号，超买是负向信号
        position = -signals.bollinger_z / 3  # 反转：低Z-score=看多
        score += max(-1, min(1, position)) * 0.2

        # 趋势贡献 (25%)
        trend = signals.trend_direction * signals.trend_strength
        score += trend * 0.25

        # RSI贡献 (15%)
        # RSI < 50 偏向看多，> 50 偏向看空
        rsi_score = (50 - signals.rsi) / 50
        score += rsi_score * 0.15

        # 量价贡献 (10%)
        volume_score = (signals.volume_z + signals.obv_trend) / 2
        score += max(-1, min(1, volume_score)) * 0.1

        return max(-1, min(1, score))


# ========== 便捷函数 ==========

def extract_signals(data: pd.DataFrame) -> TechnicalSignals:
    """便捷函数：快速提取信号"""
    extractor = SignalExtractor()
    return extractor.extract(data)


def extract_signals_series(data: pd.DataFrame) -> pd.DataFrame:
    """便捷函数：提取信号时间序列"""
    extractor = SignalExtractor()
    return extractor.extract_series(data)


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("信号提取器测试")
    print("=" * 60)

    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='B')
    np.random.seed(42)

    # 模拟价格走势（带趋势）
    returns = np.random.randn(len(dates)) * 0.02 + 0.0005
    prices = 100 * np.exp(np.cumsum(returns))

    test_data = pd.DataFrame({
        'Open': prices * (1 + np.random.randn(len(dates)) * 0.005),
        'High': prices * (1 + abs(np.random.randn(len(dates))) * 0.01),
        'Low': prices * (1 - abs(np.random.randn(len(dates))) * 0.01),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    # 确保 High >= Close >= Low
    test_data['High'] = test_data[['Open', 'Close', 'High']].max(axis=1)
    test_data['Low'] = test_data[['Open', 'Close', 'Low']].min(axis=1)

    print(f"\n测试数据: {len(test_data)} 条")
    print(test_data.head())

    # 提取信号
    print("\n" + "=" * 60)
    print("提取当前信号")
    print("=" * 60)

    extractor = SignalExtractor()
    signals = extractor.extract(test_data)

    print(signals.to_prompt_format())

    # 提取信号序列
    print("\n" + "=" * 60)
    print("提取信号时间序列 (最后5天)")
    print("=" * 60)

    signal_df = extractor.extract_series(test_data)
    print(signal_df[['roc_5d', 'rsi', 'bollinger_z', 'composite_score']].tail())

    print("\n✅ 测试完成!")
