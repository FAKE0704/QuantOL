import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.frontend.navigation import initialize_navigation
from src.frontend.history import show_history_page
from src.frontend.indicators import show_indicators_page
from src.frontend.backtesting import show_backtesting_page
from src.frontend.trading import show_trading_page
from src.frontend.settings import show_settings_page
from src.frontend.global_market import show_global_market
from src.frontend.market_research import show_market_research_page
from src.frontend.system_settings import show_system_settings_page
from src.frontend.auth.login_page import show_auth_page
from src.frontend.auth.admin_panel import show_admin_panel
from src.frontend.auth.auth_utils import check_authentication, require_auth

import streamlit as st
from src.core.data.database_factory import get_db_adapter
from src.services.stock_search import StockSearchService
import asyncio, platform

async def init_global_services():
    """初始化全局服务并存储在session_state"""
    if "_loop" not in st.session_state:
        st.session_state._loop = None

    # 初始化数据库适配器
    if 'db' not in st.session_state:
        # 使用工厂函数获取数据库适配器
        db_adapter = get_db_adapter()

        # 如果是SQLite适配器，传递session_state引用
        if hasattr(db_adapter, '_session_state_ref'):
            db_adapter._session_state_ref = st.session_state

        await db_adapter.initialize()
        st.session_state.db = db_adapter

        # 如果是PostgreSQL，需要获取事件循环
        import os
        if os.getenv('DATABASE_TYPE', 'postgresql') in ['postgresql', 'postgres']:
            if hasattr(st.session_state.db, '_loop'):
                st.session_state._loop = st.session_state.db._loop
            else:
                # 创建新的事件循环
                st.session_state._loop = asyncio.get_event_loop()

    if 'search_service' not in st.session_state:
        st.session_state.search_service = StockSearchService(st.session_state.db)

    # 初始化认证服务（但不立即初始化，让需要时再初始化）
    # 这里是为了避免在用户表创建前就初始化认证服务
        

def show_home_page():
    st.title("欢迎使用智能量化平台")

    # 检查登录状态
    if check_authentication():
        user = st.session_state.current_user
        st.success(f"👋 欢迎回来，{user.get('username', '用户')}！")

        st.markdown("---")
        st.write("请从左侧导航栏选择功能")
    else:
        st.warning("请先登录以使用完整功能")

        # 显示注册状态
        try:
            auth_service = st.session_state.get('auth_service')
            if auth_service:
                import asyncio
                status = asyncio.run(auth_service.get_registration_status())

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col2:
                    st.metric("测试名额", f"{status['registered']}/{status['max_users']}")

                if not status['is_full']:
                    st.info(f"🎉 还有 {status['remaining']} 个名额，快来注册吧！")
                    if st.button("立即注册", use_container_width=True):
                        st.session_state.show_page = 'register'
                        st.rerun()
                else:
                    st.warning("😔 测试名额已满，请等待下一批开放")
        except:
            pass

async def main():
    # 初始化全局服务
    await init_global_services()

    # 检查是否需要显示登录/注册页面
    if st.session_state.get('show_page') in ['login', 'register']:
        show_auth_page()
        return

    page = initialize_navigation()

    if page == "首页":
        show_home_page()
    elif page == "历史行情":
        # 历史行情需要登录
        if check_authentication():
            await show_history_page()
        else:
            st.error("请先登录")
            st.session_state.show_page = 'login'
    elif page == "技术指标":
        show_indicators_page()
    elif page == "回测":
        # 回测需要登录
        if check_authentication():
            await show_backtesting_page()
        else:
            st.error("请先登录")
            st.session_state.show_page = 'login'
    elif page == "交易管理":
        show_trading_page()
    elif page == "系统设置":
        # 系统设置需要登录
        if check_authentication():
            await show_system_settings_page()
        else:
            st.error("请先登录")
            st.session_state.show_page = 'login'
    elif page == "市场研究":
        await show_market_research_page()
    elif page == "全球市场资金分布":
        await show_global_market()
    elif page == "用户管理":
        # 用户管理需要管理员权限
        if check_authentication():
            if st.session_state.current_user.get('role') == 'admin':
                await show_admin_panel()
            else:
                st.error("权限不足，需要管理员权限")
        else:
            st.error("请先登录")
            st.session_state.show_page = 'login'



    # print("### main循环结束 ####")

if __name__ == "__main__":
    import asyncio

    # 获取或创建事件循环
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 执行主程序
    loop.run_until_complete(main())
