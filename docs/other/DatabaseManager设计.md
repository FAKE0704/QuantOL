# 核心类结构
## DatabaseManager 类
- 功能：作为数据库操作的总入口，负责连接池管理、表结构初始化、数据操作与监控。  

### 关键属性

  ```python
  self.pool = None          # 异步连接池（asyncpg.create_pool）
  self._loop = None         # 绑定的事件循环
  self.connection_config    # 数据库连接配置
  self.active_connections   # 活跃连接跟踪（字典）
  self._conn_lock           # 异步锁（控制并发访问）
  ```

---

### 方法

#### 连接池管理
##### `_create_pool()`  

- 功能：创建异步连接池，配置连接参数（最大连接数、超时时间等）。  

- 技术细节：  

    ```python
    await asyncpg.create_pool(loop=..., min_size=3, max_size=15, ...)
    ```

##### `_get_connection()`  

- 功能：异步获取数据库连接，确保通过上下文管理器（`async with`）释放资源。  

- 异常处理：捕获连接获取失败并记录日志。


#### 表结构初始化  
##### `_init_db_tables()`  

- 功能：异步创建表（`StockData`, `StockInfo`, `PoliticalEvents`），使用 `IF NOT EXISTS` 避免重复建表。  

- 示例：  

    ```python
    await conn.execute("CREATE TABLE IF NOT EXISTS StockData (...)")
    ```

#### 数据操作  
##### `save_stock_info()`  

- 功能：插入或更新股票基本信息，使用 `ON CONFLICT` 处理唯一约束冲突。  

- 参数：`code, code_name, ipo_date` 等字段。


##### `check_data_completeness()`  

- 功能：异步检查数据完整性，结合交易日历排除节假日，返回缺失日期区间。  

- 核心逻辑：比对数据库已有日期与理论交易日集合。


##### `load_stock_data()`  

- 功能：加载数据时自动补全缺失数据（调用外部数据源 `BaostockDataSource`）。  

- 流程：  

    1. 检查数据完整性 → 2. 调用外部接口 → 3. 保存新数据 → 4. 返回合并结果。

#####  `del_stock_data()`  

- 功能：异步删除表，并二次验证表是否存在（通过 `pg_tables` 系统表查询）。  

- 安全设计：避免误删非空表。


#### 连接状态监控与维护  
#####  `get_pool_status()`  

- 功能：返回连接池状态（活跃连接数、最大容量等），用于性能监控。  


##### `monitor_connections()`  

- 功能：定期记录连接池状态（异步定时任务），支持运维调试。


---

#### 扩展方法**  
##### `_is_stock_info_up_to_date()`  

- 功能：检查 `StockInfo` 表是否最新（基于最大 IPO 日期），用于触发数据更新。  


##### `_validate_stock_info()`  

- 功能：验证股票信息格式（必填字段、日期格式），确保数据质量。  


##### `_update_stock_info()`  

- 功能：批量更新 `StockInfo` 表，支持清空旧数据并插入新数据（`TRUNCATE + INSERT`）。


---


### 调用逻辑
1. 类的实例化
2. 表结构初始化