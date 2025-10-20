import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from frontend.navigation import initialize_navigation
from frontend.history import show_history_page
from frontend.indicators import show_indicators_page
from frontend.backtesting import show_backtesting_page
from frontend.trading import show_trading_page
from frontend.settings import show_settings_page
from frontend.global_market import show_global_market
from frontend.market_research import show_market_research_page

import streamlit as st
from core.data.database import get_db_manager
from services.stock_search import StockSearchService
import asyncio, platform

async def init_global_services():
    """初始化全局服务并存储在session_state"""
    if "_loop" not in st.session_state:
        st.session_state._loop = None

    # 初始化db_manager对象
    if 'db' not in st.session_state:
        db_manager = get_db_manager()
        await db_manager.initialize()
        st.session_state.db  = db_manager
        st.session_state._loop = st.session_state.db._loop
    if 'search_service' not in st.session_state:
        st.session_state.search_service = StockSearchService(st.session_state.db)
        

def show_home_page():
    st.title("欢迎使用智能量化平台")
    st.write("请从左侧导航栏选择功能")

async def main():
    # 初始化全局服务
    await init_global_services()
    
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
    elif page == "市场研究":
        await show_market_research_page()
    elif page == "全球市场资金分布":
        await show_global_market()
    
  

    # print("### main循环结束 ####")

if __name__ == "__main__":
    import asyncio
    if "_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
    else:
        loop = st.session_state._loop
    loop.run_until_complete(main())
