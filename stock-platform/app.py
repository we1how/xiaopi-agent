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
    if 'oversold_analysis_results' not in st.session_state:
        st.session_state.oversold_analysis_results = None


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
    """渲染超跌反弹策略的侧边栏 - 使用st.form防止rerun"""
    st.sidebar.title("⚙️ 参数设置")

    # 日期选择（放在form外部，可独立调节）
    st.sidebar.subheader("📅 日期范围")

    # 结束日期默认为今天
    end_date = st.sidebar.date_input(
        "结束日期",
        value=datetime.now(),
        max_value=datetime.now(),
        help="扫描数据的截止日期"
    )

    # 开始日期默认为结束日期往前120天
    default_start = end_date - timedelta(days=120)
    start_date = st.sidebar.date_input(
        "开始日期",
        value=default_start,
        max_value=end_date,
        help="扫描数据的开始日期"
    )

    st.sidebar.divider()

    # 使用form包裹扫描参数，避免调节参数时触发rerun
    with st.sidebar.form("oversold_params_form"):
        st.subheader("📉 超跌参数")

        st.caption("💡 观察周期：计算前期高点时回看多少天。期间最高点与当前价格的差值即为跌幅")

        # 观察周期（独立参数，不绑定日期范围）
        lookback_period = st.number_input(
            "观察周期 (天)",
            min_value=20,
            max_value=365,
            value=120,
            step=10,
            help="计算跌幅时回看多少天。60日=季度, 120日=半年, 250日=年线。例：120表示看120天内最高价跌了百分之多少",
        )

        st.caption("💡 跌幅阈值：从前高下跌超过此比例才认为是超跌。用盘中最高价计算")

        # 跌幅阈值 - 放宽默认值为30%
        drawdown_pct = st.number_input(
            "跌幅阈值 (%)",
            min_value=10.0,
            max_value=80.0,
            value=30.0,
            step=5.0,
            help="从前高下跌多少才认为是超跌。例：30%表示股票从120天内最高价跌了30%以上",
        )

        st.subheader("📈 反弹参数")

        st.caption("💡 反弹比例：从观察期内最低点反弹超过此比例，认为是企稳信号。用于确认止跌回升")

        # 买入反弹比例 - 放宽默认值为10%
        bounce_pct = st.number_input(
            "反弹比例 (%)",
            min_value=1.0,
            max_value=50.0,
            value=10.0,
            step=1.0,
            help="从最低点反弹多少视为企稳。例：10%表示从120天内最低价涨了10%以上。太小容易假突破，太大可能错过买点",
        )

        st.subheader("📊 成交量筛选（可选）")

        st.caption("💡 缩量说明：超跌过程中成交量萎缩，表示抛压减轻、卖盘枯竭，是止跌信号之一")

        # 成交量过滤
        enable_volume_filter = st.checkbox(
            "启用成交量筛选",
            value=False,
            help="启用后只显示成交量萎缩的股票。超跌时缩量表示抛压减轻，是企稳信号"
        )

        st.caption("💡 成交量比：最近20日平均成交量 ÷ 最近60日平均成交量。比值越小说明缩量越明显")

        # 成交量萎缩阈值
        volume_pct = st.number_input(
            "成交量比 (%)",
            min_value=20.0,
            max_value=100.0,
            value=70.0,
            step=5.0,
            help="20日均量/60日均量的阈值。50%=严重缩量, 70%=明显缩量, 90%=轻微缩量",
            disabled=not enable_volume_filter
        )

        st.subheader("🎯 分析设置")

        # 持有期计算
        hold_days = st.number_input(
            "持有期 (天)",
            min_value=5,
            max_value=120,
            value=20,
            step=5,
            help="计算成功率的持有期。10天=短线, 20天=中线, 60天=长线"
        )

        # 目标涨幅
        target_pct = st.number_input(
            "目标涨幅 (%)",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=5.0,
            help="达到此涨幅视为成功"
        )

        # form提交按钮
        st.divider()
        scan_button = st.form_submit_button("🔍 开始扫描", use_container_width=True, type="primary")

    # form外部的信息提示（修改参数不会触发rerun）
    st.sidebar.divider()
    st.sidebar.header("💡 使用提示")

    # 显示当前参数摘要
    st.sidebar.caption("当前参数：")
    st.sidebar.caption(f"- 日期范围: {start_date.strftime('%m-%d')} 至 {end_date.strftime('%m-%d')}")
    st.sidebar.caption(f"- 跌幅阈值: {drawdown_pct}%")
    st.sidebar.caption(f"- 买入反弹: {bounce_pct}%")
    st.sidebar.caption(f"- 成交量过滤: {'开' if enable_volume_filter else '关'}")

    st.sidebar.info("""
    **使用说明**：
    1. 设置日期范围和筛选条件
    2. 点击"开始扫描"获取超跌股票列表
    3. 在结果中查看每只股票的成功率分析

    **关闭应用**：在终端按 `Ctrl+C`
    """)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'drawdown_threshold': drawdown_pct / 100,
        'lookback_period': int(lookback_period),
        'bounce_ratio': bounce_pct / 100,
        'enable_volume_filter': enable_volume_filter,
        'volume_contraction': volume_pct / 100,
        'hold_days': int(hold_days),
        'target_pct': target_pct / 100,
        'scan_button': scan_button
    }


def render_oversold_page(params: dict):
    """渲染超跌反弹策略页面 - 两阶段筛选"""
    st.markdown('<p class="main-header">📉 超跌反弹策略</p>', unsafe_allow_html=True)

    st.info("""
    **策略说明**：基于均值回归理论，捕捉深度超跌后的技术性反弹机会。

    **使用流程**：
    1. **第一阶段**：使用宽松条件筛选超跌股票（跌幅+反弹+可选成交量）
    2. **第二阶段**：对筛选结果计算成功率/失败率等指标
    """)

    # 显示当前参数
    st.caption(f"📅 数据范围：{params['start_date'].strftime('%Y-%m-%d')} 至 {params['end_date'].strftime('%Y-%m-%d')} | 🔍 观察周期：{params['lookback_period']}天")

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

            # 执行第一阶段扫描（宽松条件）
            candidates = scanner.scan_all_stocks(
                drawdown_threshold=params['drawdown_threshold'],
                lookback_period=params['lookback_period'],
                bounce_ratio=params['bounce_ratio'],
                enable_volume_filter=params['enable_volume_filter'],
                volume_contraction=params['volume_contraction'],
                progress_callback=progress_callback,
                start_date=params['start_date'].strftime('%Y-%m-%d'),
                end_date=params['end_date'].strftime('%Y-%m-%d')
            )

            st.session_state.oversold_scan_results = candidates

            if candidates:
                st.success(f"✅ 第一阶段完成！找到 {len(candidates)} 只超跌股票")
            else:
                st.warning("⚠️ 未找到符合条件的股票")

    # 显示扫描结果（第一阶段）
    if st.session_state.oversold_scan_results:
        render_scan_results(st.session_state.oversold_scan_results)

        # 第二阶段：详细分析（独立可折叠区域）
        st.markdown("---")
        with st.expander("📊 点击查看策略回测验证", expanded=False):
            render_backtest_section(st.session_state.oversold_scan_results, params)


def render_backtest_section(candidates, scan_params):
    """渲染独立的策略回测验证区域 - 使用每只股票的独立买入日期"""
    st.subheader("📈 策略回测验证")

    st.info(f"对扫描出的 **{len(candidates)}** 只超跌股票进行回测验证。每只股票的买入日期为其反弹触发日期。")

    # 获取数据库日期范围
    db_start, db_end = st.session_state.data_loader.get_date_range()
    max_date = datetime.strptime(db_end, '%Y-%m-%d').date() if isinstance(db_end, str) else db_end
    if hasattr(max_date, 'date'):
        max_date = max_date.date()

    # 过滤掉没有触发日期的股票
    valid_candidates = [c for c in candidates if c.bounce_trigger_date]

    if not valid_candidates:
        st.warning("⚠️ 没有可回测的股票（缺少反弹触发日期）")
        st.info("💡 请重新扫描股票以获取反弹触发日期")
        return

    st.caption(f"其中 **{len(valid_candidates)}** 只股票有明确的反弹触发日期")

    # 显示有/无触发日期的统计
    no_trigger_count = len(candidates) - len(valid_candidates)
    if no_trigger_count > 0:
        st.caption(f"另有 {no_trigger_count} 只股票缺少触发日期（可能数据不足）")

    # 回测参数设置（独立于扫描参数）
    st.markdown("**回测参数设置**")

    col1, col2, col3 = st.columns(3)

    with col1:
        hold_days = st.number_input(
            "持有期 (天)",
            min_value=5,
            max_value=120,
            value=scan_params.get('hold_days', 20),
            step=5,
            help="从每只股票反弹触发日期开始计算持有天数"
        )

    with col2:
        target_pct = st.number_input(
            "目标涨幅 (%)",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=5.0,
            help="达到此涨幅视为成功（止盈）"
        )

    with col3:
        stop_pct = st.number_input(
            "止损比例 (%)",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=1.0,
            help="跌破此比例视为失败（止损）"
        )

    # 执行回测按钮
    if st.button("🚀 开始回测验证", type="primary", use_container_width=True):
        # 构建回测参数
        backtest_params = {
            'hold_days': int(hold_days),
            'target_pct': target_pct / 100,
            'stop_pct': stop_pct / 100,
        }

        try:
            with st.spinner(f"正在对 {len(valid_candidates)} 只股票进行回测..."):
                analysis_results = analyze_backtest_performance(
                    valid_candidates,
                    st.session_state.data_loader,
                    backtest_params
                )
                st.session_state.backtest_results = analysis_results

                if analysis_results:
                    st.success(f"✅ 回测完成！成功分析 {len(analysis_results)} / {len(valid_candidates)} 只股票")
                else:
                    st.warning("⚠️ 没有获得有效的回测结果，请检查数据范围是否足够")
        except Exception as e:
            st.error(f"❌ 回测过程出错: {e}")
            import traceback
            st.code(traceback.format_exc())

    # 显示回测结果
    if st.session_state.get('backtest_results'):
        render_backtest_results(st.session_state.backtest_results)


def analyze_backtest_performance(candidates, data_loader, params):
    """
    分析回测表现 - 新版本，修复空结果问题

    Returns:
        List[dict]: 每只股票的回测结果
    """
    results = []
    hold_days = params['hold_days']
    target_pct = params['target_pct']
    stop_pct = params['stop_pct']

    # 获取数据库最新日期
    db_start, db_end = data_loader.get_date_range()
    max_date = datetime.strptime(db_end, '%Y-%m-%d').date() if isinstance(db_end, str) else db_end
    if hasattr(max_date, 'date'):
        max_date = max_date.date()

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, candidate in enumerate(candidates):
        progress = (i + 1) / len(candidates)
        progress_bar.progress(progress)
        status_text.text(f"回测进度: {i+1}/{len(candidates)} ({progress*100:.1f}%) - {candidate.code}")

        try:
            # 使用每只股票的反弹触发日期作为买入日期
            if not candidate.bounce_trigger_date:
                continue

            buy_date = datetime.strptime(candidate.bounce_trigger_date, '%Y-%m-%d').date()

            # 检查买入日期是否有效
            if buy_date >= max_date:
                continue

            # 计算分析结束日期（买入日期 + 持有期），但不能超过数据库最新日期
            analysis_end = min(buy_date + timedelta(days=hold_days + 30), max_date)

            # 获取数据：从买入日期前几天开始（确保能获取到买入日数据）
            data_start = buy_date - timedelta(days=5)

            df = data_loader.get_stock_data(
                candidate.code,
                data_start.strftime('%Y-%m-%d'),
                analysis_end.strftime('%Y-%m-%d')
            )

            if df.empty or len(df) < 2:
                continue

            # 找到买入日或之后的第一个交易日
            buy_date_ts = pd.Timestamp(buy_date)
            valid_data = df[df.index >= buy_date_ts]

            if valid_data.empty:
                continue

            # 使用第一个可用交易日的收盘价作为买入价
            entry_price = valid_data['Close'].iloc[0]
            actual_buy_date = valid_data.index[0].strftime('%Y-%m-%d')

            # 持有期内的数据（最多hold_days个交易日）
            hold_data = valid_data.head(hold_days)
            if len(hold_data) < 1:
                continue

            # 回测逻辑：逐日检查是否触发止盈或止损
            result_status = 'holding'
            trigger_date = None
            trigger_price = None
            trigger_type = None
            exit_date = hold_data.index[-1].strftime('%Y-%m-%d')
            exit_price = hold_data['Close'].iloc[-1]
            hold_period = len(hold_data)

            for idx in range(len(hold_data)):
                current_date = hold_data.index[idx]
                high_price = hold_data['High'].iloc[idx]
                low_price = hold_data['Low'].iloc[idx]

                # 检查止盈
                gain_pct = (high_price - entry_price) / entry_price
                if gain_pct >= target_pct:
                    result_status = 'success'
                    trigger_date = current_date.strftime('%Y-%m-%d')
                    trigger_price = high_price
                    trigger_type = 'target'
                    exit_date = trigger_date
                    exit_price = entry_price * (1 + target_pct)
                    hold_period = idx + 1
                    break

                # 检查止损
                loss_pct = (low_price - entry_price) / entry_price
                if loss_pct <= -stop_pct:
                    result_status = 'failure'
                    trigger_date = current_date.strftime('%Y-%m-%d')
                    trigger_price = low_price
                    trigger_type = 'stop'
                    exit_date = trigger_date
                    exit_price = entry_price * (1 - stop_pct)
                    hold_period = idx + 1
                    break

            # 计算收益
            final_return = (exit_price - entry_price) / entry_price
            max_gain = (hold_data['High'].max() - entry_price) / entry_price
            max_loss = (hold_data['Low'].min() - entry_price) / entry_price

            results.append({
                'code': candidate.code,
                'name': candidate.name,
                'industry': candidate.industry,
                'scan_date': candidate.scan_date,
                'scan_price': candidate.current_price,
                'entry_date': actual_buy_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_period': hold_period,
                'result_status': result_status,
                'trigger_date': trigger_date,
                'trigger_type': trigger_type,
                'max_gain': max_gain,
                'max_loss': max_loss,
                'final_return': final_return,
                'drawdown_at_scan': candidate.drawdown_pct,
                'bounce_at_scan': candidate.bounce_from_low,
            })

        except Exception as e:
            # 静默跳过错误，不中断整体回测
            continue

    progress_bar.empty()
    status_text.empty()

    return results


def render_backtest_results(results):
    """渲染回测结果"""
    if not results:
        st.warning("没有回测结果")
        return

    # 统计
    total = len(results)
    success = sum(1 for r in results if r['result_status'] == 'success')
    failure = sum(1 for r in results if r['result_status'] == 'failure')
    holding = total - success - failure

    avg_return = sum(r['final_return'] for r in results) / total * 100

    # 显示汇总
    st.markdown("---")
    st.subheader("📊 回测统计汇总")

    cols = st.columns(5)
    with cols[0]:
        st.metric("回测股票数", total)
    with cols[1]:
        st.metric("✅ 成功", f"{success} ({success/total*100:.1f}%)")
    with cols[2]:
        st.metric("❌ 止损", f"{failure} ({failure/total*100:.1f}%)")
    with cols[3]:
        st.metric("➖ 持有到期", f"{holding} ({holding/total*100:.1f}%)")
    with cols[4]:
        st.metric("平均收益", f"{avg_return:.1f}%")

    # 详细表格
    st.subheader("📋 详细回测结果")

    df_data = []
    for r in results:
        if r['result_status'] == 'success':
            status = "✅ 止盈"
            detail = f"于 {r['trigger_date']} 达到目标"
        elif r['result_status'] == 'failure':
            status = "❌ 止损"
            detail = f"于 {r['trigger_date']} 触发止损"
        else:
            status = "➖ 到期"
            detail = f"持有 {r['hold_period']} 天后平仓"

        df_data.append({
            '股票代码': r['code'],
            '股票名称': r['name'] if r['name'] else '-',
            '买入日期': r['entry_date'],
            '买入价': f"{r['entry_price']:.2f}",
            '卖出日期': r['exit_date'],
            '卖出价': f"{r['exit_price']:.2f}",
            '持有天数': r['hold_period'],
            '结果': status,
            '详情': detail,
            '收益率': f"{r['final_return']*100:.1f}%",
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, height=400)

    # 按结果分类展示
    tabs = st.tabs(["✅ 成功股票", "❌ 止损股票", "➖ 持有到期"])

    with tabs[0]:
        success_list = [r for r in results if r['result_status'] == 'success']
        if success_list:
            for r in success_list[:20]:  # 限制显示前20只
                st.write(f"**{r['code']}** {r['name'] or ''} - 于 **{r['trigger_date']}** 止盈，收益 **{r['final_return']*100:.1f}%**")
        else:
            st.info("没有成功止盈的股票")

    with tabs[1]:
        failure_list = [r for r in results if r['result_status'] == 'failure']
        if failure_list:
            for r in failure_list[:20]:
                st.write(f"**{r['code']}** {r['name'] or ''} - 于 **{r['trigger_date']}** 止损，亏损 **{r['final_return']*100:.1f}%**")
        else:
            st.info("没有触发止损的股票")

    with tabs[2]:
        holding_list = [r for r in results if r['result_status'] == 'holding']
        if holding_list:
            for r in holding_list[:20]:
                profit = "盈利" if r['final_return'] > 0 else "亏损"
                st.write(f"**{r['code']}** {r['name'] or ''} - 持有到期，{profit} **{r['final_return']*100:.1f}%**")
        else:
            st.info("没有持有到期的股票")


def render_scan_results(candidates: list):
    """渲染扫描结果"""
    st.subheader("📊 扫描结果")

    # 如果没有结果，显示调试建议
    if not candidates:
        st.warning("⚠️ 未找到符合条件的股票")

        with st.expander("🔍 查看可能的原因"):
            st.markdown("""
            **可能的原因：**
            1. **参数过于严格** - 尝试放宽跌幅阈值（如设为20-30%）
            2. **市场环境** - 当前可能处于牛市，很少有超跌股票
            3. **数据问题** - 检查数据是否最新、完整
            4. **观察周期** - 尝试缩短观察周期（如60天）

            **建议调整：**
            - 跌幅阈值: 30% → 20%
            - 买入反弹: 10% → 5%
            - 观察周期: 120天 → 60天
            - 关闭成交量过滤（测试用）
            """)
        return

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


def analyze_candidates_performance(candidates, data_loader, params):
    """
    第二阶段：分析候选股票的持有期表现

    分析逻辑：
    - 以扫描结束日期的收盘价为买入点
    - 在持有期内（hold_days）检查是否触发目标涨幅或止损
    - 记录触发日期、触发类型、持有天数
    - 如果持有期内未触发任何条件，则以持有期最后一天的收盘价结算

    Returns:
        List[dict]: 每只股票的详细分析结果
    """
    results = []
    hold_days = params['hold_days']
    target_pct = params['target_pct']
    stop_pct = 0.05  # 5%止损

    # 获取数据库的日期范围
    db_start, db_end = data_loader.get_date_range()

    # 统一转换为datetime.date类型
    def to_date(dt):
        if isinstance(dt, str):
            return datetime.strptime(dt, '%Y-%m-%d').date()
        elif hasattr(dt, 'date'):  # pandas Timestamp
            return dt.date()
        else:
            return dt

    max_available_date = to_date(db_end)

    # 检查扫描结束日期是否在数据库范围内
    scan_end = to_date(params['end_date'])

    if scan_end >= max_available_date:
        st.error(f"❌ 无法分析：扫描结束日期 {scan_end} 超过了数据库最新日期 {max_available_date}")
        st.info("💡 请将扫描的结束日期设置为历史日期（数据库最新日期之前），以便分析后续表现")
        return []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, candidate in enumerate(candidates):
        progress = (i + 1) / len(candidates)
        progress_bar.progress(progress)
        status_text.text(f"分析进度: {i+1}/{len(candidates)} ({progress*100:.1f}%) - {candidate.code}")

        try:
            # 买入日期是扫描结束日期
            analysis_start = scan_end
            # 获取持有期+缓冲期的数据，但不能超过数据库最新日期
            analysis_end = min(scan_end + timedelta(days=hold_days + 30), max_available_date)

            start_str = analysis_start.strftime('%Y-%m-%d') if hasattr(analysis_start, 'strftime') else str(analysis_start)
            end_str = analysis_end.strftime('%Y-%m-%d') if hasattr(analysis_end, 'strftime') else str(analysis_end)

            df = data_loader.get_stock_data(
                candidate.code,
                start_str,
                end_str
            )

            if df.empty:
                continue

            # 获取买入日数据（扫描结束日期的收盘价）
            entry_price = candidate.current_price
            entry_date = start_str

            # 持有期内的数据（最多hold_days个交易日）
            hold_data = df.head(hold_days)
            if len(hold_data) < 1:
                continue

            # 检查持有期内每一天，按时间顺序检查是否触发条件
            # 优先记录最先触发的条件
            result_status = 'holding'  # success, failure, holding
            trigger_date = None
            trigger_price = None
            trigger_type = None  # 'target', 'stop', 'timeout'
            exit_date = hold_data.index[-1].strftime('%Y-%m-%d')
            exit_price = hold_data['Close'].iloc[-1]
            hold_period = len(hold_data)

            for idx in range(len(hold_data)):
                current_date = hold_data.index[idx]
                high_price = hold_data['High'].iloc[idx]
                low_price = hold_data['Low'].iloc[idx]

                # 检查是否达到目标涨幅（盘中最高价）
                gain_pct = (high_price - entry_price) / entry_price
                if gain_pct >= target_pct:
                    result_status = 'success'
                    trigger_date = current_date.strftime('%Y-%m-%d')
                    trigger_price = high_price
                    trigger_type = 'target'
                    exit_date = trigger_date
                    exit_price = entry_price * (1 + target_pct)  # 按目标价卖出
                    hold_period = idx + 1
                    break

                # 检查是否触发止损（盘中最低价）
                loss_pct = (low_price - entry_price) / entry_price
                if loss_pct <= -stop_pct:
                    result_status = 'failure'
                    trigger_date = current_date.strftime('%Y-%m-%d')
                    trigger_price = low_price
                    trigger_type = 'stop'
                    exit_date = trigger_date
                    exit_price = entry_price * (1 - stop_pct)  # 按止损价卖出
                    hold_period = idx + 1
                    break

            # 计算最终收益
            final_return = (exit_price - entry_price) / entry_price
            max_gain = (hold_data['High'].max() - entry_price) / entry_price
            max_loss = (hold_data['Low'].min() - entry_price) / entry_price

            results.append({
                'code': candidate.code,
                'name': candidate.name,
                'industry': candidate.industry,
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_period': hold_period,
                'result_status': result_status,
                'trigger_date': trigger_date,
                'trigger_type': trigger_type,
                'trigger_price': trigger_price,
                'max_gain': max_gain,
                'max_loss': max_loss,
                'final_return': final_return,
                'drawdown_at_scan': candidate.drawdown_pct,
                'bounce_at_scan': candidate.bounce_from_low,
            })

        except Exception as e:
            st.warning(f"分析 {candidate.code} 失败: {e}")
            import traceback
            st.code(traceback.format_exc())
            continue

    progress_bar.empty()
    status_text.empty()

    return results


def render_analysis_results(results, params):
    """渲染第二阶段分析结果 - 带详细日期信息"""
    if not results:
        st.warning("没有分析结果")
        return

    # 统计指标
    total = len(results)
    success_count = sum(1 for r in results if r['result_status'] == 'success')
    failure_count = sum(1 for r in results if r['result_status'] == 'failure')
    neutral_count = sum(1 for r in results if r['result_status'] == 'holding')

    success_rate = success_count / total * 100 if total > 0 else 0
    failure_rate = failure_count / total * 100 if total > 0 else 0

    # 计算平均收益
    avg_final_return = sum(r['final_return'] for r in results) / total * 100 if total > 0 else 0
    avg_hold_days = sum(r['hold_period'] for r in results) / total if total > 0 else 0

    # 显示汇总统计
    st.subheader("📈 汇总统计")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("分析股票数", total)
    with col2:
        st.metric(f"✅ 成功(≥{params['target_pct']*100:.0f}%)", f"{success_count} ({success_rate:.1f}%)")
    with col3:
        st.metric("❌ 失败(止损)", f"{failure_count} ({failure_rate:.1f}%)")
    with col4:
        st.metric("➖ 持有到期", f"{neutral_count} ({neutral_count/total*100:.1f}%)")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("平均收益", f"{avg_final_return:.1f}%")
    with col6:
        success_returns = [r['final_return']*100 for r in results if r['result_status'] == 'success']
        avg_success_return = sum(success_returns) / len(success_returns) if success_returns else 0
        st.metric("成功股平均收益", f"{avg_success_return:.1f}%")
    with col7:
        failure_returns = [r['final_return']*100 for r in results if r['result_status'] == 'failure']
        avg_failure_return = sum(failure_returns) / len(failure_returns) if failure_returns else 0
        st.metric("失败股平均亏损", f"{avg_failure_return:.1f}%")
    with col8:
        st.metric("平均持有天数", f"{avg_hold_days:.0f}天")

    # 详细结果表格 - 带转向日期
    st.subheader("📋 详细分析结果（含转向日期）")

    df_data = []
    for r in results:
        # 判断结果和颜色
        if r['result_status'] == 'success':
            result_str = f"✅ 成功"
            result_detail = f"于 {r['trigger_date']} 达到目标"
        elif r['result_status'] == 'failure':
            result_str = f"❌ 止损"
            result_detail = f"于 {r['trigger_date']} 触发止损"
        else:
            result_str = f"➖ 持有到期"
            result_detail = f"持有{params['hold_days']}天后平仓"

        df_data.append({
            '股票代码': r['code'],
            '股票名称': r['name'] if r['name'] else '-',
            '所属行业': r['industry'] if r['industry'] else '-',
            '买入日期': r['entry_date'],
            '买入价': f"{r['entry_price']:.2f}",
            '平仓日期': r['exit_date'],
            '平仓价': f"{r['exit_price']:.2f}",
            '持有天数': r['hold_period'],
            '结果': result_str,
            '转向详情': result_detail,
            '最终收益': f"{r['final_return']*100:.1f}%",
            '期间最大涨幅': f"{r['max_gain']*100:.1f}%",
            '期间最大跌幅': f"{r['max_loss']*100:.1f}%",
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, height=400)

    # 按转向类型分类展示
    st.subheader("📊 分类详情")

    tab1, tab2, tab3 = st.tabs(["✅ 成功股票", "❌ 止损股票", "➖ 持有到期"])

    with tab1:
        success_list = [r for r in results if r['result_status'] == 'success']
        if success_list:
            st.write(f"**共 {len(success_list)} 只股票成功达到目标涨幅**")
            for r in success_list:
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.write(f"**{r['code']}** {r['name'] if r['name'] else ''}")
                with col2:
                    st.write(f"于 **{r['trigger_date']}** 达到目标涨幅 **{params['target_pct']*100:.0f}%**")
                with col3:
                    st.write(f"持有 **{r['hold_period']}** 天 | 收益 **{r['final_return']*100:.1f}%**")
        else:
            st.info("没有成功达到目标的股票")

    with tab2:
        failure_list = [r for r in results if r['result_status'] == 'failure']
        if failure_list:
            st.write(f"**共 {len(failure_list)} 只股票触发止损**")
            for r in failure_list:
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.write(f"**{r['code']}** {r['name'] if r['name'] else ''}")
                with col2:
                    st.write(f"于 **{r['trigger_date']}** 触发 **5%** 止损")
                with col3:
                    st.write(f"持有 **{r['hold_period']}** 天 | 亏损 **{r['final_return']*100:.1f}%**")
        else:
            st.info("没有触发止损的股票")

    with tab3:
        holding_list = [r for r in results if r['result_status'] == 'holding']
        if holding_list:
            st.write(f"**共 {len(holding_list)} 只股票持有到期**")
            for r in holding_list:
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.write(f"**{r['code']}** {r['name'] if r['name'] else ''}")
                with col2:
                    st.write(f"持有 **{params['hold_days']}** 天后平仓")
                with col3:
                    profit_loss = "盈利" if r['final_return'] > 0 else "亏损"
                    st.write(f"收益 **{r['final_return']*100:.1f}%** ({profit_loss})")
        else:
            st.info("没有持有到期的股票")

    # 成功率分布图
    st.subheader("📊 成功率分布")

    fig_data = {
        '结果类型': ['✅ 成功', '❌ 止损', '➖ 到期'],
        '数量': [success_count, failure_count, neutral_count],
    }

    fig_df = pd.DataFrame(fig_data)

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(fig_df.set_index('结果类型')['数量'])
    with col2:
        st.write("**统计汇总**")
        summary_df = pd.DataFrame({
            '指标': ['成功率', '止损率', '到期率', '平均收益'],
            '数值': [
                f"{success_rate:.1f}%",
                f"{failure_rate:.1f}%",
                f"{neutral_count/total*100:.1f}%" if total > 0 else "0%",
                f"{avg_final_return:.1f}%"
            ]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
