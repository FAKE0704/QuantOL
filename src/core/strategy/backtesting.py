from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Type
from core.strategy.position_strategy import FixedPercentStrategy, KellyStrategy
from core.strategy.indicators import IndicatorService  # 新增IndicatorService导入
from core.strategy.rule_parser import RuleParser  # 新增RuleParser导入
from event_bus.event_types import StrategyScheduleEvent, TradingDayEvent, StrategySignalEvent  # 新增事件类型导入
import json
from pathlib import Path
import os
import pandas as pd
import streamlit as st
import logging
from support.log.logger import logger
logger.setLevel(logging.DEBUG)  # 确保DEBUG级别日志输出

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
    frequency:str
    monthly_investment: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_days: Optional[int] = None
    extra_params: Optional[Dict[str, Any]] = None
    initial_capital: float = 1e6
    commission: float = 0.0005
    slippage: float = 0.00

    def __post_init__(self):
        """参数验证"""
        if self.initial_capital <= 0:
            raise ValueError("初始资金必须大于0")
        if self.commission < 0:
            raise ValueError("手续费率不能为负")
        if self.slippage < 0:
            raise ValueError("滑点率不能为负")
        if datetime.strptime(self.start_date, "%Y%m%d") > datetime.strptime(self.end_date, "%Y%m%d"):
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
    
    def __init__(self, config: BacktestConfig, data):
        self.logger = logger
        self.config = config
        self.event_queue = []
        self.current_price = None  # 回测过程的当前价格
        self.current_time = None #回测过程的当前时间

        self.current_index = None
        self.handlers = {}  # 事件处理器字典 {event_type: handler}
        self.strategies = []  # 支持多个策略
        self.data = data  # 回测数据
        # 初始化指标服务和规则解析器
        self.indicator_service = IndicatorService()
        self.rule_parser = RuleParser(self.data, self.indicator_service)
        self.trades = [] # 交易记录
        self.results = {}
        self.current_capital = config.initial_capital
        self.errors = []
        self.equity_records = pd.DataFrame(columns=[  # 净值记录
            'timestamp',
            'price',
            'position',
            'cash',
            'total_value'
        ])

        # 仓位、持仓相关
        self.positions = {}  # 按策略ID存储持仓 {strategy_id: position}
        self.position_strategy = None  # 仓位策略id
        self.current_month = None  # 跟踪当前月份
        
        # 注册StrategySignalEvent处理器
        self.register_handler(StrategySignalEvent, self._handle_signal_event)
        
        self.position_meta = {
            'quantity': 0,
            'avg_price': 0.0,
            'direction': 0  # 1: 多头, -1: 空头
        }
        self.strategy_holdings = {}  # 策略持仓状态 {strategy_id: holdings}
        self.position_records = {}  # 记录持仓时间 {strategy_id: {'entry_time': datetime, 'quantity': int}}

    def update_rule_parser_data(self):
        """更新RuleParser的数据引用"""
        self.rule_parser.data = self.data
        self.rule_parser.indicator_service = self.indicator_service

    def run(self, start_date: datetime, end_date: datetime):
        """执行事件驱动的回测"""

        # 初始化仓位策略资金
        if self.position_strategy:
            self.position_strategy.account_value = self.current_capital
        
        # 更新RuleParser数据引用
        self.update_rule_parser_data()
        
        # 根据数据频率处理时间字段
        if self.config.frequency.lower() == 'd':
            self.logger.debug(f"识别数据频率为：日线")
            self.data['combined_time'] = pd.to_datetime(self.data['date'], format='%Y-%m-%d')
            # 为日线数据添加默认时间
            self.data['time'] = '00:00:00'
        else:
            if 'time' not in self.data.columns:
                raise ValueError("分钟线数据必须包含time字段")
            self.data['combined_time'] = pd.to_datetime(
                self.data['date'].astype(str) + ' ' + self.data['time'].astype(str),
                format='%Y-%m-%d %H:%M:%S'
            )
        
        # 初始化signal列
        self.data['signal'] = 0  # 0:无信号, 1:买入, -1:卖出
        
        # 初始化净值记录
        self._update_equity({
            'datetime': start_date,
            'close': self.data.iloc[0]['close']
        })
        
        # 设置初始日期
        self.current_time = self.data['combined_time'].iloc[0]
        
        
        # 遍历触发事件
        self.logger.debug("开始回测...")
        for idx in range(len(self.data)):
            current_time = self.data.iloc[idx]['combined_time']
            self.current_time = current_time
            self.current_index = idx
            
            # 系统初始化（首个交易日）
            if idx == 0:
                self._initialize_backtest_system()
            
            # 更新RuleParser数据引用和当前索引
            self.update_rule_parser_data()
            self.rule_parser.current_index = idx
            
            
            # 触发所有注册策略的定时检查
            for strategy in self.strategies:
                # logger.debug("进入on_schedule方法")
                strategy.on_schedule(self)
            # logger.debug(f"已触发策略数量: {len(self.strategies)}")

            # 添加详细调试日志
            # logger.debug(f"当前数据: {self.data.iloc[idx].to_dict()}")
            
        self.logger.debug("回测完成")

    def handle_trading_day_event(self, event):
        """处理交易日事件"""
        self.logger.debug(f"处理交易日事件 @ {event.timestamp}")
        self.logger.debug(f"待处理事件队列: {[e.__class__.__name__ for e in self.event_queue]}")
        
        # 处理事件队列
        while self.event_queue:
            event = self.event_queue.pop(0)
            handler = self.handlers.get(type(event))
            if handler:
                try:
                    # 处理策略信号事件
                    if isinstance(event, StrategySignalEvent):
                        # 使用StrategySignalEvent的direction属性
                        if event.direction in ('BUY', 'SELL'):
                            self.data.loc[event.timestamp, 'signal'] = 1 if event.direction == 'BUY' else -1
                        else:
                            self.log_error(f"无效的信号方向: {event.direction}")
                    # 处理策略定时事件
                    elif isinstance(event, StrategyScheduleEvent):
                        # 处理定时事件逻辑
                        pass
                except Exception as e:
                    self.log_error(f"处理事件失败: {str(e)}")
        
        # 更新净值记录
        self._update_equity({
            'datetime': event.timestamp,
            'close': self.current_price
        })

    def _handle_signal_event(self, event: StrategySignalEvent):
        """处理策略信号事件"""
        self.logger.debug(f"处理策略信号: {event.direction} {event.symbol}@{event.price}")
        
        # 使用current_index参数（如果存在）或默认使用当前索引
        idx = getattr(event, 'current_index', self.current_index)
        
        # 在此处添加信号处理逻辑
        if event.direction in ('BUY', 'SELL'):
            print("信号只是没有被更新"*5)
            self.data.loc[idx, 'signal'] = 1 if event.direction == 'BUY' else -1
            self.logger.debug(f"在索引 {idx} 处记录信号: {event.direction}")
        else:
            self.log_error(f"无效的信号方向: {event.direction}")

    def log_error(self, message: str):
        """记录错误信息"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'current_capital': self.current_capital,
            'position': self.position_meta.copy()
        }
        self.errors.append(error_entry)
        self.logger.error(f"ERROR | {message}")

    def push_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)

    def register_handler(self, event_type: Type, handler):
        """注册事件处理器
        Args:
            event_type: 事件类型类
            handler: 事件处理函数
        """
        self.handlers[event_type] = handler
        self.logger.debug(f"注册事件处理器: {event_type.__name__}")

    def register_strategy(self, strategy):
        """注册策略实例
        Args:
            strategy: 策略实例，必须实现handle_event方法和strategy_id属性
        """
        if not hasattr(strategy, 'handle_event'):
            raise ValueError("策略必须实现handle_event方法")
        if not hasattr(strategy, 'strategy_id'):
            raise ValueError("策略必须设置strategy_id属性")
            
        # 验证策略ID是否有效
        if not strategy.strategy_id or not isinstance(strategy.strategy_id, str):
            raise ValueError(f"无效的策略ID: {strategy.strategy_id}")
            
        # 检查是否已存在相同ID的策略
        if strategy.strategy_id in self.strategy_holdings:
            raise ValueError(f"策略ID {strategy.strategy_id} 已存在")
            
        self.strategies.append(strategy)
        self.strategy_holdings[strategy.strategy_id] = 0  # 初始化持仓
        
        # 注册策略调度事件处理器
        self.register_handler(StrategyScheduleEvent, strategy.on_schedule)
        self.logger.debug(f"注册策略调度处理器: {strategy.strategy_id}")
        
        # 记录策略注册日志
        self.logger.info(f"策略注册成功 | ID: {strategy.strategy_id} | 名称: {getattr(strategy, 'name', '未命名')}")

    def create_rule_based_strategy(self, name: str, 
                                  buy_rule_expr: str = "", 
                                  sell_rule_expr: str = ""):
        """创建基于规则的策略实例"""
        from .rule_based_strategy import RuleBasedStrategy
        return RuleBasedStrategy(
            Data=self.data,
            name=name,
            indicator_service=self.indicator_service,
            buy_rule_expr=buy_rule_expr,
            sell_rule_expr=sell_rule_expr
        )

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
            "errors": self.errors,
            "equity_records": self.equity_records.to_dict('records')
        }

    def _calculate_win_rate(self) -> float:
        """计算交易胜率"""
        if not self.trades:
            return 0.0
        winning_trades = len([t for t in self.trades if t.get('profit', 0) > 0])
        return winning_trades / len(self.trades) if self.trades else 0.0

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if self.equity_records.empty:
            return 0.0
        peak = self.equity_records['total_value'].max()
        trough = self.equity_records['total_value'].min()
        return (peak - trough) / peak if peak != 0 else 0.0

    def _initialize_backtest_system(self):
        """回测系统初始化（首个交易日执行）"""
        self.logger.info("回测系统初始化开始")
        
        # 1. 预计算指标数据
        if hasattr(self.indicator_service, 'calculate_indicators'):
            # TODO
            pass
            # self.indicator_service.calculate_indicators(self.data)
        
        # 2. 初始化所有注册策略
        for strategy in self.strategies:
            if hasattr(strategy, 'initialize'):
                strategy.initialize(self.data)
            self.logger.info(f"策略初始化完成: {strategy.strategy_id}")
        
        # 3. 设置仓位管理策略
        if not self.position_strategy:
            # TODO:添加仓位管理策略
            pass
            # self.logger.info("使用默认仓位策略: FixedPercentStrategy(1%)")
        
        # 4. 初始化持仓记录
        self.position_meta = {
            'quantity': 0,
            'avg_price': 0.0,
            'direction': 0
        }
        
        # 5. 清空交易记录和错误日志
        self.trades = []
        self.errors = []
        self.logger.info("回测系统初始化完成")
        
    def _update_equity(self, market_data):
        """更新净值记录"""
        # 确保数值类型正确
        if market_data['close'] is None:
            self.logger.warning(f"跳过净值更新: 收盘价为None | 时间: {market_data['datetime']}")
            return
            
        try:
            close_price = float(market_data['close'])
            current_capital = float(self.current_capital)
        except (TypeError, ValueError) as e:
            self.log_error(f"净值更新参数类型错误: {str(e)}")
            return
            
        # 计算持仓价值
        position_value = self.position_meta['quantity'] * close_price
        total_value = current_capital + position_value
        
        # 创建净值记录
        record = {
            'timestamp': pd.to_datetime(market_data['datetime']),
            'price': close_price,
            'position': self.position_meta['quantity'],
            'cash': current_capital,
            'total_value': total_value
        }
        
        # 更新净值记录
        if self.equity_records.empty:
            self.equity_records = pd.DataFrame([record])
        else:
            self.equity_records = pd.concat([
                self.equity_records,
                pd.DataFrame([record])
            ], ignore_index=True)

    # 保留其他原有方法不变...
    # (_update_equity, get_results, create_order等)
