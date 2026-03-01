"""
信号提取模块

实现细粒度的技术指标提取，支持分层决策架构

核心思想：
1. 预计算所有指标（代码计算 > LLM计算）
2. 所有指标归一化（Z-score/RoC）
3. 消除价格偏见，实现跨标的可比性
"""

from .extractor import SignalExtractor, TechnicalSignals

__all__ = ['SignalExtractor', 'TechnicalSignals']
