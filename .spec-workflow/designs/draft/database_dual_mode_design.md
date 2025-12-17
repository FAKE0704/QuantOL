# 数据库双模式支持设计文档

## 1. 设计概述

### 1.1 背景与问题
当前项目仅支持PostgreSQL数据库，存在以下问题：
- 新用户学习成本高，需要额外安装配置PostgreSQL
- 快速体验门槛高，无法"开箱即用"
- 部署复杂度影响用户采用率

### 1.2 设计目标
- 保持现有PostgreSQL性能优势的同时，提供SQLite作为快速体验选项
- 降低用户使用门槛，支持一键切换数据库模式
- 保持现有异步架构兼容性
- 提供预置数据包，支持离线快速体验

## 2. 技术方案

### 2.1 架构设计

#### 2.1.1 数据库适配器模式
```python
# 数据库适配器抽象基类
class DatabaseAdapter(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def create_connection_pool(self) -> Any:
        pass

    @abstractmethod
    async def execute_query(self, query: str, *args) -> Any:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

# PostgreSQL适配器（现有功能）
class PostgreSQLAdapter(DatabaseAdapter):
    async def initialize(self) -> None:
        # 现有的asyncpg逻辑
        pass

# SQLite适配器（新增功能）
class SQLiteAdapter(DatabaseAdapter):
    async def initialize(self) -> None:
        # 使用aiosqlite实现
        pass
```

#### 2.1.2 配置驱动切换
```env
# 数据库类型配置
DATABASE_TYPE=sqlite  # postgresql | sqlite

# SQLite配置（当DATABASE_TYPE=sqlite时使用）
SQLITE_DB_PATH=./data/quantdb.sqlite

# PostgreSQL配置（当DATABASE_TYPE=postgresql时使用）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantdb
DB_USER=quant
DB_PASSWORD=quant123
```

### 2.2 实现细节

#### 2.2.1 数据库工厂
```python
# src/core/data/database_factory.py
class DatabaseFactory:
    @staticmethod
    def create_adapter(config: Config) -> DatabaseAdapter:
        if config.DATABASE_TYPE == "sqlite":
            return SQLiteAdapter(config)
        elif config.DATABASE_TYPE == "postgresql":
            return PostgreSQLAdapter(config)
        else:
            raise ValueError(f"不支持的数据库类型: {config.DATABASE_TYPE}")

# 工厂函数（保持向后兼容）
def get_db_adapter() -> DatabaseAdapter:
    config = get_config()
    return DatabaseFactory.create_adapter(config)
```

#### 2.2.2 表结构兼容性
```sql
-- SQLite表结构（与PostgreSQL保持兼容）
CREATE TABLE StockData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    amount REAL,
    adjustflag TEXT,
    frequency TEXT NOT NULL,
    UNIQUE (code, date, time, frequency)
);

-- 其他表结构类似，主要差异：
-- SERIAL -> INTEGER PRIMARY KEY AUTOINCREMENT
-- NUMERIC -> REAL
-- VARCHAR -> TEXT
```

#### 2.2.3 异步兼容性
```python
# src/core/data/sqlite_adapter.py
import aiosqlite
from typing import Any, Optional

class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, config: Config):
        self.config = config
        self.pool: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.config.SQLITE_DB_PATH), exist_ok=True)

        # 创建连接
        self.pool = await aiosqlite.connect(self.config.SQLITE_DB_PATH)

        # 启用外键约束
        await self.pool.execute("PRAGMA foreign_keys = ON")

        # 创建表结构
        await self._create_tables()

    async def create_connection_pool(self) -> aiosqlite.Connection:
        if not self.pool:
            await self.initialize()
        return self.pool

    async def execute_query(self, query: str, *args) -> Any:
        if not self.pool:
            await self.initialize()

        # 适配PostgreSQL的查询语法到SQLite
        sqlite_query = self._convert_query_syntax(query)

        if query.strip().upper().startswith('SELECT'):
            return await self.pool.execute_fetchall(sqlite_query, *args)
        else:
            return await self.pool.execute(sqlite_query, *args)

    def _convert_query_syntax(self, query: str) -> str:
        """转换PostgreSQL语法到SQLite语法"""
        # 处理数据类型差异
        query = query.replace('SERIAL', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        query = query.replace('NUMERIC', 'REAL')
        query = query.replace('VARCHAR', 'TEXT')

        # 处理函数差异
        query = query.replace('NOW()', "datetime('now')")
        query = query.replace('TRUE', '1')
        query = query.replace('FALSE', '0')

        return query
```

### 2.3 数据迁移策略

#### 2.3.1 数据导出功能
```python
# src/core/data/migration.py
class DataExporter:
    @staticmethod
    async def export_to_sqlite(pg_adapter: PostgreSQLAdapter,
                             sqlite_path: str) -> None:
        """将PostgreSQL数据导出为SQLite文件"""

        sqlite_adapter = SQLiteAdapter(sqlite_path)
        await sqlite_adapter.initialize()

        # 导出各个表的数据
        tables = ['StockData', 'StockInfo', 'PoliticalEvents', 'MoneySupplyData']

        for table in tables:
            data = await pg_adapter.execute_query(f"SELECT * FROM {table}")
            await sqlite_adapter._bulk_insert(table, data)

class DataImporter:
    @staticmethod
    async def import_from_sqlite(sqlite_path: str,
                               pg_adapter: PostgreSQLAdapter) -> None:
        """将SQLite数据导入PostgreSQL"""
        sqlite_adapter = SQLiteAdapter(sqlite_path)
        await sqlite_adapter.initialize()

        tables = ['StockData', 'StockInfo', 'PoliticalEvents', 'MoneySupplyData']

        for table in tables:
            data = await sqlite_adapter.execute_query(f"SELECT * FROM {table}")
            await pg_adapter._bulk_insert(table, data)
```

#### 2.3.2 预置数据包
```python
# scripts/create_sample_data.py
async def create_sample_sqlite():
    """创建包含示例数据的SQLite文件"""

    # 1. 创建SQLite数据库
    sqlite_path = "./data/sample_quantdb.sqlite"
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)

    # 2. 初始化表结构
    adapter = SQLiteAdapter(sqlite_path)
    await adapter.initialize()

    # 3. 插入示例数据
    sample_data = get_sample_stock_data()
    await adapter._bulk_insert('StockData', sample_data)

    # 4. 添加政治事件示例
    political_events = get_sample_political_events()
    await adapter._bulk_insert('PoliticalEvents', political_events)

    print(f"示例数据库已创建: {sqlite_path}")
```

## 3. 用户体验改进

### 3.1 一键切换功能
```python
# src/cli/database_switch.py
import click

@click.command()
@click.option('--type', type=click.Choice(['sqlite', 'postgresql']))
def switch_database(type):
    """切换数据库类型"""

    # 更新配置文件
    config_path = '.env'
    with open(config_path, 'r') as f:
        content = f.read()

    content = re.sub(r'DATABASE_TYPE=.*', f'DATABASE_TYPE={type}', content)

    with open(config_path, 'w') as f:
        f.write(content)

    if type == 'sqlite':
        # 创建示例数据
        asyncio.run(create_sample_sqlite())
        click.echo("已切换到SQLite模式，示例数据已生成")
    else:
        click.echo("已切换到PostgreSQL模式")

# 添加到Streamlit界面
def render_database_settings():
    st.sidebar.subheader("数据库设置")

    db_type = st.sidebar.selectbox(
        "选择数据库类型",
        ["sqlite", "postgresql"],
        index=["sqlite", "postgresql"].index(config.DATABASE_TYPE)
    )

    if db_type != config.DATABASE_TYPE:
        if st.sidebar.button(f"切换到{db_type.upper()}"):
            switch_database.callback(type=db_type)
            st.experimental_rerun()
```

### 3.2 数据库状态检查
```python
# src/utils/database_health.py
async def check_database_health():
    """检查数据库状态"""
    adapter = get_db_adapter()

    try:
        # 测试连接
        await adapter.initialize()

        # 检查表是否存在
        tables = await adapter.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )

        # 检查数据量
        stock_data_count = await adapter.execute_query(
            "SELECT COUNT(*) FROM StockData"
        )

        return {
            "status": "healthy",
            "tables": len(tables),
            "stock_data_count": stock_data_count[0][0]
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

## 4. 部署与使用指南

### 4.1 SQLite模式快速开始
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 切换到SQLite模式
python -m src.cli.database_switch --type sqlite

# 3. 启动应用（会自动创建数据库和示例数据）
streamlit run main.py
```

### 4.2 PostgreSQL模式（现有用户）
```bash
# 配置保持不变
DATABASE_TYPE=postgresql

# 启动PostgreSQL服务
docker-compose up -d

# 启动应用
streamlit run main.py
```

### 4.3 数据迁移
```bash
# PostgreSQL到SQLite
python -m src.cli.migration --from postgresql --to sqlite --output ./data/my_data.sqlite

# SQLite到PostgreSQL
python -m src.cli.migration --from sqlite --to postgresql --input ./data/my_data.sqlite
```

## 5. 性能考虑

### 5.1 性能对比
| 特性 | PostgreSQL | SQLite |
|------|------------|--------|
| 并发性能 | 优秀 | 一般 |
| 数据一致性 | 强 | 基础 |
| 部署复杂度 | 中等 | 简单 |
| 存储大小 | 中等 | 小 |
| 适合场景 | 生产环境 | 开发/演示 |

### 5.2 优化策略
```python
# SQLite性能优化
class SQLiteAdapter(DatabaseAdapter):
    async def initialize(self) -> None:
        # ... 其他初始化代码

        # 性能优化设置
        await self.pool.execute("PRAGMA journal_mode = WAL")
        await self.pool.execute("PRAGMA synchronous = NORMAL")
        await self.pool.execute("PRAGMA cache_size = 10000")
        await self.pool.execute("PRAGMA temp_store = MEMORY")
```

## 6. 测试策略

### 6.1 单元测试
```python
# tests/test_database_adapter.py
@pytest.mark.asyncio
async def test_sqlite_adapter():
    """测试SQLite适配器基本功能"""
    adapter = SQLiteAdapter(":memory:")
    await adapter.initialize()

    # 测试数据插入
    await adapter.execute_query(
        "INSERT INTO StockData (code, date, open, close) VALUES (?, ?, ?, ?)",
        ("000001", "2024-01-01", 10.0, 11.0)
    )

    # 测试数据查询
    result = await adapter.execute_query("SELECT * FROM StockData")
    assert len(result) == 1

@pytest.mark.asyncio
async def test_adapter_compatibility():
    """测试两种适配器的兼容性"""
    pg_adapter = PostgreSQLAdapter(pg_config)
    sqlite_adapter = SQLiteAdapter(":memory:")

    await pg_adapter.initialize()
    await sqlite_adapter.initialize()

    # 执行相同查询，验证结果一致性
    pg_result = await pg_adapter.execute_query("SELECT COUNT(*) FROM StockData")
    sqlite_result = await sqlite_adapter.execute_query("SELECT COUNT(*) FROM StockData")

    # 注意：在空数据库下结果应该一致
    assert pg_result[0][0] == sqlite_result[0][0]
```

### 6.2 集成测试
```python
# tests/test_database_switch.py
@pytest.mark.asyncio
async def test_database_switch():
    """测试数据库切换功能"""

    # 切换到SQLite模式
    switch_database.callback(type="sqlite")
    assert get_config().DATABASE_TYPE == "sqlite"

    # 验证SQLite适配器正常工作
    adapter = get_db_adapter()
    assert isinstance(adapter, SQLiteAdapter)
    await adapter.initialize()

    # 切换到PostgreSQL模式
    switch_database.callback(type="postgresql")
    assert get_config().DATABASE_TYPE == "postgresql"
```

## 7. 风险评估与缓解

### 7.1 技术风险
| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| SQLite性能瓶颈 | 中 | 高 | 提供性能监控，建议大数据量使用PostgreSQL |
| 数据迁移失败 | 高 | 低 | 完整的备份恢复机制，事务支持 |
| 语法兼容性问题 | 中 | 中 | 全面的测试覆盖，语法转换层 |

### 7.2 用户体验风险
| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 配置复杂化 | 低 | 中 | 提供默认配置，一键切换工具 |
| 数据不一致 | 高 | 低 | 数据完整性检查，版本控制 |

## 8. 实施计划

### 8.1 开发阶段
1. **Phase 1** (1-2周): 实现SQLite适配器
2. **Phase 2** (1周): 数据库工厂和配置切换
3. **Phase 3** (1周): 数据迁移工具
4. **Phase 4** (1周): 用户界面集成
5. **Phase 5** (1周): 测试和文档完善

### 8.2 部署策略
- 保持向后兼容，现有用户无需修改配置
- 新版本默认使用SQLite模式，降低新用户门槛
- 提供详细的迁移指南和最佳实践文档

## 9. 总结

本设计通过引入数据库适配器模式，在保持现有PostgreSQL性能优势的同时，提供SQLite作为快速体验选项。主要收益包括：

1. **降低使用门槛**: 新用户可以快速开始使用，无需复杂的环境配置
2. **保持技术先进性**: 生产环境仍可使用PostgreSQL的高性能特性
3. **提升用户体验**: 提供一键切换和数据迁移功能
4. **扩大用户群体**: 吸引更多初学者和快速验证需求的用户

通过这种方式，既解决了用户反馈的复杂性问题，又保持了项目的技术竞争力。