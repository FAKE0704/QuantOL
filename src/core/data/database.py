import psycopg2
import logging
from typing import Optional
import pandas as pd
import chinese_calendar as calendar
from .stock import Stock


class DatabaseManager:
    def __init__(self, host='113.45.40.20', port=8080, dbname='quantdb', 
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

    def _get_connection(self):
        """获取数据库连接，自动初始化连接"""
        if not self.connection or self.connection.closed:
            if not self._initialized:
                self._init_db()
                self._initialized = True
            self.connection = psycopg2.connect(**self.connection_config)

        # print(self.connection) #debug    
        return self.connection

    def _init_db(self):
        """Initialize database and tables"""
        try:
            # Check if database exists
            self.logger.info("Checking if database 'quantdb' exists")
            admin_conn = psycopg2.connect(**self.admin_config)
            admin_conn.autocommit = True
            with admin_conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname='quantdb'")
                exists = cursor.fetchone()
                
                if not exists:
                    self.logger.info("Database 'quantdb' does not exist, creating it")
                    cursor.execute("CREATE DATABASE quantdb")
                    self.logger.info("Database 'quantdb' created successfully")
            
            # Connect to target database
            self.connection = psycopg2.connect(**self.connection_config)
            
            # Create tables
            self.logger.info("Initializing database tables")
            self._init_tables(self.connection)
            self.logger.info("Database tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise

    def _init_tables(self, connection):
        """Initialize database tables"""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DROP TABLE StockData
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS StockData (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    time TIME,
                    open NUMERIC NOT NULL,
                    high NUMERIC NOT NULL,
                    low NUMERIC NOT NULL,
                    close NUMERIC NOT NULL,
                    volume NUMERIC NOT NULL,
                    amount NUMERIC,
                    adjustflag VARCHAR(10),
                    frequency VARCHAR(10) NOT NULL
                );

                CREATE TABLE IF NOT EXISTS StockInfo (
                    code VARCHAR(20) PRIMARY KEY,
                    code_name VARCHAR(50) NOT NULL,
                    ipoDate DATE NOT NULL,
                    outDate DATE,
                    type VARCHAR(20) CHECK(type IN ('A股','B股','指数','ETF')),
                    status VARCHAR(10) CHECK(status IN ('上市','退市','停牌'))
                );
                """
            )
        connection.commit()

    def save_stock_info(self, code: str, code_name: str, ipo_date: str, 
                      stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息"""
        try:
            query = """
                INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    code_name = EXCLUDED.code_name,
                    ipoDate = EXCLUDED.ipoDate,
                    outDate = EXCLUDED.outDate,
                    type = EXCLUDED.type,
                    status = EXCLUDED.status
            """
            with self._get_connection().cursor() as cursor:
                cursor.execute(query, (
                    code, 
                    code_name,
                    ipo_date,
                    out_date,
                    stock_type,
                    status
                ))
            self.connection.commit()
            self.logger.info(f"成功保存股票基本信息: {code}")
            return True
        except Exception as e:
            self.logger.error(f"保存股票信息失败: {str(e)}")
            self.connection.rollback()
            raise

    def check_data_completeness(self, symbol: str, start_date: str, end_date: str) -> list:
        """检查指定日期范围内的数据完整性，返回缺失日期区间，自动排除节假日"""
        try:
            self.logger.info(f"Checking data completeness for {symbol} from {start_date} to {end_date}")
            
            # 转换输入日期
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date()
            
            # 使用上下文管理器获取连接
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取数据库中已有日期
                    query = """
                        SELECT DISTINCT date 
                        FROM StockData
                        WHERE code = %s AND date BETWEEN %s AND %s
                        ORDER BY date
                    """
                    cursor.execute(query, (symbol, start_date, end_date))
                    existing_dates = set(pd.to_datetime(row[0]).date() for row in cursor.fetchall())
                    
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
                            missing_ranges.append((range_start.strftime('%Y-%m-%d'), 
                                                 prev_date.strftime('%Y-%m-%d')))
                            range_start = current_date
                        prev_date = current_date
                    
                    # 添加最后一个区间
                    missing_ranges.append((range_start.strftime('%Y-%m-%d'), 
                                         prev_date.strftime('%Y-%m-%d')))
                
                self.logger.info(f"Found {len(missing_ranges)} missing data ranges for {symbol}")
                return missing_ranges
                
        except Exception as e:
            self.logger.error(f"检查数据完整性失败: {str(e)}")
            raise

    async def load_stock_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """Load stock data from database, fetch missing data from Baostock if needed"""
        try:
            if not self.connection or self.connection.closed:
                self.connection = psycopg2.connect(**self.connection_config)
                
            self.logger.info(f"Loading stock data for {symbol} from {start_date} to {end_date}")
            
            # Check data completeness
            missing_ranges = self.check_data_completeness(symbol, start_date, end_date)
            
            # Fetch missing data ranges from Baostock
            if missing_ranges:
                self.logger.info(f"Fetching missing data ranges for {symbol}")
                from .baostock_source import BaostockDataSource
                data_source = BaostockDataSource(frequency)
                for range_start, range_end in missing_ranges:
                    self.logger.info(f"Fetching data from {range_start} to {range_end}")
                    await data_source.load_data(symbol, range_start, range_end, frequency)
            
            # Load complete data from database
            query = """
                SELECT date, time, code, open, high, low, close, volume, amount, adjustflag
                FROM StockData
                WHERE code = %s
                AND date BETWEEN %s AND %s
                AND frequency = %s
                ORDER BY date
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (symbol, start_date, end_date, frequency))
                rows = cursor.fetchall()
                
                if not rows:
                    self.logger.warning(f"No data found for {symbol} in specified date range")
                    return pd.DataFrame()
                
                df = pd.DataFrame(rows, columns=['date', 'time', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag'])
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

    def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票信息
        1. 若数据库表StockInfo是最新，则返回StockInfo数据库表的所有数据
        2. 若数据库表StockInfo不是最新，则调用baostock_source.py的get_all_stocks方法更新数据
        Returns:
            包含所有股票信息的DataFrame
        """
        try:
            # 检查数据是否最新
            print("####debug2####")
            if self._is_stock_info_up_to_date():
                print("####debug2.5####")
                query = "SELECT * FROM StockInfo"
                with self._get_connection().cursor() as cursor:
                    cursor.execute(query)
                    columns = [desc[0] for desc in cursor.description]
                    data = cursor.fetchall()
                    return pd.DataFrame(data, columns=columns)
            else:
                # 调用baostock_source更新数据
                from .baostock_source import BaostockDataSource
                print("####debug3####")
                data_source = BaostockDataSource()
                df = data_source._get_all_stocks()
                # 将数据保存到数据库
                self._update_stock_info(df)
                return df
        except Exception as e:
            self.logger.error(f"获取所有股票信息失败: {str(e)}")
            raise

    def _is_stock_info_up_to_date(self) -> bool:
        """检查StockInfo表是否最新"""
        try:
            # 耗时巨久。。。
            query = """
                SELECT MAX(ipoDate) as latest_ipo 
                FROM StockInfo
            """
            print("####debug2.1####")
            with self._get_connection().cursor() as cursor:
                print("####debug2.2####")
                cursor.execute(query) 
                latest_ipo = cursor.fetchone()[0]
                print("####debug2.3####")
                # 如果最新IPO日期在最近30天内，则认为数据是最新的
                return (pd.Timestamp.now() - pd.Timestamp(latest_ipo)) < pd.Timedelta(days=30)
        except Exception as e:
            self.logger.error(f"检查StockInfo表状态失败: {str(e)}")
            return False

    def _update_stock_info(self, df: pd.DataFrame) -> None:
        """更新StockInfo表数据"""
        try:
            with self._get_connection().cursor() as cursor:
                # 清空现有数据
                cursor.execute("TRUNCATE TABLE StockInfo")
                
                # 插入新数据
                for _, row in df.iterrows():
                    cursor.execute("""
                        INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        row['code'],
                        row['code_name'],
                        row['ipoDate'],
                        row.get('outDate'),
                        row['type'],
                        row['status']
                    ))
            self.connection.commit()
            self.logger.info("成功更新StockInfo表数据")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"更新StockInfo表数据失败: {str(e)}")
            raise

    def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        try:
            query = """
                SELECT code_name, ipoDate, outDate, type, status 
                FROM StockInfo 
                WHERE code = %s
            """
            with self._get_connection().cursor() as cursor:
                cursor.execute(query, (code,))
                result = cursor.fetchone()
                
                if not result:
                    return {}
                    
                return {
                    "code_name": result[0],
                    "ipo_date": result[1].strftime("%Y-%m-%d"),
                    "out_date": result[2].strftime("%Y-%m-%d") if result[2] else None,
                    "type": result[3],
                    "status": result[4]
                }
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {str(e)}")
            raise


    def get_stock_name(self, code: str) -> str:
        """根据股票代码获取名称"""
        try:
            query = "SELECT code_name FROM StockInfo WHERE code = %s"
            with self._get_connection().cursor() as cursor:
                cursor.execute(query, (code,))
                result = cursor.fetchone()
                return result[0] if result else ""
        except Exception as e:
            self.logger.error(f"获取股票名称失败: {str(e)}")
            raise
