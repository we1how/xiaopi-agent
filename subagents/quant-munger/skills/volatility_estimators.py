"""
OHLC Range-Based Volatility Estimators
=====================================
基于Arxiv:2603.02898的波动率估计器实现
适用于A股市场的市场压力监测

四种经典估计器：
1. Parkinson (1980) - 仅使用高低点
2. Garman-Klass (1980) - 使用OHLC，假设无漂移
3. Rogers-Satchell (1991) - 允许漂移，更稳健
4. Yang-Zhang (2000) - 综合隔夜和日内波动，最推荐

作者: quant-munger
日期: 2026-03-05
"""

import numpy as np
import pandas as pd
from typing import Union, Optional


def parkinson_volatility(high: np.ndarray, low: np.ndarray, 
                         annualize: bool = True, 
                         trading_periods: int = 252) -> np.ndarray:
    """
    Parkinson波动率估计器 (1980)
    
    仅使用日内最高价和最低价，假设价格服从几何布朗运动无漂移
    效率约为Close-to-Close估计器的5.2倍
    
    公式: σ² = (ln(H/L))² / (4·ln2)
    
    Parameters:
    -----------
    high : np.ndarray - 最高价序列
    low : np.ndarray - 最低价序列  
    annualize : bool - 是否年化
    trading_periods : int - 年交易周期数（日频252，月频12）
    
    Returns:
    --------
    np.ndarray - 波动率序列
    """
    log_hl = np.log(high / low)
    variance = (log_hl ** 2) / (4 * np.log(2))
    
    if annualize:
        return np.sqrt(variance * trading_periods)
    return np.sqrt(variance)


def garman_klass_volatility(open_: np.ndarray, high: np.ndarray, 
                            low: np.ndarray, close: np.ndarray,
                            annualize: bool = True,
                            trading_periods: int = 252) -> np.ndarray:
    """
    Garman-Klass波动率估计器 (1980)
    
    使用完整的OHLC数据，假设无漂移，是Parkinson的改进版
    效率约为Close-to-Close的7.4倍
    
    公式: σ² = 0.5·(ln(H/L))² - (2ln2-1)·(ln(C/O))²
    
    Parameters:
    -----------
    open_ : np.ndarray - 开盘价序列
    high : np.ndarray - 最高价序列
    low : np.ndarray - 最低价序列
    close : np.ndarray - 收盘价序列
    annualize : bool - 是否年化
    trading_periods : int - 年交易周期数
    
    Returns:
    --------
    np.ndarray - 波动率序列
    """
    log_hl = np.log(high / low)
    log_co = np.log(close / open_)
    
    variance = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
    variance = np.maximum(variance, 0)  # 防止数值误差
    
    if annualize:
        return np.sqrt(variance * trading_periods)
    return np.sqrt(variance)


def rogers_satchell_volatility(open_: np.ndarray, high: np.ndarray,
                               low: np.ndarray, close: np.ndarray,
                               annualize: bool = True,
                               trading_periods: int = 252) -> np.ndarray:
    """
    Rogers-Satchell波动率估计器 (1991)
    
    允许存在价格漂移，更稳健，对趋势不敏感
    
    公式: σ² = ln(H/C)·ln(H/O) + ln(L/C)·ln(L/O)
    
    Parameters:
    -----------
    open_, high, low, close : np.ndarray - OHLC序列
    annualize : bool - 是否年化
    trading_periods : int - 年交易周期数
    
    Returns:
    --------
    np.ndarray - 波动率序列
    """
    log_hc = np.log(high / close)
    log_ho = np.log(high / open_)
    log_lc = np.log(low / close)
    log_lo = np.log(low / open_)
    
    variance = log_hc * log_ho + log_lc * log_lo
    variance = np.maximum(variance, 0)
    
    if annualize:
        return np.sqrt(variance * trading_periods)
    return np.sqrt(variance)


def yang_zhang_volatility(open_: np.ndarray, high: np.ndarray,
                          low: np.ndarray, close: np.ndarray,
                          window: int = 30,
                          annualize: bool = True,
                          trading_periods: int = 252) -> np.ndarray:
    """
    Yang-Zhang波动率估计器 (2000) - 推荐默认使用
    
    综合隔夜跳盘波动和日内波动，最全面且稳健
    效率约为Close-to-Close的14倍
    
    公式: σ²_yz = σ²_overnight + k·σ²_open_close + (1-k)·σ²_rs
    
    其中k = 0.34 / (1.34 + (n+1)/(n-1))，n为窗口期
    
    Parameters:
    -----------
    open_, high, low, close : np.ndarray - OHLC序列
    window : int - 滚动窗口期（默认30）
    annualize : bool - 是否年化
    trading_periods : int - 年交易周期数
    
    Returns:
    --------
    np.ndarray - 波动率序列（前window期为NaN）
    """
    n = window
    
    # 隔夜跳盘波动 ( Overnight variance )
    log_oc_prev = np.log(open_[1:] / close[:-1])
    overnight_var = pd.Series(log_oc_prev ** 2).rolling(window=n).mean()
    overnight_var = np.concatenate([[np.nan] * (n+1), overnight_var.values[n:]])
    
    # 开盘收盘波动 ( Open-Close variance )
    log_oc = np.log(close / open_)
    oc_var = pd.Series(log_oc ** 2).rolling(window=n).mean()
    
    # Rogers-Satchell波动
    rs_vol = rogers_satchell_volatility(open_, high, low, close, annualize=False)
    rs_var = pd.Series(rs_vol ** 2).rolling(window=n).mean()
    
    # 最优权重k
    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    
    # 组合波动率
    variance = overnight_var + k * oc_var + (1 - k) * rs_var
    variance = np.maximum(variance, 0)
    
    if annualize:
        return np.sqrt(variance * trading_periods)
    return np.sqrt(variance)


def detect_market_stress(volatility: np.ndarray, 
                        quantile: float = 0.95,
                        min_periods: int = 60) -> pd.Series:
    """
    市场压力检测 - 基于滚动分位数阈值
    
    根据Arxiv:2603.02898的方法，当波动率超过历史滚动分位数时标记为压力期
    
    Parameters:
    -----------
    volatility : np.ndarray - 波动率序列
    quantile : float - 分位数阈值（默认95%）
    min_periods : int - 最小观察期数
    
    Returns:
    --------
    pd.Series - 布尔序列，True表示压力期
    """
    vol_series = pd.Series(volatility)
    rolling_threshold = vol_series.rolling(window=min_periods, min_periods=min_periods//2).quantile(quantile)
    stress_signal = vol_series > rolling_threshold
    return stress_signal


def calculate_all_volatilities(df: pd.DataFrame,
                               open_col: str = 'open',
                               high_col: str = 'high', 
                               low_col: str = 'low',
                               close_col: str = 'close',
                               window: int = 30) -> pd.DataFrame:
    """
    计算所有四种波动率估计器的便捷函数
    
    Parameters:
    -----------
    df : pd.DataFrame - 包含OHLC列的数据框
    open_col, high_col, low_col, close_col : str - 列名
    window : int - Yang-Zhang的窗口期
    
    Returns:
    --------
    pd.DataFrame - 包含各波动率估计器的原始数据框
    """
    o = df[open_col].values
    h = df[high_col].values
    l = df[low_col].values
    c = df[close_col].values
    
    result = df.copy()
    result['vol_parkinson'] = parkinson_volatility(h, l)
    result['vol_garman_klass'] = garman_klass_volatility(o, h, l, c)
    result['vol_rogers_satchell'] = rogers_satchell_volatility(o, h, l, c)
    result['vol_yang_zhang'] = yang_zhang_volatility(o, h, l, c, window=window)
    
    return result


# ============ A股专用示例 ============

def demo_a_share_usage():
    """
    A股使用示例
    
    假设数据来自Tushare/AkShare，包含沪深300指数的OHLC数据
    """
    print("=" * 60)
    print("A股市场压力监测 - OHLC波动率估计器")
    print("=" * 60)
    
    # 模拟沪深300指数的30天OHLC数据
    np.random.seed(42)
    n = 30
    base_price = 3800
    
    # 生成模拟OHLC数据
    close = base_price + np.cumsum(np.random.randn(n) * 20)
    open_ = close + np.random.randn(n) * 10
    high = np.maximum(open_, close) + np.random.uniform(5, 25, n)
    low = np.minimum(open_, close) - np.random.uniform(5, 25, n)
    
    # 计算四种波动率
    vol_p = parkinson_volatility(high, low, annualize=False)
    vol_gk = garman_klass_volatility(open_, high, low, close, annualize=False)
    vol_rs = rogers_satchell_volatility(open_, high, low, close, annualize=False)
    vol_yz = yang_zhang_volatility(open_, high, low, close, window=10, annualize=False)
    
    # 转换为numpy数组以便使用负索引
    vol_p = np.array(vol_p)
    vol_gk = np.array(vol_gk)
    vol_rs = np.array(vol_rs)
    vol_yz = np.array(vol_yz)
    
    print(f"\n最近5日波动率对比 (日波动率):")
    print(f"{'日期':>6} {'Parkinson':>12} {'Garman-Klass':>14} {'Rogers-Satchell':>16} {'Yang-Zhang':>12}")
    print("-" * 70)
    for i in range(-5, 0):
        yz_val = vol_yz[i] if not np.isnan(vol_yz[i]) else 0
        print(f"Day{i+6:>3} {vol_p[i]:>12.4f} {vol_gk[i]:>14.4f} {vol_rs[i]:>16.4f} {yz_val:>12.4f}")
    
    print(f"\n推荐: Yang-Zhang波动率在响应性和稳健性间取得最佳平衡")
    print(f"应用建议:")
    print(f"  1. 当vol_yang_zhang > 历史95%分位数 → 市场压力信号")
    print(f"  2. 结合成交量萎缩确认流动性风险")
    print(f"  3. 可用于控制仓位/调整止损")


if __name__ == "__main__":
    demo_a_share_usage()
