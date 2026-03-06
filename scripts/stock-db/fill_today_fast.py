#!/usr/bin/env python3
"""高效补充今天剩余数据 - 复用baostock连接"""
import time
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class FillTodayFast:
    def __init__(self):
        self.parquet_path = Path("~/StockData/parquet").expanduser()
        self.today = datetime.now().date()
        self.today_str = self.today.strftime('%Y-%m-%d')
        self.stock_codes = self._get_stock_list()
        self.completed = self._get_today_completed()
        self.remaining = [c for c in self.stock_codes if c not in self.completed]
        logger.info(f"股票总数: {len(self.stock_codes)}, 今天已完成: {len(self.completed)}, 剩余: {len(self.remaining)}")

    def _get_stock_list(self):
        basic_path = self.parquet_path / "stock_basic.parquet"
        df = pd.read_parquet(basic_path)
        codes = df['symbol'].tolist()
        clean_codes = [str(c).split('.')[1] if '.' in str(c) else str(c) for c in codes]
        valid_prefixes = ('600', '601', '603', '605', '688', '689', '000', '001', '002', '003', '300', '301')
        return [c for c in clean_codes if len(c) == 6 and c.isdigit() and c.startswith(valid_prefixes)]

    def _get_today_completed(self):
        """只获取今天已完成的股票"""
        completed = set()
        partition_path = self.parquet_path / "daily/year=2026/month=03/data.parquet"
        if partition_path.exists():
            df = pd.read_parquet(partition_path)
            today_data = df[df['trade_date'] == self.today_str]
            completed.update(today_data['ts_code'].unique().tolist())
        return completed

    def run(self):
        if not self.remaining:
            logger.info("✅ 今天数据已完整!")
            return

        lg = bs.login()
        if lg.error_code != '0':
            logger.error("登录失败")
            return
        logger.info("✅ 已登录baostock，开始补充今天数据...")

        success = 0
        total_records = 0
        start_time = time.time()

        for i, code in enumerate(self.remaining):
            try:
                records = self._fetch_one(code)
                if records > 0:
                    success += 1
                    total_records += records

                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    speed = (i + 1) / elapsed * 60
                    logger.info(f"进度: {i+1}/{len(self.remaining)}, 成功: {success}, 记录: {total_records}, 速度: {speed:.0f}只/分钟")

                time.sleep(0.03)
            except Exception as e:
                logger.error(f"{code} 失败: {e}")

        bs.logout()
        logger.info(f"✅ 完成! {success}/{len(self.remaining)} 成功, {total_records} 条记录")

    def _fetch_one(self, code):
        if code.startswith(('6', '688', '689')):
            bs_code = f"sh.{code}"
        else:
            bs_code = f"sz.{code}"

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date=self.today_str, end_date=self.today_str,
            frequency="d", adjustflag="2"
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
    FillTodayFast().run()
