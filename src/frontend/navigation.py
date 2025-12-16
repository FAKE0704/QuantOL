import streamlit as st
from src.frontend.auth.auth_utils import check_authentication, logout

def show_navigation():
    """
    显示应用导航栏
    """
    # 样式注入
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { padding: 5px !important; }
        .stRadio > div { padding: 10px 0; }
        .stButton > button { width: 100%; margin-top: 10px; }
        .disabled-option {
            color: #ccc !important;
            opacity: 0.6 !important;
            pointer-events: none !important;
        }
        .unavailable-option {
            color: #888 !important;
            font-style: italic !important;
        }
        [data-testid="stSelectbox"] > div > div {
            background-color: transparent;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.title("🚀 QuantOL")
        st.markdown("---")

        # 检查登录状态
        is_authenticated = check_authentication()

        if is_authenticated:
            # 显示用户信息
            user = st.session_state.current_user
            st.success(f"👤 {user.get('username', '用户')}")

            if user.get('role') == 'admin':
                st.info("🔧 管理员")

        # 创建导航菜单
        if is_authenticated:
            # 已登录用户的菜单
            available_options = ["首页", "历史行情", "回测"]

            # 管理员额外菜单
            if st.session_state.current_user.get('role') == 'admin':
                available_options.append("系统设置")
                available_options.append("用户管理")
        else:
            # 未登录用户只能看到首页和系统设置
            available_options = ["首页", "系统设置"]

        unavailable_options = ["技术指标 (开发中)", "交易管理 (开发中)", "全球市场资金分布 (开发中)", "市场研究 (开发中)"]

        # 显示可用功能
        st.markdown("**可用功能**")
        page = st.radio(
            "功能选择",
            options=available_options,
            index=0,
            help="选择要进入的功能模块"
        )

        # 显示不可用功能
        st.markdown("**即将推出**")
        for option in unavailable_options:
            st.markdown(f"• {option}")

        st.markdown("---")

        # 登录/登出按钮
        if is_authenticated:
            if st.button("🚪 退出登录", use_container_width=True):
                logout()
        else:
            if st.button("🔐 登录/注册", use_container_width=True):
                st.session_state.show_page = 'login'
                st.rerun()

        st.markdown("---")

        # 显示注册状态（未登录时）
        if not is_authenticated:
            try:
                auth_service = st.session_state.auth_service
                import asyncio
                status = asyncio.run(auth_service.get_registration_status())
                st.info(f"📊 测试名额: {status['registered']}/{status['max_users']}")
            except:
                pass

        # 系统状态显示
        try:
            from src.frontend.system_settings import show_database_status_widget
            show_database_status_widget()
        except:
            pass

        st.markdown("---")
        if st.button("清空缓存", help="重置所有配置"):
            st.cache_data.clear()
            st.success("缓存已清空")

    return page

def show_user_status():
    """
    显示用户登录状态
    """
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if st.session_state['logged_in']:
        st.sidebar.success(f"欢迎, {st.session_state.get('username', '用户')}")
        if st.sidebar.button("退出登录"):
            st.session_state['logged_in'] = False
            st.rerun()
    else:
        if st.sidebar.button("登录"):
            st.session_state['logged_in'] = True
            st.rerun()

def initialize_navigation():
    """
    初始化导航栏
    """
    st.set_page_config(
        page_icon="🧊",
        page_title="量化交易系统",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://www.extremelycoolapp.com/help',
            'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': "# This is a header. This is an *extremely* cool app!"
        }
    )
    page = show_navigation()
    show_user_status()
    return page
