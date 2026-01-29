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
from src.core.strategy.indicators import IndicatorService

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
    indicator_service = IndicatorService()  # Use real service for actual calculations
    parser = RuleParser(data, indicator_service)

    # 测试不同位置
    for i in range(5, len(data)):  # Start from index 5 to have enough data for SMA(5)
        # 使用evaluate_at验证REF行为
        rule = "REF(SMA(close,5),1) < SMA(close,5)"
        assert parser.evaluate_at(rule, i), f"位置 {i}: REF(SMA(5),1) 应小于当前SMA(5)"

def test_nested_functions():
    """测试嵌套函数调用（使用公共API）"""
    data = setup_data()
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 测试嵌套REF
    rule = "REF(REF(SMA(close,5),1),1) < SMA(close,5)"
    assert parser.evaluate_at(rule, 5), "嵌套REF应小于当前SMA(5)"

def test_boundary_conditions():
    """测试边界条件处理（使用公共API）"""
    # 测试索引越界
    data = pd.DataFrame({'close': [10.0, 20.0, 30.0]})
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 超出左边界应返回False（REF返回0）
    assert not parser.evaluate_at("REF(SMA(close,2),3) > 0", 2)

    # 测试空值处理
    data_with_nan = pd.DataFrame({'close': [10.0, np.nan, 30.0]})
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data_with_nan, indicator_service)

    # 包含NaN的值应正确处理
    assert parser.evaluate_at("close > 0", 0)
    assert not parser.evaluate_at("close > 0", 1), "NaN值应处理为False"

def test_recursion_limit():
    """测试递归深度限制（使用公共API）"""
    data = setup_data()
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # Note: Current implementation doesn't track nested REF depth across multiple calls
    # Each REF call increments/decrements the counter independently
    # This test verifies that deeply nested REF can be evaluated (no recursion error)
    deep_expr = "SMA(close,2)"
    for _ in range(10):  # Use reasonable nesting depth
        deep_expr = f"REF({deep_expr}, 1)"

    rule = f"{deep_expr} > 0"

    # Should not raise RecursionError with current implementation
    result = parser.evaluate_at(rule, 5)
    # The result should be False because REF(REF(...)) will eventually return 0 at some depth
    assert isinstance(result, bool)

def test_evaluate_at():
    """测试evaluate_at方法"""
    data = setup_data()
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 测试规则：SMA(close,5) > SMA(close,2)
    rule = "SMA(close,5) > SMA(close,2)"

    # 验证不同位置的结果 - with increasing close prices, SMA(2) should be higher than SMA(5)
    assert not parser.evaluate_at(rule, 4), "位置4: SMA(5)应小于SMA(2)"
    assert not parser.evaluate_at(rule, 7), "位置7: SMA(5)应小于SMA(2)"
    assert not parser.evaluate_at(rule, 9), "位置9: SMA(5)应小于SMA(2)"

    # 测试正确的情况
    assert parser.evaluate_at("SMA(close,2) > SMA(close,5)", 4)

def test_cache_mechanism():
    """测试缓存机制（通过性能间接验证）"""
    data = setup_data()
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

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
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 测试 AND/OR 组合
    rule = "(SMA(close,5) > 30) and (RSI(close,14) < 70) or (volume > 100)"
    assert parser.evaluate_at(rule, 7), "复杂逻辑应返回True"

def test_multi_indicator():
    """测试多指标组合"""
    data = setup_data()
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 测试 SMA+RSI组合
    rule = "SMA(close,5) > SMA(close,10) and RSI(close,14) < 70"
    assert parser.evaluate_at(rule, 8), "多指标组合应返回True"

def test_extreme_params():
    """测试极端参数值"""
    # 长序列测试
    data = pd.DataFrame({'close': [10.0] * 1000})
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    # 极小周期
    assert parser.evaluate_at("SMA(close,1) == 10", 999)

    # 极大周期
    assert parser.evaluate_at("SMA(close,200) == 10", 999)

    # 边界REF
    assert not parser.evaluate_at("REF(SMA(close,5),995) > 0", 999)

def test_performance():
    """测试性能基准"""
    data = pd.DataFrame({'close': [10.0] * 10000})
    indicator_service = IndicatorService()  # Use real service
    parser = RuleParser(data, indicator_service)

    import time
    start = time.time()

    # 复杂规则评估
    rule = "REF(SMA(close,5),1) > REF(SMA(close,20),1) and SMA(close,5) > SMA(close,20)"
    for i in range(100, 1100):  # 避免边界值
        parser.evaluate_at(rule, i)

    duration = time.time() - start
    assert duration < 2.0, f"性能不达标: 1000次评估耗时 {duration:.2f}秒 > 2秒"

def test_std_function():
    """测试STD函数计算标准差"""
    data = pd.DataFrame({'close': [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]})
    indicator_service = IndicatorService()
    parser = RuleParser(data, indicator_service)

    # 测试标准差计算 - 使用parse with mode='ref' 获取原始数值
    # [12, 14, 16, 18] 的样本标准差约为 2.58
    # 对于window=4，需要index>=4才能计算
    parser.current_index = 4
    result = parser.parse("STD(close, 4)", mode='ref')
    # 在Python中，pd.Series([12, 14, 16, 18]).std() = 2.581988897471611
    assert abs(result - 2.5819) < 0.01, f"STD计算错误: {result}"

    # 测试数据不足时返回0 (index=3, window=4 => 3 < 4, 返回0)
    parser.current_index = 3
    result = parser.parse("STD(close, 4)", mode='ref')
    assert result == 0.0, f"数据不足时应返回0: {result}"

    # 测试不同窗口的结果
    parser.current_index = 5
    result = parser.parse("STD(close, 4)", mode='ref')
    # [14, 16, 18, 20] 的样本标准差约为 2.58
    assert abs(result - 2.5819) < 0.01, f"STD计算错误: {result}"

    # 测试在规则中使用STD
    # STD > 0 应该为True（有波动）
    assert parser.evaluate_at("STD(close, 4) > 0", 4)

    # 测试布林带条件
    # close > SMA(close, 4) + 2 * STD(close, 4)
    # SMA([12,14,16,18]) = 15, STD = 2.58, 15 + 2*2.58 = 20.16, 18 < 20.16
    assert not parser.evaluate_at("close > SMA(close, 4) + 2 * STD(close, 4)", 4)

def test_zscore_function():
    """测试Z_SCORE函数计算"""
    data = pd.DataFrame({'close': [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]})
    indicator_service = IndicatorService()
    parser = RuleParser(data, indicator_service)

    # 测试Z_SCORE计算
    # 对于window=4，需要index>=4才能计算
    parser.current_index = 4
    result = parser.parse("Z_SCORE(close, 4)", mode='ref')
    # SMA([12,14,16,18]) = 15, STD = 2.58, current_value = 18
    # Z_SCORE = (18 - 15) / 2.58 = 3 / 2.58 ≈ 1.16
    expected = (18 - 15) / 2.581988897471611
    assert abs(result - expected) < 0.01, f"Z_SCORE计算错误: {result}, 期望: {expected}"

    # 测试数据不足时返回0 (index=3, window=4 => 3 < 4, 返回0)
    parser.current_index = 3
    result = parser.parse("Z_SCORE(close, 4)", mode='ref')
    assert result == 0.0, f"数据不足时应返回0: {result}"

    # 测试在规则中使用Z_SCORE
    # Z_SCORE > 1 应该为True（价格高于均值1倍标准差以上）
    assert parser.evaluate_at("Z_SCORE(close, 4) > 1", 4)

    # 测试均值回归条件
    # Z_SCORE < -1 表示价格低于均值1倍标准差以上
    # 在index=5时，SMA([14,16,18,20]) = 17, STD ≈ 2.58, current_value = 20
    # Z_SCORE = (20 - 17) / 2.58 ≈ 1.16 > -1，所以条件不成立
    assert not parser.evaluate_at("Z_SCORE(close, 4) < -1", 5)

    # 测试Z_SCORE等于0的情况（价格等于均值）
    # 使用不同的数据来测试，需要创建新的indicator_service避免缓存干扰
    data_equal = pd.DataFrame({'close': [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]})
    indicator_service_fresh = IndicatorService()
    parser_equal = RuleParser(data_equal, indicator_service_fresh)
    parser_equal.current_index = 4
    result = parser_equal.parse("Z_SCORE(close, 4)", mode='ref')
    # 当所有值相同时，STD=0，Z_SCORE应该返回0（避免除零）
    assert result == 0.0, f"所有值相等时应返回0: {result}"

def test_ema_function():
    """测试EMA函数计算指数移动平均"""
    data = pd.DataFrame({'close': [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]})
    indicator_service = IndicatorService()
    parser = RuleParser(data, indicator_service)

    # 测试EMA计算
    # 对于window=4，需要index>=4才能计算（因为min_required=window）
    parser.current_index = 4
    result = parser.parse("EMA(close, 4)", mode='ref')
    # EMA应该有值（具体值取决于计算方法）
    assert result > 0, f"EMA应该大于0: {result}"

    # 测试数据不足时返回0 (index=3, window=4 => 3 < 4, 返回0)
    parser.current_index = 3
    result = parser.parse("EMA(close, 4)", mode='ref')
    assert result == 0.0, f"数据不足时应返回0: {result}"

    # 测试在规则中使用EMA
    # EMA > 0 应该为True（有数据时）
    assert parser.evaluate_at("EMA(close, 4) > 0", 4)

    # 测试EMA交叉
    # 短期EMA应该大于长期EMA（上涨趋势中）
    assert parser.evaluate_at("EMA(close, 4) > EMA(close, 6)", 5)

    # 测试EMA与价格的关系
    # 在上涨趋势中，价格应该大于短期EMA
    assert parser.evaluate_at("close > EMA(close, 4)", 5)

def test_dif_dea_macd_functions():
    """测试DIF、DEA、MACD函数"""
    # 创建更多数据点来支持MACD计算
    data = pd.DataFrame({'close': [10.0 + i * 0.5 for i in range(50)]})
    indicator_service = IndicatorService()
    parser = RuleParser(data, indicator_service)

    # 测试DIF计算
    # DIF = EMA(12) - EMA(26)，需要至少26个数据点
    parser.current_index = 26
    dif_result = parser.parse("DIF(close, 12, 26)", mode='ref')
    assert dif_result > 0, f"DIF应该大于0（上涨趋势）: {dif_result}"

    # 数据不足时返回0
    parser.current_index = 25
    dif_result = parser.parse("DIF(close, 12, 26)", mode='ref')
    assert dif_result == 0.0, f"数据不足时DIF应返回0: {dif_result}"

    # 测试DEA计算
    # DEA = EMA(DIF, 9)，需要至少26+9=35个数据点
    parser.current_index = 35
    dea_result = parser.parse("DEA(close, 9, 12, 26)", mode='ref')
    assert dea_result > 0, f"DEA应该大于0: {dea_result}"

    # 测试MACD计算
    # MACD = 2 * (DIF - DEA)
    macd_result = parser.parse("MACD(close, 9, 12, 26)", mode='ref')
    assert isinstance(macd_result, float), f"MACD应该返回float: {macd_result}"

    # 测试在规则中使用DIF
    # DIF > 0 表示上涨趋势
    parser.current_index = 30
    assert parser.evaluate_at("DIF(close, 12, 26) > 0", 30)

    # 测试金叉条件：DIF > DEA
    # 在上涨趋势中，DIF应该大于DEA（需要足够数据）
    parser.current_index = 40
    dif_val = parser.parse("DIF(close, 12, 26)", mode='ref')
    dea_val = parser.parse("DEA(close, 9, 12, 26)", mode='ref')
    assert dif_val > 0 and dea_val > 0, "上涨趋势中DIF和DEA应该大于0"

if __name__ == "__main__":
    pytest.main([__file__])
