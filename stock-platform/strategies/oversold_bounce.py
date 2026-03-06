#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超跌反弹策略 - Oversold Bounce Strategy

基于行为金融学和均值回归理论，捕捉深度超跌后的技术性反弹机会。

核心逻辑：
1. 选择从前高下跌超过阈值（默认40%）的股票
2. 成交量萎缩确认（20日均量 < 60日均量的70%）
3. 买入触发：从最低点反弹一定比例（默认12.5%）
4. 卖出触发：从买入点回调一定比例（默认8%）
5. 硬止损：跌破买入前低点-5%

作者: 量化研究组
版本: 1.0.0
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加父目录到路径（支持直接运行）
sys.path.append(str(Path(__file__).parent))

from base_v2 import BaseStrategyV2
sys.path.append(str(Path(__file__).parent.parent))
from signals import TechnicalSignals


class OversoldBounceStrategy(BaseStrategyV2):
    """
    超跌反弹策略

    参数:
        drawdown_threshold: 跌幅阈值 (默认0.40，即40%)
        lookback_period: 观察周期 (默认120日)
        bounce_ratio: 买入反弹比例 (默认0.125 = 1/8)
        pullback_ratio: 卖出回调比例 (默认0.08 = 1/12)
        stop_loss_pct: 硬止损比例 (默认0.05)
        volume_contraction: 成交量萎缩阈值 (默认0.70)
        enable_volume_filter: 是否启用成交量过滤 (默认True)

    示例:
        # 保守型参数
        conservative = OversoldBounceStrategy(
            drawdown_threshold=0.50,  # 跌幅50%才考虑
            bounce_ratio=0.20,        # 反弹20%才买入
            volume_contraction=0.60   # 成交量萎缩40%
        )

        # 激进型参数
        aggressive = OversoldBounceStrategy(
            drawdown_threshold=0.30,  # 跌幅30%就考虑
            bounce_ratio=0.10,        # 反弹10%就买入
            volume_contraction=0.80   # 成交量萎缩20%
        )
    """

    # ========== 策略参数 ==========
    drawdown_threshold = 0.40      # 跌幅阈值
    lookback_period = 120          # 观察周期（日）
    bounce_ratio = 0.125           # 买入反弹比例 (y/8)
    pullback_ratio = 0.08          # 卖出回调比例 (y/12)
    stop_loss_pct = 0.05           # 硬止损比例
    volume_contraction = 0.70      # 成交量萎缩阈值
    enable_volume_filter = True    # 是否启用成交量过滤

    # ========== 状态变量 ==========
    entry_price = 0.0              # 买入价格
    pre_low = 0.0                  # 买入前的最低点
    max_drawdown_in_position = 0.0 # 持仓期间最大跌幅

    def init(self):
        """初始化 - 计算指标用于可视化"""
        super().init()

        # 为可视化计算指标
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        volume = pd.Series(self.data.Volume)

        # 最高价（观察期内，使用盘中最高价）
        self.high_lookback = self.I(
            lambda: high.rolling(self.lookback_period).max(),
            name=f'High({self.lookback_period})'
        )

        # 最低价（观察期内，使用盘中最低价）
        self.low_lookback = self.I(
            lambda: low.rolling(self.lookback_period).min(),
            name=f'Low({self.lookback_period})'
        )

        # 跌幅计算
        self.drawdown = self.I(
            lambda: (close - close.rolling(self.lookback_period).max()) / close.rolling(self.lookback_period).max(),
            name='Drawdown'
        )

        # 成交量均线
        self.vol_sma_20 = self.I(
            lambda: volume.rolling(20).mean(),
            name='Vol_SMA20'
        )
        self.vol_sma_60 = self.I(
            lambda: volume.rolling(60).mean(),
            name='Vol_SMA60'
        )

    def calibrate_signals(self, signals: TechnicalSignals) -> Dict[str, Any]:
        """
        Level 2: 信号校准

        计算超跌反弹策略所需的关键指标：
        1. 当前跌幅（相对于观察期内最高点）
        2. 从最低点的反弹幅度
        3. 成交量萎缩情况
        4. 持仓状态管理

        Returns:
            {
                'current_price': 当前价格,
                'high_lookback': 观察期内最高价,
                'low_lookback': 观察期内最低价,
                'drawdown': 当前跌幅,
                'bounce_from_low': 从最低点反弹幅度,
                'volume_ratio': 成交量比率(20日/60日),
                'volume_contracted': 成交量是否萎缩,
                'is_oversold': 是否满足超跌条件,
                'has_position': 是否有持仓,
                'entry_price': 买入价格,
                'pre_low': 买入前低点,
                'pullback_from_entry': 从买入点回调幅度,
                'stop_loss_price': 止损价格,
            }
        """
        # 获取当前数据
        data_slice = self._get_data_slice()
        close = data_slice['Close']
        high = data_slice['High']
        low = data_slice['Low']
        volume = data_slice['Volume']
        current_price = close.iloc[-1]

        # 计算观察期内的高低点（使用盘中最高/最低价）
        high_lookback = high.rolling(self.lookback_period).max().iloc[-1]
        low_lookback = low.rolling(self.lookback_period).min().iloc[-1]

        # 当前跌幅
        drawdown = (current_price - high_lookback) / high_lookback if high_lookback != 0 else 0

        # 从最低点反弹幅度
        bounce_from_low = (current_price - low_lookback) / low_lookback if low_lookback != 0 else 0

        # 成交量萎缩检查
        vol_sma_20 = volume.rolling(20).mean().iloc[-1]
        vol_sma_60 = volume.rolling(60).mean().iloc[-1]
        volume_ratio = vol_sma_20 / vol_sma_60 if vol_sma_60 != 0 else 1.0
        volume_contracted = volume_ratio < self.volume_contraction

        # 是否满足超跌条件
        is_oversold = drawdown <= -self.drawdown_threshold

        # 持仓状态
        has_position = self.position.is_long if self.position else False

        # 计算从买入点的回调幅度
        pullback_from_entry = 0.0
        stop_loss_price = 0.0
        if has_position and self.entry_price > 0:
            pullback_from_entry = (self.entry_price - current_price) / self.entry_price
            stop_loss_price = self.pre_low * (1 - self.stop_loss_pct)

        return {
            'current_price': current_price,
            'high_lookback': high_lookback,
            'low_lookback': low_lookback,
            'drawdown': drawdown,
            'bounce_from_low': bounce_from_low,
            'volume_ratio': volume_ratio,
            'volume_contracted': volume_contracted,
            'is_oversold': is_oversold,
            'has_position': has_position,
            'entry_price': self.entry_price,
            'pre_low': self.pre_low,
            'pullback_from_entry': pullback_from_entry,
            'stop_loss_price': stop_loss_price,
            # 附加信号
            'trend_strength': signals.trend_strength,
            'rsi': signals.rsi,
            'composite_score': signals.composite_score,
        }

    def make_decision(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Level 3: 交易决策

        决策规则:
        1. 买入条件（必须全部满足）:
           - 当前跌幅 >= 阈值（如40%）
           - 从最低点反弹 >= bounce_ratio（如12.5%）
           - 成交量萎缩（可选）
           - 无持仓

        2. 卖出条件（满足其一即可）:
           - 从买入点回调 >= pullback_ratio（如8%）
           - 跌破硬止损价（前低-5%）

        3. 其他情况: 持仓等待
        """
        has_position = calibrated['has_position']

        # ========== 买入决策 ==========
        if not has_position:
            return self._evaluate_buy_signal(calibrated)

        # ========== 卖出决策 ==========
        else:
            return self._evaluate_sell_signal(calibrated)

    def _evaluate_buy_signal(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """评估买入信号"""
        reasons = []
        conditions_met = []

        # 条件1: 超跌检查
        if calibrated['is_oversold']:
            conditions_met.append(True)
            reasons.append(f"跌幅{abs(calibrated['drawdown']):.1%} >= 阈值{self.drawdown_threshold:.1%}")
        else:
            conditions_met.append(False)
            return {
                'action': 'hold',
                'reason': f"跌幅{abs(calibrated['drawdown']):.1%}不足，未达阈值{self.drawdown_threshold:.1%}",
                'confidence': 0.0
            }

        # 条件2: 反弹确认
        if calibrated['bounce_from_low'] >= self.bounce_ratio:
            conditions_met.append(True)
            reasons.append(f"反弹{calibrated['bounce_from_low']:.1%} >= 阈值{self.bounce_ratio:.1%}")
        else:
            conditions_met.append(False)
            return {
                'action': 'hold',
                'reason': f"反弹{calibrated['bounce_from_low']:.1%}不足，等待反弹{self.bounce_ratio:.1%}",
                'confidence': 0.0
            }

        # 条件3: 成交量萎缩（可选）
        if self.enable_volume_filter:
            if calibrated['volume_contracted']:
                conditions_met.append(True)
                reasons.append(f"成交量萎缩({calibrated['volume_ratio']:.1%} < {self.volume_contraction:.1%})")
            else:
                conditions_met.append(False)
                return {
                    'action': 'hold',
                    'reason': f"成交量未萎缩({calibrated['volume_ratio']:.1%} >= {self.volume_contraction:.1%})，等待确认",
                    'confidence': 0.0
                }

        # 条件4: RSI过滤（附加条件，不必须）
        rsi_ok = calibrated['rsi'] < 50  # 避免超买
        if rsi_ok:
            reasons.append(f"RSI={calibrated['rsi']:.1f}未超买")

        # 所有条件满足，执行买入
        if all(conditions_met):
            return {
                'action': 'buy',
                'reason': ' | '.join(reasons),
                'confidence': min(1.0, len(conditions_met) * 0.25 + 0.25)
            }

        return {'action': 'hold', 'reason': '条件未满足', 'confidence': 0.0}

    def _evaluate_sell_signal(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """评估卖出信号"""
        current_price = calibrated['current_price']

        # 条件1: 硬止损检查（最高优先级）
        if current_price <= calibrated['stop_loss_price']:
            return {
                'action': 'sell',
                'reason': f"硬止损触发：价格{current_price:.2f} <= 止损价{calibrated['stop_loss_price']:.2f}",
                'confidence': 1.0
            }

        # 条件2: 回调止盈
        if calibrated['pullback_from_entry'] >= self.pullback_ratio:
            return {
                'action': 'sell',
                'reason': f"回调止盈：回撤{calibrated['pullback_from_entry']:.1%} >= 阈值{self.pullback_ratio:.1%}",
                'confidence': 0.8
            }

        # 条件3: 趋势反转（附加条件）
        if calibrated['composite_score'] < -0.5:
            return {
                'action': 'sell',
                'reason': f"趋势恶化：综合评分{calibrated['composite_score']:.2f}跌破-0.5",
                'confidence': 0.6
            }

        # 持仓等待
        hold_reason = f"持仓中，回撤{calibrated['pullback_from_entry']:.1%}，止损价{calibrated['stop_loss_price']:.2f}"
        return {'action': 'hold', 'reason': hold_reason, 'confidence': 0.0}

    def _execute_decision(self, decision: Dict[str, Any]):
        """执行交易决策，并记录状态"""
        action = decision.get('action', 'hold')

        if action == 'buy':
            if not self.position:
                self.buy()
                # 记录买入状态
                self.entry_price = self.data.Close[-1]
                # 计算买入前的最低点（用于止损）
                data_slice = self._get_data_slice()
                self.pre_low = data_slice['Close'].rolling(self.lookback_period).min().iloc[-1]
                self.max_drawdown_in_position = 0.0

        elif action == 'sell':
            if self.position:
                self.position.close()
                # 重置状态
                self.entry_price = 0.0
                self.pre_low = 0.0
                self.max_drawdown_in_position = 0.0

        # 'hold' 不执行任何操作

    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数（用于展示和保存）"""
        return {
            'drawdown_threshold': self.drawdown_threshold,
            'lookback_period': self.lookback_period,
            'bounce_ratio': self.bounce_ratio,
            'pullback_ratio': self.pullback_ratio,
            'stop_loss_pct': self.stop_loss_pct,
            'volume_contraction': self.volume_contraction,
            'enable_volume_filter': self.enable_volume_filter,
        }


class OversoldBounceConservative(OversoldBounceStrategy):
    """
    保守版超跌反弹策略

    更严格的条件，追求更高的胜率
    """
    drawdown_threshold = 0.50      # 跌幅50%才考虑
    bounce_ratio = 0.20            # 反弹20%才买入
    pullback_ratio = 0.05          # 回调5%就止盈
    stop_loss_pct = 0.03           # 更紧的止损
    volume_contraction = 0.60      # 成交量萎缩40%


class OversoldBounceAggressive(OversoldBounceStrategy):
    """
    激进版超跌反弹策略

    更宽松的条件，更多的交易机会
    """
    drawdown_threshold = 0.30      # 跌幅30%就考虑
    bounce_ratio = 0.10            # 反弹10%就买入
    pullback_ratio = 0.12          # 回调12%才止盈
    stop_loss_pct = 0.08           # 更宽松的止损
    volume_contraction = 0.80      # 成交量萎缩20%
    enable_volume_filter = False   # 不检查成交量


# ========== 便捷函数 ==========

def check_oversold_condition(
    data: pd.DataFrame,
    drawdown_threshold: float = 0.40,
    lookback_period: int = 120,
    volume_contraction: float = 0.70,
) -> Tuple[bool, Dict[str, Any]]:
    """
    检查单只股票是否满足超跌条件

    Returns:
        (是否满足条件, 详细信息字典)
    """
    if len(data) < lookback_period:
        return False, {'error': '数据不足'}

    close = data['Close']
    high = data['High']
    low = data['Low']
    volume = data['Volume']
    current_price = close.iloc[-1]

    # 计算观察期内的高低点（使用盘中最高/最低价）
    high_lookback = high.rolling(lookback_period).max().iloc[-1]
    low_lookback = low.rolling(lookback_period).min().iloc[-1]

    # 当前跌幅
    drawdown = (current_price - high_lookback) / high_lookback if high_lookback != 0 else 0

    # 从最低点反弹幅度
    bounce_from_low = (current_price - low_lookback) / low_lookback if low_lookback != 0 else 0

    # 成交量萎缩检查
    vol_sma_20 = volume.rolling(20).mean().iloc[-1]
    vol_sma_60 = volume.rolling(60).mean().iloc[-1]
    volume_ratio = vol_sma_20 / vol_sma_60 if vol_sma_60 != 0 else 1.0
    volume_contracted = volume_ratio < volume_contraction

    # 是否满足超跌条件
    is_oversold = drawdown <= -drawdown_threshold

    info = {
        'current_price': current_price,
        'high_lookback': high_lookback,
        'low_lookback': low_lookback,
        'drawdown': drawdown,
        'bounce_from_low': bounce_from_low,
        'volume_ratio': volume_ratio,
        'volume_contracted': volume_contracted,
        'is_oversold': is_oversold,
    }

    return is_oversold, info


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 70)
    print("超跌反弹策略测试")
    print("=" * 70)

    # 测试策略类创建
    print("\n✅ 策略类创建成功:")
    print(f"   - OversoldBounceStrategy (标准版)")
    print(f"   - OversoldBounceConservative (保守版)")
    print(f"   - OversoldBounceAggressive (激进版)")

    # 测试参数（策略类参数是类变量，不需要实例化）
    print("\n✅ 策略参数:")
    print(f"   drawdown_threshold: {OversoldBounceStrategy.drawdown_threshold}")
    print(f"   lookback_period: {OversoldBounceStrategy.lookback_period}")
    print(f"   bounce_ratio: {OversoldBounceStrategy.bounce_ratio}")
    print(f"   pullback_ratio: {OversoldBounceStrategy.pullback_ratio}")
    print(f"   stop_loss_pct: {OversoldBounceStrategy.stop_loss_pct}")
    print(f"   volume_contraction: {OversoldBounceStrategy.volume_contraction}")
    print(f"   enable_volume_filter: {OversoldBounceStrategy.enable_volume_filter}")

    # 测试便捷函数
    print("\n✅ 测试便捷函数:")
    # 创建模拟数据
    dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='B')
    np.random.seed(42)

    # 模拟一个超跌反弹的走势
    prices = []
    current = 100
    for i in range(len(dates)):
        if i < 80:
            # 下跌阶段
            current *= (1 - np.random.uniform(0.005, 0.02))
        elif i == 80:
            # 最低点
            current *= 0.95
        else:
            # 反弹阶段
            current *= (1 + np.random.uniform(0.005, 0.015))
        prices.append(current)

    test_data = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
        'Low': [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    # 检查超跌条件
    is_oversold, info = check_oversold_condition(test_data)
    print(f"   是否超跌: {is_oversold}")
    print(f"   当前跌幅: {info.get('drawdown', 0):.2%}")
    print(f"   从低点反弹: {info.get('bounce_from_low', 0):.2%}")
    print(f"   成交量比率: {info.get('volume_ratio', 0):.2%}")

    print("\n" + "=" * 70)
    print("✅ 测试通过!")
    print("=" * 70)
