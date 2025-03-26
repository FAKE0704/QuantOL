import streamlit as st
import pandas as pd
from ..core.config import get_config, update_config, get_system_logs

def show_settings_page():
    st.title("系统设置")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["用户偏好", "API密钥管理", "系统日志"])
    
    with tab1:
        st.subheader("用户偏好设置")
        
        # 主题设置
        theme = st.selectbox(
            "选择主题",
            options=["浅色", "深色"],
            index=0 if get_config("theme") == "light" else 1
        )
        
        # 语言设置
        language = st.selectbox(
            "选择语言",
            options=["简体中文", "English"],
            index=0 if get_config("language") == "zh" else 1
        )
        
        if st.button("保存偏好设置"):
            update_config({
                "theme": "light" if theme == "浅色" else "dark",
                "language": "zh" if language == "简体中文" else "en"
            })
            st.success("偏好设置已保存！")
    
    with tab2:
        st.subheader("API密钥管理")
        
        # 显示当前API密钥
        api_keys = get_config("api_keys", {})
        if api_keys:
            st.dataframe(pd.DataFrame.from_dict(api_keys, orient='index'))
        else:
            st.warning("未配置任何API密钥")
        
        # 添加新API密钥
        st.subheader("添加新API密钥")
        col1, col2 = st.columns(2)
        with col1:
            api_name = st.text_input("API名称")
            api_key = st.text_input("API密钥")
        with col2:
            api_secret = st.text_input("API密钥密钥", type="password")
        
        if st.button("保存API密钥"):
            if api_name and api_key:
                api_keys[api_name] = {
                    "key": api_key,
                    "secret": api_secret
                }
                update_config({"api_keys": api_keys})
                st.success("API密钥已保存！")
            else:
                st.error("请填写完整的API密钥信息")
    
    with tab3:
        st.subheader("系统日志")
        logs = get_system_logs()
        if logs:
            st.text_area("日志内容", logs, height=400)
        else:
            st.info("没有系统日志")
