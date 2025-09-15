import streamlit as st
from typing import Callable, Any, Dict
from core.strategy.backtesting import BacktestEngine
from core.strategy.event_handlers import handle_signal
from event_bus.event_types import StrategySignalEvent
from core.strategy.signal_types import SignalType

class CallbackServices:
    """回调服务，负责处理所有按钮回调和交互逻辑"""

    def __init__(self, session_state):
        self.session_state = session_state

    def create_backtest_callback(self) -> Callable[[], None]:
        """创建回测按钮回调"""
        def on_backtest_click():
            self.session_state.start_backtest_clicked = not self.session_state.start_backtest_clicked

        return on_backtest_click

    def create_refresh_callback(self, data_loader) -> Callable[[], None]:
        """创建刷新按钮回调"""
        async def on_refresh_click():
            self.session_state.stock_cache = None
            # 这里需要异步刷新，但Streamlit回调不支持async
            # 实际刷新逻辑在UI组件中处理

        return on_refresh_click

    def create_signal_handler(self, engine: BacktestEngine) -> Callable[[StrategySignalEvent], Any]:
        """创建信号处理回调"""
        def handle_signal_with_direction(event: StrategySignalEvent):
            # 保持向后兼容性：如果使用旧的direction方式，自动设置signal_type
            if not hasattr(event, 'signal_type') or event.signal_type is None:
                event.signal_type = SignalType.BUY if event.confidence > 0 else SignalType.SELL
            return handle_signal(event)

        return handle_signal_with_direction

    def register_event_handlers(self, engine: BacktestEngine) -> None:
        """注册事件处理器"""
        signal_handler = self.create_signal_handler(engine)
        engine.register_handler(StrategySignalEvent, signal_handler)

    def handle_backtest_completion(self, results: Dict[str, Any], success: bool = True) -> None:
        """处理回测完成回调"""
        if success:
            self.session_state.backtest_results = results
            self.session_state.backtest_completed = True
            self.session_state.backtest_error = None
        else:
            self.session_state.backtest_completed = False
            self.session_state.backtest_error = "回测执行失败"

    def handle_backtest_error(self, error: Exception) -> None:
        """处理回测错误回调"""
        self.session_state.backtest_completed = False
        self.session_state.backtest_error = str(error)
        st.error(f"回测执行错误: {error}")

    def reset_backtest_state(self) -> None:
        """重置回测状态"""
        self.session_state.start_backtest_clicked = False
        self.session_state.backtest_completed = False
        self.session_state.backtest_results = None
        self.session_state.backtest_error = None

    def create_rule_validation_callback(self, rule_group_manager) -> Callable[[], None]:
        """创建规则验证回调"""
        def on_validate_click():
            # 这里可以添加规则验证逻辑
            st.info("规则验证功能待实现")

        return on_validate_click

    def create_config_save_callback(self, config_manager) -> Callable[[], None]:
        """创建配置保存回调"""
        def on_save_click():
            try:
                config_manager.save_config()
                st.success("配置保存成功")
            except Exception as e:
                st.error(f"配置保存失败: {e}")

        return on_save_click

    def create_config_load_callback(self, config_manager) -> Callable[[], None]:
        """创建配置加载回调"""
        def on_load_click():
            try:
                config_manager.load_config()
                st.success("配置加载成功")
                st.rerun()
            except Exception as e:
                st.error(f"配置加载失败: {e}")

        return on_load_click