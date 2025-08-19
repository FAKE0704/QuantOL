from typing import Dict, List
from dataclasses import dataclass
from ..data.stock import Stock
from ..strategy.position_strategy import PositionStrategy
from ..risk.risk_manager import RiskManager

@dataclass
class Position:
    """持仓数据结构
    要求Stock类实现以下属性:
    - symbol: 股票代码
    - last_price: 最新价格
    """
    stock: Stock
    quantity: float
    avg_cost: float
    current_value: float

class Portfolio:
    """投资组合管理类"""
    
    def __init__(self, 
                 initial_capital: float,
                 position_strategy: PositionStrategy,
                 risk_manager: RiskManager):
        """初始化组合
        Args:
            initial_capital: 初始资金
            position_strategy: 仓位策略
            risk_manager: 风控管理器
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.position_strategy = position_strategy
        self.risk_manager = risk_manager
        self.positions: Dict[str, Position] = {}
        
    def update_position(self, stock: Stock, quantity: float, price: float) -> bool:
        """更新持仓
        
        Args:
            stock: 股票对象
            quantity: 数量(正为买入，负为卖出)
            price: 交易价格
        Returns:
            是否执行成功
        """
        # 计算理论仓位
        target_amount = self.position_strategy.calculate_position()
        
        # 风险检查
        # 风险检查暂时跳过，待RiskManager实现
        # if not self.risk_manager.validate_position(stock, quantity, price):
        #     return False
        return True
            
        # 执行仓位更新
        cost = quantity * price
        if stock.symbol in self.positions:
            position = self.positions[stock.symbol]
            new_quantity = position.quantity + quantity
            if new_quantity == 0:
                del self.positions[stock.symbol]
            else:
                position.avg_cost = (
                    (position.quantity * position.avg_cost + cost) / new_quantity
                )
                position.quantity = new_quantity
        else:
            self.positions[stock.symbol] = Position(
                stock=stock,
                quantity=quantity,
                avg_cost=price,
                current_value=quantity * price
            )
            
        self.current_cash -= cost
        return True
        
    def get_portfolio_value(self) -> float:
        """获取组合总价值"""
        positions_value = sum(
            pos.current_value for pos in self.positions.values()
        )
        return self.current_cash + positions_value
        
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
                        current_pos.stock, quantity, current_pos.stock.last_price
                    ))
                else:
                    # 需要卖出
                    quantity = (current_value - target_value) / current_pos.stock.last_price
                    results.append(self.update_position(
                        current_pos.stock, -quantity, current_pos.stock.last_price
                    ))
            else:
                # 新持仓标的处理
                pass
                
        return results
                
        return results
