# src/core/data/database.py
## DatabaseManager
- 负责数据库连接池管理（asyncpg实现）
- 表结构初始化
- 股票数据CRUD操作
- 数据完整性检查



主要方法
- save_order：保存订单
- update_order_status：更新订单状态
- log_execution：交易执行结果日志记录
- record_trade：交易记录
- query_orders：订单队列
- query_trades：交易历史队列

待实现：
- 添加交易相关方法
```
async def save_order(self, order: dict) -> int:
        """异步保存订单"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO Orders (...) VALUES (...) RETURNING order_id
            """, ...)
```


- 

# src/core/data/data_source.py
## DataSourceError
- 数据源操作异常基类
## DataSource
- 数据源抽象基类

# src/core/data/data_factory.py
## DataFactory(DataSource)
- 数据源工厂类，实现单例模式和线程安全的数据源管理
### BaostockDataSource(DataSource)
- 已注册到数据源工厂
### AkShareSource(DataSource)
- 已注册到数据源工厂

# src/core/data/market_data_source.py
## DatabaseConnection(Protocal)
- 可能冗余
- 数据库连接协议
## MarketDataSource(DataSource)
市场数据源实现类


# src/core/execution/Trader.py
## TradeOrderManager(BaseTrader)
- 负责订单生命周期管理（创建、修改、取消、状态管理、数据库操作）
- process_orders：处理等待中的订单，使用注入的trader执行订单

## TradeExecutionEngine
- 负责交易指令生成
## TradeRecorder

## BaseTrader
## BacktestTrader(BaseTrader)
- 负责订单实际执行和事件转换
- execute_order：回测时处理OrderEvent并返回FillEvent
## LiveTrader(BaseTrader)
- 负责实际执行和事件转换


# src/core/risk/risk_manager.py
## RiskManager
- 负责系统级风险控制（全局资金/仓位限额）
- 负责验证PositionStrategy的输出是否合规（风控）

待分析
输入​：所有策略的目标仓位、系统风险参数（总资金限额、集中度阈值）、实时账户状态。
•
​输出​：风险验证结果（通过/拒绝/调整建议）。
- 验证策略输出是否违反系统级风控规则（如总仓位≤总资金的50%）
- 动态调整仓位以符合全局约束（如自动缩减超限订单的数量）
- 举例：你有n个策略，提供了n个仓位目标， RiskManager会校验总和是否超出资金上限、单一标的持仓 ≤ 总资金的10%等

属性
- portfolio：PortfolioManager




主要方法
- validate_order：验证订单风险是否通过
- _check_funds：检查资金是否充足
- _check_position：检查是否超过仓位限制

问题：
- RiskManager直接访问`portfolio.get_position()`和`portfolio.get_strategy_limit()`
- 这可能导致RiskManager与Portfolio实现强耦合


# src/core/strategy/strategy.py
## BaseStrategy
## FixedInvestmentStrategy

# src/core/strategy/rule_parser.py
## IndicatorFunction
## RuleParser
_store_expression_result：存储表达式结果到data

！COST不是静态数据列，而是动态的持仓总成本，需要从portfolio_manager实时获取


# src/core/strategy/rule_based_strategy.py
## RuleBasedStrategy

# src/core/strategy/position_strategy.py
## PositionStrategy
仓位策略基类
- 基于策略逻辑生成目标仓位
- 

待分析：
输入​：市场数据（价格、波动率）、策略参数（风险偏好、杠杆率）、账户状态（当前持仓）。
•
​输出​：策略级别的目标仓位（如股票A买入200股）
- 计算信号强度
- 应用策略级风控

## FixedPercentStrategy(PositionStrategy)
固定比例仓位策略
- calculate_position：计算仓位比例
## KellyStrategy(PositionStrategy)
凯利公式仓位策略
- calculate_position：计算凯利公式仓位


# src/core/strategy/indicators.py
## IndicatorService

# src/core/strategy/dca_strategy.py
## DCABaseStrategy


# src/core/strategy/backtesting.py
## BacktestConfig
回测配置类，包含回测所需的所有参数配置，用于存储、验证和管理回测策略的设置。
### DUTIES
- 存储和管理回测参数配置，包括资金、手续费、日期等。
- 验证配置参数的合法性，确保输入值符合业务逻辑约束。
- 处理多符号模式的兼容性和资金分配逻辑，支持单标或多标交易。

### PROPERTIES
- `initial_capital`: 初始资金，默认100万。
- `commission_rate`: 单笔交易手续费率（百分比值），默认0.0005。
- `slippage`: 滑点率，默认0.0。
- `start_date`: 回测开始日期，格式'YYYY-MM-DD'。
- `end_date`: 回测结束日期，格式'YYYY-MM-DD'。
- `target_symbol`: 目标交易标的代码。
- `target_symbols`: 多标的交易代码列表。
- `frequency`: 数据频率。
- `stop_loss`: 止损比例，None表示不启用。
- `take_profit`: 止盈比例，None表示不启用。
- `max_holding_days`: 最大持仓天数，None表示不限制。
- `extra_params`: 额外参数存储。
- `position_strategy_type`: 仓位策略类型，默认"fixed_percent"。
- `position_strategy_params`: 仓位策略参数。
- `min_lot_size`: 最小交易手数，默认100股（A股市场）。
- `strategy_mapping`: 股票-策略映射配置，支持为不同股票选择不同策略。
- `default_strategy`: 默认策略配置，用于单符号模式或未指定策略的股票。

### METHODS
- `__post_init__`: 参数验证和兼容性处理，包括日期格式、资金分配等。
- `get_symbols`: 统一获取所有交易标的符号列表。
- `is_multi_symbol`: 判断是否为多符号模式。
- `get_primary_symbol`: 获取主符号（用于兼容旧代码）。
- `_distribute_capital`: 多符号模式下的资金分配逻辑。
- `get_symbol_capital`: 获取指定符号的分配资金。
- `get_strategy_for_symbol`: 获取指定股票的策略配置。
- `_validate_position_strategy_params`: 验证仓位策略参数。
- `to_dict`: 将配置转换为字典。
- `from_dict`: 从字典创建配置实例（类方法）。
- `to_json`: 将配置转换为JSON字符串。
- `from_json`: 从JSON字符串创建配置实例（类方法）。

## BacktestEngine
- 负责执行回测流程


方法
get_results:获取回测结果
- _handle_fill_event：订单完成后，处理事件：更新仓位等信息


属性
- portfolio: BacktestPortfolioAdapter类
  - `available_cash`: 返回当前可用现金  
  - `total_value`: 计算总资产价值（现金 + 持仓市值）  
  - `get_position()`: 获取当前持仓数量  
  - `get_strategy_limit()`: 获取策略的最大持仓比例（默认20%）[7](@ref)

- equity_records:净值记录

主要方法
_validate_order_risk：使用RiskManager.validate_order进行完整的风险检查

_create_portfolio：

# src/core/strategy/signal_types.py
## SignalType
### PROPERTIES
OPEN = "OPEN"      # 开仓信号
BUY = "BUY"        # 加仓信号
SELL = "SELL"      # 减仓信号
CLOSE = "CLOSE"    # 清仓信号
HEDGE = "HEDGE"    # 对冲信号
REBALANCE = "REBALANCE"  # 再平衡信号

# src/core/portfolio/portfolio_interface.py
## IPortfolio
BacktestEngine通过IPortfolio接口访问 PortfolioManager 的属性与方法。

### METHODS
- get_cash_balance：获取当前余额
- get_total_return：计算总收益率


# src/core/portfolio/portfolio.py
## PortfolioManager
投资组合管理类
### DUTIES
- 投资组合管理：管理整个投资组合的资产配置和持仓情况
- 资金管理：跟踪和管理可用现金、初始资金和组合总价值、持仓信息（持仓状态、持仓金额等）
- 根据信号持仓操作：执行买入、卖出等持仓更新操作历史记录
- 组合再平衡：根据目标配置比例自动调整持仓
- 风险控制集成：与风险管理系统集成进行风险检查
- 与TradeExecutionEngine协同工作，不执行实际交易操作

### PROPERTIES
- `initial_capital`: 初始资金
- `current_cash`: 当前现金余额
- `position_strategy`: 仓位策略实例
- `event_bus`: 事件总线实例（可选）
- `positions`: 持仓字典（键为股票代码，值为Position对象）
- `equity_history` = {
    'timestamp': timestamp,
    'total_value': total_value,
    'cash': self.current_cash,
    'positions_value': total_value - self.current_cash,
    'return_pct': self.get_total_return() * 100,
    'drawdown_pct': current_drawdown,
    'peak_value': self._peak_value
  } : 历史净值记录列表
- `_peak_value`: 最高收益值
- `_max_drawdown`: 最大回撤值
- `_portfolio_value_cache`: 组合价值缓存
- `_cache_timestamp`: 缓存时间戳
- `_cache_ttl`: 缓存有效期（秒）
- `_last_update_time`: 最后更新时间戳


### METHODS
- update_position(self, symbol: str, quantity: float, price: float) -> bool: 更新指定股票的持仓数量和价格（含风险检查和事件发布）
- update_position_for_backtest(self, symbol: str, quantity: float, price: float) -> bool: 回测专用的更新持仓方法（直接调用update_position）
- get_portfolio_value：获取投资组合总价值 （不使用@st.cache_data）
- rebalance：组合再平衡
- _handle_open_signal
- _handle_close_signal
- _handle_buy_signal
- _handle_sell_signal
- _handle_rebalance_signal
- _handle_hedge_signal


## Position
stock
quantity
avg_cost
current_value

## PositionStrategyFactory



# src/event_bus/handlers/strategy/strategy_handler.py
## StrategyEventHandler
- 策略事件处理



# src/event_bus/event_types.py
## BaseEvent
事件基类
## MarketDataEvent
行情数据事件
## OrderEvent
订单事件


## FillEvent
成交回报事件
## SignalEvent
信号事件
## SystemEvent
系统控制事件
## StrategySignalEvent
策略信号事件

### PROPERTIES
- `signal_type`
- `symbol`
- `price`
- `confidence`
- `strategy_id`
- `position_percent`
- `hedge_ratio`
direction: str
signal_type: SignalType  # 信号类型: OPEN/BUY/SELL/CLOSE/HEDGE/REBALANCE
price:
quantity: 
confidence:
quantity: int = 0  # 交易数量，0表示自动计算
confidence: float = 1.0  # 信号置信度
timestamp: datetime
engine: Any = 
parameters:
position_percent: Optional[float] = None  # 用于REBALANCE信号的目标仓位比例
hedge_ratio:



## StrategyScheduleEvent
策略定时任务事件
## TradingDayEvent
交易日事件
## PortfolioPositionUpdateEvent
投资组合持仓更新事件

# src/services/chart_service.py
- 配置管理类（ChartConfig, LayoutConfig, DataConfig）
- 图表基类和具体实现（ChartBase, CandlestickChart, VolumeChart, CapitalFlowChart）
- 指标系统（Indicator基类和具体指标实现）
- 工厂模式（ChartFactory, IndicatorFactory）
- 装饰器模式（IndicatorDecorator）
- 数据容器（DataBundle）

## ChartService
