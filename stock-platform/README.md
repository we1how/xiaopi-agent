# 股票策略回测平台

基于 backtesting.py + Streamlit 的股票策略回测平台 MVP 版本

## 功能特性

- 📈 **股票数据查询** - 连接本地 DuckDB 数据库
- 🔄 **策略回测** - 基于 backtesting.py 引擎
- 📊 **可视化分析** - Streamlit 仪表盘展示结果
- 📝 **策略管理** - 支持上传/选择策略文件

## 项目结构

```
stock-platform/
├── app.py                 # Streamlit 主应用
├── data_loader.py         # 数据加载模块
├── backtest_engine.py     # 回测引擎
├── requirements.txt       # 依赖包
├── README.md             # 说明文档
└── strategies/           # 示例策略目录
    ├── __init__.py
    └── sma_cross.py      # 双均线策略示例
```

## 快速启动

### 1. 安装依赖

```bash
cd /Users/linweihao/.openclaw/workspace/stock-platform
python3 -m pip install -r requirements.txt
```

### 2. 启动应用

```bash
cd /Users/linweihao/.openclaw/workspace/stock-platform
streamlit run app.py
```

应用将在 http://localhost:8501 启动

或者指定端口：
```bash
streamlit run app.py --server.port 8501
```

## 使用说明

1. **选择股票** - 输入股票代码（如: 000001, 600519）
2. **设置时间范围** - 选择回测开始和结束日期
3. **选择策略** - 从预设策略中选择或上传自定义策略文件
4. **运行回测** - 点击运行按钮查看结果

## 策略文件格式

策略文件需遵循 backtesting.py 的标准格式：

```python
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

class MyStrategy(Strategy):
    # 策略参数
    param1 = 10
    param2 = 20
    
    def init(self):
        # 初始化指标
        self.sma1 = self.I(lambda: pd.Series(self.data.Close).rolling(self.param1).mean())
        self.sma2 = self.I(lambda: pd.Series(self.data.Close).rolling(self.param2).mean())
    
    def next(self):
        # 交易逻辑
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()
```

## 数据说明

数据来源于本地 DuckDB 数据库（~/StockData/），包含：
- 日线数据（daily）
- 股票基本信息（stock_basic）
- 基本面数据（fundamentals）

## 依赖要求

- Python 3.12+
- backtesting.py
- streamlit
- pandas
- numpy
- plotly
- duckdb
