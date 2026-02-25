#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线交叉策略 (SMA Cross)
经典的移动平均线交叉策略

策略逻辑：
- 当短期均线上穿长期均线时买入
- 当短期均线下穿长期均线时卖出
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np


class SmaCross(Strategy):
    """
    双均线交叉策略
    
    参数:
        n_short: 短期均线周期（默认10）
        n_long: 长期均线周期（默认20）
    
    使用示例:
        from strategies import SmaCross
        results = run_backtest(df, SmaCross, n1=10, n2=30)
    """
    
    # 策略参数（可在回测时调整）
    n_short = 10  # 短期均线周期
    n_long = 20   # 长期均线周期
    
    def init(self):
        """初始化指标"""
        # 计算短期和长期移动平均线
        close = pd.Series(self.data.Close)
        self.sma_short = self.I(
            lambda: close.rolling(self.n_short).mean(),
            name=f'SMA({self.n_short})'
        )
        self.sma_long = self.I(
            lambda: close.rolling(self.n_long).mean(),
            name=f'SMA({self.n_long})'
        )
    
    def next(self):
        """每个新K线触发"""
        # 短期均线上穿长期均线 - 买入信号
        if crossover(self.sma_short, self.sma_long):
            self.buy()
        
        # 短期均线下穿长期均线 - 卖出信号
        elif crossover(self.sma_long, self.sma_short):
            self.sell()


class SmaCrossWithFilters(Strategy):
    """
    带过滤条件的双均线策略
    
    增加了成交量和趋势过滤，减少震荡市假信号
    
    参数:
        n_short: 短期均线周期（默认10）
        n_long: 长期均线周期（默认20）
        volume_factor: 成交量倍数（默认1.5）
        trend_ma: 趋势判断均线（默认60）
    """
    
    n_short = 10
    n_long = 20
    volume_factor = 1.5  # 成交量需大于均量的倍数
    trend_ma = 60        # 趋势判断均线
    
    def init(self):
        """初始化指标"""
        close = pd.Series(self.data.Close)
        volume = pd.Series(self.data.Volume)
        
        # 均线
        self.sma_short = self.I(
            lambda: close.rolling(self.n_short).mean(),
            name=f'SMA({self.n_short})'
        )
        self.sma_long = self.I(
            lambda: close.rolling(self.n_long).mean(),
            name=f'SMA({self.n_long})'
        )
        self.sma_trend = self.I(
            lambda: close.rolling(self.trend_ma).mean(),
            name=f'Trend({self.trend_ma})'
        )
        
        # 成交量均线
        self.vol_ma = self.I(
            lambda: volume.rolling(20).mean(),
            name='Vol_MA(20)'
        )
    
    def next(self):
        """交易逻辑"""
        close = self.data.Close[-1]
        volume = self.data.Volume[-1]
        
        # 只在趋势向上时买入
        uptrend = close > self.sma_trend[-1]
        
        # 成交量确认
        volume_confirm = volume > self.vol_ma[-1] * self.volume_factor
        
        # 买入信号：金叉 + 趋势向上 + 成交量确认
        if crossover(self.sma_short, self.sma_long):
            if uptrend and volume_confirm:
                self.buy()
        
        # 卖出信号：死叉
        elif crossover(self.sma_long, self.sma_short):
            self.sell()


if __name__ == "__main__":
    print("SMA Cross 策略示例")
    print("=" * 50)
    print("""
使用说明:

1. 基本用法:
   from strategies import SmaCross
   
   # 运行回测
   results = run_backtest(
       data=df,
       strategy_class=SmaCross,
       n_short=10,  # 短期均线
       n_long=20    # 长期均线
   )

2. 参数优化:
   engine = BacktestEngine(df, SmaCross)
   opt_results = engine.optimize(
       n_short=range(5, 50),
       n_long=range(10, 100),
       maximize='Sharpe Ratio'
   )

3. 带过滤器的版本:
   from strategies.sma_cross import SmaCrossWithFilters
   
   results = run_backtest(
       data=df,
       strategy_class=SmaCrossWithFilters,
       n_short=10,
       n_long=20,
       volume_factor=1.5
   )
    """)
