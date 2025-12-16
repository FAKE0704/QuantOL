"""
管理员面板
用于查看用户注册情况和系统状态
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.core.auth.auth_service import AuthService
from src.frontend.auth.auth_utils import require_admin

async def show_admin_panel():
    """显示管理员面板"""
    require_admin(lambda: None)()  # 检查管理员权限

    st.title("🔧 管理员面板")
    st.markdown("---")

    # 获取认证服务
    if 'auth_service' not in st.session_state:
        st.session_state.auth_service = AuthService(st.session_state.db)

    auth_service = st.session_state.auth_service

    # 系统状态概览
    st.subheader("📊 系统状态")
    status = await auth_service.get_registration_status()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("最大用户数", status['max_users'])
    with col2:
        st.metric("已注册用户", status['registered'])
    with col3:
        st.metric("剩余名额", status['remaining'])
    with col4:
        usage_rate = (status['registered'] / status['max_users'] * 100) if status['max_users'] > 0 else 0
        st.metric("使用率", f"{usage_rate:.1f}%")

    # 进度条
    st.progress(status['registered'] / status['max_users'])

    st.markdown("---")

    # 用户列表
    st.subheader("👥 用户列表")

    # 获取所有用户
    users = await st.session_state.db.fetch_all("""
        SELECT
            id,
            username,
            email,
            role,
            status,
            created_at,
            last_login
        FROM users
        ORDER BY created_at DESC
    """)

    if users:
        # 转换为DataFrame
        df = pd.DataFrame(users)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')

        # 显示数据表格
        st.dataframe(df, use_container_width=True)

        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            active_users = sum(1 for u in users if u['last_login'])
            st.metric("活跃用户", active_users)
        with col2:
            admin_users = sum(1 for u in users if u['role'] == 'admin')
            st.metric("管理员", admin_users)
        with col3:
            today_users = sum(1 for u in users
                            if u['created_at'].date() == datetime.now().date())
            st.metric("今日注册", today_users)

    else:
        st.info("暂无用户数据")

    st.markdown("---")

    # 操作日志
    st.subheader("📋 操作日志")

    # 获取最近的操作日志
    logs = await st.session_state.db.fetch_all("""
        SELECT
            ol.operation_type,
            ol.operation_detail,
            ol.created_at,
            u.username
        FROM user_operation_logs ol
        LEFT JOIN users u ON ol.user_id = u.id
        ORDER BY ol.created_at DESC
        LIMIT 100
    """)

    if logs:
        for log in logs:
            with st.expander(f"{log['created_at']} - {log['operation_type']}"):
                st.write(f"用户: {log['username'] or '系统'}")
                st.write(f"详情: {log['operation_detail'] or '无'}")
    else:
        st.info("暂无操作日志")

    # 导出数据按钮
    if st.button("导出用户数据"):
        if users:
            csv = df.to_csv(index=False)
            st.download_button(
                label="下载用户数据 CSV",
                data=csv,
                file_name=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )