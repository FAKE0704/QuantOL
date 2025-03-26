# 1. 量化交易系统项目
## 1.1. 项目概述
本项目是基于streamlit开发的量化交易系统,分为几个模块。
## 1.2. 项目文件夹路径
C:\Users\Thomas P Gao\Documents\personal\VSC\awesome-Qsys
## 1.3. 文件结构
awesome-Qsys/src/
├── frontend/                     # 前端模块
│   ├── main.py                   # 前端主程序
├── backend/                      # 后端模块
│   ├── api/                      # API接口
├── core/                         # 核心模块
│   ├── data/                     # 数据模块
│   │   ├── database.py
│   │   ├── baostock_source.py
│   │   ├── data_source.py
│   ├── execution/                # 执行模块
│   │   ├── Trader.py             # 交易执行
│   │   ├── TradeDatabaseManager.py # 交易数据管理
│   ├── risk/                     # 风险模块
│   ├── strategy/                 # 策略模块
│   │   ├── strategy.py
│   ├── backtest.py               # 回测引擎
├── notification/                 # 通知模块
├── support/                      # 支持模块
├── venvQuant/                    # 虚拟环境文件夹
├── database.log                  # 数据库日志
├── main.py                       # 项目主函数文件
├── myimports.py                  # 自定义导入


## 1.4. 数据模块
功能：负责市场数据的获取、存储和预处理，支持多种数据源接入。
![1742906681628](image/README/1742906681628.png)

[Data Sources] → [Data Manager] → [Indicator Calculators]
       ↑                ↓
[Data Service] ← [Cache Layer]

### 1.4.1. Data类核心方法
- `load()`: 加载股票数据
- `update_data(data_end_date)`: 异步更新单个股票数据
- `get_sma(window)`: 计算简单移动平均线
- `get_macd(short_window, signal_window, long_window)`: 计算MACD指标
- `get_rsi(window)`: 计算相对强弱指数
- `delete()`: 删除当前数据
- `delete_last()`: 删除最后一行数据

### 1.4.2. BaostockDataSource类
功能：封装Baostock数据获取逻辑，支持异步数据加载和缓存

#### 1.4.2.1. 核心方法：
- `load_data(symbol, start_date, end_date, frequency)`: 异步加载股票数据
- `_transform_data(data)`: 标准化数据格式

### 1.4.3. 数据库模块
功能：通过PostgreSQL数据库进行数据存储和查询

#### 1.4.3.1. 数据库表结构
- StockData: 存储股票历史数据
  - id: 主键
  - symbol: 股票代码
  - date: 日期时间
  - open: 开盘价
  - high: 最高价
  - low: 最低价
  - close: 收盘价
  - volume: 成交量
  - frequency: 数据频率

#### 1.4.3.2. DatabaseManager类

```python
class DatabaseManager:
    """
    数据库管理类，负责与PostgreSQL数据库的交互
    """
    def __init__(self, host='113.45.40.20', port=8080, dbname='quantdb', 
                 user='quant', password='quant123', admin_db='quantdb'):
        """
        初始化数据库连接配置
        :param host: 数据库主机地址
        :param port: 数据库端口
        :param dbname: 数据库名称
        :param user: 用户名
        :param password: 密码
        :param admin_db: 管理数据库名称
        """

#### 1.4.3.3. 特性说明：
1. 异步数据加载：
   - 支持异步加载股票数据，提高系统响应速度
   - 自动检查并补充缺失数据
   
2. 数据完整性检查：
   - 精确计算缺失日期范围
   - 支持跨日期范围的数据完整性验证

3. 日志记录：
   - 详细记录每个操作步骤
   - 支持错误日志和调试信息

4. 错误处理：
   - 增强的异常处理机制
   - 自动回滚失败的事务

#### 1.4.3.4. 核心方法：

1. `init_db() -> None`
   - 功能：初始化数据库表结构
   - 参数：无
   - 返回：无

2. `save_stock_data(data: pd.DataFrame, symbol: str, frequency: str) -> bool`
   - 功能：保存股票数据到数据库
   - 参数：
     - data: 包含股票数据的DataFrame
     - symbol: 股票代码
     - frequency: 数据频率（如"5"表示5分钟数据）
   - 返回：保存是否成功

3. `async load_stock_data(symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame`
   - 功能：从数据库异步加载股票数据
   - 参数：
     - symbol: 股票代码
     - start_date: 开始日期
     - end_date: 结束日期
     - frequency: 数据频率
   - 返回：包含股票数据的DataFrame

4. `check_data_completeness(symbol: str, start_date: str, end_date: str) -> list[tuple[str, str]]`
   - 功能：检查数据完整性并返回缺失日期范围
   - 参数：
     - symbol: 股票代码
     - start_date: 开始日期
     - end_date: 结束日期
   - 返回：缺失日期范围列表，每个元素为(start_date, end_date)元组


#### 1.4.3.4. 使用示例：
```python
# 初始化数据库
db_manager = DatabaseManager()
db_manager.init_db()

# 保存数据
success = db_manager.save_stock_data(df, "sh.600622", "5")

# 查询数据
df = db_manager.load_stock_data("sh.600622", "2025-03-01", "2025-03-25", "5")
```

### 1.4.4. 数据获取流程
1. 检查内存缓存
2. 检查磁盘缓存
3. 从数据库获取数据
4. 从Baostock API获取数据
5. 缓存新数据
6. 更新数据库表数据

### 1.4.5. 数据库表
- Market_Data
- Trade_Records
- Positions
- Strategies
- Signals
- Accounts
- Fund_Flows
- Backtest_Results
- Risk_Management
- Logs

### 1.4.6. 数据格式标准化
- 统一时间字段格式
- 统一列名命名规范
- 处理缺失值和异常值

## 1.5. 策略模块 Strategy class
功能：定义和管理交易策略。
子模块：
策略模板：提供策略开发的基类和接口。
策略市场：存储和管理用户创建的策略。
策略回测：支持策略的历史回测功能。

## 1.6. 交易模块 Buyer class
功能：负责交易订单的生成和执行。
子模块：
订单管理：创建、修改、取消订单。通过OrderManager类提供RESTful API接口
执行引擎：对接交易所 API，执行交易。实现与交易所API的对接，支持异步订单执行
交易记录：记录所有交易细节。将交易数据持久化到数据库，提供查询接口


### OrderManager 订单管理类
负责订单的创建、修改、取消
主要方法：create_order(), modify_order(), cancel_order()
### ExecutionEngine 执行引擎类
负责与交易所API的对接和订单执行
主要方法：execute_order(), cancel_execution()
- format_for_ths(): 格式化指令以适应交易所(同花顺)

### TradeRecorder 交易记录类
负责记录所有交易细节
主要方法：record_trade(), query_trades()
### 数据库表设计：
Orders 订单表
- order_id (主键)
- symbol 标的代码
- order_type 订单类型 (市价/限价)
- quantity 数量
- price 价格
- status 状态 (新建/已提交/已完成/已取消)
- create_time 创建时间
- update_time 更新时间

Executions 执行表
- execution_id (主键)
- order_id (外键)
- exec_price 执行价格
- exec_quantity 执行数量
- exec_time 执行时间
- status 执行状态 (成功/失败)

TradeHistory 交易历史表

- trade_id (主键)
- symbol 标的代码
- trade_time 交易时间
- trade_price 交易价格
- trade_quantity 交易数量
- trade_type 交易类型 (买入/卖出)




## 1.7. 风险模块
功能：监控和管理交易风险。
子模块：
风险评估：计算风险指标（如 VaR、最大回撤等）。
风险控制：设置止损、止盈等规则。
风险报告：生成风险报告和警报。
# 2. 前端模块
## 2.1. 2.1 用户界面模块
功能：提供用户交互界面。
子模块：
仪表盘：展示关键指标和市场概况。
策略管理：允许用户创建、编辑和监控策略。
交易执行：提供交易订单的界面。
风险监控：展示风险指标和警报。
## 2.2. 2.2 数据可视化模块
功能：将数据和交易结果以可视化形式展示。
子模块：
K 线图：展示价格走势。
指标图：展示技术指标（如 MA、MACD 等）。
统计图表：展示交易统计结果。
## 2.3. 2.3 实时通信模块
功能：支持前端与后端的实时数据通信。
子模块：
WebSocket：处理实时市场数据和交易更新。
REST API：处理非实时请求。
# 3. 后端模块
## 3.1. 3.1 API 网关
功能：作为前端与核心模块之间的桥梁。
子模块：
路由管理：定义 API 路由。
请求处理：解析和处理前端请求。
响应格式化：将后端数据格式化为前端可读的格式。
## 3.2. 3.2 任务调度模块
功能：管理定时任务和异步任务。
子模块：
定时任务：如定期获取市场数据、更新策略等。
异步任务：如处理大量计算任务。
## 3.3. 3.3 认证授权模块
功能：管理用户认证和权限控制。
子模块：
用户认证：处理登录、注册等。
权限控制：定义用户角色和权限。
# 4. 支持模块
## 4.1. 4.1 日志模块
功能：记录系统运行日志和交易日志。
子模块：
日志记录：存储日志信息。
日志查询：提供日志查询接口。
## 4.2. 4.2 监控模块
功能：监控系统性能和状态。
子模块：
性能监控：监控 CPU、内存等资源使用情况。
健康检查：提供系统健康状态检查接口。
## 4.3. 4.3 通知模块
功能：发送通知和警报。
子模块：
邮件通知：发送交易确认、风险警报等邮件。
站内通知：提供站内消息系统。




## 5. 数据库部署

### 5.1. 使用docker-compose部署

1. 确保已安装Docker和docker-compose
2. 在项目根目录执行以下命令启动服务：
```bash
docker-compose up -d
```

### 5.2. 服务信息

#### PostgreSQL数据库
- 访问地址：localhost:5432
- 用户名：quant
- 密码：quant123
- 数据库名称：quantdb

#### pgAdmin管理界面
- 访问地址：http://localhost:8080
- 登录邮箱：admin@quant.com
- 登录密码：admin123

### 5.3. 环境变量（可选）
可以在docker-compose.yml中修改以下环境变量：
- POSTGRES_USER：数据库用户名
- POSTGRES_PASSWORD：数据库密码
- POSTGRES_DB：数据库名称
- PGADMIN_DEFAULT_EMAIL：pgAdmin登录邮箱
- PGADMIN_DEFAULT_PASSWORD：pgAdmin登录密码

# 6. 待更新
- [ ] streamlit rerun需要耗费大量时间重新计算数据,使用数据库
- [ ] 仔细检查回测思路
- [x] 买卖点绘制
- [ ] hover 参数
