# QuantOL - 基于事件驱动的量化交易系统
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Nginx](https://img.shields.io/badge/Nginx-1.24+-green.svg)](https://nginx.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-green.svg)](https://www.sqlite.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-API-orange.svg)](https://websockets.ws/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

一个基于事件驱动架构的专业量化交易系统，提供完整的策略开发、回测分析和交易执行功能。采用前后端分离架构，支持实时进度追踪和异步任务执行。

## ✨ 特性

### 🚀 核心功能
- **事件驱动架构** - 基于消息总线的松耦合设计
- **前后端分离** - React/Next.js 前端 + FastAPI 后端
- **异步任务执行** - 支持后台回测和实时进度追踪
- **WebSocket 通信** - 实时推送回测进度和状态更新
- **Redis 状态存储** - 持久化回测状态和结果
- **Nginx 反向代理** - 统一入口，支持 WebSocket 代理
- **双数据库模式** - 支持SQLite(快速体验)和PostgreSQL(生产环境)
- **多数据源支持** - Tushare、Baostock、AkShare等数据源集成
- **策略回测引擎** - 支持多股票组合回测和规则组管理
- **风险控制系统** - 完整的资金管理和风险控制机制
- **双重界面** - React新版界面 + Streamlit经典界面

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
- Python 3.12+
- Node.js 20+ (用于 React 前端)
- uv (包管理器)
- **Redis**: 7.0+ (用于状态存储)
- **Nginx**: 1.24+ (反向代理)
- **数据库**: SQLite 3.0+ (默认) 或 PostgreSQL 13+ (可选)

### 🗄️ 数据库模式选择

本项目支持两种数据库模式：

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **SQLite** (默认) | 快速体验、开发测试 | 零配置、开箱即用 | 性能有限、不适合大数据量 |
| **PostgreSQL** | 生产环境、大数据处理 | 高性能、高并发 | 需要额外安装配置 |

### 📦 安装步骤

1. **安装依赖软件**
```bash
# 安装 Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# 或使用 Docker
docker run -d -p 6379:6379 redis:7

# 安装 Nginx
# Ubuntu/Debian
sudo apt-get install nginx

# macOS
brew install nginx
```

2. **安装 uv**
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用包管理器
pip install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **克隆项目**
```bash
git clone https://github.com/FAKE0704/QuantOL.git
cd QuantOL
```

4. **安装依赖**
```bash
# Python 依赖
uv sync

# 前端依赖
cd landing-page && npm install && cd ..
```

5. **配置环境**
```bash
# 复制配置文件
cp .env.example .env
```

6. **启动应用**
```bash
# 一键启动所有服务
./start.sh
```

启动后访问：- 新版界面: http://localhost:8087
- Streamlit: http://localhost:8087/app

### 🔄 数据库模式切换

#### 方式一：命令行切换
```bash
# 切换到SQLite模式（默认）
uv run python -m src.cli.database_switch switch --type sqlite

# 切换到PostgreSQL模式
uv run python -m src.cli.database_switch switch --type postgresql
```

#### 方式二：Web界面切换
1. 启动应用后，在左侧导航栏选择"系统设置-数据库设置"
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

#### 包管理
```bash
# 同步依赖（安装/更新虚拟环境）
uv sync

# 添加新依赖
uv add <package>

# 更新所有依赖
uv lock --upgrade
```

#### 数据库管理
```bash
# 查看当前数据库状态
uv run python -m src.cli.database_switch status

# 重新初始化数据库
uv run python -m src.cli.database_switch init

# 切换数据库类型
uv run python -m src.cli.database_switch switch --type sqlite
uv run python -m src.cli.database_switch switch --type postgresql
```

#### 应用管理
```bash
# 启动应用
uv run streamlit run main.py

# 指定端口启动
uv run streamlit run main.py --server.port 8501

# 允许外部访问
uv run streamlit run main.py --server.address 0.0.0.0
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
系统支持多种数据源，可通过系统设置页面灵活切换：

| 数据源 | 特点 | 配置要求 | 适用场景 |
|--------|------|----------|----------|
| **Tushare** | 专业级金融数据接口 | 需要注册获取Token | 生产环境、专业分析 |
| **Baostock** | 免费开源证券数据平台 | 无需配置 | 学习测试、快速体验 |
| **AkShare** | 多市场数据源 | 可选API密钥 | 多市场数据获取 |

##### Tushare配置 (推荐)
1. 访问 [Tushare官网](https://tushare.pro/register?reg=693641) 注册账户
2. 在个人中心获取API Token
3. 在系统设置 → 数据源配置中输入Token
4. 或在 `.env` 文件中配置：
   ```bash
   TUSHARE_TOKEN=your_32_character_token_here
   SELECTED_DATA_SOURCE=Tushare
   ```

##### Baostock配置 (默认)
- 无需任何配置，开箱即用
- 适合快速体验和学习测试
- 在系统设置中直接选择即可使用

## 🏗️ 项目架构

### 核心模块

```
QuantOL/
├── src/                     # 后端核心
│   ├── api/                 # FastAPI 路由
│   │   ├── models/          # Pydantic 请求/响应模型
│   │   │   ├── common.py           # 通用模型
│   │   │   ├── backtest_requests.py
│   │   │   └── backtest_responses.py
│   │   ├── routers/         # API 端点
│   │   │   ├── backtest/    # 回测路由子包 (模块化)
│   │   │   │   ├── execution.py      # 执行端点
│   │   │   │   ├── results.py        # 结果端点
│   │   │   │   ├── configs.py        # 配置端点
│   │   │   │   ├── custom_strategies.py # 策略端点
│   │   │   │   └── logs.py           # 日志端点
│   │   │   ├── auth.py      # 认证 API
│   │   │   ├── stocks.py    # 股票 API
│   │   │   └── websocket.py # WebSocket API
│   │   ├── deps.py          # 通用依赖注入
│   │   ├── utils.py         # 共享工具函数
│   │   └── server.py        # FastAPI 应用
│   ├── core/                # 核心业务逻辑
│   │   ├── data/            # 数据管理
│   │   │   ├── database.py  # 数据库管理
│   │   │   └── data_source.py
│   │   ├── strategy/        # 策略管理
│   │   │   ├── backtesting.py      # 回测引擎
│   │   │   ├── rule_parser/        # 规则解析器包 (模块化)
│   │   │   │   ├── expression_context.py    # 评估上下文
│   │   │   │   ├── ast_node_handler.py      # AST操作工具
│   │   │   │   ├── cache_manager.py          # LRU缓存管理
│   │   │   │   ├── result_storage.py         # 结果存储管理
│   │   │   │   ├── cross_sectional_ranker.py # 横截面排名
│   │   │   │   ├── rule_evaluator.py         # 表达式评估
│   │   │   │   └── rule_parser.py            # 门面类 (向后兼容)
│   │   │   ├── rule_based_strategy.py # 规则策略
│   │   │   └── position_strategy.py   # 仓位策略
│   │   ├── backtest/        # 回测引擎 (模块化)
│   │   │   ├── protocols/    # 协议接口
│   │   │   ├── services/     # 服务层
│   │   │   ├── coordinators/ # 协调器
│   │   │   └── engine.py     # 重构引擎
│   │   ├── execution/       # 交易执行
│   │   ├── risk/            # 风险控制
│   │   └── portfolio/       # 投资组合
│   ├── frontend/            # Streamlit 界面
│   │   ├── backtesting.py
│   │   └── backtest_config_ui.py
│   ├── services/            # 服务层
│   │   ├── interfaces/      # 服务接口定义
│   │   ├── backtest_state_service.py    # Redis 状态存储
│   │   ├── backtest_task_manager.py     # 异步任务管理
│   │   ├── backtest_task_service.py     # 任务服务
│   │   ├── websocket_manager.py         # WebSocket 连接管理
│   │   └── chart_service.py             # 图表服务
│   ├── event_bus/          # 事件总线
│   │   ├── service_events.py            # 服务事件定义
│   │   └── local_service_bus.py         # 本地服务总线
│   └── utils/              # 工具模块
│       ├── encoders.py      # JSON 编码器
│       ├── async_helpers.py # 异步辅助工具
│       └── strategy_registry.py # 策略注册表
├── landing-page/            # React/Next.js 前端
│   ├── app/                 # Next.js App Router
│   │   └── (app)/
│   │       └── backtest/    # 回测页面
│   ├── components/          # React 组件
│   │   └── backtest/        # 回测相关组件
│   ├── lib/                 # 工具库
│   │   ├── api.ts           # API 客户端
│   │   └── hooks/           # React Hooks
│   │       └── useBacktestWebSocket.ts
│   └── package.json
├── nginx.conf               # Nginx 配置
├── start.sh                 # 启动脚本
└── stop.sh                  # 停止脚本
```

### 架构改进 (2025年2月重构)

#### RuleParser 模块化 (1061行 → 7个组件)
- **ExpressionContext** - 不可变的评估上下文数据类
- **ASTNodeHandler** - 无状态AST节点操作工具
- **RuleCacheManager** - LRU缓存管理器 (时间相关/无关分离)
- **ResultStorageManager** - DataFrame列存储管理
- **CrossSectionalRanker** - 横截面排名逻辑
- **RuleEvaluator** - 表达式评估核心逻辑
- **RuleParser (门面)** - 向后兼容的统一入口

#### API Router 模块化 (1408行 → 5个子模块)
- **execution.py** - 回测执行端点
- **results.py** - 结果查询端点 (6个)
- **configs.py** - 配置管理端点 (6个)
- **custom_strategies.py** - 自定义策略端点 (6个)
- **logs.py** - 日志查询端点
- **models/** - 统一的Pydantic模型组织

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

### 异步回测流程

1. **前端发起** → POST /api/backtest/run
2. **创建任务** → BacktestTaskManager 提交后台任务
3. **状态存储** → Redis 保存回测状态
4. **执行回测** → BacktestEngine 异步执行
5. **进度推送** → WebSocket 实时推送进度
6. **前端展示** → 进度条显示 + 结果展示

### 技术栈

| 层级 | 技术栈 | 用途 |
|------|--------|------|
| **前端** | React 18, Next.js 14, Tailwind CSS | 用户界面 |
| **后端** | FastAPI, Python 3.12+ | API 服务 |
| **通信** | WebSocket, HTTP/REST | 实时通信 |
| **缓存** | Redis 7.0+ | 状态存储 |
| **代理** | Nginx 1.24+ | 反向代理 |
| **数据库** | SQLite, PostgreSQL | 数据持久化 |
| **任务** | FastAPI BackgroundTasks | 异步执行 |

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

### 核心技术
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Python Web 框架
- [React](https://react.dev/) - 用户界面库
- [Next.js](https://nextjs.org/) - React 应用框架
- [WebSocket](https://websockets.ws/) - 实时双向通信
- [Redis](https://redis.io/) - 内存数据库和缓存
- [Nginx](https://nginx.org/) - 高性能反向代理
- [Streamlit](https://streamlit.io/) - 优秀的Web应用框架

### 数据源
- [Baostock](http://baostock.com/) - 免费A股数据源
- [AkShare](https://github.com/akfamily/akshare) - 多市场数据接口
- [Tushare](https://tushare.pro/) - 专业金融数据接口

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 项目 Issues: [GitHub Issues](https://github.com/FAKE0704/QuantOL/issues)
- 邮箱: pengfeigaofake@gmail.com
- 微信: ThomasGao0704

---


⭐ 如果这个项目对您有帮助，请给我一个 Star！



