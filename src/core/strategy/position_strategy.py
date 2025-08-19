from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
import pandas as pd

class PositionStrategy(ABC):
    """仓位策略基类
    职责：
    - 计算理论仓位大小
    - 根据策略信号确定仓位比例
    注意：
    - 实际仓位限制检查由RiskManager负责
    """
    
    def __init__(self, account_value: float):
        """初始化策略
        Args:
            account_value: 账户当前净值
        """
        self.account_value = account_value
        
    @abstractmethod
    def calculate_position(self, signal_strength: float = 1.0) -> float:
        """计算仓位大小
        Args:
            signal_strength: 信号强度(0-1)
        Returns:
            仓位金额(绝对数值)
        """
        pass

class FixedPercentStrategy(PositionStrategy):
    """固定比例仓位策略
    职责：
    - 按固定比例计算仓位
    - 不考虑风险限制(由RiskManager处理)
    """
    
    def __init__(self, account_value: float, percent: float = 0.1):
        """初始化策略
        Args:
            account_value: 账户当前净值
            percent: 固定仓位比例(0-1)
        """
        super().__init__(account_value)
        if not 0 <= percent <= 1:
            raise ValueError("仓位比例必须在0-1之间")
        self.percent = percent
        
    def calculate_position(self, signal_strength: float = 1.0) -> float:
        """计算固定比例仓位
        Args:
            signal_strength: 信号强度(0-1)
        Returns:
            仓位金额 = 账户净值 * 固定比例 * 信号强度
        """
        if not 0 <= signal_strength <= 1:
            raise ValueError("信号强度必须在0-1之间")
        return self.account_value * self.percent * signal_strength

class KellyStrategy(PositionStrategy):
    """凯利公式仓位策略
    职责：
    - 根据凯利公式计算最优仓位
    - 最大仓位限制仅为公式计算上限
    - 实际执行需通过RiskManager验证
    """
    
    def __init__(self, 
                 account_value: float,
                 win_rate: float,
                 win_loss_ratio: float,
                 max_percent: float = 0.25):
        """初始化策略
        Args:
            account_value: 账户当前净值
            win_rate: 策略胜率(0-1)
            win_loss_ratio: 平均盈亏比(正数)
            max_percent: 最大仓位限制(0-1)
        """
        super().__init__(account_value)
        if not 0 <= win_rate <= 1:
            raise ValueError("胜率必须在0-1之间")
        if win_loss_ratio <= 0:
            raise ValueError("盈亏比必须为正数")
        if not 0 <= max_percent <= 1:
            raise ValueError("最大仓位限制必须在0-1之间")
            
        self.win_rate = win_rate
        self.win_loss_ratio = win_loss_ratio
        self.max_percent = max_percent
        
    def calculate_position(self, signal_strength: float = 1.0) -> float:
        """计算凯利公式仓位
        Args:
            signal_strength: 信号强度(0-1)
        Returns:
            仓位金额 = 账户净值 * 凯利比例 * 信号强度
        """
        if not 0 <= signal_strength <= 1:
            raise ValueError("信号强度必须在0-1之间")
            
        # 凯利公式计算
        kelly_fraction = (self.win_rate * (self.win_loss_ratio + 1) - 1) / self.win_loss_ratio
        kelly_fraction = max(0, min(kelly_fraction, self.max_percent))  # 限制范围
        
        return self.account_value * kelly_fraction * signal_strength
