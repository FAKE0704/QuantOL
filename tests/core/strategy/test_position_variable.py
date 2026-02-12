"""
测试POSITION变量在规则解析中的使用

验证：
1. POSITION == 0 能够正确识别无持仓状态
2. POSITION > 0 能够正确识别有持仓状态
3. 包含POSITION的规则表达式能够正确解析
4. 规则策略能够根据POSITION生成正确的信号
"""

import pytest
import pandas as pd
import numpy as np
from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.indicators import IndicatorService
from src.core.portfolio.portfolio import PortfolioManager
from src.core.portfolio.portfolio_interface import Position
from src.core.strategy.position_strategy import FixedPercentPositionStrategy
from src.core.strategy.rule_based_strategy import RuleBasedStrategy
from src.core.strategy.signal_types import SignalType


def create_mock_indicator_service():
    """创建模拟指标服务"""
    mock_service = IndicatorService()

    # Mock SMA函数
    def mock_sma(data, period, index=None):
        if index is None:
            return data['close'].rolling(window=period).mean()
        else:
            return data['close'].iloc[max(0, index - period + 1):index + 1].mean()

    mock_service.calculate_indicator = lambda data, indicator_name, **kwargs: mock_sma(data, kwargs.get('period', 5))
    return mock_service


def create_portfolio_manager_with_position(symbol: str, quantity: int = 0, avg_cost: float = 10.0):
    """创建带有指定持仓的投资组合管理器"""
    position_strategy = FixedPercentPositionStrategy(percent=0.1)
    portfolio_manager = PortfolioManager(initial_capital=100000, position_strategy=position_strategy)

    if quantity > 0:
        portfolio_manager.update_position(
            symbol=symbol,
            quantity=quantity,
            price=avg_cost,
            commission=0
        )

    return portfolio_manager


def test_position_variable_equals_zero():
    """测试 POSITION == 0 的条件"""
    # 创建测试数据
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': pd.date_range('2024-01-01', periods=20),
        'close': np.linspace(10.0, 20.0, 20),
        'high': np.linspace(10.5, 20.5, 20),
        'low': np.linspace(9.5, 19.5, 20),
        'volume': [1000] * 20
    })

    # 创建无持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=0)

    # 创建规则解析器
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service, portfolio_manager=portfolio_manager)
    parser.current_index = 10

    # 测试 POSITION == 0
    result = parser.evaluate_at('POSITION == 0', 10)
    assert result == True, "无持仓时 POSITION == 0 应该返回 True"

    # 测试 POSITION > 0
    result = parser.evaluate_at('POSITION > 0', 10)
    assert result == False, "无持仓时 POSITION > 0 应该返回 False"


def test_position_variable_greater_than_zero():
    """测试 POSITION > 0 的条件"""
    # 创建测试数据
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': pd.date_range('2024-01-01', periods=20),
        'close': np.linspace(10.0, 20.0, 20),
        'high': np.linspace(10.5, 20.5, 20),
        'low': np.linspace(9.5, 19.5, 20),
        'volume': [1000] * 20
    })

    # 创建有持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=1000, avg_cost=10.0)

    # 创建规则解析器
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service, portfolio_manager=portfolio_manager)
    parser.current_index = 10

    # 测试 POSITION == 0
    result = parser.evaluate_at('POSITION == 0', 10)
    assert result == False, "有持仓时 POSITION == 0 应该返回 False"

    # 测试 POSITION > 0
    result = parser.evaluate_at('POSITION > 0', 10)
    assert result == True, "有持仓时 POSITION > 0 应该返回 True"


def test_position_with_open_rule():
    """测试包含POSITION的开仓规则"""
    # 创建测试数据
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': pd.date_range('2024-01-01', periods=20),
        'close': np.linspace(10.0, 20.0, 20),
        'high': np.linspace(10.5, 20.5, 20),
        'low': np.linspace(9.5, 19.5, 20),
        'volume': [1000] * 20
    })

    # 创建无持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=0)

    # 创建规则解析器
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service, portfolio_manager=portfolio_manager)
    parser.parse('(POSITION == 0) & (close > 15)')

    # 在索引10处，close应该大于15
    parser.current_index = 10
    assert parser.evaluate_at('(POSITION == 0) & (close > 15)', 10) == True


def test_position_with_buy_rule():
    """测试包含POSITION的加仓规则"""
    # 创建测试数据
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': pd.date_range('2024-01-01', periods=20),
        'close': np.linspace(10.0, 20.0, 20),
        'high': np.linspace(10.5, 20.5, 20),
        'low': np.linspace(9.5, 19.5, 20),
        'volume': [1000] * 20
    })

    # 创建有持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=1000, avg_cost=10.0)

    # 创建规则解析器
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service, portfolio_manager=portfolio_manager)
    parser.parse('(POSITION > 0) & (close > 15)')

    # 在索引10处，close应该大于15
    parser.current_index = 10
    assert parser.evaluate_at('(POSITION > 0) & (close > 15)', 10) == True


def test_rule_based_strategy_with_position():
    """测试规则策略根据持仓状态自动选择规则"""
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=20)
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': dates,
        'close': np.linspace(10.0, 20.0, 20),
        'high': np.linspace(10.5, 20.5, 20),
        'low': np.linspace(9.5, 19.5, 20),
        'volume': [1000] * 20,
        'combined_time': dates  # 添加combined_time列
    })

    # 创建无持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=0)

    # 创建指标服务
    mock_service = create_mock_indicator_service()

    # 创建规则策略（不需要在规则中写POSITION条件）
    strategy = RuleBasedStrategy(
        Data=data,
        name="测试策略",
        indicator_service=mock_service,
        open_rule_expr='close > 15',   # 开仓规则：只写技术条件
        buy_rule_expr='close > 15',    # 加仓规则：只写技术条件
        portfolio_manager=portfolio_manager
    )

    # 测试无持仓时应该生成OPEN信号（open_rule生效）
    signal = strategy.generate_signals(current_index=10)
    assert signal is not None, "无持仓且条件满足时应该生成信号"
    assert signal.signal_type == SignalType.OPEN, "无持仓时应该生成OPEN信号"

    # 添加持仓
    portfolio_manager.update_position('sh.600000', 1000, 15.0, 0)

    # 测试有持仓时应该生成BUY信号（buy_rule生效）
    signal = strategy.generate_signals(current_index=10)
    assert signal is not None, "有持仓且条件满足时应该生成信号"
    assert signal.signal_type == SignalType.BUY, "有持仓时应该生成BUY信号"


def test_position_variable_value_accuracy():
    """测试POSITION变量返回的值是否准确"""
    # 创建测试数据
    data = pd.DataFrame({
        'code': ['sh.600000'] * 20,
        'date': pd.date_range('2024-01-01', periods=20),
        'close': [10.0] * 20,
        'high': [10.5] * 20,
        'low': [9.5] * 20,
        'volume': [1000] * 20
    })

    # 创建有1000股持仓的投资组合管理器
    portfolio_manager = create_portfolio_manager_with_position('sh.600000', quantity=1000, avg_cost=10.0)

    # 创建规则解析器
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service, portfolio_manager=portfolio_manager)
    parser.current_index = 10

    # 测试包含POSITION的比较表达式
    result = parser.evaluate_at('POSITION > 500', 10)
    assert result == True, "POSITION(1000) > 500 应该返回 True"

    result = parser.evaluate_at('POSITION > 1500', 10)
    assert result == False, "POSITION(1000) > 1500 应该返回 False"

    result = parser.evaluate_at('POSITION == 1000', 10)
    assert result == True, "POSITION == 1000 应该返回 True"

    result = parser.evaluate_at('POSITION >= 1000', 10)
    assert result == True, "POSITION >= 1000 应该返回 True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
