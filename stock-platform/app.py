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
from strategies import SmaCross, RsiStrategy, MacdStrategy

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


def main():
    """主函数"""
    init_session_state()
    render_header()
    
    # 获取侧边栏参数
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
            render_trades_table(st.session_state.backtest_results)
            
    except Exception as e:
        st.error(f"❌ 发生错误: {e}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
