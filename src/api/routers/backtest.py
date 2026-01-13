"""Backtest router for FastAPI.

Provides RESTful API endpoints for backtesting:
- POST /api/backtest/run - Run a backtest
- GET /api/backtest/results/{backtest_id} - Get backtest results
- GET /api/backtest/list - List all backtests
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from src.database import get_db_adapter

# Router
router = APIRouter()

# Pydantic models


class BacktestRequest(BaseModel):
    """Backtest request model."""

    # Date config
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD
    frequency: str

    # Stock selection
    symbols: list[str]

    # Basic config
    initial_capital: float
    commission_rate: float
    slippage: float
    min_lot_size: int

    # Position strategy
    position_strategy: str  # "fixed_percent", "kelly", "martingale"
    position_params: dict

    # Strategy config (rules, signals, etc.)
    strategy_config: Optional[dict] = None


class BacktestResponse(BaseModel):
    """Backtest response model."""

    success: bool
    message: str
    data: Optional[dict] = None


class BacktestResult(BaseModel):
    """Backtest result model."""

    backtest_id: str
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    completed_at: Optional[str] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None


class BacktestListResponse(BaseModel):
    """Backtest list response model."""

    success: bool
    message: str
    data: Optional[list[BacktestResult]] = None


# In-memory storage for backtests (replace with database in production)
_backtests: dict[str, dict] = {}


# Endpoints


@router.post("/run", response_model=BacktestResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(request: BacktestRequest):
    """Run a backtest with the given configuration.

    Args:
        request: Backtest configuration

    Returns:
        Backtest response with backtest_id
    """
    try:
        # Generate unique backtest ID
        backtest_id = f"bt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Store backtest request
        _backtests[backtest_id] = {
            "id": backtest_id,
            "status": "pending",
            "config": request.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
        }

        # TODO: Execute backtest asynchronously
        # For now, just return the backtest_id
        # In production, this should:
        # 1. Create a BacktestConfig from the request
        # 2. Initialize a BacktestEngine with the config
        # 3. Run the backtest
        # 4. Store results in database

        return BacktestResponse(
            success=True,
            message=f"Backtest {backtest_id} queued for execution",
            data={"backtest_id": backtest_id},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue backtest: {str(e)}",
        )


@router.get("/results/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_results(backtest_id: str):
    """Get results for a specific backtest.

    Args:
        backtest_id: Backtest ID

    Returns:
        Backtest results response
    """
    try:
        if backtest_id not in _backtests:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found",
            )

        backtest = _backtests[backtest_id]

        return BacktestResponse(
            success=True,
            message="Backtest found",
            data=backtest,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest results: {str(e)}",
        )


@router.get("/list", response_model=BacktestListResponse)
async def list_backtests(
    limit: int = 50,
    offset: int = 0,
):
    """List all backtests.

    Args:
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        Backtest list response
    """
    try:
        # Get backtests sorted by creation date
        backtest_list = sorted(
            _backtests.values(),
            key=lambda x: x["created_at"],
            reverse=True,
        )

        # Apply pagination
        paginated_list = backtest_list[offset : offset + limit]

        # Convert to response format
        results = [
            BacktestResult(
                backtest_id=bt["id"],
                status=bt["status"],
                created_at=bt["created_at"],
                completed_at=bt.get("completed_at"),
                total_return=bt.get("result", {}).get("total_return"),
                sharpe_ratio=bt.get("result", {}).get("sharpe_ratio"),
                max_drawdown=bt.get("result", {}).get("max_drawdown"),
                win_rate=bt.get("result", {}).get("win_rate"),
            )
            for bt in paginated_list
        ]

        return BacktestListResponse(
            success=True,
            message=f"Found {len(results)} backtests",
            data=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backtests: {str(e)}",
        )
