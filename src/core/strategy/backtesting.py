from dataclasses import dataclass
from datetime import datetime, timedelta
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Type
import json
from .events import ScheduleEvent, SignalEvent
import pandas as pd

@dataclass
class BacktestConfig:
    """
    回测配置类，包含回测所需的所有参数配置
    
    Attributes:
        initial_capital (float): 初始资金，默认100万
        commission (float): 单笔交易手续费率，默认0.0005
        slippage (float): 滑点率，默认0.001
        start_date (str): 回测开始日期，格式'YYYY-MM-DD'
        end_date (str): 回测结束日期，格式'YYYY-MM-DD'
        target_symbol (str): 目标交易标的代码
        monthly_investment (Optional[float]): 每月定投金额，None表示不定投
        stop_loss (Optional[float]): 止损比例，None表示不启用
        take_profit (Optional[float]): 止盈比例，None表示不启用
        max_holding_days (Optional[int]): 最大持仓天数，None表示不限制
        extra_params (Dict[str, Any]): 额外参数存储
    """
    
    start_date: str
    end_date: str
    target_symbol: str
    monthly_investment: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_days: Optional[int] = None
    extra_params: Dict[str, Any] = None
    initial_capital: float = 1e6
    commission: float = 0.0005
    slippage: float = 0.001

    def __post_init__(self):
        """参数验证"""
        if self.initial_capital <= 0:
            raise ValueError("初始资金必须大于0")
        if self.commission < 0:
            raise ValueError("手续费率不能为负")
        if self.slippage < 0:
            raise ValueError("滑点率不能为负")
        if datetime.strptime(self.start_date, "%Y-%m-%d") > datetime.strptime(self.end_date, "%Y-%m-%d"):
            raise ValueError("开始日期不能晚于结束日期")
        if self.monthly_investment is not None and self.monthly_investment <= 0:
            raise ValueError("定投金额必须大于0")
        if self.stop_loss is not None and (self.stop_loss <= 0 or self.stop_loss >= 1):
            raise ValueError("止损比例必须在0到1之间")
        if self.take_profit is not None and (self.take_profit <= 0 or self.take_profit >= 1):
            raise ValueError("止盈比例必须在0到1之间")
        if self.max_holding_days is not None and self.max_holding_days <= 0:
            raise ValueError("最大持仓天数必须大于0")
        if self.extra_params is None:
            self.extra_params = {}

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            "initial_capital": self.initial_capital,
            "commission": self.commission,
            "slippage": self.slippage,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "target_symbol": self.target_symbol,
            "monthly_investment": self.monthly_investment,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "max_holding_days": self.max_holding_days,
            "extra_params": self.extra_params
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BacktestConfig":
        """从字典创建配置实例"""
        return cls(**config_dict)

    def to_json(self) -> str:
        """将配置转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "BacktestConfig":
        """从JSON字符串创建配置实例"""
        return cls.from_dict(json.loads(json_str))

class BacktestEngine:
    """回测引擎，负责执行回测流程"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.event_queue = []
        self.handlers = {}
        self.strategy = None
        self.market_data = None
        self.trades = []
        self.results = {}
        self.current_capital = config.initial_capital
        self.positions = {}
        self.errors = []
        self.equity_history = {"dates": [], "values": []}  # 初始化净值记录
        self.last_equity_date = None

    def register_handler(self, event_type: Type, handler):
        """根据时间类型，注册事件处理器。"""
        self.handlers[event_type] = handler

    def push_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)

    def run(self, start_date: datetime, end_date: datetime):
        """执行事件循环"""
        current_date = start_date
        
        # 记录初始净值
        if not self.equity_history["dates"]:
            self.equity_history["dates"].append(current_date.strftime("%Y-%m-%d"))
            self.equity_history["values"].append(self.config.initial_capital)
        
        while current_date <= end_date:
            # 记录当日开盘净值
            if current_date != self.last_equity_date:
                self.equity_history["dates"].append(current_date.strftime("%Y-%m-%d"))
                self.equity_history["values"].append(self.current_capital)
                self.last_equity_date = current_date
            
            # 处理当日事件
            # print("##"*20)
            # print(self.event_queue[0]) # debug
            while self.event_queue:
                event = self.event_queue.pop(0)
                handler = self.handlers.get(type(event))
                if handler:
                    try:
                        handler(event)
                    except Exception as e:
                        self.log_error(f"处理事件失败: {str(e)}")
            
            # 移动到下个交易日
            current_date += timedelta(days=1)
        
        # 确保最后一天净值被记录
        if self.equity_history["dates"][-1] != end_date.strftime("%Y-%m-%d"):
            self.equity_history["dates"].append(end_date.strftime("%Y-%m-%d"))
            self.equity_history["values"].append(self.current_capital)

    def get_results(self) -> Dict:
        """获取回测结果"""
        return {
            "summary": {
                "initial_capital": self.config.initial_capital,
                "final_capital": self.current_capital,
                "total_trades": len(self.trades),
                "win_rate": self._calculate_win_rate(),
                "max_drawdown": self._calculate_max_drawdown()
            },
            "trades": self.trades,
            "errors": self.errors
        }

    def get_historical_data(self, timestamp: datetime, lookback_days: int):
        """获取历史数据"""
        # 实现数据获取逻辑
        pass

    def update_market_data(self, data):
        """更新市场数据"""
        self.market_data = data

    def create_order(self, symbol: str, quantity: int, side: str, price: float):
        """创建交易订单"""
        trade = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "price": price
        }
        self.trades.append(trade)

    def log_error(self, message: str):
        """记录错误日志"""
        self.errors.append({
            "timestamp": datetime.now(),
            "message": message
        })

    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        if not self.trades:
            return 0.0
        winning_trades = [t for t in self.trades if t['side'] == 'buy' and t['price'] > t['entry_price']]
        return len(winning_trades) / len(self.trades)

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.trades:
            return 0.0
        peak = self.trades[0]['price']
        max_drawdown = 0.0
        for trade in self.trades:
            if trade['price'] > peak:
                peak = trade['price']
            drawdown = (peak - trade['price']) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown

    def get_equity_curve(self) -> pd.DataFrame:
        """获取净值曲线数据"""

        return pd.DataFrame({
            "dates": self.equity_history["dates"],
            "values": self.equity_history["values"]
        })
