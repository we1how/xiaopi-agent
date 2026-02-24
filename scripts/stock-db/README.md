# A股本地股票数据库

基于 DuckDB + Parquet 的高性能本地股票数据库系统。

## 架构特点

- **存储**: Parquet 列式存储，压缩率高，查询快
- **查询**: DuckDB 提供 SQL 接口，支持复杂分析
- **数据源**: Akshare 为主 (免费无限制) + Tushare 财报 (高质量)
- **更新**: 增量更新，断点续传

## 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/scripts/stock-db
pip install -r requirements.txt
```

### 2. 首次初始化

```bash
# 快速模式（测试用，只拉最近30天）
python init_stock_db.py --quick

# 完整模式（全部历史数据）
python init_stock_db.py
```

### 3. 每日更新

```bash
python daily_update.py
```

### 4. 查询数据

```python
from query_examples import StockQuery

query = StockQuery()

# 获取单只股票历史
df = query.get_stock_history("600519", days=30)

# 获取涨幅排行
df = query.get_top_gainers(limit=20)

# 自定义 SQL
df = query.custom_query("SELECT * FROM daily LIMIT 10")
```

## 数据存储

```
~/StockData/
├── parquet/              # 数据文件
│   ├── stock_basic.parquet
│   ├── daily/            # 分区存储 (year=2024/month=01/)
│   ├── fundamentals.parquet
│   ├── income_statement.parquet
│   ├── balance_sheet.parquet
│   └── cash_flow.parquet
├── meta/                 # 元数据
├── logs/                 # 日志
└── stock.duckdb          # DuckDB 数据库
```

## 预计时间表

| 阶段 | 内容 | 预计时间 |
|-----|------|---------|
| Day 1 | 股票基本信息 + 基本面 | 5-10 分钟 |
| Day 2 | 日线数据 (2020至今) | 4-6 小时 |
| Day 3 | 财务报表 (Tushare) | 1-2 小时 |
| 每日 | 增量更新 | 10-20 分钟 |

## 文件说明

- `database_schema.py` - 数据库表结构定义
- `init_stock_db.py` - 首次初始化脚本
- `daily_update.py` - 每日增量更新
- `query_examples.py` - 查询示例
- `Dockerfile` / `docker-compose.yml` - Docker 配置

## Docker 使用 (Windows 备用)

```bash
# 初始化
docker-compose run --rm stock-db-init

# 每日更新
docker-compose run --rm stock-db-daily
```

## 注意事项

1. **空间占用**: 日线数据约 5-10GB，全部数据约 15-20GB
2. **Rate Limit**: Akshare 免费无限制，Tushare 有积分限制
3. **更新时机**: 建议交易日 15:30 后执行

## 后续优化

- [ ] 添加分钟线数据支持
- [ ] 添加实时数据接口
- [ ] 添加更多技术指标计算
- [ ] 添加回测框架集成
