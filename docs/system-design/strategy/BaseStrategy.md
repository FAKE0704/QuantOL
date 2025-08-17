# 生命周期状态：
- 采用有限状态机模型
初始化(INIT)、激活(ACTIVE)、休眠(DORMANT)、销毁(DESTROYED)

## INIT
- 触发条件：策略实例化时自动进入

- 行为：\
  ✓ 加载配置参数\
  ✓ 注册事件监听器\
  ✓ 初始化指标计算器



## ACTIVE
收到`StrategyActivateEvent`
行为：\
✓ 启动行情数据订阅\
✓ 开始生成交易信号\
✓ 响应定时任务事件

## DORMANT
- 触发条件：收到`StrategyDeactivateEvent`

- 行为：\
  ✓ 暂停信号生成\
  ✓ 保留持仓和状态快照\
  ✓ 停止消耗计算资源

- 典型场景：盘后分析、参数调整期


## DESTROYED

- 触发条件：收到`StrategyDestroyEvent`
- 行为：\
  ✓ 释放所有资源\
  ✓ 持久化最终状态\
  ✓ 注销事件监听



# 状态转换触发器：事件驱动（StrategyScheduleEvent等）

