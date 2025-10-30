import streamlit as st
from src.core.strategy.backtesting import BacktestConfig
from typing import Dict, Any

class BacktestConfigManager:
    """回测配置管理类，负责配置的创建、验证和会话状态管理"""

    def __init__(self, session_state):
        self.session_state = session_state

    def create_default_config(self) -> BacktestConfig:
        """创建默认回测配置"""
        return BacktestConfig(
            start_date="20250401",
            end_date="20250430",
            target_symbol="sh.600000",
            frequency="d",
            initial_capital=100000,
            commission_rate=0.0003,
            strategy_type="月定投",
            position_strategy_type="fixed_percent",
            position_strategy_params={"percent": 0.1}
        )

    def initialize_session_config(self):
        """初始化会话状态中的配置对象"""
        if 'backtest_config' not in self.session_state:
            self.session_state.backtest_config = self.create_default_config()

    def update_config_from_ui(self, config_key: str, value: Any):
        """根据UI输入更新配置对象"""
        if hasattr(self.session_state.backtest_config, config_key):
            setattr(self.session_state.backtest_config, config_key, value)

    def get_config(self) -> BacktestConfig:
        """获取当前配置对象"""
        return self.session_state.backtest_config

    def validate_config(self, config: BacktestConfig) -> bool:
        """验证配置参数的合法性"""
        # 基本参数验证
        if config.initial_capital <= 0:
            st.error("初始资金必须大于0")
            return False

        if config.commission_rate < 0:
            st.error("交易佣金不能为负数")
            return False

        # 日期验证
        try:
            start_date = config.start_date
            end_date = config.end_date
            if start_date > end_date:
                st.error("开始日期不能晚于结束日期")
                return False
        except:
            st.error("日期格式错误")
            return False

        # 多符号模式验证
        if config.is_multi_symbol():
            symbols = config.get_symbols()
            if not symbols:
                st.error("多符号模式需要至少选择一个股票")
                return False

        return True

    def save_ui_settings_to_session(self):
        """保存UI设置到会话状态"""
        # 保存初始资金和佣金率
        if 'last_initial_capital' not in self.session_state:
            self.session_state.last_initial_capital = 100000
        if 'last_commission_rate' not in self.session_state:
            self.session_state.last_commission_rate = 0.03

    def render_basic_config_ui(self):
        """渲染基础配置UI组件"""
        config = self.get_config()

        # 初始资金输入
        initial_capital = st.number_input(
            "初始资金(元)",
            min_value=10000,
            value=self.session_state.get('last_initial_capital', 100000),
            key="initial_capital_input"
        )
        config.initial_capital = initial_capital

        # 交易佣金输入
        commission_rate = st.number_input(
            "交易佣金(%)",
            min_value=0.0,
            max_value=1.0,
            value=self.session_state.get('last_commission_rate', 0.03),
            key="commission_rate_input"
        )
        config.commission_rate = commission_rate / 100

        # 更新会话状态
        self.session_state.last_initial_capital = initial_capital
        self.session_state.last_commission_rate = commission_rate

    def render_date_config_ui(self):
        """渲染日期配置UI组件"""
        config = self.get_config()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", key="start_date_input_global", value="2025-04-01")
            config.start_date = start_date.strftime("%Y%m%d")
        with col2:
            end_date = st.date_input("结束日期", key="end_date_input_global")
            config.end_date = end_date.strftime("%Y%m%d")

    def render_frequency_config_ui(self):
        """渲染频率配置UI组件"""
        config = self.get_config()

        frequency_options = {
            "5": "5分钟", "15": "15分钟", "30": "30分钟", "60": "60分钟",
            "120": "120分钟", "d": "日线", "w": "周线", "m": "月线", "y": "年线"
        }

        frequency = st.selectbox(
            "频率",
            options=list(frequency_options.keys()),
            format_func=lambda x: frequency_options[x],
            key="frequency_select_global"
        )
        config.frequency = frequency

    def render_position_strategy_ui(self):
        """渲染仓位策略配置UI组件"""
        config = self.get_config()

        # 仓位策略类型选择
        position_strategy_type = st.selectbox(
            "仓位策略类型",
            options=["fixed_percent", "kelly", "martingale"],
            format_func=lambda x: "固定比例" if x == "fixed_percent" else "凯利公式" if x == "kelly" else "马丁策略",
            key="position_strategy_select"
        )
        config.position_strategy_type = position_strategy_type

        # 根据策略类型显示不同的参数配置
        if position_strategy_type == "fixed_percent":
            percent = st.slider(
                "固定仓位比例(%)",
                min_value=1, max_value=100, value=10,
                key="fixed_percent_slider"
            )
            config.position_strategy_params = {"percent": percent / 100}

        elif position_strategy_type == "kelly":
            col1, col2, col3 = st.columns(3)
            with col1:
                win_rate = st.slider("策略胜率(%)", min_value=1, max_value=99, value=50)
            with col2:
                win_loss_ratio = st.slider("盈亏比", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
            with col3:
                max_percent = st.slider("最大仓位限制(%)", min_value=1, max_value=100, value=25)

            config.position_strategy_params = {
                "win_rate": win_rate / 100,
                "win_loss_ratio": win_loss_ratio,
                "max_percent": max_percent / 100
            }

        elif position_strategy_type == "martingale":
            col1, col2 = st.columns(2)
            with col1:
                initial_ratio = st.slider("初始开仓资金比例(%)", min_value=1.0, max_value=10.0, value=0.01, step=0.01)
            with col2:
                multiplier = st.slider("加仓倍数", min_value=1.0, max_value=10.0, value=2.0, step=0.1)

            config.position_strategy_params = {
                "initial_ratio": initial_ratio / 100,
                "multiplier": multiplier,
                "clear_on_insufficient": True
            }