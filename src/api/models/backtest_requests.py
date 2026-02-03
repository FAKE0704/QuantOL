"""回测请求模型

包含回测相关的请求 Pydantic 模型。
"""
from typing import Optional
from pydantic import BaseModel


class RebalancePeriodConfig(BaseModel):
    """再平衡周期配置"""
    mode: str = "disabled"  # "trading_days", "calendar_rule", "disabled"
    trading_days_interval: Optional[int] = None
    calendar_frequency: Optional[str] = None  # "weekly", "monthly", "quarterly", "yearly"
    calendar_day: Optional[int] = None
    calendar_month: Optional[int] = None
    min_interval_days: Optional[int] = 0
    allow_first_rebalance: bool = True


class BacktestRequest(BaseModel):
    """回测请求模型"""

    # 日期配置
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD
    frequency: str

    # 标的选择
    symbols: list[str]

    # 基本配置
    initial_capital: float
    commission_rate: float
    slippage: float
    min_lot_size: int

    # 仓位策略
    position_strategy: str  # "fixed_percent", "kelly", "martingale"
    position_params: dict

    # 策略配置（规则、信号等）
    strategy_config: Optional[dict] = None

    # 再平衡周期配置
    rebalance_period: Optional[RebalancePeriodConfig] = None


class BacktestConfigCreate(BaseModel):
    """回测配置创建模型"""

    name: str
    description: Optional[str] = None
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD
    frequency: str
    symbols: list[str]
    initial_capital: float
    commission_rate: float
    slippage: float
    min_lot_size: int
    position_strategy: str
    position_params: dict
    trading_strategy: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None
    is_default: bool = False


class BacktestConfigUpdate(BaseModel):
    """回测配置更新模型"""

    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[str] = None
    symbols: Optional[list[str]] = None
    initial_capital: Optional[float] = None
    commission_rate: Optional[float] = None
    slippage: Optional[float] = None
    min_lot_size: Optional[int] = None
    position_strategy: Optional[str] = None
    position_params: Optional[dict] = None
    trading_strategy: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None
    is_default: Optional[bool] = None


class CustomStrategyCreate(BaseModel):
    """自定义策略创建模型"""

    strategy_key: str
    label: str
    open_rule: str
    close_rule: str
    buy_rule: str
    sell_rule: str


class CustomStrategyUpdate(BaseModel):
    """自定义策略更新模型"""

    label: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None


class RuleValidationRequest(BaseModel):
    """规则验证请求模型"""

    rule: str
