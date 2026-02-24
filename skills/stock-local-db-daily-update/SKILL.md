# stock-local-db-daily-update

A股本地数据库每日增量更新

## 用途

每天运行一次，拉取最新的股票数据。

## 使用方法

### 手动运行

```bash
cd ~/.openclaw/workspace/scripts/stock-db
python daily_update.py
```

### 指定数据路径

```bash
python daily_update.py --base-path /path/to/data
```

## 更新内容

- 股票基本信息（价格、市值等）
- 日线数据（回溯5天，补全可能缺失的）
- 基本面数据
- DuckDB 视图刷新

## 每日更新时间

- **推荐时间**: 交易日 15:30 之后（收盘后30分钟）
- **预计耗时**: 10-20 分钟

## 自动化配置

### 使用 Cron (Mac/Linux)

```bash
# 编辑 crontab
crontab -e

# 添加每日 15:30 执行
crontab: 30 15 * * 1-5 cd ~/.openclaw/workspace/scripts/stock-db && python daily_update.py
```

### 使用 OpenClaw Cron

已配置自动任务，每日 15:30 执行。

## 更新报告

每次更新后会生成报告：

```
~/StockData/logs/update_report_YYYYMMDD.json
```

包含：
- 更新时间
- 更新股票数
- 新增记录数
- 存储占用

## 查看更新历史

```python
import json
with open('~/StockData/meta/daily_update_log.json') as f:
    history = json.load(f)
    print(history)
```
