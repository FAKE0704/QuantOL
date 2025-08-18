# 类 ​BacktestEngine
- 负责记录各类信息

- 负责时间推进和事件调度（生成、推送、处理）

# 数据存储
字段名称|数据类型|说明
-|-|-
event_queue|`List<Event>`|待处理事件队列（如行情更新、订单触发）
handlers|Dict<事件类型, EventHandler>|事件类型 → 处理函数的映射
strategy|Strategy|用户定义的交易策略逻辑
market_data|MarketData|当前最新市场快照（价格、成交量等）
trades|List<Trade>|模拟执行的所有交易记录
results|Dict|回测结果指标（收益率、最大回撤等）

# 关键操作接口
## 事件管理​
▸ register_handler(event_type, handler)
　→ 绑定指定事件类型​（如行情更新）到处理函数
▸ push_event(event)
　→ 向队列注入新事件（驱动回测流程）

## ​回测控制​
▸ run(start_date, end_date)
　→ ​启动回测​（核心入口，模拟指定时间段）
▸ get_results() → Dict
　→ 返回回测统计结果

## ​数据服务​
▸ update_market_data(data)
　→ 更新当前市场数据（模拟实时行情推送）
▸ get_historical_data(timestamp, lookback_days) → MarketData
　→ 查询历史时点的市场数据（供策略分析）

## ​交易模拟​
▸ create_order(symbol, quantity, side, price)
　→ 策略调用的下单接口（生成模拟订单）

## ​辅助功能​
▸ log_error(message)
　→ 记录错误信息（用于调试与监控）