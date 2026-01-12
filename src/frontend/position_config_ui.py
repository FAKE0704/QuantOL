import streamlit as st

class PositionConfigUI:
    """仓位配置UI组件，负责仓位相关配置的界面渲染"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_position_strategy_ui(self) -> None:
        """渲染仓位策略配置UI"""
        st.subheader("💰 仓位管理策略")

        # 获取动态 key 后缀（用于在加载配置后强制刷新 widget）
        key_suffix = self.session_state.get('_position_key_suffix', '')

        # 获取仓位策略值（优先从加载配置的临时标记获取）
        if '_load_position_strategy' in self.session_state:
            position_strategy_type = self.session_state._load_position_strategy
            del self.session_state._load_position_strategy
        else:
            position_strategy_type = getattr(self.session_state.backtest_config, 'position_strategy_type', 'fixed_percent')

        # 映射到显示选项
        strategy_to_display = {
            "fixed_percent": "固定比例",
            "kelly": "凯利公式",
            "martingale": "马丁格尔"
        }

        # 计算索引
        strategy_options = ["固定比例", "凯利公式", "马丁格尔"]
        try:
            default_display = strategy_to_display.get(position_strategy_type, "固定比例")
            index = strategy_options.index(default_display)
        except ValueError:
            index = 0

        # 仓位策略选择
        position_strategy = st.selectbox(
            "仓位策略",
            options=strategy_options,
            index=index,
            key=f"position_strategy_{key_suffix}"
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
            self._render_fixed_percent_ui(key_suffix)
        elif position_strategy == "凯利公式":
            self._render_kelly_ui(key_suffix)
        elif position_strategy == "马丁格尔":
            self._render_martingale_ui(key_suffix)

    def _render_fixed_percent_ui(self, key_suffix: str = '') -> None:
        """渲染固定比例策略UI"""
        # 获取参数值（优先从加载配置的临时标记获取）
        if '_load_fixed_percent' in self.session_state:
            percent = self.session_state._load_fixed_percent
            del self.session_state._load_fixed_percent
        elif hasattr(self.session_state.backtest_config, 'position_strategy_params') and self.session_state.backtest_config.position_strategy_params:
            percent = self.session_state.backtest_config.position_strategy_params.get('percent', 10.0) * 100.0
        else:
            percent = 10.0

        percent = st.slider(
            "仓位比例",
            min_value=0.0,
            max_value=100.0,
            value=percent,
            step=0.01,
            format="%.2f%%",
            key=f"fixed_percent_slider_{key_suffix}"
        )

        # 转换为小数格式存储
        percent_decimal = percent / 100.0

        self.session_state.backtest_config.position_strategy_params = {
            "percent": percent_decimal
        }

        # 使用markdown来更清晰地显示当前值
        st.markdown(f"**当前仓位比例**: {percent:.2f}%")

    def _render_kelly_ui(self, key_suffix: str = '') -> None:
        """渲染凯利公式策略UI"""
        # 获取参数值（优先从加载配置的临时标记获取）
        if hasattr(self.session_state.backtest_config, 'position_strategy_params') and self.session_state.backtest_config.position_strategy_params:
            params = self.session_state.backtest_config.position_strategy_params
            win_rate = params.get('win_rate', 0.6)
            win_loss_ratio = params.get('win_loss_ratio', 1.5)
            max_percent = params.get('max_percent', 0.25)
        else:
            win_rate = 0.6
            win_loss_ratio = 1.5
            max_percent = 0.25

        col1, col2 = st.columns(2)

        with col1:
            win_rate = st.slider(
                "预估胜率",
                min_value=0.0,
                max_value=100.0,
                value=win_rate * 100.0,
                step=0.01,
                format="%.2f%%",
                key=f"kelly_win_rate_slider_{key_suffix}"
            )

        with col2:
            win_loss_ratio = st.slider(
                "预估盈亏比",
                min_value=0.1,
                max_value=5.0,
                value=win_loss_ratio,
                step=0.1,
                key=f"kelly_win_loss_ratio_slider_{key_suffix}"
            )

        max_percent = st.slider(
            "最大仓位限制",
            min_value=0.0,
            max_value=50.0,
            value=max_percent * 100.0,
            step=0.01,
            format="%.2f%%",
            key=f"kelly_max_percent_slider_{key_suffix}"
        )

        self.session_state.backtest_config.position_strategy_params = {
            "win_rate": win_rate / 100.0,
            "win_loss_ratio": win_loss_ratio,
            "max_percent": max_percent / 100.0
        }

        # 使用更清晰的显示方式
        st.markdown(f"**当前配置**:")
        st.markdown(f"- **胜率**: {win_rate:.2f}%")
        st.markdown(f"- **盈亏比**: {win_loss_ratio:.1f}")
        st.markdown(f"- **最大仓位**: {max_percent:.2f}%")

    def _render_martingale_ui(self, key_suffix: str = '') -> None:
        """渲染马丁格尔策略UI"""
        # 获取参数值（优先从加载配置的临时标记获取）
        if hasattr(self.session_state.backtest_config, 'position_strategy_params') and self.session_state.backtest_config.position_strategy_params:
            params = self.session_state.backtest_config.position_strategy_params
            multiplier = params.get('multiplier', 2.0)
            max_doubles = params.get('max_doubles', 5)
            base_percent = params.get('base_percent', 0.05)
        else:
            multiplier = 2.0
            max_doubles = 5
            base_percent = 0.05

        multiplier = st.slider(
            "加倍系数",
            min_value=1.0,
            max_value=5.0,
            value=multiplier,
            step=0.1,
            key=f"martingale_multiplier_slider_{key_suffix}"
        )

        max_doubles = st.slider(
            "最大加倍次数",
            min_value=1,
            max_value=10,
            value=max_doubles,
            key=f"martingale_max_doubles_slider_{key_suffix}"
        )

        base_percent = st.slider(
            "基础仓位比例",
            min_value=0.0,
            max_value=20.0,
            value=base_percent * 100.0,
            step=0.01,
            format="%.2f%%",
            key=f"martingale_base_percent_slider_{key_suffix}"
        )

        self.session_state.backtest_config.position_strategy_params = {
            "multiplier": multiplier,
            "max_doubles": max_doubles,
            "base_percent": base_percent / 100.0
        }

        # 使用更清晰的显示方式
        st.markdown(f"**当前配置**:")
        st.markdown(f"- **基础仓位**: {base_percent:.2f}%")
        st.markdown(f"- **加倍系数**: {multiplier:.1f}")
        st.markdown(f"- **最大加倍次数**: {max_doubles}次")

    def render_basic_config_ui(self) -> None:
        """渲染基础配置UI"""
        st.subheader("⚙️ 基础配置")

        # 获取动态 key 后缀（用于在加载配置后强制刷新 widget）
        key_suffix = self.session_state.get('_basic_config_key_suffix', '')

        # 从配置对象获取初始值
        config = self.session_state.backtest_config
        initial_capital = getattr(config, 'initial_capital', 1000000)
        commission_rate = getattr(config, 'commission_rate', 0.0005)
        slippage = getattr(config, 'slippage', 0.0)
        min_lot_size = getattr(config, 'min_lot_size', 100)

        col1, col2 = st.columns(2)

        with col1:
            # 初始资金配置
            initial_capital = st.number_input(
                "初始资金",
                min_value=1000,
                max_value=100000000,
                value=initial_capital,
                step=10000,
                format="%d",
                key=f"initial_capital_{key_suffix}"
            )

            # 手续费率配置
            commission_rate = st.number_input(
                "单笔手续费率",
                min_value=0.0,
                max_value=0.1,
                value=commission_rate,
                step=0.0001,
                format="%.4f",
                key=f"commission_rate_{key_suffix}"
            )

        with col2:
            # 滑点配置
            slippage = st.number_input(
                "滑点率",
                min_value=0.0,
                max_value=0.1,
                value=slippage,
                step=0.0001,
                format="%.4f",
                key=f"slippage_{key_suffix}"
            )

            # 最小交易手数
            min_lot_size = st.number_input(
                "最小交易手数",
                min_value=1,
                max_value=1000,
                value=min_lot_size,
                step=1,
                key=f"min_lot_size_{key_suffix}"
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