import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 必须在第一个st调用之前导入并设置页面配置
import streamlit as st

# 检查用户是否已登录（在session_state中）
# 注意：这是简单的token检查，完整的验证需要数据库
is_logged_in = 'auth_token' in st.session_state or 'current_user' in st.session_state

# 根据登录状态设置页面配置
if is_logged_in:
    st.set_page_config(
        page_icon="🧊",
        page_title="量化交易系统",
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_icon="🔐",
        page_title="QuantOL - 用户登录",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

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
from src.frontend.auth.auth_utils import check_authentication, require_auth, logout

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

def show_user_menu():
    """显示右上角用户头像和下拉菜单 - 使用 st.popover 原生组件"""
    user = st.session_state.current_user
    username = user.get('username', 'U')
    email = user.get('email', '')

    # 获取用户名首字母作为头像
    initial = username[0].upper() if username else 'U'

    # 添加自定义样式
    st.markdown("""
    <style>
        /* 自定义 popover 按钮样式为 avatar */
        div[data-testid="stPopover"] > button {
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
            height: 42px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 2px solid white !important;
            box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3) !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stPopover"] > button span {
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
        }

        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4) !important;
        }

        /* 将 popover 放置在右上角，限制容器宽度 */
        div[data-testid="stPopover"] {
            position: fixed !important;
            top: 1rem !important;
            right: calc(1rem + 40px) !important;
            z-index: 999999 !important;
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
        }

        /* 自定义 popover 内容样式 */
        [data-testid="stPopoverContent"] {
            border-radius: 12px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
            border: 1px solid #f0f0f0 !important;
        }

        /* 菜单按钮样式 */
        .menu-button {
            width: 100% !important;
            text-align: left !important;
            border: none !important;
            background: transparent !important;
            padding: 12px 16px !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            color: #595959 !important;
            font-size: 14px !important;
        }

        .menu-button:hover {
            background: #f5f5f5 !important;
        }

        .menu-button.danger {
            color: #ff4d4f !important;
        }

        .menu-button.danger:hover {
            background: #fff1f0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 使用 st.popover 创建用户菜单
    with st.popover(initial, use_container_width=False):
        # 用户信息
        st.markdown(f"""
        <div style="padding: 16px; border-bottom: 1px solid #f0f0f0; margin-bottom: 8px;">
            <div style="font-weight: 600; font-size: 15px; color: #262626;">{username}</div>
            <div style="font-size: 13px; color: #8c8c8c; margin-top: 2px;">{email}</div>
        </div>
        """, unsafe_allow_html=True)

        # 菜单项
        if st.button("👤 Profile", key="menu_profile", use_container_width=True, help="查看个人资料"):
            st.info("个人资料页面开发中...")

        if st.button("⚙️ Settings", key="menu_settings", use_container_width=True, help="用户设置"):
            st.info("用户设置（悬浮窗口）开发中...")

        if st.button("⭐ Upgrade", key="menu_upgrade", use_container_width=True, help="升级账户"):
            st.info("升级功能开发中...")

        st.markdown('<div style="height: 1px; background: #f0f0f0; margin: 8px 0;"></div>', unsafe_allow_html=True)

        if st.button("🚪 Sign Out", key="menu_signout", use_container_width=True, type="primary"):
            logout()
            st.rerun()

async def main():
    # 初始化全局服务
    await init_global_services()

    # 检查是否需要显示登录/注册页面
    # 如果用户未登录，只显示登录页面，不显示任何其他功能
    if not check_authentication():
        await show_auth_page()
        return

    # 已登录用户，初始化导航栏并显示功能
    page = initialize_navigation()

    # 显示用户头像菜单
    show_user_menu()

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
