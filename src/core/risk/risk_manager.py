from typing import TYPE_CHECKING
from support.log.logger import logger

if TYPE_CHECKING:
    from ..portfolio.portfolio_interface import IPortfolio

class RiskManager:
    def __init__(self, portfolio: 'IPortfolio', commission_rate:float=0.0005):
        self.portfolio = portfolio
        self.commission_rate = commission_rate
        
    def validate_order(self, order_event):
        """验证订单是否满足风险要求"""
        # 检查可用资金
        if not self._check_funds(order_event):
            return False
        
        # 检查仓位限制 TODO:
        # if not self._check_position(order_event):
        #     return False
        return True
        
    def _check_funds(self, order_event):
        """检查可用资金是否充足"""
        required_cash = float(order_event.quantity) * float(order_event.price) * (1+self.commission_rate)  # 包含手续费缓冲
        # logger.debug(f"需求资金：{required_cash}") # 运行正常
        if order_event.direction == 'BUY':
            available_cash = self.portfolio.get_available_cash()
            # logger.debug(f"资金检查：尝试买入：{required_cash}；当前available_cash:{available_cash}") # 运行正常
            # logger.debug(f"{available_cash >= required_cash}") # 运行正常
            return available_cash >= required_cash
        else:
            position_amount = self.portfolio.get_position_amount()
            # logger.debug(f"资金检查：尝试卖出：{required_cash}；当前position_amount:{position_amount}") # 运行正常
            # logger.debug(f"{position_amount >= required_cash}") # 运行正常
            return position_amount >= required_cash # 持仓金额>=卖出金额
        
    def _check_position(self, order_event):
        """检查是否超过仓位限制"""
        current_position = self.portfolio.get_position(order_event.symbol)
        if current_position is None:
            # 没有持仓，直接返回True
            return True
        
        new_position = current_position.quantity + float(order_event.quantity)
        # 检查是否超过最大持仓比例
        # TODO: 需要从策略配置获取限制比例
        max_percent = 0.1  # 默认10%限制
        portfolio_value = self.portfolio.get_portfolio_value()
        position_value = float(abs(new_position)) * float(order_event.price)
        
        return position_value <= portfolio_value * max_percent
