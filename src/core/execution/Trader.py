from datetime import datetime
from decimal import Decimal
from ..data.database import DatabaseManager
from typing import Dict, Literal, Optional
import pandas as pd
# from THS.THSTrader import THSTrader
from src.event_bus.event_types import FillEvent

from enum import Enum, auto
from threading import Lock

class OrderDirection(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = auto()      # 订单已创建但未处理
    ACCEPTED = auto()     # 订单已通过风险检查
    PARTIALLY_FILLED = auto()  # 订单部分成交
    FILLED = auto()       # 订单完全成交
    CANCELLED = auto()    # 订单已取消
    REJECTED = auto()     # 订单被拒绝

class TradeOrderManager:
    """交易订单管理类，负责订单的创建、修改、取消"""
    
    def __init__(self, db_manager: DatabaseManager, software_dir=None, commission_rate=0.0003):
        self.db_manager = db_manager
        self.trader = None
        self.commission_rate = commission_rate
        self.pending_orders = []
        self.executed_trades = []
        self._status_lock = Lock()  # 状态变更锁
        self._db_queue = []  # 数据库操作队列
        self._db_flush_lock = Lock()  # 队列刷新锁

    async def create_order(
        self,
        strategy_id: str,
        symbol: str,
        direction: OrderDirection,
        quantity: Decimal,
        order_type: OrderType,
        price: Optional[Decimal] = None,
        time_in_force: str = "DAY"
    ) -> Dict:
        """参数说明：
        - strategy_id: 策略唯一标识
        - symbol: 交易标的代码
        - direction: 买卖方向
        - quantity: 数量(必须为正数)
        - order_type: 订单类型
        - price: 限价单价格
        - time_in_force: 订单有效期
        """
        order = {
            'strategy_id': strategy_id,
            'symbol': symbol,
            'direction': direction.value,
            'order_type': order_type.value,
            'quantity': float(quantity),
            'price': float(price) if price else None,
            'time_in_force': time_in_force,
            'status': OrderStatus.PENDING.name
        }
        order_id = await self.db_manager.save_order(order)
        self.pending_orders.append(order)
        return await self.get_order(order_id)

    def update_order_status(self, order_id, new_status: OrderStatus):
        """更新订单状态"""
        with self._status_lock:
            order = self.get_order(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            current_status = OrderStatus[order['status']]
            valid_transitions = {
                OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.REJECTED],
                OrderStatus.ACCEPTED: [OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED],
                OrderStatus.PARTIALLY_FILLED: [OrderStatus.FILLED, OrderStatus.CANCELLED]
            }
            
            if new_status not in valid_transitions.get(current_status, []):
                raise ValueError(f"Invalid status transition from {current_status} to {new_status}")
            
            order['status'] = new_status.name
            with self._db_flush_lock:
                self._db_queue.append(('update_status', order_id, new_status.name))
            return order

    def flush_db_queue(self):
        """批量执行数据库操作"""
        with self._db_flush_lock:
            if not self._db_queue:
                return
            
            batch_updates = []
            for op in self._db_queue:
                if op[0] == 'update_status':
                    batch_updates.append((op[1], op[2]))
            
            if batch_updates:
                self.db_manager.batch_update_order_status(batch_updates)
            
            self._db_queue = []

    def process_orders(self, market_data: pd.DataFrame):
        """处理等待中的订单"""
        executed_trades = []
        with self._db_flush_lock:
            for order in self.pending_orders:
                trade = self._execute_order(order, market_data)
                if trade:
                    executed_trades.append(trade)
                    self._db_queue.append(('update_status', order['order_id'], OrderStatus.FILLED.name))
            
            self.executed_trades.extend(executed_trades)
            self.pending_orders = []
            return executed_trades

    def _execute_order(self, order: Dict, market_data: pd.DataFrame) -> Optional[Dict]:
        """执行单个订单"""
        symbol = order['symbol']
        quantity = order['quantity']
        order_type = order['order_type']
        
        if order_type == 'market':
            price = market_data.loc[market_data['symbol'] == symbol, 'close'].values[0]
        else:
            price = order.get('price')
            if price is None:
                return None
        
        cost = price * quantity
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        trade = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'commission': commission,
            'cost': total_cost,
            'timestamp': market_data['date'].iloc[0]
        }
        return trade
        
    def modify_order(self, order_id, quantity=None, price=None):
        """修改已有订单"""
        order = self.get_order(order_id)
        if quantity:
            order['quantity'] = quantity
        if price:
            order['price'] = price
        self.db_manager.update_order_status(order_id, order['status'])
        return self.get_order(order_id)
        
    def cancel_order(self, order_id):
        """取消订单"""
        self.db_manager.update_order_status(order_id, OrderStatus.CANCELLED.name)
        return self.get_order(order_id)
        
    async def get_order(self, order_id) -> Optional[Dict]:
        """获取指定订单
        返回:
            Optional[Dict]: 订单字典或None(如果订单不存在)
        """
        return await self.db_manager.query_orders(order_id)


class TradeExecutionEngine:
    """交易执行引擎类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def generate_order_instruction(self, order):
        instruction = {
            'symbol': order['symbol'],
            'action': 'buy' if order['order_type'] == 'market_buy' else 'sell',
            'quantity': order['quantity'],
            'price': order['price'],
            'status': OrderStatus.PENDING.name
        }
        return instruction
        
    def log_execution(self, instruction, status):
        execution = {
            'order_id': instruction.get('order_id'),
            'exec_price': instruction['price'],
            'exec_quantity': instruction['quantity'],
            'status': status
        }
        self.db_manager.log_execution(execution)
        return execution


class TradeRecorder:
    """交易记录类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def record_trade(self, execution):
        trade = {
            'symbol': execution['instruction']['symbol'],
            'trade_price': execution['instruction']['price'],
            'trade_quantity': execution['instruction']['quantity'],
            'trade_type': execution['instruction']['action']
        }
        self.db_manager.record_trade(trade)
        return trade
        
    def query_trades(self, symbol=None):
        return self.db_manager.query_trades(symbol)


from abc import ABC, abstractmethod

class BaseTrader(ABC):
    """交易执行基类"""
    @abstractmethod
    def execute_order(self, order_event) -> FillEvent:
        pass

class BacktestTrader(BaseTrader):
    """回测交易执行"""
    def __init__(self, commission_rate=0.0003):
        self.commission_rate = commission_rate
        
    def execute_order(self, order_event) -> FillEvent:
        fill_price = self._simulate_market_impact(order_event)
        return FillEvent(
            order_id=order_event.order_id,
            symbol=order_event.symbol,
            fill_price=fill_price,
            fill_quantity=order_event.quantity,
            commission=self._calculate_commission(order_event)
        )
        
    def _simulate_market_impact(self, order_event):
        return order_event.price * 1.0005
        
    def _calculate_commission(self, order_event):
        return abs(order_event.quantity) * order_event.price * self.commission_rate

class LiveTrader(BaseTrader):
    """实盘交易执行"""
    def __init__(self, api_config):
        self.api = None
        
    def execute_order(self, order_event) -> FillEvent:
        return FillEvent(
            order_id=order_event.order_id,
            symbol=order_event.symbol,
            fill_price=order_event.price,
            fill_quantity=order_event.quantity,
            commission=0
        )
