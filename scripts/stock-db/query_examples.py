#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股本地数据库 - 查询示例
展示如何使用 DuckDB + Parquet 进行数据查询
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


class StockQuery:
    """股票数据查询类"""
    
    def __init__(self, base_path: str = "~/StockData"):
        self.base_path = Path(base_path).expanduser()
        self.parquet_path = self.base_path / "parquet"
        self.db_path = self.base_path / "stock.duckdb"
        
        # 连接 DuckDB
        self.conn = duckdb.connect(str(self.db_path))
        self._init_views()
    
    def _init_views(self):
        """初始化视图"""
        # 日线数据视图
        daily_path = self.parquet_path / "daily" / "**" / "**" / "*.parquet"
        self.conn.execute(f"""
            CREATE OR REPLACE VIEW daily AS
            SELECT * FROM read_parquet('{daily_path}', hive_partitioning=1)
        """)
        
        # 其他表视图
        tables = ['stock_basic', 'fundamentals', 'income_statement', 
                  'balance_sheet', 'cash_flow']
        for table in tables:
            parquet_path = self.parquet_path / f"{table}.parquet"
            if parquet_path.exists():
                self.conn.execute(f"""
                    CREATE OR REPLACE VIEW {table} AS
                    SELECT * FROM read_parquet('{parquet_path}')
                """)
    
    def get_stock_history(self, code: str, days: int = 30) -> pd.DataFrame:
        """
        获取单只股票历史数据
        
        Args:
            code: 股票代码 (如: 000001)
            days: 获取最近多少天的数据
        
        Returns:
            DataFrame 包含日线数据
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        query = f"""
            SELECT 
                ts_code,
                trade_date,
                open,
                high,
                low,
                close,
                vol,
                amount,
                pct_chg,
                turnover_rate
            FROM daily
            WHERE ts_code = '{code}'
              AND trade_date >= '{start_date}'
            ORDER BY trade_date DESC
        """
        
        return self.conn.execute(query).fetchdf()
    
    def get_industry_stocks(self, industry: str) -> pd.DataFrame:
        """
        获取某个行业的所有股票
        
        Args:
            industry: 行业名称 (如: '银行', '医药生物')
        """
        query = f"""
            SELECT 
                s.symbol,
                s.name,
                s.close,
                s.pct_chg,
                s.total_mv,
                s.pe,
                s.pb
            FROM stock_basic s
            WHERE s.name LIKE '%{industry}%'
               OR s.industry = '{industry}'
            ORDER BY s.total_mv DESC
        """
        
        return self.conn.execute(query).fetchdf()
    
    def get_top_gainers(self, days: int = 1, limit: int = 20) -> pd.DataFrame:
        """
        获取涨幅最大的股票
        
        Args:
            days: 多少天内
            limit: 返回多少条
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        query = f"""
            SELECT 
                d.ts_code,
                s.name,
                d.close,
                d.pct_chg,
                d.vol,
                d.amount,
                d.trade_date
            FROM daily d
            JOIN stock_basic s ON d.ts_code = s.symbol
            WHERE d.trade_date >= '{start_date}'
            ORDER BY d.pct_chg DESC
            LIMIT {limit}
        """
        
        return self.conn.execute(query).fetchdf()
    
    def get_stock_fundamentals(self, code: str) -> pd.DataFrame:
        """
        获取股票基本面数据
        
        Args:
            code: 股票代码
        """
        query = f"""
            SELECT *
            FROM fundamentals
            WHERE ts_code = '{code}'
            ORDER BY trade_date DESC
            LIMIT 1
        """
        
        return self.conn.execute(query).fetchdf()
    
    def custom_query(self, sql: str) -> pd.DataFrame:
        """
        执行自定义 SQL 查询
        
        Args:
            sql: SQL 查询语句
        """
        return self.conn.execute(sql).fetchdf()
    
    def export_to_csv(self, query: str, output_path: str):
        """
        导出查询结果到 CSV
        
        Args:
            query: SQL 查询
            output_path: 输出文件路径
        """
        df = self.conn.execute(query).fetchdf()
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 已导出到: {output_path}")
    
    def export_to_excel(self, query: str, output_path: str):
        """
        导出查询结果到 Excel
        
        Args:
            query: SQL 查询
            output_path: 输出文件路径
        """
        df = self.conn.execute(query).fetchdf()
        df.to_excel(output_path, index=False)
        print(f"✅ 已导出到: {output_path}")
    
    def get_market_overview(self) -> pd.DataFrame:
        """获取市场概览数据"""
        query = """
            SELECT 
                COUNT(*) as total_stocks,
                AVG(pct_chg) as avg_change,
                MAX(pct_chg) as max_gain,
                MIN(pct_chg) as max_loss,
                SUM(amount) as total_amount
            FROM daily
            WHERE trade_date = (SELECT MAX(trade_date) FROM daily)
        """
        
        return self.conn.execute(query).fetchdf()
    
    def get_volume_leaders(self, limit: int = 20) -> pd.DataFrame:
        """获取成交量排行"""
        query = f"""
            SELECT 
                d.ts_code,
                s.name,
                d.vol,
                d.amount,
                d.pct_chg
            FROM daily d
            JOIN stock_basic s ON d.ts_code = s.symbol
            WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily)
            ORDER BY d.vol DESC
            LIMIT {limit}
        """
        
        return self.conn.execute(query).fetchdf()
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def demo():
    """查询示例演示"""
    print("=" * 60)
    print("🚀 A股本地数据库查询示例")
    print("=" * 60)
    
    query = StockQuery()
    
    # 示例 1: 获取单只股票历史数据
    print("\n📈 示例 1: 获取贵州茅台(600519)最近30天数据")
    df = query.get_stock_history("600519", days=30)
    print(df.head(10))
    
    # 示例 2: 获取涨幅排行
    print("\n📊 示例 2: 今日涨幅前10名")
    df = query.get_top_gainers(days=1, limit=10)
    print(df)
    
    # 示例 3: 市场概览
    print("\n🌍 示例 3: 市场概览")
    df = query.get_market_overview()
    print(df)
    
    # 示例 4: 自定义 SQL 查询
    print("\n🔍 示例 4: 自定义查询 - 市值大于1000亿的股票")
    sql = """
        SELECT symbol, name, total_mv, pe, pb
        FROM stock_basic
        WHERE total_mv > 10000000
        ORDER BY total_mv DESC
        LIMIT 10
    """
    df = query.custom_query(sql)
    print(df)
    
    # 示例 5: 导出数据
    print("\n💾 示例 5: 导出数据到 CSV")
    query.export_to_csv(
        "SELECT * FROM stock_basic LIMIT 100",
        "~/Desktop/top100_stocks.csv"
    )
    
    query.close()
    
    print("\n✅ 所有示例执行完成！")


if __name__ == "__main__":
    demo()
