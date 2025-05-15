from dataclasses import dataclass
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Type
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import os
from core.strategy.events import ScheduleEvent, SignalEvent
import pandas as pd
import streamlit as st

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
    extra_params: Dict[str, Any] = None
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
    
    def __init__(self, config: BacktestConfig, data):\
        slef.
        self.config = config
        self.event_queue = []
        self.current_price = None  # 添加当前价格属性
        self.handlers = {}
        self.strategies = []  # 改为支持多个策略
        self.data = data  # 回测数据
        self.trades = [] # 交易记录
        self.results = {}
        self.current_capital = config.initial_capital
        self.positions = {}  # 按策略ID存储持仓 {strategy_id: position}
        self.errors = []
        # 更详细的净值记录结构
        self.equity_records = pd.DataFrame(columns=[
            'timestamp',
            'price',
            'position',
            'cash',
            'total_value'
        ])
        self.current_month = None  # 跟踪当前月份
        self.current_date = None  # 初始化当前回测日期
        self.position_meta = {
            'quantity': 0,
            'avg_price': 0.0,
            'direction': 0  # 1: 多头, -1: 空头
        }
        self.strategy_holdings = {}  # 策略持仓状态 {strategy_id: holdings}
        self.position_records = {}  # 记录持仓时间 {strategy_id: {'entry_time': datetime, 'quantity': int}}

        # 初始化日志配置
        self._init_logging()

    

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

    def register_handler(self, event_type: Type, handler):
        """注册事件处理器"""
        self.handlers[event_type] = handler

    def register_strategy(self, strategy):
        """注册策略实例"""
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
        
        # 为定投策略添加事件处理器
        if hasattr(strategy, 'is_fixed_investment') and strategy.is_fixed_investment:
            self.register_handler(ScheduleEvent, strategy.handle_event)
            
        # 记录策略注册日志
        self.logger.info(f"策略注册成功 | ID: {strategy.strategy_id} | 名称: {strategy.name}")

    def push_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)

    def run(self, start_date: datetime, end_date: datetime):
        """执行事件循环"""
        
        # 调试日志：输出数据时间范围
        self.logger.info(f"[DEBUG] 回测数据时间范围: {self.data['date'].min()} 至 {self.data['date'].max()}")
        self.logger.info(f"[DEBUG] 数据记录总数: {len(self.data)}")
        
        # 明确指定日期时间格式
        self.data['combined_time'] = pd.to_datetime(
            self.data['date'].astype(str) + ' ' + self.data['time'].astype(str),
            format='%Y-%m-%d %H:%M:%S'
        )
        
        # 初始化净值记录
        self._update_equity({
            'datetime': start_date,
            'close': self.data.iloc[0]['close']
        })
        
        # 调试日志：显示数据日期范围
        print(f"[DEBUG] 可用数据日期范围: {self.data['date'].min()} 至 {self.data['date'].max()}")
        print(f"[DEBUG] 请求回测日期范围: {start_date} 至 {end_date}")
        
        # 验证并调整日期范围
        max_data_date = pd.to_datetime(self.data['date'].max()).date()
        if end_date.date() > max_data_date:
            print(f"[WARNING] 结束日期 {end_date.date()} 超出数据范围 {max_data_date}, 将使用最近可用日期 {max_data_date}")
            end_date = datetime.combine(max_data_date, datetime.min.time())
            
        self.current_date = self.data['combined_time'].iloc[0] # timestamp
        current_date = self.current_date
        
        # 查找小于等于end_date的最近日期
        available_dates = pd.to_datetime(self.data['date'].unique())
        valid_dates = available_dates[available_dates <= pd.to_datetime(end_date)]
        if len(valid_dates) == 0:
            raise ValueError(f"没有可用的历史数据早于 {end_date.date()}")
            
        closest_date = valid_dates.max()
        if closest_date.date() != end_date.date():
            print(f"[WARNING] 使用调整后的结束日期: {closest_date.date()} (原请求: {end_date.date()})")
            
        # Get the last time of day for the closest date
        last_time = self.data[self.data['date']==closest_date.date()]['time'].iloc[-1]
        # Combine date and time properly
        end_date = datetime.combine(closest_date.date(), last_time)

        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        
        # 初始净值已在_init_equity中记录
        
        while current_date <= end_date: # 遍历日期，触发策略
            # 每月首个交易日触发定投
            if current_date.month != self.current_month:
                first_trading_day = self.get_first_trading_day_of_month(current_date)
                if first_trading_day is not None:
                    monthly_event = ScheduleEvent(
                        timestamp=first_trading_day,
                        schedule_type="MONTHLY",
                        engine=self,
                        parameters={
                            'investment_amount': self.config.monthly_investment,
                            'current_capital': self.current_capital
                        }
                    )
                    self.push_event(monthly_event)
                    self.current_month = current_date.month
                    
                    # 处理当月定投事件
                    for strategy in self.strategies:
                        if hasattr(strategy, 'on_event'):
                            strategy.on_event(monthly_event)
                        else:
                            strategy.handle_event(event = monthly_event, engine = self)
            
            
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
            
            # 只处理交易日
            if current_date in self.data.index:
                # 获取当前价格，处理空值
                current_price = self.data.loc[current_date, 'close']
                if pd.isnull(current_price):
                    self.log_error(f"获取到空价格在 {current_date}, 使用前值填充")
                    current_price = self.data['close'].shift(1).loc[current_date]
                self.current_price = current_price
                
                # 处理当日事件
                while self.event_queue:
                    event = self.event_queue.pop(0)
                    handler = self.handlers.get(type(event))
                    if handler:
                        try:
                            handler(event)
                        except Exception as e:
                            self.log_error(f"处理事件失败: {str(e)}")
                
            # 更新净值记录
            current_data = self.data[self.data['combined_time'] == current_date].iloc[0]
            self._update_equity({
                'datetime': current_date,
                'close': current_data['close']
            })
            
            # 获取下一个有效交易日 (使用combined_time进行比较)
            next_dates = self.data[self.data['combined_time'] > current_date]['combined_time']
            self.current_date = next_dates.iloc[0] if len(next_dates) > 0 else current_date + timedelta(days=1)
            current_date = self.current_date
        
        # 确保最后一天净值被记录
        self._update_equity({
            'datetime': end_date,
            'close': self.data[self.data['combined_time'] == end_date].iloc[0]['close']
        })

    def get_first_trading_day_of_month(self, date):
        """获取某个月份的第一个交易日"""
        month_start = date.replace(day=1)
        # 使用已创建的combined_time列作为索引
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = self.data['combined_time']
        
        # 获取该月所有交易日
        try:
            trading_days = self.data.loc[month_start:month_start + pd.DateOffset(months=1)].index
            return trading_days[0] if len(trading_days) > 0 else None
        except KeyError:
            # 如果指定日期不在数据范围内，返回该月第一个有效交易日
            trading_days = self.data.loc[self.data.index >= month_start].index
            return trading_days[0] if len(trading_days) > 0 else None

    def _calculate_win_rate(self) -> float:
        """计算交易胜率"""
        if not self.trades:
            return 0.0
            
        # 计算盈利交易数量
        winning_trades = 0
        for trade in self.trades:
            if trade['side'] == 'BUY':
                # 查找对应的卖出交易
                sell_trades = [t for t in self.trades 
                             if t['side'] == 'sell' 
                             and t['strategy_id'] == trade['strategy_id']
                             and t['timestamp'] > trade['timestamp']]
                if sell_trades:
                    profit = sell_trades[0]['price'] - trade['price']
                    if profit > 0:
                        winning_trades += 1
            elif trade['side'] == 'sell' and trade['strategy_id']:
                # 查找对应的买入交易
                BUY_trades = [t for t in self.trades 
                            if t['side'] == 'BUY' 
                            and t['strategy_id'] == trade['strategy_id']
                            and t['timestamp'] < trade['timestamp']]
                if BUY_trades:
                    profit = trade['price'] - BUY_trades[0]['price']
                    if profit > 0:
                        winning_trades += 1
        
        return winning_trades / len(self.trades) if self.trades else 0.0

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if self.equity_records.empty:
            return 0.0
            
        peak = self.equity_records['total_value'].max()
        trough = self.equity_records['total_value'].min()
        return (peak - trough) / peak if peak != 0 else 0.0

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

    def _update_equity(self, market_data):
        """更新净值记录"""
        # 确保数值类型正确
        if market_data['close'] is None:
            self.logger.warning(f"跳过净值更新: 收盘价为None | 时间: {market_data['datetime']}")
            return  # 如果收盘价为None，跳过更新
        try:
            close_price = float(market_data['close'])
        except (TypeError, ValueError):
            self.log_error(f"无法将收盘价转换为浮点数: {market_data['close']}")
            return
        current_capital = float(self.current_capital)
        
        # 计算持仓价值
        position_quantity = self.position_meta['quantity']
        avg_price = self.position_meta['avg_price']
        
        # 验证持仓数量
        if position_quantity == 0:
            position_value = 0
            unrealized_pnl = 0
        else:
            # 验证持仓方向
            if self.position_meta['direction'] == 0:
                self.log_error(f"持仓方向为0但持仓数量不为0: {position_quantity}")
                position_value = 0
                unrealized_pnl = 0
            else:
                position_value = position_quantity * close_price
                unrealized_pnl = (close_price - avg_price) * position_quantity
                
                # 验证计算
                if position_value < 0:
                    self.log_error(f"持仓价值为负: {position_value:.2f} | 数量: {position_quantity} | 价格: {close_price:.2f}")
                    position_value = 0
                    
                # 验证未实现盈亏
                expected_pnl = (close_price - avg_price) * position_quantity
                if abs(unrealized_pnl - expected_pnl) > 0.01:
                    self.log_error(
                        f"未实现盈亏计算错误: {unrealized_pnl:.2f} vs expected {expected_pnl:.2f} | "
                        f"数量: {position_quantity} | 价格: {close_price:.2f} | 平均成本: {avg_price:.2f}"
                    )
                    unrealized_pnl = expected_pnl
            
        total_value = current_capital + position_value
        
        # 验证总资产计算
        if total_value < 0:
            self.log_error(f"总资产为负: {total_value:.2f} | 现金: {current_capital:.2f} | 持仓价值: {position_value:.2f}")
            total_value = current_capital  # 仅保留现金部分
            
        # 记录详细计算过程
        # self.logger.debug(
        #     f"净值计算过程 | 现金: {current_capital:.2f} | "
        #     f"持仓数量: {self.position_meta['quantity']} | "
        #     f"当前价格: {close_price:.2f} | "
        #     f"平均成本: {self.position_meta['avg_price']:.2f} | "
        #     f"持仓价值: {position_value:.2f} | "
        #     f"未实现盈亏: {unrealized_pnl:.2f} | "
        #     f"总资产: {total_value:.2f}"
        # )
        
        # 确保时间戳格式一致
        timestamp = pd.to_datetime(market_data['datetime'])
        
        # 获取策略持仓
        strategy_position = sum(self.strategy_holdings.values())
        
        record = {
            'timestamp': timestamp,
            'price': close_price,
            'position': strategy_position,  # 使用策略总持仓
            'cash': current_capital,
            'total_value': total_value,
            'position_value': position_value,
            'unrealized_pnl': unrealized_pnl,
            'avg_price': self.position_meta['avg_price'],
            'position_direction': 'long' if strategy_position > 0 else 
                                 'short' if strategy_position < 0 else 'flat'
        }
        
        # 使用loc避免concat警告
        if self.equity_records.empty:
            self.equity_records = pd.DataFrame([record])
        else:
            # 检查是否已存在该时间戳的记录
            existing = self.equity_records[
                self.equity_records['timestamp'] == timestamp
            ]
            if len(existing) == 0:
                self.equity_records.loc[len(self.equity_records)] = record
            else:
                # 更新现有记录
                idx = existing.index[0]
                self.equity_records.loc[idx] = record
                
        # 记录详细的净值计算
        # self.logger.info(
        #     f"净值计算 | 时间: {timestamp} | 价格: {close_price:.2f} | "
        #     f"持仓: {self.position_meta['quantity']} | 现金: {current_capital:.2f} | "
        #     f"持仓价值: {position_value:.2f} | 总资产: {total_value:.2f} | "
        #     f"未实现盈亏: {unrealized_pnl:.2f} | 平均成本: {self.position_meta['avg_price']:.2f} | "
        #     f"持仓方向: {'多头' if self.position_meta['direction'] > 0 else '空头' if self.position_meta['direction'] < 0 else '无'}"
        # )
        
        # 如果总资产没有变化，记录警告
        # if len(self.equity_records) > 1 and total_value == self.equity_records.iloc[-2]['total_value']:
        #     self.logger.warning(
        #         f"总资产未变化 | 当前总资产: {total_value:.2f} | "
        #         f"前次总资产: {self.equity_records.iloc[-2]['total_value']:.2f}"
        #     )

    def get_historical_data(self, timestamp: datetime, lookback_days: int):
        """获取历史数据"""
        # 实现数据获取逻辑
        pass

    async def load_data(self, symbol: str):
        """从数据源加载数据，不存数据库？"""
        from core.data.baostock_source import BaostockDataSource
        ds = BaostockDataSource()
        self.data = await ds.load_data(
            symbol=symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            frequency=self.config.frequency
        )
        # 调试日志：验证加载的数据
        print(f"[DEBUG] 数据列: {self.data.columns.tolist()}")

        
        # 添加数据校验
        if 'close' not in self.data.columns:
            raise ValueError("数据缺少close字段")
        print(f"[DEBUG] 空值检查 - close列空值数量: {self.data['close'].isnull().sum()}")
        
        # 填充空值（如果存在）
        # self.data['close'].fillna(method='ffill', inplace=True)
        
        return self.data

    def create_order(self, timestamp : datetime ,symbol: str, quantity: int, side: str, price: float, strategy_id: str = None):
        """创建交易订单"""
        # 添加DEBUG日志记录订单创建
        self.logger.debug(
            f"Creating order | Symbol: {symbol} | Side: {side} | "
            f"Qty: {quantity} | Price: {price:.2f} | Strategy: {strategy_id or 'GLOBAL'}"
        )
        
        # 如果是定投买入且配置了monthly_investment，则动态计算数量
        if side == 'BUY' and self.config.monthly_investment and strategy_id:
            quantity = int(self.config.monthly_investment / price)
            if quantity <= 0:
                raise ValueError(f"计算数量无效: {quantity} (price={price}, investment={self.config.monthly_investment})")
            
        # 记录操作前状态
        prev_capital = self.current_capital
        prev_position = self.position_meta.copy()
        
        # 计算交易金额和手续费
        trade_amount = quantity * price
        commission = trade_amount * self.config.commission
        
        # 更新资金和持仓
        if side == 'BUY':
            self.current_capital -= (trade_amount + commission)
            # 添加调试日志验证资金扣除
            self.logger.debug(f"资金扣除验证 | 原金额: {prev_capital:.2f} | 扣除: {trade_amount + commission:.2f} | 新金额: {self.current_capital:.2f}")
            if self.position_meta['quantity'] * quantity < 0:  # 反向交易
                self._close_position(quantity, price)
            else:
                new_qty = self.position_meta['quantity'] + quantity
                new_avg = ((self.position_meta['avg_price'] * self.position_meta['quantity']) + 
                          (price * quantity)) / new_qty
                self.position_meta.update({
                    'quantity': new_qty,
                    'avg_price': new_avg,
                    'direction': 1 if new_qty > 0 else -1
                })
            
            if strategy_id:
                # 记录操作前持仓
                prev_strategy_holding = self.strategy_holdings.get(strategy_id, 0)
                
                # 更新策略持仓
                self.strategy_holdings[strategy_id] += quantity
                
                # 记录买入时间
                self.position_records[strategy_id] = {
                    'entry_time': self.current_date,
                    'quantity': quantity,
                    'entry_price': price
                }
                
                # 验证持仓更新
                if self.strategy_holdings[strategy_id] != prev_strategy_holding + quantity:
                    self.log_error(
                        f"策略持仓更新错误: expected={prev_strategy_holding + quantity} "
                        f"actual={self.strategy_holdings[strategy_id]}"
                    )
                    # 强制修正
                    self.strategy_holdings[strategy_id] = prev_strategy_holding + quantity
                
                # 验证全局持仓
                if self.strategy_holdings[strategy_id] != self.position_meta['quantity']:
                    self.log_error(
                        f"持仓不一致: strategy_holdings={self.strategy_holdings[strategy_id]} "
                        f"vs position_meta={self.position_meta['quantity']}"
                    )
                    # 强制同步
                    self.position_meta['quantity'] = self.strategy_holdings[strategy_id]
                
            # 记录交易日志并立即刷新
            self.logger.info(
                f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] BUY | {symbol} | Qty: {quantity} | Price: {price:.2f} | "
                f"Cost: {trade_amount:.2f} | Commission: {commission:.2f} | "
                f"Capital: {self.current_capital:.2f} | "
                f"Position: {self.position_meta['quantity']}@{self.position_meta['avg_price']:.2f} | "
                f"Strategy: {strategy_id or 'GLOBAL'}"
            )
            self.logger.handlers[0].flush()
            
        elif side == 'sell':
            # 自动修正卖出数量不超过持仓
            if strategy_id:
                available_qty = abs(self.strategy_holdings.get(strategy_id, 0))
                if quantity > available_qty:
                    self.log_error(f"修正卖出数量: {quantity}->{available_qty} (策略{strategy_id})")
                    quantity = available_qty
                
                # 检查持仓时间是否超过最大持仓天数限制
                if self.config.max_holding_days is not None and strategy_id in self.position_records:
                    holding_days = (self.current_date - self.position_records[strategy_id]['entry_time']).days
                    if holding_days < self.config.max_holding_days:
                        raise ValueError(f"持仓天数不足{self.config.max_holding_days}天，当前持仓{holding_days}天")
                
                self.strategy_holdings[strategy_id] -= quantity
                # 清除持仓记录
                if strategy_id in self.position_records:
                    del self.position_records[strategy_id]
            else:
                available_qty = abs(self.position_meta['quantity'])
                if quantity > available_qty:
                    self.log_error(f"修正卖出数量: {quantity}->{available_qty} (全局持仓)")
                    quantity = available_qty
            
            self.current_capital += (trade_amount - commission)
            if self.position_meta['quantity'] * quantity > 0:  # 同向减仓
                self.position_meta['quantity'] -= quantity
                if self.position_meta['quantity'] == 0:
                    self.position_meta.update({
                        'avg_price': 0.0,
                        'direction': 0
                    })
            else:  # 反向交易
                self._close_position(-quantity, price)
            
            # 记录交易日志并立即刷新
            self.logger.info(
                f"SELL | {symbol} | Qty: {quantity} | Price: {price:.2f} | "
                f"Proceeds: {trade_amount:.2f} | Commission: {commission:.2f} | "
                f"Capital: {self.current_capital:.2f} | "
                f"Position: {self.position_meta['quantity']}@{self.position_meta['avg_price']:.2f} | "
                f"Strategy: {strategy_id or 'GLOBAL'}"
            )
            self.logger.handlers[0].flush()
            
            
        # 触发净值更新
        self._update_equity({
            'datetime': self.current_date,
            'close': self.current_price
        })
        
        # 记录交易
        # Get position information from strategy if available
        position_info = {
            'position_size': 0,
            'position_cost': 0.0
        }
        if strategy_id:
            for strategy in self.strategies:
                if strategy.strategy_id == strategy_id:
                    position_info = {
                        'position_size': strategy.position_size,
                        'position_cost': strategy.position_cost
                    }
                    break

        # 确保仓位信息正确传递
        trade = {
            "timestamp": self.current_date if hasattr(self, 'current_date') else datetime.now(),
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "price": price,
            "amount": trade_amount,
            "commission": commission,
            "remaining_capital": self.current_capital,
            "strategy_id": strategy_id,
            "entry_price": price if side == 'BUY' else None,
            "position_size": self.position_meta['quantity'],
            "position_cost": self.position_meta['avg_price']
        }
        
        # 触发策略仓位同步
        if strategy_id:
            for strategy in self.strategies:
                if strategy.strategy_id == strategy_id:
                    strategy.update_position(
                        self.position_meta['quantity'],
                        self.position_meta['avg_price']
                    )
        self.trades.append(trade)
        # 记录详细的交易影响
        self.logger.info(
            f"交易影响 | 类型: {side} | 数量: {quantity} | 价格: {price:.2f} | "
            f"交易金额: {trade_amount:.2f} | 手续费: {commission:.2f} | "
            f"现金变化: {prev_capital:.2f} -> {self.current_capital:.2f} | "
            f"持仓变化: {prev_position['quantity']}@{prev_position['avg_price']:.2f} -> "
            f"{self.position_meta['quantity']}@{self.position_meta['avg_price']:.2f}"
        )
        
        # 确保策略ID正确传递到交易记录
        if strategy_id:
            for strategy in self.strategies:
                if strategy.strategy_id == strategy_id:
                    # strategy.on_trade_executed(trade)
                    pass
        
        # 触发持仓更新回调
        if strategy_id:
            for strategy in self.strategies:
                if strategy.strategy_id == strategy_id:
                    strategy.update_position(self.strategy_holdings[strategy_id],self.position_meta['avg_price'])

    def _sync_position(self):
        """同步持仓状态，确保position_meta和strategy_holdings一致"""
        total_strategy_holdings = sum(abs(qty) for qty in self.strategy_holdings.values())
        position_quantity = self.position_meta['quantity']
        
        # 验证持仓数量
        if abs(position_quantity) != total_strategy_holdings:
            self.log_error(
                f"持仓不一致: position_meta={position_quantity} " 
                f"vs strategy_holdings={total_strategy_holdings}"
            )
            
            # 验证持仓方向
            expected_direction = 1 if sum(self.strategy_holdings.values()) > 0 else -1
            if self.position_meta['direction'] != expected_direction:
                self.log_error(
                    f"持仓方向不一致: position_meta={self.position_meta['direction']} " 
                    f"vs expected={expected_direction}"
                )
            
            # 强制同步到position_meta
            self.position_meta.update({
                'quantity': sum(self.strategy_holdings.values()),
                'avg_price': self.position_meta['avg_price'],
                'direction': expected_direction
            })
            
            # 记录详细持仓信息
            self.logger.info(
                f"持仓同步 | 全局持仓: {self.position_meta['quantity']} | " 
                f"策略持仓: {total_strategy_holdings} | " 
                f"平均价格: {self.position_meta['avg_price']:.2f} | " 
                f"方向: {'多头' if self.position_meta['direction'] > 0 else '空头'}"
            )
            
            # 验证同步结果
            if abs(self.position_meta['quantity']) != total_strategy_holdings:
                self.log_error(
                    f"同步失败: position_meta={self.position_meta['quantity']} " 
                    f"vs strategy_holdings={total_strategy_holdings}"
                )

    def _close_position(self, qty, price):
        """处理平仓逻辑"""
        closed_value = qty * (price - self.position_meta['avg_price'])
        self.current_capital += closed_value
        self.position_meta.update({
            'quantity': self.position_meta['quantity'] + qty,
            'avg_price': 0.0,
            'direction': 0
        })
        self.logger.info(
            f"CLOSE | Qty: {qty} | Price: {price:.2f} | "
            f"P/L: {closed_value:.2f} | "
            f"Capital: {self.current_capital:.2f}"
        )
