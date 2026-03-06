#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超跌股票扫描器

全市场扫描符合超跌反弹条件的股票

功能:
1. 全市场扫描
2. 单只股票检查
3. 结果导出
4. 参数灵活配置

作者: 量化研究组
版本: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from data_loader import StockDataLoader


@dataclass
class OversoldCandidate:
    """
    超跌候选股票数据结构

    包含股票基本信息和技术指标
    """
    # 基本信息
    code: str                      # 股票代码
    name: str = ""                 # 股票名称
    industry: str = ""             # 所属行业

    # 价格信息
    current_price: float = 0.0     # 当前价格
    high_lookback: float = 0.0     # 观察期内最高价
    low_lookback: float = 0.0      # 观察期内最低价

    # 跌幅指标
    drawdown: float = 0.0          # 当前跌幅（负值）
    drawdown_pct: float = 0.0      # 跌幅百分比（正值表示下跌幅度）

    # 反弹指标
    bounce_from_low: float = 0.0   # 从最低点反弹幅度
    distance_to_resistance: float = 0.0  # 距前期高点的距离（反弹空间）

    # 成交量指标
    volume_ratio: float = 0.0      # 20日均量 / 60日均量
    volume_contracted: bool = False  # 是否成交量萎缩

    # 状态
    is_oversold: bool = False      # 是否满足超跌条件
    meet_all_conditions: bool = False  # 是否满足所有条件（可买入）

    # 时间戳
    scan_date: str = ""            # 扫描日期
    lookback_period: int = 120     # 观察周期
    bounce_trigger_date: str = ""  # 反弹触发日期（买入信号日期）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_display_dict(self) -> Dict[str, Any]:
        """转换为展示用的字典（格式化数值）"""
        return {
            '股票代码': self.code,
            '股票名称': self.name if self.name else '-',
            '所属行业': self.industry if self.industry else '-',
            '当前价格': f"{self.current_price:.2f}" if self.current_price > 0 else "-",
            '距前高跌幅 📉': f"{self.drawdown_pct:.1f}%",
            '从低点反弹 📈': f"{self.bounce_from_low:.1f}%",
            '反弹触发日期 📅': self.bounce_trigger_date if self.bounce_trigger_date else '-',
            '潜在上涨空间 🎯': f"{self.distance_to_resistance:.1f}%",
            '成交量比 📊': f"{self.volume_ratio:.1f}%",
            '缩量确认 ✅': "是" if self.volume_contracted else "否",
            '满足条件 🚀': "✅ 可买入" if self.meet_all_conditions else "❌ 观察中",
        }


class OversoldScanner:
    """
    超跌股票扫描器

    全市场扫描符合超跌反弹条件的股票

    示例:
        scanner = OversoldScanner()
        candidates = scanner.scan_all_stocks(
            drawdown_threshold=0.40,
            lookback_period=120,
            bounce_ratio=0.125,
            enable_volume_filter=True,
            volume_contraction=0.70
        )

        # 导出结果
        scanner.export_results(candidates, "oversold_scan_20240301.csv")
    """

    def __init__(self, data_loader: Optional[StockDataLoader] = None):
        """
        初始化扫描器

        Args:
            data_loader: 数据加载器实例（可选）
        """
        self.data_loader = data_loader or StockDataLoader()
        self.scan_results: List[OversoldCandidate] = []
        self.scan_date = datetime.now().strftime('%Y-%m-%d')

    def scan_single_stock(
        self,
        code: str,
        drawdown_threshold: float = 0.40,
        lookback_period: int = 120,
        bounce_ratio: float = 0.125,
        enable_volume_filter: bool = True,
        volume_contraction: float = 0.70,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[OversoldCandidate]:
        """
        检查单只股票是否符合超跌条件

        Args:
            code: 股票代码
            drawdown_threshold: 跌幅阈值
            lookback_period: 观察周期（计算跌幅的天数）
            bounce_ratio: 买入反弹比例
            enable_volume_filter: 是否启用成交量过滤
            volume_contraction: 成交量萎缩阈值
            start_date: 开始日期（数据获取范围）
            end_date: 结束日期（数据获取范围，默认今天）

        Returns:
            OversoldCandidate 或 None
        """
        try:
            # 默认日期范围
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                # 默认获取比观察周期多30天的数据，确保有足够数据计算指标
                start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=lookback_period + 60)).strftime('%Y-%m-%d')

            # 获取股票数据
            df = self.data_loader.get_stock_data(code, start_date, end_date)

            if df.empty or len(df) < 60:  # 至少需要60天数据
                return None

            # 如果数据不足lookback_period，使用实际可用天数
            actual_lookback = min(lookback_period, len(df))

            # 获取股票基本信息
            stock_info = self.data_loader.get_stock_info(code)
            name = stock_info.get('name', '') if stock_info is not None else ''
            industry = stock_info.get('industry', '') if stock_info is not None else ''

            # 计算指标
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']
            current_price = close.iloc[-1]

            # 观察期内的高低点（使用实际可用天数，使用盘中最高/最低价）
            high_lookback = high.rolling(actual_lookback).max().iloc[-1]
            low_lookback = low.rolling(actual_lookback).min().iloc[-1]

            # 当前跌幅
            drawdown = (current_price - high_lookback) / high_lookback if high_lookback != 0 else 0
            drawdown_pct = abs(drawdown) * 100

            # 从最低点反弹幅度
            bounce_from_low = (current_price - low_lookback) / low_lookback if low_lookback != 0 else 0

            # 距前期高点的距离（反弹空间）
            distance_to_resistance = (high_lookback - current_price) / current_price if current_price != 0 else 0

            # 成交量萎缩检查
            vol_sma_20 = volume.rolling(20).mean().iloc[-1]
            vol_sma_60 = volume.rolling(60).mean().iloc[-1]
            volume_ratio = (vol_sma_20 / vol_sma_60 * 100) if vol_sma_60 != 0 else 100
            volume_contracted = volume_ratio < (volume_contraction * 100)

            # 是否满足超跌条件
            is_oversold = drawdown <= -drawdown_threshold

            # 是否满足所有买入条件
            meet_conditions = [
                is_oversold,
                bounce_from_low >= bounce_ratio,
            ]
            if enable_volume_filter:
                meet_conditions.append(volume_contracted)

            meet_all_conditions = all(meet_conditions)

            # 计算反弹触发日期：从后向前遍历，找到首次满足反弹条件的那一天
            bounce_trigger_date = ""
            if meet_all_conditions:
                # 从最后一天向前遍历
                for i in range(len(df) - 1, -1, -1):
                    # 计算截至当前日期的最低点
                    current_low = low.iloc[:i+1].min() if i > 0 else low.iloc[0]
                    current_close = close.iloc[i]
                    # 计算截至当前日期的反弹幅度
                    current_bounce = (current_close - current_low) / current_low if current_low != 0 else 0

                    # 如果当前反弹幅度小于阈值，说明已经找到了触发点的前一天
                    if current_bounce < bounce_ratio:
                        # 触发日期是下一天（即首次满足条件的那一天）
                        if i < len(df) - 1:
                            trigger_idx = i + 1
                            bounce_trigger_date = df.index[trigger_idx].strftime('%Y-%m-%d')
                        break
                    # 如果遍历到开头都满足条件，则触发日期就是第一天
                    elif i == 0:
                        bounce_trigger_date = df.index[0].strftime('%Y-%m-%d')

            return OversoldCandidate(
                code=code,
                name=name,
                industry=industry,
                current_price=current_price,
                high_lookback=high_lookback,
                low_lookback=low_lookback,
                drawdown=drawdown,
                drawdown_pct=drawdown_pct,
                bounce_from_low=bounce_from_low * 100,  # 转为百分比
                distance_to_resistance=distance_to_resistance * 100,
                volume_ratio=volume_ratio,
                volume_contracted=volume_contracted,
                is_oversold=is_oversold,
                meet_all_conditions=meet_all_conditions,
                scan_date=self.scan_date,
                lookback_period=lookback_period,
                bounce_trigger_date=bounce_trigger_date,
            )

        except Exception as e:
            # print(f"扫描 {code} 失败: {e}")
            return None

    def scan_all_stocks(
        self,
        stock_list: Optional[List[str]] = None,
        drawdown_threshold: float = 0.40,
        lookback_period: int = 120,
        bounce_ratio: float = 0.125,
        enable_volume_filter: bool = True,
        volume_contraction: float = 0.70,
        max_stocks: Optional[int] = None,
        min_price: float = 2.0,  # 最低价格过滤（排除仙股）
        progress_callback: Optional[callable] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[OversoldCandidate]:
        """
        全市场扫描

        Args:
            stock_list: 股票列表（默认从数据库获取全部）
            drawdown_threshold: 跌幅阈值
            lookback_period: 观察周期
            bounce_ratio: 买入反弹比例
            enable_volume_filter: 是否启用成交量过滤
            volume_contraction: 成交量萎缩阈值
            max_stocks: 最大扫描数量（用于测试）
            min_price: 最低价格过滤
            progress_callback: 进度回调函数(current, total)
            start_date: 扫描开始日期 (YYYY-MM-DD)
            end_date: 扫描结束日期 (YYYY-MM-DD)

        Returns:
            候选股票列表
        """
        # 保存日期参数供单只股票扫描使用
        self.scan_start_date = start_date
        self.scan_end_date = end_date
        # 获取股票列表
        if stock_list is None:
            stocks_df = self.data_loader.get_available_stocks(limit=10000)
            stock_list = stocks_df['code'].tolist() if 'code' in stocks_df.columns else []

        if max_stocks:
            stock_list = stock_list[:max_stocks]

        print(f"开始扫描 {len(stock_list)} 只股票...")
        print(f"参数: 跌幅阈值={drawdown_threshold:.1%}, 观察周期={lookback_period}日, 反弹比例={bounce_ratio:.1%}")

        # 统计信息
        stats = {
            'total': len(stock_list),
            'no_data': 0,
            'data_insufficient': 0,
            'not_oversold': 0,
            'no_bounce': 0,
            'no_volume': 0,
            'low_price': 0,
            'passed': 0,
        }

        candidates = []
        total = len(stock_list)

        print(f"开始扫描 {len(stock_list)} 只股票...")
        print(f"参数: 跌幅阈值={drawdown_threshold:.1%}, 观察周期={lookback_period}日, 反弹比例={bounce_ratio:.1%}")

        # 由于DuckDB连接不是线程安全的，使用单线程但批量处理
        # 每50只股票批量查询基本信息，减少数据库访问次数
        batch_size = 50

        for i, code in enumerate(stock_list):
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total)

            # 每50只打印一次进度
            if (i + 1) % 50 == 0:
                print(f"  进度: {i + 1}/{total} ({(i + 1) / total * 100:.1f}%)")

            # 扫描单只股票
            candidate = self.scan_single_stock(
                code=code,
                drawdown_threshold=drawdown_threshold,
                lookback_period=lookback_period,
                bounce_ratio=bounce_ratio,
                enable_volume_filter=enable_volume_filter,
                volume_contraction=volume_contraction,
                start_date=start_date,
                end_date=end_date,
            )

            # 统计筛选原因
            if candidate is None:
                stats['no_data'] += 1
            elif candidate.current_price < min_price:
                stats['low_price'] += 1
            elif not candidate.is_oversold:
                stats['not_oversold'] += 1
            elif candidate.bounce_from_low < bounce_ratio * 100:
                stats['no_bounce'] += 1
            elif enable_volume_filter and not candidate.volume_contracted:
                stats['no_volume'] += 1
            else:
                stats['passed'] += 1
                candidates.append(candidate)

        # 按跌幅排序（跌幅大的排前面）
        candidates.sort(key=lambda x: x.drawdown)

        self.scan_results = candidates

        # 打印详细统计
        print(f"\n" + "="*50)
        print(f"扫描统计:")
        print(f"  - 扫描总数: {stats['total']}")
        print(f"  - 无数据/数据不足: {stats['no_data']}")
        print(f"  - 价格过低(<{min_price}元): {stats['low_price']}")
        print(f"  - 未超跌: {stats['not_oversold']}")
        print(f"  - 未反弹: {stats['no_bounce']}")
        print(f"  - 成交量不符: {stats['no_volume']}")
        print(f"  - 符合条件: {stats['passed']}")
        print(f"="*50)

        return candidates

    def get_buy_candidates(self, min_drawdown: float = 0.35) -> List[OversoldCandidate]:
        """
        获取可买入的候选股票（满足所有条件）

        Args:
            min_drawdown: 最小跌幅要求

        Returns:
            可买入的候选列表
        """
        return [
            c for c in self.scan_results
            if c.meet_all_conditions and c.drawdown_pct >= min_drawdown * 100
        ]

    def get_oversold_watchlist(self, min_drawdown: float = 0.30) -> List[OversoldCandidate]:
        """
        获取观察列表（仅满足超跌条件，不一定满足买入条件）

        Args:
            min_drawdown: 最小跌幅要求

        Returns:
            观察列表
        """
        return [
            c for c in self.scan_results
            if c.is_oversold and c.drawdown_pct >= min_drawdown * 100
        ]

    def export_results(
        self,
        candidates: List[OversoldCandidate],
        filename: Optional[str] = None,
        output_dir: str = "./scan_results"
    ) -> str:
        """
        导出扫描结果到CSV

        Args:
            candidates: 候选列表
            filename: 文件名（默认自动生成）
            output_dir: 输出目录

        Returns:
            保存的文件路径
        """
        if not candidates:
            print("没有候选股票可导出")
            return ""

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"oversold_scan_{timestamp}.csv"

        filepath = output_path / filename

        # 转换为DataFrame
        data = [c.to_dict() for c in candidates]
        df = pd.DataFrame(data)

        # 保存
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"结果已保存: {filepath}")

        return str(filepath)

    def get_summary(self) -> Dict[str, Any]:
        """获取扫描结果摘要"""
        if not self.scan_results:
            return {}

        total = len(self.scan_results)
        buyable = len([c for c in self.scan_results if c.meet_all_conditions])
        avg_drawdown = np.mean([c.drawdown_pct for c in self.scan_results])
        avg_bounce = np.mean([c.bounce_from_low for c in self.scan_results])

        return {
            'scan_date': self.scan_date,
            'total_candidates': total,
            'buyable_candidates': buyable,
            'watch_only': total - buyable,
            'avg_drawdown': avg_drawdown,
            'avg_bounce': avg_bounce,
        }

    def close(self):
        """关闭数据连接"""
        if self.data_loader:
            self.data_loader.close()


# ========== 便捷函数 ==========

def scan_oversold_stocks(
    stock_list: Optional[List[str]] = None,
    drawdown_threshold: float = 0.40,
    lookback_period: int = 120,
    bounce_ratio: float = 0.125,
    enable_volume_filter: bool = True,
    volume_contraction: float = 0.70,
    max_stocks: Optional[int] = None,
) -> Tuple[List[OversoldCandidate], Dict[str, Any]]:
    """
    便捷函数：扫描超跌股票

    Returns:
        (候选列表, 摘要信息)
    """
    scanner = OversoldScanner()
    try:
        candidates = scanner.scan_all_stocks(
            stock_list=stock_list,
            drawdown_threshold=drawdown_threshold,
            lookback_period=lookback_period,
            bounce_ratio=bounce_ratio,
            enable_volume_filter=enable_volume_filter,
            volume_contraction=volume_contraction,
            max_stocks=max_stocks,
        )
        summary = scanner.get_summary()
        return candidates, summary
    finally:
        scanner.close()


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 70)
    print("超跌股票扫描器测试")
    print("=" * 70)

    # 测试扫描器创建
    print("\n✅ 扫描器创建成功")
    scanner = OversoldScanner()

    # 测试单只股票检查（使用已知股票代码）
    print("\n✅ 测试单只股票检查")
    test_codes = ['000001', '600519', '000858']  # 平安银行、茅台、五粮液

    for code in test_codes:
        print(f"\n  检查 {code}...")
        candidate = scanner.scan_single_stock(
            code=code,
            drawdown_threshold=0.40,
            lookback_period=120,
        )
        if candidate:
            print(f"    名称: {candidate.name}")
            print(f"    价格: {candidate.current_price:.2f}")
            print(f"    跌幅: {candidate.drawdown_pct:.1f}%")
            print(f"    超跌: {'是' if candidate.is_oversold else '否'}")
        else:
            print(f"    无数据或检查失败")

    scanner.close()

    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)
