"""API 模型包

包含所有 Pydantic 请求/响应模型。
"""
from .common import (
    BacktestResponse,
    BacktestListResponse,
)
from .backtest_requests import (
    RebalancePeriodConfig,
    BacktestRequest,
    BacktestConfigCreate,
    BacktestConfigUpdate,
    CustomStrategyCreate,
    CustomStrategyUpdate,
    RuleValidationRequest,
)
from .backtest_responses import (
    BacktestResult,
    BacktestConfigResponse,
    BacktestConfigListResponse,
    CustomStrategyResponse,
    CustomStrategyListResponse,
    RuleValidationResponse,
)

__all__ = [
    # Common
    'BacktestResponse',
    'BacktestListResponse',
    # Requests
    'RebalancePeriodConfig',
    'BacktestRequest',
    'BacktestConfigCreate',
    'BacktestConfigUpdate',
    'CustomStrategyCreate',
    'CustomStrategyUpdate',
    'RuleValidationRequest',
    # Responses
    'BacktestResult',
    'BacktestConfigResponse',
    'BacktestConfigListResponse',
    'CustomStrategyResponse',
    'CustomStrategyListResponse',
    'RuleValidationResponse',
]
