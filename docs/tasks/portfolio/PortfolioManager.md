# PortfolioManager

## Responsibilities
- __投资组合管理__：管理整个投资组合的资产配置和持仓情况
- __资金管理__：跟踪和管理可用现金、初始资金和组合总价值,持仓状态管理
- __持仓操作__：执行买入、卖出等持仓更新操作历史记录
- __组合再平衡__：根据目标配置比例自动调整持仓
- __风险控制集成__：与风险管理系统集成进行风险检查
- 收益指标计算

## Attributes
- `equity_history`: 净值历史记录
  - `timestamp`: 时间戳
  - `total_value`: 总资产价值
  - `cash`: 当前现金
  - `positions_value`: 持仓市值
  - `return_pct`: 总收益率百分比
  - `drawdown_pct`: 当前回撤百分比
  - `peak_value`: 峰值资产价值

## Position Structure
- `stock`: 股票代码
- `quantity`: 持仓数量
- `avg_cost`: 平均成本
- `current_value`: 当前市值

## Methods
- `update_position(symbol: str, quantity: int, price: float)`: 更新持仓
- `get_portfolio_value() -> float`: 获取投资组合总价值
- `rebalance(target_allocations: dict)`: 组合再平衡
- `get_cash_balance() -> float`: 获取当前余额
- `get_total_return() -> float`: 计算总收益率

## Implementation Progress
- ✅ 投资组合基础管理
- ✅ 资金跟踪功能
- ✅ 持仓操作功能
- ⏳ 组合再平衡实现
- ⏳ 风险控制集成