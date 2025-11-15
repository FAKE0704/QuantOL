# QuantOL - 基于事件驱动的量化交易系统
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-green.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

一个基于事件驱动架构的专业量化交易系统，提供完整的策略开发、回测分析和交易执行功能。

## ✨ 特性

### 🚀 核心功能
- **事件驱动架构** - 基于消息总线的松耦合设计
- **双数据库模式** - 支持SQLite(快速体验)和PostgreSQL(生产环境)
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
- Streamlit 1.28+
- **数据库**: SQLite 3.0+ (默认) 或 PostgreSQL 13+ (可选)

### 🗄️ 数据库模式选择

本项目支持两种数据库模式：

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **SQLite** (默认) | 快速体验、开发测试 | 零配置、开箱即用 | 性能有限、不适合大数据量 |
| **PostgreSQL** | 生产环境、大数据处理 | 高性能、高并发 | 需要额外安装配置 |

### 📦 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/FAKE0704/QuantOL.git
cd QuantOL
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
# 复制配置文件
cp .env.example .env
```

4. **启动应用**
```bash
# 默认使用SQLite模式，无需额外配置
streamlit run main.py
```

### 🔄 数据库模式切换

#### 方式一：命令行切换
```bash
# 切换到SQLite模式（默认）
python -m src.cli.database_switch switch --type sqlite

# 切换到PostgreSQL模式
python -m src.cli.database_switch switch --type postgresql
```

#### 方式二：Web界面切换
1. 启动应用后，在左侧导航栏选择"数据库设置"
2. 点击相应按钮切换数据库类型
3. 系统会自动处理配置和初始化

#### 方式三：手动配置
编辑 `.env` 文件：
```env
# 选择数据库类型 (sqlite/postgresql)
DATABASE_TYPE=sqlite

# SQLite配置
SQLITE_DB_PATH=./data/quantdb.sqlite

# PostgreSQL配置 (当使用PostgreSQL时)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantdb
DB_USER=quant
DB_PASSWORD=your_password_here
```

### 🐘 PostgreSQL模式配置（可选）

如果需要使用PostgreSQL模式，请按以下步骤配置：

#### 使用Docker（推荐）
```bash
# 启动PostgreSQL容器
docker-compose up -d

# 验证数据库运行状态
docker-compose ps
```

#### 使用本地PostgreSQL
```bash
# macOS (使用Homebrew)
brew install postgresql
brew services start postgresql

# 创建数据库和用户
createdb quantdb
createuser quant
psql -d postgres -c "ALTER USER quant PASSWORD 'your_password';"
psql -d quantdb -c "GRANT ALL PRIVILEGES ON DATABASE quantdb TO quant;"

# 参见详细文档: LOCAL_POSTGRES_SETUP.md
```

### 🛠️ 常用命令

#### 数据库管理
```bash
# 查看当前数据库状态
python -m src.cli.database_switch status

# 重新初始化数据库
python -m src.cli.database_switch init

# 切换数据库类型
python -m src.cli.database_switch switch --type sqlite
python -m src.cli.database_switch switch --type postgresql
```

#### 应用管理
```bash
# 启动应用
streamlit run main.py

# 指定端口启动
streamlit run main.py --server.port 8501

# 允许外部访问
streamlit run main.py --server.address 0.0.0.0
```

### ⚠️ 注意事项

- **SQLite模式**: 数据存储在本地文件中，适合开发测试和个人使用
- **PostgreSQL模式**: 需要数据库服务运行，适合生产环境和团队使用
- **数据迁移**: 两种模式间的数据需要手动迁移
- **性能差异**: PostgreSQL在处理大量数据时性能更优

### 🔧 故障排除

#### 常见问题
1. **数据库连接失败**: 检查数据库服务状态和配置信息
2. **SQLite权限错误**: 确保数据目录有写入权限
3. **PostgreSQL连接超时**: 检查防火墙和网络配置

#### 获取帮助
- 查看应用日志获取详细错误信息
- 使用"数据库设置"页面进行连接测试
- 检查配置文件格式和参数

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



