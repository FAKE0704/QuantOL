# DatabaseManager

## Responsibilities
- 负责数据库连接池管理（asyncpg实现）
- 表结构初始化
- 股票数据CRUD操作
- 数据完整性检查

## Attributes
- pool: asyncpg连接池对象

## Methods
- `async save_order(order: dict) -> int`: 异步保存订单
- `async update_order_status(order_id: int, status: str)`: 更新订单状态
- `async log_execution(execution_data: dict)`: 交易执行结果日志记录
- `async record_trade(trade_data: dict)`: 交易记录
- `async query_orders(filters: dict)`: 订单队列查询
- `async query_trades(filters: dict)`: 交易历史队列查询

## Implementation Progress
- ✅ 基础连接池管理
- ✅ 订单保存功能
- ⏳ 交易相关方法待实现

## TODOs
- 添加交易相关方法
- 完善数据完整性检查