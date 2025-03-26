import streamlit as st

def show_navigation():
    """
    显示应用导航栏
    """
    st.sidebar.title("导航")
    page = st.sidebar.radio(
        "选择页面",
        options=["首页", "历史行情", "技术指标", "回测", "交易管理", "系统设置"]
    )
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
            st.experimental_rerun()
    else:
        if st.sidebar.button("登录"):
            st.session_state['logged_in'] = True
            st.experimental_rerun()

def initialize_navigation():
    """
    初始化导航栏
    """
    st.set_page_config(page_title="量化交易系统", layout="wide")
    page = show_navigation()
    show_user_status()
    return page
