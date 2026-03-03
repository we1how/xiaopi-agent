#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股本地数据库 - 每日增量更新脚本

功能:
- 只拉取新数据
- 合并到现有 Parquet
- 更新 DuckDB 视图
- 生成更新报告
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import pandas as pd
import duckdb

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path('~/StockData/logs/daily_update.log').expanduser()),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyUpdater:
    """每日数据更新器"""
    
    def __init__(self, base_path: str = "~/StockData"):
        self.base_path = Path(base_path).expanduser()
        self.parquet_path = self.base_path / "parquet"
        self.meta_path = self.base_path / "meta"
        self.log_path = self.base_path / "logs"
        self.db_path = self.base_path / "stock.duckdb"
        self.update_log = self.meta_path / "daily_update_log.json"
        
        # 创建目录
        for path in [self.parquet_path, self.meta_path, self.log_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # 加载更新记录
        self.update_history = self._load_update_history()
        
        # 初始化数据源
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源（akshare为主，baostock备用）"""
        self.ak = None
        self.bs = None
        self.ts = None
        
        # 1. 尝试 akshare
        try:
            import akshare as ak
            self.ak = ak
            logger.info("✅ akshare 已加载")
        except ImportError:
            logger.warning("⚠️ akshare 未安装")
        
        # 2. 尝试 baostock（备用）
        try:
            import baostock as bs
            self.bs = bs
            logger.info("✅ baostock 已加载（备用）")
        except ImportError:
            logger.warning("⚠️ baostock 未安装")
        
        # 3. Tushare (可选)
        token_path = Path("~/.openclaw/credentials/tushare.json").expanduser()
        if token_path.exists():
            try:
                with open(token_path) as f:
                    config = json.load(f)
                    token = config.get("token")
                    if token:
                        import tushare as ts
                        ts.set_token(token)
                        self.ts = ts.pro_api()
                        logger.info("✅ Tushare 已加载")
            except Exception as e:
                logger.warning(f"Tushare 加载失败: {e}")
        
        # 检查至少有一个数据源可用
        if self.ak is None and self.bs is None:
            logger.error("❌ 没有可用的数据源（akshare 或 baostock 至少安装一个）")
            sys.exit(1)
    
    def _load_update_history(self) -> Dict:
        """加载更新历史"""
        if self.update_log.exists():
            with open(self.update_log) as f:
                return json.load(f)
        return {
            "last_update": None,
            "daily": {"last_date": None, "record_count": 0},
            "fundamentals": {"last_date": None, "record_count": 0},
        }
    
    def _save_update_history(self):
        """保存更新历史"""
        self.update_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.update_log, 'w') as f:
            json.dump(self.update_history, f, indent=2, default=str)
    
    def _smart_sleep(self, base_delay: float = 0.3):
        """智能延时"""
        import random
        delay = base_delay + random.uniform(0, 0.2)
        time.sleep(delay)
    
    def update_stock_basic(self):
        """更新股票基本信息（akshare为主，baostock备用）"""
        logger.info("📊 更新股票基本信息...")
        
        df = None
        
        # 尝试 akshare
        if self.ak is not None:
            try:
                df = self.ak.stock_zh_a_spot_em()
                logger.info("✅ 使用 akshare 获取股票列表")
            except Exception as e:
                logger.warning(f"⚠️ akshare 获取失败: {e}，尝试备用源...")
        
        # 尝试 baostock 备用
        if df is None and self.bs is not None:
            try:
                lg = self.bs.login()
                if lg.error_code == '0':
                    rs = self.bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
                    stock_list = []
                    while (rs.error_code == '0') & rs.next():
                        stock_list.append(rs.get_row_data())
                    self.bs.logout()
                    
                    df = pd.DataFrame(stock_list, columns=rs.fields)
                    df = df.rename(columns={'code': 'symbol', 'code_name': 'name'})
                    logger.info(f"✅ 使用 baostock 获取股票列表: {len(df)} 只")
            except Exception as e:
                logger.error(f"❌ baostock 获取也失败: {e}")
        
        if df is None:
            logger.error("❌ 所有数据源均失败")
            return 0
        
        try:
            # 标准化列名（akshare格式）
            if '代码' in df.columns:
                df = df.rename(columns={
                    '代码': 'symbol',
                    '名称': 'name',
                    '最新价': 'close',
                    '涨跌幅': 'pct_chg',
                    '涨跌额': 'change',
                    '成交量': 'vol',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '最高': 'high',
                    '最低': 'low',
                    '今开': 'open',
                    '昨收': 'pre_close',
                    '量比': 'volume_ratio',
                    '换手率': 'turnover_rate',
                    '市盈率-动态': 'pe',
                    '市净率': 'pb',
                    '总市值': 'total_mv',
                    '流通市值': 'circ_mv',
                })
            
            df['update_time'] = datetime.now()
            
            # 保存
            output_path = self.parquet_path / "stock_basic.parquet"
            df.to_parquet(output_path, index=False, compression='zstd')
            
            logger.info(f"✅ 股票基本信息已更新: {len(df)} 只股票")
            return len(df)
            
        except Exception as e:
            logger.error(f"❌ 处理股票基本信息失败: {e}")
            return 0
    
    def update_daily_data(self, lookback_days: int = 5):
        """
        更新日线数据（支持akshare和baostock双源）
        
        Args:
            lookback_days: 回溯天数，用于补全可能缺失的数据
        """
        today = datetime.now()
        start_date = (today - timedelta(days=lookback_days)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")
        
        logger.info(f"📈 更新日线数据 ({start_date} ~ {end_date})...")
        
        # 获取股票列表
        stock_codes = self._get_stock_list()
        if not stock_codes:
            logger.error("❌ 无法获取股票列表")
            return 0
        
        total = len(stock_codes)
        new_records = 0
        updated_stocks = 0
        failed_codes = []
        
        for i, code in enumerate(stock_codes):
            try:
                # 尝试 akshare
                df = self._fetch_daily_akshare(code, start_date, end_date)
                
                # 如果 akshare 失败且 baostock 可用，尝试备用
                if df is None and self.bs is not None:
                    df = self._fetch_daily_baostock(code, start_date, end_date)
                
                if df is not None and len(df) > 0:
                    df['ts_code'] = code
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    
                    # 按日期分区保存
                    self._save_daily_partition(df, code)
                    
                    new_records += len(df)
                    updated_stocks += 1
                
                self._smart_sleep(0.2)
                
                # 每100只报告一次进度
                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i+1}/{total}，已更新 {updated_stocks} 只股票")
                
            except Exception as e:
                logger.error(f"更新 {code} 失败: {e}")
                failed_codes.append(code)
                continue
        
        if failed_codes:
            logger.warning(f"⚠️ {len(failed_codes)} 只股票更新失败")
        
        logger.info(f"✅ 日线数据更新完成: {updated_stocks} 只股票, {new_records} 条新记录")
        
        # 更新历史记录
        self.update_history["daily"]["last_date"] = end_date
        self.update_history["daily"]["record_count"] += new_records
        self._save_update_history()
        
        return new_records
    
    def _get_stock_list(self) -> List[str]:
        """获取股票代码列表（支持多源）"""
        # 尝试 akshare
        if self.ak is not None:
            try:
                stock_df = self.ak.stock_zh_a_spot_em()
                return stock_df['代码'].tolist()
            except Exception as e:
                logger.warning(f"akshare 获取股票列表失败: {e}")
        
        # 尝试 baostock
        if self.bs is not None:
            try:
                lg = self.bs.login()
                if lg.error_code == '0':
                    rs = self.bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
                    codes = []
                    while (rs.error_code == '0') & rs.next():
                        code = rs.get_row_data()[0]
                        # baostock格式: sh.600000 -> 600000
                        if '.' in code:
                            code = code.split('.')[1]
                        codes.append(code)
                    self.bs.logout()
                    return codes
            except Exception as e:
                logger.warning(f"baostock 获取股票列表失败: {e}")
        
        return []
    
    def _fetch_daily_akshare(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """使用 akshare 获取日线数据"""
        if self.ak is None:
            return None
        
        try:
            df = self.ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df is not None and len(df) > 0:
                return df.rename(columns={
                    '日期': 'trade_date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'vol',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_chg',
                    '涨跌额': 'change',
                    '换手率': 'turnover_rate',
                })
        except Exception as e:
            logger.debug(f"akshare 获取 {code} 失败: {e}")
        
        return None
    
    def _fetch_daily_baostock(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """使用 baostock 获取日线数据（备用）"""
        if self.bs is None:
            return None
        
        try:
            # 转换代码格式: 600000 -> sh.600000
            if code.startswith('6'):
                bs_code = f"sh.{code}"
            else:
                bs_code = f"sz.{code}"
            
            lg = self.bs.login()
            if lg.error_code != '0':
                return None
            
            # 转换日期格式: 20240301 -> 2024-03-01
            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            rs = self.bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,preclose,volume,amount,turn,pctChg",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2"  # 前复权
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            self.bs.logout()
            
            if data_list:
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
                for col in ['open', 'high', 'low', 'close', 'vol', 'amount', 'turnover_rate', 'pct_chg']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
                
        except Exception as e:
            logger.debug(f"baostock 获取 {code} 失败: {e}")
        
        return None
    
    def _save_daily_partition(self, df: pd.DataFrame, code: str):
        """保存日线数据到分区"""
        df['year'] = df['trade_date'].dt.year
        df['month'] = df['trade_date'].dt.month
        
        for (year, month), group in df.groupby(['year', 'month']):
            partition_path = self.parquet_path / "daily" / f"year={year}" / f"month={month:02d}"
            partition_path.mkdir(parents=True, exist_ok=True)
            
            parquet_file = partition_path / "data.parquet"
            
            if parquet_file.exists():
                # 读取现有数据，合并，去重
                existing = pd.read_parquet(parquet_file)
                combined = pd.concat([existing, group], ignore_index=True)
                combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')
                combined.to_parquet(parquet_file, index=False, compression='zstd')
            else:
                group.to_parquet(parquet_file, index=False, compression='zstd')
    
    def update_fundamentals(self):
        """更新基本面数据（支持akshare和baostock双源）"""
        logger.info("📊 更新基本面数据...")
        
        df = None
        
        # 尝试 akshare
        if self.ak is not None:
            try:
                df = self.ak.stock_zh_a_spot_em()
                fundamental_cols = ['代码', '名称', '市盈率-动态', '市净率', '总市值', '流通市值']
                df = df[fundamental_cols]
                df = df.rename(columns={
                    '代码': 'ts_code',
                    '名称': 'name',
                    '市盈率-动态': 'pe',
                    '市净率': 'pb',
                    '总市值': 'total_mv',
                    '流通市值': 'circ_mv',
                })
                logger.info("✅ 使用 akshare 获取基本面数据")
            except Exception as e:
                logger.warning(f"⚠️ akshare 获取基本面失败: {e}，尝试备用源...")
        
        # 尝试 baostock 备用
        if df is None and self.bs is not None:
            try:
                df = self._fetch_fundamentals_baostock()
                if df is not None:
                    logger.info(f"✅ 使用 baostock 获取基本面数据: {len(df)} 条")
            except Exception as e:
                logger.error(f"❌ baostock 获取基本面也失败: {e}")
        
        if df is None:
            logger.error("❌ 所有数据源均失败")
            return 0
        
        try:
            df['trade_date'] = datetime.now().date()
            
            output_path = self.parquet_path / "fundamentals.parquet"
            df.to_parquet(output_path, index=False, compression='zstd')
            
            logger.info(f"✅ 基本面数据已更新: {len(df)} 条记录")
            
            self.update_history["fundamentals"]["last_date"] = datetime.now().isoformat()
            self.update_history["fundamentals"]["record_count"] = len(df)
            self._save_update_history()
            
            return len(df)
            
        except Exception as e:
            logger.error(f"❌ 处理基本面数据失败: {e}")
            return 0
    
    def _fetch_fundamentals_baostock(self) -> Optional[pd.DataFrame]:
        """使用 baostock 获取基本面数据"""
        try:
            lg = self.bs.login()
            if lg.error_code != '0':
                return None
            
            # 获取当前所有股票的基本面数据
            # baostock 没有直接的实时基本面接口，使用历史查询
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 获取股票列表
            rs = self.bs.query_all_stock(day=today)
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                stock_list.append(rs.get_row_data()[0])
            
            # 批量查询基本面（这里简化处理，实际可以优化为批量查询）
            fundamentals = []
            for code in stock_list[:100]:  # 限制数量避免超时
                try:
                    rs = self.bs.query_stock_basic(code)
                    if rs.error_code == '0':
                        data = rs.get_row_data()
                        fundamentals.append({
                            'ts_code': code.split('.')[1] if '.' in code else code,
                            'name': data[1] if len(data) > 1 else '',
                            'pe': None,  # baostock 实时PE需要额外查询
                            'pb': None,
                            'total_mv': None,
                            'circ_mv': None,
                        })
                except:
                    continue
            
            self.bs.logout()
            
            if fundamentals:
                return pd.DataFrame(fundamentals)
            
        except Exception as e:
            logger.warning(f"baostock 获取基本面失败: {e}")
        
        return None
    
    def refresh_duckdb_views(self):
        """刷新 DuckDB 视图"""
        logger.info("🦆 刷新 DuckDB 视图...")
        
        try:
            conn = duckdb.connect(str(self.db_path))
            
            # 刷新各表视图
            tables = ['stock_basic', 'fundamentals', 'income_statement', 
                      'balance_sheet', 'cash_flow']
            
            for table in tables:
                parquet_path = self.parquet_path / f"{table}.parquet"
                if parquet_path.exists():
                    conn.execute(f"""
                        CREATE OR REPLACE VIEW {table} AS
                        SELECT * FROM read_parquet('{parquet_path}')
                    """)
            
            # 日线数据视图
            daily_path = self.parquet_path / "daily" / "**" / "**" / "*.parquet"
            conn.execute(f"""
                CREATE OR REPLACE VIEW daily AS
                SELECT * FROM read_parquet('{daily_path}', hive_partitioning=1)
            """)
            
            conn.close()
            logger.info("✅ DuckDB 视图已刷新")
            
        except Exception as e:
            logger.error(f"刷新 DuckDB 视图失败: {e}")
    
    def generate_report(self) -> Dict:
        """生成更新报告"""
        report = {
            "update_time": datetime.now().isoformat(),
            "stocks_updated": 0,
            "new_records": 0,
            "storage_used_gb": 0,
        }
        
        # 计算存储使用量
        total_size = 0
        for parquet_file in self.parquet_path.rglob("*.parquet"):
            total_size += parquet_file.stat().st_size
        
        report["storage_used_gb"] = round(total_size / (1024**3), 2)
        
        # 统计记录数
        try:
            conn = duckdb.connect(str(self.db_path))
            
            # 日线数据数量
            result = conn.execute("SELECT COUNT(*) FROM daily").fetchone()
            report["daily_records"] = result[0] if result else 0
            
            # 股票数量
            result = conn.execute("SELECT COUNT(*) FROM stock_basic").fetchone()
            report["stock_count"] = result[0] if result else 0
            
            conn.close()
        except Exception as e:
            logger.warning(f"统计记录数失败: {e}")
        
        return report
    
    def run_daily_update(self):
        """执行每日更新"""
        logger.info("=" * 60)
        logger.info("🚀 开始每日数据更新")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. 更新股票基本信息
        stock_count = self.update_stock_basic()
        
        # 2. 更新日线数据（回溯5天，补全可能缺失的）
        new_records = self.update_daily_data(lookback_days=5)
        
        # 3. 更新基本面数据
        fundamentals_count = self.update_fundamentals()
        
        # 4. 刷新 DuckDB 视图
        self.refresh_duckdb_views()
        
        # 5. 生成报告
        report = self.generate_report()
        report["stocks_updated"] = stock_count
        report["new_records"] = new_records
        
        elapsed = time.time() - start_time
        
        # 保存报告
        report_path = self.log_path / f"update_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info(f"✅ 每日更新完成！耗时: {elapsed/60:.1f} 分钟")
        logger.info(f"📊 更新统计:")
        logger.info(f"   - 股票数: {report['stock_count']}")
        logger.info(f"   - 日线记录: {report['daily_records']}")
        logger.info(f"   - 存储占用: {report['storage_used_gb']} GB")
        logger.info("=" * 60)
        
        # 更新最后更新时间
        self.update_history["last_update"] = datetime.now().isoformat()
        self._save_update_history()
        
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='A股本地数据库每日更新')
    parser.add_argument('--base-path', default='~/StockData', help='数据存储路径')
    args = parser.parse_args()
    
    updater = DailyUpdater(base_path=args.base_path)
    report = updater.run_daily_update()
    
    # 输出 JSON 报告（方便自动化脚本解析）
    print("\n" + "=" * 60)
    print("更新报告 JSON:")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
