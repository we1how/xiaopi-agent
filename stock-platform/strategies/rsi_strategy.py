#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI 相对强弱指标策略
基于超买超卖原理的动量策略

策略逻辑：
- RSI < 超卖线(30) 时买入
- RSI > 超买线(70) 时卖出
"""

from backtesting import Strategy
import pandas as pd
import numpy as np


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI 指标
    
    Args:
        prices: 价格序列
        period: RSI周期（默认14）
    
    Returns:
        RSI值序列
    """
    delta = prices.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


class RsiStrategy(Strategy):
    """
    RSI 超买超卖策略
    
    参数:
        period: RSI计算周期（默认14）
        oversold: 超卖阈值（默认30）
        overbought: 超买阈值（默认70）
    
    使用示例:
        from strategies import RsiStrategy
        results = run_backtest(df, RsiStrategy, period=14, oversold=30, overbought=70)
    """
    
    period = 14
    oversold = 30
    overbought = 70
    
    def init(self):
        """初始化 RSI 指标"""
        close = pd.Series(self.data.Close)
        self.rsi = self.I(
            lambda: calculate_rsi(close, self.period),
            name=f'RSI({self.period})'
        )
    
    def next(self):
        """交易逻辑"""
        # 获取当前 RSI 值
        current_rsi = self.rsi[-1]
        
        # 检查是否有持仓
        if not self.position:
            # RSI 低于超卖线 - 买入信号
            if current_rsi < self.oversold:
                self.buy()
        else:
            # RSI 高于超买线 - 卖出信号
            if current_rsi > self.overbought:
                self.sell()


class RsiWithMaFilter(Strategy):
    """
    RSI + 均线过滤策略
    
    在 RSI 策略基础上增加趋势过滤：
    - 只在价格高于均线时考虑买入（上升趋势）
    - 只在价格低于均线时考虑卖出（下降趋势）
    
    参数:
        period: RSI周期（默认14）
        oversold: 超卖线（默认30）
        overbought: 超买线（默认70）
        ma_period: 均线周期（默认50）
    """
    
    period = 14
    oversold = 30
    overbought = 70
    ma_period = 50
    
    def init(self):
        """初始化指标"""
        close = pd.Series(self.data.Close)
        
        # RSI
        self.rsi = self.I(
            lambda: calculate_rsi(close, self.period),
            name=f'RSI({self.period})'
        )
        
        # 移动平均线（趋势过滤）
        self.ma = self.I(
            lambda: close.rolling(self.ma_period).mean(),
            name=f'MA({self.ma_period})'
        )
    
    def next(self):
        """交易逻辑"""
        close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        
        # 上升趋势判断
        uptrend = close > self.ma[-1]
        
        if not self.position:
            # 超卖 + 上升趋势 = 买入
            if current_rsi < self.oversold and uptrend:
                self.buy()
        else:
            # 超买 + 下降趋势 = 卖出
            downtrend = close < self.ma[-1]
            if current_rsi > self.overbought or downtrend:
                self.sell()


class RsiDivergence(Strategy):
    """
    RSI 背离策略（进阶）
    
    检测价格与 RSI 的背离：
    - 底背离（价格新低，RSI未新低）-> 买入
    - 顶背离（价格新高，RSI未新高）-> 卖出
    
    参数:
        period: RSI周期（默认14）
        lookback: 背离检测回溯期（默认5）
    """
    
    period = 14
    lookback = 5
    
    def init(self):
        """初始化"""
        close = pd.Series(self.data.Close)
        self.rsi = self.I(
            lambda: calculate_rsi(close, self.period),
            name=f'RSI({self.period})'
        )
    
    def next(self):
        """交易逻辑"""
        if len(self.data.Close) < self.lookback + 1:
            return
        
        close = self.data.Close
        rsi = self.rsi
        
        # 获取回溯期数据
        recent_closes = list(close[-self.lookback-1:])
        recent_rsi = list(rsi[-self.lookback-1:])
        
        # 底背离检测：价格创新低但 RSI 未创新低
        price_lower_low = recent_closes[-1] < min(recent_closes[:-1])
        rsi_not_lower = recent_rsi[-1] > min(recent_rsi[:-1])
        
        # 顶背离检测：价格创新高但 RSI 未创新高
        price_higher_high = recent_closes[-1] > max(recent_closes[:-1])
        rsi_not_higher = recent_rsi[-1] < max(recent_rsi[:-1])
        
        if not self.position:
            if price_lower_low and rsi_not_lower:
                self.buy()
        else:
            if price_higher_high and rsi_not_higher:
                self.sell()


if __name__ == "__main__":
    print("RSI 策略示例")
    print("=" * 50)
    print("""
使用说明:

1. 基本 RSI 策略:
   from strategies import RsiStrategy
   
   results = run_backtest(
       data=df,
       strategy_class=RsiStrategy,
       period=14,
       oversold=30,
       overbought=70
   )

2. RSI + 均线过滤:
   from strategies.rsi_strategy import RsiWithMaFilter
   
   results = run_backtest(
       data=df,
       strategy_class=RsiWithMaFilter,
       period=14,
       ma_period=50
   )

3. RSI 背离策略:
   from strategies.rsi_strategy import RsiDivergence
   
   results = run_backtest(
       data=df,
       strategy_class=RsiDivergence,
       period=14,
       lookback=5
   )
    """)
