import streamlit as st
import pandas as pd
from ..core.execution import get_orders, get_positions, get_trade_history

def show_trading_page():
    st.title("交易管理")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["订单管理", "持仓管理", "交易记录"])
    
    with tab1:
        st.subheader("订单管理")
        orders = get_orders()
        if orders is not None:
            st.dataframe(orders)
        else:
            st.error("获取订单数据失败")
        
        # 新订单功能
        st.subheader("新建订单")
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("股票代码")
            quantity = st.number_input("数量", min_value=100, step=100)
        with col2:
            order_type = st.selectbox("订单类型", ["市价单", "限价单"])
            if order_type == "限价单":
                price = st.number_input("价格", min_value=0.01)
            else:
                price = None
        
        if st.button("提交订单"):
            if symbol and quantity > 0:
                # TODO: 实现提交订单逻辑
                st.success("订单提交成功！")
            else:
                st.error("请填写完整的订单信息")
    
    with tab2:
        st.subheader("持仓管理")
        positions = get_positions()
        if positions is not None:
            st.dataframe(positions)
        else:
            st.error("获取持仓数据失败")
    
    with tab3:
        st.subheader("交易记录")
        trades = get_trade_history()
        if trades is not None:
            st.dataframe(trades)
        else:
            st.error("获取交易记录失败")
