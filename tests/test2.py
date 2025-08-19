import streamlit as st


# 初始化数值保持类型一致
if 'start_year' not in st.session_state:
    st.session_state.start_year = 2020  # 改为int类型，与selectbox选项匹配

# 创建回调函数处理状态更新
def update_year():
    st.session_state.start_year = st.session_state.widget_year  # 通过组件key获取新值

# 组件绑定与回调分离
start_year = st.selectbox(
    "选择开始年份",
    options=range(2000, 2030),
    index=20,
    key='widget_year',  # 定义独立组件key
    on_change=update_year  # 绑定变更回调
)


# 显示当前年份（持久化展示）
if 'start_year' in st.session_state:
    if st.button('选好了年份', key='run_btn'):
        # 使用session_state获取最新值
        start_month = st.selectbox(
            "选择开始月份",
            options=range(2000, 2030),
            index=20,
            key='widget_month',  # 定义独立组件key
        )