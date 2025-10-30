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
### DUTIES
- 计算理论仓位大小
- 根据策略信号确定仓位比例
- 注意：实际仓位限制检查由RiskManager负责

### PROPERTIES
- `account_value`: 账户当前净值

### METHODS
- `__init__(account_value: float)`: 初始化策略
- `calculate_position(signal_strength: float = 1.0) -> float`: 计算仓位大小

## FixedPercentStrategy(PositionStrategy)
固定比例仓位策略
### DUTIES
- 按固定比例计算仓位
- 不考虑风险限制(由RiskManager处理)

### PROPERTIES
- `percent`: 固定仓位比例(0-1)

### METHODS
- `__init__(account_value: float, percent: float = 0.1)`: 初始化策略
- `calculate_position(signal_strength: float = 1.0) -> float`: 计算固定比例仓位

## KellyStrategy(PositionStrategy)
凯利公式仓位策略
### DUTIES
- 根据凯利公式计算最优仓位
- 最大仓位限制仅为公式计算上限
- 实际执行需通过RiskManager验证

### PROPERTIES
- `win_rate`: 策略胜率(0-1)
- `win_loss_ratio`: 平均盈亏比(正数)
- `max_percent`: 最大仓位限制(0-1)

### METHODS
- `__init__(account_value: float, win_rate: float, win_loss_ratio: float, max_percent: float = 0.25)`: 初始化策略
- `calculate_position(signal_strength: float = 1.0) -> float`: 计算凯利公式仓位

## PositionStrategyFactory
仓位策略工厂类
### DUTIES
- 根据配置创建相应的仓位策略实例
- 提供统一的策略创建接口

### METHODS
- `create_strategy(strategy_type: str, account_value: float, params: Dict[str, Any]) -> PositionStrategy`: 创建仓位策略实例


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

# src/frontend/backtest_config_ui.py
## BacktestConfigUI
- 负责回测范围配置的UI组件渲染
- 提供日期、频率、股票选择等配置界面

### DUTIES
- `日期配置`: 渲染回测日期范围选择UI
- `频率配置`: 渲染数据频率选择UI
- `股票选择`: 渲染多股票选择UI组件
- `配置摘要`: 显示当前配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `date_config`: 日期配置参数
- `frequency_config`: 频率配置参数

### METHODS
- `__init__(session_state)`: 初始化配置UI组件
- `render_date_config_ui()`: 渲染日期配置UI
- `render_frequency_config_ui()`: 渲染频率配置UI
- `render_stock_selection_ui()`: 渲染股票选择UI
- `render_config_summary()`: 渲染配置摘要

# src/frontend/strategy_config_ui.py
## StrategyConfigUI
- 负责策略相关配置的UI组件渲染
- 提供策略选择、规则编辑等配置界面

### DUTIES
- `策略选择`: 渲染策略类型选择UI
- `规则编辑`: 渲染自定义规则编辑UI
- `多股票策略`: 渲染多股票策略配置UI
- `策略摘要`: 显示策略配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `strategy_types`: 可用策略类型列表
- `rule_templates`: 规则模板配置

### METHODS
- `__init__(session_state)`: 初始化策略配置UI组件
- `render_strategy_selection_ui()`: 渲染策略选择UI
- `render_custom_rules_ui(rule_group_manager, strategy_type)`: 渲染自定义规则UI
- `render_multi_symbol_strategy_ui(selected_options, rule_group_manager, config_manager)`: 渲染多股票策略UI
- `render_strategy_summary()`: 渲染策略配置摘要

# src/frontend/position_config_ui.py
## PositionConfigUI
- 负责仓位相关配置的UI组件渲染
- 提供仓位策略、基础参数等配置界面

### DUTIES
- `仓位策略`: 渲染仓位策略选择UI
- `参数配置`: 渲染策略参数配置UI
- `基础配置`: 渲染基础参数配置UI
- `配置摘要`: 显示仓位配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `position_strategies`: 可用仓位策略列表
- `config_params`: 配置参数字典

### METHODS
- `__init__(session_state)`: 初始化仓位配置UI组件
- `render_position_strategy_ui()`: 渲染仓位策略UI
- `render_basic_config_ui()`: 渲染基础配置UI
- `render_config_summary()`: 渲染配置摘要
- `_render_fixed_percent_ui()`: 渲染固定比例策略UI
- `_render_kelly_ui()`: 渲染凯利公式策略UI
- `_render_martingale_ui()`: 渲染马丁格尔策略UI

# src/frontend/results_display_ui.py
## ResultsDisplayUI
- 负责回测结果的UI组件渲染
- 提供多标签页结果展示界面

### DUTIES
- `结果标签页`: 渲染多标签页结果展示布局
- `摘要显示`: 渲染回测摘要标签页
- `交易记录`: 渲染交易记录标签页
- `仓位明细`: 渲染仓位明细标签页
- `净值曲线`: 渲染净值曲线标签页

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `chart_service`: 图表服务实例
- `results_data`: 回测结果数据

### METHODS
- `__init__(session_state)`: 初始化结果展示UI组件
- `render_results_tabs(results, backtest_config)`: 渲染结果展示标签页
- `render_summary_tab(results, backtest_config)`: 渲染回测摘要标签页
- `render_trades_tab(results)`: 渲染交易记录标签页
- `render_positions_tab(results)`: 渲染仓位明细标签页
- `render_equity_chart_tab(results)`: 渲染净值曲线标签页

# src/frontend/data_loader.py
## DataLoader
- 负责统一的数据加载和预处理服务
- 提供单股票和多股票数据加载接口

### DUTIES
- `数据加载`: 异步加载回测所需数据
- `数据验证`: 验证数据质量和完整性
- `数据预处理`: 准备引擎所需数据格式
- `缓存管理`: 管理数据加载缓存

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `data_cache`: 数据缓存字典
- `validation_rules`: 数据验证规则

### METHODS
- `__init__(session_state)`: 初始化数据加载服务
- `load_backtest_data(backtest_config)`: 加载回测数据
- `_load_single_stock_data(config, symbol)`: 加载单股票数据
- `_load_multiple_stock_data(config, symbols)`: 加载多股票数据
- `prepare_engine_data(loaded_data, config)`: 准备引擎数据
- `validate_data_quality(data, config)`: 验证数据质量
- `get_data_summary(data, config)`: 获取数据摘要

# src/frontend/callback_services.py
## CallbackServices
- 负责回调函数的管理和服务
- 提供统一的按钮回调和事件处理接口

### DUTIES
- `回调管理`: 管理所有按钮回调函数
- `事件处理`: 处理事件处理器注册
- `状态管理`: 管理回测状态转换
- `错误处理`: 处理回测错误回调

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `callbacks`: 回调函数字典
- `event_handlers`: 事件处理器实例

### METHODS
- `__init__(session_state)`: 初始化回调服务
- `create_backtest_callback()`: 创建回测按钮回调
- `create_refresh_callback(data_loader)`: 创建刷新按钮回调
- `create_signal_handler(engine)`: 创建信号处理回调
- `register_event_handlers(engine)`: 注册事件处理器
- `handle_backtest_completion(results, success)`: 处理回测完成回调
- `handle_backtest_error(error)`: 处理回测错误回调
- `reset_backtest_state()`: 重置回测状态

# src/frontend/event_handlers.py
## EventHandlers
- 负责事件处理逻辑的管理
- 提供上下文感知的事件处理器

### DUTIES
- `事件处理`: 管理所有事件处理逻辑
- `上下文管理`: 添加上下文信息到事件
- `进度跟踪`: 更新回测进度状态
- `状态管理`: 管理回测运行状态

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `progress_tracker`: 进度跟踪器
- `status_manager`: 状态管理器

### METHODS
- `__init__(session_state)`: 初始化事件处理器
- `create_signal_handler(engine)`: 创建信号事件处理器
- `create_schedule_handler(engine)`: 创建调度事件处理器
- `register_all_handlers(engine)`: 注册所有事件处理器
- `handle_backtest_start(engine)`: 处理回测开始事件
- `handle_backtest_end(results)`: 处理回测结束事件
- `handle_backtest_error(error)`: 处理回测错误事件
- `cleanup_after_backtest()`: 回测后清理

# src/services/chart_service.py
- 配置管理类（ChartConfig, LayoutConfig, DataConfig）
- 图表基类和具体实现（ChartBase, CandlestickChart, VolumeChart, CapitalFlowChart）
- 指标系统（Indicator基类和具体指标实现）
- 工厂模式（ChartFactory, IndicatorFactory）
- 装饰器模式（IndicatorDecorator）
- 数据容器（DataBundle）

## ChartService

# src/frontend/backtesting.py
## BacktestingFrontend
- 负责策略回测的前端界面实现
- 基于Streamlit框架构建交互式回测配置界面
- 支持多股票组合回测和规则组管理

### DUTIES
- `界面布局管理`: 使用标签页组织回测配置、策略配置、仓位配置
- `组件协调`: 协调各模块化组件的工作流程和数据传递
- `数据加载`: 异步加载股票列表和行情数据
- `流程控制`: 管理回测的整体执行流程和状态转换
- `结果展示`: 整合各模块的结果展示和可视化

### PROPERTIES
- `st.session_state.backtest_config`: 回测配置对象实例
- `st.session_state.rule_groups`: 规则组字典存储
- `st.session_state.strategy_mapping`: 股票-策略映射配置
- `st.session_state.stock_cache`: 股票列表缓存
- `st.session_state.chart_service`: 图表服务实例（委托给ChartService）
- `st.session_state.chart_instance_id`: 图表实例ID

### METHODS
- `show_backtesting_page()`: 主页面显示函数（协调各模块化组件）
- 各种Streamlit组件交互方法

### 新增功能特性
- 支持预设规则组：金叉死叉、相对强度、Martingale策略
- 改进的规则组加载机制，避免Streamlit widget修改错误
- 多股票策略映射配置界面
- 统一的规则语法校验和显示
- 完整的策略性能指标计算和显示
- 通过ChartService实现交易信号与K线叠加可视化
- 通过ChartService实现综合指标面板显示
- 通过ChartService实现回撤曲线分析和可视化
- 通过ChartService实现收益分布直方图和统计分析

# src/frontend/backtest_config_manager.py
## BacktestConfigManager
- 负责回测配置的集中管理和UI渲染
- 提供统一的配置参数访问接口

### DUTIES
- `配置参数管理`: 管理回测配置参数的存储和验证
- `UI组件渲染`: 渲染配置相关的Streamlit UI组件
- `参数验证`: 验证配置参数的合法性和业务逻辑约束
- `默认值管理`: 提供合理的默认配置值

### PROPERTIES
- `backtest_config`: 当前回测配置对象实例
- `default_config`: 默认配置参数字典

### METHODS
- `__init__(backtest_config)`: 初始化配置管理器
- `render_basic_config_ui()`: 渲染基础配置UI组件
- `render_position_strategy_ui()`: 渲染仓位策略配置UI
- `render_advanced_config_ui()`: 渲染高级配置UI组件
- `get_config()`: 获取当前配置对象
- `update_config(params)`: 更新配置参数
- `validate_config()`: 验证配置完整性

# src/frontend/rule_group_manager.py
## RuleGroupManager
- 负责规则组的管理和UI渲染
- 提供规则语法验证和预设规则组功能

### DUTIES
- `规则组管理`: 管理规则组的创建、加载、保存和删除
- `规则验证`: 验证规则表达式的语法正确性
- `预设规则`: 提供预设的常用规则组模板
- `UI渲染`: 渲染规则编辑和管理相关的UI组件

### PROPERTIES
- `rule_groups`: 规则组字典存储
- `preset_rules`: 预设规则组模板
- `current_group`: 当前选中的规则组

### METHODS
- `__init__()`: 初始化规则组管理器
- `render_rule_editor_ui(rule_type, default_value, key_suffix, height)`: 渲染规则编辑器UI
- `render_rule_group_ui()`: 渲染规则组管理UI
- `validate_rule(rule_expression)`: 验证规则语法
- `save_rule_group(name, rules)`: 保存规则组
- `load_rule_group(name)`: 加载规则组
- `delete_rule_group(name)`: 删除规则组
- `get_preset_rules()`: 获取预设规则组

# src/frontend/strategy_mapping_manager.py
## StrategyMappingManager
- 负责多股票策略映射配置管理
- 支持为不同股票选择不同的策略配置

### DUTIES
- `策略映射管理`: 管理股票到策略的映射关系
- `多符号配置`: 支持多股票模式下的策略配置
- `UI渲染`: 渲染策略映射配置UI组件
- `配置验证`: 验证策略映射配置的完整性

### PROPERTIES
- `strategy_mapping`: 策略映射配置字典
- `available_strategies`: 可用策略类型列表

### METHODS
- `__init__()`: 初始化策略映射管理器
- `render_multi_symbol_strategy_ui(selected_options, rule_group_manager, config_manager)`: 渲染多股票策略配置UI
- `get_strategy_for_symbol(symbol)`: 获取指定股票的策略配置
- `update_strategy_mapping(symbol, strategy_config)`: 更新策略映射配置
- `validate_mapping_config()`: 验证映射配置完整性

# src/frontend/backtest_executor.py
## BacktestExecutor
- 负责回测执行流程的管理
- 提供统一的回测执行接口和进度跟踪

### DUTIES
- `回测执行`: 管理回测引擎的执行流程
- `数据加载`: 协调数据加载和预处理
- `进度跟踪`: 提供回测进度监控和状态反馈
- `错误处理`: 处理回测过程中的异常和错误

### PROPERTIES
- `backtest_engine`: 回测引擎实例
- `progress_service`: 进度服务实例
- `current_status`: 当前执行状态

### METHODS
- `__init__(config, data)`: 初始化回测执行器
- `execute_backtest()`: 执行回测流程
- `execute_multi_symbol_backtest()`: 执行多符号回测
- `get_progress()`: 获取当前进度
- `cancel_backtest()`: 取消回测执行
- `get_results()`: 获取回测结果

# src/frontend/results_display_manager.py
## ResultsDisplayManager
- 负责回测结果的显示和分析
- 提供统一的性能指标计算和可视化接口

### DUTIES
- `结果展示`: 管理回测结果的显示和布局
- `性能分析`: 计算和展示性能指标
- `可视化`: 协调图表服务的可视化渲染
- `报告生成`: 生成回测分析报告

### PROPERTIES
- `backtest_results`: 回测结果数据
- `chart_service`: 图表服务实例
- `performance_metrics`: 性能指标计算结果

### METHODS
- `__init__(results, chart_service)`: 初始化结果展示管理器
- `render_results_ui()`: 渲染结果展示UI
- `calculate_performance_metrics(results)`: 计算性能指标
- `render_performance_tab()`: 渲染性能分析标签页
- `render_charts_tab()`: 渲染图表标签页
- `render_details_tab()`: 渲染详细数据标签页
- `generate_report()`: 生成回测报告

# src/frontend/backtest_config_ui.py
## BacktestConfigUI
- 负责回测范围配置的UI组件渲染
- 提供日期、频率、股票选择等配置界面

### DUTIES
- `日期配置`: 渲染回测日期范围选择UI
- `频率配置`: 渲染数据频率选择UI
- `股票选择`: 渲染多股票选择UI组件
- `配置摘要`: 显示当前配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `date_config`: 日期配置参数
- `frequency_config`: 频率配置参数

### METHODS
- `__init__(session_state)`: 初始化配置UI组件
- `render_date_config_ui()`: 渲染日期配置UI
- `render_frequency_config_ui()`: 渲染频率配置UI
- `render_stock_selection_ui()`: 渲染股票选择UI
- `render_config_summary()`: 渲染配置摘要

# src/frontend/strategy_config_ui.py
## StrategyConfigUI
- 负责策略相关配置的UI组件渲染
- 提供策略选择、规则编辑等配置界面

### DUTIES
- `策略选择`: 渲染策略类型选择UI
- `规则编辑`: 渲染自定义规则编辑UI
- `多股票策略`: 渲染多股票策略配置UI
- `策略摘要`: 显示策略配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `strategy_types`: 可用策略类型列表
- `rule_templates`: 规则模板配置

### METHODS
- `__init__(session_state)`: 初始化策略配置UI组件
- `render_strategy_selection_ui()`: 渲染策略选择UI
- `render_custom_rules_ui(rule_group_manager, strategy_type)`: 渲染自定义规则UI
- `render_multi_symbol_strategy_ui(selected_options, rule_group_manager, config_manager)`: 渲染多股票策略UI
- `render_strategy_summary()`: 渲染策略配置摘要

# src/frontend/position_config_ui.py
## PositionConfigUI
- 负责仓位相关配置的UI组件渲染
- 提供仓位策略、基础参数等配置界面

### DUTIES
- `仓位策略`: 渲染仓位策略选择UI
- `参数配置`: 渲染策略参数配置UI
- `基础配置`: 渲染基础参数配置UI
- `配置摘要`: 显示仓位配置摘要信息

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `position_strategies`: 可用仓位策略列表
- `config_params`: 配置参数字典

### METHODS
- `__init__(session_state)`: 初始化仓位配置UI组件
- `render_position_strategy_ui()`: 渲染仓位策略UI
- `render_basic_config_ui()`: 渲染基础配置UI
- `render_config_summary()`: 渲染配置摘要
- `_render_fixed_percent_ui()`: 渲染固定比例策略UI
- `_render_kelly_ui()`: 渲染凯利公式策略UI
- `_render_martingale_ui()`: 渲染马丁格尔策略UI

# src/frontend/results_display_ui.py
## ResultsDisplayUI
- 负责回测结果的UI组件渲染
- 提供多标签页结果展示界面

### DUTIES
- `结果标签页`: 渲染多标签页结果展示布局
- `摘要显示`: 渲染回测摘要标签页
- `交易记录`: 渲染交易记录标签页
- `仓位明细`: 渲染仓位明细标签页
- `净值曲线`: 渲染净值曲线标签页

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `chart_service`: 图表服务实例
- `results_data`: 回测结果数据

### METHODS
- `__init__(session_state)`: 初始化结果展示UI组件
- `render_results_tabs(results, backtest_config)`: 渲染结果展示标签页
- `render_summary_tab(results, backtest_config)`: 渲染回测摘要标签页
- `render_trades_tab(results)`: 渲染交易记录标签页
- `render_positions_tab(results)`: 渲染仓位明细标签页
- `render_equity_chart_tab(results)`: 渲染净值曲线标签页

# src/frontend/data_loader.py
## DataLoader
- 负责统一的数据加载和预处理服务
- 提供单股票和多股票数据加载接口

### DUTIES
- `数据加载`: 异步加载回测所需数据
- `数据验证`: 验证数据质量和完整性
- `数据预处理`: 准备引擎所需数据格式
- `缓存管理`: 管理数据加载缓存

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `data_cache`: 数据缓存字典
- `validation_rules`: 数据验证规则

### METHODS
- `__init__(session_state)`: 初始化数据加载服务
- `load_backtest_data(backtest_config)`: 加载回测数据
- `_load_single_stock_data(config, symbol)`: 加载单股票数据
- `_load_multiple_stock_data(config, symbols)`: 加载多股票数据
- `prepare_engine_data(loaded_data, config)`: 准备引擎数据
- `validate_data_quality(data, config)`: 验证数据质量
- `get_data_summary(data, config)`: 获取数据摘要

# src/frontend/callback_services.py
## CallbackServices
- 负责回调函数的管理和服务
- 提供统一的按钮回调和事件处理接口

### DUTIES
- `回调管理`: 管理所有按钮回调函数
- `事件处理`: 处理事件处理器注册
- `状态管理`: 管理回测状态转换
- `错误处理`: 处理回测错误回调

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `callbacks`: 回调函数字典
- `event_handlers`: 事件处理器实例

### METHODS
- `__init__(session_state)`: 初始化回调服务
- `create_backtest_callback()`: 创建回测按钮回调
- `create_refresh_callback(data_loader)`: 创建刷新按钮回调
- `create_signal_handler(engine)`: 创建信号处理回调
- `register_event_handlers(engine)`: 注册事件处理器
- `handle_backtest_completion(results, success)`: 处理回测完成回调
- `handle_backtest_error(error)`: 处理回测错误回调
- `reset_backtest_state()`: 重置回测状态

# src/frontend/event_handlers.py
## EventHandlers
- 负责事件处理逻辑的管理
- 提供上下文感知的事件处理器

### DUTIES
- `事件处理`: 管理所有事件处理逻辑
- `上下文管理`: 添加上下文信息到事件
- `进度跟踪`: 更新回测进度状态
- `状态管理`: 管理回测运行状态

### PROPERTIES
- `session_state`: Streamlit会话状态对象
- `progress_tracker`: 进度跟踪器
- `status_manager`: 状态管理器

### METHODS
- `__init__(session_state)`: 初始化事件处理器
- `create_signal_handler(engine)`: 创建信号事件处理器
- `create_schedule_handler(engine)`: 创建调度事件处理器
- `register_all_handlers(engine)`: 注册所有事件处理器
- `handle_backtest_start(engine)`: 处理回测开始事件
- `handle_backtest_end(results)`: 处理回测结束事件
- `handle_backtest_error(error)`: 处理回测错误事件
- `cleanup_after_backtest()`: 回测后清理

# src/services/chart_service.py
## ChartService
- 负责通用图表渲染和可视化组件
- 提供统一的图表配置管理和主题系统
- 支持多种图表类型和技术指标可视化

### DUTIES
- `基础图表渲染`: K线图、成交量图、资金流向图等
- `技术指标可视化`: MA、MACD、RSI等指标叠加
- `图表配置管理`: 统一的配置管理和主题系统
- `工厂模式支持`: 动态创建图表实例和指标装饰
- `数据容器管理`: DataBundle数据统一管理

### PROPERTIES
- `data_bundle`: DataBundle数据容器实例
- `figure`: 当前图表Figure对象
- `config`: 图表配置对象
- `_selected_primary_fields`: 主图选中字段
- `_selected_secondary_fields`: 副图选中字段
- `_chart_types`: 图表类型映射

### METHODS
- `render_chart_controls()`: 渲染图表配置控件
- `render_chart_button()`: 渲染作图按钮
- `create_kline()`: 创建K线图（工厂模式）
- `create_volume_chart()`: 创建成交量图
- `create_capital_flow_chart()`: 创建资金流图表
- `create_combined_chart()`: 创建组合图表
- `draw_equity_and_allocation()`: 绘制净值与资产配置图表
- `drawMA()`: 绘制均线指标
- `drawMACD()`: 绘制MACD指标
- `drawBollingerBands()`: 绘制布林带指标
- `drawRSI()`: 绘制RSI指标
- `render_ma()`: 渲染均线组件

### 图表类型支持
- `CandlestickChart`: K线图表实现
- `VolumeChart`: 成交量图表实现
- `CapitalFlowChart`: 资金流图表实现
- `IndicatorDecorator`: 指标装饰器
- 工厂模式支持动态图表创建

