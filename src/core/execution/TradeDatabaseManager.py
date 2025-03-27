from core.data.database import DatabaseManager
from datetime import datetime
import logging
from typing import List, Dict, Optional

class TradeDatabaseManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self._init_trade_tables()

    def _init_trade_tables(self):
        """Initialize trade-related tables"""
        try:
            with self.connection.cursor() as cursor:
                # Create Orders table
                cursor.execute("""
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
                cursor.execute("""
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
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS TradeHistory (
                        trade_id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        trade_time TIMESTAMP NOT NULL,
                        trade_price NUMERIC NOT NULL,
                        trade_quantity NUMERIC NOT NULL,
                        trade_type VARCHAR(10) NOT NULL
                    );
                """)
                
                self.connection.commit()
                self.logger.info("Trade tables initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize trade tables: {str(e)}")
            self.connection.rollback()
            raise

    def save_order(self, order: Dict) -> int:
        """Save an order to database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Orders 
                    (symbol, order_type, quantity, price, status, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING order_id
                """, (
                    order['symbol'],
                    order['order_type'],
                    order['quantity'],
                    order['price'],
                    order['status'],
                    datetime.now()
                ))
                order_id = cursor.fetchone()[0]
                self.connection.commit()
                return order_id
        except Exception as e:
            self.logger.error(f"Failed to save order: {str(e)}")
            self.connection.rollback()
            raise

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE Orders
                    SET status = %s, update_time = %s
                    WHERE order_id = %s
                """, (status, datetime.now(), order_id))
                self.connection.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update order status: {str(e)}")
            self.connection.rollback()
            raise

    def log_execution(self, execution: Dict) -> int:
        """Log execution result"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Executions
                    (order_id, exec_price, exec_quantity, exec_time, status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING execution_id
                """, (
                    execution['order_id'],
                    execution['exec_price'],
                    execution['exec_quantity'],
                    datetime.now(),
                    execution['status']
                ))
                execution_id = cursor.fetchone()[0]
                self.connection.commit()
                return execution_id
        except Exception as e:
            self.logger.error(f"Failed to log execution: {str(e)}")
            self.connection.rollback()
            raise

    def record_trade(self, trade: Dict) -> int:
        """Record a trade"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO TradeHistory
                    (symbol, trade_time, trade_price, trade_quantity, trade_type)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING trade_id
                """, (
                    trade['symbol'],
                    datetime.now(),
                    trade['trade_price'],
                    trade['trade_quantity'],
                    trade['trade_type']
                ))
                trade_id = cursor.fetchone()[0]
                self.connection.commit()
                return trade_id
        except Exception as e:
            self.logger.error(f"Failed to record trade: {str(e)}")
            self.connection.rollback()
            raise

    def query_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Query orders"""
        try:
            with self.connection.cursor() as cursor:
                if symbol:
                    cursor.execute("""
                        SELECT * FROM Orders WHERE symbol = %s
                    """, (symbol,))
                else:
                    cursor.execute("SELECT * FROM Orders")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to query orders: {str(e)}")
            raise

    def query_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """Query trade history"""
        try:
            with self.connection.cursor() as cursor:
                if symbol:
                    cursor.execute("""
                        SELECT * FROM TradeHistory WHERE symbol = %s
                    """, (symbol,))
                else:
                    cursor.execute("SELECT * FROM TradeHistory")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to query trades: {str(e)}")
            raise
