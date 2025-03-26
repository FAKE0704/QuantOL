from .navigation import initialize_navigation
from .history import show_history_page
from .indicators import show_indicators_page
from .backtesting import show_backtesting_page
from .trading import show_trading_page
from .settings import show_settings_page
import streamlit as st

def show_home_page():
    st.title("欢迎使用量化交易系统")
    st.write("请从左侧导航栏选择功能")

def main():
    page = initialize_navigation()
    
    if page == "首页":
        show_home_page()
    elif page == "历史行情":
        show_history_page()
    elif page == "技术指标":
        show_indicators_page()
    elif page == "回测":
        show_backtesting_page()
    elif page == "交易管理":
        show_trading_page()
    elif page == "系统设置":
        show_settings_page()

if __name__ == "__main__":
    main()
