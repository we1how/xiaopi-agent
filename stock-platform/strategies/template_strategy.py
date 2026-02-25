#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例策略模板
用户可参考此模板创建自定义策略
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np


class MyCustomStrategy(Strategy):
    """
    自定义策略模板
    
    说明:
    1. 继承自 backtesting.Strategy
    2. 必须实现 init() 和 next() 方法
    3. 可在类级别定义可调参数
    
    策略逻辑:
    - 在这里描述你的交易策略
    - 买入条件: ...
    - 卖出条件: ...
    """
    
    # ========== 策略参数（可在回测时调整）==========
    param1 = 10  # 参数1说明
    param2 = 20  # 参数2说明
    
    # ========== 初始化方法 ==========
    def init(self):
        """
        初始化指标
        
        此方法在回测开始前调用一次
        用于计算技术指标
        """
        # 获取收盘价序列
        close = pd.Series(self.data.Close)
        
        # 示例：计算移动平均线
        self.ma1 = self.I(
            lambda: close.rolling(self.param1).mean(),
            name=f'MA{self.param1}'
        )
        self.ma2 = self.I(
            lambda: close.rolling(self.param2).mean(),
            name=f'MA{self.param2}'
        )
    
    # ========== 交易逻辑 ==========
    def next(self):
        """
        每个新K线触发此方法
        
        在此实现交易逻辑：
        - self.buy()  # 开多仓
        - self.sell() # 开空仓（如允许）
        - self.position.close()  # 平仓
        """
        # 示例：均线金叉买入，死叉卖出
        
        # 如果没有持仓
        if not self.position:
            # 短期均线上穿长期均线（金叉）
            if crossover(self.ma1, self.ma2):
                self.buy()
        
        # 如果持有多仓
        else:
            # 短期均线下穿长期均线（死叉）
            if crossover(self.ma2, self.ma1):
                self.sell()
    
    # ========== 可选：辅助方法 ==========
    def log(self, message):
        """打印日志"""
        timestamp = self.data.index[-1]
        print(f"[{timestamp}] {message}")


# ========== 策略变体示例 ==========

class MyStrategyWithStopLoss(Strategy):
    """
    带止损的策略示例
    
    参数:
        ma_period: 均线周期
        stop_loss_pct: 止损百分比（如0.02表示2%）
        take_profit_pct: 止盈百分比
    """
    
    ma_period = 20
    stop_loss_pct = 0.02
    take_profit_pct = 0.05
    
    def init(self):
        close = pd.Series(self.data.Close)
        self.ma = self.I(
            lambda: close.rolling(self.ma_period).mean(),
            name=f'MA({self.ma_period})'
        )
    
    def next(self):
        price = self.data.Close[-1]
        
        if not self.position:
            # 价格突破均线买入
            if price > self.ma[-1]:
                self.buy(
                    sl=price * (1 - self.stop_loss_pct),      # 止损价
                    tp=price * (1 + self.take_profit_pct)     # 止盈价
                )
        else:
            # 价格跌破均线卖出
            if price < self.ma[-1]:
                self.position.close()


class MyStrategyWithPositionSizing(Strategy):
    """
    带仓位管理的策略示例
    
    参数:
        risk_pct: 每笔交易风险资金比例
        atr_period: ATR计算周期
    """
    
    risk_pct = 0.02  # 每笔交易风险2%资金
    atr_period = 14
    
    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        
        # 计算 ATR
        self.atr = self.I(
            lambda: self._calculate_atr(high, low, close, self.atr_period),
            name=f'ATR({self.atr_period})'
        )
    
    def _calculate_atr(self, high, low, close, period):
        """计算 ATR 指标"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    def next(self):
        if not self.position:
            # 简单的买入信号示例
            if self.data.Close[-1] > self.data.Open[-1]:
                # 根据 ATR 计算仓位大小
                atr_value = self.atr[-1]
                if atr_value > 0:
                    risk_amount = self.equity * self.risk_pct
                    stop_distance = 2 * atr_value  # 2倍ATR止损
                    size = int(risk_amount / stop_distance)
                    
                    if size > 0:
                        self.buy(size=size)


# ========== 使用说明 ==========
"""
如何在回测平台使用自定义策略:

1. 编写策略文件（如 my_strategy.py）
2. 在 Streamlit 界面选择"上传策略文件"
3. 上传你的 .py 文件
4. 系统会自动加载策略类

注意事项:
- 策略类必须继承自 backtesting.Strategy
- 必须实现 init() 和 next() 方法
- 类级别的参数会自动识别为可调参数
- 可以使用 self.buy(), self.sell(), self.position.close() 进行交易

可用数据:
- self.data.Open   - 开盘价
- self.data.High   - 最高价
- self.data.Low    - 最低价
- self.data.Close  - 收盘价
- self.data.Volume - 成交量

常用方法:
- self.I()         - 注册指标（会在图表上显示）
- crossover(a, b)  - 判断 a 是否上穿 b
- self.equity      - 当前权益
- self.position    - 当前持仓信息
"""

if __name__ == "__main__":
    print("自定义策略模板")
    print("=" * 50)
    print("这是一个策略模板文件，展示了如何创建自定义策略。")
    print("请复制此文件并根据需要修改策略逻辑。")
