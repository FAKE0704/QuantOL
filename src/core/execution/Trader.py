from datetime import datetime
from .TradeDatabaseManager import TradeDatabaseManager
from typing import Dict, Optional
import pandas as pd

class OrderManager:
    """订单管理类，负责订单的创建、修改、取消"""
    
    def __init__(self, db_manager: TradeDatabaseManager, commission_rate=0.0003):
        self.db_manager = db_manager
        self.commission_rate = commission_rate
        self.pending_orders = []
        self.executed_trades = []
        
    def create_order(self, symbol, order_type, quantity, price=None):
        """创建新订单"""
        order = {
            'symbol': symbol,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'status': 'new'
        }
        order_id = self.db_manager.save_order(order)
        self.pending_orders.append(order)
        return self.get_order(order_id)

    def process_orders(self, market_data: pd.DataFrame):
        """处理等待中的订单"""
        executed_trades = []
        for order in self.pending_orders:
            trade = self._execute_order(order, market_data)
            if trade:
                executed_trades.append(trade)
                self.db_manager.update_order_status(order['order_id'], 'executed')
        
        self.executed_trades.extend(executed_trades)
        self.pending_orders = []
        return executed_trades

    def _execute_order(self, order: Dict, market_data: pd.DataFrame) -> Optional[Dict]:
        """执行单个订单"""
        symbol = order['symbol']
        quantity = order['quantity']
        order_type = order['order_type']
        
        # 获取当前价格
        if order_type == 'market':
            price = market_data.loc[market_data['symbol'] == symbol, 'close'].values[0]
        else:
            price = order.get('price')
            if price is None:
                return None
        
        # 计算交易成本
        cost = price * quantity
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        # 生成交易记录
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
        self.db_manager.update_order_status(order_id, 'cancelled')
        return self.get_order(order_id)
        
    def get_order(self, order_id):
        """获取指定订单"""
        return self.db_manager.query_orders(order_id)


class ExecutionEngine:
    """执行引擎类，负责与同花顺app交互"""
    
    def __init__(self, db_manager: TradeDatabaseManager):
        self.db_manager = db_manager
        
    def generate_order_instruction(self, order):
        """生成交易指令"""
        instruction = {
            'symbol': order['symbol'],
            'action': 'buy' if order['order_type'] == 'market_buy' else 'sell',
            'quantity': order['quantity'],
            'price': order['price'],
            'status': 'pending'
        }
        return instruction
        
    def format_for_ths(self, instruction):
        """格式化指令以适应同花顺"""
        return f"{instruction['symbol']} {instruction['action']} {instruction['quantity']} @ {instruction['price']}"
        
    def log_execution(self, instruction, status):
        """记录执行状态"""
        execution = {
            'order_id': instruction.get('order_id'),
            'exec_price': instruction['price'],
            'exec_quantity': instruction['quantity'],
            'status': status
        }
        self.db_manager.log_execution(execution)
        return execution


class TradeRecorder:
    """交易记录类，负责记录所有交易细节"""
    
    def __init__(self, db_manager: TradeDatabaseManager):
        self.db_manager = db_manager
        
    def record_trade(self, execution):
        """记录交易"""
        trade = {
            'symbol': execution['instruction']['symbol'],
            'trade_price': execution['instruction']['price'],
            'trade_quantity': execution['instruction']['quantity'],
            'trade_type': execution['instruction']['action']
        }
        self.db_manager.record_trade(trade)
        return trade
        
    def query_trades(self, symbol=None):
        """查询交易记录"""
        return self.db_manager.query_trades(symbol)
