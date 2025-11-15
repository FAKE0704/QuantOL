import aiosqlite
import pandas as pd
import chinese_calendar as calendar
from datetime import datetime, date, time
from typing import Any, Optional, Dict, List
import os
import chinese_calendar as calendar
from src.support.log.logger import logger
from .database_adapter import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""

    def __init__(self, db_path: str = "./data/quantdb.sqlite"):
        self.db_path = db_path
        self.pool: Optional[aiosqlite.Connection] = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        if self._initialized:
            return

        try:
            # 确保数据目录存在
            data_dir = os.path.dirname(self.db_path)
            if data_dir:
                os.makedirs(data_dir, exist_ok=True)
                logger.info(f"确保数据目录存在: {data_dir}")

            # 创建连接
            logger.info(f"正在创建SQLite数据库连接: {self.db_path}")
            self.pool = await aiosqlite.connect(self.db_path)

            # 启用外键约束
            await self.pool.execute("PRAGMA foreign_keys = ON")

            # 性能优化设置
            await self.pool.execute("PRAGMA journal_mode = WAL")
            await self.pool.execute("PRAGMA synchronous = NORMAL")
            await self.pool.execute("PRAGMA cache_size = 10000")
            await self.pool.execute("PRAGMA temp_store = MEMORY")

            logger.info("SQLite连接创建成功，开始初始化表结构...")

            # 创建表结构
            await self._init_db_tables()
            self._initialized = True

            logger.info(f"SQLite数据库初始化成功: {self.db_path}")

        except Exception as e:
            logger.error(f"SQLite数据库初始化失败: {str(e)}")
            # 打印详细的堆栈信息
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise

    async def create_connection_pool(self) -> aiosqlite.Connection:
        """创建连接池（SQLite使用单连接）"""
        if not self.pool:
            await self.initialize()
        return self.pool

    async def execute_query(self, query: str, *args) -> Any:
        """执行查询"""
        if not self.pool:
            await self.initialize()

        try:
            # 转换PostgreSQL语法到SQLite语法
            sqlite_query = self._convert_query_syntax(query)

            if query.strip().upper().startswith('SELECT'):
                cursor = await self.pool.execute(sqlite_query, parameters=args if args else ())
                rows = await cursor.fetchall()
                # 获取列名
                columns = [description[0] for description in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in rows]
            else:
                await self.pool.execute(sqlite_query, parameters=args if args else ())
                return None

        except Exception as e:
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
        """关闭连接"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False

    async def _init_db_tables(self):
        """初始化表结构"""
        logger.info("开始SQLite表结构初始化...")

        try:
            # 逐个创建表，以便准确定位问题
            logger.debug("开始创建StockData表...")
            await self.pool.execute(
                "CREATE TABLE IF NOT EXISTS StockData ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "code TEXT NOT NULL, "
                "date TEXT NOT NULL, "
                "time TEXT NOT NULL, "
                "open REAL NOT NULL, "
                "high REAL NOT NULL, "
                "low REAL NOT NULL, "
                "close REAL NOT NULL, "
                "volume INTEGER NOT NULL, "
                "amount REAL, "
                "adjustflag TEXT, "
                "frequency TEXT NOT NULL, "
                "UNIQUE (code, date, time, frequency)"
                ");"
            )
            logger.debug("StockData表创建成功")

            logger.debug("开始创建StockInfo表...")
            await self.pool.execute(
                "CREATE TABLE IF NOT EXISTS StockInfo ("
                "code TEXT PRIMARY KEY, "
                "code_name TEXT NOT NULL, "
                "ipoDate TEXT NOT NULL, "
                "outDate TEXT, "
                "type TEXT, "
                "status TEXT"
                ");"
            )
            logger.debug("StockInfo表创建成功")

            logger.debug("开始创建PoliticalEvents表...")
            await self.pool.execute(
                "CREATE TABLE IF NOT EXISTS PoliticalEvents ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_date TEXT NOT NULL, "
                "country TEXT NOT NULL, "
                "policy_type TEXT NOT NULL, "
                "impact_score REAL NOT NULL, "
                "raw_content TEXT NOT NULL, "
                "processed INTEGER DEFAULT 0, "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
                ");"
            )
            logger.debug("PoliticalEvents表创建成功")

            logger.debug("开始创建MoneySupplyData表...")
            await self.pool.execute(
                "CREATE TABLE IF NOT EXISTS MoneySupplyData ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "stat_month TEXT NOT NULL, "
                "m2 REAL NOT NULL, "
                "m2_yoy REAL NOT NULL, "
                "m1 REAL NOT NULL, "
                "m1_yoy REAL NOT NULL, "
                "m0 REAL NOT NULL, "
                "m0_yoy REAL NOT NULL, "
                "cd REAL NOT NULL, "
                "cd_yoy REAL NOT NULL, "
                "qm REAL NOT NULL, "
                "qm_yoy REAL NOT NULL, "
                "ftd REAL NOT NULL, "
                "ftd_yoy REAL NOT NULL, "
                "sd REAL NOT NULL, "
                "sd_yoy REAL NOT NULL, "
                "UNIQUE (stat_month)"
                ");"
            )
            logger.debug("MoneySupplyData表创建成功")

            logger.debug("SQLite表结构初始化完成")

        except Exception as e:
            logger.error(f"SQLite表结构初始化失败: {str(e)}")
            # 打印详细的堆栈信息
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise

    async def save_stock_info(self, code: str, code_name: str, ipo_date: str,
                             stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息到StockInfo表"""
        try:
            await self.pool.execute("""
                INSERT OR REPLACE INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, code, code_name, ipo_date, out_date, stock_type, status)

            logger.info(f"成功保存股票基本信息: {code}")
            return True
        except Exception as e:
            logger.error(f"保存股票信息失败: {str(e)}")
            raise

    async def check_data_completeness(self, symbol: str, start_date: date, end_date: date, frequency: str) -> list:
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

            # 获取数据库中已有日期
            query = """
                SELECT DISTINCT date
                FROM StockData
                WHERE code = ? AND frequency = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            cursor = await self.pool.execute(query, parameters=(symbol, frequency, start_dt, end_dt))
            rows = await cursor.fetchall()
            logger.info(f"从数据库获取 {start_dt}-{end_dt} for {symbol}")

            existing_dates = {pd.to_datetime(row[0]).date() for row in rows}

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
                WHERE code = ?
                AND date BETWEEN ? AND ?
                AND frequency = ?
                ORDER BY date
            """

            cursor = await self.pool.execute(query, parameters=(symbol, start_dt, end_dt, frequency))
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
        """获取所有股票信息"""
        try:
            logger.debug("检查数据是否最新")
            if await self._is_stock_info_up_to_date():
                cursor = await self.pool.execute("SELECT * FROM StockInfo")
                rows = await cursor.fetchall()
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
            await self.initialize()

        for attempt in range(max_retries):
            try:
                logger.debug(f"检查StockInfo表状态(尝试{attempt+1}/{max_retries})")

                # 检查表是否存在
                cursor = await self.pool.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='StockInfo'
                """)
                table_exists = await cursor.fetchone()

                if not table_exists:
                    logger.warning("表StockInfo不存在")
                    return False

                # 检查最新IPO日期
                cursor = await self.pool.execute("""
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

            # 清空现有数据
            logger.debug("Truncating StockInfo table")
            await self.pool.execute("DELETE FROM StockInfo")

            # 执行批量插入
            logger.debug(f"Inserting {len(valid_data)} rows into StockInfo")
            await self.pool.executemany("""
                INSERT INTO StockInfo (code, code_name, ipoDate, outDate, type, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, parameters=valid_data)

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
                ipo_date.strftime('%Y-%m-%d'),  # 转换为字符串
                out_date.strftime('%Y-%m-%d') if out_date else None,
                str(row['type']),
                str(row['status'])
            )
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)} - 行数据: {row.to_dict()}")
            raise

    async def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        try:
            cursor = await self.pool.execute("""
                SELECT code_name, ipoDate, outDate, type, status
                FROM StockInfo
                WHERE code = ?
            """, parameters=(code,))

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
        try:
            cursor = await self.pool.execute("""
                SELECT code_name FROM StockInfo WHERE code = ?
            """, parameters=(code,))
            row = await cursor.fetchone()
            return row[0] if row else ""
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

            await self.pool.executemany("""
                INSERT OR REPLACE INTO StockData (
                    code, date, time, open, high, low, close,
                    volume, amount, adjustflag, frequency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, parameters=insert_data)

            # 验证数据是否成功插入
            logger.info(f"成功保存{symbol}的{frequency}频率数据，共{len(insert_data)}条记录")

            # 简单验证：查询刚插入的记录数
            verify_cursor = await self.pool.execute(
                "SELECT COUNT(*) FROM StockData WHERE code = ? AND frequency = ?",
                parameters=(symbol, frequency)
            )
            count = await verify_cursor.fetchone()
            logger.info(f"数据库中{symbol}的{frequency}频率记录总数: {count[0] if count else 0}")

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

            await self.pool.executemany("""
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
        try:
            cursor = await self.pool.execute("""
                SELECT * FROM MoneySupplyData
                WHERE stat_month BETWEEN ? AND ?
                ORDER BY stat_month
            """, start_month, end_month)

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
            "connected": self.pool is not None
        }