#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载模块
负责从本地 DuckDB 数据库加载股票数据
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List


class StockDataLoader:
    """股票数据加载器"""
    
    def __init__(self, base_path: str = "~/StockData"):
        self.base_path = Path(base_path).expanduser()
        self.parquet_path = self.base_path / "parquet"
        self.db_path = self.base_path / "stock.duckdb"
        
        # 连接 DuckDB
        self.conn = duckdb.connect(str(self.db_path))
        self._init_views()
    
    def _init_views(self):
        """初始化视图"""
        # 日线数据视图 - 支持分区路径
        daily_path = self.parquet_path / "daily" / "**" / "**" / "*.parquet"
        try:
            self.conn.execute(f"""
                CREATE OR REPLACE VIEW daily AS
                SELECT * FROM read_parquet('{daily_path}', hive_partitioning=1)
            """)
        except Exception as e:
            print(f"Warning: daily view creation failed: {e}")
        
        # 其他表视图
        tables = ['stock_basic', 'fundamentals', 'income_statement', 
                  'balance_sheet', 'cash_flow']
        for table in tables:
            parquet_path = self.parquet_path / f"{table}.parquet"
            if parquet_path.exists():
                try:
                    self.conn.execute(f"""
                        CREATE OR REPLACE VIEW {table} AS
                        SELECT * FROM read_parquet('{parquet_path}')
                    """)
                except Exception as e:
                    print(f"Warning: {table} view creation failed: {e}")
    
    def get_stock_data(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        获取单只股票的历史数据
        
        Args:
            code: 股票代码 (如: 000001, 600519)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame 包含 OHLCV 数据，格式适配 backtesting.py
        """
        # 标准化股票代码格式
        if '.' not in code:
            # 根据代码前缀判断交易所
            if code.startswith('6'):
                code = f"{code}.SH"
            elif code.startswith('0') or code.startswith('3'):
                code = f"{code}.SZ"
            elif code.startswith('8') or code.startswith('4'):
                code = f"{code}.BJ"
        
        query = f"""
            SELECT 
                trade_date as Date,
                open as Open,
                high as High,
                low as Low,
                close as Close,
                vol as Volume
            FROM daily
            WHERE ts_code = '{code}'
              AND trade_date >= '{start_date}'
              AND trade_date <= '{end_date}'
            ORDER BY trade_date ASC
        """
        
        df = self.conn.execute(query).fetchdf()
        
        if df.empty:
            return df
        
        # 设置日期索引（backtesting.py 要求）
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # 确保列名首字母大写（backtesting.py 要求）
        df.columns = [col.capitalize() if col.lower() in ['open', 'high', 'low', 'close', 'volume'] 
                      else col for col in df.columns]
        
        return df
    
    def get_available_stocks(self, limit: int = 1000) -> pd.DataFrame:
        """
        获取可用股票列表
        
        Returns:
            DataFrame 包含股票代码和名称
        """
        # 尝试从 stock_basic 表获取
        parquet_path = self.parquet_path / "stock_basic.parquet"
        
        if parquet_path.exists():
            query = f"""
                SELECT 
                    symbol as code,
                    name,
                    industry,
                    market
                FROM stock_basic
                WHERE list_status = 'L'
                ORDER BY total_mv DESC
                LIMIT {limit}
            """
            try:
                return self.conn.execute(query).fetchdf()
            except:
                pass
        
        # 从 daily 表获取股票列表
        query = f"""
            SELECT DISTINCT ts_code as code
            FROM daily
            LIMIT {limit}
        """
        
        try:
            return self.conn.execute(query).fetchdf()
        except Exception as e:
            print(f"Error getting stock list: {e}")
            return pd.DataFrame(columns=['code'])
    
    def get_stock_info(self, code: str) -> Optional[pd.Series]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
        
        Returns:
            股票信息 Series
        """
        if '.' not in code:
            if code.startswith('6'):
                code = f"{code}.SH"
            elif code.startswith('0') or code.startswith('3'):
                code = f"{code}.SZ"
            elif code.startswith('8') or code.startswith('4'):
                code = f"{code}.BJ"
        
        parquet_path = self.parquet_path / "stock_basic.parquet"
        
        if parquet_path.exists():
            query = f"""
                SELECT *
                FROM stock_basic
                WHERE symbol = '{code}' OR ts_code = '{code}'
                LIMIT 1
            """
            try:
                df = self.conn.execute(query).fetchdf()
                if not df.empty:
                    return df.iloc[0]
            except:
                pass
        
        return None
    
    def get_date_range(self) -> tuple:
        """
        获取数据的日期范围
        
        Returns:
            (最早日期, 最晚日期)
        """
        query = """
            SELECT 
                MIN(trade_date) as min_date,
                MAX(trade_date) as max_date
            FROM daily
        """
        
        try:
            df = self.conn.execute(query).fetchdf()
            if not df.empty:
                return df.iloc[0]['min_date'], df.iloc[0]['max_date']
        except Exception as e:
            print(f"Error getting date range: {e}")
        
        # 默认返回最近一年的范围
        end = datetime.now()
        start = end - timedelta(days=365)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词（代码或名称）
        
        Returns:
            匹配的股票列表
        """
        parquet_path = self.parquet_path / "stock_basic.parquet"
        
        if parquet_path.exists():
            query = f"""
                SELECT 
                    symbol as code,
                    name,
                    industry
                FROM stock_basic
                WHERE symbol LIKE '%{keyword}%'
                   OR name LIKE '%{keyword}%'
                   OR cnspell LIKE '%{keyword}%'
                LIMIT 20
            """
            try:
                return self.conn.execute(query).fetchdf()
            except:
                pass
        
        return pd.DataFrame(columns=['code', 'name', 'industry'])
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# 便捷函数
def load_stock_data(
    code: str, 
    start_date: str, 
    end_date: str,
    base_path: str = "~/StockData"
) -> pd.DataFrame:
    """
    便捷函数：加载股票数据
    
    Example:
        df = load_stock_data('000001', '2023-01-01', '2023-12-31')
    """
    loader = StockDataLoader(base_path)
    try:
        data = loader.get_stock_data(code, start_date, end_date)
        return data
    finally:
        loader.close()


if __name__ == "__main__":
    # 测试代码
    print("测试数据加载器...")
    
    loader = StockDataLoader()
    
    # 测试获取日期范围
    min_date, max_date = loader.get_date_range()
    print(f"\n数据日期范围: {min_date} ~ {max_date}")
    
    # 测试获取股票数据
    print("\n获取贵州茅台(600519)最近30天数据:")
    df = loader.get_stock_data('600519', '2024-01-01', '2024-12-31')
    print(df.head())
    print(f"\n数据条数: {len(df)}")
    
    # 测试获取股票列表
    print("\n获取股票列表(前10条):")
    stocks = loader.get_available_stocks(10)
    print(stocks)
    
    loader.close()
    print("\n测试完成!")
