import os
import sys
import pandas as pd
import numpy as np
import pytest
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.rule_parser import RuleParser

def setup_data() -> pd.DataFrame:
    """创建标准测试数据"""
    return pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        'volume': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    })

# 创建模拟IndicatorService
def create_mock_indicator_service():
    mock_service = Mock()
    mock_service.calculate_indicator.return_value = 10.0  # 返回固定值
    return mock_service

def test_ref_function():
    """测试REF函数正确回溯历史值（使用公共API）"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 测试不同位置
    for i in range(1, len(data)):
        # 使用evaluate_at验证REF行为
        rule = f"REF(SMA(close,5),1) < SMA(close,5)"
        assert parser.evaluate_at(rule, i), f"位置 {i}: REF(SMA(5),1) 应小于当前SMA(5)"

def test_nested_functions():
    """测试嵌套函数调用（使用公共API）"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 测试嵌套REF
    rule = "REF(REF(SMA(close,5),1),1) < SMA(close,5)"
    assert parser.evaluate_at(rule, 5), "嵌套REF应小于当前SMA(5)"

def test_boundary_conditions():
    """测试边界条件处理（使用公共API）"""
    # 测试索引越界
    data = pd.DataFrame({'close': [10.0, 20.0, 30.0]})
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 超出左边界应返回False（REF返回0）
    assert not parser.evaluate_at("REF(SMA(close,2),3) > 0", 2)
    
    # 测试空值处理
    data_with_nan = pd.DataFrame({'close': [10.0, np.nan, 30.0]})
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data_with_nan, mock_service)
    
    # 包含NaN的值应正确处理
    assert parser.evaluate_at("close > 0", 0)
    assert not parser.evaluate_at("close > 0", 1), "NaN值应处理为False"

def test_recursion_limit():
    """测试递归深度限制（使用公共API）"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 创建深度嵌套表达式
    deep_expr = "SMA(close,2)"
    for _ in range(10):
        deep_expr = f"REF({deep_expr}, 1)"
    
    rule = f"{deep_expr} > 0"
    
    with pytest.raises(RecursionError):
        parser.evaluate_at(rule, 5)

def test_evaluate_at():
    """测试evaluate_at方法"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 测试规则：SMA(close,5) > SMA(close,2)
    rule = "SMA(close,5) > SMA(close,2)"
    
    # 验证不同位置的结果
    assert not parser.evaluate_at(rule, 4), "位置4: SMA(5)应小于SMA(2)"
    assert not parser.evaluate_at(rule, 7), "位置7: SMA(5)应小于SMA(2)"
    assert not parser.evaluate_at(rule, 9), "位置9: SMA(5)应小于SMA(2)"
    
    # 测试正确的情况
    assert parser.evaluate_at("SMA(close,2) > SMA(close,5)", 4)

def test_cache_mechanism():
    """测试缓存机制（通过性能间接验证）"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 第一次评估
    start_first = pd.Timestamp.now()
    parser.evaluate_at("SMA(close,5) > SMA(close,20)", 5)
    duration_first = (pd.Timestamp.now() - start_first).total_seconds()
    
    # 第二次评估（应使用缓存）
    start_second = pd.Timestamp.now()
    parser.evaluate_at("SMA(close,5) > SMA(close,20)", 5)
    duration_second = (pd.Timestamp.now() - start_second).total_seconds()
    
    assert duration_second < duration_first * 0.5, "缓存应显著提升性能"

def test_complex_logic():
    """测试复杂逻辑表达式"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 测试 AND/OR 组合
    rule = "(SMA(close,5) > 30) & (RSI(14) < 70) | (VOLUME > 100)"
    assert parser.evaluate_at(rule, 7), "复杂逻辑应返回True"

def test_multi_indicator():
    """测试多指标组合"""
    data = setup_data()
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 测试 SMA+RSI组合
    rule = "SMA(close,5) > SMA(close,10) & RSI(14) < 70"
    assert parser.evaluate_at(rule, 8), "多指标组合应返回True"

def test_extreme_params():
    """测试极端参数值"""
    # 长序列测试
    data = pd.DataFrame({'close': [10.0] * 1000})
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    # 极小周期
    assert parser.evaluate_at("SMA(close,1) == 10", 999)
    
    # 极大周期
    assert parser.evaluate_at("SMA(close,200) == 10", 999)
    
    # 边界REF
    assert not parser.evaluate_at("REF(SMA(close,5),995) > 0", 999)

def test_performance():
    """测试性能基准"""
    data = pd.DataFrame({'close': [10.0] * 10000})
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)
    
    import time
    start = time.time()
    
    # 复杂规则评估
    rule = "REF(SMA(close,5),1) > REF(SMA(close,20),1) & SMA(close,5) > SMA(close,20)"
    for i in range(100, 1100):  # 避免边界值
        parser.evaluate_at(rule, i)
    
    duration = time.time() - start
    assert duration < 2.0, f"性能不达标: 1000次评估耗时 {duration:.2f}秒 > 2秒"

if __name__ == "__main__":
    pytest.main([__file__])
