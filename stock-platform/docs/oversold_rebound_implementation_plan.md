# 超跌反弹策略 - 结构化实施计划

> **策略定位**: 基于均值回归的中短期量化交易策略  
> **核心逻辑**: 捕捉超跌后的反弹机会，结合分层仓位管理与严格风控

---

## 一、MVP版本（最小可行产品）

### 1.1 MVP目标
在 **2-3周** 内实现可跑通的策略原型，验证核心逻辑有效性

### 1.2 MVP功能范围

#### 阶段1: 核心引擎（Week 1）
```
✓ 跌幅扫描器（Oversold Scanner）
  - 计算N日跌幅（默认90日/126日）
  - 区分大盘股/小盘股阈值
  
✓ 反弹确认器（Rebound Confirmer）
  - 检测从低点反弹超过y/8（12.5%）
  - 单日确认信号
  
✓ 基本面过滤器（Fundamental Filter）
  - ROE > 5% 校验
  - ST/退市风险排除
```

#### 阶段2: 交易执行（Week 2）
```
✓ 仓位分配器（Position Sizer）
  - 3档仓位: 重仓(<5%盈利)/中仓(5-10%)/轻仓(>10%)
  - 单票最大仓位10%
  
✓ 止损控制器（Stop Loss Manager）
  - -5% 硬止损（自动触发）
  - 10日时间止损（日历提醒）
  
✓ 模拟交易接口（Paper Trading）
  - 模拟下单与持仓追踪
```

#### 阶段3: 回测框架（Week 3）
```
✓ 历史数据回测（Backtest Engine）
✓ 基础绩效报表（P&L, Sharpe, Max Drawdown）
```

### 1.3 MVP技术栈建议
```
语言: Python 3.10+
数据: AkShare / Tushare (免费) 或 Wind/同花顺iFinD (付费)
存储: SQLite (MVP阶段) / PostgreSQL (生产阶段)
调度: APScheduler / Cron
回测: Backtrader / 自研轻量框架
通知: 企业微信/钉钉Webhook
```

### 1.4 MVP输出交付物
| 交付物 | 说明 |
|--------|------|
| `scanner.py` | 每日扫描超跌股票 |
| `signal_generator.py` | 生成买入信号 |
| `position_manager.py` | 仓位与止损管理 |
| `backtest.py` | 回测验证脚本 |
| `config.yaml` | 策略参数配置 |
| `daily_report.html` | 每日扫描报告 |

---

## 二、开发优先级与时间估算

### 2.1 功能优先级矩阵

```
┌─────────────────────────────────────────────────────────┐
│  高价值/高紧急        │  高价值/低紧急                  │
│  1. 跌幅扫描器        │  5. 绩效归因分析                │
│  2. 反弹确认器        │  6. 多因子增强                  │
│  3. 止损控制器        │  7. 智能择时                    │
├─────────────────────────────────────────────────────────┤
│  低价值/高紧急        │  低价值/低紧急                  │
│  4. 数据清洗模块      │  8. 可视化Dashboard             │
│                      │  9. 移动端APP                   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 开发路线图

```
Phase 1: 核心验证期 (Week 1-3)      [MVP]
├─ Day 1-3:   数据接入 + 跌幅计算
├─ Day 4-7:   反弹确认 + 信号生成
├─ Day 8-14:  仓位管理 + 止损逻辑
└─ Day 15-21: 回测框架 + 初步验证

Phase 2: 优化迭代期 (Week 4-6)      [增强]
├─ Week 4: 参数敏感性分析
├─ Week 5: 多周期回测 (2018-2024)
└─ Week 6: 模拟盘验证

Phase 3: 生产准备期 (Week 7-8)      [上线]
├─ Week 7: 实盘接口对接
└─ Week 8: 监控告警 + 部署上线
```

### 2.3 人力估算

| 角色 | 人力投入 | 周期 |
|------|----------|------|
| 量化策略师 | 0.5 FTE | 全程 |
| Python开发 | 1.0 FTE | 全程 |
| 数据工程师 | 0.3 FTE | Week 1-2 |
| 风控专员 | 0.2 FTE | Week 3-8 |

**总人天估算**: 约 35-40 人天

---

## 三、数据需求清单

### 3.1 核心数据表

#### 表1: 行情数据（日级）
```sql
CREATE TABLE daily_price (
    trade_date DATE,
    stock_code VARCHAR(10),
    open DECIMAL(10,4),
    high DECIMAL(10,4),
    low DECIMAL(10,4),
    close DECIMAL(10,4),
    volume BIGINT,
    amount DECIMAL(20,4),
    PRIMARY KEY (trade_date, stock_code)
);
-- 更新频率: 每日收盘后
-- 来源: 交易所 / 数据供应商
```

#### 表2: 股票基本信息
```sql
CREATE TABLE stock_info (
    stock_code VARCHAR(10) PRIMARY KEY,
    stock_name VARCHAR(50),
    market VARCHAR(10),           -- 主板/创业板/科创板
    industry VARCHAR(50),         -- 行业分类
    total_cap DECIMAL(20,4),      -- 总市值（区分大盘/小盘）
    list_date DATE,
    is_st BOOLEAN,                -- ST标记
    is_delisting BOOLEAN          -- 退市风险
);
-- 更新频率: 每日
-- 来源: 交易所公告
```

#### 表3: 财务指标（季度）
```sql
CREATE TABLE financial_ratio (
    report_date DATE,
    stock_code VARCHAR(10),
    roe DECIMAL(8,4),             -- 净资产收益率
    roa DECIMAL(8,4),             -- 总资产收益率
    pe_ratio DECIMAL(10,4),       -- 市盈率（辅助）
    pb_ratio DECIMAL(10,4),       -- 市净率（辅助）
    PRIMARY KEY (report_date, stock_code)
);
-- 更新频率: 季度
-- 来源: 财报数据
```

#### 表4: 交易信号记录
```sql
CREATE TABLE trade_signals (
    signal_id SERIAL PRIMARY KEY,
    trade_date DATE,
    stock_code VARCHAR(10),
    signal_type VARCHAR(10),      -- BUY / SELL
    trigger_price DECIMAL(10,4),
    drop_pct DECIMAL(8,4),        -- 跌幅百分比
    rebound_pct DECIMAL(8,4),     -- 反弹百分比
    position_size VARCHAR(10),    -- heavy/medium/light
    reason TEXT
);
-- 更新频率: 实时生成
```

#### 表5: 持仓与交易记录
```sql
CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10),
    entry_date DATE,
    entry_price DECIMAL(10,4),
    shares INTEGER,
    position_type VARCHAR(10),    -- heavy/medium/light
    stop_loss_price DECIMAL(10,4),
    time_stop_date DATE,          -- 10日时间止损日
    exit_date DATE,
    exit_price DECIMAL(10,4),
    exit_reason VARCHAR(50),      -- target/stop_loss/time_stop
    pnl DECIMAL(20,4),
    pnl_pct DECIMAL(8,4)
);
-- 更新频率: 交易触发时
```

### 3.2 数据接入方案

| 数据类型 | 推荐源 | 成本 | 接入难度 |
|----------|--------|------|----------|
| 日K线数据 | AkShare (免费) | ¥0 | 低 |
| 财务数据 | Tushare Pro | ¥500-2000/年 | 中 |
| 实时行情 | 同花顺iFinD | ¥8000+/年 | 低 |
| 分钟级数据 | Wind/Choice | ¥20000+/年 | 中 |

**MVP推荐**: AkShare + Tushare Pro（免费额度足够MVP验证）

### 3.3 数据质量检查点
```python
data_quality_checks = {
    "完整性": "检查是否有缺失交易日",
    "一致性": "价格逻辑检查 (high >= low, close在范围内)",
    "时效性": "T+1数据获取延迟监控",
    "异常值": "涨跌停标记、停牌识别",
    "复权处理": "前复权/后复权统一"
}
```

---

## 四、回测验证方案

### 4.1 回测框架设计

```python
class OversoldReboundBacktest:
    """
    回测参数配置
    """
    params = {
        # 时间范围
        'start_date': '2018-01-01',
        'end_date': '2024-12-31',
        
        # 股票池
        'universe': '沪深A股（排除ST、北交所、上市<1年）',
        
        # 策略参数
        'lookback_days': 90,           # 跌幅计算周期
        'large_cap_threshold': 35,      # 大盘跌幅阈值(%)
        'small_cap_threshold': 45,      # 小盘跌幅阈值(%)
        'rebound_trigger': 12.5,        # 反弹触发比例(%)
        'max_position_per_stock': 0.10, # 单票最大仓位
        
        # 仓位分层
        'heavy_weight': 0.08,           # 重仓 (<5%目标)
        'medium_weight': 0.05,          # 中仓 (5-10%目标)
        'light_weight': 0.03,           # 轻仓 (>10%目标)
        
        # 风控参数
        'hard_stop_loss': -5,           # 硬止损(%)
        'time_stop_days': 10,           # 时间止损(日)
        
        # 交易成本
        'commission': 0.0003,           # 佣金
        'slippage': 0.001,              # 滑点
        'stamp_tax': 0.001              # 印花税(卖出)
    }
```

### 4.2 回测场景矩阵

| 场景 | 目的 | 测试区间 | 关键指标 |
|------|------|----------|----------|
| **基准回测** | 验证核心逻辑 | 2018-2024 | 年化收益、最大回撤 |
| **牛市测试** | 验证上涨市表现 | 2019-2021 | 相对超额收益 |
| **熊市测试** | 验证下跌市风控 | 2018、2022 | 回撤控制、胜率 |
| **震荡市测试** | 验证常态表现 | 2023-2024 | 交易频率、盈亏比 |
| **参数敏感性** | 寻找稳健参数 | 全区间 | 参数稳定性 |
| **蒙特卡洛** | 验证统计显著性 | 随机抽样 | 置信区间 |

### 4.3 关键评估指标

```python
performance_metrics = {
    # 收益指标
    "年化收益率": "CAGR (Compound Annual Growth Rate)",
    "超额收益": "相对于沪深300的超额",
    "盈亏比": "平均盈利/平均亏损",
    
    # 风险指标
    "最大回撤": "Max Drawdown",
    "夏普比率": "Sharpe Ratio (无风险利率2%)",
    "卡玛比率": "Calmar Ratio (收益/最大回撤)",
    
    # 交易指标
    "胜率": "盈利交易次数/总交易次数",
    "交易频率": "年均交易次数",
    "持仓周期": "平均持仓天数",
    "资金利用率": "平均仓位比例",
    
    # 策略特异性指标
    "超跌命中率": "触发买入后成功反弹比例",
    "止损触发率": "各类型止损触发占比",
    "分层收益差异": "重/中/轻仓收益对比"
}
```

### 4.4 回测报告模板

```markdown
## 回测报告: 超跌反弹策略 v1.0

### 1. 测试概要
- 时间区间: 2018-01-01 至 2024-12-31
- 股票池: 沪深A股 (排除ST, 北交所)
- 初始资金: ¥1,000,000

### 2. 核心绩效
| 指标 | 策略 | 沪深300 | 超额 |
|------|------|---------|------|
| 年化收益 | XX% | XX% | XX% |
| 最大回撤 | XX% | XX% | - |
| 夏普比率 | X.XX | X.XX | - |

### 3. 交易统计
- 总交易次数: XXX
- 胜率: XX%
- 盈亏比: X:1
- 平均持仓: X.X 天

### 4. 风险分析
- 硬止损触发率: XX%
- 时间止损触发率: XX%
- 目标止盈占比: XX%

### 5. 参数敏感性
- 最佳跌幅阈值: XX%
- 最佳反弹触发: XX%
- 参数稳定性: 高/中/低

### 6. 结论与建议
- 策略有效性: [✓] 通过 / [✗] 未通过
- 建议优化方向: XXX
```

---

## 五、风险控制机制

### 5.1 三层风控体系

```
┌────────────────────────────────────────────────────────────┐
│  L1: 信号层风控 (事前)                                      │
│  ├─ 基本面过滤: ROE>5%, 排除ST, 排除退市风险                │
│  ├─ 流动性过滤: 日均成交额>5000万                           │
│  └─ 异常波动过滤: 排除连续涨停/跌停股票                     │
├────────────────────────────────────────────────────────────┤
│  L2: 交易层风控 (事中)                                      │
│  ├─ 单票最大仓位: 10%                                       │
│  ├─ 行业集中度: 单一行业不超过30%                           │
│  ├─ 总仓位控制: 根据市场状态动态调整 (60%-100%)             │
│  └─ 买入冷却期: 同一股票卖出后N日不得买入                   │
├────────────────────────────────────────────────────────────┤
│  L3: 账户层风控 (事后)                                      │
│  ├─ 单日最大亏损: 账户净值回撤不超过3%                      │
│  ├─ 月度止损线: 月度亏损超过10%暂停交易                     │
│  ├─ 最大回撤控制: 净值从高点回撤15%减仓50%                  │
│  └─ 熔断机制: 净值回撤20%停止策略，人工复核                 │
└────────────────────────────────────────────────────────────┘
```

### 5.2 止损执行规则

#### 硬止损 (-5%)
```python
def check_hard_stop(position, current_price):
    """
    硬止损检查
    触发条件: 当前价格 <= 买入价 * 0.95
    执行方式: 市价单立即卖出
    """
    stop_price = position.entry_price * 0.95
    if current_price <= stop_price:
        return Signal(action='SELL', reason='HARD_STOP', urgency='HIGH')
```

#### 时间止损 (10日)
```python
def check_time_stop(position, current_date):
    """
    时间止损检查
    触发条件: 持仓天数 >= 10日
    执行方式: 第10日收盘前市价卖出
    """
    holding_days = (current_date - position.entry_date).days
    if holding_days >= 10:
        return Signal(action='SELL', reason='TIME_STOP', urgency='MEDIUM')
```

#### 目标止盈 (分层)
```python
def check_profit_target(position, current_price, current_profit_pct):
    """
    目标止盈检查
    """
    if current_profit_pct >= position.target_profit_pct:
        return Signal(action='SELL', reason='TARGET_HIT', urgency='NORMAL')
    
    # 回撤止盈: 浮盈回撤50%时止盈
    if position.max_profit_pct > 0:
        drawdown_from_peak = (position.max_profit_pct - current_profit_pct) / position.max_profit_pct
        if drawdown_from_peak >= 0.5:
            return Signal(action='SELL', reason='PROFIT_PULLBACK', urgency='MEDIUM')
```

### 5.3 风险监控Dashboard

```yaml
实时监控指标:
  - 当前持仓盈亏分布
  - 临近止损股票列表
  - 当日已触发止损次数
  - 账户净值变动
  - 策略运行状态

日报指标:
  - 当日交易明细
  - 持仓过夜风险暴露
  - 行业/市值分布
  - 近期胜率趋势

周报指标:
  - 策略绩效归因
  - 参数有效性评估
  - 风险事件复盘
```

### 5.4 应急预案

| 场景 | 触发条件 | 应对措施 |
|------|----------|----------|
| **连续止损** | 单日触发>5次硬止损 | 暂停新信号，复盘市场状态 |
| **数据异常** | 数据源延迟>30分钟 | 切换备用数据源，手工确认 |
| **系统故障** | 交易接口断开 | 启动人工交易模式，电话下单 |
| **黑天鹅事件** | 大盘跌>5% | 启动熔断，全部平仓观望 |
| **策略失效** | 连续3月跑输基准 | 暂停策略，启动归因分析 |

---

## 六、实施时间线与里程碑

```
Week 1-2:  【✓】MVP开发完成
           里程碑: 能跑通单只股票的历史回测

Week 3:    【✓】回测验证完成
           里程碑: 确定参数有效区间，胜率>55%

Week 4-5:  【✓】模拟盘验证
           里程碑: 模拟盘运行2周，信号与回测一致

Week 6:    【✓】风控系统上线
           里程碑: 所有风控规则代码化并测试通过

Week 7:    【✓】生产环境部署
           里程碑: 系统稳定运行，监控告警正常

Week 8+:   【✓】小资金实盘
           里程碑: 实盘资金10万，验证全流程
```

---

## 七、成功标准与退出条件

### 7.1 策略成功标准
- [ ] 回测年化收益 > 15%
- [ ] 最大回撤 < 20%
- [ ] 夏普比率 > 1.0
- [ ] 胜率 > 55%
- [ ] 盈亏比 > 1.5

### 7.2 策略暂停/退出条件
- 连续3个月跑输沪深300
- 单次最大回撤超过25%
- 策略逻辑被市场结构改变（如注册制全面改革）
- 胜率持续低于50%超过6个月

---

## 附录：Quant-Munger优化建议对照表

| 建议项 | 原策略 | 优化后 | 实施状态 |
|--------|--------|--------|----------|
| 跌幅阈值 | 统一40% | 大盘35%，小盘45-50% | ✅ Phase 1 |
| 买入触发 | 未明确 | 反弹12.5% | ✅ Phase 1 |
| 获利分层 | 未分层 | 3档仓位管理 | ✅ Phase 2 |
| 基本面过滤 | ROE>5% | ROE>5% + 排除ST | ✅ Phase 1 |
| 止损机制 | 未明确 | -5%硬损 + 10日时间损 | ✅ Phase 2 |

---

*文档版本: v1.0*  
*编制日期: 2025年*  
*适用对象: 量化策略开发团队*
