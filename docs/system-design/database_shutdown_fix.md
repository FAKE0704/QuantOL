# 数据库连接检查失败问题修复方案

## 问题现象
- `_is_stock_info_up_to_date()`方法检查StockInfo表状态失败
- 发生在数据库初始化后约1分钟
- 日志显示连接数从0变为1，可能有连接泄漏

## 根本原因
1. 表状态检查SQL性能问题
2. 连接池配置不合理(max_inactive_connection_lifetime=60)
3. 缺少重试机制

## 解决方案

### 1. SQL优化
```sql
-- 原查询
SELECT MAX(ipoDate) FROM StockInfo

-- 优化为
SELECT ipoDate FROM StockInfo ORDER BY ipoDate DESC LIMIT 1
```

### 2. 连接池配置调整
```python
self.pool = await asyncpg.create_pool(
    max_inactive_connection_lifetime=300,  # 延长到5分钟
    ...
)
```

### 3. 添加重试逻辑
```python
async def _is_stock_info_up_to_date(self, max_retries=3):
    for attempt in range(max_retries):
        try:
            # 原有检查逻辑
            ...
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
```

## 实施步骤
1. [ ] 优化SQL查询
2. [ ] 调整连接池参数
3. [ ] 添加重试机制
4. [ ] 更新单元测试