"""Backtest 路由子包

组合所有子路由，提供完整的回测API。
"""
from fastapi import APIRouter
from .execution import router as execution_router
from .results import router as results_router
from .configs import router as configs_router
from .custom_strategies import router as custom_strategies_router
from .logs import router as logs_router

# 创建主路由器组合所有子路由
router = APIRouter()

router.include_router(execution_router, tags=["backtest"])
router.include_router(results_router, tags=["backtest"])
router.include_router(configs_router, tags=["backtest"])
router.include_router(custom_strategies_router, tags=["backtest"])
router.include_router(logs_router, tags=["backtest"])

__all__ = ['router']
