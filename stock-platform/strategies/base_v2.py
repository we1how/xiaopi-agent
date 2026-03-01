#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
细粒度策略基类 - Level 2 & Level 3

实现分层决策架构：
- Level 1: SignalExtractor (信号提取)
- Level 2: calibrate_signals (信号校准)
- Level 3: make_decision (交易决策)

特点：
1. 指标计算与决策分离
2. 决策理由输出（语义一致性）
3. 支持决策历史记录
"""

from backtesting import Strategy
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from signals import SignalExtractor, TechnicalSignals


class BaseStrategyV2(Strategy):
    """
    细粒度策略基类

    使用方式：
        class MyStrategy(BaseStrategyV2):
            def calibrate_signals(self, signals: TechnicalSignals) -> Dict:
                # 自定义校准逻辑
                return calibrated

            def make_decision(self, calibrated: Dict) -> Dict:
                # 自定义决策逻辑
                return {'action': 'buy', 'reason': '...'}
    """

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)

        # 信号提取器 (Level 1)
        self.extractor = SignalExtractor()

        # 决策历史（用于分析）
        self.decision_history: List[Dict] = []

        # 当前信号缓存
        self.current_signals: Optional[TechnicalSignals] = None
        self.current_calibrated: Optional[Dict] = None

    def init(self):
        """
        初始化方法

        子类可以重写此方法添加自定义指标（用于可视化）
        """
        pass

    def next(self):
        """
        主循环 - 分层决策流程

        流程：
        1. Level 1: 提取信号
        2. Level 2: 校准信号
        3. Level 3: 做出决策
        4. 执行交易
        """
        # 准备数据切片（只使用历史数据，防未来函数）
        data_slice = self._get_data_slice()

        # Level 1: 信号提取
        signals = self.extractor.extract(data_slice)
        self.current_signals = signals

        # Level 2: 信号校准
        calibrated = self.calibrate_signals(signals)
        self.current_calibrated = calibrated

        # Level 3: 交易决策
        decision = self.make_decision(calibrated)

        # 执行交易
        self._execute_decision(decision)

        # 记录决策
        self._record_decision(decision, signals, calibrated)

    def _get_data_slice(self) -> pd.DataFrame:
        """获取当前可用的历史数据切片"""
        return pd.DataFrame({
            'Open': self.data.Open,
            'High': self.data.High,
            'Low': self.data.Low,
            'Close': self.data.Close,
            'Volume': self.data.Volume
        })

    def calibrate_signals(self, signals: TechnicalSignals) -> Dict[str, Any]:
        """
        Level 2: 信号校准

        在此方法中：
        - 基于持仓状态调整信号权重
        - 应用市场环境过滤
        - 风险调整

        Args:
            signals: 原始技术信号

        Returns:
            校准后的信号字典

        示例：
            def calibrate_signals(self, signals):
                # 高波动率降低置信度
                confidence = signals.trend_strength
                if signals.volatility_20d > 0.05:
                    confidence *= 0.8

                return {
                    'momentum': signals.roc_5d,
                    'confidence': confidence,
                    'rsi': signals.rsi
                }
        """
        # 默认实现：直接传递信号
        return {
            'composite_score': signals.composite_score,
            'trend_strength': signals.trend_strength,
            'trend_direction': signals.trend_direction,
            'rsi': signals.rsi,
            'bollinger_z': signals.bollinger_z,
            'volatility': signals.volatility_20d,
            'has_position': self.position.is_long if self.position else False
        }

    def make_decision(self, calibrated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Level 3: 交易决策

        在此方法中：
        - 综合所有信号做出最终决策
        - 确定交易动作（buy/sell/hold）
        - 生成决策理由（语义一致性）

        Args:
            calibrated: 校准后的信号

        Returns:
            {
                'action': 'buy' | 'sell' | 'hold',
                'reason': '决策理由描述',
                'confidence': 0.0-1.0,  # 可选
                'size': 1.0  # 仓位大小（可选）
            }

        示例：
            def make_decision(self, calibrated):
                if not calibrated['has_position']:
                    if calibrated['composite_score'] > 0.5:
                        return {
                            'action': 'buy',
                            'reason': f'综合评分{calibrated["composite_score"]:.2f}超过阈值'
                        }
                else:
                    if calibrated['composite_score'] < -0.3:
                        return {
                            'action': 'sell',
                            'reason': f'综合评分{calibrated["composite_score"]:.2f}跌破止损线'
                        }

                return {'action': 'hold', 'reason': '无明确信号'}
        """
        raise NotImplementedError("子类必须实现 make_decision 方法")

    def _execute_decision(self, decision: Dict[str, Any]):
        """执行交易决策"""
        action = decision.get('action', 'hold')
        size = decision.get('size', 1.0)

        if action == 'buy':
            if not self.position:
                self.buy(size=size)
        elif action == 'sell':
            if self.position:
                self.position.close()
        # 'hold' 不执行任何操作

    def _record_decision(self, decision: Dict, signals: TechnicalSignals,
                         calibrated: Dict):
        """记录决策历史"""
        self.decision_history.append({
            'date': self.data.index[-1],
            'action': decision.get('action', 'hold'),
            'reason': decision.get('reason', ''),
            'confidence': decision.get('confidence', 0.0),
            'signals': asdict(signals),
            'calibrated': calibrated,
            'equity': self.equity,
            'position_size': self.position.size if self.position else 0
        })

    def get_decision_history(self) -> pd.DataFrame:
        """获取决策历史记录"""
        if not self.decision_history:
            return pd.DataFrame()

        df = pd.DataFrame(self.decision_history)
        df.set_index('date', inplace=True)
        return df

    def get_current_signals(self) -> Optional[TechnicalSignals]:
        """获取当前信号（用于可视化）"""
        return self.current_signals

    def get_signal_summary(self) -> Dict[str, Any]:
        """获取信号汇总统计"""
        if not self.decision_history:
            return {}

        df = self.get_decision_history()

        return {
            'total_decisions': len(df),
            'buy_count': (df['action'] == 'buy').sum(),
            'sell_count': (df['action'] == 'sell').sum(),
            'hold_count': (df['action'] == 'hold').sum(),
            'avg_confidence': df['confidence'].mean() if 'confidence' in df else 0,
            'signal_changes': (df['action'] != df['action'].shift()).sum()
        }


# ========== 辅助函数 ==========

def create_simple_strategy(name: str, buy_condition, sell_condition):
    """
    工厂函数：快速创建简单策略

    Args:
        name: 策略名称
        buy_condition: 买入条件函数 (calibrated) -> bool
        sell_condition: 卖出条件函数 (calibrated) -> bool

    Returns:
        策略类

    示例：
        MyStrategy = create_simple_strategy(
            'MyStrategy',
            buy_condition=lambda c: c['composite_score'] > 0.5,
            sell_condition=lambda c: c['composite_score'] < -0.3
        )
    """
    class SimpleStrategy(BaseStrategyV2):
        def make_decision(self, calibrated):
            has_position = calibrated.get('has_position', False)

            if not has_position and buy_condition(calibrated):
                return {
                    'action': 'buy',
                    'reason': f'{name}买入信号触发'
                }
            elif has_position and sell_condition(calibrated):
                return {
                    'action': 'sell',
                    'reason': f'{name}卖出信号触发'
                }

            return {'action': 'hold', 'reason': '无交易信号'}

    SimpleStrategy.__name__ = name
    return SimpleStrategy


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("细粒度策略基类测试")
    print("=" * 60)

    # 测试工厂函数
    TestStrategy = create_simple_strategy(
        'TestStrategy',
        buy_condition=lambda c: c['composite_score'] > 0.3,
        sell_condition=lambda c: c['composite_score'] < -0.2
    )

    print(f"\n✅ 创建策略类: {TestStrategy.__name__}")
    print(f"   基类: {TestStrategy.__bases__}")

    print("\n✅ 基类测试通过!")
