import asyncpg
from typing import Optional
import pandas as pd
import chinese_calendar as calendar
from .stock import Stock
import streamlit as st
from datetime import datetime, date,time
import asyncio

@st.cache_resource(ttl=3600, show_spinner=False)
def get_db_manager():
    """带缓存的数据库管理器工厂函数"""
    manager = DatabaseManager()
    return manager


class DatabaseManager:
    def __init__(self, host='113.45.40.20', port='8080', dbname='quantdb',
                 user='quant', password='quant123', admin_db='quantdb'):
        self.connection = None
        # self._loop = asyncio.get_event_loop()  # 全局唯一事件循环
        import logging
        from support.log.logger import logger
        self.logger = logger
        self.logger.setLevel(logging.DEBUG)
        self._instance_id = id(self)  # 添加实例ID用于调试
        self.connection_states = {}  # 连接状态跟踪 {conn_id: {status, last_change}}
        self.logger.debug(f"DatabaseManager initialized, instance_id: {self._instance_id}")  # 测试warning日志
        self.connection_config = { # 数据库连接配置
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.admin_config = {
            'host': host,
            'port': port,
            'dbname': admin_db,
            'user': user,
            'password': password
        }
        self._initialized = False  # 初始化状态
        self._initializing = False  # 防止重复初始化
        self.pool = None  # 记录连接池
        self._loop = None
        self.max_pool_size = 15  # 最大连接数
        self.query_timeout = 60  # 查询超时时间（秒）
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
        self.logger.debug(
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
                self.logger.debug(f"连接池初始化成功, 循环ID: {id(self.pool._loop)}")
            except Exception as e:
                self.logger.error(f"连接池初始化失败: {str(e)}")
                raise
            # self.logger.debug(f"running_loop_id:{id(asyncio.get_running_loop())}")

    async def _init_db_tables(self):
        """异步初始化表结构"""
        self.logger.info("开始数据库表结构初始化...")
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
            
        self.logger.debug("数据库表结构初始化完成",
                extra={'connection_id': id(conn)}
            )
        # self.logger.debug(f"连接已释放，当前活跃连接数: {self.pool.get_size() - self.pool.get_idle_size()}")
        self.logger.debug(f"当前循环活跃状态: {not asyncio.get_event_loop().is_closed()}")
    
    async def _get_connection(self):
        """异步获取数据库连接"""
        try:
            async with self.pool.acquire() as conn:  # ✅ 进入上下文管理器
                return conn  # 返回 Connection 对象
        except Exception as e:
            self.logger.error(f"Failed to get database connection: {str(e)}")
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
                self.logger.info(f"成功保存股票基本信息: {code}")
                return True
        except Exception as e:
            self.logger.error(f"保存股票信息失败: {str(e)}")
            raise

    async def check_data_completeness(self, symbol: str, start_date: date, end_date: date, frequency: str) -> list:
        """异步检查数据完整性
        Args:
            symbol: 股票代码
            start_date: 开始日期(date对象)，示例
            end_date: 结束日期(date对象)
        Returns:
            缺失日期区间列表[(start1,end1), (start2,end2)...]
        """
        self.logger.debug("""异步检查数据完整性""")
        if not self.pool:
            await self._create_pool()

        try:
            self.logger.info(f"Checking data completeness for {symbol} from {start_date} to {end_date}")
            
            # 直接使用date对象
            start_dt = start_date
            end_dt = end_date
            
            async with self.pool.acquire() as conn:
                # 获取数据库中已有日期
                query = """
                    SELECT DISTINCT date 
                    FROM StockData
                    WHERE code = $1 AND frequency = $4 AND date BETWEEN $2 AND $3 
                    ORDER BY date
                """
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                self.logger.info(f"从数据库获取 {start_dt}-{end_dt} for {symbol}\n")

                existing_dates = {pd.to_datetime(row["date"]).date() for row in rows}
                # self.logger.info(f"Existing_dates {existing_dates} for {symbol}\n")
                
                # 生成理论交易日集合（排除节假日）
                all_dates = pd.date_range(start_dt, end_dt, freq='B')  # 工作日
                trading_dates = set(
                    date.date() for date in all_dates 
                    if not calendar.is_holiday(date.date())
                )
                today = date.today()
                trading_dates = {d for d in trading_dates if d != today}  # 若今日查询，则排除今日
                # self.logger.info(f"trading_dates {trading_dates} for {symbol}")
                
                # 计算缺失日期
                missing_dates = trading_dates - existing_dates
                # self.logger.info(f"Missing_dates {missing_dates} for {symbol}")
                
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
                
                self.logger.info(f"Found {len(missing_ranges)} missing data ranges for {symbol}")
                return missing_ranges
                
        except Exception as e:
            self.logger.error(f"检查数据完整性失败: {str(e)}")
            raise

# 加载数据
    async def load_stock_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
        """从数据库加载股票数据，如有缺失则从数据源获取并保存
        Args:
            symbol: 股票代码
            start_date: 开始日期(date对象)
            end_date: 结束日期(date对象)
            frequency: 数据频率(如'd'表示日线)
        Returns:
            包含股票数据的DataFrame
        """
        try:
            self.logger.info(f"Loading stock data for {symbol} from {start_date} to {end_date}")

            # the date that data lack of  # 
            missing_ranges = await self.check_data_completeness(symbol, start_date, end_date,frequency)
            
            # 直接使用date对象
            start_dt = start_date
            end_dt = end_date

            # Fetch missing data ranges from Baostock
            if missing_ranges:
                self.logger.info(f"missing_ranges {missing_ranges}")
                self.logger.info(f"Fetching missing data ranges for {symbol}")  
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource(frequency)
                data = pd.DataFrame()
                for range_start, range_end in missing_ranges:
                    self.logger.info(f"Fetching data from {range_start} to {range_end}")
                    # 转换为 Baostock 需要的格式
                    
                    new_data = await data_source.load_data(symbol, range_start, range_end, frequency)
                    
                    await self.save_stock_data(symbol, new_data, frequency)  # save stock data into table Stockdata
                    data = pd.concat([data, new_data])

            

            # Load complete data from database
            query = """
                SELECT date, time, code, open, high, low, close, volume, amount, adjustflag
                FROM StockData
                WHERE code = $1
                AND date BETWEEN $2 AND $3
                AND frequency = $4
                ORDER BY date
            """
            
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                
                if not rows:
                    self.logger.warning(
                        f"[{symbol}] 未找到股票数据 date_range=[{start_date}~{end_date}] "
                        f"frequency={frequency} pool_status={self.get_pool_status()}",
                        extra={'connection_id': f'QUERY-{symbol}'}
                    )
                    self.logger.debug(
                        f"详细查询参数: symbol={symbol} "
                        f"start_date={start_dt} end_date={end_dt} "
                        f"frequency={frequency}"
                    )
                    return pd.DataFrame()
                data = [dict(row) for row in rows]
                df = pd.DataFrame(data, columns=['date', 'time', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag'])
                df = self._transform_data(df)
                
                self.logger.info(f"Successfully loaded {len(df)} rows for {symbol}")
                return df
                
        except Exception as e:
            self.logger.error(f"Failed to load stock data: {str(e)}")
            raise

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        if 'time' in data.columns:
            data['time'] = data['time'].astype(str)
            data['time'] = pd.to_datetime(
                data['time'].str[9:14],
                format="%H%M%S"
            ).dt.time

        return data

    def get_technical_indicators(self):
        pass

    def get_stock(self, code: str) -> Stock:
        """获取股票对象
        Args:
            code: 股票代码，如 '600000'
        Returns:
            Stock实例
        """
        return Stock(code, self)

    async def get_all_stocks(self) -> pd.DataFrame:
        """异步获取所有股票信息
        1. 若数据库表StockInfo是最新，则返回StockInfo数据库表的所有数据
        2. 若数据库表StockInfo不是最新，则调用baostock_source.py的get_all_stocks方法更新数据
        Returns:
            包含所有股票信息的DataFrame
        """
        # self.logger.debug(f"running_loop_id:{id(asyncio.get_running_loop())}")
        try:
            self.logger.debug("检查数据是否最新")
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
            self.logger.error(f"获取所有股票信息失败: {str(e)}")
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
                    self.logger.debug(f"检查StockInfo表状态(尝试{attempt+1}/{max_retries})")
                    self.logger.debug(f"当前活跃连接数: {self.pool.get_size() - self.pool.get_idle_size()}",
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
                        self.logger.warning("StockInfo表为空")
                        return False
                        
                    latest_ipo = pd.Timestamp(row['ipodate'])
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
                    is_up_to_date = latest_ipo >= cutoff
                    
                    self.logger.debug(f"最新IPO日期: {latest_ipo.isoformat()}, 是否最新: {is_up_to_date}")
                    return is_up_to_date
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"检查StockInfo表状态失败(最终尝试): {str(e)}")
                    raise
                self.logger.warning(f"检查StockInfo表状态失败(尝试{attempt+1}): {str(e)}")
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
            self.logger.error(f"数据验证失败: {str(e)} - 行数据: {row.to_dict()}")
            raise

    async def _update_stock_info(self, df: pd.DataFrame) -> tuple:
        """异步更新StockInfo表数据
        返回: (成功插入行数, 失败行数)
        """
        valid_data = []
        invalid_rows = []
            
        try:
            
            async with self.pool.acquire() as conn:
            
                # 清空现有数据
                self.logger.debug("Truncating StockInfo table")
                await conn.execute("TRUNCATE TABLE StockInfo")
                
                # 执行批量插入
                self.logger.debug(f"Inserting {len(valid_data)} rows into StockInfo")
                await conn.executemany("""
                    INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, valid_data)
                
            self.logger.info(f"成功更新StockInfo表数据，成功插入{len(valid_data)}行，失败{len(invalid_rows)}行")
            return len(valid_data), len(invalid_rows)
            
        except Exception as e:
            self.logger.error(f"批量插入失败: {str(e)}")
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
            self.logger.error(f"获取股票信息失败: {str(e)}")
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
            self.logger.error(f"获取股票名称失败: {str(e)}")
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
                
            # self.logger.info(f"成功保存{symbol}的{frequency}频率数据，共{len(insert_data)}条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"保存股票数据失败: {str(e)}")
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
                
            self.logger.info(f"成功保存{len(insert_data)}条货币供应量数据")
            return True
            
        except Exception as e:
            self.logger.error(f"保存货币供应量数据失败: {str(e)}")
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
                    self.logger.warning(
                        f"未找到{start_month}至{end_month}的货币供应量数据",
                        extra={'connection_id': 'MONETARY-QUERY'}
                    )
                    return pd.DataFrame()
                    
                df = pd.DataFrame(rows, columns=[
                    'stat_month', 'm2', 'm2_yoy', 'm1', 'm1_yoy',
                    'm0', 'm0_yoy', 'cd', 'cd_yoy', 'qm', 'qm_yoy',
                    'ftd', 'ftd_yoy', 'sd', 'sd_yoy'
                ])
                
                self.logger.info(f"成功获取{len(df)}条货币供应量数据")
                return df
                
        except Exception as e:
            self.logger.error(f"获取货币供应量数据失败: {str(e)}")
            raise

    async def del_stock_data(self, name):
        self.logger.info(f"开始删除数据库表{name}...")
        self.logger.debug(f"调用了del方法")
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
                self.logger.warning(f"表 {name}已删除", extra={'connection_id': id(conn)})

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
            self.logger.info(f"Connection pool status: {status}")
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
                    self.logger.warning("未找到全球市场资金分布数据")
                    return pd.DataFrame()
                
                return pd.DataFrame(rows, columns=['type', 'name', 'currency', 'assets', 'year'])
                
        except Exception as e:
            self.logger.error(f"获取全球市场资金分布数据失败: {str(e)}")
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
            self.logger.error(f"获取distinct值失败: {str(e)}")
            return {'types': [], 'years': []}
