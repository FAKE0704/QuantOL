# QuantOL - 基于事件驱动的量化交易系统

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

一个基于事件驱动架构的专业量化交易系统，提供完整的策略开发、回测分析和交易执行功能。

## ✨ 特性

### 🚀 核心功能
- **事件驱动架构** - 基于消息总线的松耦合设计
- **多数据源支持** - Baostock、AkShare等数据源集成
- **策略回测引擎** - 支持多股票组合回测和规则组管理
- **风险控制系统** - 完整的资金管理和风险控制机制
- **实时可视化** - 基于Streamlit的交互式界面

### 📊 策略支持
- **规则策略** - 支持技术指标组合和自定义规则
- **仓位管理** - 固定比例、凯利公式、马丁格尔等多种仓位策略
- **多股票组合** - 支持多股票策略映射和资金分配
- **技术指标** - MA、MACD、RSI、布林带等常用指标

### 🎯 专业工具
- **图表服务** - K线图、成交量、资金流向等专业图表
- **性能分析** - 夏普比率、最大回撤、年化收益等指标
- **交易记录** - 完整的交易历史和持仓管理
- **数据管理** - 异步数据加载和缓存机制

## 🚀 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 13+
- Streamlit 1.28+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/QuantOL.git
cd QuantOL
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **数据库配置**
```bash
# 使用Docker快速部署数据库
docker-compose up -d
```

4. **启动应用**
```bash
streamlit run main.py
```

### 配置说明

#### 环境变量配置
复制 `.env.example` 为 `.env` 并配置数据库连接信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantdb
DB_USER=quant
DB_PASSWORD=your_secure_password_here

# 连接池配置
DB_MAX_POOL_SIZE=15
DB_QUERY_TIMEOUT=60
```

#### 数据源配置
系统支持多种数据源，默认使用Baostock：
- Baostock: 免费A股数据
- AkShare: 多市场数据源

## 🏗️ 项目架构

### 核心模块

```
src/
├── core/                    # 核心业务逻辑
│   ├── data/               # 数据管理
│   │   ├── database.py     # 数据库管理
│   │   ├── data_source.py  # 数据源抽象
│   │   └── market_data_source.py
│   ├── strategy/           # 策略管理
│   │   ├── backtesting.py  # 回测引擎
│   │   ├── rule_parser.py  # 规则解析
│   │   └── position_strategy.py
│   ├── execution/          # 交易执行
│   │   └── Trader.py       # 交易引擎
│   ├── risk/               # 风险控制
│   │   └── risk_manager.py
│   └── portfolio/          # 投资组合
│       └── portfolio.py
├── frontend/               # 前端界面
│   ├── backtesting.py      # 回测界面
│   ├── backtest_config_ui.py
│   ├── strategy_config_ui.py
│   └── results_display_ui.py
├── event_bus/              # 事件总线
│   └── event_types.py
└── services/               # 服务层
    └── chart_service.py    # 图表服务
```

### 事件驱动架构

系统采用事件驱动设计，主要事件类型：
- `MarketDataEvent` - 市场数据事件
- `SignalEvent` - 策略信号事件
- `OrderEvent` - 订单事件
- `FillEvent` - 成交回报事件

### 数据流

1. **数据获取** → 数据管理器 → 指标计算
2. **策略引擎** → 信号生成 → 风险验证 → 订单执行
3. **交易执行** → 持仓更新 → 组合管理 → 业绩评估

## 📈 使用示例

### 策略回测

```python
from src.core.strategy.backtesting import BacktestConfig, BacktestEngine

# 创建回测配置
config = BacktestConfig(
    start_date="2023-01-01",
    end_date="2024-01-01",
    target_symbol="000001.SZ",
    initial_capital=100000,
    position_strategy_type="fixed_percent",
    position_strategy_params={"percent": 0.1}
)

# 执行回测
engine = BacktestEngine(config)
results = engine.run()
```

### 规则策略

```python
# 定义交易规则
rules = {
    "buy_rule": "CLOSE > MA(CLOSE, 20) AND MA(CLOSE, 5) > MA(CLOSE, 20)",
    "sell_rule": "CLOSE < MA(CLOSE, 10)"
}
```

## 🛠️ 开发指南

### 添加新策略

1. 继承 `BaseStrategy` 类
2. 实现 `generate_signals` 方法
3. 注册到策略工厂

```python
from src.core.strategy.strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def generate_signals(self, data):
        # 实现策略逻辑
        return signals
```

### 添加新指标

1. 继承 `Indicator` 类
2. 实现计算逻辑
3. 注册到指标工厂

```python
from src.services.chart_service import Indicator

class CustomIndicator(Indicator):
    def calculate(self, data):
        # 实现指标计算
        return result
```

## 📊 性能指标

系统提供完整的性能分析：
- **年化收益率** - 策略年化收益表现
- **夏普比率** - 风险调整后收益
- **最大回撤** - 最大亏损幅度
- **胜率** - 交易成功比例
- **盈亏比** - 平均盈利/平均亏损

## 🤝 贡献指南

我们欢迎各种形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 Apache 2.0 许可证。详细信息请参见 [LICENSE](LICENSE) 文件。

Copyright 2025 QuantOL Project

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 优秀的Web应用框架
- [Baostock](http://baostock.com/) - 免费A股数据源
- [AkShare](https://github.com/akfamily/akshare) - 多市场数据接口

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 项目 Issues: [GitHub Issues](https://github.com/FAKE0704/QuantOL/issues)
- 邮箱: pengfeigaofake@gmail.com
- 微信: ThomasGao0704

---


⭐ 如果这个项目对您有帮助，请给我一个 Star！
