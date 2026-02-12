# 测试文件组织规范

## 目录结构

```
tests/
├── core/                    # 核心功能测试
│   └── strategy/           # 策略相关测试
│       ├── test_rule_parser.py           # 规则解析器测试
│       ├── test_indicator_xxx.py         # 指标函数测试（每个指标一个文件）
│       └── test_xxx_position_strategy.py # 仓位策略测试
├── integration/             # 集成测试
├── __init__.py
└── conftest.py             # pytest 配置（如需要）
```

## 文件命名规则

### 指标函数测试
- 格式：`test_indicator_<指标名>.py`
- 示例：
  - `test_indicator_sma.py` - SMA 指标测试
  - `test_indicator_rsi.py` - RSI 指标测试
  - `test_indicator_q.py` - Q 分位数函数测试

### 策略测试
- 格式：`test_<策略名>_strategy.py`
- 示例：
  - `test_position_strategy.py` - 仓位策略测试（包含 FixedPercent、Martingale、Kelly）

### 组件测试
- 格式：`test_<组件名>.py`
- 示例：
  - `test_rule_parser.py` - 规则解析器测试
  - `test_backtest_engine.py` - 回测引擎测试

## 新增测试流程

### 1. 新增指标函数测试

当实现新的技术指标函数时，创建独立的测试文件：

```bash
# 新增指标 ABC 的测试
touch tests/core/strategy/test_indicator_abc.py
```

### 2. 测试文件放置原则

- **一个指标一个文件**：每个技术指标函数应有独立的测试文件
- **按功能分组**：相关测试放在同一目录下
- **避免修改现有测试**：不要在已有测试文件中添加不相关的测试

### 3. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定目录的测试
uv run pytest tests/core/strategy/

# 运行单个测试文件
uv run pytest tests/core/strategy/test_indicator_q.py

# 运行单个测试用例
uv run pytest tests/core/strategy/test_indicator_q.py::test_q_function_basic -v

# 查看覆盖率
uv run pytest tests/core/strategy/test_indicator_q.py --cov=src.core.strategy.rule_parser --cov-report=term-missing:skip-covered
```

## 测试文件依赖

所有测试文件应包含以下导入和设置：

```python
import os
import sys
import pandas as pd
import pytest
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.indicators import IndicatorService
```

## 常见模式

### Mock IndicatorService
```python
def create_mock_indicator_service():
    """创建模拟IndicatorService"""
    mock_service = Mock()
    mock_service.calculate_indicator.return_value = 10.0
    return mock_service
```

### 标准测试数据
```python
def setup_ohlcv_data():
    """创建标准OHLCV测试数据"""
    return pd.DataFrame({
        'open': [9.5, 10.5, 11.5, 12.5, 13.5],
        'high': [10.5, 11.5, 12.5, 13.5, 14.5],
        'low': [9.0, 10.0, 11.0, 12.0, 13.0],
        'close': [10.0, 11.0, 12.0, 13.0, 14.0],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })
```
