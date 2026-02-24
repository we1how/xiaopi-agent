#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股本地数据库 - 数据库结构设计
基于 DuckDB + Parquet 的本地股票数据库系统

表结构定义：
- daily: 日线数据
- minute: 1分钟K线数据
- fundamentals: 基本面数据
- financial_reports: 财务报表
- meta: 元数据管理
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import duckdb
from pathlib import Path


@dataclass
class TableSchema:
    """表结构定义"""
    name: str
    columns: Dict[str, str]
    partition_by: Optional[List[str]] = None
    primary_key: Optional[List[str]] = None


class StockDatabaseSchema:
    """
    A股数据库表结构设计
    
    设计理念：
    1. 所有数据以 Parquet 格式存储，DuckDB 提供 SQL 查询接口
    2. 按日期分区，便于增量更新和查询优化
    3. 统一字段命名规范，便于跨表关联
    """
    
    def __init__(self, base_path: str = "~/StockData/parquet"):
        self.base_path = Path(base_path).expanduser()
        self.tables = self._define_tables()
    
    def _define_tables(self) -> Dict[str, TableSchema]:
        """定义所有表结构"""
        
        # 1. 日线数据表
        daily = TableSchema(
            name="daily",
            columns={
                "ts_code": "VARCHAR",           # 股票代码 (如: 000001.SZ)
                "trade_date": "DATE",           # 交易日期
                "open": "DOUBLE",               # 开盘价
                "high": "DOUBLE",               # 最高价
                "low": "DOUBLE",                # 最低价
                "close": "DOUBLE",              # 收盘价
                "pre_close": "DOUBLE",          # 昨收价
                "change": "DOUBLE",             # 涨跌额
                "pct_chg": "DOUBLE",            # 涨跌幅(%)
                "vol": "BIGINT",                # 成交量(手)
                "amount": "DOUBLE",             # 成交额(千元)
                "turnover_rate": "DOUBLE",      # 换手率(%)
                "turnover_rate_f": "DOUBLE",    # 换手率(自由流通股)
                "volume_ratio": "DOUBLE",       # 量比
                "pe": "DOUBLE",                 # 市盈率
                "pe_ttm": "DOUBLE",             # 市盈率TTM
                "pb": "DOUBLE",                 # 市净率
                "ps": "DOUBLE",                 # 市销率
                "ps_ttm": "DOUBLE",             # 市销率TTM
                "dv_ratio": "DOUBLE",           # 股息率(%)
                "dv_ttm": "DOUBLE",             # 股息率TTM(%)
                "total_share": "DOUBLE",        # 总股本(万股)
                "float_share": "DOUBLE",        # 流通股本(万股)
                "free_share": "DOUBLE",         # 自由流通股本(万股)
                "total_mv": "DOUBLE",           # 总市值(万元)
                "circ_mv": "DOUBLE",            # 流通市值(万元)
            },
            partition_by=["trade_date"],
            primary_key=["ts_code", "trade_date"]
        )
        
        # 2. 1分钟K线数据表
        minute = TableSchema(
            name="minute",
            columns={
                "ts_code": "VARCHAR",           # 股票代码
                "trade_time": "TIMESTAMP",      # 交易时间
                "open": "DOUBLE",               # 开盘价
                "high": "DOUBLE",               # 最高价
                "low": "DOUBLE",                # 最低价
                "close": "DOUBLE",              # 收盘价
                "vol": "BIGINT",                # 成交量
                "amount": "DOUBLE",             # 成交额
            },
            partition_by=["trade_date"],
            primary_key=["ts_code", "trade_time"]
        )
        
        # 3. 基本面数据表
        fundamentals = TableSchema(
            name="fundamentals",
            columns={
                "ts_code": "VARCHAR",           # 股票代码
                "trade_date": "DATE",           # 交易日期
                "name": "VARCHAR",              # 股票名称
                "industry": "VARCHAR",          # 行业
                "area": "VARCHAR",              # 地域
                "pe": "DOUBLE",                 # 市盈率
                "pe_ttm": "DOUBLE",             # 市盈率TTM
                "pb": "DOUBLE",                 # 市净率
                "ps": "DOUBLE",                 # 市销率
                "ps_ttm": "DOUBLE",             # 市销率TTM
                "total_share": "DOUBLE",        # 总股本
                "float_share": "DOUBLE",        # 流通股本
                "total_mv": "DOUBLE",           # 总市值
                "circ_mv": "DOUBLE",            # 流通市值
                "dv_ratio": "DOUBLE",           # 股息率
                "dv_ttm": "DOUBLE",             # 股息率TTM
                "eps": "DOUBLE",                # 每股收益
                "bps": "DOUBLE",                # 每股净资产
            },
            partition_by=["trade_date"],
            primary_key=["ts_code", "trade_date"]
        )
        
        # 4. 财务报表表 - 利润表
        income_statement = TableSchema(
            name="income_statement",
            columns={
                "ts_code": "VARCHAR",           # 股票代码
                "ann_date": "DATE",             # 公告日期
                "f_ann_date": "DATE",           # 实际公告日期
                "end_date": "DATE",             # 报告期截止日
                "report_type": "VARCHAR",       # 报告类型
                "comp_type": "VARCHAR",         # 公司类型
                "basic_eps": "DOUBLE",          # 基本每股收益
                "diluted_eps": "DOUBLE",        # 稀释每股收益
                "total_revenue": "DOUBLE",      # 营业总收入
                "revenue": "DOUBLE",            # 营业收入
                "total_cogs": "DOUBLE",         # 营业总成本
                "oper_cost": "DOUBLE",          # 营业成本
                "int_exp": "DOUBLE",            # 利息支出
                "biz_tax_surchg": "DOUBLE",     # 营业税金及附加
                "sell_exp": "DOUBLE",           # 销售费用
                "admin_exp": "DOUBLE",          # 管理费用
                "fin_exp": "DOUBLE",            # 财务费用
                "operate_profit": "DOUBLE",     # 营业利润
                "total_profit": "DOUBLE",       # 利润总额
                "n_income": "DOUBLE",           # 净利润
                "n_income_attr_p": "DOUBLE",    # 归母净利润
            },
            partition_by=["end_date"],
            primary_key=["ts_code", "end_date", "report_type"]
        )
        
        # 5. 财务报表表 - 资产负债表
        balance_sheet = TableSchema(
            name="balance_sheet",
            columns={
                "ts_code": "VARCHAR",           # 股票代码
                "ann_date": "DATE",             # 公告日期
                "f_ann_date": "DATE",           # 实际公告日期
                "end_date": "DATE",             # 报告期截止日
                "report_type": "VARCHAR",       # 报告类型
                "comp_type": "VARCHAR",         # 公司类型
                "total_assets": "DOUBLE",       # 资产总计
                "total_liab": "DOUBLE",         # 负债合计
                "total_hldr_eqy_exc_min_int": "DOUBLE",  # 股东权益合计
                "total_hldr_eqy_inc_min_int": "DOUBLE",  # 股东权益合计(含少数股东)
                "total_liab_hldr_eqy": "DOUBLE",         # 负债及股东权益总计
                "money_cap": "DOUBLE",          # 货币资金
                "trad_asset": "DOUBLE",         # 交易性金融资产
                "notes_receiv": "DOUBLE",       # 应收票据
                "accounts_receiv": "DOUBLE",    # 应收账款
                "inventories": "DOUBLE",        # 存货
                "total_cur_assets": "DOUBLE",   # 流动资产合计
                "fix_assets": "DOUBLE",         # 固定资产
                "total_nca": "DOUBLE",          # 非流动资产合计
                "notes_payable": "DOUBLE",      # 应付票据
                "acct_payable": "DOUBLE",       # 应付账款
                "total_cur_liab": "DOUBLE",     # 流动负债合计
                "total_nc_liab": "DOUBLE",      # 非流动负债合计
            },
            partition_by=["end_date"],
            primary_key=["ts_code", "end_date", "report_type"]
        )
        
        # 6. 财务报表表 - 现金流量表
        cash_flow = TableSchema(
            name="cash_flow",
            columns={
                "ts_code": "VARCHAR",           # 股票代码
                "ann_date": "DATE",             # 公告日期
                "f_ann_date": "DATE",           # 实际公告日期
                "end_date": "DATE",             # 报告期截止日
                "report_type": "VARCHAR",       # 报告类型
                "comp_type": "VARCHAR",         # 公司类型
                "net_profit": "DOUBLE",         # 净利润
                "finan_exp": "DOUBLE",          # 财务费用
                "c_fr_sale_sg": "DOUBLE",       # 销售商品提供劳务收到的现金
                "c_paid_for_taxes": "DOUBLE",   # 支付的各项税费
                "c_paid_to_for_empl": "DOUBLE", # 支付给职工的现金
                "n_cashflow_act": "DOUBLE",     # 经营活动现金流净额
                "n_cashflow_inv_act": "DOUBLE", # 投资活动现金流净额
                "n_cash_flows_fnc_act": "DOUBLE",  # 筹资活动现金流净额
                "free_cashflow": "DOUBLE",      # 企业自由现金流
            },
            partition_by=["end_date"],
            primary_key=["ts_code", "end_date", "report_type"]
        )
        
        # 7. 元数据表
        meta = TableSchema(
            name="meta",
            columns={
                "table_name": "VARCHAR",        # 表名
                "last_update": "TIMESTAMP",     # 最后更新时间
                "data_start": "DATE",           # 数据开始日期
                "data_end": "DATE",             # 数据结束日期
                "record_count": "BIGINT",       # 记录数
                "file_path": "VARCHAR",         # 文件路径
                "version": "VARCHAR",           # 版本号
                "description": "VARCHAR",       # 描述
            },
            primary_key=["table_name"]
        )
        
        # 8. 股票基本信息表
        stock_basic = TableSchema(
            name="stock_basic",
            columns={
                "ts_code": "VARCHAR",           # TS代码
                "symbol": "VARCHAR",            # 股票代码
                "name": "VARCHAR",              # 股票名称
                "area": "VARCHAR",              # 地域
                "industry": "VARCHAR",          # 所属行业
                "fullname": "VARCHAR",          # 股票全称
                "enname": "VARCHAR",            # 英文名称
                "cnspell": "VARCHAR",           # 拼音缩写
                "market": "VARCHAR",            # 市场类型
                "exchange": "VARCHAR",          # 交易所代码
                "curr_type": "VARCHAR",         # 交易货币
                "list_status": "VARCHAR",       # 上市状态
                "list_date": "DATE",            # 上市日期
                "delist_date": "DATE",          # 退市日期
                "is_hs": "VARCHAR",             # 是否沪深港通标的
            },
            primary_key=["ts_code"]
        )
        
        return {
            "daily": daily,
            "minute": minute,
            "fundamentals": fundamentals,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "meta": meta,
            "stock_basic": stock_basic,
        }
    
    def get_create_table_sql(self, table_name: str) -> str:
        """生成创建表的 SQL 语句"""
        if table_name not in self.tables:
            raise ValueError(f"未知表名: {table_name}")
        
        schema = self.tables[table_name]
        columns_def = ",\n    ".join([f"{col} {dtype}" for col, dtype in schema.columns.items()])
        
        sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
    {columns_def}
)"""
        return sql
    
    def get_parquet_path(self, table_name: str) -> Path:
        """获取表的 Parquet 文件路径"""
        return self.base_path / f"{table_name}.parquet"
    
    def get_partitioned_parquet_path(self, table_name: str, partition_value: str) -> Path:
        """获取分区表的 Parquet 文件路径"""
        return self.base_path / table_name / f"{partition_value}.parquet"
    
    def init_database(self, conn: duckdb.DuckDBPyConnection):
        """初始化数据库，创建所有表"""
        for table_name in self.tables:
            sql = self.get_create_table_sql(table_name)
            conn.execute(sql)
        
        # 创建 Parquet 视图
        for table_name, schema in self.tables.items():
            parquet_path = self.get_parquet_path(table_name)
            if parquet_path.exists():
                conn.execute(f"""
                    CREATE OR REPLACE VIEW {table_name}_view AS
                    SELECT * FROM read_parquet('{parquet_path}')
                """)


def create_all_tables(db_path: str = "~/StockData/stock.duckdb"):
    """
    创建所有表的便捷函数
    
    Usage:
        from database_schema import create_all_tables
        create_all_tables()
    """
    db_path = Path(db_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = duckdb.connect(str(db_path))
    schema = StockDatabaseSchema()
    schema.init_database(conn)
    conn.close()
    print(f"✅ 数据库初始化完成: {db_path}")


if __name__ == "__main__":
    # 测试创建表结构
    create_all_tables()
    
    # 打印所有表结构
    schema = StockDatabaseSchema()
    print("\n📊 数据库表结构:")
    print("=" * 60)
    for name, table in schema.tables.items():
        print(f"\n🔹 {name}")
        print(f"   字段数: {len(table.columns)}")
        print(f"   主键: {table.primary_key}")
        print(f"   分区: {table.partition_by}")
