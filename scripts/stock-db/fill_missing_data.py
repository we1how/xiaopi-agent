#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失的历史数据
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
import duckdb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path('~/StockData/logs/fill_missing.log').expanduser()),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataFiller:
    def __init__(self, base_path: str = "~/StockData"):
        self.base_path = Path(base_path).expanduser()
        self.parquet_path = self.base_path / "parquet"
        self.db_path = self.base_path / "stock.duckdb"
        self._init_data_sources()

    def _init_data_sources(self):
        self.ak = None
        self.bs = None

        try:
            import akshare as ak
            self.ak = ak
            logger.info("✅ akshare 已加载")
        except ImportError:
            logger.warning("⚠️ akshare 未安装")

        try:
            import baostock as bs
            self.bs = bs
            logger.info("✅ baostock 已加载")
        except ImportError:
            logger.warning("⚠️ baostock 未安装")

    def check_missing_dates(self, days_back: int = 10) -> List[str]:
        """检查缺失数据的日期"""
        conn = duckdb.connect(str(self.db_path))

        # 获取最近N天每天的数据量
        recent_data = conn.execute(f"""
            SELECT
                trade_date::DATE as date,
                COUNT(*) as count
            FROM daily
            WHERE trade_date >= CURRENT_DATE - INTERVAL '{days_back} days'
            GROUP BY trade_date
            ORDER BY trade_date DESC
        """).fetchall()

        conn.close()

        # 预期每交易日应该有 4000-6000 条记录
        missing_dates = []
        for date, count in recent_data:
            if count < 1000:  # 数据量不足，视为缺失
                missing_dates.append(str(date))
                logger.warning(f"⚠️ {date}: 只有 {count} 条记录，需要补充")

        return missing_dates

    def get_stock_list(self) -> List[str]:
        """从 parquet 文件获取股票列表，返回纯数字代码"""
        try:
            basic_path = self.parquet_path / "stock_basic.parquet"
            if basic_path.exists():
                df = pd.read_parquet(basic_path)
                # 尝试不同的列名
                codes = []
                if 'symbol' in df.columns:
                    codes = df['symbol'].tolist()
                elif '代码' in df.columns:
                    codes = df['代码'].tolist()

                # 统一转换为纯数字代码（去掉 sh./sz./bj. 前缀）
                clean_codes = []
                for code in codes:
                    if '.' in str(code):
                        # 提取数字部分，如 sh.600000 -> 600000
                        clean_codes.append(str(code).split('.')[1])
                    else:
                        clean_codes.append(str(code))

                # 只保留真正的A股股票代码
                # 上海: 600-609, 688, 689
                # 深圳: 000-004, 300-309, 301
                valid_prefixes = (
                    '600', '601', '603', '605', '688', '689',  # 上海
                    '000', '001', '002', '003', '300', '301'   # 深圳
                )
                stock_codes = [c for c in clean_codes if len(c) == 6 and c.isdigit() and c.startswith(valid_prefixes)]
                logger.info(f"获取到 {len(stock_codes)} 只股票（已过滤指数和基金）")
                return stock_codes
        except Exception as e:
            logger.warning(f"读取股票列表失败: {e}")

        # 回退到从 daily 分区读取
        try:
            conn = duckdb.connect(str(self.db_path))
            stocks = conn.execute("""
                SELECT DISTINCT ts_code FROM daily LIMIT 10000
            """).fetchall()
            conn.close()
            return [s[0] for s in stocks]
        except Exception as e:
            logger.error(f"从数据库获取股票列表失败: {e}")
            return []

    def fetch_and_save_stock(self, code: str, start_date: str, end_date: str) -> int:
        """获取单只股票的历史数据并保存"""
        try:
            # 使用 baostock
            if code.startswith(('6', '688', '689')):
                bs_code = f"sh.{code}"
            elif code.startswith(('8', '4')):
                bs_code = f"bj.{code}"
            else:
                bs_code = f"sz.{code}"

            lg = self.bs.login()
            if lg.error_code != '0':
                return 0

            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

            rs = self.bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2"
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            self.bs.logout()

            if not data_list:
                return 0

            df = pd.DataFrame(data_list, columns=rs.fields)
            df = df.rename(columns={
                'date': 'trade_date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'preclose': 'pre_close',
                'volume': 'vol',
                'amount': 'amount',
                'turn': 'turnover_rate',
                'pctChg': 'pct_chg',
            })

            # 转换数值类型
            for col in ['open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount', 'turnover_rate', 'pct_chg']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df['ts_code'] = code
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 保存到分区
            df['year'] = df['trade_date'].dt.year
            df['month'] = df['trade_date'].dt.month

            for (year, month), group in df.groupby(['year', 'month']):
                partition_path = self.parquet_path / "daily" / f"year={year}" / f"month={month:02d}"
                partition_path.mkdir(parents=True, exist_ok=True)

                parquet_file = partition_path / "data.parquet"

                if parquet_file.exists():
                    existing = pd.read_parquet(parquet_file)
                    combined = pd.concat([existing, group], ignore_index=True)
                    combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')
                    combined.to_parquet(parquet_file, index=False, compression='zstd')
                else:
                    group.to_parquet(parquet_file, index=False, compression='zstd')

            return len(df)

        except Exception as e:
            logger.error(f"获取 {code} 失败: {e}")
            return 0

    def fill_missing_data(self, start_date: str, end_date: str):
        """补充指定日期范围的数据"""
        logger.info("=" * 60)
        logger.info(f"🚀 开始补充数据: {start_date} ~ {end_date}")
        logger.info("=" * 60)

        # 获取股票列表
        stock_codes = self.get_stock_list()
        if not stock_codes:
            logger.error("❌ 无法获取股票列表")
            return

        logger.info(f"📊 共有 {len(stock_codes)} 只股票需要更新")

        total = len(stock_codes)
        success_count = 0
        failed_codes = []
        total_records = 0

        for i, code in enumerate(stock_codes):
            try:
                records = self.fetch_and_save_stock(code, start_date, end_date)
                if records > 0:
                    success_count += 1
                    total_records += records

                # 延时避免请求过快
                time.sleep(0.1)

                # 每50只报告进度
                if (i + 1) % 50 == 0:
                    logger.info(f"进度: {i+1}/{total}, 成功: {success_count}, 新增记录: {total_records}")

            except Exception as e:
                logger.error(f"更新 {code} 失败: {e}")
                failed_codes.append(code)

        logger.info("=" * 60)
        logger.info(f"✅ 补充完成!")
        logger.info(f"   成功: {success_count}/{total} 只股票")
        logger.info(f"   失败: {len(failed_codes)} 只股票")
        logger.info(f"   新增记录: {total_records} 条")
        logger.info("=" * 60)

        return {
            'success': success_count,
            'failed': len(failed_codes),
            'total_records': total_records
        }


if __name__ == "__main__":
    filler = DataFiller()

    # 只补充缺失的最近5个交易日（从2月27日到3月4日）
    # 排除周末：2/24周一有数据，2/25-2/26缺失严重，2/27周五，3/1-3/2周末，3/3-3/4周一二
    start_date = "20250227"
    end_date = datetime.now().strftime("%Y%m%d")

    logger.info(f"优化策略: 只补充 {start_date} ~ {end_date} (5个交易日)")
    logger.info(f"预计时间: ~1小时 (5399只股票 x 0.1秒)")

    result = filler.fill_missing_data(start_date, end_date)

    print("\n补充结果:")
    print(json.dumps(result, indent=2))
