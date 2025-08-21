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
    def get_cash_balance(self) -> float:
        """获取当前现金余额"""
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
    def get_position_weights(self) -> Dict[str, float]:
        """获取所有持仓的权重"""
        pass
    
    @abstractmethod
    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓信息"""
        pass
    
    @abstractmethod
    def get_total_return(self) -> float:
        """计算总收益率"""
        pass
    
    @abstractmethod
    def get_daily_return(self) -> float:
        """计算日收益率"""
        pass
    
    @abstractmethod
    def update_position(self, symbol: str, quantity: float, price: float) -> bool:
        """更新持仓
        
        Args:
            symbol: 股票代码
            quantity: 数量(正为买入，负为卖出)
            price: 交易价格
        Returns:
            是否执行成功
        """
        pass
    
    @abstractmethod
    def validate_position_update(self, symbol: str, quantity: float, price: float) -> bool:
        """验证仓位更新是否有效"""
        pass
    
    @abstractmethod
    def clear_positions(self) -> None:
        """清空所有持仓，恢复初始现金状态"""
        pass
    
    @abstractmethod
    def invalidate_cache(self) -> None:
        """使缓存失效，在持仓或资金发生变化时调用"""
        pass
