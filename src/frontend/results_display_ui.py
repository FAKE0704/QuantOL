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
            chart_service.draw_equity_and_allocation(equity_data)
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

            # 获取价格数据以提取规则结果
            price_data = results.get("price_data")
            if price_data is not None and not price_data.empty:
                # 查找规则结果列
                rule_columns = self._find_rule_columns(price_data)

                # 将规则结果合并到净值记录中
                equity_df = self._merge_rule_results_to_equity(equity_df, price_data, rule_columns)

            st.dataframe(equity_df, use_container_width=True)

        if "trades" in results and results["trades"]:
            st.subheader("交易记录")
            trades_df = pd.DataFrame(results["trades"])
            st.dataframe(trades_df, use_container_width=True)

    def _find_rule_columns(self, price_data: pd.DataFrame) -> dict:
        """查找规则结果列并返回映射关系"""
        rule_columns = {}
        rule_type_mapping = {}

        # 添加调试信息
        st.write(f"**调试信息:** 价格数据列名: {list(price_data.columns)}")

        # 排除价格数据列（避免将OHLCV误认为规则列）
        price_columns = {'open', 'high', 'low', 'close', 'volume', 'time', 'date', 'datetime', 'signal'}

        # 详细分析每个列
        st.write("**详细列分析:**")

        # 专门搜索复合规则相关的列
        compound_rule_keywords = ['&', '|', 'and', 'or', '>', '<', '>=', '<=', '==', '!=']

        for col in price_data.columns:
            col_lower = col.lower()
            is_price_col = col_lower in price_columns

            # 检查是否包含规则关键字
            has_open = any(keyword in col_lower for keyword in ['open', '开仓'])
            has_close = any(keyword in col_lower for keyword in ['close', '清仓'])
            has_buy = any(keyword in col_lower for keyword in ['buy', '加仓'])
            has_sell = any(keyword in col_lower for keyword in ['sell', '平仓'])

            # 检查是否包含复合规则的特征
            has_compound = any(keyword in col for keyword in compound_rule_keywords)

            # 检查是否为规则结果列
            sample_values = price_data[col].dropna().head(5)
            is_rule_col = self._is_rule_result_column(sample_values)

            # 如果是规则列，显示True的计数
            true_count = 0
            if is_rule_col and not sample_values.empty:
                try:
                    true_count = sample_values.sum() if sample_values.dtype in [bool, np.bool_] else (sample_values.astype(bool).sum())
                except:
                    pass

            st.write(f"  • {col}: 价格列={is_price_col}, 包含关键字(开仓={has_open},清仓={has_close},加仓={has_buy},平仓={has_sell}), 复合规则={has_compound}, 规则列={is_rule_col}, True数量={true_count}")
            if not sample_values.empty:
                st.write(f"    样本值: {sample_values.tolist()}, 类型: {sample_values.dtype}")

            # 如果列名看起来像复合规则，显示更多信息
            if has_compound and is_rule_col:
                st.write(f"    ⚠️ 发现可能的复合规则列: {col}")
                # 显示这个列的一些True值对应的行索引
                true_indices = price_data[price_data[col] == True].head(5).index.tolist()
                if true_indices:
                    st.write(f"    前5个True的索引: {true_indices}")

        # 查找四种规则的判断结果列（放宽条件）
        for col in price_data.columns:
            col_lower = col.lower()

            # 跳过价格数据列
            if col_lower in price_columns:
                continue

            # 检查该列是否包含布尔值或数值类型的规则结果
            sample_values = price_data[col].dropna().head(10)
            if not self._is_rule_result_column(sample_values):
                continue

            # 检查列名是否包含规则相关的关键词（放宽条件）
            if any(keyword in col_lower for keyword in ['open', '开仓']) and '开仓' not in rule_type_mapping.values():
                rule_columns[col] = '开仓'
                rule_type_mapping[col] = '开仓'
                st.write(f"✓ 找到开仓规则列: {col} (样本: {sample_values.tolist()[:3]})")

            elif any(keyword in col_lower for keyword in ['close', '清仓']) and '清仓' not in rule_type_mapping.values():
                rule_columns[col] = '清仓'
                rule_type_mapping[col] = '清仓'
                st.write(f"✓ 找到清仓规则列: {col} (样本: {sample_values.tolist()[:3]})")

            elif any(keyword in col_lower for keyword in ['buy', '加仓']) and '加仓' not in rule_type_mapping.values():
                rule_columns[col] = '加仓'
                rule_type_mapping[col] = '加仓'
                st.write(f"✓ 找到加仓规则列: {col} (样本: {sample_values.tolist()[:3]})")

            elif any(keyword in col_lower for keyword in ['sell', '平仓']) and '平仓' not in rule_type_mapping.values():
                rule_columns[col] = '平仓'
                rule_type_mapping[col] = '平仓'
                st.write(f"✓ 找到平仓规则列: {col} (样本: {sample_values.tolist()[:3]})")

            # 如果四种规则都找到了，就停止搜索
            if len(rule_columns) == 4:
                break

        st.write(f"**调试信息:** 找到的规则列: {rule_columns}")

        # 如果规则列不足4个，尝试其他方式识别
        if len(rule_columns) < 4:
            st.write(f"⚠️ 只找到 {len(rule_columns)} 个规则列，尝试其他识别方式...")

            # 寻找所有布尔值列，按顺序分配给缺失的规则类型
            missing_rules = []
            if '开仓' not in rule_type_mapping.values():
                missing_rules.append('开仓')
            if '清仓' not in rule_type_mapping.values():
                missing_rules.append('清仓')
            if '加仓' not in rule_type_mapping.values():
                missing_rules.append('加仓')
            if '平仓' not in rule_type_mapping.values():
                missing_rules.append('平仓')

            rule_col_count = 0
            for col in price_data.columns:
                if col_lower in price_columns:
                    continue
                if col in rule_columns:
                    continue

                sample_values = price_data[col].dropna().head(10)
                if self._is_rule_result_column(sample_values):
                    if rule_col_count < len(missing_rules):
                        rule_type = missing_rules[rule_col_count]
                        rule_columns[col] = rule_type
                        rule_type_mapping[col] = rule_type
                        st.write(f"✓ 自动分配 {rule_type} 规则列: {col} (样本: {sample_values.tolist()[:3]})")
                        rule_col_count += 1

        # 特别检查开仓规则相关的列
        if '开仓' in rule_type_mapping.values():
            open_rule_col = None
            for col, rule_type in rule_type_mapping.items():
                if rule_type == '开仓':
                    open_rule_col = col
                    break

            if open_rule_col:
                st.write(f"🔍 深入分析开仓规则列: {open_rule_col}")
                open_rule_data = price_data[open_rule_col]
                true_count = open_rule_data.sum()
                st.write(f"   总True数量: {true_count}")

                # 查找可能的子条件列
                st.write("   查找可能的子条件列:")
                sub_conditions = []
                for col in price_data.columns:
                    if ('REF(SMA' in col and 'close' in col) or ('SMA' in col and 'close' in col):
                        if col != open_rule_col and self._is_rule_result_column(price_data[col].dropna().head(10)):
                            sub_conditions.append(col)
                            true_count_sub = price_data[col].sum()
                            st.write(f"     • {col}: True数量={true_count_sub}")

                if sub_conditions:
                    st.write(f"   找到 {len(sub_conditions)} 个可能的子条件列")

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
            st.write("⚠️ 调试信息: 没有找到规则列，无法合并")
            return equity_df

        st.write(f"📊 调试信息: 开始合并规则结果到净值记录")
        st.write(f"   净值记录行数: {len(equity_df)}, 价格数据行数: {len(price_data)}")

        # 确保时间戳列名一致
        equity_time_col = 'timestamp'
        price_time_col = price_data.index.name if price_data.index.name else 'index'

        # 检查价格数据是否有日期时间列
        datetime_col = None
        for col in price_data.columns:
            if 'time' in col.lower() or 'date' in col.lower() or col == 'datetime':
                datetime_col = col
                break

        # 如果净值记录有timestamp列，将其转换为datetime类型以便匹配
        if equity_time_col in equity_df.columns:
            equity_df[equity_time_col] = pd.to_datetime(equity_df[equity_time_col])

        if datetime_col:
            # 使用价格数据中的日期时间列
            price_data_index = pd.to_datetime(price_data[datetime_col])
            st.write(f"   找到价格数据时间列: {datetime_col}")
        else:
            # 检查价格数据索引是否已经是数值型（0, 1, 2...），如果是则按行号匹配
            if price_data.index.dtype in ['int64', 'int32']:
                st.write(f"   价格数据使用数值索引，将按行号匹配净值记录")
                # 使用行号匹配的逻辑
                return self._merge_by_row_number(equity_df, price_data, rule_columns)
            else:
                # 尝试将索引转换为datetime
                price_data_index = pd.to_datetime(price_data.index)

        st.write(f"   净值记录时间范围: {equity_df[equity_time_col].min()} 到 {equity_df[equity_time_col].max()}")
        st.write(f"   价格数据时间范围: {price_data_index.min()} 到 {price_data_index.max()}")

        match_count = 0
        # 为每个规则列创建匹配函数
        for original_col, display_name in rule_columns.items():
            # 创建规则结果列，初始值为空
            equity_df[f'规则_{display_name}'] = None

            # 检查规则列的数据类型和示例值
            sample_values = price_data[original_col].dropna().head(5)
            st.write(f"   规则列 '{original_col}' 样本值: {sample_values.tolist()}, 数据类型: {price_data[original_col].dtype}")

            # 遍历净值记录的每一行
            for idx, equity_row in equity_df.iterrows():
                equity_time = equity_row[equity_time_col]

                # 在价格数据中找到最接近的时间点
                closest_idx = None
                min_time_diff = None

                for price_idx, price_time in enumerate(price_data_index):
                    time_diff = abs((price_time - equity_time).total_seconds())
                    if min_time_diff is None or time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_idx = price_idx

                # 如果找到匹配的时间点，获取规则结果
                if closest_idx is not None and min_time_diff < 86400:  # 24小时内
                    rule_result = price_data.iloc[closest_idx][original_col]

                    # 将布尔值或数值转换为更易读的格式
                    if isinstance(rule_result, (bool, np.bool_)):  # 包含 numpy.bool_
                        equity_df.at[idx, f'规则_{display_name}'] = '触发' if rule_result else '未触发'
                        match_count += 1
                    elif isinstance(rule_result, (int, float, np.integer, np.floating)):  # 包含 numpy 数值类型
                        equity_df.at[idx, f'规则_{display_name}'] = '触发' if rule_result > 0 else '未触发'
                        match_count += 1
                    else:
                        st.write(f"   ⚠️ 未识别的规则结果类型: {type(rule_result)}, 值: {rule_result}")

        st.write(f"✅ 调试信息: 成功匹配 {match_count} 个规则结果")
        return equity_df

    def _merge_by_row_number(self, equity_df: pd.DataFrame, price_data: pd.DataFrame, rule_columns: dict) -> pd.DataFrame:
        """按行号匹配合并规则结果到净值记录"""
        st.write(f"🔄 使用行号匹配方式合并数据")

        # 检查净值记录和价格数据的行数是否匹配
        min_rows = min(len(equity_df), len(price_data))
        st.write(f"   将匹配前 {min_rows} 行数据")

        match_count = 0
        # 为每个规则列创建匹配
        for original_col, display_name in rule_columns.items():
            # 创建规则结果列，初始值为空
            equity_df[f'规则_{display_name}'] = None

            # 检查规则列的数据类型和示例值
            sample_values = price_data[original_col].dropna().head(5)
            st.write(f"   规则列 '{original_col}' 样本值: {sample_values.tolist()}, 数据类型: {price_data[original_col].dtype}")

            # 按行号匹配
            for i in range(min_rows):
                rule_result = price_data.iloc[i][original_col]

                # 检查规则结果是否为布尔值（True/False）或可以解释为布尔值
                if isinstance(rule_result, (bool, np.bool_)):
                    equity_df.at[i, f'规则_{display_name}'] = '触发' if rule_result else '未触发'
                    match_count += 1
                elif isinstance(rule_result, (int, float, str, np.integer, np.floating)):
                    # 尝试将数值或字符串转换为布尔值判断
                    try:
                        if str(rule_result).lower() in ['true', '1', 'yes', 'on']:
                            equity_df.at[i, f'规则_{display_name}'] = '触发'
                            match_count += 1
                        elif str(rule_result).lower() in ['false', '0', 'no', 'off', '']:
                            equity_df.at[i, f'规则_{display_name}'] = '未触发'
                            match_count += 1
                        else:
                            # 对于数值，检查是否大于0
                            if float(rule_result) > 0:
                                equity_df.at[i, f'规则_{display_name}'] = '触发'
                                match_count += 1
                            elif float(rule_result) == 0:
                                equity_df.at[i, f'规则_{display_name}'] = '未触发'
                                match_count += 1
                    except (ValueError, TypeError):
                        st.write(f"   ⚠️ 无法解释规则结果: {rule_result} (类型: {type(rule_result)})")

        st.write(f"✅ 调试信息: 按行号成功匹配 {match_count} 个规则结果")
        return equity_df

    def render_debug_data_tab(self, results: Dict[str, Any]) -> None:
        """渲染调试数据标签页"""
        st.subheader("🐛 规则解析器调试数据")

        # 调试信息显示
        st.write("**调试信息:**")
        if "debug_data" in results:
            st.write(f"• debug_data键存在: 是")
            st.write(f"• debug_data内容: {list(results['debug_data'].keys()) if results['debug_data'] else '空'}")
        else:
            st.write(f"• debug_data键存在: 否")

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

            if show_columns:
                # 显示数据预览
                st.write(f"**数据预览 (最近20行):**")
                display_data = strategy_data[show_columns].tail(20)
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
            return pd.DataFrame(results["equity_records"])
        return None

    def _get_price_data(self, results: Dict[str, Any]) -> pd.DataFrame:
        """获取价格数据"""
        # 这里需要根据实际数据结构调整
        if "price_data" in results:
            return results["price_data"]
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