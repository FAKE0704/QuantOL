"""
用户登录和注册页面
"""

import streamlit as st
from src.core.auth.auth_service import AuthService

def show_login_page():
    """显示登录页面"""
    st.title("🔐 用户登录")
    st.markdown("---")

    # 获取认证服务
    if 'auth_service' not in st.session_state:
        st.session_state.auth_service = AuthService(st.session_state.db)

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("用户名或邮箱", placeholder="请输入用户名或邮箱")
        with col2:
            password = st.text_input("密码", type="password", placeholder="请输入密码")

        submitted = st.form_submit_button("登录", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("请填写完整的登录信息")
            else:
                with st.spinner("正在验证..."):
                    result, msg = st.session_state.auth_service.login(username, password)

                    if result:
                        # 保存登录状态
                        st.session_state.auth_token = result['token']
                        st.session_state.current_user = result['user']

                        st.success("登录成功！")
                        st.balloons()

                        # 延迟刷新
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")

    # 注册链接
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("没有账号？点击注册", use_container_width=True):
            st.session_state.show_page = 'register'
            st.rerun()

    # 显示注册状态
    auth_service = st.session_state.auth_service
    status = auth_service.get_registration_status()

    st.info(f"""
    📊 **当前系统状态**:
    - 已注册用户: {status['registered']}/{status['max_users']}
    - 剩余名额: {status['remaining']}
    """)

def show_register_page():
    """显示注册页面"""
    st.title("📝 用户注册")
    st.markdown("---")

    # 获取认证服务
    if 'auth_service' not in st.session_state:
        st.session_state.auth_service = AuthService(st.session_state.db)

    # 检查是否还有注册名额
    auth_service = st.session_state.auth_service
    status = auth_service.get_registration_status()

    if status['is_full']:
        st.error("😔 测试名额已满，请等待下一批开放！")

        if st.button("返回登录"):
            st.session_state.show_page = 'login'
            st.rerun()
        return

    with st.form("register_form"):
        st.warning(f"当前剩余名额: **{status['remaining']}**")

        username = st.text_input("用户名", placeholder="请输入用户名", help="用户名将用于登录，请妥善保管")
        email = st.text_input("邮箱", placeholder="请输入邮箱地址", help="邮箱可用于找回密码")

        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("密码", type="password", placeholder="请输入密码", help="密码长度至少6位")
        with col2:
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")

        submitted = st.form_submit_button("注册", use_container_width=True)

        if submitted:
            if not all([username, email, password, confirm_password]):
                st.error("请填写所有必填项")
            elif password != confirm_password:
                st.error("两次输入的密码不一致")
            elif len(password) < 6:
                st.error("密码长度至少6位")
            else:
                with st.spinner("正在注册..."):
                    success, msg = await auth_service.register(username, email, password)

                    if success:
                        st.success(msg)
                        st.info("请使用您的账号登录")

                        # 自动跳转到登录页
                        import time
                        time.sleep(2)
                        st.session_state.show_page = 'login'
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")

    # 返回登录链接
    if st.button("已有账号？点击登录", use_container_width=True):
        st.session_state.show_page = 'login'
        st.rerun()

    # 显示注册条款
    with st.expander("📖 注册须知"):
        st.markdown("""
        **注意事项：**
        1. 本次为内测版本，仅开放100个测试名额
        2. 请妥善保管您的账号信息
        3. 禁止恶意注册或使用
        4. 如有问题请联系管理员

        **管理员联系方式：**
        - 邮箱: admin@quantol.com
        """)

def show_auth_page():
    """显示认证页面（登录或注册）"""
    # 确定显示哪个页面
    page_type = st.session_state.get('show_page', 'login')

    if page_type == 'register':
        show_register_page()
    else:
        show_login_page()