from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Type
from src.core.strategy.position_strategy import FixedPercentStrategy, KellyStrategy, PositionStrategyFactory
from src.core.strategy.indicators import IndicatorService  # 新增IndicatorService导入
from src.core.strategy.rule_parser import RuleParser  # 新增RuleParser导入
from src.core.strategy.rule_based_strategy import RuleBasedStrategy  # 新增RuleBasedStrategy导入
from src.core.strategy.signal_types import SignalType  # 新增信号类型导入
from src.event_bus.event_types import StrategyScheduleEvent, TradingDayEvent, StrategySignalEvent, OrderEvent, FillEvent  # 新增OrderEvent和FillEvent导入
from src.core.risk.risk_manager import RiskManager  
from src.core.portfolio.portfolio import PortfolioManager 
from src.core.portfolio.portfolio_interface import Position, IPortfolio
from src.core.execution.Trader import BacktestTrader, TradeOrderManager  # 新增交易执行组件导入
import json
import streamlit as st  # 新增streamlit导入
from pathlib import Path
from src.support.log.logger import logger
import os
import pandas as pd

import logging
logger.setLevel(logging.DEBUG)  

@dataclass
class BacktestConfig:
    """
    回测配置类，包含回测所需的所有参数配置
    Attributes:
        initial_capital (float): 初始资金，默认100万
        commission_rate (float): 单笔交易手续费率（百分比值），默认0.0005
        slippage (float): 滑点率，默认0.001
        start_date (str): 回测开始日期，格式'YYYY-MM-DD'
        end_date (str): 回测结束日期，格式'YYYY-MM-DD'
        target_symbol (str): 目标交易标的代码
        target_symbols (List[str]): 多标的交易代码列表
        frequency (str): 数据频率

        strategy_type (str): 策略类型，默认"月定投"
        stop_loss (Optional[float]): 止损比例，None表示不启用
        take_profit (Optional[float]): 止盈比例，None表示不启用
        max_holding_days (Optional[int]): 最大持仓天数，None表示不限制
        extra_params (Dict[str, Any]): 额外参数存储

        position_strategy_type (str): 仓位策略类型，默认"fixed_percent"
        position_strategy_params (Dict[str, float]): 仓位策略参数，支持参数包括：
            - fixed_percent: {"percent": 0.1} (10%仓位)
            - kelly: {"max_position_percent": 0.25} (最大25%仓位)

        min_lot_size (int): 最小交易手数，默认100股（A股市场）

        strategy_mapping (Dict[str, Dict[str, Any]]): 股票-策略映射配置
        default_strategy (Dict[str, Any]): 默认策略配置
    """

    start_date: str
    end_date: str
    target_symbol: str
    frequency: str
    target_symbols: List[str] = field(default_factory=list)

    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_days: Optional[int] = None
    extra_params: Optional[Dict[str, Any]] = None
    initial_capital: float = 1e6
    commission_rate: float = 0.0005
    slippage: float = 0.00
    strategy_type: str = "月定投"
    position_strategy_type: str = "fixed_percent"
    position_strategy_params: Dict[str, Any] = field(default_factory=dict)
    min_lot_size: int = 100
    strategy_mapping: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_strategy: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """参数验证和兼容性处理"""
        self.commission_rate = self.commission_rate
        self.slippage = float(self.slippage)
        
        # 增强的符号兼容性处理
        if not self.target_symbols and self.target_symbol:
            # 只有target_symbol时，自动转换为target_symbols
            self.target_symbols = [self.target_symbol]
        elif self.target_symbols and not self.target_symbol:
            # 只有target_symbols时，设置target_symbol为首个符号
            self.target_symbol = self.target_symbols[0]
        elif self.target_symbols and self.target_symbol and self.target_symbol not in self.target_symbols:
            # 如果target_symbol不在target_symbols中，添加到列表开头
            self.target_symbols.insert(0, self.target_symbol)
        
        # 确保target_symbol始终是target_symbols的第一个元素
        if self.target_symbols and self.target_symbol != self.target_symbols[0]:
            self.target_symbol = self.target_symbols[0]
        elif not self.target_symbol and not self.target_symbols:
            raise ValueError("必须指定至少一个交易标的")
        
        # 资金分配逻辑（多符号模式下）
        if len(self.target_symbols) > 1:
            self._distribute_capital()
        
        if self.initial_capital <= 0:
            raise ValueError("初始资金必须大于0")
        if self.commission_rate < 0:
            raise ValueError("手续费率不能为负")
        if self.slippage < 0:
            raise ValueError("滑点率不能为负")
        if datetime.strptime(self.start_date, "%Y%m%d") > datetime.strptime(self.end_date, "%Y%m%d"):
            raise ValueError("开始日期不能晚于结束日期")
        if self.stop_loss is not None and (self.stop_loss <= 0 or self.stop_loss >= 1):
            raise ValueError("止损比例必须在0到1之间")
        if self.take_profit is not None and (self.take_profit <= 0 or self.take_profit >= 1):
            raise ValueError("止盈比例必须在0到1之间")

    def get_symbols(self) -> List[str]:
        """统一获取所有交易标的符号列表"""
        if self.target_symbols:
            return self.target_symbols
        elif self.target_symbol:
            return [self.target_symbol]
        else:
            raise ValueError("未指定任何交易标的")

    def is_multi_symbol(self) -> bool:
        """判断是否为多符号模式"""
        return len(self.get_symbols()) > 1

    def get_primary_symbol(self) -> str:
        """获取主符号（用于兼容旧代码）"""
        symbols = self.get_symbols()
        return symbols[0] if symbols else None

    def _distribute_capital(self):
        """多符号模式下的资金分配逻辑"""
        if not hasattr(self, '_capital_distribution'):
            # 默认平均分配资金
            num_symbols = len(self.target_symbols)
            self._capital_distribution = {
                symbol: self.initial_capital / num_symbols 
                for symbol in self.target_symbols
            }
        
        # 支持自定义资金分配比例
        if self.extra_params and 'capital_weights' in self.extra_params:
            weights = self.extra_params['capital_weights']
            total_weight = sum(weights.values())
            if total_weight > 0:
                self._capital_distribution = {
                    symbol: self.initial_capital * (weights.get(symbol, 0) / total_weight)
                    for symbol in self.target_symbols
                }

    def get_symbol_capital(self, symbol: str) -> float:
        """获取指定符号的分配资金"""
        if not self.is_multi_symbol():
            return self.initial_capital

        if hasattr(self, '_capital_distribution'):
            return self._capital_distribution.get(symbol, 0)

        # 默认平均分配
        return self.initial_capital / len(self.target_symbols)

    def get_strategy_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """获取指定股票的策略配置"""
        return self.strategy_mapping.get(symbol, self.default_strategy)
        
    def _validate_position_strategy_params(self):
        """验证仓位策略参数"""
        if self.position_strategy_type == "fixed_percent":
            percent = self.position_strategy_params.get("percent", 0.1)
            if not (0 < percent <= 1):
                raise ValueError("fixed_percent策略的percent参数必须在0到1之间")
        elif self.position_strategy_type == "kelly":
            max_position_percent = self.position_strategy_params.get("max_position_percent", 0.25)
            if not (0 < max_position_percent <= 1):
                raise ValueError("kelly策略的max_position_percent参数必须在0到1之间")
        # 可以添加其他策略类型的验证

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            "initial_capital": self.initial_capital,
            "commission_rate": self.commission_rate,
            "slippage": self.slippage,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "target_symbol": self.target_symbol,
        "target_symbols": self.target_symbols,
            "frequency": self.frequency,
            
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "max_holding_days": self.max_holding_days,
            "extra_params": self.extra_params,
            "position_strategy_type": self.position_strategy_type,
            "position_strategy_params": self.position_strategy_params.copy()  # 返回副本避免引用问题
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
        
        self.config = config
        self.event_queue = []
        self.current_price = None  # 回测过程的当前价格
        self.current_time = None #回测过程的当前时间

        self.current_index = None
        self.handlers = {}  # 事件处理器字典 {event_type: handler}
        self.strategies = []  # 支持多个策略
        
        # 支持单符号和多符号数据
        if isinstance(data, dict):
            # 多符号模式：data是字典 {symbol: dataframe}
            self.multi_symbol_mode = True
            self.data_dict = data
            # 使用第一个符号的数据作为主时间轴
            first_symbol = next(iter(data.keys()))
            self.data = data[first_symbol]
        else:
            # 单符号模式：data是DataFrame
            self.multi_symbol_mode = False
            self.data_dict = {config.target_symbol: data}
            self.data = data
        
        # 初始化指标服务和规则解析器
        self.indicator_service = IndicatorService()
        self.rule_parser = RuleParser(self.data, self.indicator_service)
        self.trades = [] # 交易记录
        self.results = {}
        self.errors = []
        self.equity_records = pd.DataFrame(columns=[  # 净值记录
            'timestamp',
            'price',
            'position',
            'cash',
            'total_value'
        ])

        # 使用配置创建仓位策略（优先使用新的固定比例仓位管理策略）
        try:
            if config.position_strategy_type == "fixed_percent":
                # 使用新的固定比例仓位管理策略
                from src.core.strategy.fixed_percent_position_strategy import FixedPercentPositionStrategy

                position_params = config.position_strategy_params
                self.position_strategy = FixedPercentPositionStrategy(
                    percent=position_params.get("percent", 0.1),
                    use_initial_capital=position_params.get("use_initial_capital", True),
                    min_lot_size=getattr(config, 'min_lot_size', 100)
                )
                logger.info(f"固定比例仓位管理策略创建成功: percent={self.position_strategy.percent}")
            else:
                # 使用旧版本的仓位策略（保持兼容性）
                self.position_strategy = PositionStrategyFactory.create_strategy(
                    config.position_strategy_type,
                    config.initial_capital,
                    config.position_strategy_params
                )
                logger.info(f"仓位策略创建成功: {config.position_strategy_type}")
        except Exception as e:
            logger.error(f"仓位策略创建失败: {str(e)}，使用默认策略")
            # 使用默认策略作为fallback
            from src.core.strategy.fixed_percent_position_strategy import FixedPercentPositionStrategy
            self.position_strategy = FixedPercentPositionStrategy(
                percent=0.1,
                use_initial_capital=True,
                min_lot_size=getattr(config, 'min_lot_size', 100)
            )
        
        # 初始化PortfolioManager
        self.portfolio_manager = PortfolioManager(
            initial_capital=config.initial_capital,
            position_strategy=self.position_strategy,
            event_bus=None  # 回测中不使用事件总线
        )
        
        # 初始化交易执行组件
        self.backtest_trader = BacktestTrader(commission_rate=config.commission_rate)
        # TradeOrderManager需要DatabaseManager和Trader
        self.trade_order_manager = TradeOrderManager(st.session_state.db, self.backtest_trader)
        
        # 初始化Portfolio接口和RiskManager
        self.portfolio = self.portfolio_manager  # PortfolioManager 实现了 IPortfolio 接口
        self.risk_manager = RiskManager(self.portfolio, self.config.commission_rate)
        
        # 更新规则解析器以包含投资组合管理器引用
        self.rule_parser.portfolio_manager = self.portfolio_manager
        
        # 注册StrategySignalEvent处理器
        self.register_handler(StrategySignalEvent, self._handle_signal_event)
        
        # 注册OrderEvent处理器
        self.register_handler(OrderEvent, self._handle_order_event)
        
        # 注册FillEvent处理器
        self.register_handler(FillEvent, self._handle_fill_event)
        
    def update_rule_parser_data(self):
        """更新RuleParser的数据引用"""
        self.rule_parser.data = self.data
        self.rule_parser.indicator_service = self.indicator_service
        self.rule_parser.portfolio_manager = self.portfolio_manager

    def run(self, start_date: datetime, end_date: datetime):
        """执行事件驱动的回测"""

        # 更新RuleParser数据引用
        self.update_rule_parser_data()
        
        
        # 根据数据频率处理时间字段
        if self.config.frequency.lower() == 'd':
            logger.debug(f"识别数据频率为：日线")
            self.data['combined_time'] = pd.to_datetime(self.data['date'], format='%Y-%m-%d')
            # 为日线数据添加默认时间
            self.data['time'] = '00:00:00'
        else:
            
            if 'time' not in self.data.columns:
                raise ValueError("分钟线数据必须包含time字段")
            
            # 检查time列的空值
            null_time_data = self.data[self.data['time'].isnull()]
            if not null_time_data.empty:
                logger.warning(f"发现{len(null_time_data)}条time列为空的记录")
                logger.debug(f"空time记录: {null_time_data.head()}")
        
        
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
        logger.debug(f"开始回测... 数据总数: {len(self.data)}")
        logger.debug(f"数据列: {list(self.data.columns)}")
        logger.debug(f"数据预览: {self.data.head(1).to_dict()}")

        for idx in range(len(self.data)):
            if idx % 100 == 0:  # 每100条记录输出一次进度
                logger.debug(f"回测进度: {idx}/{len(self.data)}")

            current_time = self.data.iloc[idx]['combined_time']
            self.current_time = current_time
            self.current_index = idx
            self.current_price = self.data.loc[self.current_index,'close']
            
            # 仓位策略的资金更新现在通过PortfolioManager接口进行
            # 在_calculate_position_amount方法中实时获取账户价值，确保状态一致性
            
            # 系统初始化（首个交易日）
            if idx == 0:
                self._initialize_backtest_system()
            
            # 更新RuleParser数据引用和当前索引
            self.update_rule_parser_data()
            self.rule_parser.current_index = idx
            
            
            # 触发所有注册策略的定时检查
            if idx == 0:
                logger.debug(f"已注册策略数量: {len(self.strategies)}")
                for i, strategy in enumerate(self.strategies):
                    logger.debug(f"策略 {i}: {type(strategy).__name__} - {strategy.name if hasattr(strategy, 'name') else '未命名'}")

            for strategy in self.strategies:
                logger.debug(f"触发策略: {type(strategy).__name__} - {strategy.name if hasattr(strategy, 'name') else '未命名'}")
                strategy.on_schedule(self)
            # logger.debug(f"已触发策略数量: {len(self.strategies)}")

            # 处理事件队列（处理非StrategySignalEvent和OrderEvent的其他事件）
            # logger.debug(f"处理前事件队列长度: {len(self.event_queue) if hasattr(self, 'event_queue') else 0}")
            self._process_event_queue()
            # logger.debug(f"处理后事件队列长度: {len(self.event_queue) if hasattr(self, 'event_queue') else 0}")

            # 在每个数据点通过PortfolioManager记录净值历史
            price_data = {
                'close': self.current_price
            }
            self.portfolio_manager.record_equity_history(current_time, price_data)

            # 添加详细调试日志
            # logger.debug(f"当前数据: {self.data.iloc[idx].to_dict()}")
        

    def handle_trading_day_event(self, event):
        """处理交易日事件"""
        logger.debug(f"处理交易日事件 @ {event.timestamp}")
        logger.debug(f"待处理事件队列: {[e.__class__.__name__ for e in self.event_queue]}")
        
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

        # 使用current_index参数（如果存在）或默认使用当前索引
        idx = getattr(event, 'current_index', self.current_index)

        # 记录信号到数据中
        if event.signal_type in [SignalType.OPEN, SignalType.BUY]:
            self.data.loc[idx, 'signal'] = 1
        elif event.signal_type in [SignalType.SELL, SignalType.CLOSE]:
            self.data.loc[idx, 'signal'] = -1
        elif event.signal_type == SignalType.HEDGE:
            self.data.loc[idx, 'signal'] = 2  # 对冲信号
        elif event.signal_type == SignalType.REBALANCE:
            self.data.loc[idx, 'signal'] = 3  # 再平衡信号

        # 使用仓位管理策略计算交易数量
        if hasattr(self.position_strategy, 'calculate_position_size'):
            # 使用新的固定比例仓位管理策略
            self._create_order_with_position_strategy(event)
        else:
            # 使用旧的订单创建方式（保持兼容性）
            if event.signal_type in [SignalType.OPEN, SignalType.BUY, SignalType.SELL, SignalType.CLOSE]:
                self._create_order_from_signal(event)
            elif event.signal_type == SignalType.HEDGE:
                self._create_hedge_order(event)
            elif event.signal_type == SignalType.REBALANCE:
                self._create_rebalance_order(event)

    def _create_order_with_position_strategy(self, event: StrategySignalEvent):
        """使用仓位管理策略创建订单"""
        try:
            # 获取当前投资组合信息
            portfolio_data = {
                'initial_capital': self.config.initial_capital,
                'available_cash': self.portfolio_manager.get_available_cash(),
                'total_equity': self.portfolio_manager.get_total_value()
            }

            # 获取当前持仓
            current_position = 0
            if self.multi_symbol_mode:
                # 多符号模式：获取对应符号的持仓
                symbol = event.symbol
                current_position = self.portfolio_manager.get_position_size(symbol)
            else:
                # 单符号模式：获取目标符号的持仓
                current_position = self.portfolio_manager.get_position_size(self.config.target_symbol)

            # 使用仓位管理策略计算交易数量
            quantity = self.position_strategy.calculate_position_size(
                signal_type=event.signal_type,
                portfolio_data=portfolio_data,
                current_price=float(event.price),
                current_position=current_position
            )

            logger.debug(f"仓位策略计算结果: {quantity}, 信号类型: {event.signal_type}, 当前持仓: {current_position}")

            # 创建交易订单
            if quantity > 0:
                # 买入订单
                self._create_buy_order(event, quantity)
            elif quantity < 0:
                # 卖出订单
                self._create_sell_order(event, abs(quantity))

        except Exception as e:
            error_msg = f"仓位策略订单创建失败: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)

    def _create_buy_order(self, event: StrategySignalEvent, quantity: int):
        """创建买入订单"""
        try:
            from src.event_bus.event_types import OrderEvent

            order_event = OrderEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                quantity=quantity,
                side="BUY",
                price=float(event.price),
                strategy_id=event.strategy_id
            )

            # 将订单事件添加到事件队列
            self.event_queue.append(order_event)
            logger.debug(f"创建买入订单: {quantity}股 {event.symbol} @ {event.price}")

        except Exception as e:
            error_msg = f"买入订单创建失败: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)

    def _create_sell_order(self, event: StrategySignalEvent, quantity: int):
        """创建卖出订单"""
        try:
            from src.event_bus.event_types import OrderEvent

            order_event = OrderEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                quantity=quantity,
                side="SELL",
                price=float(event.price),
                strategy_id=event.strategy_id
            )

            # 将订单事件添加到事件队列
            self.event_queue.append(order_event)
            logger.debug(f"创建卖出订单: {quantity}股 {event.symbol} @ {event.price}")

        except Exception as e:
            error_msg = f"卖出订单创建失败: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)

    def _create_order_from_signal(self, event: StrategySignalEvent):
        """从策略信号创建订单事件（通过TradeOrderManager处理）"""
        try:
            price = float(event.price)
            
            # 确定订单方向
            if event.signal_type in [SignalType.OPEN, SignalType.BUY]:
                direction = "BUY"
            elif event.signal_type in [SignalType.SELL, SignalType.CLOSE]:
                direction = "SELL"
            else:
                self.log_error(f"不支持创建订单的信号类型: {event.signal_type}")
                return
            
            # 计算订单数量
            if event.quantity > 0:
                # 如果信号中指定了数量，直接使用
                quantity = event.quantity
            else:
                # 否则使用仓位策略计算
                position_amount = self._calculate_position_amount(event)
                quantity = self._calculate_order_quantity(position_amount, price)
            
            # 对于CLOSE信号，计算全部持仓数量
            if event.signal_type == SignalType.CLOSE:
                current_position = self.portfolio_manager.get_position(event.symbol)
                if current_position and current_position.quantity > 0:
                    quantity = current_position.quantity
                else:
                    self.log_error(f"无法清仓: {event.symbol} 无持仓")
                    return
            
            # 3. 创建OrderEvent
            order_event = OrderEvent(
                strategy_id=event.strategy_id,
                symbol=event.symbol,
                direction=direction,
                price=price,
                quantity=quantity,
                order_type="LIMIT"
            )
            # logger.debug(f"创建订单事件: {order_event}") # 运行正常
            
            # 4. 风险检查
            risk_check_result = self._validate_order_risk(order_event)
            
            if risk_check_result:
                # 5. 通过TradeOrderManager创建订单并处理
                self._process_order_through_trade_manager(order_event)
               
            else:
                # logger.warning(f"订单风险检查失败: {order_event}")
                pass
                
        except Exception as e:
            self.log_error(f"创建订单失败: {str(e)}")
            
    def _process_order_through_trade_manager(self, order_event: OrderEvent):
        """在回测环境中处理订单（直接生成模拟的FillEvent）"""
        try:
            # logger.debug(f"开始处理回测订单: {order_event.direction} {order_event.quantity}@{order_event.price}")
            
            # 在回测环境中，我们不需要依赖外部交易接口
            # 直接假设订单立即成交，生成模拟的FillEvent
            
            # 计算手续费（确保类型兼容）
            commission_amount = float(order_event.quantity) * float(order_event.price) * float(self.config.commission_rate)
            # logger.debug(f"计算手续费: {commission_amount:.2f} (费率: {self.config.commission_rate:.4f})")
            
            # 创建模拟的FillEvent（根据FillEvent的实际构造函数参数）
            order_id = f"backtest_order_{len(self.trades)}"
            
            # 确保timestamp是datetime类型（pandas Timestamp需要转换）
            if self.current_time is not None and hasattr(self.current_time, 'to_pydatetime'):
                timestamp = self.current_time.to_pydatetime()
            elif self.current_time is not None and isinstance(self.current_time, datetime):
                timestamp = self.current_time
            else:
                timestamp = datetime.now()
                
            fill_event = FillEvent(
                order_id=order_id,
                symbol=order_event.symbol,
                direction=order_event.direction, # 买卖方向
                fill_price=order_event.price,  # 假设按订单价格成交
                fill_quantity=order_event.quantity,  # 假设全部成交
                commission=commission_amount,
                timestamp=timestamp
            )

            # 处理成交回报
            
            self._handle_fill_event(fill_event)
                 
        except Exception as e:
            self.log_error(f"处理回测订单失败: {str(e)}")
            
    def _calculate_position_amount(self, event: StrategySignalEvent) -> float:
        """计算仓位金额
        通过PortfolioManager接口获取当前账户价值，确保状态一致性
        """
        signal_strength = getattr(event, 'confidence', 1.0)
        
        # 获取当前账户价值
        current_account_value = self.portfolio_manager.get_portfolio_value()
        
        # 更新仓位策略的账户价值
        self.position_strategy.account_value = current_account_value
        
        return self.position_strategy.calculate_position(signal_strength)
        
    def _calculate_order_quantity(self, position_amount: float, price: float) -> int:
        """计算订单数量（向下取整到最小交易手数的倍数）"""
        if price <= 0:
            raise ValueError("价格必须大于0")
        
        # 计算理论数量
        raw_quantity = position_amount / price
        
        # 向下取整到最小交易手数的倍数
        min_lot = self.config.min_lot_size
        quantity = int(raw_quantity // min_lot) * min_lot
        
        # 确保至少是最小手数
        return max(min_lot, quantity)
        
    def _validate_order_risk(self, order_event: OrderEvent) -> bool:
        """验证订单风险"""
        
        if not self.risk_manager.validate_order(order_event):
            # logger.warning(f"订单风险检查失败: 拒绝操作！")
            return False
        return True
        
    def _handle_order_event(self, event: OrderEvent):
        """处理订单事件 - 使用PortfolioManager执行订单并更新持仓和资金"""
        logger.debug(f"处理订单事件: {event}")
        
        try:
            # 计算订单总金额（包含手续费），确保类型一致性
            order_amount = float(event.quantity) * float(event.price)
            commission = order_amount * self.config.commission_rate
            total_cost = order_amount + commission
            
            # 根据订单方向确定仓位更新数量
            quantity = event.quantity if event.direction == 'BUY' else -event.quantity
            
            # 使用PortfolioManager更新持仓
            success = self.portfolio_manager.update_position(
                symbol=event.symbol,
                quantity=quantity,
                price=event.price
            )
            
            if not success:
                self.log_error(f"订单执行失败: {event.direction} {event.quantity}@{event.price}")
                return
                
            # 记录交易
            trade_record = {
                'timestamp': self.current_time,
                'symbol': event.symbol,
                'direction': event.direction,
                'price': event.price,
                'quantity': event.quantity,
                'commission': commission,
                'total_cost': total_cost if event.direction == 'BUY' else -total_cost
            }
            self.trades.append(trade_record)
                
            
        except Exception as e:
            self.log_error(f"订单执行失败: {str(e)}")

    def log_error(self, message: str):
        """记录错误信息"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'current_capital': self.portfolio_manager.get_available_cash(),
            'position': self.portfolio_manager.get_all_positions()
        }
        self.errors.append(error_entry)
        logger.error(f"ERROR | {message}")

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
        logger.debug(f"注册事件处理器: {event_type.__name__}")

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
        existing_ids = [s.strategy_id for s in self.strategies]
        if strategy.strategy_id in existing_ids:
            raise ValueError(f"策略ID {strategy.strategy_id} 已存在")

        self.strategies.append(strategy)

        # 添加调试信息
        strategy_name = getattr(strategy, 'name', '未命名')
        print(f"[DEBUG] 策略注册成功 | ID: {strategy.strategy_id} | 名称: {strategy_name} | 类型: {type(strategy).__name__}")

        # 注册策略调度事件处理器
        self.register_handler(StrategyScheduleEvent, strategy.on_schedule)
        logger.debug(f"注册策略调度处理器: {strategy.strategy_id}")

        # 记录策略注册日志
        logger.info(f"策略注册成功 | ID: {strategy.strategy_id} | 名称: {strategy_name}")

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

        if self.multi_symbol_mode and hasattr(self, 'results') and self.results:
            # 多符号模式，返回组合结果
            return self.results

        # 单符号模式
        # 使用PortfolioManager的性能指标
        performance_metrics = self.portfolio_manager.get_performance_metrics()

        # 收集调试数据（如果有基于规则的策略）
        debug_data = {}
        print(f"[DEBUG] 收集调试数据 - 总策略数: {len(self.strategies)}")

        for strategy in self.strategies:
            strategy_name = strategy.name if hasattr(strategy, 'name') else 'unknown'
            strategy_type = type(strategy).__name__

            print(f"[DEBUG] 检查策略: {strategy_name} ({strategy_type})")

            if hasattr(strategy, 'debug_data'):
                if strategy.debug_data is not None:
                    debug_data[strategy_name] = strategy.debug_data
                    print(f"[DEBUG] ✓ 找到debug_data: {strategy_name}, 列数: {len(strategy.debug_data.columns)}")
                else:
                    print(f"[DEBUG] ✗ debug_data为None: {strategy_name}")
            else:
                print(f"[DEBUG] ✗ 无debug_data属性: {strategy_name} ({strategy_type})")

        print(f"[DEBUG] 最终收集到的debug_data数量: {len(debug_data)}")

        return {
            "summary": {
                "initial_capital": self.config.initial_capital,
                "final_capital": self.portfolio_manager.get_portfolio_value(),
                "total_trades": len(self.trades),
                "win_rate": self._calculate_win_rate(),
                "max_drawdown": performance_metrics['max_drawdown_pct'],
                "total_return": performance_metrics['total_return_pct'],
                "current_drawdown": performance_metrics['current_drawdown_pct'],
                "position_strategy_type": self.config.position_strategy_type
            },
            "trades": self.trades,
            "errors": self.errors,
            "equity_records": self.portfolio_manager.get_equity_history(),
            "position_strategy_config": {
                "type": self.config.position_strategy_type,
                "params": self.config.position_strategy_params
            },
            "performance_metrics": performance_metrics,
            "debug_data": debug_data  # 添加调试数据
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
        logger.info("回测系统初始化开始")
        
        # 1. 预计算指标数据
        if hasattr(self.indicator_service, 'calculate_indicators'):
            # TODO
            pass
            # self.indicator_service.calculate_indicators(self.data)
        
        # 2. 初始化所有注册策略
        for strategy in self.strategies:
            if hasattr(strategy, 'initialize'):
                strategy.initialize(self.data)
            # logger.info(f"策略初始化完成: {strategy.strategy_id}")
        
        # 3. 设置仓位管理策略
        # if not self.position_strategy:
            # TODO:添加仓位管理策略
            # pass
            # logger.info("使用默认仓位策略: FixedPercentStrategy(1%)")
        
        # 4. 清空交易记录和错误日志
        self.trades = []
        self.errors = []
        logger.info("回测系统初始化完成")
        
    def _update_equity(self, market_data):
        """更新净值记录"""
        # 确保数值类型正确
        if market_data['close'] is None:
            logger.warning(f"跳过净值更新: 收盘价为None | 时间: {market_data['datetime']}")
            return
            
        try:
            close_price = float(market_data['close'])
            # 使用PortfolioManager接口获取当前资金
            current_capital = float(self.portfolio_manager.get_available_cash())
        except (TypeError, ValueError) as e:
            self.log_error(f"净值更新参数类型错误: {str(e)}")
            return
            
        # 计算持仓价值 - 通过PortfolioManager接口获取持仓信息
        all_positions = self.portfolio_manager.get_all_positions()
        position_quantity = 0.0
        if self.config.target_symbol in all_positions:
            position_quantity = all_positions[self.config.target_symbol].quantity
        
        position_value = position_quantity * close_price
        total_value = current_capital + position_value
        
        # 创建净值记录
        record = {
            'timestamp': pd.to_datetime(market_data['datetime']),
            'price': close_price,
            'position': position_quantity,
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

    def _process_event_queue(self):
        """处理事件队列中的事件（处理非StrategySignalEvent和OrderEvent的其他事件）"""
        if not self.event_queue:
            return
            
        logger.debug(f"处理事件队列，当前队列长度: {len(self.event_queue)}")
        
        # 处理队列中的所有事件
        while self.event_queue:
            event = self.event_queue.pop(0)
            handler = self.handlers.get(type(event))
            
            if handler:
                try:
                    # 跳过StrategySignalEvent和OrderEvent，因为它们已经直接处理
                    if isinstance(event, (StrategySignalEvent, OrderEvent)):
                        logger.debug(f"跳过直接处理的事件类型: {type(event).__name__}")
                        continue
                        
                    # 处理其他类型的事件
                    handler(event)
                    logger.debug(f"成功处理事件: {type(event).__name__}")
                    
                except Exception as e:
                    self.log_error(f"处理事件失败: {type(event).__name__} - {str(e)}")
            else:
                logger.warning(f"未找到事件处理器: {type(event).__name__}")

    def _handle_fill_event(self, event: FillEvent):
        """处理成交回报事件，使用PortfolioManager更新资金和持仓"""
        
        try:
            # 计算成交金额，确保类型一致性
            fill_price = float(event.fill_price)
            fill_quantity = float(event.fill_quantity)
            commission = float(event.commission)
            
            # 根据方向确定仓位更新数量（买入为正，卖出为负）
            quantity = fill_quantity if event.direction == 'BUY' else -fill_quantity
            
            # 记录交易发生前的现金和持仓状态
            cash_before = self.portfolio_manager.get_cash_balance()
            portfolio_value_before = self.portfolio_manager.get_portfolio_value()
            positions_value_before = portfolio_value_before - cash_before
            
            # 使用PortfolioManager更新持仓
            success = self.portfolio_manager.update_position(
                symbol=event.symbol,
                quantity=quantity,
                price=fill_price
            )
            
            if not success:
                self.log_error(f"成交回报处理失败: 无法更新持仓")
                return
                
            # 记录交易
            trade_record = {
                'timestamp': event.timestamp,
                'symbol': event.symbol,
                'direction': event.direction,
                'price': event.fill_price,
                'quantity': event.fill_quantity,
                'commission': event.commission,
                'total_cost': (fill_price * fill_quantity + commission) if event.direction == 'BUY' else -(fill_price * fill_quantity - commission),
                'cash_before': cash_before,
                'positions_value_before': positions_value_before,
                'cash_after': self.portfolio_manager.get_cash_balance(),
                'positions_value_after': self.portfolio_manager.get_portfolio_value() - self.portfolio_manager.get_cash_balance()
            }
            self.trades.append(trade_record)
            
            
        except Exception as e:
            self.log_error(f"处理成交回报事件失败: {str(e)}")
            # 添加更详细的错误信息
            import traceback
            self.log_error(f"详细错误信息: {traceback.format_exc()}")
            
    # 保留其他原有方法不变...
    # (get_results, create_order等)

    def run_multi_symbol(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """执行多符号回测

        对于每个符号，运行单独的回测，然后组合结果
        """
        if not self.multi_symbol_mode:
            # 单符号模式，直接运行普通回测
            self.run(start_date, end_date)
            return self.get_results()

        # 多符号模式
        all_results = {}
        individual_results = {}

        # 为每个符号运行单独的回测
        for symbol, data in self.data_dict.items():
            logger.info(f"Running backtest for symbol: {symbol}")

            # 为每个符号创建单独的配置
            symbol_config = BacktestConfig(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                target_symbol=symbol,
                frequency=self.config.frequency,
                initial_capital=self.config.initial_capital / len(self.data_dict),  # 平均分配资金
                commission_rate=self.config.commission_rate,
                position_strategy_type=self.config.position_strategy_type,
                position_strategy_params=self.config.position_strategy_params
            )

            # 创建并运行单独的引擎
            symbol_engine = BacktestEngine(symbol_config, data)

            # 为每个符号创建新的策略实例（根据策略映射）
            for strategy in self.strategies:
                # 获取该股票的策略配置
                symbol_strategy_config = self.config.get_strategy_for_symbol(symbol)

                # 创建策略副本或新实例
                if hasattr(strategy, 'name') and hasattr(strategy, 'buy_rule_expr'):
                    # 对于RuleBasedStrategy类型的策略，重新创建实例
                    # 确保指标服务不为None
                    indicator_service = getattr(strategy, 'indicator_service', None)
                    if indicator_service is None:
                        from src.core.strategy.indicators import IndicatorService
                        indicator_service = IndicatorService()

                    # 使用策略映射中的规则表达式（如果存在），否则使用原策略的规则
                    buy_rule = symbol_strategy_config.get('buy_rule', getattr(strategy, 'buy_rule_expr', ''))
                    sell_rule = symbol_strategy_config.get('sell_rule', getattr(strategy, 'sell_rule_expr', ''))
                    open_rule = symbol_strategy_config.get('open_rule', getattr(strategy, 'open_rule_expr', ''))
                    close_rule = symbol_strategy_config.get('close_rule', getattr(strategy, 'close_rule_expr', ''))

                    symbol_strategy = RuleBasedStrategy(
                        Data=data,  # 使用当前符号的数据
                        name=f"{getattr(strategy, 'name', 'Unknown')}_{symbol}",
                        indicator_service=indicator_service,
                        buy_rule_expr=buy_rule,
                        sell_rule_expr=sell_rule,
                        open_rule_expr=open_rule,
                        close_rule_expr=close_rule,
                        portfolio_manager=getattr(strategy, 'portfolio_manager', None)
                    )
                else:
                    # 对于其他类型的策略，使用原策略
                    symbol_strategy = strategy
                symbol_engine.register_strategy(symbol_strategy)

            # 运行回测
            symbol_engine.run(start_date, end_date)

            # 存储单个符号的结果
            individual_results[symbol] = symbol_engine.get_results()

            # 合并交易记录
            self.trades.extend(symbol_engine.trades)

            # 合并错误
            self.errors.extend(symbol_engine.errors)

        # 创建组合结果
        all_results["individual"] = individual_results
        all_results["trades"] = self.trades
        all_results["errors"] = self.errors

        # 计算组合净值曲线（简单相加）
        combined_equity = pd.DataFrame()
        for symbol, results in individual_results.items():
            if "equity_records" in results:
                equity_data = pd.DataFrame(results["equity_records"])
                if combined_equity.empty:
                    combined_equity = equity_data[['timestamp', 'total_value']].copy()
                    combined_equity.rename(columns={'total_value': symbol}, inplace=True)
                else:
                    # 合并时间对齐的净值数据
                    equity_data = equity_data[['timestamp', 'total_value']].rename(columns={'total_value': symbol})
                    combined_equity = combined_equity.merge(equity_data, on='timestamp', how='outer')

        # 计算组合总净值
        if not combined_equity.empty:
            combined_equity['total_value'] = combined_equity.drop('timestamp', axis=1).sum(axis=1)
            all_results["combined_equity"] = combined_equity

        # 收集所有符号的调试数据
        all_debug_data = {}
        for symbol, results in individual_results.items():
            if "debug_data" in results and results["debug_data"]:
                # 为每个符号的调试数据添加前缀
                for strategy_name, debug_data in results["debug_data"].items():
                    prefixed_name = f"{symbol}_{strategy_name}"
                    all_debug_data[prefixed_name] = debug_data

        # 添加调试数据到总结果中
        if all_debug_data:
            all_results["debug_data"] = all_debug_data

        # 添加策略映射信息到结果中
        all_results["strategy_mapping"] = self.config.strategy_mapping
        all_results["default_strategy"] = self.config.default_strategy

        self.results = all_results
        return all_results

    def _create_hedge_order(self, event: StrategySignalEvent):
        """创建对冲订单"""
        # 对冲逻辑实现 - 创建反向仓位
        try:
            price = float(event.price)
            
            # 获取当前持仓
            current_position = self.portfolio_manager.get_position(event.symbol)
            if not current_position or current_position.quantity == 0:
                self.log_error(f"无法对冲: {event.symbol} 无持仓")
                return
            
            # 计算对冲数量
            hedge_ratio = event.hedge_ratio or 0.5  # 默认50%对冲
            hedge_quantity = int(current_position.quantity * hedge_ratio)
            
            # 创建反向订单
            direction = "SELL" if current_position.quantity > 0 else "BUY"
            
            order_event = OrderEvent(
                strategy_id=event.strategy_id,
                symbol=event.symbol,
                direction=direction,
                price=price,
                quantity=hedge_quantity,
                order_type="LIMIT"
            )
            
            if self._validate_order_risk(order_event):
                self._process_order_through_trade_manager(order_event)
                
        except Exception as e:
            self.log_error(f"创建对冲订单失败: {str(e)}")

    def _create_rebalance_order(self, event: StrategySignalEvent):
        """创建再平衡订单"""
        # 再平衡逻辑实现
        try:
            price = float(event.price)
            
            # 获取当前持仓
            current_position = self.portfolio_manager.get_position(event.symbol)
            
            # 计算目标持仓数量
            target_percent = event.position_percent or 0.0
            portfolio_value = self.portfolio_manager.get_portfolio_value()
            target_value = portfolio_value * target_percent
            target_quantity = int(target_value / price) if price > 0 else 0
            
            # 计算需要调整的数量
            current_quantity = current_position.quantity if current_position else 0
            adjust_quantity = target_quantity - current_quantity
            
            if adjust_quantity == 0:
                return  # 无需调整
            
            # 确定订单方向
            direction = "BUY" if adjust_quantity > 0 else "SELL"
            
            order_event = OrderEvent(
                strategy_id=event.strategy_id,
                symbol=event.symbol,
                direction=direction,
                price=price,
                quantity=abs(adjust_quantity),
                order_type="LIMIT"
            )
            
            if self._validate_order_risk(order_event):
                self._process_order_through_trade_manager(order_event)
                
        except Exception as e:
            self.log_error(f"创建再平衡订单失败: {str(e)}")
