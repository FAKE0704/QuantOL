# SQLite数据库锁定问题修复方案

## 问题描述

用户在"系统设置"中选择使用SQLite数据库和tushare数据源，点击历史行情功能页后出现以下错误：

```
[2025-11-15 21:33:15,514] [ERROR] [sqlite_adapter] 批量插入失败: database is locked
[2025-11-15 21:33:15,514] [ERROR] [sqlite_adapter] 获取所有股票信息失败: database is locked
```

## 根本原因分析

### 1. 技术原因
- **单连接瓶颈**：原SQLiteAdapter使用单个连接处理所有并发操作
- **事务管理不当**：`_update_stock_info`方法中DELETE后立即executemany产生锁竞争
- **PRAGMA配置不完整**：缺少关键的并发和性能优化参数
- **缺少重试机制**：没有处理SQLITE_BUSY和SQLITE_LOCKED错误的恢复策略

### 2. SQLite特性限制
- SQLite在同一个数据库连接上不支持真正的并发写入
- 写操作会锁定整个数据库文件
- 默认的busy_timeout设置为0，导致立即失败

## 解决方案

### 1. 增强连接池管理
```python
# 从单连接改为连接池
self.pools: List[aiosqlite.Connection] = []
self._max_connections = 3  # 可配置
self._pool_index = 0       # 轮询分配连接
self._pool_lock = asyncio.Lock()
```

### 2. 智能重试机制
```python
async def _execute_with_retry(self, conn, query, parameters=None, max_retries=3):
    """带重试机制的数据库操作执行"""
    for attempt in range(max_retries):
        try:
            return await conn.execute(query, parameters)
        except Exception as e:
            if self._is_locked_error(e):
                if attempt == max_retries - 1:
                    raise
                delay = (2 ** attempt) + random.uniform(0, 1)  # 指数退避
                await asyncio.sleep(delay)
            else:
                raise
```

### 3. 优化PRAGMA配置
```python
# 完善的性能优化设置
PRAGMA busy_timeout = 30000          # 30秒超时
PRAGMA journal_mode = WAL           # 写前日志模式
PRAGMA synchronous = NORMAL         # 平衡性能和安全
PRAGMA cache_size = -64000          # 64MB缓存
PRAGMA mmap_size = 268435456        # 256MB内存映射
PRAGMA wal_autocheckpoint = 1000    # 自动检查点
PRAGMA journal_size_limit = 1048576 # 1MB日志限制
```

### 4. 批量操作优化
```python
async def _update_stock_info(self, df: pd.DataFrame) -> tuple:
    """更新StockInfo表数据（优化版）"""
    async with conn.transaction():
        await self._execute_with_retry(conn, "DELETE FROM StockInfo")

        # 分批插入，每批1000条记录
        batch_size = self._batch_size
        for i in range(0, len(valid_data), batch_size):
            batch = valid_data[i:i + batch_size]
            await self._executemany_with_retry(conn, query, batch)

            # 批次间短暂暂停，让其他操作有机会访问数据库
            if i + batch_size < len(valid_data):
                await asyncio.sleep(0.01)
```

### 5. 环境变量配置
新增SQLite专用配置选项：

```bash
# SQLite 专用性能配置 (解决数据库锁定问题)
SQLITE_MAX_CONNECTIONS=3          # 连接池大小，建议2-5
SQLITE_BUSY_TIMEOUT=30000        # 忙等待超时(毫秒)，建议30000-60000
SQLITE_CACHE_SIZE=-64000         # 缓存大小(KB)，负值表示KB
SQLITE_MMAP_SIZE=268435456       # 内存映射大小，256MB
SQLITE_BATCH_SIZE=1000           # 批量操作大小
SQLITE_WAL_AUTO_CHECKPOINT=1000  # WAL自动检查点间隔
SQLITE_JOURNAL_LIMIT=1048576     # 日志大小限制，1MB
```

## 实施效果

### 1. 错误恢复能力
- 自动重试机制处理临时性锁定
- 指数退避算法减少重试冲突
- 详细的错误日志和诊断信息

### 2. 性能提升
- 连接池支持真正的并发读取
- 优化的PRAGMA设置提高查询性能
- 分批操作减少长时间锁定

### 3. 配置灵活性
- 环境变量支持运行时配置调整
- 可根据硬件环境优化参数
- 便于不同场景下的性能调优

## 监控和诊断

### 1. 连接池状态监控
```python
def get_pool_status(self) -> dict:
    return {
        "db_type": "sqlite",
        "pool_size": len(self.pools),
        "max_connections": self._max_connections,
        "current_connection_index": self._pool_index,
        "busy_timeout": self._busy_timeout,
        "connected": len(self.pools) > 0
    }
```

### 2. 详细日志记录
- 锁定重试的详细日志
- 批量操作进度跟踪
- 性能指标记录

## 最佳实践建议

### 1. 生产环境配置
```bash
SQLITE_MAX_CONNECTIONS=5          # 增加连接数
SQLITE_BUSY_TIMEOUT=60000        # 延长超时时间
SQLITE_BATCH_SIZE=500            # 减小批量大小
```

### 2. 开发环境配置
```bash
SQLITE_MAX_CONNECTIONS=3          # 适中的连接数
SQLITE_BUSY_TIMEOUT=30000        # 标准超时时间
SQLITE_BATCH_SIZE=1000           # 标准批量大小
```

### 3. 资源受限环境
```bash
SQLITE_MAX_CONNECTIONS=2          # 最小连接数
SQLITE_MMAP_SIZE=134217728        # 减小内存映射
SQLITE_CACHE_SIZE=-32000          # 减小缓存
```

## 总结

这个修复方案通过多层次的改进解决了SQLite数据库锁定问题：

1. **架构层面**：从单连接改为连接池，支持并发操作
2. **算法层面**：实现智能重试和指数退避机制
3. **配置层面**：优化PRAGMA参数和环境变量配置
4. **操作层面**：改进批量操作策略和事务管理

实施后，历史行情页面应该能够正常加载股票列表，不再出现"database is locked"错误。同时，系统的整体稳定性和性能也得到了显著提升。