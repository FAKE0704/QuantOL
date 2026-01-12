import aiosqlite
import pandas as pd
import chinese_calendar as calendar
import datetime
from typing import Any, Optional, Dict, List
import os
import chinese_calendar as calendar
import asyncio
import random
import time
from src.support.log.logger import logger
from .database_adapter import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""

    def __init__(self, db_path: str = "./data/quantdb.sqlite"):
        self.db_path = db_path
        self.pools: List[aiosqlite.Connection] = []
        self._initialized = False
        self._pool_lock = asyncio.Lock()
        self._pool_index = 0

        # 从环境变量读取配置，提供默认值
        import os
        self._max_connections = int(os.getenv('SQLITE_MAX_CONNECTIONS', '3'))
        self._busy_timeout = int(os.getenv('SQLITE_BUSY_TIMEOUT', '30000'))
        self._cache_size = int(os.getenv('SQLITE_CACHE_SIZE', '-64000'))
        self._mmap_size = int(os.getenv('SQLITE_MMAP_SIZE', '268435456'))
        self._batch_size = int(os.getenv('SQLITE_BATCH_SIZE', '1000'))
        self._wal_auto_checkpoint = int(os.getenv('SQLITE_WAL_AUTO_CHECKPOINT', '1000'))
        self._journal_limit = int(os.getenv('SQLITE_JOURNAL_LIMIT', '1048576'))

        # 添加实例ID用于调试
        self._instance_id = id(self)
        self._data_source_manager = None
        logger.info(f"创建SQLiteAdapter实例 #{self._instance_id} - 连接池:{self._max_connections}, 超时:{self._busy_timeout}ms, 批量大小:{self._batch_size}")

    def set_data_source_manager(self, data_source_manager):
        """设置数据源管理器引用"""
        self._data_source_manager = data_source_manager
        logger.info(f"SQLiteAdapter已设置数据源管理器")

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        logger.info(f"开始初始化SQLiteAdapter实例 #{self._instance_id}")

        if self._initialized:
            logger.info(f"实例 #{self._instance_id} 已初始化，跳过")
            return

        async with self._pool_lock:
            if self._initialized:
                logger.info(f"实例 #{self._instance_id} 在锁检查时已初始化，跳过")
                return

            try:
                # 确保数据目录存在
                data_dir = os.path.dirname(self.db_path)
                if data_dir:
                    os.makedirs(data_dir, exist_ok=True)
                    logger.info(f"确保数据目录存在: {data_dir}")

                logger.info(f"正在创建SQLite数据库连接池: {self.db_path}")

                # 创建连接池
                for i in range(self._max_connections):
                    conn = await aiosqlite.connect(self.db_path)
                    await self._configure_connection(conn)
                    self.pools.append(conn)
                    logger.debug(f"创建连接 {i+1}/{self._max_connections}")

                # 创建表结构
                await self._init_db_tables()
                self._initialized = True

                logger.info(f"SQLite数据库连接池初始化成功: {self.db_path} (连接数: {len(self.pools)})")

            except Exception as e:
                logger.error(f"SQLite数据库初始化失败: {str(e)}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                raise

    async def _configure_connection(self, conn: aiosqlite.Connection) -> None:
        """配置数据库连接参数"""
        try:
            # 启用外键约束
            await conn.execute("PRAGMA foreign_keys = ON")

            # 基础PRAGMA设置（避免过度优化导致的问题）
            await conn.execute(f"PRAGMA busy_timeout = {self._busy_timeout}")
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")

            logger.debug(f"SQLite基础连接配置完成 - 超时:{self._busy_timeout}ms")

            # 尝试设置高级选项（如果失败不影响运行）
            try:
                await conn.execute(f"PRAGMA cache_size = {self._cache_size}")
                await conn.execute("PRAGMA temp_store = MEMORY")
            except Exception as e:
                logger.warning(f"设置基础性能参数失败: {e}")

            try:
                await conn.execute(f"PRAGMA mmap_size = {self._mmap_size}")
                await conn.execute(f"PRAGMA wal_autocheckpoint = {self._wal_auto_checkpoint}")
                await conn.execute(f"PRAGMA journal_size_limit = {self._journal_limit}")
                logger.debug(f"SQLite高级连接配置完成 - 缓存:{self._cache_size}KB, MMAP:{self._mmap_size}字节")
            except Exception as e:
                logger.warning(f"设置高级性能参数失败: {e}")

        except Exception as e:
            logger.error(f"SQLite连接配置失败: {e}")
            # 配置失败不应该阻止系统运行
            pass

    async def create_connection_pool(self) -> aiosqlite.Connection:
        """创建连接池（为了兼容抽象类接口）"""
        # 为了保持向后兼容，返回第一个连接
        if not self._initialized:
            await self.initialize()

        if not self.pools:
            raise RuntimeError("连接池未初始化")

        return self.pools[0]

    async def _get_connection(self) -> aiosqlite.Connection:
        """从连接池获取连接"""
        if not self._initialized:
            # 不在这里调用initialize()，避免递归
            raise RuntimeError("数据库未初始化，请先调用initialize()")

        async with self._pool_lock:
            if not self.pools:
                raise RuntimeError("连接池未初始化")

            # 轮询获取连接
            conn = self.pools[self._pool_index]
            self._pool_index = (self._pool_index + 1) % len(self.pools)
            return conn

    async def _execute_with_retry(self, conn: aiosqlite.Connection, query: str, parameters=None, max_retries=3):
        """带重试机制的数据库操作执行"""
        for attempt in range(max_retries):
            try:
                if parameters is None:
                    return await conn.execute(query)
                else:
                    return await conn.execute(query, parameters)
            except Exception as e:
                error_msg = str(e).lower()

                # 检查是否是数据库锁定错误
                if any(keyword in error_msg for keyword in ['database is locked', 'database locked', 'sqlite_busy']):
                    if attempt == max_retries - 1:
                        logger.error(f"数据库操作最终失败，重试{max_retries}次后仍锁定: {query[:100]}")
                        raise

                    # 指数退避 + 随机抖动
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"数据库锁定，第{attempt+1}次重试，等待{delay:.2f}秒: {query[:100]}")
                    await asyncio.sleep(delay)
                else:
                    # 非锁定错误，直接抛出
                    raise

    async def _executemany_with_retry(self, conn: aiosqlite.Connection, query: str, parameters=None, max_retries=8):
        """带重试机制的批量数据库操作执行（增强版 - 解决锁定问题）"""
        for attempt in range(max_retries):
            try:
                if parameters is None:
                    return await conn.executemany(query)
                else:
                    return await conn.executemany(query, parameters)
            except Exception as e:
                error_msg = str(e).lower()

                # 检查是否是数据库锁定错误
                if any(keyword in error_msg for keyword in ['database is locked', 'database locked', 'sqlite_busy']):
                    if attempt == max_retries - 1:
                        logger.error(f"批量数据库操作最终失败，重试{max_retries}次后仍锁定: {query[:100]}")
                        raise

                    # 改进的退避策略：更长的等待时间，特别是前几次重试
                    if attempt < 2:
                        # 前两次重试使用较短延迟
                        delay = 0.5 + random.uniform(0, 0.5)
                    elif attempt < 4:
                        # 中间重试使用中等延迟
                        delay = 2 + random.uniform(0, 1)
                    else:
                        # 后续重试使用更长延迟
                        delay = 5 + random.uniform(0, 2)

                    logger.warning(f"批量数据库操作锁定，第{attempt+1}次重试，等待{delay:.2f}秒: {query[:100]}")
                    await asyncio.sleep(delay)
                else:
                    # 非锁定错误，直接抛出
                    raise

    async def execute_query(self, query: str, *args) -> Any:
        """执行查询"""
        conn = await self._get_connection()

        try:
            # 转换PostgreSQL语法到SQLite语法
            sqlite_query = self._convert_query_syntax(query)

            if query.strip().upper().startswith('SELECT'):
                cursor = await self._execute_with_retry(conn, sqlite_query, args if args else ())
                rows = await cursor.fetchall()
                # 获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows]
            else:
                await self._execute_with_retry(conn, sqlite_query, args if args else ())
                # 提交事务，释放锁
                await conn.commit()
                return None

        except Exception as e:
            # 回滚事务，释放锁
            try:
                await conn.rollback()
            except:
                pass
            logger.error(f"SQLite查询执行失败: {str(e)}")
            raise

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

        # 处理ON CONFLICT语法
        if 'ON CONFLICT' in query:
            query = self._convert_on_conflict_syntax(query)

        # 处理RETURNING子句（SQLite不支持）
        if 'RETURNING' in query:
            query = query.split('RETURNING')[0]

        return query

    def _convert_on_conflict_syntax(self, query: str) -> str:
        """转换ON CONFLICT语法"""
        # 简化的ON CONFLICT转换，实际情况可能需要更复杂的处理
        if 'ON CONFLICT (code, date, time, frequency) DO UPDATE SET' in query:
            query = query.replace('ON CONFLICT (code, date, time, frequency) DO UPDATE SET',
                                'ON CONFLICT(code, date, time, frequency) DO UPDATE SET')
            query = query.replace('EXCLUDED.', 'new.')
        elif 'ON CONFLICT (code) DO UPDATE SET' in query:
            query = query.replace('ON CONFLICT (code) DO UPDATE SET',
                                'ON CONFLICT(code) DO UPDATE SET')
            query = query.replace('EXCLUDED.', 'new.')
        elif 'ON CONFLICT (stat_month) DO UPDATE SET' in query:
            query = query.replace('ON CONFLICT (stat_month) DO UPDATE SET',
                                'ON CONFLICT(stat_month) DO UPDATE SET')
            query = query.replace('EXCLUDED.', 'new.')

        return query

    async def close(self) -> None:
        """关闭连接池"""
        async with self._pool_lock:
            if self.pools:
                logger.info(f"关闭{len(self.pools)}个SQLite连接")
                for conn in self.pools:
                    await conn.close()
                self.pools.clear()
                self._initialized = False

    async def _init_db_tables(self):
        """初始化表结构 - 极简版本"""
        logger.info("开始SQLite表结构初始化...")

        try:
            # 直接使用第一个连接，避免获取连接的死锁问题
            logger.info("🔧 使用第一个连接进行初始化...")
            if not self.pools:
                raise RuntimeError("连接池为空，无法进行初始化")

            conn = self.pools[0]  # 直接使用第一个连接
            logger.info("✅ 获取到连接用于表初始化")

            # 根据字段映射文档创建标准表结构
            logger.info("🔨 开始创建StockInfo表...")

            # 创建符合多数据源的StockInfo表
            sql = """
                CREATE TABLE IF NOT EXISTS StockInfo (
                    code TEXT PRIMARY KEY,           -- 统一股票代码（不带交易所后缀）
                    code_name TEXT NOT NULL,        -- 股票名称
                    ipoDate TEXT NOT NULL,         -- 上市日期 (YYYY-MM-DD)
                    outDate TEXT,                   -- 退市日期 (YYYY-MM-DD)，null表示未退市
                    type TEXT DEFAULT '股票',      -- 股票类型
                    status TEXT DEFAULT '上市',    -- 上市状态：上市/退市/暂停
                    market TEXT,                    -- 交易所信息（可选）
                    data_source TEXT DEFAULT '',   -- 数据来源标识
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """

            await conn.execute(sql)
            logger.info("✅ StockInfo表创建成功")

            # 创建StockData表（保持简单结构）
            logger.info("🔨 开始创建StockData表...")
            sql2 = """
                CREATE TABLE IF NOT EXISTS StockData (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,              -- 股票代码
                    date TEXT NOT NULL,              -- 日期
                    time TEXT NOT NULL,              -- 时间
                    open REAL NOT NULL,              -- 开盘价
                    high REAL NOT NULL,              -- 最高价
                    low REAL NOT NULL,               -- 最低价
                    close REAL NOT NULL,             -- 收盘价
                    volume INTEGER NOT NULL,         -- 成交量
                    amount REAL,                     -- 成交额
                    adjustflag TEXT,                 -- 复权状态
                    frequency TEXT NOT NULL,         -- 数据频率
                    data_source TEXT DEFAULT '',     -- 数据来源标识
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (code, date, time, frequency)
                )
            """

            await conn.execute(sql2)
            logger.info("✅ StockData表创建成功")

            logger.info("🎉 SQLite表结构初始化完成")

        except Exception as e:
            logger.error(f"❌ SQLite表结构初始化失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    async def save_stock_info(self, code: str, code_name: str, ipo_date: str,
                             stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息到StockInfo表"""
        conn = await self._get_connection()
        try:
            await self._execute_with_retry(conn, """
                INSERT OR REPLACE INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, code_name, ipo_date, out_date, stock_type, status))

            logger.info(f"成功保存股票基本信息: {code}")
            return True
        except Exception as e:
            logger.error(f"保存股票信息失败: {str(e)}")
            raise

    async def check_data_completeness(self, symbol: str, start_date: datetime.date, end_date: datetime.date, frequency: str) -> list:
        """检查数据完整性"""
        try:
            # 确保日期格式正确
            if isinstance(start_date, str):
                start_dt = pd.to_datetime(start_date).date()
            else:
                start_dt = start_date

            if isinstance(end_date, str):
                end_dt = pd.to_datetime(end_date).date()
            else:
                end_dt = end_date

            logger.info(f"Checking data completeness for {symbol} from {start_dt} to {end_dt}")

            conn = await self._get_connection()
            # 获取数据库中已有日期
            query = """
                SELECT DISTINCT date
                FROM StockData
                WHERE code = ? AND frequency = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            cursor = await self._execute_with_retry(conn, query, (symbol, frequency, start_dt, end_dt))
            rows = await cursor.fetchall()
            logger.info(f"从数据库获取 {start_dt}-{end_dt} for {symbol}")

            existing_dates = {pd.to_datetime(row[0]).date() for row in rows}

            # 生成理论交易日集合（排除节假日）
            all_dates = pd.date_range(start_dt, end_dt, freq='B')  # 工作日
            trading_dates = set(
                date.date() for date in all_dates
                if not calendar.is_holiday(date.date())
            )
            today = datetime.date.today()
            trading_dates = {d for d in trading_dates if d != today}  # 若今日查询，则排除今日

            # 计算缺失日期
            missing_dates = trading_dates - existing_dates

            # 将连续缺失日期合并为区间
            missing_ranges = []
            if missing_dates:
                sorted_dates = sorted(missing_dates)
                range_start = sorted_dates[0]
                prev_date = range_start

                for current_date in sorted_dates[1:]:
                    if (current_date - prev_date).days > 1:  # 出现断点
                        missing_ranges.append((range_start, prev_date))
                        range_start = current_date
                    prev_date = current_date

                # 添加最后一个区间
                missing_ranges.append((range_start, prev_date))

            logger.info(f"Found {len(missing_ranges)} missing data ranges for {symbol}")
            return missing_ranges

        except Exception as e:
            logger.error(f"检查数据完整性失败: {str(e)}")
            raise

    async def load_stock_data(self, symbol: str, start_date: datetime.date, end_date: datetime.date, frequency: str) -> pd.DataFrame:
        """从数据库加载股票数据"""
        try:
            # 确保日期格式正确
            if isinstance(start_date, str):
                start_dt = pd.to_datetime(start_date).date()
            else:
                start_dt = start_date

            if isinstance(end_date, str):
                end_dt = pd.to_datetime(end_date).date()
            else:
                end_dt = end_date

            logger.info(f"Loading stock data for {symbol} from {start_dt} to {end_dt}")

            # 检查数据完整性
            missing_ranges = await self.check_data_completeness(symbol, start_dt, end_dt, frequency)
            logger.info(f"数据完整性检查完成，发现 {len(missing_ranges)} 个缺失区间")

            # 如果有缺失数据，从选择的数据源获取并保存
            if missing_ranges:
                logger.info(f"Fetching missing data ranges for {symbol}")

                # 获取当前选择的数据源
                try:
                    from .config.data_source_config import get_data_source_manager
                    data_source_manager = get_data_source_manager()

                    # 先尝试从环境变量更新Tushare配置
                    data_source_manager.update_tushare_token_from_env()

                    current_source = data_source_manager.get_current_data_source()
                    logger.info(f"使用当前选择的数据源: {current_source}")

                    if current_source and current_source.lower() == 'tushare':
                        logger.info("尝试使用Tushare数据源")
                        # 使用Tushare数据源
                        from .adapters.tushare_service_adapter import TushareServiceAdapter
                        from .config.tushare_config import TushareConfig

                        # 重新获取更新后的Tushare配置
                        tushare_config = data_source_manager.get_data_source('Tushare')
                        logger.debug(f"获取Tushare配置: {tushare_config}")

                        if tushare_config and tushare_config.settings.enabled and tushare_config.credentials.token:
                            logger.info(f"Tushare配置完整，token: {tushare_config.credentials.token[:8]}...，创建TushareServiceAdapter")
                            config = TushareConfig(
                                token=tushare_config.credentials.token,
                                cache_enabled=tushare_config.settings.cache_enabled,
                                cache_ttl=tushare_config.settings.cache_ttl,
                                rate_limit=tushare_config.settings.rate_limit
                            )
                            data_source = TushareServiceAdapter(config)
                            logger.info("TushareServiceAdapter创建成功")
                        else:
                            logger.warning(f"Tushare数据源未启用或配置不完整，回退到Baostock。enabled: {tushare_config.settings.enabled if tushare_config else 'None'}, token: {'有' if tushare_config and tushare_config.credentials.token else '无'}")
                            from .baostock_source import BaostockDataSource
                            data_source = BaostockDataSource(frequency)
                    else:
                        logger.warning(f"当前数据源不是Tushare ({current_source})，使用默认Baostock数据源")
                        # 默认使用Baostock数据源
                        from .baostock_source import BaostockDataSource
                        data_source = BaostockDataSource(frequency)

                except Exception as e:
                    logger.error(f"获取数据源配置失败，使用默认Baostock: {str(e)}")
                    import traceback
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    from .baostock_source import BaostockDataSource
                    data_source = BaostockDataSource(frequency)

                data = pd.DataFrame()
                for range_start, range_end in missing_ranges:
                    logger.info(f"Fetching data from {range_start} to {range_end} using {current_source}")
                    new_data = await data_source.load_data(symbol, range_start, range_end, frequency)
                    await self.save_stock_data(symbol, new_data, frequency)
                    data = pd.concat([data, new_data])
            else:
                logger.info(f"数据完整，无需从外部数据源获取 {symbol} 的数据")

            # 从数据库加载完整数据
            query = """
                SELECT date, time, code, open, high, low, close, volume, amount, adjustflag, frequency
                FROM StockData
                WHERE code = ?
                AND date BETWEEN ? AND ?
                AND frequency = ?
                ORDER BY date
            """

            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await self._execute_with_retry(conn, query, (symbol, start_dt, end_dt, frequency))
                rows = await cursor.fetchall()
            logger.info(f"数据库查询完成，返回 {len(rows) if rows else 0} 行数据")

            if not rows:
                logger.warning(f"[{symbol}] 未找到股票数据 date_range=[{start_date}~{end_date}] frequency={frequency}")
                return pd.DataFrame()

            data = [row for row in rows]
            df = pd.DataFrame(data, columns=['date', 'time', 'code', 'open', 'high', 'low', 'close',
                                            'volume', 'amount', 'adjustflag', 'frequency'])
            df = self._transform_data(df)

            logger.info(f"Successfully loaded {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to load stock data: {str(e)}")
            raise

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 与PostgreSQL版本相同的转换逻辑
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')

        if 'time' in data.columns:
            if data['time'].isna().any():
                logger.warning(f"发现 {data['time'].isna().sum()} 个NaT值在time列")
                data.loc[data['time'].isna(), 'time'] = '00:00:00'

            data['time'] = data['time'].astype(str)
            data['time'] = data['time'].apply(lambda x: x if len(x) >= 8 else '00:00:00')

        if 'frequency' in data.columns:
            if data['frequency'].isna().any():
                logger.warning(f"发现 {data['frequency'].isna().sum()} 个NaN值在frequency列")
                data.loc[data['frequency'].isna(), 'frequency'] = 'd'

        if 'date' in data.columns and 'time' in data.columns:
            try:
                data['date'] = data['date'].astype(str)
                data['time'] = data['time'].astype(str)
                data['combined_time'] = data['date'] + ' ' + data['time']
                data['combined_time'] = pd.to_datetime(
                    data['combined_time'],
                    format='%Y-%m-%d %H:%M:%S',
                    errors='coerce'
                )

                if data['combined_time'].isna().any():
                    failed_count = data['combined_time'].isna().sum()
                    logger.warning(f"发现 {failed_count} 个combined_time转换失败")
                    mask = data['combined_time'].isna()
                    data.loc[mask, 'combined_time'] = pd.to_datetime(
                        data.loc[mask, 'date'] + ' 00:00:00',
                        format='%Y-%m-%d %H:%M:%S'
                    )

            except Exception as e:
                logger.error(f"创建combined_time列失败: {str(e)}")
                data['combined_time'] = pd.to_datetime(data['date'])

        if 'combined_time' in data.columns:
            data = data.sort_values(by='combined_time').reset_index(drop=True)

        return data

    async def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票信息（优化版）"""
        try:
            logger.debug("检查数据是否最新")
            if await self._is_stock_info_up_to_date():
                # 从数据库读取现有数据
                conn = await self._get_connection()
                cursor = await self._execute_with_retry(conn, "SELECT * FROM StockInfo")
                rows = await cursor.fetchall()

                # 动态获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                logger.debug(f"从数据库获取到{len(columns)}列: {columns}")

                return pd.DataFrame(rows, columns=columns)
            else:
                # 需要更新数据
                logger.info("StockInfo表数据过期，开始更新")

                # 使用数据源管理器获取当前选择的数据源
                selected_data_source = None
                if self._data_source_manager:
                    selected_data_source = self._data_source_manager.get_current_data_source()
                    logger.info(f"从数据源管理器获取当前数据源: {selected_data_source}")
                else:
                    # 降级到环境变量读取
                    selected_data_source = os.getenv('SELECTED_DATA_SOURCE', 'baostock')
                    logger.info(f"从环境变量获取数据源（降级模式）: {selected_data_source}")

                # 标准化数据源名称（匹配系统设置中的选项）
                if selected_data_source == 'Tushare':
                    data_source_type = 'tushare'
                elif selected_data_source == 'Baostock':
                    data_source_type = 'baostock'
                else:
                    data_source_type = 'baostock'  # 默认

                if data_source_type == 'tushare':
                    # 使用Tushare数据源
                    from .adapters.tushare_adapter import TushareAdapter
                    from .config.tushare_config import TushareConfig

                    try:
                        token = os.getenv('TUSHARE_TOKEN')
                        if not token:
                            raise ValueError("Tushare token未配置")

                        config = TushareConfig(token=token)
                        adapter = TushareAdapter(config.token)
                        df = adapter.get_stock_basic()

                        # 标记数据源类型
                        df['data_source'] = 'tushare'
                        logger.info(f"从Tushare获取到 {len(df)} 条股票数据")

                    except Exception as e:
                        logger.error(f"Tushare数据源获取失败，切换到Baostock: {e}")
                        # 降级到Baostock
                        from .baostock_source import BaostockDataSource
                        data_source = BaostockDataSource()
                        df = await data_source._get_all_stocks()
                        df['data_source'] = 'baostock'

                else:
                    # 默认使用Baostock数据源
                    from .baostock_source import BaostockDataSource
                    data_source = BaostockDataSource()
                    df = await data_source._get_all_stocks()
                    df['data_source'] = 'baostock'

                # 将数据保存到数据库
                await self._update_stock_info(df)
                return df
        except Exception as e:
            logger.error(f"获取所有股票信息失败: {str(e)}")
            raise

    async def _is_stock_info_up_to_date(self, max_retries: int = 3) -> bool:
        """检查StockInfo表是否最新"""
        conn = await self._get_connection()

        for attempt in range(max_retries):
            try:
                logger.debug(f"检查StockInfo表状态(尝试{attempt+1}/{max_retries})")

                # 检查表是否存在
                cursor = await self._execute_with_retry(conn, """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='StockInfo'
                """)
                table_exists = await cursor.fetchone()

                if not table_exists:
                    logger.warning("表StockInfo不存在")
                    return False

                # 检查最新IPO日期
                cursor = await self._execute_with_retry(conn, """
                    SELECT ipoDate FROM StockInfo
                    ORDER BY ipoDate DESC LIMIT 1
                """)
                row = await cursor.fetchone()

                if not row:
                    logger.warning("StockInfo表为空")
                    return False

                latest_ipo = pd.Timestamp(row[0])
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
                is_up_to_date = latest_ipo >= cutoff

                logger.debug(f"最新IPO日期: {latest_ipo.isoformat()}, 是否最新: {is_up_to_date}")
                return is_up_to_date

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"检查StockInfo表状态失败(最终尝试): {str(e)}")
                    raise
                logger.warning(f"检查StockInfo表状态失败(尝试{attempt+1}): {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))
        return False

    async def _update_stock_info(self, df: pd.DataFrame) -> tuple:
        """更新StockInfo表数据（优化版 - 解决锁定问题）"""
        valid_data = []
        invalid_rows = []

        try:
            # 验证所有数据行
            for _, row in df.iterrows():
                try:
                    validated_row = await self._validate_stock_info(row)
                    valid_data.append(validated_row)
                except Exception as e:
                    invalid_rows.append((row.to_dict(), str(e)))

            # 如果没有有效数据，提前返回
            if not valid_data:
                logger.warning("没有有效数据可插入StockInfo表")
                return 0, len(invalid_rows)

            # 使用独立连接进行事务处理
            conn = await self._get_connection()

            # 手动管理事务
            try:
                # 开始事务
                await conn.execute("BEGIN")
                logger.debug("开始事务更新StockInfo表")

                # 清空现有数据
                logger.debug("清空现有StockInfo表数据")
                await self._execute_with_retry(conn, "DELETE FROM StockInfo")

                # 分批插入数据以减少锁持有时间
                batch_size = self._batch_size  # 使用配置的批量大小
                total_inserted = 0

                for i in range(0, len(valid_data), batch_size):
                    batch = valid_data[i:i + batch_size]
                    logger.debug(f"插入第{i//batch_size + 1}批数据，共{len(batch)}条记录")

                    try:
                        await self._executemany_with_retry(conn, """
                            INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status, data_source)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, parameters=batch)
                        total_inserted += len(batch)

                        # 在批次之间短暂暂停，让其他操作有机会访问数据库
                        if i + batch_size < len(valid_data):
                            await asyncio.sleep(0.01)  # 10ms暂停

                    except Exception as e:
                        logger.error(f"批次插入失败: {str(e)}")
                        # 回滚事务
                        await conn.execute("ROLLBACK")
                        raise

                # 提交事务
                await conn.execute("COMMIT")
                logger.info(f"成功更新StockInfo表数据，成功插入{total_inserted}行，失败{len(invalid_rows)}行")
                return total_inserted, len(invalid_rows)

            except Exception as e:
                # 确保事务被回滚
                try:
                    await conn.execute("ROLLBACK")
                except:
                    pass  # 回滚失败，连接可能已经关闭
                raise

        except Exception as e:
            logger.error(f"更新StockInfo表失败: {str(e)}")
            raise

    async def _validate_stock_info(self, row: pd.Series) -> tuple:
        """验证并转换股票信息格式（支持多数据源字段）"""
        try:
            # 使用字段映射器进行验证
            from .field_mapper import FieldMapper

            # 将row转换为DataFrame进行验证
            df = pd.DataFrame([row])

            # 映射字段并验证
            mapped_df = FieldMapper.map_to_standard_fields(df, row.get('data_source', 'baostock'))
            is_valid, issues = FieldMapper.validate_required_fields(mapped_df)

            if not is_valid:
                raise ValueError(f"字段验证失败: {issues}")

            # 获取验证后的数据
            mapped_row = mapped_df.iloc[0]

            # 验证ipoDate格式
            if not isinstance(mapped_row['ipo_date'], str):
                raise ValueError(f"Invalid ipoDate format: {mapped_row['ipo_date']}")

            try:
                ipo_date = pd.to_datetime(mapped_row['ipo_date'], format='%Y-%m-%d', errors='coerce')
                if pd.isna(ipo_date):
                    raise ValueError(f"Invalid ipoDate value: {mapped_row['ipo_date']}")
                ipo_date_str = ipo_date.strftime('%Y-%m-%d')
            except Exception as e:
                raise ValueError(f"ipoDate转换失败: {e}")

            # 处理outDate
            out_date_str = None
            if pd.notna(mapped_row.get('out_date')) and mapped_row['out_date'] != '':
                try:
                    out_date = pd.to_datetime(mapped_row['out_date'], format='%Y-%m-%d', errors='coerce')
                    if pd.notna(out_date):
                        out_date_str = out_date.strftime('%Y-%m-%d')
                except Exception as e:
                    logger.warning(f"outDate转换失败，设为null: {e}")
                    out_date_str = None

            # 构建插入元组
            return (
                str(mapped_row['code']),
                str(mapped_row['code_name']),
                ipo_date_str,
                out_date_str,
                str(mapped_row['type']),
                str(mapped_row['status']),
                str(mapped_row.get('data_source', ''))
            )
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)} - 行数据: {row.to_dict()}")
            raise

    async def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        conn = await self._get_connection()
        try:
            cursor = await self._execute_with_retry(conn, """
                SELECT code_name, ipoDate, outDate, type, status
                FROM StockInfo
                WHERE code = ?
            """, (code,))

            row = await cursor.fetchone()
            if not row:
                return {}

            return {
                "code_name": row[0],
                "ipo_date": row[1],
                "out_date": row[2],
                "type": row[3],
                "status": row[4]
            }
        except Exception as e:
            logger.error(f"获取股票信息失败: {str(e)}")
            raise

    async def get_stock_name(self, code: str) -> str:
        """根据股票代码获取名称"""
        conn = await self._get_connection()
        try:
            cursor = await self._execute_with_retry(conn, """
                SELECT code_name FROM StockInfo WHERE code = ?
            """, (code,))
            row = await cursor.fetchone()
            return row[0] if row else ""
        except Exception as e:
            logger.error(f"获取股票名称失败: {str(e)}")
            raise

    async def save_stock_data(self, symbol: str, data: pd.DataFrame, frequency: str) -> bool:
        """保存股票数据到StockData表（优化版 - 解决锁定问题）"""
        conn = None
        data_tmp = data.copy()
        data_tmp['date'] = pd.to_datetime(data_tmp['date'], format="%Y-%m-%d").dt.date

        # 确保 time 列是字符串格式（处理 datetime.time 对象）
        if 'time' in data_tmp.columns:
            # 记录转换前的类型，用于调试
            sample_time = data_tmp['time'].iloc[0] if len(data_tmp) > 0 else None
            logger.info(f"[save_stock_data] 转换前 time 列样本: {sample_time}, 类型: {type(sample_time)}")

            data_tmp['time'] = data_tmp['time'].apply(
                lambda x: x.strftime('%H:%M:%S') if isinstance(x, datetime.time) else str(x) if pd.notna(x) else "00:00:00"
            )

            # 记录转换后的类型
            sample_time_after = data_tmp['time'].iloc[0] if len(data_tmp) > 0 else None
            logger.info(f"[save_stock_data] 转换后 time 列样本: {sample_time_after}, 类型: {type(sample_time_after)}")

        try:
            conn = await self._get_connection()
            records = data_tmp.to_dict('records')

            # 处理不同频率的数据
            if frequency in ["1", "5", "15", "30", "60"]:
                # 分钟级数据有time字段（已在前面转换为字符串）
                insert_data = [
                    (
                        symbol,
                        record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else str(record['date']),
                        record.get('time', "00:00:00"),
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume'],
                        record.get('amount'),
                        record.get('adjustflag'),
                        frequency
                    )
                    for record in records
                ]
            else:
                # 日线及以上频率数据，设置默认时间
                insert_data = [
                    (
                        symbol,
                        record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else str(record['date']),
                        "00:00:00",
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume'],
                        record.get('amount'),
                        record.get('adjustflag'),
                        frequency
                    )
                    for record in records
                ]

            # 使用更小的批次以减少锁定时间
            batch_size = min(100, self._batch_size)  # 强制最大批次为100
            total_batches = (len(insert_data) + batch_size - 1) // batch_size

            for i in range(0, len(insert_data), batch_size):
                batch = insert_data[i:i + batch_size]
                logger.debug(f"插入第{i//batch_size + 1}/{total_batches}批数据，共{len(batch)}条记录")

                await self._executemany_with_retry(conn, """
                    INSERT OR REPLACE INTO StockData (
                        code, date, time, open, high, low, close,
                        volume, amount, adjustflag, frequency
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, parameters=batch)

                # 批次间暂停，减少锁定竞争，让其他操作有机会执行
                if i + batch_size < len(insert_data):
                    await asyncio.sleep(0.1)  # 增加暂停时间

            # 验证数据是否成功插入
            logger.info(f"成功保存{symbol}的{frequency}频率数据，共{len(insert_data)}条记录")

            # 显式提交事务
            await conn.commit()
            logger.debug(f"事务已提交，保存{symbol}的{frequency}频率数据")

            # 简单验证：查询刚插入的记录数
            verify_cursor = await self._execute_with_retry(conn,
                "SELECT COUNT(*) FROM StockData WHERE code = ? AND frequency = ?",
                (symbol, frequency)
            )
            count = await verify_cursor.fetchone()
            logger.info(f"数据库中{symbol}的{frequency}频率记录总数: {count[0] if count else 0}")

            return True

        except Exception as e:
            logger.error(f"保存股票数据失败: {str(e)}")
            if conn:
                try:
                    await conn.rollback()
                    logger.debug("事务已回滚")
                except Exception as rollback_error:
                    logger.error(f"事务回滚失败: {rollback_error}")
            raise
        finally:
            # 连接池中的连接不需要显式关闭，连接池会自动管理
            pass

    async def save_money_supply_data(self, data: pd.DataFrame) -> bool:
        """保存货币供应量数据（优化版）"""
        conn = await self._get_connection()
        try:
            records = data.to_dict('records')
            insert_data = [
                (
                    record['statMonth'],
                    record['m2'],
                    record['m2YoY'],
                    record['m1'],
                    record['m1YoY'],
                    record['m0'],
                    record['m0YoY'],
                    record['cd'],
                    record['cdYoY'],
                    record['qm'],
                    record['qmYoY'],
                    record['ftd'],
                    record['ftdYoY'],
                    record['sd'],
                    record['sdYoY']
                )
                for record in records
            ]

            await self._executemany_with_retry(conn, """
                INSERT OR REPLACE INTO MoneySupplyData (
                    stat_month, m2, m2_yoy, m1, m1_yoy, m0, m0_yoy,
                    cd, cd_yoy, qm, qm_yoy, ftd, ftd_yoy, sd, sd_yoy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, parameters=insert_data)

            logger.info(f"成功保存{len(insert_data)}条货币供应量数据")
            return True

        except Exception as e:
            logger.error(f"保存货币供应量数据失败: {str(e)}")
            raise

    async def get_money_supply_data(self, start_month: str, end_month: str) -> pd.DataFrame:
        """获取货币供应量数据"""
        conn = await self._get_connection()
        try:
            cursor = await self._execute_with_retry(conn, """
                SELECT * FROM MoneySupplyData
                WHERE stat_month BETWEEN ? AND ?
                ORDER BY stat_month
            """, (start_month, end_month))

            rows = await cursor.fetchall()

            if not rows:
                logger.warning(f"未找到{start_month}至{end_month}的货币供应量数据")
                return pd.DataFrame()

            df = pd.DataFrame(rows, columns=[
                'id', 'stat_month', 'm2', 'm2_yoy', 'm1', 'm1_yoy',
                'm0', 'm0_yoy', 'cd', 'cd_yoy', 'qm', 'qm_yoy',
                'ftd', 'ftd_yoy', 'sd', 'sd_yoy'
            ])

            # 移除id列，与PostgreSQL版本保持一致
            if 'id' in df.columns:
                df = df.drop('id', axis=1)

            logger.info(f"成功获取{len(df)}条货币供应量数据")
            return df

        except Exception as e:
            logger.error(f"获取货币供应量数据失败: {str(e)}")
            raise

    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        return {
            "db_type": "sqlite",
            "db_path": self.db_path,
            "initialized": self._initialized,
            "pool_size": len(self.pools),
            "max_connections": self._max_connections,
            "current_connection_index": self._pool_index,
            "busy_timeout": self._busy_timeout,
            "connected": len(self.pools) > 0
        }