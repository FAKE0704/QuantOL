from datetime import datetime
from decimal import Decimal
from ..data.database import DatabaseManager
from typing import Dict, Literal, Optional
import pandas as pd
import uuid
# from THS.THSTrader import THSTrader
from event_bus.event_types import FillEvent, OrderEvent

from enum import Enum, auto
from threading import Lock
from abc import ABC, abstractmethod

class BaseTrader(ABC):
    """交易执行基类"""
    @abstractmethod
    def execute_order(self, order_event) -> FillEvent:
        pass

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
    
    def __init__(self, db_manager: DatabaseManager, trader: BaseTrader, software_dir=None):
        self.db_manager = db_manager
        self.trader = trader
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

    async def update_order_status(self, order_id, new_status: OrderStatus):
        """更新订单状态"""
        with self._status_lock:
            order = await self.get_order(order_id)
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

    async def process_orders(self, market_data: pd.DataFrame):
        """处理等待中的订单，使用注入的trader执行订单"""
        executed_trades = []
        with self._db_flush_lock:
            for order in self.pending_orders:
                # 将字典订单转换为OrderEvent
                order_event = self._convert_to_order_event(order, market_data)
                if order_event:
                    # 使用注入的trader执行订单
                    fill_event = self.trader.execute_order(order_event)
                    if fill_event:
                        trade = self._convert_fill_event_to_trade(fill_event, order)
                        executed_trades.append(trade)
                        self._db_queue.append(('update_status', order['order_id'], OrderStatus.FILLED.name))
            
            self.executed_trades.extend(executed_trades)
            self.pending_orders = []
            return executed_trades

    def _convert_to_order_event(self, order_dict: Dict, market_data: pd.DataFrame) -> Optional[OrderEvent]:
        """将字典订单转换为OrderEvent对象"""
        try:
            symbol = order_dict['symbol']
            
            # 确定成交价格
            if order_dict['order_type'].lower() == 'market':
                # 市价单：使用当前市场价格
                # 确保market_data是DataFrame且有正确的列
                if not isinstance(market_data, pd.DataFrame) or 'symbol' not in market_data.columns or 'close' not in market_data.columns:
                    return None
                
                symbol_data = market_data[market_data['symbol'] == symbol]
                if len(symbol_data) == 0:
                    return None
                
                price = symbol_data['close'].iloc[0]
            else:
                # 限价单：使用指定价格
                price = order_dict.get('price')
                if price is None:
                    return None
            
            return OrderEvent(
                strategy_id=order_dict['strategy_id'],
                symbol=symbol,
                direction=order_dict['direction'],
                price=float(price),
                quantity=int(order_dict['quantity']),
                order_type=order_dict['order_type'].upper(),
                order_id=order_dict.get('order_id', '')
            )
        except (KeyError, IndexError, ValueError, AttributeError) as e:
            print(f"Error converting order to OrderEvent: {e}")
            return None

    def _convert_fill_event_to_trade(self, fill_event: FillEvent, original_order: Dict) -> Dict:
        """将FillEvent转换为交易记录字典"""
        return {
            'symbol': fill_event.symbol,
            'quantity': fill_event.fill_quantity,
            'price': fill_event.fill_price,
            'order_type': original_order['order_type'],
            'commission': fill_event.commission,
            'cost': (fill_event.fill_price * fill_event.fill_quantity) + fill_event.commission,
            'timestamp': fill_event.timestamp,
            'order_id': fill_event.order_id
        }
        
    async def modify_order(self, order_id, quantity=None, price=None):
        """修改已有订单"""
        order = await self.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if quantity:
            order['quantity'] = quantity
        if price:
            order['price'] = price
        self.db_manager.update_order_status(order_id, order['status'])
        return await self.get_order(order_id)
        
    async def cancel_order(self, order_id):
        """取消订单"""
        order = await self.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        await self.db_manager.update_order_status(order_id, OrderStatus.CANCELLED.name)
        return await self.get_order(order_id)
        
    async def get_order(self, order_id) -> Optional[Dict]:
        """获取指定订单
        返回:
            Optional[Dict]: 订单字典或None(如果订单不存在)
        """
        orders = await self.db_manager.query_orders(order_id)
        if orders and len(orders) > 0:
            return orders[0]  # 返回第一个匹配的订单
        return None

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
        
    async def log_execution(self, instruction, status):
        execution = {
            'order_id': instruction.get('order_id'),
            'exec_price': instruction['price'],
            'exec_quantity': instruction['quantity'],
            'status': status
        }
        await self.db_manager.log_execution(execution)
        return execution


class TradeRecorder:
    """交易记录类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    async def record_trade(self, execution):
        trade = {
            'symbol': execution['instruction']['symbol'],
            'trade_price': execution['instruction']['price'],
            'trade_quantity': execution['instruction']['quantity'],
            'trade_type': execution['instruction']['action']
        }
        await self.db_manager.record_trade(trade)
        return trade
        
    async def query_trades(self, symbol: str = None):
        return await self.db_manager.query_trades(symbol)

class BacktestTrader(BaseTrader):
    """回测交易执行类，负责处理OrderEvent到FillEvent的转换"""
    def __init__(self, commission_rate=0.0003):
        self.commission_rate = commission_rate
        
    def execute_order(self, order_event: OrderEvent) -> FillEvent:
        """执行订单并返回成交事件
        
        Args:
            order_event: 订单事件对象
            
        Returns:
            FillEvent: 成交回报事件
        """
        # 生成订单ID（如果OrderEvent中没有order_id）
        order_id = order_event.order_id
        if not order_id:
            order_id = self._generate_order_id()
            
        fill_price = self._simulate_market_impact(order_event)
        commission = self._calculate_commission(order_event)
        
        return FillEvent(
            order_id=order_id,
            symbol=order_event.symbol,
            fill_price=fill_price,
            fill_quantity=order_event.quantity,
            commission=commission,
            timestamp=datetime.now()
        )
        
    def _simulate_market_impact(self, order_event: OrderEvent) -> float:
        """模拟市场冲击，返回成交价格"""
        # 简单模拟：市价单按当前价格成交，限价单按指定价格成交
        if order_event.order_type == "MARKET":
            # 市价单：添加微小滑点
            return order_event.price * 1.0005
        else:
            # 限价单：按指定价格成交
            return order_event.price
        
    def _calculate_commission(self, order_event: OrderEvent) -> float:
        """计算交易佣金"""
        return abs(order_event.quantity) * order_event.price * self.commission_rate
        
    def _generate_order_id(self) -> str:
        """生成唯一订单ID"""
        return f"order_{uuid.uuid4().hex[:8]}"

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
            commission=0,
            timestamp=datetime.now()
        )
