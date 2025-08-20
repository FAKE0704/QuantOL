from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Position:
    """持仓数据结构"""
    stock: Any
    quantity: float
    avg_cost: float
    current_value: float

class IPortfolio(ABC):
    """投资组合接口
    
    定义RiskManager等组件需要访问的投资组合方法
    """
    
    @abstractmethod
    def get_available_cash(self) -> float:
        """获取可用现金余额"""
        pass
    
    @abstractmethod
    def get_position_amount(self) -> float:
        """获取持仓总金额"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定标的的持仓信息"""
        pass
    
    @abstractmethod
    def get_portfolio_value(self) -> float:
        """获取组合总价值"""
        pass
    
    @abstractmethod
    def get_position_weight(self, symbol: str) -> float:
        """获取单个持仓的权重"""
        pass
    
    @abstractmethod
    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓信息"""
        pass
