import asyncpg
from typing import Optional, List, Dict
import pandas as pd
import chinese_calendar as calendar
import streamlit as st
from datetime import datetime, date,time
import asyncio
import os
from support.log.logger import logger

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

@st.cache_resource(ttl=3600, show_spinner=False)
def get_db_manager():
    """带缓存的数据库管理器工厂函数"""
    manager = DatabaseManager()
    return manager


class DatabaseManager:
    def __init__(self, host=None, port=None, dbname=None,
                 user=None, password=None, admin_db=None):
        self.connection = None
        # self._loop = asyncio.get_event_loop()  # 全局唯一事件循环
        import logging
        from support.log.logger import logger
        logger = logger
        logger.setLevel(logging.DEBUG)
        self._instance_id = id(self)  # 添加实例ID用于调试
        self.connection_states = {}  # 连接状态跟踪 {conn_id: {status, last_change}}
        logger.debug(f"DatabaseManager initialized, instance_id: {self._instance_id}")  # 测试warning日志
        # 从环境变量获取配置，支持参数覆盖
        db_password = password or os.getenv('DB_PASSWORD')
        if not db_password:
            raise ValueError("数据库密码未配置。请设置DB_PASSWORD环境变量或通过参数传递。")

        self.connection_config = { # 数据库连接配置
            'host': host or os.getenv('DB_HOST', 'localhost'),
            'port': port or os.getenv('DB_PORT', '5432'),
            'dbname': dbname or os.getenv('DB_NAME', 'quantdb'),
            'user': user or os.getenv('DB_USER', 'quant'),
            'password': db_password
        }
        self.admin_config = {
            'host': host or os.getenv('DB_HOST', 'localhost'),
            'port': port or os.getenv('DB_PORT', '5432'),
            'dbname': admin_db or os.getenv('ADMIN_DB_NAME', 'quantdb'),
            'user': user or os.getenv('DB_USER', 'quant'),
            'password': db_password
        }
        self._initialized = False  # 初始化状态
        self._initializing = False  # 防止重复初始化
        self.pool = None  # 记录连接池
        self._loop = None
        self.max_pool_size = int(os.getenv('DB_MAX_POOL_SIZE', '15'))  # 最大连接数
        self.query_timeout = int(os.getenv('DB_QUERY_TIMEOUT', '60'))  # 查询超时时间（秒）
        self.active_connections = {}  # 目前活跃的连接
        self._conn_lock = asyncio.Lock()  
        

    async def initialize(self):
        """异步初始化整个模块"""
        if self._initialized:
            return
            
        start_time = asyncio.get_event_loop().time()
        await self._create_pool()
        await self._init_db_tables()
        self._initialized = True
        logger.debug(
            f"initialize调用结束，总耗时: {asyncio.get_event_loop().time() - start_time:.2f}s"
        )

    async def _create_pool(self):
        """创建连接池"""
        if not self.pool:
            try:
                valid_config = {
                    "database": self.connection_config["dbname"],
                    "user": self.connection_config["user"],
                    "password": self.connection_config["password"],
                    "host": self.connection_config["host"],
                    "port": self.connection_config.get("port",'5432')
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
                # logger.debug(f"连接池初始化成功, 循环ID: {id(self.pool._loop)}")
            except Exception as e:
                logger.error(f"连接池初始化失败: {str(e)}")
                raise
            # logger.debug(f"running_loop_id:{id(asyncio.get_running_loop())}")

    async def _init_db_tables(self):
        """异步初始化表结构"""
        logger.info("开始数据库表结构初始化...")
        # 删表（测试用）
        # await self.del_stock_data("StockData")

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
            
        logger.debug("数据库表结构初始化完成",
                extra={'connection_id': id(conn)}
            )
        # logger.debug(f"连接已释放，当前活跃连接数: {self.pool.get_size() - self.pool.get_idle_size()}")
        logger.debug(f"当前循环活跃状态: {not asyncio.get_event_loop().is_closed()}")
    
    async def _get_connection(self):
        """异步获取数据库连接"""
        try:
            async with self.pool.acquire() as conn:  # ✅ 进入上下文管理器
                return conn  # 返回 Connection 对象
        except Exception as e:
            logger.error(f"Failed to get database connection: {str(e)}")
            raise

    async def save_stock_info(self, code: str, code_name: str, ipo_date: str, 
                      stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """异步保存股票基本信息到StockInfo表"""
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
        """异步检查数据完整性
        Args:
            symbol: 股票代码
            start_date: 开始日期(date对象或字符串)
            end_date: 结束日期(date对象或字符串)
        Returns:
            缺失日期区间列表[(start1,end1), (start2,end2)...]
        """
        # logger.debug("""异步检查数据完整性""")
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
                logger.info(f"从数据库获取 {start_dt}-{end_dt} for {symbol}\n")

                existing_dates = {pd.to_datetime(row["date"]).date() for row in rows}
                # logger.info(f"Existing_dates {existing_dates} for {symbol}\n")
                
                # 生成理论交易日集合（排除节假日）
                all_dates = pd.date_range(start_dt, end_dt, freq='B')  # 工作日
                trading_dates = set(
                    date.date() for date in all_dates 
                    if not calendar.is_holiday(date.date())
                )
                today = date.today()
                trading_dates = {d for d in trading_dates if d != today}  # 若今日查询，则排除今日
                # logger.info(f"trading_dates {trading_dates} for {symbol}")
                
                # 计算缺失日期
                missing_dates = trading_dates - existing_dates
                # logger.info(f"Missing_dates {missing_dates} for {symbol}")
                
                # 将连续缺失日期合并为区间
                missing_ranges = []
                if missing_dates:
                    sorted_dates = sorted(missing_dates)
                    range_start = sorted_dates[0]
                    prev_date = range_start
                    
                    for current_date in sorted_dates[1:]:
                        if (current_date - prev_date).days > 1:  # 出现断点
                            missing_ranges.append((range_start,
                                                 prev_date))
                            range_start = current_date
                        prev_date = current_date
                    
                    # 添加最后一个区间
                    missing_ranges.append((range_start,
                                         prev_date))
                
                logger.info(f"Found {len(missing_ranges)} missing data ranges for {symbol}")
                return missing_ranges
                
        except Exception as e:
            logger.error(f"检查数据完整性失败: {str(e)}")
            raise

# 加载数据
    async def load_stock_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
        """从数据库加载股票数据，如有缺失则从数据源获取并保存
        Args:
            symbol: 股票代码
            start_date: 开始日期(date对象或字符串)
            end_date: 结束日期(date对象或字符串)
            frequency: 数据频率(如'd'表示日线)
        Returns:
            包含股票数据的DataFrame
        """
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
            # the date that data lack of  #
            missing_ranges = await self.check_data_completeness(symbol, start_dt, end_dt,frequency)

            # Fetch missing data ranges from Baostock
            if missing_ranges:
                logger.info(f"missing_ranges {missing_ranges}")
                logger.info(f"Fetching missing data ranges for {symbol}")  
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource(frequency)
                data = pd.DataFrame()
                for range_start, range_end in missing_ranges:
                    logger.info(f"Fetching data from {range_start} to {range_end}")
                    # 转换为 Baostock 需要的格式
                    
                    new_data = await data_source.load_data(symbol, range_start, range_end, frequency)
                    
                    await self.save_stock_data(symbol, new_data, frequency)  # save stock data into table Stockdata
                    data = pd.concat([data, new_data])

            

            # Load complete data from database
            query = """
                SELECT date, time, code, open, high, low, close, volume, amount, adjustflag, frequency
                FROM StockData
                WHERE code = $1
                AND date BETWEEN $2 AND $3
                AND frequency = $4
                ORDER BY date
            """
            
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                
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
                df = pd.DataFrame(data, columns=['date', 'time', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag', 'frequency'])
                df = self._transform_data(df)
                
                
                logger.info(f"Successfully loaded {len(df)} rows for {symbol}")
                return df
                
        except Exception as e:
            logger.error(f"Failed to load stock data: {str(e)}")
            raise

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        
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

        # 调试信息：检查time和frequency列是否有空值
        time_nulls = 0
        freq_nulls = 0
        
        if 'time' in data.columns:
            time_nulls = data['time'].isna().sum()
            if time_nulls > 0:
                logger.warning(f"time列包含 {time_nulls} 个空值")
                
        if 'frequency' in data.columns:
            freq_nulls = data['frequency'].isna().sum()
            if freq_nulls > 0:
                logger.warning(f"frequency列包含 {freq_nulls} 个空值")
                
        # 确保数据按combined_time排序（修复回测和图表显示问题）
        if 'combined_time' in data.columns:
            data = data.sort_values(by='combined_time').reset_index(drop=True)
        
        # 记录数据转换后的状态
        logger.debug(f"数据转换完成 - 行数: {len(data)}, time列空值: {time_nulls}, frequency列空值: {freq_nulls}")

        return data

    def get_technical_indicators(self):
        pass

    async def get_all_stocks(self) -> pd.DataFrame:
        """异步获取所有股票信息
        1. 若数据库表StockInfo是最新，则返回StockInfo数据库表的所有数据
        2. 若数据库表StockInfo不是最新，则调用baostock_source.py的get_all_stocks方法更新数据
        Returns:
            包含所有股票信息的DataFrame
        """
        # logger.debug(f"running_loop_id:{id(asyncio.get_running_loop())}")
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
        """异步检查StockInfo表是否最新
        Args:
            max_retries: 最大重试次数
        """
        if not self.pool:
            await self._create_pool()
            
        for attempt in range(max_retries):
            try:
                async with self.pool.acquire() as conn:
                    logger.debug(f"检查StockInfo表状态(尝试{attempt+1}/{max_retries})")
                    logger.debug(f"当前活跃连接数: {self.pool.get_size() - self.pool.get_idle_size()}",
                                    extra={'connection_id': id(conn)})
                    
                    # 优化后的表检查查询
                    table_check = await conn.fetchval(
                        """SELECT 1 FROM information_schema.tables
                        WHERE table_schema='public' AND table_name='stockinfo'"""
                    )
                    if not table_check:
                        raise ValueError("表StockInfo不存在")

                    # 优化后的字段检查
                    field_check = await conn.fetchval(
                        """SELECT 1 FROM information_schema.columns
                        WHERE table_name='stockinfo' AND column_name='ipodate'"""
                    )
                    if not field_check:
                        raise ValueError("字段ipoDate不存在")

                    # 优化后的IPO日期查询
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

    async def _validate_stock_info(self, row: pd.Series) -> tuple:
        """异步验证并转换股票信息格式"""
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

    async def _update_stock_info(self, df: pd.DataFrame) -> tuple:
        """异步更新StockInfo表数据
        返回: (成功插入行数, 失败行数)
        """
        valid_data = []
        invalid_rows = []
            
        try:
            # 首先验证所有数据行
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

    async def get_stock_info(self, code: str) -> dict:
        """异步获取股票完整信息"""
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
        """异步根据股票代码获取名称"""
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
        """异步保存股票数据到StockData表
        
        Args:
            symbol: 股票代码
            data: 包含股票数据的DataFrame
            frequency: 数据频率 (如 '5' 表示5分钟线，'d' 表示日线)
            
        Returns:
            bool: 是否成功保存
        """
        data_tmp = data.copy()
        data_tmp['date'] = pd.to_datetime(data_tmp['date'], format="%Y-%m-%d").dt.date
        try:
            # 将DataFrame转换为适合插入的格式
            records = data_tmp.to_dict('records')
            
            # 处理不同频率的数据
            if frequency in ["1", "5", "15", "30", "60"]:
                # 分钟级数据有time字段
                insert_data = [
                    (
                        symbol,
                        record['date'],
                        record.get('time', "00:00:00"),  # 安全获取时间字段
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
                
            # logger.info(f"成功保存{symbol}的{frequency}频率数据，共{len(insert_data)}条记录")
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
        """获取货币供应量数据
        
        Args:
            start_month: 开始月份 (格式: YYYY-MM)
            end_month: 结束月份 (格式: YYYY-MM)
            
        Returns:
            包含货币供应量数据的DataFrame
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM MoneySupplyData
                    WHERE stat_month BETWEEN $1 AND $2
                    ORDER BY stat_month
                """, start_month, end_month)
                
                if not rows:
                    logger.warning(
                        f"未找到{start_month}至{end_month}的货币供应量数据",
                        extra={'connection_id': 'MONETARY-QUERY'}
                    )
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

    async def del_stock_data(self, name):
        logger.info(f"开始删除数据库表{name}...")
        logger.debug(f"调用了del方法")
        async with self.pool.acquire() as conn:
                # debug
            await conn.execute(
                f"""
                DROP TABLE {name};
                """
            )

            # 检查表是否存在
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_tables
                    WHERE tablename = $1
                );
                """, name
            )
            if not exists:
                logger.warning(f"表 {name}已删除", extra={'connection_id': id(conn)})

    def get_pool_status(self):
        """获取连接池状态"""
        return {
            "max_size": self.max_pool_size,
            "active": len(self.active_connections),
            "oldest": min((v["acquired_at"] for v in self.active_connections.values()), default=None)
        }

    async def monitor_connections(self):
        """定期记录连接池状态"""
        while True:
            status = self.get_pool_status()
            logger.info(f"Connection pool status: {status}")
            await asyncio.sleep(60)

    async def load_global_market_data(self, type: Optional[str] = None, year: Optional[int] = None) -> pd.DataFrame:
        """加载全球市场资金分布数据
        Args:
            type: 机构类型(可选)
            year: 年份(可选)
        Returns:
            包含全球市场资金分布数据的DataFrame
        """
        if not self.pool:
            await self._create_pool()
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT type, name, currency, assets, year FROM global_fund_distribution"
                params = []
                
                if type or year:
                    conditions = []
                    if type:
                        conditions.append("type = $1")
                        params.append(type)
                    if year:
                        conditions.append("year = ${}".format(len(params)+1))
                        params.append(year)
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY year, assets DESC"
                
                rows = await conn.fetch(query, *params)
                if not rows:
                    logger.warning("未找到全球市场资金分布数据")
                    return pd.DataFrame()
                
                return pd.DataFrame(rows, columns=['type', 'name', 'currency', 'assets', 'year'])
                
        except Exception as e:
            logger.error(f"获取全球市场资金分布数据失败: {str(e)}")
            raise

    async def get_distinct_values(self) -> dict:
        """获取全球市场资金分布表中的distinct类型和年份
        Returns:
            {'types': [类型列表], 'years': [年份列表]}
        """
        if not self.pool:
            await self._create_pool()
        try:
            async with self.pool.acquire() as conn:
                # 获取distinct类型
                type_rows = await conn.fetch(
                    "SELECT DISTINCT type FROM global_fund_distribution ORDER BY type"
                )
                types = [row['type'] for row in type_rows] if type_rows else []
                
                # 获取distinct年份
                year_rows = await conn.fetch(
                    "SELECT DISTINCT year FROM global_fund_distribution ORDER BY year DESC"
                )
                years = [str(row['year']) for row in year_rows] if year_rows else []
                
                return {
                    'types': types,
                    'years': years
                }
                
        except Exception as e:
            logger.error(f"获取distinct值失败: {str(e)}")
            return {'types': [], 'years': []}

    # 交易相关方法
    async def _init_trade_tables(self):
        """Initialize trade-related tables"""
        try:
            async with self.pool.acquire() as conn:
                # Create Orders table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS Orders (
                        order_id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        order_type VARCHAR(20) NOT NULL,
                        quantity NUMERIC NOT NULL,
                        price NUMERIC,
                        status VARCHAR(20) NOT NULL,
                        create_time TIMESTAMP NOT NULL,
                        update_time TIMESTAMP
                    );
                """)
                
                # Create Executions table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS Executions (
                        execution_id SERIAL PRIMARY KEY,
                        order_id INTEGER REFERENCES Orders(order_id),
                        exec_price NUMERIC,
                        exec_quantity NUMERIC,
                        exec_time TIMESTAMP,
                        status VARCHAR(20) NOT NULL
                    );
                """)
                
                # Create TradeHistory table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS TradeHistory (
                        trade_id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        trade_time TIMESTAMP NOT NULL,
                        trade_price NUMERIC NOT NULL,
                        trade_quantity NUMERIC NOT NULL,
                        trade_type VARCHAR(10) NOT NULL
                    );
                """)
                
                logger.info("Trade tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize trade tables: {str(e)}")
            raise

    async def save_order(self, order: dict) -> int:
        """Save an order to database"""
        try:
            async with self.pool.acquire() as conn:
                order_id = await conn.fetchval("""
                    INSERT INTO Orders 
                    (symbol, order_type, quantity, price, status, create_time)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING order_id
                """, 
                    order['symbol'],
                    order['order_type'],
                    order['quantity'],
                    order['price'],
                    order['status'],
                    datetime.now()
                )
                return order_id
        except Exception as e:
            logger.error(f"Failed to save order: {str(e)}")
            raise

    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE Orders
                    SET status = $1, update_time = $2
                    WHERE order_id = $3
                """, status, datetime.now(), order_id)
                return True
        except Exception as e:
            logger.error(f"Failed to update order status: {str(e)}")
            raise

    async def log_execution(self, execution: dict) -> int:
        """Log execution result"""
        try:
            async with self.pool.acquire() as conn:
                execution_id = await conn.fetchval("""
                    INSERT INTO Executions
                    (order_id, exec_price, exec_quantity, exec_time, status)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING execution_id
                """,
                    execution['order_id'],
                    execution['exec_price'],
                    execution['exec_quantity'],
                    datetime.now(),
                    execution['status']
                )
                return execution_id
        except Exception as e:
            logger.error(f"Failed to log execution: {str(e)}")
            raise

    async def record_trade(self, trade: dict) -> int:
        """Record a trade"""
        try:
            async with self.pool.acquire() as conn:
                trade_id = await conn.fetchval("""
                    INSERT INTO TradeHistory
                    (symbol, trade_time, trade_price, trade_quantity, trade_type)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING trade_id
                """,
                    trade['symbol'],
                    datetime.now(),
                    trade['trade_price'],
                    trade['trade_quantity'],
                    trade['trade_type']
                )
                return trade_id
        except Exception as e:
            logger.error(f"Failed to record trade: {str(e)}")
            raise

    async def query_orders(self, symbol: str = None) -> list:
        """Query orders"""
        try:
            async with self.pool.acquire() as conn:
                if symbol:
                    rows = await conn.fetch("""
                        SELECT * FROM Orders WHERE symbol = $1
                    """, symbol)
                else:
                    rows = await conn.fetch("SELECT * FROM Orders")
                return rows
        except Exception as e:
            logger.error(f"Failed to query orders: {str(e)}")
            raise

    async def query_trades(self, symbol: str = None) -> list:
        """Query trade history"""
        try:
            async with self.pool.acquire() as conn:
                if symbol:
                    rows = await conn.fetch("""
                        SELECT * FROM TradeHistory WHERE symbol = $1
                    """, symbol)
                else:
                    rows = await conn.fetch("SELECT * FROM TradeHistory")
                return rows
        except Exception as e:
            logger.error(f"Failed to query trades: {str(e)}")
            raise

    async def batch_update_order_status(self, updates: list) -> bool:
        """批量更新订单状态
        Args:
            updates: [(order_id, new_status), ...]
        Returns:
            bool: 是否成功
        """
        try:
            async with self.pool.acquire() as conn:
                # 使用事务批量更新
                async with conn.transaction():
                    for order_id, status in updates:
                        await conn.execute("""
                            UPDATE Orders
                            SET status = $1, update_time = $2
                            WHERE order_id = $3
                        """, status, datetime.now(), order_id)
                return True
        except Exception as e:
            logger.error(f"批量更新订单状态失败: {str(e)}")
            raise

    async def load_multiple_stock_data(self, symbols: List[str], start_date: date, end_date: date, frequency: str) -> Dict[str, pd.DataFrame]:
        """批量加载多个股票的数据
        Args:
            symbols: 股票代码列表
            start_date: 开始日期(date对象)
            end_date: 结束日期(date对象)
            frequency: 数据频率
        Returns:
            字典，键为股票代码，值为对应的DataFrame
        """
        import asyncio
        
        async def load_single(symbol):
            try:
                data = await self.load_stock_data(symbol, start_date, end_date, frequency)
                return symbol, data
            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
                return symbol, pd.DataFrame()
        
        # 并行加载所有股票数据
        tasks = [load_single(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return {symbol: data for symbol, data in results if not data.empty}
