#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎模块
封装 backtesting.py 的回测功能
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Type, Union
from datetime import datetime
import traceback

from backtesting import Backtest, Strategy


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self, 
        data: pd.DataFrame,
        strategy_class: Type[Strategy],
        cash: float = 100000.0,
        commission: float = 0.001,
        margin: float = 1.0,
        trade_on_close: bool = False,
        hedging: bool = False,
        exclusive_orders: bool = False
    ):
        """
        初始化回测引擎
        
        Args:
            data: OHLCV 数据 DataFrame
            strategy_class: 策略类（继承自 backtesting.Strategy）
            cash: 初始资金
            commission: 手续费率（默认千分之一）
            margin: 保证金比例
            trade_on_close: 是否以收盘价成交
            hedging: 是否允许双向持仓
            exclusive_orders: 是否互斥订单
        """
        self.data = data
        self.strategy_class = strategy_class
        self.cash = cash
        self.commission = commission
        
        # 创建回测实例
        self.bt = Backtest(
            data=data,
            strategy=strategy_class,
            cash=cash,
            commission=commission,
            margin=margin,
            trade_on_close=trade_on_close,
            hedging=hedging,
            exclusive_orders=exclusive_orders
        )
        
        self.results = None
        self.stats = None
        self.strategy_instance = None  # 保存策略实例以访问决策历史
    
    def run(self, **strategy_params) -> Dict[str, Any]:
        """
        运行回测

        Args:
            **strategy_params: 策略参数

        Returns:
            回测结果字典
        """
        try:
            self.stats = self.bt.run(**strategy_params)

            # 保存策略实例（用于V2策略访问决策历史）
            # backtesting.py 将策略实例存储在 stats._strategy
            if hasattr(self.stats, '_strategy'):
                self.strategy_instance = self.stats._strategy
            
            # 转换为字典格式
            results = {
                'success': True,
                'start_date': str(self.data.index[0]),
                'end_date': str(self.data.index[-1]),
                'duration': len(self.data),
                'initial_cash': self.cash,
                'final_equity': float(self.stats.get('Equity Final [$]', 0)),
                'total_return': float(self.stats.get('Return [%]', 0)),
                'total_return_pct': f"{self.stats.get('Return [%]', 0):.2f}%",
                'buy_hold_return': float(self.stats.get('Buy & Hold Return [%]', 0)),
                'max_drawdown': float(self.stats.get('Max. Drawdown [%]', 0)),
                'max_drawdown_pct': f"{self.stats.get('Max. Drawdown [%]', 0):.2f}%",
                'sharpe_ratio': float(self.stats.get('Sharpe Ratio', 0)),
                'sortino_ratio': float(self.stats.get('Sortino Ratio', 0)),
                'calmar_ratio': float(self.stats.get('Calmar Ratio', 0)),
                'win_rate': float(self.stats.get('Win Rate [%]', 0)),
                'win_rate_pct': f"{self.stats.get('Win Rate [%]', 0):.2f}%",
                'total_trades': int(self.stats.get('# Trades', 0)),
                'avg_trade': float(self.stats.get('Avg. Trade [%]', 0)),
                'profit_factor': float(self.stats.get('Profit Factor', 0)) if 'Profit Factor' in self.stats else 0,
                'expectancy': float(self.stats.get('Expectancy [%]', 0)) if 'Expectancy [%]' in self.stats else 0,
                'sqn': float(self.stats.get('SQN', 0)) if 'SQN' in self.stats else 0,
                'exposure_time': f"{self.stats.get('Exposure Time [%]', 0):.2f}%" if 'Exposure Time [%]' in self.stats else "N/A",
            }
            
            self.results = results
            return results
            
        except Exception as e:
            error_msg = f"回测执行失败: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def optimize(
        self,
        maximize: str = 'SQN',
        constraint=None,
        max_tries: int = 100,
        **param_ranges
    ) -> Dict[str, Any]:
        """
        参数优化
        
        Args:
            maximize: 优化目标指标
            constraint: 约束条件函数
            max_tries: 最大尝试次数
            **param_ranges: 参数范围（如: n1=range(5, 50), n2=range(10, 100)）
        
        Returns:
            优化结果
        """
        try:
            opt_stats, heatmap = self.bt.optimize(
                maximize=maximize,
                constraint=constraint,
                max_tries=max_tries,
                return_heatmap=True,
                **param_ranges
            )
            
            return {
                'success': True,
                'best_params': opt_stats._strategy,
                'best_stats': dict(opt_stats),
                'heatmap': heatmap
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_equity_curve(self) -> pd.DataFrame:
        """
        获取权益曲线数据
        
        Returns:
            权益曲线 DataFrame
        """
        if self.stats is None:
            return pd.DataFrame()
        
        # 获取权益曲线
        equity = self.stats._equity_curve
        return equity
    
    def get_trades(self) -> pd.DataFrame:
        """
        获取交易记录
        
        Returns:
            交易记录 DataFrame
        """
        if self.stats is None:
            return pd.DataFrame()
        
        trades = self.stats._trades
        return trades
    
    def plot(self, filename: Optional[str] = None, **kwargs) -> str:
        """
        生成回测图表
        
        Args:
            filename: 输出文件名（HTML格式）
            **kwargs: 其他绘图参数
        
        Returns:
            HTML 文件路径或图表对象
        """
        if filename is None:
            filename = f"backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            self.bt.plot(filename=filename, **kwargs)
            return filename
        except Exception as e:
            print(f"绘图失败: {e}")
            return ""


def run_backtest(
    data: pd.DataFrame,
    strategy_class: Type[Strategy],
    cash: float = 100000.0,
    commission: float = 0.001,
    **strategy_params
) -> Dict[str, Any]:
    """
    便捷函数：运行回测
    
    Example:
        results = run_backtest(df, SmaCross, cash=100000, n1=10, n2=20)
    """
    engine = BacktestEngine(
        data=data,
        strategy_class=strategy_class,
        cash=cash,
        commission=commission
    )
    
    return engine.run(**strategy_params)


# 内置策略基类
class BaseStrategy(Strategy):
    """策略基类，提供一些通用功能"""
    
    def log(self, message: str):
        """记录日志"""
        timestamp = self.data.index[-1] if len(self.data.index) > 0 else None
        print(f"[{timestamp}] {message}")
    
    def get_position_size(self) -> int:
        """获取当前持仓数量"""
        return self.position.size if self.position else 0
    
    def is_long(self) -> bool:
        """是否持有多单"""
        return self.position.is_long if self.position else False
    
    def is_short(self) -> bool:
        """是否持有空单"""
        return self.position.is_short if self.position else False


if __name__ == "__main__":
    print("回测引擎测试...")
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='B')
    np.random.seed(42)
    
    test_data = pd.DataFrame({
        'Open': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'High': 102 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'Low': 98 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'Close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    # 确保 High >= Close >= Low
    test_data['High'] = test_data[['Open', 'Close', 'High']].max(axis=1)
    test_data['Low'] = test_data[['Open', 'Close', 'Low']].min(axis=1)
    
    print(f"测试数据: {len(test_data)} 条")
    print(test_data.head())
