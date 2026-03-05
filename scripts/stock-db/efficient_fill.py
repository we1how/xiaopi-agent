#!/usr/bin/env python3
"""高效补充 - 复用baostock连接"""
import time
import logging
from pathlib import Path
import pandas as pd
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EfficientFiller:
    def __init__(self):
        self.parquet_path = Path("~/StockData/parquet").expanduser()
        self.stock_codes = self._get_stock_list()
        self.completed = set()
        self._load_completed()

    def _get_stock_list(self):
        basic_path = self.parquet_path / "stock_basic.parquet"
        df = pd.read_parquet(basic_path)
        codes = df['symbol'].tolist()
        clean_codes = [str(c).split('.')[1] if '.' in str(c) else str(c) for c in codes]
        valid_prefixes = ('600', '601', '603', '605', '688', '689', '000', '001', '002', '003', '300', '301')
        return [c for c in clean_codes if len(c) == 6 and c.isdigit() and c.startswith(valid_prefixes)]

    def _load_completed(self):
        try:
            partition_path = self.parquet_path / "daily/year=2026/month=03/data.parquet"
            if partition_path.exists():
                df = pd.read_parquet(partition_path)
                self.completed.update(df['ts_code'].unique().tolist())
            partition_path2 = self.parquet_path / "daily/year=2026/month=02/data.parquet"
            if partition_path2.exists():
                df2 = pd.read_parquet(partition_path2)
                recent = df2[df2['trade_date'] >= '2026-02-27']
                self.completed.update(recent['ts_code'].unique().tolist())
            logger.info(f"已跳过 {len(self.completed)} 只已完成股票")
        except Exception as e:
            logger.warning(f"加载已完成股票失败: {e}")

    def run(self):
        remaining = [c for c in self.stock_codes if c not in self.completed]
        logger.info(f"共有 {len(self.stock_codes)} 只股票，已完成 {len(self.completed)} 只，剩余 {len(remaining)} 只需补充")

        if not remaining:
            logger.info("✅ 所有股票已补充完成！")
            return

        start = '2026-02-26'
        end = '2026-03-04'

        lg = bs.login()
        if lg.error_code != '0':
            logger.error("登录失败")
            return
        logger.info("✅ 已登录baostock，开始批量补充...")

        success = 0
        total_records = 0

        for i, code in enumerate(remaining):
            try:
                records = self._fetch_one(code, start, end)
                if records > 0:
                    success += 1
                    total_records += records

                time.sleep(0.05)

                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i+1}/{len(remaining)}, 成功: {success}, 新增: {total_records}")
            except Exception as e:
                logger.error(f"{code} 失败: {e}")

        bs.logout()
        logger.info(f"✅ 完成! {success}/{len(remaining)} 只成功, {total_records} 条记录")

    def _fetch_one(self, code, start, end):
        if code.startswith(('6', '688', '689')):
            bs_code = f"sh.{code}"
        else:
            bs_code = f"sz.{code}"

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date=start, end_date=end, frequency="d", adjustflag="2"
        )

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

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

        df['year'] = df['trade_date'].dt.year
        df['month'] = df['trade_date'].dt.month

        for (year, month), group in df.groupby(['year', 'month']):
            partition_path = self.parquet_path / f"daily/year={year}/month={month:02d}"
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

if __name__ == "__main__":
    EfficientFiller().run()
