#!/usr/bin/env python3
"""快速补充 - 只获取缺失的那几天数据，使用更高并发"""

import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class FastFiller:
    def __init__(self):
        self.parquet_path = Path("~/StockData/parquet").expanduser()
        self.stock_codes = self._get_stock_list()

    def _get_stock_list(self):
        basic_path = self.parquet_path / "stock_basic.parquet"
        df = pd.read_parquet(basic_path)
        codes = df['symbol'].tolist()
        clean_codes = [str(c).split('.')[1] if '.' in str(c) else str(c) for c in codes]
        valid_prefixes = ('600', '601', '603', '605', '688', '689', '000', '001', '002', '003', '300', '301')
        return [c for c in clean_codes if len(c) == 6 and c.isdigit() and c.startswith(valid_prefixes)]

    def fetch_stock(self, code, dates):
        """获取单只股票指定日期的数据"""
        try:
            if code.startswith(('6', '688', '689')):
                bs_code = f"sh.{code}"
            else:
                bs_code = f"sz.{code}"

            # 每次查询只获取缺失的那几天
            start = min(dates)
            end = max(dates)

            lg = bs.login()
            if lg.error_code != '0':
                return 0

            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
                start_date=start, end_date=end, frequency="d", adjustflag="2"
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            bs.logout()

            if not data_list:
                return 0

            df = pd.DataFrame(data_list, columns=rs.fields)
            df = df.rename(columns={
                'date': 'trade_date', 'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'preclose': 'pre_close', 'volume': 'vol',
                'amount': 'amount', 'turn': 'turnover_rate', 'pctChg': 'pct_chg',
            })
            for col in ['open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount', 'turnover_rate', 'pct_chg']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['ts_code'] = code
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 保存
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
            return 0

    def run(self):
        # 只补充最近5个交易日（3/3-3/4是周末后的交易日）
        target_dates = ['2026-03-04', '2026-03-03', '2026-03-02', '2026-02-27', '2026-02-26']
        logger.info(f"快速补充 {len(self.stock_codes)} 只股票，日期: {target_dates}")

        # 使用多线程，控制并发数
        success = 0
        total = 0
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.fetch_stock, code, target_dates): code for code in self.stock_codes}
            for future in as_completed(futures):
                code = futures[future]
                try:
                    records = future.result()
                    if records > 0:
                        success += 1
                        total += records
                except Exception as e:
                    pass

                if (success + len(self.stock_codes) - len(futures)) % 100 == 0:
                    logger.info(f"进度: {success} 只成功, {total} 条记录")

        logger.info(f"完成! {success}/{len(self.stock_codes)} 只成功, {total} 条记录")


if __name__ == "__main__":
    FastFiller().run()
