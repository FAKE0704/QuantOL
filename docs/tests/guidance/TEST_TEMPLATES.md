# 测试模板示例

## 指标函数测试模板

当新增技术指标函数时，使用以下模板创建测试文件：

```python
"""测试 <函数名> 指标函数 - 模拟实际开仓/平仓条件"""
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


def test_xxx_function_basic():
    """测试XXX函数基本功能"""
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

    # 基本功能测试
    rule = "close > XXX(close, 参数1, 参数2)"
    result = parser.evaluate_at(rule, 10)
    assert result == True, "测试条件应满足"


def test_xxx_function_complex_condition():
    """测试XXX函数在复杂条件中的使用"""
    data = pd.DataFrame({
        'close': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0],
        'open': [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5],
        'high': [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 20.5],
        'low': [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 复杂开仓条件：结合多个指标（注意使用括号）
    open_rule = "(close > XXX(close, ...)) & (close > SMA(close, 5))"
    result = parser.evaluate_at(open_rule, 10)
    assert result == True, "复杂条件应满足"


def test_xxx_function_boundary_conditions():
    """测试XXX函数边界条件"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
        'open': [9.5, 19.5, 29.5, 39.5, 49.5],
        'high': [10.5, 20.5, 30.5, 40.5, 50.5],
        'low': [9.0, 19.0, 29.0, 39.0, 49.0],
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 测试边界值（如0、最小值、最大值等）
    result = parser.evaluate_at("close > XXX(close, 边界值, 5)", 4)
    assert result == True, "边界条件测试应通过"


def test_xxx_function_different_series():
    """测试XXX函数对不同数据列的支持"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
        'high': [15.0, 25.0, 35.0, 45.0, 55.0],
        'low': [5.0, 15.0, 25.0, 35.0, 45.0],
        'volume': [100, 200, 300, 400, 500]
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 对不同列进行测试
    result = parser.evaluate_at("close > XXX(close, ...)", 4)
    assert result == True, "close列测试应通过"

    result = parser.evaluate_at("volume > XXX(volume, ...)", 4)
    assert result == True, "volume列测试应通过"


def test_xxx_function_invalid_params():
    """测试XXX函数参数验证"""
    data = pd.DataFrame({
        'close': [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 参数超出范围
    with pytest.raises(SyntaxError, match="参数错误提示"):
        parser.evaluate_at("close > XXX(close, 超出范围的值)", 4)

    # 周期小于等于0
    with pytest.raises(SyntaxError, match="周期必须为正整数"):
        parser.evaluate_at("close > XXX(close, ..., 0)", 4)

    # 参数数量错误
    with pytest.raises(SyntaxError, match="XXX需要n个参数"):
        parser.evaluate_at("close > XXX(close, 参数不足)", 4)

    with pytest.raises(SyntaxError, match="XXX需要n个参数"):
        parser.evaluate_at("close > XXX(close, ..., 参数过多)", 4)


def test_xxx_function_different_windows():
    """测试XXX函数不同窗口大小"""
    data = pd.DataFrame({
        'close': [i * 1.0 for i in range(10, 21)],  # 10到20
    })
    mock_service = create_mock_indicator_service()
    parser = RuleParser(data, mock_service)

    # 短窗口
    result = parser.evaluate_at("close > XXX(close, ..., 5)", 10)
    assert result == True, "短窗口测试应通过"

    # 长窗口
    result = parser.evaluate_at("close > XXX(close, ..., 10)", 10)
    assert result == True, "长窗口测试应通过"


if __name__ == "__main__":
    pytest.main([__file__])
```

## 使用模板的步骤

1. **复制模板**
   ```bash
   cp docs/tests/guidage/TEST_TEMPLATES.md tests/core/strategy/test_indicator_xxx.py
   ```

2. **替换占位符**
   - `<函数名>` → 实际函数名（如 `Q`、`SMA`）
   - `XXX` → 大写函数名
   - `参数1, 参数2` → 实际参数

3. **实现具体测试逻辑**
   - 根据函数特性编写测试数据
   - 设置正确的预期结果
   - 添加函数特定的验证

4. **运行测试**
   ```bash
   uv run pytest tests/core/strategy/test_indicator_xxx.py -v
   ```

## 实际示例

参考 `tests/core/strategy/test_indicator_q.py` 查看完整实现示例。
