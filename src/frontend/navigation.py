import streamlit as st

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
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.title("🚀 智能量化平台")
        st.markdown("---")
        
        page = st.radio(
            "导航菜单",
            options=["首页", "历史行情", "技术指标", "回测", "交易管理", "系统设置"],
            index=0,
            help="选择要进入的功能模块"
        )
        
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
    st.set_page_config(page_title="量化交易系统", layout="wide")
    page = show_navigation()
    show_user_status()
    return page
