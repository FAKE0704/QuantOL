"""策略类型 API 路由"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from src.services.strategy_service import strategy_service

router = APIRouter()


class StrategyOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None
    default_params: Optional[dict] = None


class StrategiesResponse(BaseModel):
    success: bool
    message: str
    data: List[StrategyOption] = []


@router.get("/trading", response_model=StrategiesResponse)
async def get_trading_strategies():
    """获取交易策略列表"""
    try:
        strategies = await strategy_service.get_trading_strategies()
        return StrategiesResponse(
            success=True,
            message=f"Found {len(strategies)} trading strategies",
            data=strategies
        )
    except Exception as e:
        return StrategiesResponse(
            success=False,
            message=str(e),
            data=[]
        )


@router.get("/position", response_model=StrategiesResponse)
async def get_position_strategies():
    """获取仓位策略列表"""
    try:
        strategies = await strategy_service.get_position_strategies()
        return StrategiesResponse(
            success=True,
            message=f"Found {len(strategies)} position strategies",
            data=strategies
        )
    except Exception as e:
        return StrategiesResponse(
            success=False,
            message=str(e),
            data=[]
        )
