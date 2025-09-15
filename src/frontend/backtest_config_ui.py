import streamlit as st
import pandas as pd
from typing import List, Tuple, Optional
from core.strategy.backtesting import BacktestConfig

class BacktestConfigUI:
    """回测配置UI组件，负责回测范围配置的界面渲染"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_date_config_ui(self) -> None:
        """渲染日期配置UI"""
        st.subheader("📅 回测日期范围")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=pd.to_datetime(self.session_state.backtest_config.start_date),
                key="backtest_start_date"
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=pd.to_datetime(self.session_state.backtest_config.end_date),
                key="backtest_end_date"
            )

        # 更新配置
        self.session_state.backtest_config.start_date = start_date.strftime('%Y-%m-%d')
        self.session_state.backtest_config.end_date = end_date.strftime('%Y-%m-%d')

    def render_frequency_config_ui(self) -> None:
        """渲染频率配置UI"""
        st.subheader("🔄 数据频率")

        frequency = st.selectbox(
            "数据频率",
            options=["日线", "周线", "月线"],
            index=0,
            key="data_frequency"
        )

        # 映射到实际频率值
        frequency_map = {"日线": "d", "周线": "w", "月线": "m"}
        self.session_state.backtest_config.frequency = frequency_map[frequency]

    def render_stock_selection_ui(self) -> List[Tuple[str, str]]:
        """渲染股票选择UI，返回选中的股票列表"""
        st.subheader("📈 选择交易标的")

        col1, col2 = st.columns([3, 1])
        selected_options = []

        with col1:
            # 初始化缓存
            if 'stock_cache' not in self.session_state or self.session_state.stock_cache is None:
                with st.spinner("正在加载股票列表..."):
                    try:
                        stock_list = self.session_state.db.get_stock_list()
                        self.session_state.stock_cache = [
                            (row['symbol'], f"{row['symbol']} - {row['name']}")
                            for _, row in stock_list.iterrows()
                        ]
                    except Exception as e:
                        st.error(f"加载股票列表失败: {e}")
                        self.session_state.stock_cache = []

            # 多选股票组件
            if self.session_state.stock_cache:
                selected_options = st.multiselect(
                    "选择股票（可多选）",
                    options=self.session_state.stock_cache,
                    format_func=lambda x: x[1],
                    key="selected_stocks"
                )
            else:
                st.warning("无法加载股票列表，请检查数据库连接")

        with col2:
            st.write("\n")
            if st.button("🔄 刷新列表", key="refresh_stock_list"):
                self.session_state.stock_cache = None
                st.rerun()

        return selected_options

    def render_config_summary(self) -> None:
        """渲染配置摘要"""
        config = self.session_state.backtest_config

        st.subheader("📋 配置摘要")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**回测期间**: {config.start_date} 至 {config.end_date}")
            st.info(f"**数据频率**: {'日线' if config.frequency == 'd' else '周线' if config.frequency == 'w' else '月线'}")

        with col2:
            st.info(f"**初始资金**: ¥{config.initial_capital:,.2f}")
            symbols = config.get_symbols()
            if len(symbols) > 1:
                st.info(f"**多股票模式**: {len(symbols)} 只股票")
            else:
                st.info(f"**交易标的**: {symbols[0] if symbols else '未选择'}")