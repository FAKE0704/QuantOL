"""Backtest 路由子包

组合所有子路由，提供完整的回测API。

重要：特定路径路由（如 /configs, /custom-strategies）必须在通配符路由（如 /{backtest_id}）之前注册！
"""
from fastapi import APIRouter
from .execution import router as execution_router
from .results import router as results_router
from .configs import router as configs_router
from .custom_strategies import router as custom_strategies_router
from .logs import router as logs_router
from .history import router as history_router

# 创建主路由器组合所有子路由
router = APIRouter()

# 特定路径路由必须先注册（避免被 /{backtest_id} 通配符拦截）
router.include_router(configs_router, tags=["backtest"])
router.include_router(custom_strategies_router, tags=["backtest"])
router.include_router(execution_router, tags=["backtest"])
router.include_router(logs_router, tags=["backtest"])
router.include_router(history_router, tags=["backtest"])
# 通配符路由必须最后注册
router.include_router(results_router, tags=["backtest"])

__all__ = ['router']
