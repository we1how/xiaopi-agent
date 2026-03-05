#!/usr/bin/env python3
"""更新今天数据并补充2026-02-25缺失数据"""
import time
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateTodayAndFeb25:
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

    def _get_feb25_completed(self):
        """获取2026-02-25已完成的股票"""
        try:
            partition_path = self.parquet_path / "daily/year=2026/month=02/data.parquet"
            if partition_path.exists():
                df = pd.read_parquet(partition_path)
                feb25_data = df[df['trade_date'] == '2026-02-25']
                return set(feb25_data['ts_code'].unique().tolist())
        except Exception as e:
            logger.warning(f"读取2月25日数据失败: {e}")
        return set()

    def update_today(self):
        """更新今天数据"""
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        logger.info(f"=== 更新今天 ({today_str}) 数据 ===")

        lg = bs.login()
        if lg.error_code != '0':
            logger.error("登录失败")
            return 0

        success = 0
        total_records = 0

        for i, code in enumerate(self.stock_codes):
            try:
                records = self._fetch_one(code, today_str, today_str)
                if records > 0:
                    success += 1
                    total_records += records

                if (i + 1) % 100 == 0:
                    logger.info(f"今天进度: {i+1}/{len(self.stock_codes)}, 成功: {success}")

                time.sleep(0.03)
            except Exception as e:
                logger.debug(f"{code} 失败: {e}")

        bs.logout()
        logger.info(f"✅ 今天完成: {success}/{len(self.stock_codes)} 只成功, {total_records} 条记录")
        return success

    def fill_feb25(self):
        """补充2026-02-25数据"""
        logger.info("=== 补充 2026-02-25 数据 ===")

        completed = self._get_feb25_completed()
        remaining = [c for c in self.stock_codes if c not in completed]

        logger.info(f"2月25日: 已完成 {len(completed)} 只, 剩余 {len(remaining)} 只需补充")

        if not remaining:
            logger.info("2月25日数据已完整")
            return 0

        lg = bs.login()
        if lg.error_code != '0':
            logger.error("登录失败")
            return 0

        success = 0
        total_records = 0

        for i, code in enumerate(remaining):
            try:
                records = self._fetch_one(code, '2026-02-25', '2026-02-25')
                if records > 0:
                    success += 1
                    total_records += records

                if (i + 1) % 100 == 0:
                    logger.info(f"2月25日进度: {i+1}/{len(remaining)}, 成功: {success}")

                time.sleep(0.03)
            except Exception as e:
                logger.debug(f"{code} 失败: {e}")

        bs.logout()
        logger.info(f"✅ 2月25日完成: {success}/{len(remaining)} 只成功, {total_records} 条记录")
        return success

    def _fetch_one(self, code, start, end):
        if code.startswith(('6', '688', '689')):
            bs_code = f"sh.{code}"
        else:
            bs_code = f"sz.{code}"

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date=start, end_date=end,
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
    updater = UpdateTodayAndFeb25()

    # 先补充2月25日
    updater.fill_feb25()

    # 再更新今天
    updater.update_today()

    logger.info("\n=== 全部完成 ===")
