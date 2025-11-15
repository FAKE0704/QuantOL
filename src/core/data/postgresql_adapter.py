import asyncpg
from typing import Optional, List, Dict, Any
import pandas as pd
import chinese_calendar as calendar
from datetime import datetime, date, time
import streamlit as st
import asyncio
import os
from src.support.log.logger import logger
from .database_adapter import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL数据库适配器"""

    def __init__(self, host=None, port=None, dbname=None,
                 user=None, password=None, admin_db=None):
        self.connection = None
        self._instance_id = id(self)
        self.connection_states = {}
        logger.debug(f"PostgreSQLAdapter initialized, instance_id: {self._instance_id}")

        # 从环境变量获取配置，支持参数覆盖
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # 解析DATABASE_URL格式: postgresql://user:password@host:port/dbname
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            self.connection_config = {
                'host': parsed.hostname,
                'port': str(parsed.port) if parsed.port else '5432',
                'dbname': parsed.path[1:],  # 去掉开头的/
                'user': parsed.username,
                'password': parsed.password
            }
        else:
            db_password = password or os.getenv('DB_PASSWORD')
            if not db_password:
                raise ValueError("数据库密码未配置。请设置DB_PASSWORD环境变量或通过参数传递。")

            self.connection_config = {
                'host': host or os.getenv('DB_HOST', 'localhost'),
                'port': port or os.getenv('DB_PORT', '5432'),
                'dbname': dbname or os.getenv('DB_NAME', 'quantdb'),
                'user': user or os.getenv('DB_USER', 'quant'),
                'password': db_password
            }

        self.admin_config = {
            'host': self.connection_config['host'],
            'port': self.connection_config['port'],
            'dbname': admin_db or os.getenv('ADMIN_DB_NAME', 'quantdb'),
            'user': self.connection_config['user'],
            'password': self.connection_config['password']
        }

        self._initialized = False
        self._initializing = False
        self.pool = None
        self._loop = None
        self.max_pool_size = int(os.getenv('DB_MAX_POOL_SIZE', '15'))
        self.query_timeout = int(os.getenv('DB_QUERY_TIMEOUT', '60'))
        self.active_connections = {}
        self._conn_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        if self._initialized:
            return

        start_time = asyncio.get_event_loop().time()
        await self._create_pool()
        await self._init_db_tables()
        self._initialized = True
        logger.debug(
            f"initialize调用结束，总耗时: {asyncio.get_event_loop().time() - start_time:.2f}s"
        )

    async def create_connection_pool(self) -> asyncpg.Pool:
        """创建连接池"""
        if not self.pool:
            try:
                valid_config = {
                    "database": self.connection_config["dbname"],
                    "user": self.connection_config["user"],
                    "password": self.connection_config["password"],
                    "host": self.connection_config["host"],
                    "port": self.connection_config.get("port", '5432')
                }
                self.pool = await asyncpg.create_pool(
                    loop=st.session_state._loop,
                    **valid_config,
                    min_size=3,
                    max_size=self.max_pool_size,
                    command_timeout=self.query_timeout,
                    max_inactive_connection_lifetime=300,
                    max_queries=10_000
                )
                self._loop = self.pool._loop
            except Exception as e:
                logger.error(f"连接池初始化失败: {str(e)}")
                raise

        return self.pool

    async def execute_query(self, query: str, *args) -> Any:
        """执行查询"""
        if not self.pool:
            await self._create_pool()

        try:
            async with self.pool.acquire() as conn:
                if query.strip().upper().startswith('SELECT'):
                    rows = await conn.fetch(query, *args)
                    return [dict(row) for row in rows]
                else:
                    await conn.execute(query, *args)
                    return None
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise

    async def close(self) -> None:
        """关闭连接"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False

    async def _create_pool(self):
        """创建连接池"""
        if not self.pool:
            try:
                valid_config = {
                    "database": self.connection_config["dbname"],
                    "user": self.connection_config["user"],
                    "password": self.connection_config["password"],
                    "host": self.connection_config["host"],
                    "port": self.connection_config.get("port", '5432')
                }
                self.pool = await asyncpg.create_pool(
                    loop=st.session_state._loop,
                    **valid_config,
                    min_size=3,
                    max_size=self.max_pool_size,
                    command_timeout=self.query_timeout,
                    max_inactive_connection_lifetime=300,
                    max_queries=10_000
                )
                self._loop = self.pool._loop
            except Exception as e:
                logger.error(f"连接池初始化失败: {str(e)}")
                raise

    async def _init_db_tables(self):
        """初始化表结构"""
        logger.info("开始数据库表结构初始化...")

        async with self.pool.acquire() as conn:
            # 建表StockData
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS StockData (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    open NUMERIC NOT NULL,
                    high NUMERIC NOT NULL,
                    low NUMERIC NOT NULL,
                    close NUMERIC NOT NULL,
                    volume NUMERIC NOT NULL,
                    amount NUMERIC,
                    adjustflag VARCHAR(10),
                    frequency VARCHAR(10) NOT NULL,
                    UNIQUE (code, date, time, frequency)
                );
            """)

            # 建表StockInfo
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS StockInfo (
                    code VARCHAR(20) PRIMARY KEY,
                    code_name VARCHAR(50) NOT NULL,
                    ipoDate DATE NOT NULL,
                    outDate DATE,
                    type VARCHAR(20),
                    status VARCHAR(10)
                );
            """)

            # 建表PoliticalEvents
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS PoliticalEvents (
                    id SERIAL PRIMARY KEY,
                    event_date TIMESTAMP NOT NULL,
                    country VARCHAR(50) NOT NULL,
                    policy_type VARCHAR(100) NOT NULL,
                    impact_score NUMERIC(5,2) NOT NULL,
                    raw_content TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # 建表MoneySupplyData
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS MoneySupplyData (
                    id SERIAL PRIMARY KEY,
                    stat_month VARCHAR(10) NOT NULL,
                    m2 NUMERIC NOT NULL,
                    m2_yoy NUMERIC NOT NULL,
                    m1 NUMERIC NOT NULL,
                    m1_yoy NUMERIC NOT NULL,
                    m0 NUMERIC NOT NULL,
                    m0_yoy NUMERIC NOT NULL,
                    cd NUMERIC NOT NULL,
                    cd_yoy NUMERIC NOT NULL,
                    qm NUMERIC NOT NULL,
                    qm_yoy NUMERIC NOT NULL,
                    ftd NUMERIC NOT NULL,
                    ftd_yoy NUMERIC NOT NULL,
                    sd NUMERIC NOT NULL,
                    sd_yoy NUMERIC NOT NULL,
                    UNIQUE (stat_month)
                );
            """)

        logger.debug("数据库表结构初始化完成")

    async def save_stock_info(self, code: str, code_name: str, ipo_date: str,
                             stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息到StockInfo表"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (code) DO UPDATE SET
                        code_name = $2,
                        ipoDate = $3,
                        outDate = $4,
                        type = $5,
                        status = $6
                """, code, code_name, ipo_date, out_date, stock_type, status)
                logger.info(f"成功保存股票基本信息: {code}")
                return True
        except Exception as e:
            logger.error(f"保存股票信息失败: {str(e)}")
            raise

    async def check_data_completeness(self, symbol: str, start_date: date, end_date: date, frequency: str) -> list:
        """检查数据完整性"""
        if not self.pool:
            await self._create_pool()

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

            async with self.pool.acquire() as conn:
                # 获取数据库中已有日期
                query = """
                    SELECT DISTINCT date
                    FROM StockData
                    WHERE code = $1 AND frequency = $4 AND date BETWEEN $2 AND $3
                    ORDER BY date
                """
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                logger.info(f"从数据库获取 {start_dt}-{end_dt} for {symbol}")

                existing_dates = {pd.to_datetime(row["date"]).date() for row in rows}

                # 生成理论交易日集合（排除节假日）
                all_dates = pd.date_range(start_dt, end_dt, freq='B')  # 工作日
                trading_dates = set(
                    date.date() for date in all_dates
                    if not calendar.is_holiday(date.date())
                )
                today = date.today()
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

    async def load_stock_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
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

            # 如果有缺失数据，从数据源获取并保存
            if missing_ranges:
                logger.info(f"Fetching missing data ranges for {symbol}")
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource(frequency)
                data = pd.DataFrame()
                for range_start, range_end in missing_ranges:
                    logger.info(f"Fetching data from {range_start} to {range_end}")
                    new_data = await data_source.load_data(symbol, range_start, range_end, frequency)
                    await self.save_stock_data(symbol, new_data, frequency)
                    data = pd.concat([data, new_data])
            else:
                logger.info(f"数据完整，无需从外部数据源获取 {symbol} 的数据")

            # 从数据库加载完整数据
            query = """
                SELECT date, time, code, open, high, low, close, volume, amount, adjustflag, frequency
                FROM StockData
                WHERE code = $1
                AND date BETWEEN $2 AND $3
                AND frequency = $4
                ORDER BY date
            """

            logger.info(f"执行数据库查询，参数: symbol={symbol}, start={start_dt}, end={end_dt}, frequency={frequency}")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                logger.info(f"数据库查询完成，返回 {len(rows) if rows else 0} 行数据")

                if not rows:
                    logger.warning(
                        f"[{symbol}] 未找到股票数据 date_range=[{start_date}~{end_date}] "
                        f"frequency={frequency} pool_status={self.get_pool_status()}",
                        extra={'connection_id': f'QUERY-{symbol}'}
                    )
                    logger.debug(
                        f"详细查询参数: symbol={symbol} "
                        f"start_date={start_dt} end_date={end_dt} "
                        f"frequency={frequency}"
                    )
                    return pd.DataFrame()

                data = [dict(row) for row in rows]
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
        # 数据转换逻辑（与原DatabaseManager相同）
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')

        # 处理time列，确保格式正确
        if 'time' in data.columns:
            # 检查time列是否包含NaT值
            if data['time'].isna().any():
                logger.warning(f"发现 {data['time'].isna().sum()} 个NaT值在time列")
                # 对于NaT值，使用默认时间
                data.loc[data['time'].isna(), 'time'] = '00:00:00'

            # 确保time列是字符串格式
            data['time'] = data['time'].astype(str)

            # 处理可能的异常格式
            data['time'] = data['time'].apply(lambda x: x if len(x) >= 8 else '00:00:00')

        # 处理frequency列，确保格式正确
        if 'frequency' in data.columns:
            # 检查frequency列是否包含NaN值
            if data['frequency'].isna().any():
                logger.warning(f"发现 {data['frequency'].isna().sum()} 个NaN值在frequency列")
                # 对于NaN值，使用默认频率
                data.loc[data['frequency'].isna(), 'frequency'] = 'd'

        # 创建combined_time列用于回测
        if 'date' in data.columns and 'time' in data.columns:
            try:
                # 确保date和time列都是字符串格式
                data['date'] = data['date'].astype(str)
                data['time'] = data['time'].astype(str)

                # 创建combined_time列
                data['combined_time'] = data['date'] + ' ' + data['time']

                # 转换为datetime格式，处理可能的格式错误
                data['combined_time'] = pd.to_datetime(
                    data['combined_time'],
                    format='%Y-%m-%d %H:%M:%S',
                    errors='coerce'
                )

                # 检查是否有转换失败的记录
                if data['combined_time'].isna().any():
                    failed_count = data['combined_time'].isna().sum()
                    logger.warning(f"发现 {failed_count} 个combined_time转换失败")

                    # 对于转换失败的记录，使用date + 默认时间
                    mask = data['combined_time'].isna()
                    data.loc[mask, 'combined_time'] = pd.to_datetime(
                        data.loc[mask, 'date'] + ' 00:00:00',
                        format='%Y-%m-%d %H:%M:%S'
                    )

            except Exception as e:
                logger.error(f"创建combined_time列失败: {str(e)}")
                # 回退方案：只使用date列
                data['combined_time'] = pd.to_datetime(data['date'])

        # 确保数据按combined_time排序（修复回测和图表显示问题）
        if 'combined_time' in data.columns:
            data = data.sort_values(by='combined_time').reset_index(drop=True)

        return data

    async def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票信息"""
        try:
            logger.debug("检查数据是否最新")
            if await self._is_stock_info_up_to_date():
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch("SELECT * FROM StockInfo")
                    return pd.DataFrame(rows, columns=['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status'])
            else:
                # 调用baostock_source更新数据
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource()
                df = await data_source._get_all_stocks()
                # 将数据保存到数据库
                await self._update_stock_info(df)
                return df
        except Exception as e:
            logger.error(f"获取所有股票信息失败: {str(e)}")
            raise

    async def _is_stock_info_up_to_date(self, max_retries: int = 3) -> bool:
        """检查StockInfo表是否最新"""
        if not self.pool:
            await self._create_pool()

        for attempt in range(max_retries):
            try:
                async with self.pool.acquire() as conn:
                    logger.debug(f"检查StockInfo表状态(尝试{attempt+1}/{max_retries})")

                    # 检查表是否存在
                    table_check = await conn.fetchval(
                        """SELECT 1 FROM information_schema.tables
                        WHERE table_schema='public' AND table_name='stockinfo'"""
                    )
                    if not table_check:
                        raise ValueError("表StockInfo不存在")

                    # 检查最新IPO日期
                    row = await conn.fetchrow(
                        """SELECT ipoDate FROM StockInfo
                        ORDER BY ipoDate DESC LIMIT 1"""
                    )

                    if not row:
                        logger.warning("StockInfo表为空")
                        return False

                    latest_ipo = pd.Timestamp(row['ipodate'])
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
                    is_up_to_date = latest_ipo >= cutoff

                    logger.debug(f"最新IPO日期: {latest_ipo.isoformat()}, 是否最新: {is_up_to_date}")
                    return is_up_to_date

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"检查StockInfo表状态失败(最终尝试): {str(e)}")
                    raise
                logger.warning(f"检查StockInfo表状态失败(尝试{attempt+1}): {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避
        return False

    async def _update_stock_info(self, df: pd.DataFrame) -> tuple:
        """更新StockInfo表数据"""
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

            async with self.pool.acquire() as conn:
                # 清空现有数据
                logger.debug("Truncating StockInfo table")
                await conn.execute("TRUNCATE TABLE StockInfo")

                # 执行批量插入
                logger.debug(f"Inserting {len(valid_data)} rows into StockInfo")
                await conn.executemany("""
                    INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, valid_data)

            logger.info(f"成功更新StockInfo表数据，成功插入{len(valid_data)}行，失败{len(invalid_rows)}行")
            return len(valid_data), len(invalid_rows)

        except Exception as e:
            logger.error(f"批量插入失败: {str(e)}")
            raise

    async def _validate_stock_info(self, row: pd.Series) -> tuple:
        """验证并转换股票信息格式"""
        try:
            # 验证必填字段
            required_fields = ['code', 'code_name', 'ipoDate', 'type', 'status']
            for field in required_fields:
                if pd.isna(row[field]) or row[field] == '':
                    raise ValueError(f"Missing required field: {field}")

            # 验证ipoDate
            if not isinstance(row['ipoDate'], str) or len(row['ipoDate']) != 10:
                raise ValueError(f"Invalid ipoDate format: {row['ipoDate']}")

            ipo_date = pd.to_datetime(row['ipoDate'], format='%Y-%m-%d', errors='coerce')
            if pd.isna(ipo_date):
                raise ValueError(f"Invalid ipoDate value: {row['ipoDate']}")
            ipo_date = ipo_date.date()

            # 处理outDate
            out_date = None
            if not pd.isna(row.get('outDate')) and row.get('outDate') != '':
                out_date = pd.to_datetime(row['outDate'], format='%Y-%m-%d', errors='coerce')
                if pd.isna(out_date):
                    raise ValueError(f"Invalid outDate value: {row['outDate']}")
                out_date = out_date.date()

            return (
                str(row['code']),
                str(row['code_name']),
                ipo_date,
                out_date,
                str(row['type']),
                str(row['status'])
            )
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)} - 行数据: {row.to_dict()}")
            raise

    async def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT code_name, ipoDate, outDate, type, status
                    FROM StockInfo
                    WHERE code = $1
                """, code)

                if not row:
                    return {}

                return {
                    "code_name": row['code_name'],
                    "ipo_date": row['ipodate'].strftime("%Y-%m-%d"),
                    "out_date": row['outdate'].strftime("%Y-%m-%d") if row['outdate'] else None,
                    "type": row['type'],
                    "status": row['status']
                }
        except Exception as e:
            logger.error(f"获取股票信息失败: {str(e)}")
            raise

    async def get_stock_name(self, code: str) -> str:
        """根据股票代码获取名称"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT code_name FROM StockInfo WHERE code = $1
                """, code)
                return row['code_name'] if row else ""
        except Exception as e:
            logger.error(f"获取股票名称失败: {str(e)}")
            raise

    async def save_stock_data(self, symbol: str, data: pd.DataFrame, frequency: str) -> bool:
        """保存股票数据到StockData表"""
        data_tmp = data.copy()
        data_tmp['date'] = pd.to_datetime(data_tmp['date'], format="%Y-%m-%d").dt.date
        try:
            records = data_tmp.to_dict('records')

            # 处理不同频率的数据
            if frequency in ["1", "5", "15", "30", "60"]:
                # 分钟级数据有time字段
                insert_data = [
                    (
                        symbol,
                        record['date'],
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
                        record['date'],
                        time.min,  # 使用time.min表示00:00:00
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

            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO StockData (
                        code, date, time, open, high, low, close,
                        volume, amount, adjustflag, frequency
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (code, date, time, frequency) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        amount = EXCLUDED.amount,
                        adjustflag = EXCLUDED.adjustflag
                """, insert_data)

            return True

        except Exception as e:
            logger.error(f"保存股票数据失败: {str(e)}")
            raise

    async def save_money_supply_data(self, data: pd.DataFrame) -> bool:
        """保存货币供应量数据"""
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

            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO MoneySupplyData (
                        stat_month, m2, m2_yoy, m1, m1_yoy, m0, m0_yoy,
                        cd, cd_yoy, qm, qm_yoy, ftd, ftd_yoy, sd, sd_yoy
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (stat_month) DO UPDATE SET
                        m2 = EXCLUDED.m2,
                        m2_yoy = EXCLUDED.m2_yoy,
                        m1 = EXCLUDED.m1,
                        m1_yoy = EXCLUDED.m1_yoy,
                        m0 = EXCLUDED.m0,
                        m0_yoy = EXCLUDED.m0_yoy,
                        cd = EXCLUDED.cd,
                        cd_yoy = EXCLUDED.cd_yoy,
                        qm = EXCLUDED.qm,
                        qm_yoy = EXCLUDED.qm_yoy,
                        ftd = EXCLUDED.ftd,
                        ftd_yoy = EXCLUDED.ftd_yoy,
                        sd = EXCLUDED.sd,
                        sd_yoy = EXCLUDED.sd_yoy
                """, insert_data)

            logger.info(f"成功保存{len(insert_data)}条货币供应量数据")
            return True

        except Exception as e:
            logger.error(f"保存货币供应量数据失败: {str(e)}")
            raise

    async def get_money_supply_data(self, start_month: str, end_month: str) -> pd.DataFrame:
        """获取货币供应量数据"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM MoneySupplyData
                    WHERE stat_month BETWEEN $1 AND $2
                    ORDER BY stat_month
                """, start_month, end_month)

                if not rows:
                    logger.warning(f"未找到{start_month}至{end_month}的货币供应量数据",
                                   extra={'connection_id': 'MONETARY-QUERY'})
                    return pd.DataFrame()

                df = pd.DataFrame(rows, columns=[
                    'stat_month', 'm2', 'm2_yoy', 'm1', 'm1_yoy',
                    'm0', 'm0_yoy', 'cd', 'cd_yoy', 'qm', 'qm_yoy',
                    'ftd', 'ftd_yoy', 'sd', 'sd_yoy'
                ])

                logger.info(f"成功获取{len(df)}条货币供应量数据")
                return df

        except Exception as e:
            logger.error(f"获取货币供应量数据失败: {str(e)}")
            raise

    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        return {
            "db_type": "postgresql",
            "max_size": self.max_pool_size,
            "active": len(self.active_connections),
            "oldest": min((v["acquired_at"] for v in self.active_connections.values()), default=None),
            "initialized": self._initialized,
            "connected": self.pool is not None
        }

    # 暴露循环属性给外部使用
    @property
    def _loop(self):
        return getattr(self, '__loop', None)

    @_loop.setter
    def _loop(self, value):
        self.__loop = value