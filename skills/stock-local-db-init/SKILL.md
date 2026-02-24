# stock-local-db-init

初始化 A股本地股票数据库 (DuckDB + Parquet)

## 用途

首次运行，拉取历史数据建立本地数据库。

## 安装依赖

```bash
cd ~/.openclaw/workspace/scripts/stock-db
pip install -r requirements.txt
```

## 使用方法

### 快速模式（测试用，只拉最近30天）

```bash
python init_stock_db.py --quick
```

### 完整模式（拉全部历史数据）

```bash
python init_stock_db.py
```

### 指定数据路径

```bash
python init_stock_db.py --base-path /path/to/data
```

## 数据存储位置

默认: `~/StockData/`

```
~/StockData/
├── parquet/          # Parquet 数据文件
│   ├── stock_basic.parquet
│   ├── daily/        # 按年月分区的日线数据
│   ├── fundamentals.parquet
│   ├── income_statement.parquet
│   ├── balance_sheet.parquet
│   └── cash_flow.parquet
├── meta/             # 元数据和进度
│   ├── init_progress.json
│   └── daily_update_log.json
├── logs/             # 日志文件
└── stock.duckdb      # DuckDB 数据库
```

## 预计时间表

| 数据类型 | 预计时间 | 说明 |
|---------|---------|------|
| 股票基本信息 | 1-2 分钟 | 5000+ 只股票 |
| 日线数据 (2020至今) | 4-6 小时 | 分批拉取，智能延时 |
| 基本面数据 | 2-3 分钟 | 每日指标 |
| 财务报表 (Tushare) | 1-2 小时 | 前50只测试，全量需更久 |

**建议分阶段执行：**
1. 第1天: 股票基本信息 + 基本面
2. 第2天: 日线数据 (可分批)
3. 第3天: 财务报表

## 断点续传

如果中断，再次运行会自动从上次位置继续。

## Tushare 配置

Token 已保存在 `~/.openclaw/credentials/tushare.json`
