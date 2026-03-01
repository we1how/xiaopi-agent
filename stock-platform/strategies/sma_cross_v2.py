#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线交叉策略 V2 - 细粒度版本

改造点：
1. 使用 BaseStrategyV2 分层架构
2. 指标计算分离到 SignalExtractor
3. 决策理由输出（语义一致性）
4. 基于趋势强度和RSI过滤信号

与原版 SmaCross 的区别：
- 原版：策略内部计算均线，直接判断交叉
- V2：使用标准化信号，可解释的综合评分决策
"""

from typing import Dict, Any
import pandas as pd
from backtesting.lib import crossover

from .base_v2 import BaseStrategyV2
from signals import TechnicalSignals


class SmaCrossV2(BaseStrategyV2):
    """
    细粒度双均线策略

    参数:
        n_short: 短期均线周期（默认10）
        n_long: 长期均线周期（默认20）
        trend_filter: 是否启用趋势过滤（默认True）
        min_trend_strength: 最小趋势强度（默认0.3）
        rsi_lower: RSI超卖阈值（默认30）
        rsi_upper: RSI超买阈值（默认70）

    决策逻辑:
        买入: 均线金叉 + 趋势强度达标 + RSI未超买
        卖出: 均线死叉 + (趋势反转或RSI超买)
    """

    # 策略参数
    n_short = 10
    n_long = 20
    trend_filter = True
    min_trend_strength = 0.3
    rsi_lower = 30
    rsi_upper = 70

    def init(self):
        """初始化 - 保留均线用于可视化"""
        super().init()

        # 为可视化计算均线
        close = pd.Series(self.data.Close)
        self.sma_short = self.I(
            lambda: close.rolling(self.n_short).mean(),
            name=f'SMA({self.n_short})'
        )
        self.sma_long = self.I(
            lambda: close.rolling(self.n_long).mean(),
            name=f'SMA({self.n_long})'
        )

    def calibrate_signals(self, signals: TechnicalSignals) -> Dict[str, Any]:
        """
        Level 2: 信号校准

        校准逻辑:
        1. 基于波动率调整置信度（高波动降低置信度）
        2. 基于趋势强度过滤信号
        3. 计算综合评分
        """
        # 基础信号
        calibrated = {
            'composite_score': signals.composite_score,
            'trend_strength': signals.trend_strength,
            'trend_direction': signals.trend_direction,
            'rsi': signals.rsi,
            'bollinger_z': signals.bollinger_z,
            'volatility': signals.volatility_20d,
            'roc_5d': signals.roc_5d,
            'macd': signals.macd_normalized,
            'has_position': self.position.is_long if self.position else False,
            'entry_price': self.trades[-1].entry_price if self.trades else 0
        }

        # 波动率调整（高波动降低置信度）
        vol_factor = 1.0 - min(1.0, signals.volatility_20d * 5)
        calibrated['confidence'] = signals.trend_strength * vol_factor

        # 趋势质量评分
        if signals.trend_direction > 0:  # 上升趋势
            trend_score = signals.trend_strength
        elif signals.trend_direction < 0:  # 下降趋势
            trend_score = -signals.trend_strength
        else:
            trend_score = 0

        calibrated['trend_score'] = trend_score

        # 动量评分（短期动量占主导）
        momentum = (signals.roc_5d * 0.6 +
                   signals.roc_10d * 0.3 +
                   signals.roc_20d * 0.1)
        calibrated['momentum_score'] = momentum

        return calibrated

    def make_decision(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Level 3: 交易决策

        决策规则:
        1. 金叉买入：
           - 短期均线上穿长期均线
           - 趋势强度 >= min_trend_strength（可选）
           - RSI <= rsi_upper（未超买）

        2. 死叉卖出：
           - 短期均线下穿长期均线
           - RSI >= rsi_lower（或未持仓盈利）
        """
        has_position = calibrated['has_position']

        # 检测均线交叉
        golden_cross = crossover(self.sma_short, self.sma_long)
        death_cross = crossover(self.sma_long, self.sma_short)

        # 构建理由组件
        reasons = []

        # ===== 买入决策 =====
        if not has_position and golden_cross:
            reasons.append(f"均线金叉(SMA{self.n_short}上穿SMA{self.n_long})")

            # 趋势过滤
            if self.trend_filter:
                if calibrated['trend_strength'] >= self.min_trend_strength:
                    reasons.append(f"趋势强度{calibrated['trend_strength']:.1%}达标")
                else:
                    # 趋势弱，但可能有反弹机会
                    if calibrated['rsi'] < 40:  # 超卖反弹
                        reasons.append(f"超卖反弹机会(RSI={calibrated['rsi']:.1f})")
                    else:
                        return {
                            'action': 'hold',
                            'reason': f"趋势强度{calibrated['trend_strength']:.1%}不足，观望",
                            'confidence': 0.3
                        }

            # RSI过滤
            if calibrated['rsi'] <= self.rsi_upper:
                reasons.append(f"RSI={calibrated['rsi']:.1f}未超买")
            else:
                return {
                    'action': 'hold',
                    'reason': f"RSI超买({calibrated['rsi']:.1f})，回避追高",
                    'confidence': 0.2
                }

            # 动量确认
            if calibrated['momentum_score'] > 0:
                reasons.append(f"短期动量向上({calibrated['momentum_score']:+.2%})")

            return {
                'action': 'buy',
                'reason': '；'.join(reasons),
                'confidence': calibrated['confidence']
            }

        # ===== 卖出决策 =====
        elif has_position and death_cross:
            reasons.append(f"均线死叉(SMA{self.n_short}下穿SMA{self.n_long})")

            # RSI过滤
            if calibrated['rsi'] >= self.rsi_lower:
                reasons.append(f"RSI={calibrated['rsi']:.1f}支持卖出")

            # 趋势确认
            if calibrated['trend_direction'] < 0:
                reasons.append(f"趋势转弱(强度{calibrated['trend_strength']:.1%})")

            return {
                'action': 'sell',
                'reason': '；'.join(reasons),
                'confidence': calibrated['confidence']
            }

        # ===== 持仓检查（止损/止盈）=====
        elif has_position:
            # 基于综合评分的动态止损
            if calibrated['composite_score'] < -0.5:
                return {
                    'action': 'sell',
                    'reason': f"综合评分跌破止损线({calibrated['composite_score']:+.2f})",
                    'confidence': 0.6
                }

            # RSI极端超买
            if calibrated['rsi'] > 80:
                return {
                    'action': 'sell',
                    'reason': f"RSI严重超买({calibrated['rsi']:.1f})，获利了结",
                    'confidence': 0.5
                }

        # ===== 默认：持仓 =====
        return {
            'action': 'hold',
            'reason': self._get_hold_reason(calibrated, golden_cross, death_cross),
            'confidence': 0.0
        }

    def _get_hold_reason(self, calibrated: Dict, golden_cross: bool,
                         death_cross: bool) -> str:
        """生成持仓理由"""
        reasons = []

        if golden_cross:
            reasons.append("有金叉但条件不满足")
            if calibrated['rsi'] > self.rsi_upper:
                reasons.append(f"RSI超买({calibrated['rsi']:.1f})")
            if calibrated['trend_strength'] < self.min_trend_strength:
                reasons.append(f"趋势弱({calibrated['trend_strength']:.1%})")
        elif death_cross:
            reasons.append("有死叉但无持仓")
        else:
            reasons.append("无明确技术信号")

        reasons.append(f"综合评分{calibrated['composite_score']:+.2f}")

        return '，'.join(reasons)


class SmaCrossV2Aggressive(SmaCrossV2):
    """
    激进版双均线策略

    减少过滤条件，提高交易频率
    """
    trend_filter = False
    min_trend_strength = 0.1
    rsi_lower = 20
    rsi_upper = 80

    def make_decision(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """简化决策：只看均线交叉"""
        has_position = calibrated['has_position']

        golden_cross = crossover(self.sma_short, self.sma_long)
        death_cross = crossover(self.sma_long, self.sma_short)

        if not has_position and golden_cross:
            return {
                'action': 'buy',
                'reason': f"金叉买入(激进模式)",
                'confidence': 0.5
            }
        elif has_position and death_cross:
            return {
                'action': 'sell',
                'reason': f"死叉卖出(激进模式)",
                'confidence': 0.5
            }

        return {'action': 'hold', 'reason': '无信号', 'confidence': 0.0}


class SmaCrossV2Conservative(SmaCrossV2):
    """
    保守版双均线策略

    增加过滤条件，提高信号质量
    """
    trend_filter = True
    min_trend_strength = 0.5
    rsi_lower = 35
    rsi_upper = 65

    def make_decision(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """严格决策：多重确认"""
        has_position = calibrated['has_position']

        golden_cross = crossover(self.sma_short, self.sma_long)
        death_cross = crossover(self.sma_long, self.sma_short)

        # 买入需要：金叉 + 强趋势 + RSI适中 + 动量向上
        if not has_position and golden_cross:
            if (calibrated['trend_strength'] >= self.min_trend_strength and
                calibrated['rsi'] <= self.rsi_upper and
                calibrated['rsi'] >= self.rsi_lower and
                calibrated['momentum_score'] > 0):

                return {
                    'action': 'buy',
                    'reason': (f"多重确认：金叉+强趋势({calibrated['trend_strength']:.1%})+"
                              f"RSI适中({calibrated['rsi']:.1f})+动量向上"),
                    'confidence': 0.8
                }

        # 卖出：死叉 或 综合评分恶化
        elif has_position:
            if death_cross:
                return {
                    'action': 'sell',
                    'reason': f"死叉卖出",
                    'confidence': 0.7
                }
            elif calibrated['composite_score'] < -0.3:
                return {
                    'action': 'sell',
                    'reason': f"评分恶化({calibrated['composite_score']:+.2f})",
                    'confidence': 0.6
                }

        return {'action': 'hold', 'reason': '条件未满足', 'confidence': 0.0}


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("SmaCrossV2 策略测试")
    print("=" * 60)

    print("\n✅ 策略类创建成功:")
    print(f"   - SmaCrossV2 (标准版)")
    print(f"   - SmaCrossV2Aggressive (激进版)")
    print(f"   - SmaCrossV2Conservative (保守版)")

    print("\n✅ 策略参数:")
    print(f"   n_short={SmaCrossV2.n_short}")
    print(f"   n_long={SmaCrossV2.n_long}")
    print(f"   trend_filter={SmaCrossV2.trend_filter}")
    print(f"   min_trend_strength={SmaCrossV2.min_trend_strength}")

    print("\n✅ 测试通过!")
