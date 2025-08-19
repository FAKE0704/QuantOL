class RiskManager:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        
    def validate_order(self, order_event):
        """验证订单是否满足风险要求"""
        # 检查可用资金
        if not self._check_funds(order_event):
            return False
            
        # 检查仓位限制
        if not self._check_position(order_event):
            return False
            
        return True
        
    def _check_funds(self, order_event):
        """检查可用资金是否充足"""
        required_cash = order_event.quantity * order_event.price * 1.001  # 包含手续费缓冲
        return self.portfolio.available_cash >= required_cash
        
    def _check_position(self, order_event):
        """检查是否超过仓位限制"""
        current_position = self.portfolio.get_position(order_event.symbol)
        new_position = current_position + order_event.quantity
        
        # 检查是否超过最大持仓比例
        max_percent = self.portfolio.get_strategy_limit(order_event.strategy_id)
        portfolio_value = self.portfolio.total_value
        position_value = abs(new_position) * order_event.price
        
        return position_value <= portfolio_value * max_percent
