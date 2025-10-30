from enum import Enum

class SignalType(Enum):
    """信号类型枚举"""
    OPEN = "OPEN"      # 开仓信号
    BUY = "BUY"        # 加仓信号  
    SELL = "SELL"      # 减仓信号
    CLOSE = "CLOSE"    # 清仓信号
    HEDGE = "HEDGE"    # 对冲信号
    REBALANCE = "REBALANCE"  # 再平衡信号