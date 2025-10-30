import streamlit as st
import pandas as pd

from src.services.theme_manager import ThemeManager

def show_settings_page():
    st.title("系统设置")
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["用户偏好", "API密钥管理", "系统日志", "主题管理"])
    
    with tab1:
        st.subheader("用户偏好设置")
        
        # 主题设置
        theme_manager = ThemeManager()
        current_theme = get_config("current_theme") or "default"
        theme_names = theme_manager.get_all_themes()
        
        theme = st.selectbox(
            "选择主题",
            options=theme_names,
            index=theme_names.index(current_theme) if current_theme in theme_names else 0
        )
        
        # 语言设置
        language = st.selectbox(
            "选择语言",
            options=["简体中文", "English"],
            index=0 if get_config("language") == "zh" else 1
        )
        
        if st.button("保存偏好设置"):
            update_config({
                "current_theme": theme,
                "language": "zh" if language == "简体中文" else "en"
            })
            st.success("偏好设置已保存！")
    
    with tab4:
        st.subheader("主题管理")
        theme_manager = ThemeManager()
        
        # 主题选择器
        current_theme = get_config("current_theme") or "default"
        theme_names = theme_manager.get_all_themes()
        selected_theme = st.selectbox(
            "当前主题",
            options=theme_names,
            index=theme_names.index(current_theme) if current_theme in theme_names else 0
        )
        
        # 主题预览
        theme_config = theme_manager.get_theme(selected_theme)
        st.color_picker("主色", theme_config["primary"], disabled=True)
        st.color_picker("背景色", theme_config["background"], disabled=True)
        
        # 自定义主题编辑器
        st.subheader("自定义主题")
        new_theme_name = st.text_input("主题名称")
        
        if new_theme_name:
            cols = st.columns(2)
            custom_theme = {}
            with cols[0]:
                custom_theme["primary"] = st.color_picker("主色", "#2c7be5")
                custom_theme["background"] = st.color_picker("背景色", "#FFFFFF")
            with cols[1]:
                custom_theme["secondary"] = st.color_picker("辅助色", "#6c757d")
                custom_theme["text"] = st.color_picker("文字色", "#333333")
            
            if st.button("保存主题"):
                theme_manager.save_theme(new_theme_name, custom_theme)
                st.success(f"主题 {new_theme_name} 已保存")
        
        # 主题删除功能
        if len(theme_names) > 1:
            theme_to_delete = st.selectbox(
                "删除主题", 
                options=[t for t in theme_names if t != "default"]
            )
            if st.button("删除选中主题"):
                theme_manager.delete_theme(theme_to_delete)
                st.success(f"已删除 {theme_to_delete} 主题")
    
    with tab2:
        st.subheader("API密钥管理")
        
        # 显示当前API密钥
        api_keys = get_config("api_keys")
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
        # TODO
        # logs = get_system_logs()
        # if logs:
        #     st.text_area("日志内容", logs, height=400)
        # else:
        #     st.info("没有系统日志")

import json
import os
from pathlib import Path

CONFIG_FILE = str(Path(__file__).parent.parent.parent / 'support' / 'config' / 'user_settings.json')

def get_config(key: str):
    """获取配置项"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get(key)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def update_config(updates: dict):
    """更新配置项"""
    try:
        # 读取现有配置
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        # 更新配置
        config.update(updates)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # 保存配置
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {e}")
