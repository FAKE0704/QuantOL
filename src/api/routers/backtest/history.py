"""回测历史路由"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status

from src.api.models.common import BacktestListResponse
from src.api.models.backtest_responses import BacktestResult
from src.services.backtest_task_service import backtest_task_service
from src.api.deps import get_current_user

router = APIRouter()


@router.get("/history", response_model=BacktestListResponse)
async def get_backtest_history(
    limit: int = 5,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get current user's backtest history from database."""
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        from src.support.log.logger import logger
        logger.info(f"[/history] user_id={user_id}, current_user={current_user}")

        tasks = await backtest_task_service.list_user_backtests(
            user_id=user_id,
            status=status_filter,
            limit=min(limit, 10),
        )
        logger.info(f"[/history] Found {len(tasks)} backtests for user_id={user_id}")

        results = []
        for task in tasks:
            summary = task.get("result_summary", {})
            results.append(
                BacktestResult(
                    backtest_id=task["backtest_id"],
                    status=task["status"],
                    created_at=task["created_at"],
                    completed_at=task["completed_at"],
                    total_return=summary.get("summary", {}).get("total_return"),
                    sharpe_ratio=summary.get("performance_metrics", {}).get("sharpe_ratio"),
                    max_drawdown=summary.get("performance_metrics", {}).get("max_drawdown_pct"),
                    win_rate=summary.get("summary", {}).get("win_rate"),
                )
            )

        return BacktestListResponse(
            success=True,
            message=f"Found {len(results)} historical backtests",
            data=results,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest history: {str(e)}",
        )
