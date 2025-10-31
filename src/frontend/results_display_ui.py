import streamlit as st
import pandas as pd
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
            # 使用ChartService绘制技术指标
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

        # 显示原始数据
        if "equity_records" in results:
            st.subheader("净值记录")
            equity_df = pd.DataFrame(results["equity_records"])
            st.dataframe(equity_df, use_container_width=True)

        if "trades" in results and results["trades"]:
            st.subheader("交易记录")
            trades_df = pd.DataFrame(results["trades"])
            st.dataframe(trades_df, use_container_width=True)

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