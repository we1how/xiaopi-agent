# CLAUDE.md - 股票策略回测平台

## 项目概述

基于 backtesting.py + Streamlit 的股票策略回测平台 MVP 版本，支持：
- 从本地 DuckDB 数据库加载 A 股数据
- 运行和可视化策略回测结果
- 内置多种经典策略（SMA、RSI、MACD）
- 支持上传自定义策略文件

## 技术栈

| 组件 | 用途 | 版本 |
|------|------|------|
| backtesting.py | 回测引擎核心 | >=0.3.3 |
| Streamlit | Web 界面框架 | >=1.28.0 |
| DuckDB | 本地数据存储 | >=0.9.0 |
| Plotly | 交互式图表 | >=5.18.0 |
| Pandas | 数据处理 | >=2.0.0 |

## 项目结构

```
stock-platform/
├── app.py                 # Streamlit 主应用（Web UI）
├── data_loader.py         # 数据加载模块（DuckDB 连接）
├── backtest_engine.py     # 回测引擎封装
├── requirements.txt       # Python 依赖
├── README.md             # 用户文档
├── CLAUDE.md             # 开发者文档（本文件）
└── strategies/           # 策略目录
    ├── __init__.py       # 策略导出
    ├── sma_cross.py      # 双均线策略（含带过滤器版本）
    ├── rsi_strategy.py   # RSI 策略（含背离策略）
    ├── macd_strategy.py  # MACD 策略（含零轴/柱状图策略）
    └── template_strategy.py  # 策略模板（供用户参考）
```

## 核心模块详解

### 1. data_loader.py - 数据加载器

**核心类**: `StockDataLoader`

```python
# 初始化（默认数据路径 ~/StockData）
loader = StockDataLoader(base_path="~/StockData")

# 获取单只股票数据
df = loader.get_stock_data('000001', '2024-01-01', '2024-12-31')
# 返回 DataFrame: Date(index), Open, High, Low, Close, Volume

# 获取可用股票列表
stocks = loader.get_available_stocks(limit=100)

# 搜索股票
results = loader.search_stocks('茅台')
```

**数据格式要求**:
- 数据存储在 `~/StockData/parquet/`
- 日线数据: `daily/year=*/month=*/*.parquet` (Hive 分区格式)
- 股票基本信息: `stock_basic.parquet`

### 2. backtest_engine.py - 回测引擎

**核心类**: `BacktestEngine`

```python
# 初始化引擎
engine = BacktestEngine(
    data=df,                    # OHLCV DataFrame
    strategy_class=SmaCross,    # 策略类
    cash=100000,               # 初始资金
    commission=0.001           # 手续费率（千分之一）
)

# 运行回测
results = engine.run(n_short=10, n_long=20)

# 获取结果数据
engine.get_equity_curve()   # 权益曲线 DataFrame
engine.get_trades()         # 交易记录 DataFrame

# 参数优化
opt_results = engine.optimize(
    n_short=range(5, 50),
    n_long=range(10, 100),
    maximize='Sharpe Ratio'
)
```

**回测结果字段**:
- `total_return`: 总收益率 (%)
- `max_drawdown`: 最大回撤 (%)
- `sharpe_ratio`: 夏普比率
- `win_rate`: 胜率 (%)
- `total_trades`: 交易次数
- `sqn`: 系统质量数字

### 3. strategies/ - 策略模块

#### 策略基类要求

所有策略必须继承 `backtesting.Strategy`:

```python
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

class MyStrategy(Strategy):
    # 可调参数（类级别）
    param1 = 10
    param2 = 20

    def init(self):
        """初始化指标（回测开始前调用一次）"""
        close = pd.Series(self.data.Close)
        self.ma = self.I(
            lambda: close.rolling(self.param1).mean(),
            name=f'MA({self.param1})'
        )

    def next(self):
        """每个 K 线触发（交易逻辑）"""
        if not self.position:           # 无持仓
            if crossover(self.ma1, self.ma2):
                self.buy()              # 买入
        else:                           # 有持仓
            if crossover(self.ma2, self.ma1):
                self.sell()             # 卖出
```

#### 内置策略列表

| 策略 | 文件 | 说明 |
|------|------|------|
| `SmaCross` | sma_cross.py | 双均线金叉死叉 |
| `SmaCrossWithFilters` | sma_cross.py | 带成交量/趋势过滤的 SMA |
| `RsiStrategy` | rsi_strategy.py | RSI 超买超卖 |
| `RsiWithMaFilter` | rsi_strategy.py | RSI + 均线过滤 |
| `RsiDivergence` | rsi_strategy.py | RSI 背离检测 |
| `MacdStrategy` | macd_strategy.py | MACD 金叉死叉 |
| `MacdZeroLine` | macd_strategy.py | MACD 零轴策略 |
| `MacdHistogram` | macd_strategy.py | MACD 柱状图策略 |

#### 策略开发模式

**模式1: 继承现有策略**
```python
from strategies.sma_cross import SmaCross

class MySMA(SmaCross):
    n_short = 5    # 覆盖默认参数
    n_long = 30
```

**模式2: 从模板创建**
```python
# 复制 template_strategy.py 并修改
# 包含止损、仓位管理等示例代码
```

**模式3: 完全自定义**
```python
# 参考 backtesting.py 官方文档
# 可使用所有 pandas/ta-lib 指标
```

## 常用开发任务

### 添加新内置策略

1. 在 `strategies/` 目录创建新文件（如 `bollinger_strategy.py`）
2. 实现策略类，继承 `Strategy`
3. 在 `strategies/__init__.py` 中导出
4. 在 `app.py` 中添加到策略选择列表

### 修改数据加载逻辑

数据加载器支持多种数据源模式：

```python
# data_loader.py 中的 _init_views() 方法
# 当前支持 Hive 分区格式的 parquet 文件

# 如需修改数据格式，修改此方法的 SQL 视图创建逻辑
```

### 添加新的回测指标

在 `backtest_engine.py` 的 `run()` 方法中添加：

```python
results = {
    # ... 现有指标
    'my_custom_metric': calculate_metric(),
}
```

### 修改 UI 样式

```python
# app.py 中的 CSS 样式块
st.markdown("""
<style>
    /* 修改这里 */
</style>
""", unsafe_allow_html=True)
```

## 运行和调试

### 启动应用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Streamlit
streamlit run app.py

# 指定端口
streamlit run app.py --server.port 8501
```

### 命令行测试

```bash
# 测试数据加载
python data_loader.py

# 测试回测引擎
python backtest_engine.py

# 测试策略
python strategies/sma_cross.py
```

### 常见问题

**Q: 数据加载失败**
- 检查 `~/StockData/` 目录是否存在
- 检查 parquet 文件格式是否正确
- 查看控制台错误信息

**Q: 策略加载失败**
- 确保策略类继承自 `backtesting.Strategy`
- 检查策略文件语法错误
- 使用 `python -m py_compile strategy.py` 检查

**Q: 回测结果异常**
- 检查数据是否包含 NaN 值
- 确保数据按日期升序排列
- 验证 OHLC 数据合理性（High >= Close >= Low）

## 关键代码路径

| 功能 | 文件 | 行号 |
|------|------|------|
| 主应用入口 | app.py | 403-467 |
| 侧边栏参数 | app.py | 85-203 |
| 策略加载 | app.py | 66-82 |
| 数据获取 | data_loader.py | 56-111 |
| 回测执行 | backtest_engine.py | 65-114 |
| 指标计算 | backtest_engine.py | 78-102 |

## 扩展资源

- [backtesting.py 文档](https://kernc.github.io/backtesting.py/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [DuckDB 文档](https://duckdb.org/docs/)
