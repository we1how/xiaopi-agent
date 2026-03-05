#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Platform MVP
股票策略回测平台 - Streamlit 主应用
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path
import sys
import importlib.util
import inspect

# 导入本地模块
from data_loader import StockDataLoader
from backtest_engine import BacktestEngine, run_backtest
from strategies import (
    SmaCross, RsiStrategy, MacdStrategy,
    SmaCrossV2, SmaCrossV2Aggressive, SmaCrossV2Conservative,
    OversoldBounceStrategy, OversoldBounceConservative, OversoldBounceAggressive
)
from signals import SignalExtractor, TechnicalSignals
from scanners import OversoldScanner

# 页面配置
st.set_page_config(
    page_title="股票策略回测平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive {
        color: #ff4b4b;
    }
    .negative {
        color: #26a69a;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 session state"""
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = StockDataLoader()
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None
    if 'oversold_scan_results' not in st.session_state:
        st.session_state.oversold_scan_results = None
    if 'oversold_scanner' not in st.session_state:
        st.session_state.oversold_scanner = None


def load_strategy_from_file(file_path: str) -> type:
    """从文件加载策略类"""
    spec = importlib.util.spec_from_file_location("strategy", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 查找策略类（继承自 Strategy 的类）
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__name__ != 'Strategy':
            try:
                from backtesting import Strategy
                if issubclass(obj, Strategy):
                    return obj
            except:
                continue
    
    raise ValueError("未找到有效的策略类")


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("⚙️ 参数设置")
    
    # 数据设置
    st.sidebar.header("📊 数据设置")
    
    # 股票代码输入
    stock_code = st.sidebar.text_input(
        "股票代码",
        value="000001",
        help="输入股票代码，如: 000001(平安银行), 600519(贵州茅台)"
    )
    
    # 日期范围
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # 策略选择
    st.sidebar.header("🤖 策略选择")
    
    strategy_option = st.sidebar.radio(
        "选择策略",
        ["内置策略", "上传策略文件"]
    )
    
    strategy_class = None
    strategy_file = None
    
    if strategy_option == "内置策略":
        # 添加策略版本选择
        strategy_version = st.sidebar.radio(
            "策略版本",
            ["原版 (V1)", "细粒度版 (V2 - 带信号面板)"]
        )

        if strategy_version == "原版 (V1)":
            strategy_name = st.sidebar.selectbox(
                "选择内置策略",
                ["SmaCross (双均线)", "RsiStrategy (RSI)", "MacdStrategy (MACD)"]
            )

            if strategy_name.startswith("SmaCross"):
                strategy_class = SmaCross
                st.sidebar.subheader("策略参数")
                n_short = st.sidebar.slider("短期均线", 5, 50, 10)
                n_long = st.sidebar.slider("长期均线", 10, 100, 20)
                strategy_params = {"n_short": n_short, "n_long": n_long}

            elif strategy_name.startswith("RsiStrategy"):
                strategy_class = RsiStrategy
                st.sidebar.subheader("策略参数")
                period = st.sidebar.slider("RSI周期", 5, 30, 14)
                oversold = st.sidebar.slider("超卖阈值", 10, 40, 30)
                overbought = st.sidebar.slider("超买阈值", 60, 90, 70)
                strategy_params = {"period": period, "oversold": oversold, "overbought": overbought}

            else:  # MACD
                strategy_class = MacdStrategy
                st.sidebar.subheader("策略参数")
                fast = st.sidebar.slider("快线周期", 5, 20, 12)
                slow = st.sidebar.slider("慢线周期", 20, 50, 26)
                signal = st.sidebar.slider("信号线周期", 5, 15, 9)
                strategy_params = {"fast": fast, "slow": slow, "signal": signal}

        else:  # V2 细粒度策略
            strategy_name = st.sidebar.selectbox(
                "选择V2策略",
                ["SmaCrossV2 (标准版)", "SmaCrossV2Aggressive (激进版)", "SmaCrossV2Conservative (保守版)"]
            )

            if strategy_name.startswith("SmaCrossV2 (标准版)"):
                strategy_class = SmaCrossV2
            elif strategy_name.startswith("SmaCrossV2Aggressive"):
                strategy_class = SmaCrossV2Aggressive
            else:
                strategy_class = SmaCrossV2Conservative

            st.sidebar.subheader("策略参数")
            n_short = st.sidebar.slider("短期均线", 5, 50, 10)
            n_long = st.sidebar.slider("长期均线", 10, 100, 20)
            trend_filter = st.sidebar.checkbox("启用趋势过滤", value=True)
            min_trend = st.sidebar.slider("最小趋势强度", 0.0, 1.0, 0.3)

            strategy_params = {
                "n_short": n_short,
                "n_long": n_long,
                "trend_filter": trend_filter,
                "min_trend_strength": min_trend
            }
            
    else:  # 上传策略文件
        strategy_file = st.sidebar.file_uploader(
            "上传策略文件 (.py)",
            type=['py']
        )
        strategy_params = {}
        
        if strategy_file is not None:
            # 保存上传的文件
            save_path = Path("/tmp") / strategy_file.name
            with open(save_path, "wb") as f:
                f.write(strategy_file.getbuffer())
            
            try:
                strategy_class = load_strategy_from_file(str(save_path))
                st.sidebar.success(f"✅ 成功加载策略: {strategy_class.__name__}")
            except Exception as e:
                st.sidebar.error(f"❌ 加载策略失败: {e}")
    
    # 回测设置
    st.sidebar.header("💰 回测设置")
    initial_cash = st.sidebar.number_input(
        "初始资金",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000
    )
    commission = st.sidebar.slider(
        "手续费率",
        min_value=0.0,
        max_value=0.01,
        value=0.001,
        step=0.0001,
        format="%.4f"
    )
    
    # 运行按钮
    run_button = st.sidebar.button("🚀 运行回测", use_container_width=True)
    
    return {
        'stock_code': stock_code,
        'start_date': start_date,
        'end_date': end_date,
        'strategy_class': strategy_class,
        'strategy_params': strategy_params,
        'initial_cash': initial_cash,
        'commission': commission,
        'run_button': run_button
    }


def render_header():
    """渲染页面头部"""
    st.markdown('<p class="main-header">📈 股票策略回测平台</p>', unsafe_allow_html=True)


def render_metrics(results: dict):
    """渲染指标卡片"""
    if not results or not results.get('success'):
        return
    
    st.subheader("📊 回测结果")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_return = results.get('total_return', 0)
        return_class = "positive" if total_return > 0 else "negative"
        st.metric(
            "总收益率",
            f"{total_return:.2f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            "最大回撤",
            f"{results.get('max_drawdown', 0):.2f}%"
        )
    
    with col3:
        st.metric(
            "夏普比率",
            f"{results.get('sharpe_ratio', 0):.2f}"
        )
    
    with col4:
        st.metric(
            "交易次数",
            f"{results.get('total_trades', 0)}"
        )
    
    # 第二行指标
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        win_rate = results.get('win_rate', 0)
        st.metric(
            "胜率",
            f"{win_rate:.2f}%"
        )
    
    with col6:
        st.metric(
            "最终权益",
            f"¥{results.get('final_equity', 0):,.2f}"
        )
    
    with col7:
        st.metric(
            "买入持有收益",
            f"{results.get('buy_hold_return', 0):.2f}%"
        )
    
    with col8:
        st.metric(
            "SQN",
            f"{results.get('sqn', 0):.2f}"
        )


def render_equity_curve(data: pd.DataFrame, results: dict):
    """渲染权益曲线"""
    if not results or not results.get('success'):
        return
    
    st.subheader("📈 权益曲线")
    
    # 获取权益曲线数据
    engine = st.session_state.get('last_engine')
    if engine and engine.stats is not None:
        equity_df = engine.get_equity_curve()
        
        fig = go.Figure()
        
        # 添加权益曲线
        fig.add_trace(go.Scatter(
            x=equity_df.index,
            y=equity_df['Equity'],
            mode='lines',
            name='策略权益',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # 添加买入持有曲线
        if 'BuyHold' in equity_df.columns:
            fig.add_trace(go.Scatter(
                x=equity_df.index,
                y=equity_df['BuyHold'],
                mode='lines',
                name='买入持有',
                line=dict(color='#ff7f0e', width=1, dash='dash')
            ))
        
        fig.update_layout(
            height=400,
            xaxis_title="日期",
            yaxis_title="权益",
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_price_chart(data: pd.DataFrame):
    """渲染K线图"""
    st.subheader("📊 价格走势")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # K线图
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='K线',
        increasing_line_color='#ff4b4b',
        decreasing_line_color='#26a69a'
    ), row=1, col=1)
    
    # 成交量
    colors = ['#ff4b4b' if close >= open else '#26a69a' 
              for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        name='成交量',
        marker_color=colors,
        opacity=0.6
    ), row=2, col=1)
    
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        yaxis_title="价格",
        yaxis2_title="成交量"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_trades_table(results: dict):
    """渲染交易记录表格"""
    if not results or not results.get('success'):
        return
    
    engine = st.session_state.get('last_engine')
    if engine and engine.stats is not None:
        trades_df = engine.get_trades()
        
        if not trades_df.empty:
            st.subheader("📋 交易记录")
            
            # 格式化交易记录
            trades_display = trades_df.copy()
            trades_display['EntryTime'] = trades_display['EntryTime'].dt.strftime('%Y-%m-%d')
            trades_display['ExitTime'] = trades_display['ExitTime'].dt.strftime('%Y-%m-%d')
            trades_display['PnL'] = trades_display['PnL'].round(2)
            trades_display['ReturnPct'] = (trades_display['ReturnPct'] * 100).round(2).astype(str) + '%'
            
            st.dataframe(trades_display, use_container_width=True)


def render_data_info(data: pd.DataFrame, stock_code: str):
    """渲染数据信息"""
    st.subheader("📋 数据概览")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"**股票代码**: {stock_code}")
    with col2:
        st.info(f"**数据条数**: {len(data)}")
    with col3:
        st.info(f"**日期范围**: {data.index[0].strftime('%Y-%m-%d')} ~ {data.index[-1].strftime('%Y-%m-%d')}")

    # 显示数据预览
    with st.expander("查看数据预览"):
        st.dataframe(data.head(20), use_container_width=True)


def render_signal_panel(data: pd.DataFrame):
    """
    渲染信号面板 - 显示标准化技术指标

    这是V2架构的核心：细粒度信号展示
    """
    st.subheader("📊 技术指标信号 (标准化)")

    # 提取信号
    extractor = SignalExtractor()
    signals = extractor.extract(data)

    # 使用列布局展示指标
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**动量指标 (RoC)**")
        roc_5_color = "🔴" if signals.roc_5d > 0 else "🟢"
        roc_10_color = "🔴" if signals.roc_10d > 0 else "🟢"
        roc_20_color = "🔴" if signals.roc_20d > 0 else "🟢"

        st.metric("5日变动率", f"{roc_5_color} {signals.roc_5d:+.2%}")
        st.metric("10日变动率", f"{roc_10_color} {signals.roc_10d:+.2%}")
        st.metric("20日变动率", f"{roc_20_color} {signals.roc_20d:+.2%}")

    with col2:
        st.markdown("**位置指标 (Z-score)**")
        bb_status = "超卖" if signals.bollinger_z < -2 else "超买" if signals.bollinger_z > 2 else "中性"
        st.metric("布林带Z-score", f"{signals.bollinger_z:+.2f} ({bb_status})")
        st.metric("价格Z-score", f"{signals.price_z:+.2f}")
        st.metric("成交量Z-score", f"{signals.volume_z:+.2f}")

    with col3:
        st.markdown("**趋势指标**")
        trend_dir = "📈 上升" if signals.trend_direction > 0 else "📉 下降" if signals.trend_direction < 0 else "➡️ 震荡"
        st.metric("趋势方向", trend_dir)
        st.metric("趋势强度", f"{signals.trend_strength:.1%}")

        rsi_status = "超卖" if signals.rsi < 30 else "超买" if signals.rsi > 70 else "中性"
        rsi_color = "🟢" if signals.rsi < 30 else "🔴" if signals.rsi > 70 else "⚪"
        st.metric("RSI", f"{rsi_color} {signals.rsi:.1f} ({rsi_status})")

    # 第二行指标
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("**波动率**")
        st.metric("20日波动率", f"{signals.volatility_20d:.2%}")
        st.metric("ATR(14)/价格", f"{signals.atr_14d:.2%}")

    with col5:
        st.markdown("**MACD (归一化)**")
        macd_color = "🔴" if signals.macd_normalized > 0 else "🟢"
        st.metric("MACD", f"{macd_color} {signals.macd_normalized:+.4f}")
        st.metric("Signal", f"{signals.macd_signal:+.4f}")
        st.metric("Histogram", f"{signals.macd_histogram:+.4f}")

    with col6:
        st.markdown("**量价指标**")
        obv_color = "🔴" if signals.obv_trend > 0 else "🟢"
        mf_color = "🔴" if signals.money_flow > 0 else "🟢"
        st.metric("OBV趋势", f"{obv_color} {signals.obv_trend:+.2f}")
        st.metric("资金流向", f"{mf_color} {signals.money_flow:+.2f}")

        rsi_div_color = "🔴" if signals.rsi_divergence > 0 else "🟢" if signals.rsi_divergence < 0 else "⚪"
        div_text = "底背离" if signals.rsi_divergence > 10 else "顶背离" if signals.rsi_divergence < -10 else "无"
        st.metric("RSI背离", f"{rsi_div_color} {signals.rsi_divergence:+.1f} ({div_text})")

    # 综合评分
    st.markdown("---")
    col7, col8 = st.columns([1, 3])

    with col7:
        score = signals.composite_score
        if score > 0.3:
            score_color = "🟢"
            score_text = "看多"
        elif score < -0.3:
            score_color = "🔴"
            score_text = "看空"
        else:
            score_color = "⚪"
            score_text = "中性"

        st.metric("综合评分", f"{score_color} {score:+.2f}", delta=score_text)

    with col8:
        # 信号说明
        st.info(f"""
        **信号解读**：
        - 综合评分基于动量(30%) + 位置(20%) + 趋势(25%) + RSI(15%) + 量价(10%)加权计算
        - 评分范围 -1(看空) 到 +1(看多)，当前 **{score:+.2f}** 表示 **{score_text}**
        - 所有指标已归一化，支持跨标的比较
        """)

    # 显示原始数据（折叠）
    with st.expander("📋 查看完整信号数据"):
        signal_dict = signals.to_dict()
        df_signals = pd.DataFrame([signal_dict]).T
        df_signals.columns = ['数值']
        df_signals['解读'] = df_signals['数值'].apply(lambda x: f"{x:.4f}")
        st.dataframe(df_signals, use_container_width=True)


def render_decision_history(engine):
    """
    渲染V2策略的决策历史

    展示每个交易决策的理由（语义一致性）
    """
    # 获取策略实例（V2策略在回测后存储在 strategy_instance）
    strategy = getattr(engine, 'strategy_instance', None)
    if strategy is None:
        return

    # 检查是否是V2策略
    if not hasattr(strategy, 'get_decision_history'):
        return

    history = strategy.get_decision_history()

    if history.empty:
        return

    st.subheader("📝 决策历史 (V2细粒度)")

    # 只显示交易相关的决策
    trade_decisions = history[history['action'].isin(['buy', 'sell'])]

    if trade_decisions.empty:
        st.info("本回测期间没有交易决策")
        return

    # 格式化显示
    display_df = trade_decisions[['action', 'reason', 'confidence']].copy()
    display_df['操作'] = display_df['action'].map({
        'buy': '🟢 买入',
        'sell': '🔴 卖出'
    })
    display_df['置信度'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
    display_df['决策理由'] = display_df['reason']

    st.dataframe(
        display_df[['操作', '置信度', '决策理由']],
        use_container_width=True
    )

    # 显示决策统计
    with st.expander("📊 决策统计"):
        stats = strategy.get_signal_summary()
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总决策数", stats['total_decisions'])
            with col2:
                st.metric("买入次数", stats['buy_count'])
            with col3:
                st.metric("卖出次数", stats['sell_count'])


def render_oversold_sidebar():
    """渲染超跌反弹策略的侧边栏"""
    st.sidebar.title("⚙️ 参数设置")

    # ========== 快捷预设 ==========
    st.sidebar.header("🎯 快速预设")

    preset = st.sidebar.selectbox(
        "选择参数组合",
        ["自定义", "保守型 (低波动)", "标准型 (平衡)", "激进型 (高频率)"],
        help="快速应用预设参数组合，选择后可继续微调"
    )

    # 预设参数
    if preset == "保守型 (低波动)":
        default_drawdown = 50
        default_lookback = 180
        default_bounce = 20
        default_pullback = 5
        default_stop = 3
        default_volume = 60
    elif preset == "激进型 (高频率)":
        default_drawdown = 25
        default_lookback = 60
        default_bounce = 8
        default_pullback = 12
        default_stop = 8
        default_volume = 85
    else:  # 标准型或自定义
        default_drawdown = 40
        default_lookback = 120
        default_bounce = 12.5
        default_pullback = 8
        default_stop = 5
        default_volume = 70

    # 使用session_state保存参数值，实现输入框和滑块同步
    if 'oversold_params' not in st.session_state:
        st.session_state.oversold_params = {
            'drawdown': default_drawdown,
            'lookback': default_lookback,
            'bounce': default_bounce,
            'pullback': default_pullback,
            'stop': default_stop,
            'volume': default_volume,
        }

    # 更新默认值
    if preset != "自定义":
        st.session_state.oversold_params.update({
            'drawdown': default_drawdown,
            'lookback': default_lookback,
            'bounce': default_bounce,
            'pullback': default_pullback,
            'stop': default_stop,
            'volume': default_volume,
        })

    st.sidebar.divider()

    # ========== 超跌参数 ==========
    st.sidebar.header("📉 超跌参数")

    # 跌幅阈值
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        drawdown_input = st.number_input(
            "跌幅(%)",
            min_value=10.0,
            max_value=80.0,
            value=float(st.session_state.oversold_params['drawdown']),
            step=1.0,
            help="从前高下跌多少才认为是超跌。10%=轻度回调, 40%=深度调整, 80%=极端情况",
            key="drawdown_input"
        )
    with col2:
        drawdown_slider = st.slider(
            "跌幅阈值",
            min_value=10,
            max_value=80,
            value=int(drawdown_input),
            step=1,
            label_visibility="collapsed",
            help="从前高下跌多少才认为是超跌",
            key="drawdown_slider"
        )
    drawdown_threshold = drawdown_input / 100

    # 观察周期
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        lookback_input = st.number_input(
            "周期(天)",
            min_value=20,
            max_value=365,
            value=int(st.session_state.oversold_params['lookback']),
            step=10,
            help="计算跌幅的时间窗口。60日=季度, 120日=半年, 250日=年线",
            key="lookback_input"
        )
    with col2:
        lookback_slider = st.slider(
            "观察周期",
            min_value=20,
            max_value=365,
            value=int(lookback_input),
            step=10,
            label_visibility="collapsed",
            help="计算跌幅的时间窗口",
            key="lookback_slider"
        )
    lookback_period = int(lookback_input)

    st.sidebar.divider()

    # ========== 反弹参数 ==========
    st.sidebar.header("📈 反弹参数")

    # 买入反弹比例
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        bounce_input = st.number_input(
            "买入(%)",
            min_value=1.0,
            max_value=50.0,
            value=float(st.session_state.oversold_params['bounce']),
            step=0.5,
            help="从最低点反弹多少触发买入。5%=短线抢反弹, 12.5%=稳健入场, 30%=趋势确认",
            key="bounce_input"
        )
    with col2:
        bounce_slider = st.slider(
            "买入反弹",
            min_value=1.0,
            max_value=50.0,
            value=bounce_input,
            step=0.5,
            label_visibility="collapsed",
            help="从最低点反弹多少触发买入",
            key="bounce_slider"
        )
    bounce_ratio = bounce_input / 100

    # 卖出回调比例
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        pullback_input = st.number_input(
            "卖出(%)",
            min_value=1.0,
            max_value=30.0,
            value=float(st.session_state.oversold_params['pullback']),
            step=0.5,
            help="从买入点回调多少触发卖出。3%=严格止盈, 8%=平衡策略, 20%=承受较大回撤",
            key="pullback_input"
        )
    with col2:
        pullback_slider = st.slider(
            "卖出回调",
            min_value=1.0,
            max_value=30.0,
            value=pullback_input,
            step=0.5,
            label_visibility="collapsed",
            help="从买入点回调多少触发卖出",
            key="pullback_slider"
        )
    pullback_ratio = pullback_input / 100

    st.sidebar.divider()

    # ========== 风控参数 ==========
    st.sidebar.header("🛑 风控参数")

    # 硬止损比例
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        stop_input = st.number_input(
            "止损(%)",
            min_value=1.0,
            max_value=20.0,
            value=float(st.session_state.oversold_params['stop']),
            step=0.5,
            help="跌破前低多少强制止损。2%=超短保护, 5%=常规止损, 15%=宽松风控",
            key="stop_input"
        )
    with col2:
        stop_slider = st.slider(
            "硬止损",
            min_value=1.0,
            max_value=20.0,
            value=stop_input,
            step=0.5,
            label_visibility="collapsed",
            help="跌破前低多少强制止损",
            key="stop_slider"
        )
    stop_loss_pct = stop_input / 100

    # 成交量过滤
    enable_volume_filter = st.sidebar.checkbox(
        "启用成交量过滤",
        value=True,
        help="超跌股通常伴随成交量萎缩"
    )

    # 成交量萎缩阈值
    col1, col2 = st.sidebar.columns([1, 2])
    with col1:
        volume_input = st.number_input(
            "量比(%)",
            min_value=20.0,
            max_value=100.0,
            value=float(st.session_state.oversold_params['volume']),
            step=5.0,
            help="20日均量/60日均量的阈值。50%=严重缩量, 70%=明显缩量, 90%=轻微缩量",
            key="volume_input",
            disabled=not enable_volume_filter
        )
    with col2:
        volume_slider = st.slider(
            "成交量比",
            min_value=20,
            max_value=100,
            value=int(volume_input),
            step=5,
            label_visibility="collapsed",
            help="20日均量/60日均量的阈值",
            key="volume_slider",
            disabled=not enable_volume_filter
        )
    volume_contraction = volume_input / 100

    st.sidebar.divider()

    # ========== 回测设置 ==========
    st.sidebar.header("💰 回测设置")

    initial_cash = st.sidebar.number_input(
        "初始资金",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000
    )

    # 手续费率使用百分比输入更直观
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        commission_pct = st.number_input(
            "手续费率(%)",
            min_value=0.0,
            max_value=0.5,
            value=0.1,
            step=0.01,
            format="%.2f",
            help="单边交易成本（佣金+印花税+滑点）。0.05%=低成本, 0.1%=标准成本, 0.3%=较高成本"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"= {commission_pct/100:.4f}")
    commission = commission_pct / 100

    # 策略风格
    st.sidebar.divider()
    st.sidebar.header("🎨 策略风格")

    strategy_style = st.sidebar.radio(
        "选择风格",
        ["标准版", "保守版", "激进版"],
        help="标准版=平衡参数, 保守版=更严格条件更高胜率, 激进版=更宽松条件更高频率"
    )

    if strategy_style == "标准版":
        strategy_class = OversoldBounceStrategy
    elif strategy_style == "保守版":
        strategy_class = OversoldBounceConservative
    else:
        strategy_class = OversoldBounceAggressive

    # 扫描按钮
    st.sidebar.divider()
    scan_button = st.sidebar.button("🔍 开始扫描", use_container_width=True, type="primary")

    # 更新session_state
    st.session_state.oversold_params.update({
        'drawdown': drawdown_input,
        'lookback': lookback_period,
        'bounce': bounce_input,
        'pullback': pullback_input,
        'stop': stop_input,
        'volume': volume_input,
    })

    return {
        'drawdown_threshold': drawdown_threshold,
        'lookback_period': lookback_period,
        'bounce_ratio': bounce_ratio,
        'pullback_ratio': pullback_ratio,
        'stop_loss_pct': stop_loss_pct,
        'enable_volume_filter': enable_volume_filter,
        'volume_contraction': volume_contraction,
        'strategy_class': strategy_class,
        'strategy_style': strategy_style,
        'initial_cash': initial_cash,
        'commission': commission,
        'scan_button': scan_button,
        'preset': preset
    }


def render_oversold_page(params: dict):
    """渲染超跌反弹策略页面"""
    st.markdown('<p class="main-header">📉 超跌反弹策略</p>', unsafe_allow_html=True)

    st.info("""
    **策略说明**：基于均值回归理论，捕捉深度超跌后的技术性反弹机会。

    **核心逻辑**：
    1. 选择从前高下跌超过40%的股票（120日观察期）
    2. 成交量萎缩确认（缩量下跌 = 抛压减轻）
    3. 买入触发：从最低点反弹12.5%
    4. 卖出触发：从买入点回调8% 或 硬止损-5%
    """)

    # 扫描功能
    if params['scan_button']:
        with st.spinner("🔍 正在扫描全市场..."):
            # 创建扫描器
            scanner = OversoldScanner(st.session_state.data_loader)
            st.session_state.oversold_scanner = scanner

            # 扫描进度条
            progress_bar = st.progress(0)
            status_text = st.empty()

            def progress_callback(current, total):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"扫描进度: {current}/{total} ({progress*100:.1f}%)")

            # 执行扫描
            candidates = scanner.scan_all_stocks(
                drawdown_threshold=params['drawdown_threshold'],
                lookback_period=params['lookback_period'],
                bounce_ratio=params['bounce_ratio'],
                enable_volume_filter=params['enable_volume_filter'],
                volume_contraction=params['volume_contraction'],
                progress_callback=progress_callback
            )

            st.session_state.oversold_scan_results = candidates

            if candidates:
                st.success(f"✅ 扫描完成！找到 {len(candidates)} 只超跌股票")
            else:
                st.warning("⚠️ 未找到符合条件的股票")

    # 显示扫描结果
    if st.session_state.oversold_scan_results:
        render_scan_results(st.session_state.oversold_scan_results)

        # 回测验证
        st.markdown("---")
        st.subheader("🔄 回测验证")

        # 获取可买入的候选
        buyable = [c for c in st.session_state.oversold_scan_results if c.meet_all_conditions]

        if buyable:
            selected_code = st.selectbox(
                "选择股票进行回测验证",
                options=[c.code for c in buyable],
                format_func=lambda x: f"{x} - {[c.name for c in buyable if c.code == x][0]}"
            )

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "回测开始日期",
                    value=datetime.now() - timedelta(days=365),
                    max_value=datetime.now()
                )
            with col2:
                end_date = st.date_input(
                    "回测结束日期",
                    value=datetime.now(),
                    max_value=datetime.now()
                )

            if st.button("🚀 运行回测"):
                run_oversold_backtest(
                    selected_code,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    params
                )
        else:
            st.info("没有满足所有买入条件的股票，无法回测")


def render_scan_results(candidates: list):
    """渲染扫描结果"""
    st.subheader("📊 扫描结果")

    # 摘要统计
    summary = {
        'total': len(candidates),
        'buyable': len([c for c in candidates if c.meet_all_conditions]),
        'watch_only': len([c for c in candidates if c.is_oversold and not c.meet_all_conditions]),
        'avg_drawdown': sum(c.drawdown_pct for c in candidates) / len(candidates) if candidates else 0,
    }

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("超跌股票数", summary['total'])
    with col2:
        st.metric("可买入", summary['buyable'])
    with col3:
        st.metric("观察中", summary['watch_only'])
    with col4:
        st.metric("平均跌幅", f"{summary['avg_drawdown']:.1f}%")

    # 分类显示
    tab1, tab2 = st.tabs(["✅ 可买入", "👀 观察列表"])

    with tab1:
        buyable = [c for c in candidates if c.meet_all_conditions]
        if buyable:
            display_data = [c.to_display_dict() for c in buyable]
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("没有满足所有买入条件的股票")

    with tab2:
        watchlist = [c for c in candidates if c.is_oversold and not c.meet_all_conditions]
        if watchlist:
            display_data = [c.to_display_dict() for c in watchlist]
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("没有观察中的股票")

    # 导出按钮
    if st.button("📥 导出结果"):
        if st.session_state.oversold_scanner:
            filepath = st.session_state.oversold_scanner.export_results(candidates)
            if filepath:
                st.success(f"结果已保存至: {filepath}")


def run_oversold_backtest(code: str, start_date: str, end_date: str, params: dict):
    """运行超跌反弹策略回测"""
    try:
        with st.spinner(f"🔄 正在对 {code} 运行回测..."):
            # 获取数据
            data = st.session_state.data_loader.get_stock_data(code, start_date, end_date)

            if data.empty:
                st.error(f"❌ 未找到 {code} 的数据")
                return

            # 创建回测引擎
            engine = BacktestEngine(
                data=data,
                strategy_class=params['strategy_class'],
                cash=params['initial_cash'],
                commission=params['commission']
            )

            # 运行回测
            results = engine.run(
                drawdown_threshold=params['drawdown_threshold'],
                lookback_period=params['lookback_period'],
                bounce_ratio=params['bounce_ratio'],
                pullback_ratio=params['pullback_ratio'],
                stop_loss_pct=params['stop_loss_pct'],
                enable_volume_filter=params['enable_volume_filter'],
                volume_contraction=params['volume_contraction']
            )

            st.session_state.backtest_results = results
            st.session_state.last_engine = engine

            if results['success']:
                st.success("✅ 回测完成！")
                # 显示结果
                render_metrics(results)
                render_equity_curve(data, results)
                render_decision_history(engine)
                render_trades_table(results)
            else:
                st.error(f"❌ 回测失败: {results.get('error', '未知错误')}")

    except Exception as e:
        st.error(f"❌ 发生错误: {e}")
        import traceback
        st.code(traceback.format_exc())


def main():
    """主函数"""
    init_session_state()

    # 侧边栏选择功能模块
    st.sidebar.title("📊 功能模块")
    page = st.sidebar.radio(
        "选择功能",
        ["单股票回测", "超跌反弹策略"]
    )

    if page == "单股票回测":
        # 原有功能
        render_header()
        params = render_sidebar()

        # 加载数据
        try:
            with st.spinner("📥 正在加载数据..."):
                data = st.session_state.data_loader.get_stock_data(
                    params['stock_code'],
                    params['start_date'].strftime('%Y-%m-%d'),
                    params['end_date'].strftime('%Y-%m-%d')
                )

            if data.empty:
                st.error(f"❌ 未找到股票 {params['stock_code']} 的数据，请检查代码是否正确")
                return

            # 显示数据信息
            render_data_info(data, params['stock_code'])

            # 显示信号面板（V2细粒度）
            if len(data) >= 20:
                render_signal_panel(data)

            # 显示价格图表
            render_price_chart(data)

            # 运行回测
            if params['run_button']:
                if params['strategy_class'] is None:
                    st.error("❌ 请选择或上传策略文件")
                    return

                with st.spinner("🔄 正在运行回测..."):
                    engine = BacktestEngine(
                        data=data,
                        strategy_class=params['strategy_class'],
                        cash=params['initial_cash'],
                        commission=params['commission']
                    )

                    results = engine.run(**params['strategy_params'])

                    st.session_state.backtest_results = results
                    st.session_state.last_engine = engine

                    if results['success']:
                        st.success("✅ 回测完成！")
                    else:
                        st.error(f"❌ 回测失败: {results.get('error', '未知错误')}")

            # 显示回测结果
            if st.session_state.backtest_results:
                render_metrics(st.session_state.backtest_results)
                render_equity_curve(data, st.session_state.backtest_results)

                if st.session_state.get('last_engine'):
                    render_decision_history(st.session_state.last_engine)

                render_trades_table(st.session_state.backtest_results)

        except Exception as e:
            st.error(f"❌ 发生错误: {e}")
            import traceback
            st.code(traceback.format_exc())

    else:  # 超跌反弹策略
        params = render_oversold_sidebar()
        render_oversold_page(params)


if __name__ == "__main__":
    main()
