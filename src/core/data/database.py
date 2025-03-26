import psycopg2
import logging
from typing import Optional
import pandas as pd


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

    def init_db(self):
        """Initialize database and tables"""
        try:
            import threading
            from functools import wraps
            
            class TimeoutError(Exception):
                pass
            
            def with_timeout(seconds):
                def decorator(func):
                    @wraps(func)
                    def wrapper(*args, **kwargs):
                        result = None
                        exception = None
                        
                        def target():
                            nonlocal result, exception
                            try:
                                result = func(*args, **kwargs)
                            except Exception as e:
                                exception = e
                        
                        thread = threading.Thread(target=target)
                        thread.start()
                        thread.join(seconds)
                        
                        if thread.is_alive():
                            raise TimeoutError("Operation timed out")
                        if exception:
                            raise exception
                        return result
                    return wrapper
                return decorator
            
            @with_timeout(30)
            def init_tables(connection):
                with connection.cursor() as cursor:
                    # Check if table is locked
                    cursor.execute("""
                        SELECT relation::regclass, mode, granted 
                        FROM pg_locks 
                        WHERE relation = 'StockData'::regclass
                    """)
                    locks = cursor.fetchall()
                    
                    if locks and any(not lock[2] for lock in locks):
                        raise Exception("Table is locked by other process")
                        
                    # Drop existing table -- 尝试获取表的排他锁（若失败则立即报错）
                    # cursor.execute("LOCK TABLE StockData IN ACCESS EXCLUSIVE MODE NOWAIT")
                    # cursor.execute("DROP TABLE IF EXISTS StockData CASCADE")
                    
                    # Create new table with updated schema
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
                        """
                    )
                connection.commit()
                return True
            
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
            
            # Create tables with timeout and lock handling
            self.logger.info("Initializing database tables")
            try:
                init_tables(self.connection)
                self.logger.info("Database tables initialized successfully")
            except TimeoutError:
                self.logger.error("Database initialization timed out after 30 seconds")
                raise
            except Exception as e:
                self.logger.error(f"Database initialization failed: {str(e)}")
                raise
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise

    def save_stock_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """Save stock data to database"""
        try:
            if data.empty:
                self.logger.warning("Empty data received, nothing to save")
                return False
            
            self.logger.info(f"Saving {len(data)} rows for {symbol}")
            
            # Verify and prepare data
            # Map baostock source columns to database columns
            column_mapping = {
                'date': 'date',
                'time': 'time', # alternative amount column
                'code': 'code',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'amount': 'amount',  # alternative amount column
                'adjustflag': 'adjustflag'
            }
            
            # Set default values for optional columns
            default_values = {
                'adjustflag': 'none',
            }
            
            # Convert column names to lowercase for case-insensitive matching
            data.columns = data.columns.str.lower()
            print(data.columns)
            # Add missing columns with default values
            for col, default in default_values.items():
                if col not in data.columns:
                    data[col] = default
                    
            # Rename columns to match database schema
            # Use the first available source column for each target column
            for target_col, source_cols in column_mapping.items():
                if isinstance(source_cols, str):
                    source_cols = [source_cols]
                    
                for source_col in source_cols:
                    if source_col in data.columns:
                        data.rename(columns={source_col: target_col}, inplace=True)
                        break
                        
            # Ensure all required columns are present
            required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag', 'time']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                self.logger.error(f"Data columns: {data.columns.tolist()}")
                raise ValueError(f"Missing required columns after mapping: {missing_columns}")
            
            # 添加frequency数据
            data['frequency'] = frequency
            
            records = data[['date', 'time','frequency', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag']].to_records(index=False)
            
            records = [tuple(record) for record in records]
            
            query = """
                INSERT INTO StockData 
                (date, time,frequency, code, open, high, low, close, volume, amount, adjustflag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            
            with self.connection.cursor() as cursor:
                cursor.executemany(query, records)
            self.connection.commit()
            
            self.logger.info(f"Successfully saved {len(records)} rows for {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save stock data: {str(e)}")
            self.connection.rollback()
            raise
        
    def get_date_range(self, symbol: str) -> tuple:
        """Get the earliest and latest date for a symbol"""
        try:
            if not self.connection or self.connection.closed:
                self.connection = psycopg2.connect(**self.connection_config)
                
            query = """
                SELECT MIN(date), MAX(date)
                FROM StockData
                WHERE code = %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (symbol,))
                min_date, max_date = cursor.fetchone()
                
                if not min_date or not max_date:
                    return None, None
                    
                return min_date, max_date
                
        except Exception as e:
            self.logger.error(f"Failed to get date range for {symbol}: {str(e)}")
            raise

    def check_data_completeness(self, symbol: str, start_date: str, end_date: str) -> list:
        """Check if data exists for given date range and return missing intervals"""
        try:
            if not self.connection or self.connection.closed:
                self.connection = psycopg2.connect(**self.connection_config)
            
            self.logger.info(f"Checking data completeness for {symbol} from {start_date} to {end_date}")
                
            # Convert input dates to datetime objects
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date()
            
            # Get existing dates
            query = """
                SELECT DISTINCT date 
                FROM StockData
                WHERE code = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (symbol, start_date, end_date))
                existing_dates = [pd.to_datetime(row[0]).date() for row in cursor.fetchall()]
                
            if not existing_dates:
                self.logger.info(f"No data found for {symbol} in specified date range")
                start_date = start_date.strftime("%Y%m%d")
                end_date = end_date.strftime("%Y%m%d")
                return [(start_date, end_date)]
                
            # Find missing date ranges
            missing_ranges = []
            current_date = start_dt
            
            # Check if there are any existing dates
            if not existing_dates:
                missing_ranges.append((start_date, end_date))
                return missing_ranges
                
            # Check for missing dates before the first existing date
            first_existing = existing_dates[0]
            if current_date < first_existing:
                missing_start = current_date.strftime('%Y-%m-%d')
                missing_end = (first_existing - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                missing_ranges.append((missing_start, missing_end))
                self.logger.info(f"Found missing data range before first existing: {missing_start} to {missing_end}")
                current_date = first_existing
            
            # Check for gaps between existing dates
            for i in range(1, len(existing_dates)):
                prev_date = existing_dates[i-1]
                curr_date = existing_dates[i]
                expected_next = prev_date + pd.Timedelta(days=1)
                
                if curr_date > expected_next:
                    missing_start = expected_next.strftime('%Y-%m-%d')
                    missing_end = (curr_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                    missing_ranges.append((missing_start, missing_end))
                    self.logger.info(f"Found missing data range between existing: {missing_start} to {missing_end}")
            
            # Check for missing dates after the last existing date
            last_existing = existing_dates[-1]
            if last_existing < end_dt:
                missing_start = (last_existing + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                missing_end = end_dt.strftime('%Y-%m-%d')
                missing_ranges.append((missing_start, missing_end))
                self.logger.info(f"Found missing data range after last existing: {missing_start} to {missing_end}")
                
            return missing_ranges
            
        except Exception as e:
            self.logger.error(f"Failed to check data completeness: {str(e)}")
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
                    await data_source.load_data(symbol, range_start, range_end)
            
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
