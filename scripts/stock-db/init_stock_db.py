#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股本地数据库 - 多数据源混合版
数据源优先级: baostock → akshare → Tushare

特性:
- 多数据源智能降级
- 统一数据格式输出
- 高频查询支持（baostock 无明确限流）
- 分批拉取，断点续传
- 详细日志
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
        logging.FileHandler(Path('~/StockData/logs/init.log').expanduser()),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 统一数据列名映射
COLUMN_MAPPING = {
    # baostock -> 统一格式
    'baostock': {
        'date': 'trade_date',
        'code': 'ts_code_raw',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'vol',
        'amount': 'amount',
        'turn': 'turnover_rate',
        'pctChg': 'pct_chg',
        'preclose': 'pre_close',
    },
    # akshare stock_zh_a_hist -> 统一格式
    'akshare': {
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
    },
    # Tushare -> 统一格式 (已经是英文)
    'tushare': {
        'trade_date': 'trade_date',
        'ts_code': 'ts_code',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'vol': 'vol',
        'amount': 'amount',
        'pct_chg': 'pct_chg',
    }
}

# 统一输出列
OUTPUT_COLUMNS = ['trade_date', 'ts_code', 'open', 'high', 'low', 'close', 
                  'vol', 'amount', 'pct_chg', 'turnover_rate', 'data_source']


class StockDBInitializer:
    """股票数据库初始化器 - 多数据源混合版"""
    
    def __init__(self, base_path: str = "~/StockData"):
        self.base_path = Path(base_path).expanduser()
        self.parquet_path = self.base_path / "parquet"
        self.meta_path = self.base_path / "meta"
        self.log_path = self.base_path / "logs"
        self.db_path = self.base_path / "stock.duckdb"
        self.progress_file = self.meta_path / "init_progress.json"
        
        # 创建目录
        for path in [self.parquet_path, self.meta_path, self.log_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # 加载进度
        self.progress = self._load_progress()
        
        # 初始化数据源
        self._init_data_sources()
        
        # 股票代码列表缓存
        self._stock_list_cache: Optional[pd.DataFrame] = None
    
    def _init_data_sources(self):
        """初始化所有数据源"""
        # 1. baostock (主力数据源)
        self.bs = None
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                self.bs = bs
                logger.info("✅ baostock 登录成功（主力数据源）")
            else:
                logger.warning(f"⚠️ baostock 登录失败: {lg.error_msg}")
        except ImportError:
            logger.warning("⚠️ baostock 未安装，请执行: pip install baostock")
        except Exception as e:
            logger.warning(f"⚠️ baostock 初始化失败: {e}")
        
        # 2. akshare (备用)
        self.ak = None
        try:
            import akshare as ak
            self.ak = ak
            logger.info("✅ akshare 加载成功（备用数据源）")
        except ImportError:
            logger.warning("⚠️ akshare 未安装")
        
        # 3. Tushare (最后备用)
        self.ts = None
        self.ts_token = self._load_tushare_token()
        if self.ts_token:
            try:
                import tushare as ts
                ts.set_token(self.ts_token)
                self.ts = ts.pro_api()
                logger.info("✅ Tushare 加载成功（备用数据源）")
            except Exception as e:
                logger.warning(f"⚠️ Tushare 加载失败: {e}")
    
    def _load_tushare_token(self) -> Optional[str]:
        """从配置文件加载 Tushare Token"""
        token_path = Path("~/.openclaw/credentials/tushare.json").expanduser()
        if token_path.exists():
            try:
                with open(token_path) as f:
                    config = json.load(f)
                    return config.get("token")
            except Exception as e:
                logger.warning(f"读取 Tushare 配置失败: {e}")
        return None
    
    def _load_progress(self) -> Dict:
        """加载初始化进度"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {
            "stock_basic": {"completed": False, "last_update": None, "count": 0},
            "daily": {"completed": False, "last_code": None, "last_date": None, "count": 0},
        }
    
    def _save_progress(self):
        """保存初始化进度"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2, default=str)
    
    def _smart_sleep(self, base_delay: float = 0.1):
        """智能延时 - baostock 限制较宽松"""
        import random
        delay = base_delay + random.uniform(0, 0.05)
        time.sleep(delay)
    
    def _convert_code_to_ts(self, code: str) -> str:
        """统一转换为 ts_code 格式 (如: 000001.SZ)"""
        # baostock 格式: sh.600000 / sz.000001
        if code.startswith('sh.'):
            return code.replace('sh.', '') + '.SH'
        elif code.startswith('sz.'):
            return code.replace('sz.', '') + '.SZ'
        # 已经是 ts_code 格式
        elif '.SH' in code or '.SZ' in code:
            return code
        # 纯数字代码，需要判断
        elif code.isdigit():
            if code.startswith('6'):
                return code + '.SH'
            else:
                return code + '.SZ'
        return code
    
    def _convert_code_to_baostock(self, ts_code: str) -> str:
        """ts_code 转 baostock 格式"""
        if ts_code.endswith('.SH'):
            return 'sh.' + ts_code.replace('.SH', '')
        elif ts_code.endswith('.SZ'):
            return 'sz.' + ts_code.replace('.SZ', '')
        return ts_code
    
    def _standardize_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """标准化数据格式"""
        if df is None or len(df) == 0:
            return pd.DataFrame()
        
        # 列名映射
        mapping = COLUMN_MAPPING.get(source, {})
        df = df.rename(columns=mapping)
        
        # 处理 baostock 的特殊 code 列
        if source == 'baostock' and 'ts_code_raw' in df.columns:
            df['ts_code'] = df['ts_code_raw'].apply(self._convert_code_to_ts)
            df = df.drop('ts_code_raw', axis=1)
        elif source == 'akshare' and 'ts_code' not in df.columns:
            # akshare 需要额外处理，在调用时传入 symbol
            pass
        
        # 添加数据源标记
        df['data_source'] = source
        
        # 统一日期格式
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 确保数值类型
        numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'amount', 'pct_chg', 'turnover_rate']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 只保留统一列
        available_cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
        return df[available_cols]
    
    def get_stock_list(self, use_cache: bool = True) -> pd.DataFrame:
        """获取股票列表"""
        if use_cache and self._stock_list_cache is not None:
            return self._stock_list_cache
        
        logger.info("📋 获取A股股票列表...")
        
        # 方法1: akshare（最快，有名称）
        if self.ak:
            try:
                df = self.ak.stock_info_a_code_name()
                df['ts_code'] = df['code'].apply(
                    lambda x: x + '.SH' if x.startswith('6') else x + '.SZ'
                )
                logger.info(f"✅ 使用 akshare 获取 {len(df)} 只股票")
                self._stock_list_cache = df
                return df
            except Exception as e:
                logger.warning(f"⚠️ akshare 获取股票列表失败: {e}")
        
        # 方法2: baostock（只获取代码，不查名称）
        if self.bs:
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                rs = self.bs.query_all_stock(day=today)
                data = []
                while (rs.error_code == '0') & rs.next():
                    row = rs.get_row_data()
                    code = row[0]  # sh.600000 格式
                    # 过滤掉指数
                    if not code.startswith(('sh.000', 'sz.399')):
                        pure_code = code.replace('sh.', '').replace('sz.', '')
                        data.append({
                            'code': pure_code,
                            'name': '',  # 暂不获取名称，加快速度
                            'ts_code': self._convert_code_to_ts(code)
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    logger.info(f"✅ 使用 baostock 获取 {len(df)} 只股票（无名称）")
                    self._stock_list_cache = df
                    return df
            except Exception as e:
                logger.warning(f"⚠️ baostock 获取股票列表失败: {e}")
        
        raise Exception("所有股票列表获取方法都失败了")
    
    def get_stock_hist_baostock(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """使用 baostock 获取历史数据"""
        if not self.bs:
            return None
        
        try:
            # 转换日期格式
            start = pd.to_datetime(start_date).strftime('%Y-%m-%d')
            end = pd.to_datetime(end_date).strftime('%Y-%m-%d')
            
            # 转换代码格式
            bs_code = self._convert_code_to_baostock(code)
            
            rs = self.bs.query_history_k_data_plus(bs_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start, end_date=end, frequency="d", adjustflag="3")
            
            data = []
            while (rs.error_code == '0') & rs.next():
                data.append(rs.get_row_data())
            
            if data:
                df = pd.DataFrame(data, columns=rs.fields)
                return self._standardize_dataframe(df, 'baostock')
            return None
        except Exception as e:
            logger.debug(f"baostock 获取 {code} 失败: {e}")
            return None
    
    def get_stock_hist_akshare(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """使用 akshare 获取历史数据"""
        if not self.ak:
            return None
        
        try:
            # 转换日期格式
            start = pd.to_datetime(start_date).strftime('%Y%m%d')
            end = pd.to_datetime(end_date).strftime('%Y%m%d')
            
            # 提取纯数字代码
            pure_code = code.replace('.SH', '').replace('.SZ', '')
            
            df = self.ak.stock_zh_a_hist(
                symbol=pure_code,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq"
            )
            
            if df is not None and len(df) > 0:
                df['ts_code'] = code
                return self._standardize_dataframe(df, 'akshare')
            return None
        except Exception as e:
            logger.debug(f"akshare 获取 {code} 失败: {e}")
            return None
    
    def get_stock_hist_tushare(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """使用 Tushare 获取历史数据"""
        if not self.ts:
            return None
        
        try:
            start = pd.to_datetime(start_date).strftime('%Y%m%d')
            end = pd.to_datetime(end_date).strftime('%Y%m%d')
            
            df = self.ts.daily(ts_code=code, start_date=start, end_date=end)
            
            if df is not None and len(df) > 0:
                return self._standardize_dataframe(df, 'tushare')
            return None
        except Exception as e:
            logger.debug(f"Tushare 获取 {code} 失败: {e}")
            return None
    
    def get_stock_hist(self, code: str, start_date: str, end_date: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取股票历史数据 - 多源智能降级
        
        Returns:
            (DataFrame, source_name) 或 (None, '')
        """
        # 1. 优先使用 baostock
        df = self.get_stock_hist_baostock(code, start_date, end_date)
        if df is not None and len(df) > 0:
            return df, 'baostock'
        self._smart_sleep(0.1)
        
        # 2. 使用 akshare
        df = self.get_stock_hist_akshare(code, start_date, end_date)
        if df is not None and len(df) > 0:
            return df, 'akshare'
        self._smart_sleep(0.3)
        
        # 3. 最后使用 Tushare
        df = self.get_stock_hist_tushare(code, start_date, end_date)
        if df is not None and len(df) > 0:
            return df, 'tushare'
        
        return None, ''
    
    def init_stock_basic(self):
        """初始化股票基本信息"""
        if self.progress["stock_basic"]["completed"]:
            logger.info("✅ 股票基本信息已存在，跳过")
            return
        
        logger.info("📊 开始获取股票基本信息...")
        
        try:
            df = self.get_stock_list()
            df['update_time'] = datetime.now()
            
            output_path = self.parquet_path / "stock_basic.parquet"
            df.to_parquet(output_path, index=False, compression='zstd')
            logger.info(f"✅ 股票基本信息已保存: {output_path} ({len(df)} 条)")
            
            self.progress["stock_basic"]["completed"] = True
            self.progress["stock_basic"]["last_update"] = datetime.now().isoformat()
            self.progress["stock_basic"]["count"] = len(df)
            self._save_progress()
            
        except Exception as e:
            logger.error(f"❌ 获取股票基本信息失败: {e}")
            raise
    
    def init_daily_data(self, start_date: str = "20200101", end_date: Optional[str] = None,
                       batch_size: int = 50, max_stocks: Optional[int] = None,
                       fill_missing: bool = False):
        """初始化日线数据"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"📈 开始获取日线数据 ({start_date} ~ {end_date})...")
        
        try:
            stock_df = self.get_stock_list()
            stock_codes = stock_df['ts_code'].tolist()
            
            if fill_missing:
                # 补漏模式
                existing = self._get_existing_stocks()
                stock_codes = [c for c in stock_codes if c not in existing]
                logger.info(f"🔍 补漏模式: 缺失 {len(stock_codes)} 只股票")
            
            if max_stocks:
                stock_codes = stock_codes[:max_stocks]
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return
        
        total = len(stock_codes)
        if total == 0:
            logger.info("✅ 所有股票数据已完整")
            return
        
        logger.info(f"共 {total} 只股票需要处理")
        
        all_data = []
        batch_count = 0
        success_count = 0
        fail_count = 0
        source_stats = {'baostock': 0, 'akshare': 0, 'tushare': 0}
        
        for i, code in enumerate(stock_codes):
            try:
                if i % 50 == 0 or i == len(stock_codes) - 1:
                    logger.info(f"[{i+1}/{total}] {code} - 成功:{success_count} 失败:{fail_count} "
                              f"(baostock:{source_stats['baostock']} akshare:{source_stats['akshare']} tushare:{source_stats['tushare']})")
                
                df, source = self.get_stock_hist(code, start_date, end_date)
                
                if df is not None and len(df) > 0:
                    all_data.append(df)
                    success_count += 1
                    source_stats[source] = source_stats.get(source, 0) + 1
                else:
                    fail_count += 1
                
                # 批量保存
                batch_count += 1
                if batch_count >= batch_size:
                    self._save_daily_batch(all_data, code)
                    all_data = []
                    batch_count = 0
                    self.progress["daily"]["last_code"] = code
                    self.progress["daily"]["last_date"] = end_date
                    self.progress["daily"]["count"] = success_count
                    self._save_progress()
                
            except Exception as e:
                logger.error(f"获取 {code} 失败: {e}")
                fail_count += 1
        
        if all_data:
            self._save_daily_batch(all_data, stock_codes[-1] if stock_codes else "end")
        
        self.progress["daily"]["completed"] = (fail_count == 0)
        self.progress["daily"]["last_code"] = None
        self.progress["daily"]["count"] = success_count
        self._save_progress()
        
        logger.info(f"✅ 日线数据完成 - 成功:{success_count} 失败:{fail_count}")
        logger.info(f"📊 数据源统计: {source_stats}")
    
    def _get_existing_stocks(self) -> set:
        """获取已有数据的股票代码"""
        existing = set()
        daily_path = self.parquet_path / "daily"
        
        if daily_path.exists():
            try:
                for parquet_file in daily_path.rglob("*.parquet"):
                    try:
                        df = pd.read_parquet(parquet_file)
                        if 'ts_code' in df.columns:
                            existing.update(df['ts_code'].unique())
                    except:
                        continue
            except:
                pass
        
        return existing
    
    def _save_daily_batch(self, data_list: List[pd.DataFrame], last_code: str):
        """保存一批日线数据"""
        if not data_list:
            return
        
        df = pd.concat(data_list, ignore_index=True)
        
        output_path = self.parquet_path / "daily"
        output_path.mkdir(exist_ok=True)
        
        # 按日期分区
        df['year'] = df['trade_date'].dt.year
        df['month'] = df['trade_date'].dt.month
        
        for (year, month), group in df.groupby(['year', 'month']):
            partition_path = output_path / f"year={year}" / f"month={month:02d}"
            partition_path.mkdir(parents=True, exist_ok=True)
            
            parquet_file = partition_path / "data.parquet"
            
            if parquet_file.exists():
                existing = pd.read_parquet(parquet_file)
                combined = pd.concat([existing, group], ignore_index=True)
                combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'])
                combined.to_parquet(parquet_file, index=False, compression='zstd')
            else:
                group.to_parquet(parquet_file, index=False, compression='zstd')
        
        logger.info(f"💾 已保存 {len(df)} 条记录，最后股票: {last_code}")
    
    def create_duckdb_views(self):
        """创建 DuckDB 视图"""
        logger.info("🦆 创建 DuckDB 视图...")
        
        conn = duckdb.connect(str(self.db_path))
        
        stock_basic_path = self.parquet_path / "stock_basic.parquet"
        if stock_basic_path.exists():
            conn.execute(f"""
                CREATE OR REPLACE VIEW stock_basic AS
                SELECT * FROM read_parquet('{stock_basic_path}')
            """)
            logger.info("✅ 视图已创建: stock_basic")
        
        daily_path = self.parquet_path / "daily" / "**" / "**" / "*.parquet"
        if daily_path.parent.exists():
            conn.execute(f"""
                CREATE OR REPLACE VIEW daily AS
                SELECT * FROM read_parquet('{daily_path}', hive_partitioning=1)
            """)
            logger.info("✅ 视图已创建: daily")
        
        conn.close()
        logger.info("✅ DuckDB 视图创建完成")
    
    def run_all(self, quick_mode: bool = False, fill_missing: bool = False):
        """运行完整初始化"""
        logger.info("=" * 60)
        if fill_missing:
            logger.info("🚀 开始补漏模式 - 多数据源混合")
        else:
            logger.info("🚀 开始初始化 A股本地数据库 - 多数据源混合")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. 股票基本信息
        if not fill_missing:
            self.init_stock_basic()
        
        # 2. 日线数据
        if quick_mode:
            start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            self.init_daily_data(start_date=start, batch_size=20, max_stocks=50)
        elif fill_missing:
            self.init_daily_data(start_date="20200101", batch_size=50, fill_missing=True)
        else:
            self.init_daily_data(start_date="20200101", batch_size=50)
        
        # 3. 创建 DuckDB 视图
        self.create_duckdb_views()
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ 完成！耗时: {elapsed/60:.1f} 分钟")
        logger.info("=" * 60)
        
        self._print_stats()
    
    def _print_stats(self):
        """打印统计信息"""
        logger.info("\n📊 数据统计:")
        logger.info(f"  - 股票基本信息: {self.progress['stock_basic'].get('count', 0)} 只")
        logger.info(f"  - 日线数据: {len(self._get_existing_stocks())} 只")
        logger.info(f"  - 数据目录: {self.base_path}")
        
    def __del__(self):
        """析构时退出 baostock"""
        if self.bs:
            try:
                self.bs.logout()
            except:
                pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='A股本地数据库初始化 - 多数据源混合版')
    parser.add_argument('--quick', action='store_true', help='快速模式')
    parser.add_argument('--fill-missing', action='store_true', help='补漏模式')
    parser.add_argument('--base-path', default='~/StockData', help='数据存储路径')
    args = parser.parse_args()
    
    initializer = StockDBInitializer(base_path=args.base_path)
    try:
        initializer.run_all(quick_mode=args.quick, fill_missing=args.fill_missing)
    finally:
        # 确保退出 baostock
        if initializer.bs:
            initializer.bs.logout()


if __name__ == "__main__":
    main()
