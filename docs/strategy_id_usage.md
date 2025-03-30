# Strategy ID 使用说明

## 概述
`strategy_id` 是 `SignalEvent` 类中的一个重要字段，用于唯一标识生成信号的策略实例。它帮助系统在多策略环境下正确路由和处理信号。

## 主要用途

### 1. 策略身份识别
- 每个策略实例在创建时都会被分配一个唯一的 `strategy_id`
- 用于区分不同策略生成的信号
- 示例：`"dca_001"`, `"ma_crossover_002"`

### 2. 多策略支持
- 允许多个策略同时运行
- 确保每个策略的信号能够被正确识别和处理
- 避免信号混淆

### 3. 性能跟踪
- 记录每个策略的绩效指标
- 计算策略级别的盈利率、胜率等
- 生成详细的策略分析报告

### 4. 参数管理
- 支持策略级别的参数配置
- 允许动态调整策略参数
- 实现策略参数的历史记录和回滚

### 5. 信号路由
- 根据 `strategy_id` 将信号路由到正确的执行引擎
- 支持策略级别的执行规则
- 实现策略优先级管理

## 使用示例

```python
# 创建 SignalEvent
signal = SignalEvent(
    timestamp=datetime.now(),
    strategy_id="dca_001",  # 策略唯一标识
    signal_type="BUY",
    parameters={"amount": 1000},
    confidence=0.85
)

# 获取策略ID
strategy_id = signal.strategy_id
```

## 最佳实践
1. 保持 `strategy_id` 的唯一性和一致性
2. 使用有意义的命名规则，如 `策略类型_编号`
3. 在策略初始化时生成 `strategy_id`
4. 在日志和报告中记录 `strategy_id`
5. 避免在运行时修改 `strategy_id`

## 相关文档
- [策略开发指南](./strategy_development.md)
- [事件系统说明](./event_system.md)
- [性能跟踪机制](./performance_tracking.md)
