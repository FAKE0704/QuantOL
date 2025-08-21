# PositionStrategy Modules

## PositionStrategy (Base Class)
### Responsibilities
- 仓位策略基类
- 基于策略逻辑生成目标仓位

### Input
- 市场数据（价格、波动率）
- 策略参数（风险偏好、杠杆率）
- 账户状态（当前持仓）

### Output
- 策略级别的目标仓位（如股票A买入200股）
- 计算信号强度
- 应用策略级风控

## FixedPercentStrategy(PositionStrategy)
### Methods
- `calculate_position(market_data: dict, params: dict) -> dict`: 计算仓位比例

## KellyStrategy(PositionStrategy)
### Methods
- `calculate_position(market_data: dict, params: dict) -> dict`: 计算凯利公式仓位

## Implementation Progress
- ✅ 仓位策略基类
- ✅ 固定比例策略
- ✅ 凯利公式策略
- ⏳ 更多策略类型