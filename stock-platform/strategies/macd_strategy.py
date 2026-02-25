#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD 策略
移动平均收敛发散指标策略

策略逻辑：
- MACD 线上穿信号线时买入
- MACD 线下穿信号线时卖出
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple:
    """
    计算 MACD 指标
    
    Args:
        prices: 价格序列
        fast: 快线周期（默认12）
        slow: 慢线周期（默认26）
        signal: 信号线周期（默认9）
    
    Returns:
        (macd_line, signal_line, histogram) 三个序列
    """
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


class MacdStrategy(Strategy):
    """
    MACD 金叉死叉策略
    
    参数:
        fast: 快线周期（默认12）
        slow: 慢线周期（默认26）
        signal: 信号线周期（默认9）
    
    使用示例:
        from strategies import MacdStrategy
        results = run_backtest(df, MacdStrategy, fast=12, slow=26, signal=9)
    """
    
    fast = 12
    slow = 26
    signal = 9
    
    def init(self):
        """初始化 MACD 指标"""
        close = pd.Series(self.data.Close)
        
        # 计算 MACD
        macd, signal, hist = calculate_macd(close, self.fast, self.slow, self.signal)
        
        self.macd_line = self.I(lambda: macd, name='MACD')
        self.signal_line = self.I(lambda: signal, name='Signal')
        self.histogram = self.I(lambda: hist, name='Histogram')
    
    def next(self):
        """交易逻辑"""
        # MACD 上穿信号线 - 金叉买入
        if crossover(self.macd_line, self.signal_line):
            self.buy()
        
        # MACD 下穿信号线 - 死叉卖出
        elif crossover(self.signal_line, self.macd_line):
            self.sell()


class MacdZeroLine(Strategy):
    """
    MACD 零轴策略
    
    结合零轴位置过滤：
    - 零轴上方金叉：强买入信号
    - 零轴下方死叉：强卖出信号
    
    参数:
        fast: 快线周期（默认12）
        slow: 慢线周期（默认26）
        signal: 信号线周期（默认9）
    """
    
    fast = 12
    slow = 26
    signal = 9
    
    def init(self):
        """初始化 MACD 指标"""
        close = pd.Series(self.data.Close)
        macd, signal, hist = calculate_macd(close, self.fast, self.slow, self.signal)
        
        self.macd_line = self.I(lambda: macd, name='MACD')
        self.signal_line = self.I(lambda: signal, name='Signal')
        self.histogram = self.I(lambda: hist, name='Histogram')
    
    def next(self):
        """交易逻辑"""
        macd_val = self.macd_line[-1]
        
        # 金叉
        if crossover(self.macd_line, self.signal_line):
            # 零轴上方金叉 - 强势买入
            if macd_val > 0:
                self.buy()
            # 零轴下方金叉 - 弱势买入（可设置只平空仓）
            else:
                if self.position and self.position.is_short:
                    self.position.close()
        
        # 死叉
        elif crossover(self.signal_line, self.macd_line):
            # 零轴下方死叉 - 强势卖出
            if macd_val < 0:
                self.sell()
            # 零轴上方死叉 - 弱势卖出（可设置只平多仓）
            else:
                if self.position and self.position.is_long:
                    self.position.close()


class MacdHistogram(Strategy):
    """
    MACD 柱状图策略
    
    基于柱状图的变化：
    - 柱状图由负转正：买入
    - 柱状图由正转负：卖出
    
    参数:
        fast: 快线周期（默认12）
        slow: 慢线周期（默认26）
        signal: 信号线周期（默认9）
    """
    
    fast = 12
    slow = 26
    signal = 9
    
    def init(self):
        """初始化 MACD 指标"""
        close = pd.Series(self.data.Close)
        macd, signal, hist = calculate_macd(close, self.fast, self.slow, self.signal)
        
        self.macd_line = self.I(lambda: macd, name='MACD')
        self.signal_line = self.I(lambda: signal, name='Signal')
        self.histogram = self.I(lambda: hist, name='Histogram')
    
    def next(self):
        """交易逻辑"""
        if len(self.data.Close) < 2:
            return
        
        # 柱状图当前值和前一个值
        hist_current = self.histogram[-1]
        hist_prev = self.histogram[-2]
        
        # 柱状图由负转正 - 买入
        if hist_prev < 0 and hist_current > 0:
            self.buy()
        
        # 柱状图由正转负 - 卖出
        elif hist_prev > 0 and hist_current < 0:
            self.sell()


if __name__ == "__main__":
    print("MACD 策略示例")
    print("=" * 50)
    print("""
使用说明:

1. 基本 MACD 策略:
   from strategies import MacdStrategy
   
   results = run_backtest(
       data=df,
       strategy_class=MacdStrategy,
       fast=12,
       slow=26,
       signal=9
   )

2. MACD 零轴策略:
   from strategies.macd_strategy import MacdZeroLine
   
   results = run_backtest(
       data=df,
       strategy_class=MacdZeroLine,
       fast=12,
       slow=26,
       signal=9
   )

3. MACD 柱状图策略:
   from strategies.macd_strategy import MacdHistogram
   
   results = run_backtest(
       data=df,
       strategy_class=MacdHistogram,
       fast=12,
       slow=26,
       signal=9
   )

MACD 参数说明:
- 默认参数 (12, 26, 9) 适合日线
- 短线交易可尝试 (6, 13, 5)
- 长线投资可尝试 (19, 39, 9)
    """)
