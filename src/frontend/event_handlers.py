import streamlit as st
from typing import Any, Dict
from core.strategy.backtesting import BacktestEngine
from event_bus.event_types import StrategySignalEvent, StrategyScheduleEvent
from core.strategy.event_handlers import handle_signal, handle_schedule
from core.strategy.signal_types import SignalType

class EventHandlers:
    """事件处理器，负责所有事件处理逻辑"""

    def __init__(self, session_state):
        self.session_state = session_state

    def create_signal_handler(self, engine: BacktestEngine) -> Any:
        """创建信号事件处理器"""
        def handle_signal_with_context(event: StrategySignalEvent):
            # 添加上下文信息
            event.current_index = engine.current_index
            event.total_steps = engine.total_steps

            # 保持向后兼容性
            if not hasattr(event, 'signal_type') or event.signal_type is None:
                event.signal_type = SignalType.BUY if event.confidence > 0 else SignalType.SELL

            # 更新进度
            self._update_progress(engine)

            return handle_signal(event)

        return handle_signal_with_context

    def create_schedule_handler(self, engine: BacktestEngine) -> Any:
        """创建调度事件处理器"""
        def handle_schedule_with_context(event: StrategyScheduleEvent):
            # 添加上下文信息
            event.current_index = engine.current_index
            event.total_steps = engine.total_steps

            # 更新进度
            self._update_progress(engine)

            return handle_schedule(event)

        return handle_schedule_with_context

    def _update_progress(self, engine: BacktestEngine) -> None:
        """更新回测进度"""
        if hasattr(engine, 'current_index') and hasattr(engine, 'total_steps'):
            progress = engine.current_index / engine.total_steps if engine.total_steps > 0 else 0
            self.session_state.backtest_progress = progress

            # 更新进度条（如果存在）
            if 'progress_bar' in self.session_state:
                self.session_state.progress_bar.progress(progress)

    def register_all_handlers(self, engine: BacktestEngine) -> None:
        """注册所有事件处理器"""
        # 注册信号处理器
        signal_handler = self.create_signal_handler(engine)
        engine.register_handler(StrategySignalEvent, signal_handler)

        # 注册调度处理器
        schedule_handler = self.create_schedule_handler(engine)
        engine.register_handler(StrategyScheduleEvent, schedule_handler)

    def handle_backtest_start(self, engine: BacktestEngine) -> None:
        """处理回测开始事件"""
        self.session_state.backtest_progress = 0
        self.session_state.backtest_running = True

        # 创建进度条
        self.session_state.progress_bar = st.progress(0)

    def handle_backtest_end(self, results: Dict[str, Any]) -> None:
        """处理回测结束事件"""
        self.session_state.backtest_progress = 1.0
        self.session_state.backtest_running = False

        # 更新进度条
        if 'progress_bar' in self.session_state:
            self.session_state.progress_bar.progress(1.0)

        # 存储结果
        self.session_state.backtest_results = results

    def handle_backtest_error(self, error: Exception) -> None:
        """处理回测错误事件"""
        self.session_state.backtest_running = False
        self.session_state.backtest_error = str(error)

        # 清除进度条
        if 'progress_bar' in self.session_state:
            self.session_state.progress_bar.empty()

    def cleanup_after_backtest(self) -> None:
        """回测后清理"""
        # 清理进度条
        if 'progress_bar' in self.session_state:
            self.session_state.progress_bar.empty()
            del self.session_state.progress_bar

        # 重置状态
        self.session_state.backtest_running = False
        self.session_state.backtest_progress = 0