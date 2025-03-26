import streamlit as st
import pandas as pd
import plotly.express as px
from ..core.data import get_historical_data

def show_history_page():
    st.title("历史行情")
    
    # 股票选择
    stock_code = st.text_input("输入股票代码", value="600519")
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期")
    with col2:
        end_date = st.date_input("结束日期")
    
    if st.button("查询历史数据"):
        # 获取历史数据
        data = get_historical_data(stock_code, start_date, end_date)
        
        if data is not None:
            st.success("数据获取成功！")
            
            # 显示数据表格
            st.subheader("历史数据")
            st.dataframe(data)
            
            # 绘制K线图
            st.subheader("K线图")
            fig = px.candlestick(
                data,
                x='date',
                open='open',
                high='high',
                low='low',
                close='close',
                title=f"{stock_code} K线图"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("获取数据失败，请检查股票代码和日期范围")
