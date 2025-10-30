# Trader Execution Modules

## TradeOrderManager(BaseTrader)
### Responsibilities
- 负责订单生命周期管理（创建、修改、取消、状态管理、数据库操作）
- process_orders：处理等待中的订单，使用注入的trader执行订单

## TradeExecutionEngine
### Responsibilities
- 负责交易指令生成

## TradeRecorder
### Responsibilities
- 交易记录管理

## BaseTrader
### Responsibilities
- 交易器基类

## BacktestTrader(BaseTrader)
### Responsibilities
- 负责订单实际执行和事件转换
- execute_order：回测时处理OrderEvent并返回FillEvent

## LiveTrader(BaseTrader)
### Responsibilities
- 负责实际执行和事件转换

## Implementation Progress
- ✅ 基础交易器框架
- ✅ 回测交易器实现
- ⏳ 实盘交易器完善
- ⏳ 订单生命周期管理