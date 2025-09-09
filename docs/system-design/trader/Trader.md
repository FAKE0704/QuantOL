- 在Trader模块中实现订单执行逻辑
__Trader实现分离__：
- 需要区分回测Trader和实盘Trader
- 回测Trader：模拟执行，考虑滑点/手续费
- 实盘Trader：连接交易所API执行真实交易
- 订单成交后生成FillEvent

- 回测引擎处理FillEvent更新持仓

# 流程
- 策略生成StrategySignalEvent

- 转换为OrderEvent（__信号转换条件__：
- 仓位控制：检查当前持仓是否超过策略限制
- 资金管理：验证可用资金是否足够
- 风险控制：评估交易风险指标
- 只有在满足所有条件时才转换为OrderEvent）

- 传递给Trader执行

- Trader执行成功后返回FillEvent

- 回测引擎根据FillEvent更新持仓


# 其他类的责任
- 策略信号到订单的转换应由`StrategyManager`类负责（位于`src/core/strategy/`）
- 转换过程需考虑仓位控制、资金管理等因素

RiskManager：负责仓位和风险管理
PositionTracker：实时跟踪持仓状态--可能在仓位策略中


实现RiskManager，Trader执行分离，其他的我需要再考虑一下


