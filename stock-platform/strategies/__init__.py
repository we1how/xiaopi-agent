"""
策略模块
包含各种交易策略实现
"""

# 原版策略（向后兼容）
from .sma_cross import SmaCross
from .rsi_strategy import RsiStrategy
from .macd_strategy import MacdStrategy

# 细粒度策略 V2（新架构）
from .base_v2 import BaseStrategyV2, create_simple_strategy
from .sma_cross_v2 import SmaCrossV2, SmaCrossV2Aggressive, SmaCrossV2Conservative

# 超跌反弹策略
from .oversold_bounce import (
    OversoldBounceStrategy,
    OversoldBounceConservative,
    OversoldBounceAggressive
)

__all__ = [
    # 原版策略
    'SmaCross', 'RsiStrategy', 'MacdStrategy',
    # V2 细粒度策略
    'BaseStrategyV2', 'create_simple_strategy',
    'SmaCrossV2', 'SmaCrossV2Aggressive', 'SmaCrossV2Conservative',
    # 超跌反弹策略
    'OversoldBounceStrategy', 'OversoldBounceConservative', 'OversoldBounceAggressive',
]
