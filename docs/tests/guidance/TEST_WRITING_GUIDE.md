# 测试编写指南

## 测试设计原则

### 1. 测试用例应覆盖的场景

每个指标函数的测试应包含以下场景：

#### a) 基本功能测试
验证函数在正常参数下能正确计算

```python
def test_xxx_function_basic():
    """测试XXX函数基本功能"""
    data = setup_test_data()
    parser = RuleParser(data, create_mock_indicator_service())

    # 正常参数调用
    result = parser.evaluate_at("close > XXX(close, 参数)", index)
    assert result == True
```

#### b) 边界条件测试
测试参数的边界值

```python
def test_xxx_function_boundary():
    """测试XXX函数边界条件"""
    # 测试最小值、最大值、零值等边界情况
    result = parser.evaluate_at("close > XXX(close, 0, 5)", index)
    assert result == True
```

#### c) 参数验证测试
验证参数错误时的异常处理

```python
def test_xxx_function_invalid_params():
    """测试XXX函数参数验证"""
    # 参数超出范围
    with pytest.raises(SyntaxError, match="参数必须在x到y之间"):
        parser.evaluate_at("close > XXX(close, 超出范围的值)", index)

    # 参数数量错误
    with pytest.raises(SyntaxError, match="XXX需要n个参数"):
        parser.evaluate_at("XXX(close, 参数不足)", index)
```

#### d) 不同数据列测试
验证函数对不同数据列的支持

```python
def test_xxx_function_different_series():
    """测试XXX函数对不同数据列的支持"""
    data = pd.DataFrame({
        'close': [...],
        'high': [...],
        'low': [...],
        'volume': [...]
    })

    # 测试不同列
    assert parser.evaluate_at("close > XXX(close, ...)", index)
    assert parser.evaluate_at("volume > XXX(volume, ...)", index)
```

#### e) 组合条件测试
验证函数在复杂条件中的使用

```python
def test_xxx_function_in_complex_condition():
    """测试XXX函数在复杂条件中的使用"""
    # 结合其他指标使用
    rule = "(close > XXX(close, ...)) & (close > SMA(close, 5))"
    assert parser.evaluate_at(rule, index)
```

## 测试数据创建规范

### OHLCV 标准数据
```python
def setup_ohlcv_data():
    """创建标准OHLCV测试数据

    Returns:
        包含 open, high, low, close, volume 列的DataFrame
    """
    return pd.DataFrame({
        'open': [9.5, 10.5, 11.5, 12.5, 13.5],
        'high': [10.5, 11.5, 12.5, 13.5, 14.5],
        'low': [9.0, 10.0, 11.0, 12.0, 13.0],
        'close': [10.0, 11.0, 12.0, 13.0, 14.0],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })
```

### 数据要求
- 包含完整的 OHLCV 列
- 数据量应足够覆盖测试场景（至少5-10行）
- 使用递增/递减的数值便于验证

## 断言编写规范

### 1. 使用描述性断言消息
```python
# 好
assert result == True, "close=50应大于中位数30"

# 不好
assert result == True
```

### 2. 验证条件表达式
测试应该是完整的条件表达式，而不是单独的函数调用：

```python
# 正确 - 测试条件表达式
result = parser.evaluate_at("close > Q(close, 0.5, 5)", 4)
assert result == True

# 不推荐 - 直接测试函数（evaluate_at会转换为bool）
# result = parser.evaluate_at("Q(close, 0.5, 5)", 4)
```

### 3. 使用 pytest.raises 测试异常
```python
# 匹配异常类型和消息
with pytest.raises(SyntaxError, match="分位数必须在0到1之间"):
    parser.evaluate_at("Q(close, 1.5, 5)", 4)
```

## 测试函数命名规范

```python
# 格式：test_<功能>_<场景>
def test_xxx_function_basic():           # 基本功能
def test_xxx_function_boundary():        # 边界条件
def test_xxx_function_invalid_params():  # 参数验证
def test_xxx_function_in_condition():    # 条件中使用
def test_xxx_function_different_series(): # 不同数据列
```

## 文档字符串规范

每个测试函数应有清晰的文档字符串：

```python
def test_q_function_in_open_condition():
    """测试Q函数在开仓条件中的使用

    场景：验证Q函数可以用于开仓条件判断
    条件：close > Q(close, 0.2, 10)
    预期：返回True
    """
```

## 运算符优先级注意事项

使用逻辑运算符时，必须使用括号明确优先级：

```python
# 正确
rule = "(close > Q(close, 0.2, 10)) & (close > SMA(close, 5))"

# 错误 - 由于运算符优先级，会被错误解析
rule = "close > Q(close, 0.2, 10) & close > SMA(close, 5)"
```

## 测试独立性

- 每个测试用例应独立运行，不依赖其他测试
- 使用 `setup` 函数创建独立的测试数据
- 避免使用共享状态
