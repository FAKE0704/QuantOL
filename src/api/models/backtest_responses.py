"""回测响应模型

包含回测相关的响应 Pydantic 模型。
"""
from typing import Optional
from pydantic import BaseModel


class BacktestResult(BaseModel):
    """回测结果模型"""

    backtest_id: str
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    completed_at: Optional[str] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None


class BacktestConfigResponse(BaseModel):
    """回测配置响应模型"""

    success: bool
    message: str
    data: Optional[dict] = None


class BacktestConfigListResponse(BaseModel):
    """回测配置列表响应模型"""

    success: bool
    message: str
    data: Optional[list[dict]] = None


class CustomStrategyResponse(BaseModel):
    """自定义策略响应模型"""

    success: bool
    message: str
    data: Optional[dict] = None


class CustomStrategyListResponse(BaseModel):
    """自定义策略列表响应模型"""

    success: bool
    message: str
    data: Optional[list[dict]] = None


class RuleValidationResponse(BaseModel):
    """规则验证响应模型"""

    success: bool
    message: str
    data: Optional[dict] = None
