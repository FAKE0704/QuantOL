"""测试 Q 分位数函数 - 模拟实际开仓/平仓条件"""
import os
import sys
import pandas as pd
import pytest
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.rule_parser import RuleParser


def create_mock_indicator_service():
    """创建模拟IndicatorService"""
    mock_service = Mock()
    mock_service.calculate_indicator.return_value = 10.0
    return mock_service


def test_q_function_in_open_condition():
    """测试Q函数在开仓条件中的使用"""
    # 创建模拟K线数据
    data = pd.DataFrame({
        'close': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0],
        'open': [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5],
        'high': [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5],
        'low': [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 开仓条件：收盘价高于10周期20%分位数
    open_rule = "close > Q(close, 0.2, 10)"
    result = parser.evaluate_at(open_rule, 10)  # 索引10位置，close=20
    assert result == True, "收盘价应高于20%分位数"


def test_q_function_complex_condition():
    """测试Q函数在复杂条件中的使用"""
    data = pd.DataFrame({
        'close': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0],
        'open': [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5],
        'high': [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5],
        'low': [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 复杂开仓条件：结合多个指标
    open_rule = "(close > Q(close, 0.2, 10)) & (close > SMA(close, 5))"
    result = parser.evaluate_at(open_rule, 10)
    assert result == True, "复杂条件应满足"


def test_q_function_boundary_conditions():
    """测试Q函数边界条件"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
        'open': [9.5, 19.5, 29.5, 39.5, 49.5],
        'high': [10.5, 20.5, 30.5, 40.5, 50.5],
        'low': [9.0, 19.0, 29.0, 39.0, 49.0],
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 0%分位数（最小值）
    result = parser.evaluate_at("close > Q(close, 0, 5)", 4)
    assert result == True, "close应大于0%分位数(最小值)"

    # 100%分位数（最大值）
    result = parser.evaluate_at("close >= Q(close, 1, 5)", 4)
    assert result == True, "close应等于100%分位数(最大值)"


def test_q_function_different_series():
    """测试Q函数对不同数据列的支持"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
        'high': [15.0, 25.0, 35.0, 45.0, 55.0],
        'low': [5.0, 15.0, 25.0, 35.0, 45.0],
        'volume': [100, 200, 300, 400, 500]
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 对 close 列计算分位数
    result = parser.evaluate_at("close > Q(close, 0.5, 5)", 4)
    assert result == True, "close列分位数测试应通过"

    # 对 volume 列计算分位数
    result = parser.evaluate_at("volume > Q(volume, 0.5, 5)", 4)
    assert result == True, "volume列分位数测试应通过"


def test_q_function_invalid_params():
    """测试Q函数参数验证"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 分位数超出范围
    with pytest.raises(SyntaxError, match="分位数必须在0到1之间"):
        parser.evaluate_at("close > Q(close, 1.5, 5)", 4)

    with pytest.raises(SyntaxError, match="分位数必须在0到1之间"):
        parser.evaluate_at("close > Q(close, -0.1, 5)", 4)

    # 周期小于等于0
    with pytest.raises(SyntaxError, match="周期必须为正整数"):
        parser.evaluate_at("close > Q(close, 0.5, 0)", 4)

    with pytest.raises(SyntaxError, match="周期必须为正整数"):
        parser.evaluate_at("close > Q(close, 0.5, -1)", 4)

    # 参数数量错误
    with pytest.raises(SyntaxError, match="Q需要3个参数"):
        parser.evaluate_at("close > Q(close, 0.5)", 4)

    with pytest.raises(SyntaxError, match="Q需要3个参数"):
        parser.evaluate_at("close > Q(close, 0.5, 5, 10)", 4)


def test_q_function_different_windows():
    """测试Q函数不同窗口大小"""
    data = pd.DataFrame({
        'close': [i * 1.0 for i in range(10, 21)],  # 10到20
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 短窗口
    result = parser.evaluate_at("close > Q(close, 0.5, 5)", 10)
    assert result == True, "短窗口分位数测试应通过"

    # 长窗口
    result = parser.evaluate_at("close > Q(close, 0.8, 10)", 10)
    assert result == True, "长窗口分位数测试应通过"


if __name__ == "__main__":
    pytest.main([__file__])
