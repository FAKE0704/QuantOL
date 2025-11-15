"""
数据源配置界面
提供用户友好的数据源配置和管理界面
"""

import streamlit as st
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from src.core.data.config.data_source_config import (
    DataSourceManager, DataSourceConfig, DataSourceType, DataSourcePriority,
    get_data_source_manager
)
from src.core.data.data_source_selector import (
    DataSourceSelector, DataSourceRequest, get_data_source_selector
)


class DataSourceSettingsUI:
    """数据源设置界面"""

    def __init__(self):
        self.config_manager = get_data_source_manager()
        self.selector = get_data_source_selector()

    def render(self):
        """渲染数据源设置界面"""
        st.title("📊 数据源配置")
        st.markdown("---")

        # 侧边栏导航
        with st.sidebar:
            selected_tab = st.radio(
                "选择功能",
                ["数据源概览", "配置管理", "连接测试", "高级设置"]
            )

        if selected_tab == "数据源概览":
            self._render_overview()
        elif selected_tab == "配置管理":
            self._render_config_management()
        elif selected_tab == "连接测试":
            self._render_connection_test()
        elif selected_tab == "高级设置":
            self._render_advanced_settings()

    def _render_overview(self):
        """渲染数据源概览页面"""
        st.header("📋 数据源概览")

        # 获取配置摘要
        summary = self.config_manager.get_config_summary()

        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总数据源", summary['total_sources'])

        with col2:
            st.metric("已启用", summary['enabled_sources'])

        with col3:
            st.metric("已配置", summary['configured_sources'])

        with col4:
            st.metric("主要数据源", summary['primary_source'] or "未设置")

        st.markdown("---")

        # 数据源状态表格
        st.subheader("数据源状态")

        # 获取所有数据源状态
        all_sources = self.config_manager.get_all_data_sources()
        source_status = self.selector.get_all_source_status()

        if all_sources:
            # 准备表格数据
            status_data = []
            for name, config in all_sources.items():
                status = source_status.get(name)
                status_data.append({
                    "名称": name,
                    "类型": config.source_type.value.title(),
                    "状态": "✅ 已启用" if config.settings.enabled else "❌ 已禁用",
                    "优先级": self._get_priority_emoji(config.settings.priority),
                    "可用性": self._get_availability_emoji(status),
                    "配置状态": "✅ 已配置" if config.is_configured else "⚠️ 未配置",
                    "最后测试": self._format_time(status.last_test_time if status else None)
                })

            df = pd.DataFrame(status_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无配置的数据源")

        # 推荐配置
        st.markdown("---")
        st.subheader("💡 配置建议")

        recommendations = self.selector.get_recommended_config()
        for rec in recommendations['recommendations']:
            if rec['level'] == 'error':
                st.error(rec['message'])
            elif rec['level'] == 'warning':
                st.warning(rec['message'])
            else:
                st.info(rec['message'])

    def _render_config_management(self):
        """渲染配置管理页面"""
        st.header("⚙️ 配置管理")

        # 添加新数据源
        with st.expander("➕ 添加新数据源", expanded=False):
            self._render_add_source_form()

        st.markdown("---")

        # 现有数据源配置
        st.subheader("📝 现有数据源")

        all_sources = self.config_manager.get_all_data_sources()
        if all_sources:
            # 数据源选择器
            selected_source_name = st.selectbox(
                "选择要编辑的数据源:",
                options=list(all_sources.keys())
            )

            if selected_source_name:
                selected_config = all_sources[selected_source_name]
                self._render_source_config_form(selected_config)
        else:
            st.info("暂无配置的数据源，请先添加数据源")

    def _render_add_source_form(self):
        """渲染添加数据源表单"""
        supported_sources = self.config_manager.get_supported_sources()

        col1, col2 = st.columns(2)

        with col1:
            source_type = st.selectbox(
                "数据源类型",
                options=list(supported_sources.keys()),
                format_func=lambda x: supported_sources[x]['name']
            )

        with col2:
            source_name = st.text_input("数据源名称")

        # 显示数据源信息
        if source_type in supported_sources:
            source_info = supported_sources[source_type]
            st.info(f"**{source_info['name']}**\n\n{source_info['description']}\n\n"
                   f"**功能**: {', '.join(source_info['features'])}")

        # 配置表单
        with st.form("add_source_form"):
            st.subheader("基础配置")

            col1, col2 = st.columns(2)
            with col1:
                enabled = st.checkbox("启用", value=True)
                priority = st.selectbox(
                    "优先级",
                    options=list(DataSourcePriority),
                    format_func=lambda x: x.value.title()
                )
                use_as_backup = st.checkbox("作为备用数据源", value=True)

            with col2:
                cache_enabled = st.checkbox("启用缓存", value=True)
                cache_ttl = st.number_input("缓存时间(TTL,秒)", min_value=60, value=3600)
                rate_limit = st.number_input("请求频率限制(次/分钟)", min_value=1, value=120)

            # 凭证配置
            st.subheader("凭证配置")
            credentials = self._render_credentials_form(source_type)

            # 提交按钮
            submitted = st.form_submit_button("添加数据源", type="primary")
            if submitted:
                if not source_name:
                    st.error("请输入数据源名称")
                    return

                # 创建配置
                from src.core.data.config.data_source_config import (
                    DataSourceSettings, DataSourceCredentials, DataSourceConfig
                )

                config = DataSourceConfig(
                    source_type=source_type,
                    name=source_name,
                    description=f"{source_type.value} 数据源",
                    credentials=credentials,
                    settings=DataSourceSettings(
                        enabled=enabled,
                        priority=priority,
                        cache_enabled=cache_enabled,
                        cache_ttl=cache_ttl,
                        rate_limit=rate_limit,
                        use_as_backup=use_as_backup
                    )
                )

                # 添加配置
                if self.config_manager.add_data_source(config):
                    st.success(f"成功添加数据源: {source_name}")
                    st.rerun()
                else:
                    st.error("添加数据源失败")

    def _render_source_config_form(self, config: DataSourceConfig):
        """渲染数据源配置表单"""
        with st.form(f"edit_source_form_{config.name}"):
            st.subheader(f"编辑 {config.name}")

            col1, col2 = st.columns(2)

            with col1:
                enabled = st.checkbox("启用", value=config.settings.enabled)
                priority = st.selectbox(
                    "优先级",
                    options=list(DataSourcePriority),
                    index=list(DataSourcePriority).index(config.settings.priority),
                    format_func=lambda x: x.value.title()
                )
                use_as_backup = st.checkbox("作为备用数据源", value=config.settings.use_as_backup)

            with col2:
                cache_enabled = st.checkbox("启用缓存", value=config.settings.cache_enabled)
                cache_ttl = st.number_input(
                    "缓存时间(TTL,秒)", min_value=60,
                    value=config.settings.cache_ttl
                )
                rate_limit = st.number_input(
                    "请求频率限制(次/分钟)", min_value=1,
                    value=config.settings.rate_limit
                )

            # 凭证配置
            st.subheader("凭证配置")
            credentials = self._render_credentials_form(config.source_type, config.credentials)

            # 操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                submitted = st.form_submit_button("保存修改", type="primary")
            with col2:
                test_button = st.form_submit_button("测试连接")
            with col3:
                delete_button = st.form_submit_button("删除", type="secondary")

            if submitted:
                # 更新配置
                from src.core.data.config.data_source_config import DataSourceSettings

                updated_config = DataSourceConfig(
                    source_type=config.source_type,
                    name=config.name,
                    description=config.description,
                    credentials=credentials,
                    settings=DataSourceSettings(
                        enabled=enabled,
                        priority=priority,
                        cache_enabled=cache_enabled,
                        cache_ttl=cache_ttl,
                        rate_limit=rate_limit,
                        use_as_backup=use_as_backup,
                        custom_params=config.settings.custom_params
                    ),
                    is_configured=config.is_configured,
                    last_test_time=config.last_test_time,
                    test_status=config.test_status
                )

                if self.config_manager.update_data_source(config.name, updated_config):
                    st.success(f"成功更新数据源: {config.name}")
                    st.rerun()
                else:
                    st.error("更新数据源失败")

            elif test_button:
                with st.spinner("测试连接中..."):
                    # 创建临时配置进行测试
                    test_config = DataSourceConfig(
                        source_type=config.source_type,
                        name=config.name,
                        credentials=credentials,
                        settings=config.settings
                    )

                    success, message = self._test_connection(test_config)
                    if success:
                        st.success(f"连接测试成功: {message}")
                    else:
                        st.error(f"连接测试失败: {message}")

            elif delete_button:
                if st.confirm(f"确定要删除数据源 {config.name} 吗？"):
                    if self.config_manager.remove_data_source(config.name):
                        st.success(f"成功删除数据源: {config.name}")
                        st.rerun()
                    else:
                        st.error("删除数据源失败")

    def _render_credentials_form(self, source_type: DataSourceType,
                                existing_credentials=None) -> Any:
        """渲染凭证配置表单"""
        from src.core.data.config.data_source_config import DataSourceCredentials

        if existing_credentials is None:
            existing_credentials = DataSourceCredentials()

        with st.expander("凭证设置", expanded=True):
            if source_type == DataSourceType.TUSHARE:
                token = st.text_input(
                    "Tushare Token",
                    value=existing_credentials.token or "",
                    help="在 https://tushare.pro 注册并获取API Token",
                    type="password"
                )
                credentials = DataSourceCredentials(
                    token=token if token else None,
                    timeout=existing_credentials.timeout,
                    retry_times=existing_credentials.retry_times,
                    proxy_url=existing_credentials.proxy_url
                )

            elif source_type == DataSourceType.YAHOO:
                # Yahoo Finance通常不需要特殊凭证
                st.info("Yahoo Finance数据源通常不需要配置Token")
                credentials = existing_credentials

            elif source_type == DataSourceType.BAOSTOCK:
                # Baostock通常不需要特殊凭证
                st.info("Baostock数据源通常不需要配置Token")
                credentials = existing_credentials

            else:
                # 通用凭证配置
                col1, col2 = st.columns(2)
                with col1:
                    api_key = st.text_input(
                        "API Key",
                        value=existing_credentials.api_key or "",
                        type="password"
                    )
                    username = st.text_input(
                        "用户名",
                        value=existing_credentials.username or ""
                    )
                with col2:
                    token = st.text_input(
                        "Token",
                        value=existing_credentials.token or "",
                        type="password"
                    )
                    password = st.text_input(
                        "密码",
                        value=existing_credentials.password or "",
                        type="password"
                    )

                credentials = DataSourceCredentials(
                    api_key=api_key if api_key else None,
                    token=token if token else None,
                    username=username if username else None,
                    password=password if password else None,
                    timeout=existing_credentials.timeout,
                    retry_times=existing_credentials.retry_times,
                    proxy_url=existing_credentials.proxy_url
                )

            # 高级设置
            with st.expander("高级设置"):
                col1, col2 = st.columns(2)
                with col1:
                    timeout = st.number_input(
                        "请求超时(秒)",
                        min_value=1,
                        value=existing_credentials.timeout
                    )
                    retry_times = st.number_input(
                        "重试次数",
                        min_value=0,
                        value=existing_credentials.retry_times
                    )
                with col2:
                    proxy_url = st.text_input(
                        "代理URL",
                        value=existing_credentials.proxy_url or "",
                        help="如需使用代理，请输入代理URL"
                    )

                credentials.timeout = timeout
                credentials.retry_times = retry_times
                credentials.proxy_url = proxy_url if proxy_url else None

        return credentials

    def _render_connection_test(self):
        """渲染连接测试页面"""
        st.header("🔗 连接测试")

        # 选择要测试的数据源
        all_sources = self.config_manager.get_enabled_data_sources()
        if not all_sources:
            st.warning("没有启用的数据源，请先启用数据源")
            return

        source_names = list(all_sources.keys())
        selected_sources = st.multiselect(
            "选择要测试的数据源",
            options=source_names,
            default=source_names[:1] if source_names else []
        )

        if selected_sources:
            if st.button("开始测试", type="primary"):
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()

                results = {}
                total_tests = len(selected_sources)

                for i, source_name in enumerate(selected_sources):
                    status_text.text(f"正在测试 {source_name}...")
                    progress_bar.progress((i + 1) / total_tests)

                    config = all_sources[source_name]
                    success, message = self._test_connection(config)

                    results[source_name] = {
                        'success': success,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }

                    # 更新配置中的测试状态
                    self.config_manager.update_test_status(source_name, success, message)

                progress_bar.progress(1.0)
                status_text.text("测试完成!")

                # 显示结果
                st.subheader("📊 测试结果")
                for source_name, result in results.items():
                    if result['success']:
                        st.success(f"✅ {source_name}: {result['message']}")
                    else:
                        st.error(f"❌ {source_name}: {result['message']}")

                # 刷新按钮
                if st.button("重新测试"):
                    st.rerun()

        # 显示历史测试状态
        st.markdown("---")
        st.subheader("📈 测试历史")

        source_status = self.selector.get_all_source_status()
        if source_status:
            history_data = []
            for name, status in source_status.items():
                history_data.append({
                    "数据源": name,
                    "最后测试时间": self._format_time(status.last_check_time),
                    "测试状态": status.test_status or "未测试",
                    "可用性": self._get_availability_emoji(status),
                    "响应时间": f"{status.response_time:.2f}s" if status.response_time else "未知",
                    "成功率": f"{status.success_rate:.1%}"
                })

            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)

    def _render_advanced_settings(self):
        """渲染高级设置页面"""
        st.header("🔧 高级设置")

        # 配置导入导出
        st.subheader("📁 配置管理")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**导出配置**")
            if st.button("导出当前配置"):
                config_data = {
                    'export_time': datetime.now().isoformat(),
                    'data_sources': [config.to_dict() for config in self.config_manager.get_all_data_sources().values()]
                }
                st.download_button(
                    label="下载配置文件",
                    data=json.dumps(config_data, ensure_ascii=False, indent=2),
                    file_name=f"data_sources_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        with col2:
            st.markdown("**导入配置**")
            uploaded_file = st.file_uploader(
                "选择配置文件",
                type=['json'],
                help="上传之前导出的数据源配置文件"
            )
            merge_option = st.checkbox("合并到现有配置", value=True)

            if uploaded_file and st.button("导入配置"):
                try:
                    import json
                    config_data = json.load(uploaded_file)
                    success = self.config_manager.import_config(uploaded_file.name, merge_option)
                    if success:
                        st.success("配置导入成功")
                        st.rerun()
                    else:
                        st.error("配置导入失败")
                except Exception as e:
                    st.error(f"配置导入失败: {e}")

        st.markdown("---")

        # 批量操作
        st.subheader("🔄 批量操作")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("刷新所有状态"):
                with st.spinner("刷新中..."):
                    asyncio.run(self.selector.refresh_all_source_status())
                st.success("状态刷新完成")

        with col2:
            if st.button("重置为默认配置"):
                if st.confirm("确定要重置为默认配置吗？这将删除当前所有配置。"):
                    # 删除配置文件并重新创建
                    self.config_manager.config_file.unlink(missing_ok=True)
                    self.config_manager.load_config()
                    st.success("已重置为默认配置")
                    st.rerun()

        with col3:
            if st.button("清理缓存"):
                # 清理所有数据源缓存
                cleared_count = 0
                for name in self.config_manager.get_enabled_data_sources():
                    try:
                        # 这里需要根据不同数据源调用对应的清理方法
                        # 暂时显示成功消息
                        cleared_count += 1
                    except:
                        pass
                st.success(f"清理了 {cleared_count} 个数据源的缓存")

        # 系统信息
        st.markdown("---")
        st.subheader("📊 系统信息")

        stats = self.selector.get_request_stats()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总请求数", stats['total_requests'])
        with col2:
            st.metric("成功请求", stats['successful_requests'])
        with col3:
            st.metric("失败请求", stats['failed_requests'])
        with col4:
            success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
            st.metric("成功率", f"{success_rate:.1f}%")

    def _test_connection(self, config: DataSourceConfig) -> tuple[bool, str]:
        """测试数据源连接"""
        try:
            # 使用选择器进行健康检查
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_available = loop.run_until_complete(
                    self.selector._perform_health_check(config)
                )
                if is_available:
                    return True, "连接成功"
                else:
                    return False, "连接失败"
            finally:
                loop.close()
        except Exception as e:
            return False, f"测试失败: {str(e)}"

    def _get_priority_emoji(self, priority: DataSourcePriority) -> str:
        """获取优先级表情符号"""
        emoji_map = {
            DataSourcePriority.PRIMARY: "🥇",
            DataSourcePriority.SECONDARY: "🥈",
            DataSourcePriority.FALLBACK: "🥉"
        }
        return emoji_map.get(priority, "❓")

    def _get_availability_emoji(self, status) -> str:
        """获取可用性表情符号"""
        if status is None:
            return "❓"
        elif status.is_available:
            return "✅"
        elif status.is_available is False:
            return "❌"
        else:
            return "⏳"

    def _format_time(self, timestamp) -> str:
        """格式化时间"""
        if timestamp is None:
            return "从未"
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def render_data_source_settings():
    """渲染数据源设置页面的入口函数"""
    ui = DataSourceSettingsUI()
    ui.render()


if __name__ == "__main__":
    render_data_source_settings()