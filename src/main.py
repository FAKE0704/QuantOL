from frontend.navigation import initialize_navigation
from frontend.history import show_history_page
from frontend.indicators import show_indicators_page
from frontend.backtesting import show_backtesting_page
from frontend.trading import show_trading_page
from frontend.settings import show_settings_page
import streamlit as st
from core.data.database import DatabaseManager
from services.stock_search import StockSearchService
import asyncio

def init_global_services():
    """初始化全局服务并存储在session_state"""
    
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
        st.session_state.db.initialize()  # 假设有连接方法
        
    if 'search_service' not in st.session_state:
        st.session_state.search_service = StockSearchService()
        # 异步初始化需要特殊处理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(st.session_state.search_service.async_init())

def show_home_page():
    st.title("欢迎使用量化交易系统")
    st.write("请从左侧导航栏选择功能")

async def main():
    # 初始化全局服务
    init_global_services()
    
    page = initialize_navigation()
    
    if page == "首页":
        show_home_page()
    elif page == "历史行情":
        await show_history_page()
    elif page == "技术指标":
        show_indicators_page()
    elif page == "回测":
        await show_backtesting_page()
    elif page == "交易管理":
        show_trading_page()
    elif page == "系统设置":
        show_settings_page()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
