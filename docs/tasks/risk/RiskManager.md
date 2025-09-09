# RiskManager

## Responsibilities
- 负责系统级风险控制（全局资金/仓位限额）
- 负责验证PositionStrategy的输出是否合规（风控）

## Input
- 所有策略的目标仓位
- 系统风险参数（总资金限额、集中度阈值）
- 实时账户状态

## Output
- 风险验证结果（通过/拒绝/调整建议）

## Attributes
- portfolio: PortfolioManager实例

## Methods
- `validate_order(order_data: dict) -> dict`: 验证订单风险是否通过
- `_check_funds(order_data: dict) -> bool`: 检查资金是否充足
- `_check_position(order_data: dict) -> bool`: 检查是否超过仓位限制

## Risk Control Rules
- 验证策略输出是否违反系统级风控规则（如总仓位≤总资金的50%）
- 动态调整仓位以符合全局约束（如自动缩减超限订单的数量）
- 单一标的持仓 ≤ 总资金的10%

## Known Issues
- RiskManager直接访问`portfolio.get_position()`和`portfolio.get_strategy_limit()`
- 可能导致RiskManager与Portfolio实现强耦合

## Implementation Progress
- ✅ 基础风险检查框架
- ✅ 资金充足性检查
- ✅ 仓位限制检查
- ⏳ 动态调整功能