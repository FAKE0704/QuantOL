import streamlit as st
import pandas as pd
import plotly.express as px
from ..core.backtest import run_backtest

def show_backtesting_page():
    st.title("策略回测")
    
    # 股票选择
    stock_code = st.text_input("输入股票代码", value="600519")
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期")
    with col2:
        end_date = st.date_input("结束日期")
    
    # 策略选择
    strategy = st.selectbox(
        "选择回测策略",
        options=["移动平均线交叉", "MACD交叉", "RSI超买超卖"]
    )
    
    # 策略参数设置
    if strategy == "移动平均线交叉":
        short_period = st.slider("短期均线周期", min_value=5, max_value=30, value=10)
        long_period = st.slider("长期均线周期", min_value=20, max_value=100, value=50)
    elif strategy == "MACD交叉":
        fast_period = st.slider("快速EMA周期", min_value=5, max_value=26, value=12)
        slow_period = st.slider("慢速EMA周期", min_value=10, max_value=50, value=26)
        signal_period = st.slider("信号线周期", min_value=5, max_value=20, value=9)
    elif strategy == "RSI超买超卖":
        period = st.slider("RSI周期", min_value=5, max_value=30, value=14)
        overbought = st.slider("超买阈值", min_value=60, max_value=90, value=70)
        oversold = st.slider("超卖阈值", min_value=10, max_value=40, value=30)
    
    # 回测参数
    initial_capital = st.number_input("初始资金(元)", min_value=10000, value=100000)
    commission_rate = st.number_input("交易佣金(%)", min_value=0.0, max_value=1.0, value=0.03)
    
    if st.button("开始回测"):
        # 准备回测参数
        params = {
            "strategy": strategy,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "commission_rate": commission_rate
        }
        
        if strategy == "移动平均线交叉":
            params.update({
                "short_period": short_period,
                "long_period": long_period
            })
        elif strategy == "MACD交叉":
            params.update({
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period
            })
        elif strategy == "RSI超买超卖":
            params.update({
                "period": period,
                "overbought": overbought,
                "oversold": oversold
            })
        
        # 运行回测
        result = run_backtest(stock_code, **params)
        
        if result is not None:
            st.success("回测完成！")
            
            # 显示回测结果
            st.subheader("回测结果")
            st.dataframe(result["summary"])
            
            # 绘制净值曲线
            st.subheader("净值曲线")
            fig = px.line(result["equity_curve"], x='date', y='equity', title="净值曲线")
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示交易记录
            st.subheader("交易记录")
            st.dataframe(result["trades"])
        else:
            st.error("回测失败，请检查输入参数")
