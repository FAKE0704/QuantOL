"""兼容性测试 - 事件类和策略接口API

测试覆盖：
- TradingDayEvent 参数兼容性
- StrategySignalEvent 参数兼容性
- BaseStrategy.handle_event() 方法签名
- OrderEvent, FillEvent 等事件类
- 策略接口变更检测
"""
import os
import sys
import pytest
import inspect
from datetime import datetime
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.event_bus.event_types import (
    TradingDayEvent,
    StrategySignalEvent,
    OrderEvent,
    FillEvent,
    StrategyScheduleEvent,
)
from src.core.strategy.strategy import BaseStrategy


# ============================================================================
# Test: TradingDayEvent Compatibility
# ============================================================================

def test_trading_day_event_no_price_param():
    """测试TradingDayEvent不接受price参数"""
    # 正确用法：只传timestamp
    event = TradingDayEvent(timestamp=datetime(2024, 1, 1))
    assert event.timestamp == datetime(2024, 1, 1)

    # 错误用法：传入price应该失败
    with pytest.raises(TypeError):
        event = TradingDayEvent(timestamp=datetime(2024, 1, 1), price=10.0)


def test_trading_day_event_is_first_day_param():
    """测试TradingDayEvent的is_first_day参数"""
    event = TradingDayEvent(
        timestamp=datetime(2024, 1, 1),
        is_first_day=True
    )
    assert event.is_first_day is True


# ============================================================================
# Test: StrategySignalEvent Compatibility
# ============================================================================

def test_strategy_signal_event_params():
    """测试StrategySignalEvent参数"""
    from src.core.strategy.signal_types import SignalType

    event = StrategySignalEvent(
        strategy_id='test_strategy',
        symbol='sh.600000',
        signal_type=SignalType.BUY,
        price=10.0,
        timestamp=datetime(2024, 1, 1),
        confidence=0.8
    )
    assert event.symbol == 'sh.600000'
    assert event.signal_type == SignalType.BUY


# ============================================================================
# Test: OrderEvent Compatibility
# ============================================================================

def test_order_event_params():
    """测试OrderEvent参数"""
    event = OrderEvent(
        timestamp=datetime(2024, 1, 1),
        strategy_id='test_strategy',
        symbol='sh.600000',
        direction='BUY',
        price=10.0,
        quantity=100
    )
    assert event.symbol == 'sh.600000'
    assert event.direction == 'BUY'
    assert event.quantity == 100


# ============================================================================
# Test: FillEvent Compatibility
# ============================================================================

def test_fill_event_params():
    """测试FillEvent参数"""
    event = FillEvent(
        order_id='order_123',
        symbol='sh.600000',
        direction='BUY',
        fill_price=10.0,
        fill_quantity=100,
        commission=3.0,
        timestamp=datetime(2024, 1, 1)
    )
    assert event.symbol == 'sh.600000'
    assert event.commission == 3.0


# ============================================================================
# Test: BaseStrategy.handle_event Signature
# ============================================================================

def test_base_strategy_handle_event_signature():
    """测试BaseStrategy.handle_event方法签名"""
    sig = inspect.signature(BaseStrategy.handle_event)
    params = list(sig.parameters.keys())

    # 应该包含self, engine, event
    assert 'self' in params
    assert 'engine' in params
    assert 'event' in params

    # 验证参数顺序
    assert params == ['self', 'engine', 'event']


def test_base_strategy_handle_event_is_sync():
    """测试BaseStrategy.handle_event是同步方法（非async）"""
    import inspect

    # 验证handle_event不是协程函数
    assert not inspect.iscoroutinefunction(BaseStrategy.handle_event), \
        "handle_event should be a synchronous method, not async"


def test_base_strategy_handle_event_call():
    """测试BaseStrategy.handle_event正确调用"""
    import pandas as pd

    class TestStrategy(BaseStrategy):
        def __init__(self, data, name):
            super().__init__(data, name)
            self.last_engine = None
            self.last_event = None

        def handle_event(self, engine, event):
            self.last_engine = engine
            self.last_event = event

    # 创建简单的测试数据
    data = pd.DataFrame({'close': [10.0, 11.0, 12.0]})
    strategy = TestStrategy(data, 'test_strategy')
    mock_engine = Mock()
    mock_event = Mock()

    # 正确调用方式
    strategy.handle_event(mock_engine, mock_event)

    assert strategy.last_engine == mock_engine
    assert strategy.last_event == mock_event


# ============================================================================
# Test: Strategy Interface Compatibility
# ============================================================================

def test_base_strategy_on_data_signature():
    """测试BaseStrategy.on_data方法签名"""
    if hasattr(BaseStrategy, 'on_data'):
        sig = inspect.signature(BaseStrategy.on_data)
        params = list(sig.parameters.keys())

        # on_data应该接受row和idx参数
        assert 'row' in params or 'data' in params
        assert 'idx' in params or 'index' in params


# ============================================================================
# Test: Event Class Field Compatibility
# ============================================================================

def test_event_class_has_timestamp():
    """测试所有事件类都有timestamp字段"""
    from src.core.strategy.signal_types import SignalType

    events = [
        (TradingDayEvent, {'timestamp': datetime(2024, 1, 1)}),
        (StrategySignalEvent, {
            'strategy_id': 'test',
            'symbol': 'sh.600000',
            'signal_type': SignalType.BUY,
            'price': 10.0,
            'timestamp': datetime(2024, 1, 1)
        }),
        (OrderEvent, {
            'timestamp': datetime(2024, 1, 1),
            'strategy_id': 'test',
            'symbol': 'sh.600000',
            'direction': 'BUY',
            'price': 10.0,
            'quantity': 100
        }),
        (FillEvent, {
            'order_id': 'order_123',
            'symbol': 'sh.600000',
            'direction': 'BUY',
            'fill_price': 10.0,
            'fill_quantity': 100,
            'commission': 3.0,
            'timestamp': datetime(2024, 1, 1)
        }),
    ]

    for event_class, params in events:
        event = event_class(**params)
        assert hasattr(event, 'timestamp')
        assert event.timestamp is not None


# ============================================================================
# Test: BacktestEngine Method Compatibility
# ============================================================================

def test_backtest_engine_has_run_method():
    """测试BacktestEngine有run方法"""
    from src.core.backtest.engine import BacktestEngine

    assert hasattr(BacktestEngine, 'run')
    assert callable(BacktestEngine.run)


def test_backtest_engine_no_run_multi_symbol():
    """测试BacktestEngine没有run_multi_symbol方法（已被移除）"""
    from src.core.backtest.engine import BacktestEngine

    # run_multi_symbol应该不存在（已被run替代）
    # 如果存在，应该发出警告
    if hasattr(BacktestEngine, 'run_multi_symbol'):
        pytest.warn("run_multi_symbol method should be removed, use run() instead")


def test_backtest_engine_has_get_results():
    """测试BacktestEngine有get_results方法"""
    from src.core.backtest.engine import BacktestEngine

    assert hasattr(BacktestEngine, 'get_results')
    assert callable(BacktestEngine.get_results)


# ============================================================================
# Test: BacktestStateService Method Compatibility
# ============================================================================

def test_backtest_state_service_has_get_backtest():
    """测试BacktestStateService有get_backtest方法"""
    from src.services.backtest_state_service import BacktestStateService

    assert hasattr(BacktestStateService, 'get_backtest')
    assert callable(BacktestStateService.get_backtest)


def test_backtest_state_service_no_get_result():
    """测试BacktestStateService没有get_result方法（已被重命名）"""
    from src.services.backtest_state_service import BacktestStateService

    # get_result应该不存在（已被get_backtest替代）
    # 如果存在，应该发出警告
    if hasattr(BacktestStateService, 'get_result'):
        pytest.warn("get_result method should be renamed to get_backtest")


# ============================================================================
# Test: API Router Method Compatibility
# ============================================================================

def test_results_router_uses_get_backtest():
    """测试results router使用get_backtest方法"""
    import ast
    import inspect

    from src.api.routers.backtest import results

    # 读取源代码
    source = inspect.getsource(results.get_backtest_results)

    # 验证使用的是get_backtest而不是get_result
    assert 'get_backtest' in source
    assert 'get_result(' not in source  # 确保没有调用get_result(
