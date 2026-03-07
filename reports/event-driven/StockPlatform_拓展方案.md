# Stock Platform 事件驱动选股体系拓展方案

**版本**: v1.0  
**日期**: 2026-03-06  
**状态**: 设计完成，待实施

---

## 1. 概述

### 1.1 背景
事件驱动选股体系通过捕捉固定事件（节日、政策、季节）产生的市场情绪波动，提前布局相关板块获取超额收益。经过股票团队5位分析师的深度评估，该策略量化可行（回测年化21.3%，Sharpe 1.32），但需严格执行筛选标准和风控纪律。

### 1.2 目标
将事件驱动选股体系集成到现有Stock Platform，实现：
- 事件日历管理（自动+手动）
- 智能组合构建（相关性筛选ρ>0.6）
- 买卖信号生成（情绪+量化双因子）
- 回测与实盘跟踪
- 风险监控与预警

### 1.3 集成原则
- **渐进式**：不影响现有策略，作为独立模块添加
- **可配置**：用户可选择启用/禁用
- **数据复用**：复用现有股票数据、行情数据
- **风控优先**：严格仓位管理和止损机制

---

## 2. 系统架构设计

### 2.1 新增模块一览

```
StockPlatform/
├── event_driven/                    # 新增：事件驱动模块
│   ├── __init__.py
│   ├── models/                      # 数据模型
│   │   ├── event.py                 # 事件定义
│   │   ├── portfolio.py             # 组合管理
│   │   └── signal.py                # 信号记录
│   ├── core/                        # 核心逻辑
│   │   ├── event_detector.py        # 事件检测
│   │   ├── correlation_analyzer.py  # 相关性分析
│   │   ├── portfolio_builder.py     # 组合构建
│   │   └── signal_generator.py      # 信号生成
│   ├── data/                        # 数据源
│   │   ├── event_calendar.py        # 事件日历
│   │   └── sentiment_fetcher.py     # 情绪数据获取
│   ├── backtest/                    # 回测引擎
│   │   └── event_backtester.py      # 事件驱动回测
│   └── web/                         # Web界面
│       ├── event_list.py            # 事件列表页
│       ├── portfolio_builder.py     # 组合构建页
│       └── signal_monitor.py        # 信号监控页
├── database/                        # 现有数据库扩展
│   └── migrations/                  # 数据库迁移脚本
├── tests/                           # 测试
│   └── test_event_driven/
└── docs/                            # 文档
    └── event_driven_strategy.md     # 策略说明
```

### 2.2 与现有系统集成

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock Platform 架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐      ┌──────────────────────────────┐  │
│  │  现有模块       │      │  新增：事件驱动模块           │  │
│  │                 │      │                              │  │
│  │ • 数据采集      │◄────►│ • 事件日历管理               │  │
│  │ • 因子计算      │◄────►│ • 相关性分析                 │  │
│  │ • 选股引擎      │◄────►│ • 组合构建                   │  │
│  │ • 回测系统      │◄────►│ • 信号生成                   │  │
│  │ • 风险监控      │◄────►│ • 情绪跟踪                   │  │
│  │                 │      │                              │  │
│  └─────────────────┘      └──────────────────────────────┘  │
│           ▲                          ▲                      │
│           │                          │                      │
│           └──────────┬───────────────┘                      │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │    统一数据库        │                          │
│           │  • stock_daily      │                          │
│           │  • event_calendar   │  (新增)                  │
│           │  • portfolio        │  (新增)                  │
│           │  • trading_signal   │  (新增)                  │
│           └─────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据库扩展设计

### 3.1 新增数据表

```sql
-- ============================================
-- 1. 事件日历表 (event_calendar)
-- ============================================
CREATE TABLE event_calendar (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      VARCHAR(50) NOT NULL,        -- 事件类型
    event_name      VARCHAR(200) NOT NULL,       -- 事件名称
    event_date      DATE NOT NULL,               -- 事件日期
    event_end_date  DATE,                        -- 事件结束日期
    impact_sectors  JSON,                        -- 影响板块
    impact_stocks   JSON,                        -- 关联股票
    intensity       INTEGER CHECK(intensity BETWEEN 1 AND 5),
    sentiment       VARCHAR(20),                 -- 情绪预期
    lead_days       INTEGER DEFAULT 10,          -- 提前布局天数
    lag_days        INTEGER DEFAULT 3,           -- 事件后持仓天数
    status          VARCHAR(20) DEFAULT 'active',-- 状态
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. 事件驱动组合表 (event_portfolio)
-- ============================================
CREATE TABLE event_portfolio (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_name      VARCHAR(100) NOT NULL,
    event_id            INTEGER NOT NULL,
    event_name          VARCHAR(200),
    create_date         DATE NOT NULL,
    target_sectors      JSON,                    -- 目标板块
    stock_list          JSON NOT NULL,           -- 股票列表及权重
    correlation_matrix  JSON,                    -- 相关性矩阵
    avg_correlation     DECIMAL(5,4),            -- 平均相关性
    status              VARCHAR(20) DEFAULT 'active',
    score               DECIMAL(5,2),            -- 质量评分
    FOREIGN KEY (event_id) REFERENCES event_calendar(id)
);

-- ============================================
-- 3. 事件驱动信号表 (event_signal)
-- ============================================
CREATE TABLE event_signal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER NOT NULL,
    signal_date     DATE NOT NULL,
    signal_type     VARCHAR(10) NOT NULL,        -- BUY/SELL/HOLD
    trigger_reason  VARCHAR(200),
    up_count        INTEGER,                     -- 上涨股票数
    down_count      INTEGER,                     -- 下跌股票数
    up_ratio        DECIMAL(5,4),                -- 上涨比例
    avg_change_pct  DECIMAL(6,4),                -- 平均涨跌幅
    entry_threshold DECIMAL(5,4),                -- 入场阈值
    exit_threshold  DECIMAL(5,4),                -- 出场阈值
    sentiment_score DECIMAL(5,2),                -- 情绪得分
    executed        BOOLEAN DEFAULT 0,
    FOREIGN KEY (portfolio_id) REFERENCES event_portfolio(id)
);
```

---

## 4. 核心模块设计

### 4.1 关键类设计

```python
class EventDetector:
    """事件检测器 - 自动识别即将到来的事件"""
    def detect_upcoming_events(self, days_ahead=30): pass
    def calculate_event_impact_score(self, event_id): pass

class CorrelationAnalyzer:
    """相关性分析器 - 计算股票间相关性"""
    def calculate_stock_correlations(self, stocks, lookback=120): pass
    def filter_by_correlation(self, stocks, sector_index, threshold=0.5): pass

class PortfolioBuilder:
    """组合构建器 - 构建最优股票组合"""
    def build_portfolio(self, event_id, max_stocks=5, 
                       correlation_threshold=0.5): pass
    def calculate_optimal_weights(self, stocks, correlation_matrix): pass
    def score_portfolio(self, portfolio): pass

class SignalGenerator:
    """信号生成器 - 生成买卖信号"""
    def generate_entry_signal(self, portfolio_id, date): pass
    def generate_exit_signal(self, portfolio_id, date): pass
    def check_stop_loss(self, position, current_price): pass
```

---

## 5. 使用流程

### 5.1 完整流程

```
1. 事件发现（T-30天）
   └─> 系统自动推送即将发生的事件

2. 事件评估
   └─> 查看历史同类事件表现
   └─> 评分>7分才参与

3. 组合构建（T-20天）
   └─> 选择影响板块
   └─> 系统筛选股票（ρ>0.5，流动性>5000万）
   └─> 确认平均相关性>0.6

4. 买入执行（信号触发）
   └─> 组合>60%股票上涨且涨幅>2%
   └─> 执行买入

5. 持有监控
   └─> 监控止损/止盈
   └─> 事件后3天减仓

6. 卖出执行
   └─> 信号触发或时间退出

7. 复盘归因
   └─> 分析绩效
   └─> 更新策略
```

---

## 6. 实施路线图

| Phase | 时长 | 任务 | 产出 |
|-------|------|------|------|
| P1 | 2周 | 数据库+基础类 | 数据表+模型类 |
| P2 | 2周 | 核心模块 | 相关性分析+组合构建 |
| P3 | 2周 | Web界面 | 事件列表+组合构建页 |
| P4 | 2周 | 回测引擎 | 回测系统+验证 |
| P5 | 2周 | 集成上线 | 生产环境部署 |
| **总计** | **10周** | - | **完整系统** |

---

## 7. 核心结论

### 7.1 关键参数（来自分析报告）

| 参数 | 建议值 | 来源 |
|------|-------|------|
| 相关性阈值 | ρ > 0.6 | Quant Munger |
| 买入条件 | >60%股票涨且>2% | Quant Munger |
| 仓位上限 | 30%（单事件） | Kelly公式 |
| 止损线 | -8% | Risk Assessment |
| 时间窗口 | T-10买入，T+3卖出 | News Analyst |

### 7.2 关键成功因素

1. **ρ>0.6是生死线** - 国庆组合失败（ρ=0.49），春节电影成功（ρ=0.72）
2. **事件质量评分>7分** - 低质量事件不参与
3. **严格风控纪律** - 硬性止损+时间止损
4. **情绪时机精准** - 提前3-4周布局，T-7减仓

### 7.3 芒格警告

> "这不是投资策略，而是博弈策略。策略越成功，失效越快。"

**建议**：降级为辅助策略（仓位≤20%），主策略仍应是价值投资。

---

**相关文档**：
- 完整分析报告：`/Users/linweihao/.openclaw/workspace/reports/event-driven/`
- 01_策略反思报告.md
- 02_量化分析报告.md
- 03_情绪分析报告.md
- 04_技术实现报告.md
- 05_风险评估报告.md

**方案制定**：Stock Platform Team  
**日期**：2026-03-06
