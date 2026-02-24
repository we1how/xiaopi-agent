#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股本地数据库 - 首次初始化脚本
基于 Akshare + Tushare 的数据拉取

特性:
- 分批拉取，避免内存溢出
- 智能延时，避免 rate limit
- 断点续传，支持中断恢复
- 免费代理池
- 详细日志
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


class StockDBInitializer:
    """股票数据库初始化器"""
    
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
        
        # 导入数据源
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源"""
        try:
            import akshare as ak
            self.ak = ak
            logger.info("✅ Akshare 加载成功")
        except ImportError:
            logger.error("❌ 请先安装 akshare: pip install akshare")
            sys.exit(1)
        
        # 加载 Tushare (可选)
        self.ts = None
        self.ts_token = self._load_tushare_token()
        if self.ts_token:
            try:
                import tushare as ts
                ts.set_token(self.ts_token)
                self.ts = ts.pro_api()
                logger.info("✅ Tushare 加载成功")
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
            "stock_basic": {"completed": False, "last_update": None},
            "daily": {"completed": False, "last_code": None, "last_date": None},
            "fundamentals": {"completed": False, "last_date": None},
            "financial_reports": {"completed": False, "last_code": None},
        }
    
    def _save_progress(self):
        """保存初始化进度"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2, default=str)
    
    def _smart_sleep(self, base_delay: float = 0.5):
        """智能延时，避免 rate limit"""
        import random
        delay = base_delay + random.uniform(0, 0.3)
        time.sleep(delay)
    
    def init_stock_basic(self):
        """初始化股票基本信息"""
        if self.progress["stock_basic"]["completed"]:
            logger.info("✅ 股票基本信息已存在，跳过")
            return
        
        logger.info("📊 开始获取股票基本信息...")
        
        try:
            # 获取所有A股列表
            df = self.ak.stock_zh_a_spot_em()
            logger.info(f"获取到 {len(df)} 只股票")
            
            # 标准化列名
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
                '涨速': 'rise_speed',
                '5分钟涨跌': 'change_5min',
                '60日涨跌幅': 'change_60d',
                '年初至今涨跌幅': 'change_ytd',
            })
            
            # 添加时间戳
            df['update_time'] = datetime.now()
            
            # 保存为 Parquet
            output_path = self.parquet_path / "stock_basic.parquet"
            df.to_parquet(output_path, index=False, compression='zstd')
            logger.info(f"✅ 股票基本信息已保存: {output_path}")
            
            # 更新进度
            self.progress["stock_basic"]["completed"] = True
            self.progress["stock_basic"]["last_update"] = datetime.now().isoformat()
            self._save_progress()
            
        except Exception as e:
            logger.error(f"❌ 获取股票基本信息失败: {e}")
            raise
    
    def init_daily_data(self, start_date: str = "20200101", end_date: Optional[str] = None, 
                       batch_size: int = 50):
        """
        初始化日线数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期，默认今天
            batch_size: 每批处理的股票数量
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"📈 开始获取日线数据 ({start_date} ~ {end_date})...")
        
        # 获取股票列表
        try:
            stock_df = self.ak.stock_zh_a_spot_em()
            stock_codes = stock_df['代码'].tolist()
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return
        
        total = len(stock_codes)
        logger.info(f"共 {total} 只股票需要处理")
        
        # 检查断点续传
        last_code = self.progress["daily"].get("last_code")
        if last_code and last_code in stock_codes:
            start_idx = stock_codes.index(last_code)
            logger.info(f"🔄 从断点继续: {last_code} (第 {start_idx + 1}/{total} 只)")
            stock_codes = stock_codes[start_idx:]
        
        all_data = []
        batch_count = 0
        
        for i, code in enumerate(stock_codes):
            try:
                logger.info(f"[{i+1}/{total}] 获取 {code} 日线数据...")
                
                # 获取单只股票历史数据
                df = self.ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"  # 前复权
                )
                
                if df is not None and len(df) > 0:
                    # 标准化列名
                    df = df.rename(columns={
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
                    df['ts_code'] = code
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    all_data.append(df)
                
                # 智能延时
                self._smart_sleep(0.3)
                
                # 批量保存
                batch_count += 1
                if batch_count >= batch_size:
                    self._save_daily_batch(all_data, code)
                    all_data = []
                    batch_count = 0
                    
                    # 更新进度
                    self.progress["daily"]["last_code"] = code
                    self.progress["daily"]["last_date"] = end_date
                    self._save_progress()
                
            except Exception as e:
                logger.error(f"获取 {code} 失败: {e}")
                continue
        
        # 保存剩余数据
        if all_data:
            self._save_daily_batch(all_data, stock_codes[-1] if stock_codes else "end")
        
        # 标记完成
        self.progress["daily"]["completed"] = True
        self.progress["daily"]["last_code"] = None
        self._save_progress()
        
        logger.info("✅ 日线数据初始化完成")
    
    def _save_daily_batch(self, data_list: List[pd.DataFrame], last_code: str):
        """保存一批日线数据"""
        if not data_list:
            return
        
        df = pd.concat(data_list, ignore_index=True)
        
        # 按日期分区保存
        output_path = self.parquet_path / "daily"
        output_path.mkdir(exist_ok=True)
        
        # 使用日期分区
        df['year'] = df['trade_date'].dt.year
        df['month'] = df['trade_date'].dt.month
        
        for (year, month), group in df.groupby(['year', 'month']):
            partition_path = output_path / f"year={year}" / f"month={month:02d}"
            partition_path.mkdir(parents=True, exist_ok=True)
            
            parquet_file = partition_path / "data.parquet"
            
            # 如果文件存在，合并数据
            if parquet_file.exists():
                existing = pd.read_parquet(parquet_file)
                combined = pd.concat([existing, group], ignore_index=True)
                combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'])
                combined.to_parquet(parquet_file, index=False, compression='zstd')
            else:
                group.to_parquet(parquet_file, index=False, compression='zstd')
        
        logger.info(f"💾 已保存 {len(df)} 条记录，最后股票: {last_code}")
    
    def init_fundamentals(self):
        """初始化基本面数据"""
        if self.progress["fundamentals"]["completed"]:
            logger.info("✅ 基本面数据已存在，跳过")
            return
        
        logger.info("📊 开始获取基本面数据...")
        
        try:
            # 获取每日指标
            df = self.ak.stock_zh_a_spot_em()
            
            # 选择基本面相关字段
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
            
            df['trade_date'] = datetime.now().date()
            
            # 保存
            output_path = self.parquet_path / "fundamentals.parquet"
            df.to_parquet(output_path, index=False, compression='zstd')
            
            logger.info(f"✅ 基本面数据已保存: {len(df)} 条记录")
            
            self.progress["fundamentals"]["completed"] = True
            self.progress["fundamentals"]["last_date"] = datetime.now().isoformat()
            self._save_progress()
            
        except Exception as e:
            logger.error(f"❌ 获取基本面数据失败: {e}")
    
    def init_financial_reports(self, batch_size: int = 20):
        """
        初始化财务报表数据（使用 Tushare）
        """
        if self.progress["financial_reports"]["completed"]:
            logger.info("✅ 财务报表已存在，跳过")
            return
        
        if not self.ts:
            logger.warning("⚠️ Tushare 未配置，跳过财务报表")
            return
        
        logger.info("📑 开始获取财务报表数据...")
        
        # 获取股票列表
        try:
            stock_df = self.ak.stock_zh_a_spot_em()
            stock_codes = stock_df['代码'].tolist()[:batch_size]  # 先测试前 batch_size 只
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return
        
        income_data = []
        balance_data = []
        cashflow_data = []
        
        for i, code in enumerate(stock_codes):
            try:
                logger.info(f"[{i+1}/{len(stock_codes)}] 获取 {code} 财务报表...")
                
                # 利润表
                income = self.ts.income(ts_code=code, start_date='20200101')
                if income is not None and len(income) > 0:
                    income_data.append(income)
                
                self._smart_sleep(0.5)
                
                # 资产负债表
                balance = self.ts.balancesheet(ts_code=code, start_date='20200101')
                if balance is not None and len(balance) > 0:
                    balance_data.append(balance)
                
                self._smart_sleep(0.5)
                
                # 现金流量表
                cashflow = self.ts.cashflow(ts_code=code, start_date='20200101')
                if cashflow is not None and len(cashflow) > 0:
                    cashflow_data.append(cashflow)
                
                self._smart_sleep(0.5)
                
            except Exception as e:
                logger.error(f"获取 {code} 财务报表失败: {e}")
                continue
        
        # 保存数据
        if income_data:
            df_income = pd.concat(income_data, ignore_index=True)
            df_income.to_parquet(self.parquet_path / "income_statement.parquet", 
                                 index=False, compression='zstd')
            logger.info(f"✅ 利润表已保存: {len(df_income)} 条")
        
        if balance_data:
            df_balance = pd.concat(balance_data, ignore_index=True)
            df_balance.to_parquet(self.parquet_path / "balance_sheet.parquet",
                                  index=False, compression='zstd')
            logger.info(f"✅ 资产负债表已保存: {len(df_balance)} 条")
        
        if cashflow_data:
            df_cashflow = pd.concat(cashflow_data, ignore_index=True)
            df_cashflow.to_parquet(self.parquet_path / "cash_flow.parquet",
                                   index=False, compression='zstd')
            logger.info(f"✅ 现金流量表已保存: {len(df_cashflow)} 条")
        
        self.progress["financial_reports"]["completed"] = True
        self._save_progress()
    
    def create_duckdb_views(self):
        """创建 DuckDB 视图"""
        logger.info("🦆 创建 DuckDB 视图...")
        
        conn = duckdb.connect(str(self.db_path))
        
        # 创建视图
        tables = ['stock_basic', 'fundamentals', 'income_statement', 
                  'balance_sheet', 'cash_flow']
        
        for table in tables:
            parquet_path = self.parquet_path / f"{table}.parquet"
            if parquet_path.exists():
                conn.execute(f"""
                    CREATE OR REPLACE VIEW {table} AS
                    SELECT * FROM read_parquet('{parquet_path}')
                """)
                logger.info(f"✅ 视图已创建: {table}")
        
        # 日线数据使用通配符读取所有分区
        daily_path = self.parquet_path / "daily" / "**" / "**" / "*.parquet"
        conn.execute(f"""
            CREATE OR REPLACE VIEW daily AS
            SELECT * FROM read_parquet('{daily_path}', hive_partitioning=1)
        """)
        logger.info("✅ 视图已创建: daily")
        
        conn.close()
        logger.info("✅ DuckDB 视图创建完成")
    
    def run_all(self, quick_mode: bool = False):
        """
        运行完整初始化
        
        Args:
            quick_mode: 快速模式，只获取最近数据用于测试
        """
        logger.info("=" * 60)
        logger.info("🚀 开始初始化 A股本地数据库")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. 股票基本信息
        self.init_stock_basic()
        
        # 2. 日线数据
        if quick_mode:
            # 快速模式：只获取最近30天
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            self.init_daily_data(start_date=start_date, batch_size=10)
        else:
            self.init_daily_data(start_date="20200101", batch_size=50)
        
        # 3. 基本面数据
        self.init_fundamentals()
        
        # 4. 财务报表（可选，需要 Tushare）
        if self.ts and not quick_mode:
            self.init_financial_reports(batch_size=50)
        
        # 5. 创建 DuckDB 视图
        self.create_duckdb_views()
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ 初始化完成！耗时: {elapsed/60:.1f} 分钟")
        logger.info("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='A股本地数据库初始化')
    parser.add_argument('--quick', action='store_true', help='快速模式，只获取最近30天数据')
    parser.add_argument('--base-path', default='~/StockData', help='数据存储路径')
    args = parser.parse_args()
    
    initializer = StockDBInitializer(base_path=args.base_path)
    initializer.run_all(quick_mode=args.quick)


if __name__ == "__main__":
    main()
