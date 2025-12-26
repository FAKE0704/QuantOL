"""
认证工具函数
"""

import streamlit as st
from functools import wraps
from src.core.auth.auth_service import AuthService

def check_authentication():
    """检查用户是否已登录"""
    # 简化检查：只检查 current_user 是否存在
    # Token 验证在登录时已完成，无需重复验证
    return 'current_user' in st.session_state and st.session_state.current_user is not None

def require_auth(func):
    """认证装饰器，确保用户已登录"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_authentication():
            st.error("请先登录")
            st.session_state.show_page = 'login'
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """管理员权限装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_authentication():
            st.error("请先登录")
            st.session_state.show_page = 'login'
            st.stop()

        if st.session_state.current_user.get('role') != 'admin':
            st.error("权限不足，需要管理员权限")
            st.stop()

        return func(*args, **kwargs)
    return wrapper

def logout():
    """用户登出"""
    if 'auth_token' in st.session_state:
        auth_service = st.session_state.get('auth_service', AuthService(st.session_state.db))
        auth_service.logout(st.session_state.auth_token)

    # 清除会话状态
    st.session_state.auth_token = None
    st.session_state.current_user = None

    st.success("已成功登出")
    st.rerun()