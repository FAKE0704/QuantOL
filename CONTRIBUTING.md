# 贡献指南

感谢您对 Awesome QSys 项目的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试用例、功能建议等。

## 🎯 如何贡献

### 报告问题
如果您发现了bug或有功能建议，请通过以下方式报告：
1. 在 [GitHub Issues](https://github.com/FAKE0704/awesome-Qsys/issues) 中搜索是否已有相关问题
2. 如果没有找到相关issue，请创建新的issue
3. 清晰描述问题或建议，包括：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（Python版本、操作系统等）

### 提交代码
1. Fork 项目到您的账户
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

#### Python 代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 [Black](https://github.com/psf/black) 进行代码格式化
- 使用 [Flake8](https://flake8.pycqa.org/) 进行代码检查

#### 命名约定
- 类名：`CamelCase` (如 `BacktestEngine`)
- 函数名：`snake_case` (如 `calculate_position`)
- 变量名：`snake_case` (如 `initial_capital`)
- 常量：`UPPER_SNAKE_CASE` (如 `MAX_POSITION_SIZE`)

#### 文档要求
- 所有公共类和方法都需要有文档字符串
- 使用 Google 风格的文档字符串格式
- 包含参数说明、返回值说明和示例

```python
def calculate_position(self, signal_strength: float = 1.0) -> float:
    """
    根据信号强度计算仓位大小

    Args:
        signal_strength: 信号强度，范围 [0, 1]

    Returns:
        float: 仓位大小，范围 [0, 1]

    Example:
        >>> strategy = FixedPercentStrategy(100000, 0.1)
        >>> position = strategy.calculate_position(0.8)
        >>> print(position)
        0.08
    """
```

### 测试要求
- 新功能需要包含单元测试
- 测试覆盖率不应低于80%
- 使用 `pytest` 运行测试

## 🏗️ 项目架构指南

### 核心模块开发

#### 添加新策略
1. 继承 `BaseStrategy` 类
2. 实现 `generate_signals` 方法
3. 在策略工厂中注册

```python
from src.core.strategy.strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)

    def generate_signals(self, data: pd.DataFrame) -> List[SignalEvent]:
        # 实现策略逻辑
        pass
```

#### 添加新指标
1. 继承 `Indicator` 类
2. 实现计算逻辑
3. 在指标工厂中注册

```python
from src.services.chart_service import Indicator

class CustomIndicator(Indicator):
    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        # 实现指标计算
        pass
```

#### 事件处理
- 所有事件都应继承 `BaseEvent`
- 事件处理器应注册到事件总线
- 保持事件处理的异步特性

### 前端开发

#### Streamlit 组件
- 使用模块化设计
- 保持组件独立性和可复用性
- 遵循 Streamlit 最佳实践

#### 图表服务
- 使用工厂模式创建图表
- 支持主题切换
- 保持图表交互性

## 🔧 开发环境设置

### 1. 克隆项目
```bash
git clone https://github.com/your-username/awesome-Qsys.git
cd awesome-Qsys
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装开发工具
```bash
pip install black flake8 pytest
```

### 5. 运行测试
```bash
pytest tests/
```

### 6. 代码格式化
```bash
black src/
flake8 src/
```

## 📋 Pull Request 流程

1. **确保代码质量**
   - 通过所有测试
   - 代码格式化检查通过
   - 文档完整

2. **描述变更**
   - 清晰描述PR的目的
   - 列出主要变更
   - 提供测试结果

3. **代码审查**
   - 至少需要一名核心贡献者审查
   - 根据反馈进行修改
   - 确保代码符合项目标准

## 🏆 贡献者奖励

优秀的贡献者将获得：
- 在项目 README 中列出
- 获得项目维护者权限的机会
- 优先参与新功能开发

## 📞 联系方式

- 项目 Issues: [GitHub Issues](https://github.com/FAKE0704/awesome-Qsys/issues)
- 讨论区: [GitHub Discussions](https://github.com/FAKE0704/awesome-Qsys/discussions)
- 邮箱: pengfeigaofake@gmail.com

---

感谢您的贡献！让我们一起打造更好的量化交易系统！