# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
这是一个基于事件驱动架构的量化交易系统，使用Streamlit框架和PostgreSQL数据库。系统包含数据管理、策略回测、交易执行、风险控制等核心模块。

## 开发环境
- **Python版本**: 3.9+
- **主要框架**: Streamlit
- **数据库**: PostgreSQL
- **数据源**: Baostock、AkShare

## 常用命令

### 启动应用
```bash
# 激活虚拟环境 (Windows)
.\venvWin\Scripts\activate

# 激活虚拟环境 (Mac/Linux)
source venvMac/bin/activate

# 运行主应用
streamlit run src/main.py
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 架构设计

### 核心模块结构
```
src/
├── core/           # 核心业务逻辑
│   ├── data/       # 数据管理
│   ├── strategy/   # 策略管理
│   ├── execution/  # 交易执行
│   ├── risk/       # 风险控制
│   └── portfolio/  # 投资组合
├── frontend/       # 前端界面
├── services/       # 服务层
├── event_bus/      # 事件总线
└── support/        # 支持功能
```

### 事件驱动架构
系统采用事件驱动设计，主要事件类型：
- `MarketDataEvent`: 市场数据事件
- `OrderEvent`: 订单事件
- `SignalEvent`: 信号事件
- `FillEvent`: 成交回报事件
- `StrategySignalEvent`: 策略信号事件

### 数据流
1. 数据源 (Baostock/AkShare) → 数据管理器 → 指标计算
2. 策略引擎 → 信号生成 → 风险验证 → 订单执行
3. 交易执行 → 持仓更新 → 组合管理 → 业绩评估

## 关键组件

### DatabaseManager (`core/data/database.py`)
- 异步数据库连接池管理 (asyncpg)
- 股票数据CRUD操作
- 数据完整性检查和补充

### BacktestEngine (`core/strategy/backtesting.py`)
- 回测配置管理 (BacktestConfig)
- 多符号回测支持
- 事件驱动的回测执行

### PortfolioManager (`core/portfolio/portfolio.py`)
- 投资组合管理和资金跟踪
- 持仓操作和再平衡
- 净值历史记录

### ChartService (`services/chart_service.py`)
- K线图、成交量图表
- 技术指标可视化
- 多图表联动和主题管理

## 开发规范

### 命名约定
- 管理类: `Manager`后缀 (RiskManager)
- 策略类: `Strategy`后缀 (PositionStrategy)
- 数据源: `Source`后缀 (DataSource)
- 事件类: 无后缀 (OrderEvent)

### 代码风格
- 使用异步编程处理IO密集型操作
- 统一的错误处理和日志记录
- 遵循DRY原则，避免代码重复

## 测试

### 单元测试
```bash
# 运行测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_backtest.py -v
```

### 回测验证
系统提供完整的回测框架，支持：
- 单股票和多股票回测
- 自定义规则策略
- 多种仓位管理策略
- 详细的业绩报告和分析

## 故障排除

### 常见问题
1. **数据加载缓慢**: 检查网络连接和数据源API限制

# 个人偏好设置
- @~/.claude/my-project-instructions.md
- 使用中文进行沟通

# 进行代码测试前
- 需要先运行`.\venvWin\Scripts\activate`进入虚拟环境

# 系统的所有模块、所有类的members与职责
@docs/system-design/project_components_catalog.md
