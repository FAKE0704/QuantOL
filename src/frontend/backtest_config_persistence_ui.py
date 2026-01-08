import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime
from src.frontend.backtest_config_persistence import BacktestConfigPersistence
from src.core.strategy.backtesting import BacktestConfig
from src.support.log.logger import logger

class BacktestConfigPersistenceUI:
    """回测配置持久化 UI 组件

    负责配置保存、加载、管理的用户界面
    """

    def __init__(self, session_state, persistence_manager: BacktestConfigPersistence):
        """初始化UI组件

        Args:
            session_state: Streamlit session_state
            persistence_manager: 配置持久化管理器
        """
        self.session_state = session_state
        self.persistence = persistence_manager

    def render_save_config_dialog(self, backtest_config: BacktestConfig) -> bool:
        """渲染保存配置对话框

        Args:
            backtest_config: 当前回测配置

        Returns:
            是否成功保存
        """
        st.subheader("💾 保存当前配置")

        # 获取当前用户
        current_user = self.session_state.get('current_user')
        if not current_user:
            st.error("请先登录")
            return False

        username = current_user.get('username')

        # 配置名称输入
        col1, col2 = st.columns([2, 1])
        with col1:
            config_name = st.text_input(
                "配置名称 *",
                placeholder="例如：双均线策略_日线",
                key="save_config_name"
            )
        with col2:
            # 显示最近保存的配置作为参考
            recent_configs = self.persistence.list_configs(username)[:3]
            if recent_configs:
                default_name = st.selectbox(
                    "或选择参考",
                    options=[c['name'] for c in recent_configs],
                    format_func=lambda x: f"📋 {x}",
                    key="recent_config_select"
                )
                if config_name and st.button("使用参考名称", key="use_reference_name"):
                    st.session_state.save_config_name = default_name
                    st.rerun()

        # 配置描述
        description = st.text_area(
            "配置描述",
            placeholder="描述此配置的特点和用途...",
            key="save_config_description",
            height=80
        )

        # 配置预览
        with st.expander("📋 查看当前配置参数", expanded=False):
            self._render_config_summary(backtest_config)

        # 保存按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ 保存配置", type="primary", key="confirm_save_config"):
                if not config_name:
                    st.error("请输入配置名称")
                    return False

                try:
                    self.persistence.save_config(username, config_name, backtest_config, description)
                    st.success(f"配置 '{config_name}' 保存成功！")
                    return True
                except ValueError as e:
                    st.error(f"配置验证失败: {e}")
                    return False
                except Exception as e:
                    st.error(f"保存失败: {e}")
                    return False

        return False

    def render_load_config_ui(self) -> Optional[BacktestConfig]:
        """渲染加载配置界面

        Returns:
            加载的配置对象，未加载则返回 None
        """
        st.subheader("📂 加载已保存配置")

        # 获取当前用户
        current_user = self.session_state.get('current_user')
        if not current_user:
            st.error("请先登录")
            return None

        username = current_user.get('username')

        # 获取配置列表
        configs = self.persistence.list_configs(username)

        if not configs:
            st.info("暂无保存的配置")
            return None

        # 搜索和过滤
        search_term = st.text_input("🔍 搜索配置", placeholder="输入配置名称...", key="load_config_search")

        if search_term:
            configs = [c for c in configs if search_term.lower() in c.get('name', '').lower()]

        # 显示配置列表
        for config_meta in configs:
            config_name = config_meta.get('name', '未命名')
            description = config_meta.get('description', '')
            created_at = config_meta.get('created_at', '')
            filename = config_meta.get('_filename', '')

            # 格式化时间
            try:
                created_time = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
            except:
                created_time = created_at

            # 配置卡片
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{config_name}**")
                    if description:
                        st.caption(description)

                with col2:
                    st.caption(f"📅 {created_time}")

                with col3:
                    if st.button("📥 加载", key=f"load_{filename}"):
                        config_data = self.persistence.load_config(username, config_name)
                        if config_data:
                            try:
                                config = BacktestConfig.from_dict(config_data['config'])
                                st.success(f"配置 '{config_name}' 加载成功！")
                                return config
                            except Exception as e:
                                st.error(f"加载失败: {e}")
                                return None

                # 配置预览（可折叠）
                with st.expander(f"查看 '{config_name}' 详情"):
                    config_data = self.persistence.load_config(username, config_name)
                    if config_data:
                        self._render_config_preview(config_data)

                st.markdown("---")

        return None

    def render_config_management_panel(self, username: str) -> None:
        """渲染完整的配置管理面板

        Args:
            username: 用户名
        """
        st.subheader("📋 配置管理")

        # Tab 切换不同功能
        tab1, tab2, tab3 = st.tabs(["配置列表", "导入/导出", "批量操作"])

        with tab1:
            self._render_config_list_tab(username)

        with tab2:
            self._render_import_export_tab(username)

        with tab3:
            self._render_batch_operations_tab(username)

    def _render_config_list_tab(self, username: str) -> None:
        """渲染配置列表标签页"""
        configs = self.persistence.list_configs(username)

        if not configs:
            st.info("暂无保存的配置")
            return

        # 转换为 DataFrame 显示
        df_data = []
        for config in configs:
            df_data.append({
                "名称": config['name'],
                "描述": config.get('description', '')[:30] + '...' if len(config.get('description', '')) > 30 else config.get('description', ''),
                "创建时间": config.get('created_at', ''),
                "文件名": config.get('_filename', '')
            })

        df = pd.DataFrame(df_data)

        # 显示数据表格
        st.dataframe(
            df,
            column_config={
                "名称": st.column_config.TextColumn("配置名称", width="medium"),
                "描述": st.column_config.TextColumn("描述", width="large"),
                "创建时间": st.column_config.DatetimeColumn("创建时间", format="YYYY-MM-DD HH:mm"),
                "文件名": st.column_config.TextColumn("文件名", width="small", disabled=True)
            },
            hide_index=True,
            width='stretch'
        )

        # 操作区域
        st.markdown("### 操作")

        selected_config_name = st.selectbox(
            "选择要操作的配置",
            options=[c['name'] for c in configs],
            key="manage_config_select"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 查看详情", key="view_config_detail"):
                config_data = self.persistence.load_config(username, selected_config_name)
                if config_data:
                    with st.expander("配置详情", expanded=True):
                        self._render_config_preview(config_data)

        with col2:
            if st.button("🗑️ 删除配置", key="delete_config_btn"):
                if self.persistence.delete_config(username, selected_config_name):
                    st.success(f"配置 '{selected_config_name}' 已删除")
                    st.rerun()
                else:
                    st.error("删除失败")

        with col3:
            if st.button("📝 更新描述", key="update_config_desc"):
                new_description = st.text_area(
                    "新描述",
                    value=next((c.get('description', '') for c in configs if c['name'] == selected_config_name), ''),
                    key="update_desc_input"
                )
                if st.button("确认更新", key="confirm_update_desc"):
                    if self.persistence.update_config_metadata(username, selected_config_name, new_description):
                        st.success("描述更新成功")
                        st.rerun()

    def _render_import_export_tab(self, username: str) -> None:
        """渲染导入/导出标签页"""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📤 导出配置")

            configs = self.persistence.list_configs(username)
            if configs:
                export_config = st.selectbox(
                    "选择要导出的配置",
                    options=[c['name'] for c in configs],
                    key="export_config_select"
                )

                export_filename = st.text_input(
                    "导出文件名",
                    value=f"{export_config}_export.json",
                    key="export_filename"
                )

                if st.button("📤 导出配置", key="export_config_btn"):
                    # 使用 Streamlit 的下载功能
                    config_data = self.persistence.load_config(username, export_config)
                    if config_data:
                        st.download_button(
                            label="下载配置文件",
                            data=str(config_data),
                            file_name=export_filename,
                            mime="application/json",
                            key="download_config_btn"
                        )
            else:
                st.info("暂无配置可导出")

        with col2:
            st.markdown("### 📥 导入配置")

            uploaded_file = st.file_uploader(
                "选择配置文件",
                type=['json'],
                key="import_config_file"
            )

            if uploaded_file:
                try:
                    import json
                    config_data = json.load(uploaded_file)

                    # 显示配置信息
                    st.json(config_data)

                    new_name = st.text_input(
                        "新配置名称（留空保持原名）",
                        key="import_config_name"
                    )

                    if st.button("📥 导入配置", key="import_config_btn"):
                        # 临时保存文件
                        temp_path = f"/tmp/temp_import_{datetime.now().timestamp()}.json"
                        with open(temp_path, 'w') as f:
                            json.dump(config_data, f)

                        if self.persistence.import_config(username, temp_path, new_name or None):
                            st.success("配置导入成功！")
                            st.rerun()
                        else:
                            st.error("导入失败")

                except Exception as e:
                    st.error(f"文件格式错误: {e}")

    def _render_batch_operations_tab(self, username: str) -> None:
        """渲染批量操作标签页"""
        st.markdown("### 批量操作")

        configs = self.persistence.list_configs(username)

        if not configs:
            st.info("暂无配置")
            return

        st.info("批量操作功能开发中...")

        # 可以在此添加批量导出、批量删除等功能

    def _render_config_preview(self, config_data: Dict[str, Any]) -> None:
        """渲染配置预览

        Args:
            config_data: 配置数据（包含 metadata 和 config）
        """
        metadata = config_data.get('metadata', {})
        config = config_data.get('config', {})

        # 元数据
        st.markdown("**元数据**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"名称: {metadata.get('name', '未命名')}")
            st.write(f"版本: {metadata.get('version', '1.0')}")
        with col2:
            st.write(f"创建时间: {metadata.get('created_at', '')}")
            st.write(f"更新时间: {metadata.get('updated_at', '')}")

        if metadata.get('description'):
            st.write(f"描述: {metadata['description']}")

        st.markdown("---")

        # 配置参数
        st.markdown("**配置参数**")

        # 基础参数
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("初始资金", f"¥{config.get('initial_capital', 0):,.0f}")
        with col2:
            st.metric("交易佣金", f"{config.get('commission_rate', 0)*100:.3f}%")
        with col3:
            st.metric("数据频率", config.get('frequency', ''))
        with col4:
            st.metric("策略类型", config.get('strategy_type', ''))

        # 时间范围
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"开始日期: {config.get('start_date', '')}")
        with col2:
            st.write(f"结束日期: {config.get('end_date', '')}")

        # 交易标的
        symbols = config.get('target_symbols') or [config.get('target_symbol', '')]
        st.write(f"交易标的: {', '.join(symbols)}")

        # 仓位策略
        pos_type = config.get('position_strategy_type', '')
        pos_params = config.get('position_strategy_params', {})
        st.write(f"仓位策略: {pos_type}")
        if pos_params:
            st.json(pos_params)

        # 显示自定义规则（如果有）
        strategy_type = config.get('strategy_type', '')
        if strategy_type == "自定义规则" or config.get('custom_rules') or config.get('default_custom_rules'):
            st.markdown("---")
            st.markdown("**自定义规则**")

            # 优先显示 custom_rules
            rules = config.get('custom_rules') or config.get('default_custom_rules')
            if rules:
                col1, col2 = st.columns(2)
                with col1:
                    if rules.get('open_rule'):
                        st.code(f"开仓: {rules['open_rule']}", language="text")
                    if rules.get('close_rule'):
                        st.code(f"平仓: {rules['close_rule']}", language="text")
                with col2:
                    if rules.get('buy_rule'):
                        st.code(f"买入: {rules['buy_rule']}", language="text")
                    if rules.get('sell_rule'):
                        st.code(f"卖出: {rules['sell_rule']}", language="text")

        # 显示规则组信息（如果有）
        elif strategy_type.startswith("规则组:"):
            st.markdown("---")
            st.markdown(f"**规则组**: {strategy_type.replace('规则组:', '').strip()}")

            # 显示 strategy_mapping 中的规则组配置
            strategy_mapping = config.get('strategy_mapping', {})
            if strategy_mapping:
                for symbol, mapping in strategy_mapping.items():
                    if mapping.get('rules'):
                        st.markdown(f"**{symbol} 规则组**")
                        rules = mapping['rules']
                        col1, col2 = st.columns(2)
                        with col1:
                            if rules.get('open_rule'):
                                st.code(f"开仓: {rules['open_rule']}", language="text")
                            if rules.get('close_rule'):
                                st.code(f"平仓: {rules['close_rule']}", language="text")
                        with col2:
                            if rules.get('buy_rule'):
                                st.code(f"买入: {rules['buy_rule']}", language="text")
                            if rules.get('sell_rule'):
                                st.code(f"卖出: {rules['sell_rule']}", language="text")

    def _render_config_summary(self, backtest_config: BacktestConfig) -> None:
        """渲染配置摘要（用于保存对话框）

        Args:
            backtest_config: 回测配置对象
        """
        # 基础参数
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**回测期间**: {backtest_config.start_date} ~ {backtest_config.end_date}")
        with col2:
            st.write(f"**初始资金**: ¥{backtest_config.initial_capital:,.0f}")
        with col3:
            st.write(f"**数据频率**: {backtest_config.frequency}")

        # 交易标的
        symbols = backtest_config.get_symbols()
        st.write(f"**交易标的**: {', '.join(symbols)}")

        # 策略信息
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**策略类型**: {backtest_config.strategy_type}")
        with col2:
            st.write(f"**仓位策略**: {backtest_config.position_strategy_type}")

        # 显示自定义规则（如果有）
        if backtest_config.strategy_type == "自定义规则" or (
            hasattr(backtest_config, 'custom_rules') and backtest_config.custom_rules
        ):
            st.markdown("---")
            st.markdown("**自定义规则**")

            # 优先显示 custom_rules
            rules = None
            if hasattr(backtest_config, 'custom_rules') and backtest_config.custom_rules:
                rules = backtest_config.custom_rules
            elif hasattr(backtest_config, 'default_custom_rules') and backtest_config.default_custom_rules:
                rules = backtest_config.default_custom_rules

            if rules:
                col1, col2 = st.columns(2)
                with col1:
                    if rules.get('open_rule'):
                        st.code(f"开仓: {rules['open_rule']}", language="text")
                    if rules.get('close_rule'):
                        st.code(f"平仓: {rules['close_rule']}", language="text")
                with col2:
                    if rules.get('buy_rule'):
                        st.code(f"买入: {rules['buy_rule']}", language="text")
                    if rules.get('sell_rule'):
                        st.code(f"卖出: {rules['sell_rule']}", language="text")

        # 显示规则组信息（如果有）
        elif backtest_config.strategy_type.startswith("规则组:"):
            st.markdown("---")
            st.markdown(f"**规则组**: {backtest_config.strategy_type.replace('规则组:', '').strip()}")

            # 显示 strategy_mapping 中的规则组配置
            if hasattr(backtest_config, 'strategy_mapping') and backtest_config.strategy_mapping:
                for symbol, mapping in backtest_config.strategy_mapping.items():
                    if mapping.get('rules'):
                        st.markdown(f"**{symbol} 规则组**")
                        rules = mapping['rules']
                        col1, col2 = st.columns(2)
                        with col1:
                            if rules.get('open_rule'):
                                st.code(f"开仓: {rules['open_rule']}", language="text")
                            if rules.get('close_rule'):
                                st.code(f"平仓: {rules['close_rule']}", language="text")
                        with col2:
                            if rules.get('buy_rule'):
                                st.code(f"买入: {rules['buy_rule']}", language="text")
                            if rules.get('sell_rule'):
                                st.code(f"卖出: {rules['sell_rule']}", language="text")
