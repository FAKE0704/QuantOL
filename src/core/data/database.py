from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
import os

Base = declarative_base()

class StockData(Base):
    """股票数据表"""
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(16), index=True)  # 股票代码
    date = Column(DateTime)  # 日期时间
    open = Column(Float)  # 开盘价
    high = Column(Float)  # 最高价
    low = Column(Float)  # 最低价
    close = Column(Float)  # 收盘价
    volume = Column(Float)  # 成交量
    frequency = Column(String(8))  # 数据频率

class DatabaseManager:
    """数据库管理类"""
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/quant')
        self.engine = create_engine(self.db_url, pool_size=5, max_overflow=10)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """初始化数据库"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
        
    def save_stock_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存股票数据"""
        session = self.get_session()
        try:
            records = data.reset_index().rename(columns={
                'date': 'Date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            records['symbol'] = symbol
            records['frequency'] = frequency
            
            session.bulk_insert_mappings(StockData, records.to_dict('records'))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"保存数据失败: {str(e)}")
            return False
        finally:
            session.close()

    def load_stock_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """从数据库加载股票数据"""
        session = self.get_session()
        try:
            query = session.query(StockData).filter(
                StockData.symbol == symbol,
                StockData.frequency == frequency,
                StockData.date >= start_date,
                StockData.date <= end_date
            ).order_by(StockData.date)
            
            data = pd.read_sql(query.statement, session.bind)
            if not data.empty:
                data = data.set_index('date').rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
            return data
        except Exception as e:
            print(f"加载数据失败: {str(e)}")
            return pd.DataFrame()
        finally:
            session.close()
