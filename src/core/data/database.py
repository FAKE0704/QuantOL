import asyncpg
import logging
from typing import Optional
import pandas as pd
import chinese_calendar as calendar
from .stock import Stock
import streamlit as st
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
import uuid
import time
import traceback

class DatabaseManager:
    def __init__(self, host='113.45.40.20', port='8080', dbname='quantdb', 
                 user='quant', password='quant123', admin_db='quantdb'):
        self.connection = None
        self._init_logger()
        self.connection_config = {
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
        self._initialized = False
        self.pool = None  # 异步连接池
        self.max_pool_size = 50  # 最大连接数
        self.query_timeout = 15  # 查询超时时间（秒）
        self.active_connections = {}
        self._conn_lock = asyncio.Lock()
        
    def _init_logger(self):
        """Initialize logger configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('database.log')
            ]
        )
        self.logger = logging.getLogger(__name__)


    async def initialize(self):
        """异步初始化整个模块"""
        await self._create_pool()
        await self._init_db_tables()
        self.initialized = True  # 添加状态标记

    async def _create_pool(self):
        """创建连接池"""
        if not self.pool:
            valid_config = {
                "database": self.connection_config["dbname"],  # 关键修改点
                "user": self.connection_config["user"],
                "password": self.connection_config["password"],
                "host": self.connection_config["host"],
                "port": self.connection_config.get("port",'5432')
            }
            self.pool = await asyncpg.create_pool(
                **valid_config,
                min_size=20,
                max_size=self.max_pool_size,
                command_timeout=self.query_timeout,
                max_inactive_connection_lifetime= 30, # 30秒不用就终止
                max_queries=10_000  # 防止单连接过度使用
            )

    async def _init_db_tables(self):
        """异步初始化表结构"""
        async with self.acquire_connection() as conn:
            async with conn.transaction():
                # debug
                # await conn.execute(
                #     """
                #     DROP TABLE StockData;
                #     """
                # )
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
                
                self.logger.info("数据库表结构初始化完成")

    

    

    async def save_stock_info(self, code: str, code_name: str, ipo_date: str, 
                      stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """异步保存股票基本信息到StockInfo表"""
        try:
            async with self.acquire_connection() as conn:
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

    async def check_data_completeness(self, symbol: str, start_date: str, end_date: str) -> list:
        """异步检查数据完整性"""
        if not self.pool:
            await self._create_pool()

        """检查指定日期范围内的数据完整性，返回缺失日期区间，自动排除节假日"""
        try:
            self.logger.info(f"Checking data completeness for {symbol} from {start_date} to {end_date}")
            
            # 转换输入日期
            start_dt = datetime.strptime(start_date, "%Y%m%d") # datetime.date()
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            # start_dt = pd.to_datetime(start_date).date() # datetime.date()
            # end_dt = pd.to_datetime(end_date).date()
            
            # 使用上下文管理器获取连接
            async with self.acquire_connection() as conn:
                # 获取数据库中已有日期
                query = """
                    SELECT DISTINCT date 
                    FROM StockData
                    WHERE code = $1 AND date BETWEEN $2 AND $3
                    ORDER BY date
                """
                rows = await conn.fetch(query, symbol, start_dt, end_dt)
                existing_dates = {pd.to_datetime(row["date"]).date() for row in rows}
                    
                # 生成理论交易日集合（排除节假日）
                all_dates = pd.date_range(start_dt, end_dt, freq='B')  # 工作日
                trading_dates = set(
                    date.date() for date in all_dates 
                    if not calendar.is_holiday(date.date())
                )
                
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
                            missing_ranges.append((range_start.strftime('%Y%m%d'), 
                                                 prev_date.strftime('%Y%m%d')))
                            range_start = current_date
                        prev_date = current_date
                    
                    # 添加最后一个区间
                    missing_ranges.append((range_start.strftime('%Y%m%d'), 
                                         prev_date.strftime('%Y%m%d')))
                
                self.logger.info(f"Found {len(missing_ranges)} missing data ranges for {symbol}")
                return missing_ranges
                
        except Exception as e:
            self.logger.error(f"检查数据完整性失败: {str(e)}")
            raise

    async def load_stock_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """Load stock data from database, fetch missing data from Baostock and save in database if needed"""
        try:
            self.logger.info(f"Loading stock data for {symbol} from {start_date} to {end_date}")
            
            # Check data completeness
            missing_ranges = await self.check_data_completeness(symbol, start_date, end_date)
            
            start_dt = datetime.strptime(start_date, "%Y%m%d") # datetime.date()
            end_dt = datetime.strptime(end_date, "%Y%m%d")

            # Fetch missing data ranges from Baostock
            if missing_ranges:
                self.logger.info(f"Fetching missing data ranges for {symbol}")  #bug:获取数据但没有存入数据库
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource(frequency)
                data = pd.DataFrame()
                for range_start, range_end in missing_ranges:
                    self.logger.info(f"Fetching data from {range_start} to {range_end}")
                    # st.write(symbol, range_start, range_end, frequency) # debug 
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
            
            async with self.acquire_connection() as conn:
                rows = await conn.fetch(query, symbol, start_dt, end_dt, frequency)
                
                
                if not rows:
                    self.logger.warning(f"No data found for {symbol} in specified date range")
                    return pd.DataFrame()
                data = [dict(row) for row in rows]
                df = pd.DataFrame(data, columns=['date', 'time', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag'])
                df['date'] = pd.to_datetime(df['date'])
                
                self.logger.info(f"Successfully loaded {len(df)} rows for {symbol}")
                return df
                
        except Exception as e:
            self.logger.error(f"Failed to load stock data: {str(e)}")
            raise

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
        try:
            # 检查数据是否最新
            if await self._is_stock_info_up_to_date():
                async with self.acquire_connection() as conn:
                    rows = await conn.fetch("SELECT * FROM StockInfo")
                    return pd.DataFrame(rows, columns=['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status'])
            else:
                # 调用baostock_source更新数据
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource()
                df = await data_source._get_all_stocks()
                # 将数据保存到数据库
                st.write(df) # debug
                await self._update_stock_info(df)
                return df
        except Exception as e:
            self.logger.error(f"获取所有股票信息失败: {str(e)}")
            raise

    async def _is_stock_info_up_to_date(self) -> bool:
        """异步检查StockInfo表是否最新"""
        try:
            async with self.acquire_connection() as conn:
                # 设置可重复读隔离级别
                latest_ipo = await conn.fetchval("""
                    SELECT MAX(ipoDate) FROM StockInfo
                """)
                # 如果最新IPO日期在最近30天内，则认为数据是最新的
                return (pd.Timestamp.now() - pd.Timestamp(latest_ipo)) < pd.Timedelta(days=30)
        except Exception as e:
            self.logger.error(f"检查StockInfo表状态失败: {str(e)}")
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
        
        # 先验证所有数据
        for idx, row in df.iterrows():
            try:
                validated_data = await self._validate_stock_info(row)
                valid_data.append(validated_data)
            except Exception as e:
                invalid_rows.append((idx, str(e)))
                self.logger.error(f"第{idx}行数据验证失败: {str(e)}")
        
        if not valid_data:
            self.logger.warning("没有有效数据可以插入")
            return 0, len(df)
            
        try:
            async with self.acquire_connection() as conn:
                async with conn.transaction():
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
            async with self.acquire_connection() as conn:
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
            async with self.acquire_connection() as conn:
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
        try:
            # 将DataFrame转换为适合插入的格式
            records = data.to_dict('records')
            insert_data = [
                (
                    symbol,
                    record['date'],
                    record['time'],
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

            async with self.acquire_connection() as conn:
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
                
            self.logger.info(f"成功保存{symbol}的{frequency}频率数据，共{len(insert_data)}条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"保存股票数据失败: {str(e)}")
            raise

    @asynccontextmanager
    async def acquire_connection(self):
        """获取数据库连接"""
        if not self.pool:
            await self._create_pool()
        conn = await self.pool.acquire()
        try:
            # 验证连接有效性
            if await conn.fetchval("SELECT 1") != 1:
                raise ConnectionResetError("连接已失效")
            yield conn
        finally:
            await self.pool.release(conn)  # 无条件释放，由连接池自动处理失效连接

    async def release_connection(self, conn):
        """释放并停止跟踪数据库连接"""
        await self.pool.release(conn)
        async with self._conn_lock:
            del self.active_connections[id(conn)]

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
