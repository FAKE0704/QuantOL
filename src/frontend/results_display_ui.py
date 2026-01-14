import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any
from src.core.strategy.backtesting import BacktestConfig
from src.services.chart_service import ChartService

class ResultsDisplayUI:
    """结果展示UI组件，负责回测结果的界面渲染"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_results_tabs(self, results: Dict[str, Any], backtest_config: BacktestConfig) -> None:
        """渲染结果展示标签页"""
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
            "📊 回测摘要", "💱 交易记录", "📈 仓位明细", "📉 净值曲线",
            "📈 技术指标", "📊 性能分析", "📉 回撤分析", "📊 收益分布",
            "🎯 交易信号", "🔍 详细数据", "🐛 调试数据"
        ])

        with tab1:
            self.render_summary_tab(results, backtest_config)
        with tab2:
            self.render_trades_tab(results)
        with tab3:
            self.render_positions_tab(results)
        with tab4:
            self.render_equity_chart_tab(results)
        with tab5:
            self.render_technical_indicators_tab(results)
        with tab6:
            self.render_performance_tab(results)
        with tab7:
            self.render_drawdown_tab(results)
        with tab8:
            self.render_returns_distribution_tab(results)
        with tab9:
            self.render_signals_tab(results)
        with tab10:
            self.render_detailed_data_tab(results)
        with tab11:
            self.render_debug_data_tab(results)

    def render_summary_tab(self, results: Dict[str, Any], backtest_config: BacktestConfig) -> None:
        """渲染回测摘要标签页"""
        from src.frontend.results_display_manager import ResultsDisplayManager

        display_manager = ResultsDisplayManager(self.session_state)
        display_manager.display_backtest_summary(results, backtest_config)

    def render_trades_tab(self, results: Dict[str, Any]) -> None:
        """渲染交易记录标签页"""
        from src.frontend.results_display_manager import ResultsDisplayManager

        display_manager = ResultsDisplayManager(self.session_state)
        display_manager.display_trade_records(results)

    def render_positions_tab(self, results: Dict[str, Any]) -> None:
        """渲染仓位明细标签页"""
        from src.frontend.results_display_manager import ResultsDisplayManager

        display_manager = ResultsDisplayManager(self.session_state)
        display_manager.display_position_details(results)

    def render_equity_chart_tab(self, results: Dict[str, Any]) -> None:
        """渲染净值曲线标签页"""
        st.subheader("📉 净值曲线")

        # 获取净值数据
        equity_data = self._get_equity_data(results)
        if equity_data is not None:
            # 使用ChartService绘制净值曲线
            from src.services.chart_service import DataBundle, ChartService
            data_bundle = DataBundle(raw_data=equity_data)
            chart_service = ChartService.get_chart_service(data_bundle)

            # 显示净值百分比变化与资产配置（现有图表）
            st.markdown("### 净值百分比变化与资产配置")
            chart_service.draw_equity_and_allocation(equity_data)

            # 分隔线
            st.divider()

            # 显示绝对净值金额（新增图表）
            st.markdown("### 绝对净值金额")
            chart_service.draw_absolute_net_value(equity_data)
        else:
            st.warning("无净值数据可用")

    def render_technical_indicators_tab(self, results: Dict[str, Any]) -> None:
        """渲染技术指标标签页"""
        st.subheader("📈 技术指标分析")

        # 获取价格数据
        price_data = self._get_price_data(results)
        if price_data is not None:
            # SMA参数选择和图表部分
            st.subheader("📊 SMA移动平均线")

            # 使用form来避免rerun
            with st.form("sma_form"):
                # 获取当前SMA周期值
                current_sma_period = st.session_state.get('sma_period', 5)

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    sma_period = st.number_input(
                        "SMA周期",
                        min_value=1,
                        max_value=200,
                        value=current_sma_period,
                        key="sma_period_input"
                    )

                with col2:
                    submitted = st.form_submit_button("确认参数")

                with col3:
                    st.write(f"当前SMA周期: {current_sma_period}")

                # 如果表单提交，更新session_state
                if submitted:
                    st.session_state.sma_period = sma_period
                    st.success(f"SMA周期已更新为: {sma_period}")
                    # 使用rerun来重新渲染图表，但由于是在form内部，只会重新渲染当前tab
                    st.rerun()

            # 绘制SMA图表，使用当前session_state中的值
            self._render_sma_chart(price_data, st.session_state.get('sma_period', 5))

            st.divider()

            # 使用ChartService绘制其他技术指标
            from src.services.chart_service import DataBundle, ChartService
            data_bundle = DataBundle(raw_data=price_data)
            chart_service = ChartService.get_chart_service(data_bundle)

            col1, col2 = st.columns(2)
            with col1:
                chart_service.drawMA(price_data, [5, 10, 20])
                chart_service.drawMACD(price_data)
            with col2:
                chart_service.drawBollingerBands(price_data)
                # 使用实例方法的drawRSI，它只需要data参数
                chart_service.drawRSI(price_data)
        else:
            st.warning("无价格数据可用")

    def render_performance_tab(self, results: Dict[str, Any]) -> None:
        """渲染性能分析标签页"""
        st.subheader("📊 综合性能指标")

        # 获取净值数据
        equity_data = self._get_equity_data(results)
        trades_data = self._get_trades_data(results)

        if equity_data is not None:
            from src.frontend.results_display_manager import ResultsDisplayManager

            display_manager = ResultsDisplayManager(self.session_state)
            display_manager.display_performance_metrics(equity_data, trades_data)
        else:
            st.warning("无净值数据可用")

    def render_drawdown_tab(self, results: Dict[str, Any]) -> None:
        """渲染回撤分析标签页"""
        st.subheader("📉 回撤分析")

        equity_data = self._get_equity_data(results)
        if equity_data is not None:
            # 使用ChartService绘制回撤曲线
            from src.services.chart_service import DataBundle, ChartService
            data_bundle = DataBundle(raw_data=equity_data)
            chart_service = ChartService.get_chart_service(data_bundle)
            chart_service.draw_drawdown_analysis(equity_data)
        else:
            st.warning("无净值数据可用")

    def render_returns_distribution_tab(self, results: Dict[str, Any]) -> None:
        """渲染收益分布标签页"""
        st.subheader("📊 收益分布分析")

        equity_data = self._get_equity_data(results)
        if equity_data is not None:
            # 使用ChartService绘制收益分布
            from src.services.chart_service import DataBundle, ChartService
            data_bundle = DataBundle(raw_data=equity_data)
            chart_service = ChartService.get_chart_service(data_bundle)
            chart_service.draw_returns_distribution(equity_data)
        else:
            st.warning("无净值数据可用")

    def render_signals_tab(self, results: Dict[str, Any]) -> None:
        """渲染交易信号标签页"""
        st.subheader("🎯 交易信号分析")

        price_data = self._get_price_data(results)
        signals_data = self._get_signals_data(results)

        if price_data is not None and signals_data is not None:
            # 使用ChartService绘制交易信号
            from src.services.chart_service import DataBundle, ChartService
            data_bundle = DataBundle(raw_data=price_data)
            chart_service = ChartService.get_chart_service(data_bundle)
            chart_service.draw_trading_signals(price_data, signals_data)
        else:
            st.warning("无价格或信号数据可用")

    def render_detailed_data_tab(self, results: Dict[str, Any]) -> None:
        """渲染详细数据标签页"""
        st.subheader("🔍 详细数据")

        # 显示净值记录（包含规则判断结果）
        if "equity_records" in results:
            st.subheader("净值记录")
            equity_df = pd.DataFrame(results["equity_records"])

            # 首先尝试从debug_data获取规则解析后的数据
            rule_data_source = None
            rule_columns = {}

            # 方法1：从debug_data获取规则数据
            if "debug_data" in results and results["debug_data"]:
                debug_data = results["debug_data"]

                # 查找第一个策略的debug_data（通常规则策略会存储在这里）
                for strategy_name, strategy_data in debug_data.items():
                    if strategy_data is not None and hasattr(strategy_data, 'columns'):
                        # 尝试从这个策略数据中找到规则列
                        found_columns = self._find_rule_columns(strategy_data)
                        if found_columns:
                            rule_columns = found_columns
                            rule_data_source = strategy_data
                            break

            # 方法2：从price_data获取规则数据（原有逻辑）
            if not rule_columns:
                price_data = results.get("price_data")
                # 如果 price_data 是列表（从JSON反序列化后），转换为DataFrame
                if isinstance(price_data, list):
                    price_data = pd.DataFrame(price_data)
                if price_data is not None and not price_data.empty:
                    rule_columns = self._find_rule_columns(price_data)
                    if rule_columns:
                        rule_data_source = price_data

            # 如果找到了规则列，合并到净值记录中
            if rule_columns and rule_data_source is not None:
                equity_df = self._merge_rule_results_to_equity(equity_df, rule_data_source, rule_columns)
            else:
                st.warning("⚠️ 未找到规则数据，无法显示规则判断结果")

            st.dataframe(equity_df, use_container_width=True)

        if "trades" in results and results["trades"]:
            st.subheader("交易记录")
            trades_df = pd.DataFrame(results["trades"])
            st.dataframe(trades_df, use_container_width=True)

    def _find_rule_columns(self, price_data: pd.DataFrame) -> dict:
        """查找规则结果列并返回映射关系"""
        rule_columns = {}

        # 方法1：从 attrs 中读取规则类型映射（最准确）
        if hasattr(price_data, 'attrs') and 'rule_type_mapping' in price_data.attrs:
            rule_type_mapping = price_data.attrs['rule_type_mapping']

            for col_name, rule_type in rule_type_mapping.items():
                if col_name in price_data.columns:
                    rule_columns[col_name] = rule_type

            if rule_columns:
                return rule_columns

        # 方法2：如果没有映射，使用关键词匹配（降级方案）
        rule_type_mapping = {}
        price_columns = {'open', 'high', 'low', 'close', 'volume', 'time', 'date', 'datetime', 'signal', 'code', 'combined_time'}

        # 查找规则表达式的存储结果
        # 规则解析器在解析时会将布尔表达式结果存储，列名为原始表达式
        potential_rule_columns = []

        # 首先收集所有可能的规则列
        for col in price_data.columns:
            if col.lower() in price_columns:
                continue

            # 检查该列是否为规则表达式结果
            sample_values = price_data[col].dropna().head(10)
            if self._is_rule_result_column(sample_values):
                potential_rule_columns.append((col, sample_values))

        # 使用更智能的识别方法：检查dataframe的attrs属性
        # 规则解析器会在attrs中存储表达式信息
        if hasattr(price_data, 'attrs'):
            # 查找规则表达式相关的属性
            expr_attributes = {k: v for k, v in price_data.attrs.items() if k.endswith('_expr')}

        # 如果使用策略组合，尝试从策略实例获取规则表达式
        # 这里需要找到与四种规则类型对应的列

        # 方法1：通过关键词匹配
        for col, sample_values in potential_rule_columns:
            col_lower = col.lower()

            if any(keyword in col_lower for keyword in ['open', '开仓']) and '开仓' not in rule_type_mapping.values():
                rule_columns[col] = '开仓'
                rule_type_mapping[col] = '开仓'

            elif any(keyword in col_lower for keyword in ['close', '清仓']) and '清仓' not in rule_type_mapping.values():
                rule_columns[col] = '清仓'
                rule_type_mapping[col] = '清仓'

            elif any(keyword in col_lower for keyword in ['buy', '加仓']) and '加仓' not in rule_type_mapping.values():
                rule_columns[col] = '加仓'
                rule_type_mapping[col] = '加仓'

            elif any(keyword in col_lower for keyword in ['sell', '平仓']) and '平仓' not in rule_type_mapping.values():
                rule_columns[col] = '平仓'
                rule_type_mapping[col] = '平仓'

        # 方法2：如果关键词匹配失败，按顺序分配
        if len(rule_columns) < 4 and len(potential_rule_columns) >= 4:
            # 获取未分配的规则类型
            missing_rules = []
            if '开仓' not in rule_type_mapping.values():
                missing_rules.append('开仓')
            if '清仓' not in rule_type_mapping.values():
                missing_rules.append('清仓')
            if '加仓' not in rule_type_mapping.values():
                missing_rules.append('加仓')
            if '平仓' not in rule_type_mapping.values():
                missing_rules.append('平仓')

            # 为未分配的规则类型选择列
            rule_idx = 0
            for col, sample_values in potential_rule_columns:
                if col not in rule_columns and rule_idx < len(missing_rules):
                    rule_type = missing_rules[rule_idx]
                    rule_columns[col] = rule_type
                    rule_type_mapping[col] = rule_type
                    rule_idx += 1

                if len(rule_columns) == 4:
                    break

        # 方法3：如果规则列不足4个，尝试从debug_data中查找
        if len(rule_columns) < 4:
            # 检查是否有布尔值列被遗漏
            all_bool_cols = []
            for col in price_data.columns:
                if col.lower() in price_columns or col in rule_columns:
                    continue

                sample_values = price_data[col].dropna().head(10)
                if self._is_rule_result_column(sample_values):
                    all_bool_cols.append((col, sample_values))

        return rule_columns

    def _is_rule_result_column(self, sample_values: pd.Series) -> bool:
        """判断列是否为规则结果列"""
        if sample_values.empty:
            return False

        # 检查是否包含布尔值（包括 numpy.bool_）
        if sample_values.dtype in [bool, np.bool_]:
            return True

        # 检查第一个值是否为布尔类型
        if len(sample_values) > 0:
            first_val = sample_values.iloc[0]
            if isinstance(first_val, (bool, np.bool_)):
                return True

        # 检查是否包含0/1数值
        try:
            numeric_values = pd.to_numeric(sample_values, errors='coerce').dropna()
            if not numeric_values.empty:
                unique_values = set(numeric_values)
                # 如果主要是0和1，很可能是规则结果
                if unique_values.issubset({0.0, 1.0, 0, 1}):
                    return True
        except:
            pass

        # 检查是否包含字符串形式的布尔值
        if sample_values.dtype == object:
            str_values = sample_values.astype(str).str.lower()
            if str_values.isin(['true', 'false', '1', '0', 'yes', 'no']).any():
                return True

        return False

    def _merge_rule_results_to_equity(self, equity_df: pd.DataFrame, price_data: pd.DataFrame, rule_columns: dict) -> pd.DataFrame:
        """将规则结果合并到净值记录中"""
        if not rule_columns:
            return equity_df

        # 直接使用行号匹配，与后端保持一致
        return self._merge_by_row_number(equity_df, price_data, rule_columns)

    def _merge_by_row_number(self, equity_df: pd.DataFrame, price_data: pd.DataFrame, rule_columns: dict) -> pd.DataFrame:
        """按行号匹配合并规则结果到净值记录"""
        # 检查净值记录和价格数据的行数是否匹配
        min_rows = min(len(equity_df), len(price_data))

        # 为每个规则列创建匹配
        for original_col, display_name in rule_columns.items():
            # 创建规则结果列，初始值为空
            equity_df[f'规则_{display_name}'] = None

            # 按行号匹配
            for i in range(min_rows):
                rule_result = price_data.iloc[i][original_col]

                # 检查规则结果是否为布尔值（True/False）或可以解释为布尔值
                if isinstance(rule_result, (bool, np.bool_)):
                    equity_df.at[i, f'规则_{display_name}'] = '触发' if rule_result else '未触发'
                elif isinstance(rule_result, (int, float, str, np.integer, np.floating)):
                    # 尝试将数值或字符串转换为布尔值判断
                    try:
                        if str(rule_result).lower() in ['true', '1', 'yes', 'on']:
                            equity_df.at[i, f'规则_{display_name}'] = '触发'
                        elif str(rule_result).lower() in ['false', '0', 'no', 'off', '']:
                            equity_df.at[i, f'规则_{display_name}'] = '未触发'
                        else:
                            # 对于数值，检查是否大于0
                            if float(rule_result) > 0:
                                equity_df.at[i, f'规则_{display_name}'] = '触发'
                            elif float(rule_result) == 0:
                                equity_df.at[i, f'规则_{display_name}'] = '未触发'
                    except (ValueError, TypeError):
                        pass

        return equity_df

    def render_debug_data_tab(self, results: Dict[str, Any]) -> None:
        """渲染调试数据标签页"""
        st.subheader("🐛 规则解析器调试数据")

        if "debug_data" not in results or not results["debug_data"]:
            st.info("无调试数据可用（仅在使用自定义规则策略时生成）")
            return

        debug_data = results["debug_data"]

        for strategy_name, strategy_data in debug_data.items():
            if strategy_data is None:
                continue

            st.subheader(f"策略: {strategy_name}")

            # 显示数据形状和基本信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("数据行数", len(strategy_data))
            with col2:
                st.metric("数据列数", len(strategy_data.columns))
            with col3:
                # 显示时间范围
                if 'combined_time' in strategy_data.columns:
                    time_range = f"{strategy_data['combined_time'].min()} 至 {strategy_data['combined_time'].max()}"
                    st.metric("时间范围", time_range)

            # 列分类：基础数据、指标数据、规则表达式结果
            basic_cols = ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time']
            indicator_cols = [col for col in strategy_data.columns
                            if any(func in col for func in ['SMA', 'RSI', 'MACD', 'REF'])]
            rule_cols = [col for col in strategy_data.columns
                        if col not in basic_cols and col not in indicator_cols]

            # 显示列分类
            st.write("**列分类:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"基础数据 ({len(basic_cols)}列):")
                st.write(", ".join(basic_cols))
            with col2:
                st.write(f"指标数据 ({len(indicator_cols)}列):")
                st.write(", ".join(indicator_cols[:10]) + ("..." if len(indicator_cols) > 10 else ""))
            with col3:
                st.write(f"规则结果 ({len(rule_cols)}列):")
                st.write(", ".join(rule_cols[:10]) + ("..." if len(rule_cols) > 10 else ""))

            # 数据展示选项
            show_columns = st.multiselect(
                "选择要显示的列",
                options=list(strategy_data.columns),
                default=basic_cols + indicator_cols[:5],  # 默认显示基础数据和前5个指标
                key=f"columns_{strategy_name}"
            )

            # 合并 equity_records 中的实际持仓数据到 debug_data
            equity_data = self._get_equity_data(results)
            merged = False
            if equity_data is not None and not equity_data.empty:
                # 将 equity_data 中的 position 和 position_cost 合并到 strategy_data
                if 'position' in equity_data.columns and 'timestamp' in equity_data.columns:
                    # 确保 strategy_data 有 datetime 列
                    if 'datetime' in strategy_data.columns:
                        # 创建一个映射，从时间戳到 position 和 position_cost
                        equity_data_copy = equity_data.copy()
                        equity_data_copy['timestamp'] = pd.to_datetime(equity_data_copy['timestamp'])
                        strategy_data_copy = strategy_data.copy()
                        strategy_data_copy['datetime'] = pd.to_datetime(strategy_data_copy['datetime'])

                        # 更新 POSITION 列为实际持仓数据
                        if len(strategy_data_copy) == len(equity_data_copy):
                            strategy_data['POSITION'] = equity_data_copy['position'].values
                            if 'position_cost' in equity_data_copy.columns:
                                strategy_data['COST'] = equity_data_copy['position_cost'].values
                            merged = True

            if show_columns:
                # 显示数据预览
                st.write(f"**数据预览:**")
                display_data = strategy_data[show_columns]
                st.dataframe(display_data, use_container_width=True)

                # 提供数据下载
                csv = display_data.to_csv(index=False)
                st.download_button(
                    label="下载显示的数据为CSV",
                    data=csv,
                    file_name=f"debug_data_{strategy_name}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("请选择要显示的列")

            st.divider()

    def _get_equity_data(self, results: Dict[str, Any]) -> pd.DataFrame:
        """获取净值数据"""
        if "combined_equity" in results:
            return results["combined_equity"]
        elif "equity_records" in results:
            equity_data = pd.DataFrame(results["equity_records"])
            # 转换 timestamp 为 datetime 类型（从Redis反序列化后是字符串）
            if 'timestamp' in equity_data.columns:
                equity_data['timestamp'] = pd.to_datetime(equity_data['timestamp'])
            return equity_data
        return None

    def _get_price_data(self, results: Dict[str, Any]) -> pd.DataFrame:
        """获取价格数据"""
        if "price_data" in results:
            price_data = results["price_data"]
            # 如果 price_data 是列表（从JSON反序列化后），转换为DataFrame
            if isinstance(price_data, list):
                price_data = pd.DataFrame(price_data)
            # 转换时间相关列为datetime类型
            if price_data is not None and not price_data.empty:
                if 'combined_time' in price_data.columns:
                    price_data['combined_time'] = pd.to_datetime(price_data['combined_time'])
                elif 'date' in price_data.columns:
                    price_data['date'] = pd.to_datetime(price_data['date'])
            return price_data
        return None

    def _get_trades_data(self, results: Dict[str, Any]) -> pd.DataFrame:
        """获取交易数据"""
        if "trades" in results and results["trades"]:
            return pd.DataFrame(results["trades"])
        return None

    def _get_signals_data(self, results: Dict[str, Any]) -> pd.DataFrame:
        """获取信号数据"""
        if "signals" in results:
            return pd.DataFrame(results["signals"])
        return None

    
    def _render_sma_chart(self, price_data: pd.DataFrame, sma_period: int):
        """渲染SMA图表"""
        try:
            import plotly.graph_objects as go

            # 计算SMA
            price_data_copy = price_data.copy()
            # 确保close列是数值类型，处理Decimal类型
            price_data_copy['close'] = pd.to_numeric(price_data_copy['close'], errors='coerce')
            price_data_copy['SMA'] = price_data_copy['close'].rolling(window=sma_period).mean()

            # 创建图表 - 使用data.index作为x轴，与其他图表保持一致
            fig = go.Figure()

            # 添加收盘价线
            fig.add_trace(go.Scatter(
                x=price_data_copy.index,
                y=price_data_copy['close'],
                name='收盘价',
                line=dict(color='blue', width=2)
            ))

            # 添加SMA线
            fig.add_trace(go.Scatter(
                x=price_data_copy.index,
                y=price_data_copy['SMA'],
                name=f'SMA({sma_period})',
                line=dict(color='red', width=2)
            ))

            # 设置图表布局
            fig.update_layout(
                title=f'收盘价与SMA({sma_period})对比图',
                xaxis_title='时间',
                yaxis_title='价格',
                hovermode='x unified',
                legend=dict(x=0, y=1),
                height=500
            )

            # 显示图表
            st.plotly_chart(fig, key="sma_chart", use_container_width=True)

            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                current_price = price_data_copy['close'].iloc[-1]
                st.metric("当前收盘价", f"{current_price:.2f}")

            with col2:
                current_sma = price_data_copy['SMA'].iloc[-1]
                if not pd.isna(current_sma):
                    st.metric(f"SMA({sma_period})", f"{current_sma:.2f}")
                else:
                    st.metric(f"SMA({sma_period})", "数据不足")

            with col3:
                if not pd.isna(current_sma):
                    diff = current_price - current_sma
                    diff_pct = (diff / current_sma) * 100
                    st.metric("价格偏离", f"{diff:.2f} ({diff_pct:+.2f}%)")
                else:
                    st.metric("价格偏离", "数据不足")

        except Exception as e:
            st.error(f"绘制SMA图表时出错: {str(e)}")