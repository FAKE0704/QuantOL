# Backtesting Module

## BacktestConfig
### Responsibilities
- 负责管理回测所需的所有参数配置

### Attributes
- `initial_capital (float)`: 初始资金，默认100万
- `commission_rate (float)`: 单笔交易手续费率（百分比值），默认0.0005
- `slippage (float)`: 滑点率，默认0.001
- `start_date (str)`: 回测开始日期，格式'YYYY-MM-DD'
- `end_date (str)`: 回测结束日期，格式'YYYY-MM-DD'
- `target_symbol (str)`: 目标交易标的代码
- `monthly_investment (Optional[float])`: 每月定投金额
- `stop_loss (Optional[float])`: 止损比例
- `take_profit (Optional[float])`: 止盈比例
- `max_holding_days (Optional[int])`: 最大持仓天数
- `extra_params (Dict[str, Any])`: 额外参数存储

## BacktestEngine
### Responsibilities
- 负责执行回测流程

### Attributes
- `portfolio: BacktestPortfolioAdapter`
  - `available_cash`: 返回当前可用现金
  - `total_value`: 计算总资产价值（现金 + 持仓市值）
  - `get_position()`: 获取当前持仓数量
  - `get_strategy_limit()`: 获取策略的最大持仓比例（默认20%）
- `equity_records`: 净值记录

### Methods
- `get_results() -> dict`: 获取回测结果
- `_handle_fill_event(fill_event: FillEvent)`: 订单完成后处理事件
- `_validate_order_risk(order: dict) -> bool`: 使用RiskManager进行风险检查
- `_create_portfolio() -> BacktestPortfolioAdapter`: 创建回测组合适配器

## Implementation Progress
- ✅ 回测配置管理
- ✅ 回测引擎框架
- ✅ 净值记录功能
- ⏳ 完整回测流程