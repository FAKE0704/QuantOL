from typing import Dict, List, Optional, Any
import time
from functools import lru_cache
from datetime import datetime
from ..strategy.position_strategy import PositionStrategy
from .portfolio_interface import IPortfolio, Position
from event_bus.event_types import PortfolioPositionUpdateEvent
from support.log.logger import logger

class PortfolioManager(IPortfolio):
    """投资组合管理类
    
    职责：
    - 管理投资组合的持仓和资金状态
    - 跟踪仓位变化和资金变动
    - 计算组合价值和收益指标
    - 支持组合再平衡计算
    - 提供性能优化的缓存机制
    - 与TradeExecutionEngine协同工作，不执行实际交易操作
    """
    
    def __init__(self, 
                 initial_capital: float,
                 position_strategy: PositionStrategy,
                 event_bus: Optional[Any] = None):
        """初始化组合
        Args:
            initial_capital: 初始资金
            position_strategy: 仓位策略
            event_bus: 事件总线实例，可选
            equity_histoy:历史净值记录，
                record = {
                    'timestamp': timestamp,
                    'total_value': total_value,
                    'cash': self.current_cash,
                    'positions_value': total_value - self.current_cash,
                    'return_pct': self.get_total_return() * 100,
                    'drawdown_pct': current_drawdown,
                    'peak_value': self._peak_value
                }
            _peak_value：最高收益
            _max_drawdown：最大回撤
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.position_strategy = position_strategy
        self.event_bus = event_bus
        self.positions: Dict[str, Position] = {}
        
        self.equity_history: List[Dict] = []
        self._peak_value: float = initial_capital
        self._max_drawdown: float = 0.0
        
        # 缓存相关属性
        self._portfolio_value_cache: Optional[float] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 1.0  # 缓存有效期1秒
        self._last_update_time: float = time.time()
        
    def update_position(self, symbol: str, quantity: float, price: float) -> bool:
        """更新持仓
        
        Args:
            symbol: 股票代码
            quantity: 数量(正为买入，负为卖出)
            price: 交易价格
        Returns:
            是否执行成功
        """
        # 基本验证
        if not self.validate_position_update(symbol, quantity, price):
            return False
            
        # 风险检查（待实现）
        # if not self.risk_manager.validate_position(symbol, quantity, price):
        #     return False
            
        # 执行仓位更新
        cost = quantity * price
        if symbol in self.positions:
            position = self.positions[symbol]
            new_quantity = position.quantity + quantity
            if new_quantity == 0:
                del self.positions[symbol]
            else:
                position.avg_cost = (
                    (position.quantity * position.avg_cost + cost) / new_quantity
                )
                position.quantity = new_quantity
                position.current_value = new_quantity * price
        else:
            # 创建简化的Stock对象用于存储
            class SimpleStock:
                def __init__(self, symbol, price):
                    self.symbol = symbol
                    self.last_price = price
                    
                def __repr__(self):
                    return f"<SimpleStock {symbol}@{price}>"
            
            stock = SimpleStock(symbol, price)
            self.positions[symbol] = Position(
                stock=stock,
                quantity=quantity,
                avg_cost=price,
                current_value=quantity * price
            )
            
        self.current_cash -= cost
        
        # 使缓存失效
        self.invalidate_cache()
        
        # 发布持仓更新事件
        if self.event_bus:
            portfolio_value = self.get_portfolio_value()
            position = self.positions.get(symbol)
            if position:
                event = PortfolioPositionUpdateEvent(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    quantity=position.quantity,
                    avg_cost=position.avg_cost,
                    current_value=position.current_value,
                    cash_balance=self.current_cash,
                    portfolio_value=portfolio_value,
                    update_type="SINGLE",
                    success=True
                )
                self.event_bus.publish(event)
        
        return True
        
    def update_position_for_backtest(self, symbol: str, quantity: float, price: float) -> bool:
        """回测专用的更新持仓方法
        
        Args:
            symbol: 股票代码
            quantity: 数量(正为买入，负为卖出)
            price: 交易价格
        Returns:
            是否执行成功
        """
        # 直接调用新的update_position方法
        return self.update_position(symbol, quantity, price)
        
    def get_portfolio_value(self, use_cache: bool = False) -> float:
        """获取组合总价值（支持缓存）
        
        Args:
            use_cache: 是否使用缓存，默认为True
        Returns:
            组合总价值
        """
        current_time = time.time()
        
        # 检查缓存是否有效
        if (use_cache and 
            self._portfolio_value_cache is not None and
            current_time - self._cache_timestamp < self._cache_ttl):
            
            logger.debug("total_value 使用缓存")
            return self._portfolio_value_cache
        
        # 计算实际价值
        positions_value = sum(
            pos.current_value for pos in self.positions.values()
        )
        total_value = self.current_cash + positions_value
        
        # 更新缓存
        self._portfolio_value_cache = total_value
        self._cache_timestamp = current_time
        
        # logger.debug(f"最终总资产{total_value}")
        return total_value
        
    def invalidate_cache(self) -> None:
        """使缓存失效，在持仓或资金发生变化时调用"""
        self._portfolio_value_cache = None
        self._cache_timestamp = 0
        
    def update_positions_batch(self, updates: List[Dict]) -> List[bool]:
        """批量更新持仓
        
        Args:
            updates: 更新列表，每个元素包含symbol, quantity, price
                [{'symbol': str, 'quantity': float, 'price': float}, ...]
        Returns:
            各更新操作的结果列表
        """
        results = []
        
        for update in updates:
            symbol = update['symbol']
            quantity = update['quantity']
            price = update['price']
            
            # 使用新的update_position方法
            result = self.update_position(symbol, quantity, price)
            results.append(result)
        
        return results
        
    def rebalance(self, target_allocations: Dict[str, float]) -> List[bool]:
        """组合再平衡
        Args:
            target_allocations: 目标配置比例 {symbol: weight}
        Returns:
            各标的调仓结果列表
        """
        results = []
        total_value = self.get_portfolio_value()
        
        for symbol, target_weight in target_allocations.items():
            current_pos = self.positions.get(symbol)
            current_value = current_pos.current_value if current_pos else 0
            target_value = total_value * target_weight
            
            # 跳过无效配置
            if target_value <= 0:
                continue
                
            if current_pos:
                if target_value > current_value:
                    # 需要买入
                    quantity = (target_value - current_value) / current_pos.stock.last_price
                    results.append(self.update_position(
                        symbol, quantity, current_pos.stock.last_price
                    ))
                else:
                    # 需要卖出
                    quantity = (current_value - target_value) / current_pos.stock.last_price
                    results.append(self.update_position(
                        symbol, -quantity, current_pos.stock.last_price
                    ))
            else:
                # 新持仓标的处理 - 需要获取股票对象
                # 这里需要外部提供股票对象，暂时跳过
                print(f"警告: 无法处理新持仓标的 {symbol}，需要提供股票对象")
                results.append(False)
                
        return results

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定标的的持仓信息
        Args:
            symbol: 股票代码
        Returns:
            持仓对象，如果不存在则返回None
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓信息
        Returns:
            持仓字典 {symbol: Position}
        """
        return self.positions.copy()

    def get_available_cash(self) -> float:
        """获取可用现金余额
        Returns:
            可用现金余额
        """
        return self.current_cash

    def get_position_amount(self) -> float:
        """获取持仓总金额
        Returns:
            持仓总金额
        """
        return sum(pos.current_value for pos in self.positions.values())

    def get_cash_balance(self) -> float:
        """获取当前现金余额
        Returns:
            现金余额
        """
        return self.current_cash

    def get_total_return(self) -> float:
        """计算总收益率
        Returns:
            总收益率 (当前价值/初始资金 - 1)
        """
        current_value = self.get_portfolio_value()
        return (current_value / self.initial_capital) - 1

    def get_daily_return(self) -> float:
        """计算日收益率
        Returns:
            日收益率 (基于上次更新时间的价值变化)
        """
        current_value = self.get_portfolio_value()
        previous_value = self._portfolio_value_cache or current_value
        return (current_value / previous_value) - 1

    def get_position_weight(self, symbol: str) -> float:
        """获取单个持仓的权重
        Args:
            symbol: 股票代码
        Returns:
            持仓权重 (持仓价值/组合总价值)
        """
        position = self.positions.get(symbol)
        if not position:
            return 0.0
        total_value = self.get_portfolio_value()
        return position.current_value / total_value if total_value > 0 else 0.0

    def get_position_weights(self) -> Dict[str, float]:
        """获取所有持仓的权重
        Returns:
            持仓权重字典 {symbol: weight}
        """
        total_value = self.get_portfolio_value()
        if total_value <= 0:
            return {}
        
        weights = {}
        for symbol, position in self.positions.items():
            weights[symbol] = position.current_value / total_value
        
        return weights

    def record_equity_history(self, timestamp: datetime, price_data: Optional[Dict] = None) -> None:
        """记录净值历史
        Args:
            timestamp: 时间戳
            price_data: 价格数据，可选
        """
        total_value = self.get_portfolio_value()
        
        # 更新峰值价值
        if total_value > self._peak_value:
            self._peak_value = total_value
        
        # 计算当前回撤
        current_drawdown = ((self._peak_value - total_value) / self._peak_value) * 100 if self._peak_value > 0 else 0.0
        
        # 更新最大回撤
        if current_drawdown > self._max_drawdown:
            self._max_drawdown = current_drawdown
        
        # 创建净值记录
        record = {
            'timestamp': timestamp,
            'total_value': total_value,
            'cash': self.current_cash,
            'positions_value': total_value - self.current_cash,
            'return_pct': self.get_total_return() * 100,
            'drawdown_pct': current_drawdown,
            'peak_value': self._peak_value
        }
        
        # 如果有价格数据，添加到记录中
        if price_data:
            record.update(price_data)
        
        self.equity_history.append(record)

    def get_equity_history(self) -> List[Dict]:
        """获取净值历史记录
        Returns:
            净值历史记录列表
        """
        return self.equity_history.copy()

    def get_max_drawdown(self) -> float:
        """获取最大回撤
        Returns:
            最大回撤百分比
        """
        return self._max_drawdown

    def get_current_drawdown(self) -> float:
        """获取当前回撤
        Returns:
            当前回撤百分比
        """
        total_value = self.get_portfolio_value()
        return ((self._peak_value - total_value) / self._peak_value) * 100 if self._peak_value > 0 else 0.0

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        Returns:
            性能指标字典
        """
        total_value = self.get_portfolio_value()
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'total_return_pct': self.get_total_return() * 100,
            'max_drawdown_pct': self.get_max_drawdown(),
            'current_drawdown_pct': self.get_current_drawdown(),
            'cash_balance': self.current_cash,
            'positions_value': total_value - self.current_cash,
            'positions_count': len(self.positions)
        }

    def clear_positions(self) -> None:
        """清空所有持仓，恢复初始现金状态"""
        self.positions.clear()
        self.current_cash = self.initial_capital
        self.equity_history.clear()
        self._peak_value = self.initial_capital
        self._max_drawdown = 0.0
        self.invalidate_cache()

    def validate_position_update(self, symbol: str, quantity: float, price: float) -> bool:
        """验证仓位更新是否有效
        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格
        Returns:
            是否有效
        """
        # 基本验证
        if quantity == 0:
            return False
            
        if price <= 0:
            return False
            
        # 资金验证
        cost = quantity * price
        if quantity > 0 and cost > self.current_cash:
            return False
            
        # 持仓验证（卖出不能超过现有持仓）
        if quantity < 0:
            current_position = self.positions.get(symbol)
            if not current_position or abs(quantity) > current_position.quantity:
                return False
                
        return True
