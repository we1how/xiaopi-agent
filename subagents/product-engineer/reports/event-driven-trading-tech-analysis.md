# 事件驱动选股体系技术实现方案

> 版本：v1.0  
> 日期：2026-03-06  
> 类型：技术分析报告

---

## 1. 数据架构设计

### 1.1 数据库选型
**推荐：SQLite (MVP) → PostgreSQL (生产)**

- **MVP阶段**：SQLite 单文件，零配置，适合快速验证
- **生产阶段**：PostgreSQL + TimescaleDB 扩展，支持时序数据高效查询

### 1.2 数据库 Schema 设计

```sql
-- ============================================
-- 1. 事件日历表 (event_calendar)
-- ============================================
CREATE TABLE event_calendar (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      VARCHAR(50) NOT NULL,        -- 事件类型: holiday/policy/earnings/others
    event_name      VARCHAR(200) NOT NULL,       -- 事件名称
    event_date      DATE NOT NULL,               -- 事件日期
    event_end_date  DATE,                        -- 事件结束日期（可选）
    impact_sectors  JSON,                        -- 影响板块列表 ["旅游", "酒店"]
    impact_stocks   JSON,                        -- 关联股票代码列表
    intensity       INTEGER CHECK(intensity BETWEEN 1 AND 5),  -- 预期强度 1-5
    sentiment       VARCHAR(20),                 -- 情绪预期: positive/negative/neutral
    lead_days       INTEGER DEFAULT 5,           -- 提前布局天数
    lag_days        INTEGER DEFAULT 3,           -- 事件后持仓天数
    data_source     VARCHAR(50),                 -- 数据来源
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_type, event_name, event_date)
);

CREATE INDEX idx_event_date ON event_calendar(event_date);
CREATE INDEX idx_event_type ON event_calendar(event_type);

-- ============================================
-- 2. 股票基础信息表 (stock_info)
-- ============================================
CREATE TABLE stock_info (
    ts_code         VARCHAR(20) PRIMARY KEY,     -- 股票代码 000001.SZ
    symbol          VARCHAR(10) NOT NULL,        -- 股票代码 000001
    name            VARCHAR(100) NOT NULL,       -- 股票名称
    industry        VARCHAR(50),                 -- 所属行业
    sector          VARCHAR(50),                 -- 所属板块
    market          VARCHAR(10),                 -- 市场 SH/SZ/BJ
    list_date       DATE,                        -- 上市日期
    total_mv        DECIMAL(20,4),               -- 总市值（万元）
    circ_mv         DECIMAL(20,4),               -- 流通市值（万元）
    avg_volume_20d  BIGINT,                      -- 20日平均成交量
    avg_amount_20d  DECIMAL(20,4),               -- 20日平均成交额
    liquidity_score DECIMAL(5,2),                -- 流动性评分 0-100
    is_active       BOOLEAN DEFAULT 1,           -- 是否活跃交易
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_industry ON stock_info(industry);
CREATE INDEX idx_stock_sector ON stock_info(sector);
CREATE INDEX idx_stock_mv ON stock_info(circ_mv);

-- ============================================
-- 3. 日线价格数据表 (stock_daily)
-- ============================================
CREATE TABLE stock_daily (
    ts_code         VARCHAR(20) NOT NULL,
    trade_date      DATE NOT NULL,
    open            DECIMAL(10,4) NOT NULL,
    high            DECIMAL(10,4) NOT NULL,
    low             DECIMAL(10,4) NOT NULL,
    close           DECIMAL(10,4) NOT NULL,
    vol             BIGINT,                      -- 成交量（手）
    amount          DECIMAL(20,4),               -- 成交额（千元）
    change_pct      DECIMAL(6,4),                -- 涨跌幅 %
    ma5             DECIMAL(10,4),               -- 5日均线
    ma10            DECIMAL(10,4),               -- 10日均线
    ma20            DECIMAL(10,4),               -- 20日均线
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_code, trade_date)
);

CREATE INDEX idx_daily_date ON stock_daily(trade_date);
CREATE INDEX idx_daily_change ON stock_daily(change_pct);

-- ============================================
-- 4. 分钟线价格数据表 (stock_minute) - 可选，用于精准入场
-- ============================================
CREATE TABLE stock_minute (
    ts_code         VARCHAR(20) NOT NULL,
    trade_time      TIMESTAMP NOT NULL,
    open            DECIMAL(10,4),
    high            DECIMAL(10,4),
    low             DECIMAL(10,4),
    close           DECIMAL(10,4),
    vol             BIGINT,
    amount          DECIMAL(20,4),
    PRIMARY KEY (ts_code, trade_time)
);

CREATE INDEX idx_minute_time ON stock_minute(trade_time);

-- ============================================
-- 5. 投资组合表 (portfolio)
-- ============================================
CREATE TABLE portfolio (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_name  VARCHAR(100) NOT NULL,       -- 组合名称
    event_id        INTEGER,                     -- 关联事件ID
    event_name      VARCHAR(200),                -- 事件名称（冗余）
    create_date     DATE NOT NULL,               -- 创建日期
    target_sectors  JSON,                        -- 目标板块
    stock_list      JSON NOT NULL,               -- 股票列表 [{"ts_code": "600258.SH", "name": "首旅酒店", "weight": 0.25}]
    status          VARCHAR(20) DEFAULT 'active', -- 状态: active/closed/holding
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. 持仓记录表 (position)
-- ============================================
CREATE TABLE position (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER NOT NULL,
    ts_code         VARCHAR(20) NOT NULL,
    trade_date      DATE NOT NULL,               -- 交易日期
    action          VARCHAR(10) NOT NULL,        -- BUY/SELL
    price           DECIMAL(10,4) NOT NULL,      -- 成交价格
    volume          INTEGER NOT NULL,            -- 成交数量
    amount          DECIMAL(20,4) NOT NULL,      -- 成交金额
    signal_type     VARCHAR(20),                 -- 信号类型: entry/exit/stop_loss
    pnl             DECIMAL(20,4),               -- 盈亏（平仓时计算）
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_position_portfolio ON position(portfolio_id);
CREATE INDEX idx_position_date ON position(trade_date);

-- ============================================
-- 7. 交易信号表 (trading_signal)
-- ============================================
CREATE TABLE trading_signal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER NOT NULL,
    signal_date     DATE NOT NULL,
    signal_type     VARCHAR(10) NOT NULL,        -- BUY/SELL/HOLD
    trigger_reason  VARCHAR(200),                -- 触发原因
    up_count        INTEGER,                     -- 上涨股票数
    down_count      INTEGER,                     -- 下跌股票数
    up_threshold    DECIMAL(5,4),                -- 上涨阈值
    down_threshold  DECIMAL(5,4),                -- 下跌阈值
    confidence      DECIMAL(5,4),                -- 置信度
    executed        BOOLEAN DEFAULT 0,           -- 是否已执行
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signal_date ON trading_signal(signal_date);

-- ============================================
-- 8. 回测结果表 (backtest_result)
-- ============================================
CREATE TABLE backtest_result (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER,
    event_name      VARCHAR(200),
    start_date      DATE,
    end_date        DATE,
    initial_capital DECIMAL(20,4),
    final_capital   DECIMAL(20,4),
    total_return    DECIMAL(10,4),               -- 总收益率
    max_drawdown    DECIMAL(10,4),               -- 最大回撤
    sharpe_ratio    DECIMAL(10,4),               -- 夏普比率
    win_rate        DECIMAL(5,4),                -- 胜率
    trade_count     INTEGER,                     -- 交易次数
    params          JSON,                        -- 回测参数
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. 系统架构设计

### 2.1 四层架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        执行层 (Execution)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  回测引擎   │  │  模拟交易   │  │  实盘接口   │             │
│  │ Backtest    │  │  Paper      │  │  Live       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ 信号
┌─────────────────────────────────────────────────────────────────┐
│                      信号生成层 (Signal)                         │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │  组合监控器     │  │  信号生成器     │                      │
│  │  Portfolio      │  │  Signal         │                      │
│  │  Monitor        │  │  Generator      │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ 事件+数据
┌─────────────────────────────────────────────────────────────────┐
│                     数据处理层 (Processing)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  事件检测   │  │  组合构建   │  │  指标计算   │             │
│  │  Event      │  │  Portfolio  │  │  Indicator  │             │
│  │  Detector   │  │  Builder    │  │  Calculator │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ 原始数据
┌─────────────────────────────────────────────────────────────────┐
│                     数据采集层 (Collection)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  股票数据   │  │  事件数据   │  │  日历数据   │             │
│  │  Tushare/   │  │  爬虫/API   │  │  交易所/    │             │
│  │  AkShare    │  │             │  │  手动录入   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 各层组件详解

#### 数据采集层 (Data Collection Layer)
| 组件 | 功能 | 数据源 | 频率 |
|------|------|--------|------|
| StockDataFetcher | 股票日线/分钟线数据 | Tushare/AkShare | 每日收盘后 |
| EventDataFetcher | 事件日历数据 | 爬虫/手动/API | 按需/每日 |
| CalendarFetcher | 交易日历 | 交易所API | 每年更新 |

#### 数据处理层 (Data Processing Layer)
| 组件 | 功能 | 输出 |
|------|------|------|
| EventDetector | 检测即将到来的事件，触发组合构建 | 事件对象列表 |
| PortfolioBuilder | 根据事件和板块构建股票组合 | 组合配置 |
| IndicatorCalculator | 计算技术指标(均线、涨跌幅等) | 指标数据 |

#### 信号生成层 (Signal Generation Layer)
| 组件 | 功能 | 输出 |
|------|------|------|
| PortfolioMonitor | 实时监控组合内股票价格变动 | 价格快照 |
| SignalGenerator | 根据策略规则生成买卖信号 | 交易信号 |

#### 执行层 (Execution Layer)
| 组件 | 功能 | 输出 |
|------|------|------|
| BacktestEngine | 历史数据回测 | 回测报告 |
| PaperTrader | 模拟交易（无真实资金） | 交易记录 |
| LiveTrader | 实盘交易接口 | 成交回报 |

### 2.3 模块交互流程

```
1. 每日收盘后触发
   ↓
2. EventDetector 检查未来N天的事件
   ↓
3. 如有事件 → PortfolioBuilder 构建组合
   ↓
4. 组合保存到 portfolio 表
   ↓
5. 定时任务监控组合内股票价格
   ↓
6. SignalGenerator 判断买卖信号
   ↓
7. 生成信号 → trading_signal 表
   ↓
8. 执行层读取信号执行交易
```

---

## 3. 核心模块设计

### 3.1 事件检测模块 (EventDetector)

```python
class EventDetector:
    """事件检测模块 - 负责检测即将到来的事件，计算布局时机"""
    
    def __init__(self, db_connection, lead_days_default=5):
        self.db = db_connection
        self.lead_days_default = lead_days_default
        
    def scan_upcoming_events(self, days_ahead=7):
        """扫描未来N天的事件"""
        pass
        
    def check_entry_timing(self, event):
        """检查是否到达入场时机"""
        pass
        
    def check_exit_timing(self, portfolio, event):
        """检查是否到达离场时机"""
        pass
```

### 3.2 组合构建模块 (PortfolioBuilder)

```python
class PortfolioBuilder:
    """组合构建模块 - 根据事件和板块筛选股票，构建投资组合"""
    
    def __init__(self, db_connection, max_stocks=5, min_stocks=3):
        self.db = db_connection
        self.max_stocks = max_stocks
        self.min_stocks = min_stocks
        
    def build_portfolio(self, event, strategy='default'):
        """构建投资组合"""
        pass
        
    def _filter_by_sectors(self, sectors, min_mv=100000, min_volume=1000):
        """根据板块筛选股票"""
        pass
        
    def _apply_strategy(self, stocks, strategy_name):
        """应用选股策略"""
        pass
```

### 3.3 信号生成模块 (SignalGenerator)

```python
class SignalGenerator:
    """信号生成模块 - 根据组合股票价格变动生成买卖信号"""
    
    def __init__(self, db_connection, 
                 buy_threshold=0.02,    # 买入阈值 2%
                 sell_threshold=-0.02,  # 卖出阈值 -2%
                 min_ratio=0.5):        # 最小触发比例 50%
        self.db = db_connection
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.min_ratio = min_ratio
        
    def generate_signal(self, portfolio, date=None):
        """为组合生成交易信号"""
        pass
        
    def check_stop_loss(self, portfolio, stop_loss_pct=-0.05):
        """检查止损条件"""
        pass
```

### 3.4 回测引擎 (BacktestEngine)

```python
class BacktestEngine:
    """回测引擎 - 基于历史数据回测策略表现"""
    
    def __init__(self, db_connection, initial_capital=100000):
        self.db = db_connection
        self.initial_capital = initial_capital
        
    def run_backtest(self, event_filter=None, date_range=None, strategy_params=None):
        """运行回测"""
        pass
        
    def _backtest_single_event(self, event, params):
        """回测单个事件"""
        pass
        
    def _calculate_summary(self, results):
        """计算回测汇总指标"""
        pass
```

---

## 4. 数据源评估

### 4.1 事件日历数据源

| 数据源 | 类型 | 获取方式 | 优点 | 缺点 | 推荐度 |
|--------|------|----------|------|------|--------|
| **手动录入** | 节假日/重大事件 | 直接数据库插入 | 准确可靠 | 工作量大 | ★★★★☆ MVP首选 |
| **交易所公告** | 休市安排 | 爬虫/API | 官方权威 | 需要解析 | ★★★☆☆ |
| **东方财富/同花顺** | 财经日历 | 爬虫 | 数据全面 | 反爬限制 | ★★★☆☆ |
| **政策法规** | 政策发布时间 | 政府网站爬虫 | 一手信息 | 分散难爬 | ★★☆☆☆ |

**MVP建议**：手动录入固定节假日（国庆、春节等），每年更新一次即可。电影档期可通过猫眼/豆瓣API获取。

### 4.2 股票价格数据源对比

| 特性 | Tushare | AkShare | Baostock | 推荐 |
|------|---------|---------|----------|------|
| **费用** | 积分制/部分付费 | 免费 | 免费 | AkShare |
| **A股日线** | ✅ 完整 | ✅ 完整 | ✅ 完整 | 均可 |
| **分钟线** | ✅ 付费 | ✅ 免费 | ❌ 无 | AkShare |
| **实时行情** | ✅ 付费 | ✅ 免费 | ❌ 无 | AkShare |
| **财务数据** | ✅ 完整 | ✅ 完整 | ✅ 基础 | Tushare/AkShare |
| **更新频率** | 每日盘后 | 每日盘后 | 每日盘后 | 均可 |
| **稳定性** | 高 | 中高 | 中 | Tushare |
| **文档质量** | 优秀 | 良好 | 一般 | Tushare |
| **社区活跃度** | 高 | 高 | 低 | Tushare/AkShare |

### 4.3 推荐方案

**MVP阶段（1-2个月）**：
- 事件数据：手动录入年度节假日 + 爬虫获取电影档期
- 股票数据：AkShare（免费、分钟线、Python友好）
- 存储：SQLite 单文件

**生产阶段（3-6个月）**：
- 事件数据：自建爬虫+人工审核
- 股票数据：Tushare Pro（稳定性优先）
- 存储：PostgreSQL + TimescaleDB

---

## 5. 技术可行性评估

### 5.1 开发难度评估

| 模块 | 难度 | 工作量 | 依赖风险 |
|------|------|--------|----------|
| 数据架构设计 | 低 | 3天 | 低 |
| 数据采集层 | 中 | 1周 | 中（数据源变更） |
| 事件检测模块 | 低 | 3天 | 低 |
| 组合构建模块 | 中 | 1周 | 低 |
| 信号生成模块 | 低 | 3天 | 低 |
| 回测引擎 | 中 | 1.5周 | 低 |
| 实盘接口 | 高 | 2-3周 | 高（券商API） |

**总体难度**：⭐⭐ 中等偏低（不含实盘交易）

### 5.2 开发时间估算

| 阶段 | 功能范围 | 时间 | 里程碑 |
|------|----------|------|--------|
| **Phase 1** | 数据层 + 基础模型 | 2周 | 能跑通数据流 |
| **Phase 2** | 回测引擎 + 策略实现 | 2周 | 能跑历史回测 |
| **Phase 3** | 信号监控 + 模拟交易 | 1周 | 能模拟跟踪 |
| **Phase 4** | 实盘接口 + 风控 | 2-3周 | 能实盘运行 |
| **总计** | MVP（不含实盘） | **5周** | 可验证策略有效性 |

### 5.3 关键依赖和风险点

| 风险项 | 风险等级 | 影响 | 缓解措施 |
|--------|----------|------|----------|
| AkShare API变更/失效 | 中 | 数据采集中断 | 封装数据层，预留Tushare切换接口 |
| 事件日历不完整 | 中 | 错过交易机会 | MVP阶段人工审核补充 |
| 策略有效性不及预期 | 高 | 项目失败 | 先做回测验证，再投入实盘 |
| 券商API接入困难 | 高 | 无法实盘 | 先使用模拟交易，积累业绩 |
| 数据存储性能瓶颈 | 低 | 查询变慢 | MVP用SQLite，后期迁移PostgreSQL |

### 5.4 渐进开发路线图

```
Phase 1: MVP核心 (Week 1-2)
├── 数据库Schema实现
├── AkShare数据接入
├── 事件检测模块
└── 组合构建模块（市值策略）

Phase 2: 回测验证 (Week 3-4)
├── 回测引擎开发
├── 历史数据填充（至少2年）
├── 策略回测验证
└── 收益归因分析

Phase 3: 信号监控 (Week 5)
├── 每日定时任务
├── 信号生成与通知
├── 模拟交易跟踪
└── 回测 vs 模拟对比

Phase 4: 生产优化 (Week 6-8)
├── 数据源迁移Tushare Pro
├── 数据库存储优化
├── 风控模块
└── 实盘接口（可选）

Phase 5: 持续迭代 (长期)
├── 更多事件类型
├── 更多选股策略
├── 策略组合优化
└── 机器学习增强
```

---

## 6. 关键技术风险

### 6.1 高风险项

1. **策略有效性风险**（最高）
   - 事件驱动策略可能在回测中表现好，但实盘效果差
   - 市场结构变化可能导致策略失效
   - **缓解**：至少回测3年历史数据，模拟交易6个月后再考虑实盘

2. **数据源依赖风险**
   - AkShare/Tushare API可能变更或停止服务
   - 免费数据源可能有频率限制
   - **缓解**：封装数据层，支持多数据源切换；本地缓存历史数据

### 6.2 中风险项

3. **事件日历完整性**
   - 可预见事件（节假日、电影档期）容易获取
   - 突发政策事件难以预测
   - **缓解**：MVP聚焦可预见事件，后续逐步扩展

4. **系统稳定性**
   - 定时任务可能因服务器重启而中断
   - 数据库连接可能出现异常
   - **缓解**：添加监控告警，使用守护进程，数据库连接池

### 6.3 低风险项

5. **性能瓶颈**
   - SQLite在数据量不大时性能足够
   - 百万级日线数据查询无压力
   - **缓解**：后期可无缝迁移至PostgreSQL

---

## 7. 总结与建议

### 7.1 核心结论

1. **技术可行**：整体开发难度中等偏低，5周可完成MVP
2. **数据源可行**：AkShare免费版可满足MVP需求
3. **架构清晰**：四层架构（采集→处理→信号→执行）职责分明
4. **风险可控**：主要风险在于策略有效性，而非技术实现

### 7.2 行动建议

| 优先级 | 行动项 | 建议 |
|--------|--------|------|
| P0 | 先验证策略有效性 | 用Excel/Python快速回测2-3个历史事件，确认策略有效后再投入开发 |
| P1 | 开发MVP | 按Phase 1-3路线图，优先完成回测功能 |
| P2 | 模拟跟踪 | 对2026年事件进行模拟交易跟踪，积累业绩 |
| P3 | 实盘接入 | 确认策略有效后再接入实盘接口 |

### 7.3 最小可行方案

如果资源有限，最小可行方案仅需：
1. **SQLite数据库** - 单文件存储
2. **AkShare数据源** - 免费获取股票数据
3. **手动事件录入** - 每年录入节假日即可
4. **回测功能** - 验证策略有效性是首要目标
5. **模拟跟踪** - 每日收盘后检查信号，人工执行

**无需实盘接口，也能验证策略价值。**
