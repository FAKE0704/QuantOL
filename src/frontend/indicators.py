import streamlit as st
import pandas as pd
import plotly.express as px
from ..core.data import get_technical_indicators

def show_indicators_page():
    st.title("技术指标分析")
    
    # 股票选择
    stock_code = st.text_input("输入股票代码", value="600519")
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期")
    with col2:
        end_date = st.date_input("结束日期")
    
    # 指标选择
    indicator = st.selectbox(
        "选择技术指标",
        options=["MA", "MACD", "RSI", "BOLL"]
    )
    
    # 参数设置
    if indicator == "MA":
        period = st.slider("移动平均周期", min_value=5, max_value=60, value=20)
    elif indicator == "MACD":
        fast_period = st.slider("快速EMA周期", min_value=5, max_value=26, value=12)
        slow_period = st.slider("慢速EMA周期", min_value=10, max_value=50, value=26)
        signal_period = st.slider("信号线周期", min_value=5, max_value=20, value=9)
    elif indicator == "RSI":
        period = st.slider("RSI周期", min_value=5, max_value=30, value=14)
    elif indicator == "BOLL":
        period = st.slider("布林线周期", min_value=10, max_value=50, value=20)
        std_dev = st.slider("标准差倍数", min_value=1, max_value=3, value=2)
    
    if st.button("计算技术指标"):
        # 获取技术指标数据
        params = {
            "indicator": indicator,
            "start_date": start_date,
            "end_date": end_date
        }
        
        if indicator == "MA":
            params["period"] = period
        elif indicator == "MACD":
            params.update({
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period
            })
        elif indicator == "RSI":
            params["period"] = period
        elif indicator == "BOLL":
            params.update({
                "period": period,
                "std_dev": std_dev
            })
        
        data = get_technical_indicators(stock_code, **params)
        
        if data is not None:
            st.success("指标计算成功！")
            
            # 显示数据表格
            st.subheader("技术指标数据")
            st.dataframe(data)
            
            # 绘制指标图表
            st.subheader(f"{indicator} 指标图")
            fig = px.line(data, x='date', y=data.columns[1:], title=f"{stock_code} {indicator} 指标")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("计算指标失败，请检查输入参数")
