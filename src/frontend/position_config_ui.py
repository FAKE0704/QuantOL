import streamlit as st

class PositionConfigUI:
    """仓位配置UI组件，负责仓位相关配置的界面渲染"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_position_strategy_ui(self) -> None:
        """渲染仓位策略配置UI"""
        st.subheader("💰 仓位管理策略")

        # 仓位策略选择
        position_strategy = st.selectbox(
            "仓位策略",
            options=["固定比例", "凯利公式", "马丁格尔"],
            key="position_strategy"
        )

        # 映射到配置值
        strategy_map = {
            "固定比例": "fixed_percent",
            "凯利公式": "kelly",
            "马丁格尔": "martingale"
        }

        self.session_state.backtest_config.position_strategy_type = strategy_map[position_strategy]

        # 根据选择的策略显示相应参数
        if position_strategy == "固定比例":
            self._render_fixed_percent_ui()
        elif position_strategy == "凯利公式":
            self._render_kelly_ui()
        elif position_strategy == "马丁格尔":
            self._render_martingale_ui()

    def _render_fixed_percent_ui(self) -> None:
        """渲染固定比例策略UI"""
        # 使用session_state来确保滑动条值在组件重渲染时保持同步
        if 'fixed_percent_value' not in self.session_state:
            self.session_state.fixed_percent_value = 10.0

        percent = st.slider(
            "仓位比例",
            min_value=0.0,
            max_value=100.0,
            value=self.session_state.fixed_percent_value,
            step=0.01,
            format="%.2f%%",
            key="fixed_percent_slider"
        )

        # 更新session_state中的值
        self.session_state.fixed_percent_value = percent

        # 转换为小数格式存储
        percent_decimal = percent / 100.0

        self.session_state.backtest_config.position_strategy_params = {
            "percent": percent_decimal
        }

        # 使用markdown来更清晰地显示当前值
        st.markdown(f"**当前仓位比例**: {percent:.2f}%")

    def _render_kelly_ui(self) -> None:
        """渲染凯利公式策略UI"""
        # 初始化session_state值
        if 'kelly_win_rate_value' not in self.session_state:
            self.session_state.kelly_win_rate_value = 0.6
        if 'kelly_win_loss_ratio_value' not in self.session_state:
            self.session_state.kelly_win_loss_ratio_value = 1.5
        if 'kelly_max_percent_value' not in self.session_state:
            self.session_state.kelly_max_percent_value = 0.25

        col1, col2 = st.columns(2)

        with col1:
            win_rate = st.slider(
                "预估胜率",
                min_value=0.0,
                max_value=100.0,
                value=self.session_state.kelly_win_rate_value * 100.0,
                step=0.01,
                format="%.2f%%",
                key="kelly_win_rate_slider"
            )
            self.session_state.kelly_win_rate_value = win_rate / 100.0

        with col2:
            win_loss_ratio = st.slider(
                "预估盈亏比",
                min_value=0.1,
                max_value=5.0,
                value=self.session_state.kelly_win_loss_ratio_value,
                step=0.1,
                key="kelly_win_loss_ratio_slider"
            )
            self.session_state.kelly_win_loss_ratio_value = win_loss_ratio

        max_percent = st.slider(
            "最大仓位限制",
            min_value=0.0,
            max_value=50.0,
            value=self.session_state.kelly_max_percent_value * 100.0,
            step=0.01,
            format="%.2f%%",
            key="kelly_max_percent_slider"
        )
        self.session_state.kelly_max_percent_value = max_percent / 100.0

        self.session_state.backtest_config.position_strategy_params = {
            "win_rate": win_rate,
            "win_loss_ratio": win_loss_ratio,
            "max_percent": max_percent
        }

        # 使用更清晰的显示方式
        st.markdown(f"**当前配置**:")
        st.markdown(f"- **胜率**: {win_rate*100:.2f}%")
        st.markdown(f"- **盈亏比**: {win_loss_ratio:.1f}")
        st.markdown(f"- **最大仓位**: {max_percent*100:.2f}%")

    def _render_martingale_ui(self) -> None:
        """渲染马丁格尔策略UI"""
        # 初始化session_state值
        if 'martingale_multiplier_value' not in self.session_state:
            self.session_state.martingale_multiplier_value = 2.0
        if 'martingale_max_doubles_value' not in self.session_state:
            self.session_state.martingale_max_doubles_value = 5
        if 'martingale_base_percent_value' not in self.session_state:
            self.session_state.martingale_base_percent_value = 0.05

        multiplier = st.slider(
            "加倍系数",
            min_value=1.0,
            max_value=5.0,
            value=self.session_state.martingale_multiplier_value,
            step=0.1,
            key="martingale_multiplier_slider"
        )
        self.session_state.martingale_multiplier_value = multiplier

        max_doubles = st.slider(
            "最大加倍次数",
            min_value=1,
            max_value=10,
            value=self.session_state.martingale_max_doubles_value,
            key="martingale_max_doubles_slider"
        )
        self.session_state.martingale_max_doubles_value = max_doubles

        base_percent = st.slider(
            "基础仓位比例",
            min_value=0.0,
            max_value=20.0,
            value=self.session_state.martingale_base_percent_value * 100.0,
            step=0.01,
            format="%.2f%%",
            key="martingale_base_percent_slider"
        )
        self.session_state.martingale_base_percent_value = base_percent / 100.0

        self.session_state.backtest_config.position_strategy_params = {
            "multiplier": multiplier,
            "max_doubles": max_doubles,
            "base_percent": base_percent
        }

        # 使用更清晰的显示方式
        st.markdown(f"**当前配置**:")
        st.markdown(f"- **基础仓位**: {base_percent*100:.2f}%")
        st.markdown(f"- **加倍系数**: {multiplier:.1f}")
        st.markdown(f"- **最大加倍次数**: {max_doubles}次")

    def render_basic_config_ui(self) -> None:
        """渲染基础配置UI"""
        st.subheader("⚙️ 基础配置")

        col1, col2 = st.columns(2)

        with col1:
            # 初始资金配置
            initial_capital = st.number_input(
                "初始资金",
                min_value=1000,
                max_value=100000000,
                value=1000000,
                step=10000,
                format="%d",
                key="initial_capital"
            )

            # 手续费率配置
            commission_rate = st.number_input(
                "单笔手续费率",
                min_value=0.0,
                max_value=0.1,
                value=0.0005,
                step=0.0001,
                format="%.4f",
                key="commission_rate"
            )

        with col2:
            # 滑点配置
            slippage = st.number_input(
                "滑点率",
                min_value=0.0,
                max_value=0.1,
                value=0.0,
                step=0.0001,
                format="%.4f",
                key="slippage"
            )

            # 最小交易手数
            min_lot_size = st.number_input(
                "最小交易手数",
                min_value=1,
                max_value=1000,
                value=100,
                step=1,
                key="min_lot_size"
            )

        # 更新配置
        config = self.session_state.backtest_config
        config.initial_capital = initial_capital
        config.commission_rate = commission_rate
        config.slippage = slippage
        config.min_lot_size = min_lot_size

        st.info(f"初始资金: ¥{initial_capital:,.0f}, 手续费: {commission_rate*100:.2f}%, 滑点: {slippage*100:.2f}%")

    def render_config_summary(self) -> None:
        """渲染仓位配置摘要"""
        config = self.session_state.backtest_config

        st.subheader("📋 仓位配置摘要")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**初始资金**: ¥{config.initial_capital:,.2f}")
            st.info(f"**手续费率**: {config.commission_rate*100:.4f}%")

        with col2:
            st.info(f"**滑点率**: {config.slippage*100:.4f}%")

            position_strategy = getattr(config, 'position_strategy_type', 'fixed_percent')
            position_map = {
                'fixed_percent': '固定比例',
                'kelly': '凯利公式',
                'martingale': '马丁格尔'
            }
            st.info(f"**仓位策略**: {position_map.get(position_strategy, position_strategy)}")