"""日志端点路由

处理回测日志查询相关的API端点。
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from src.api.models.common import BacktestResponse
from src.services.backtest_task_service import backtest_task_service
from src.api.utils import filter_result_summary

router = APIRouter()


@router.get("/{backtest_id}/logs", response_model=BacktestResponse)
async def get_backtest_logs(
    backtest_id: str,
    lines: Optional[int] = 100
):
    """获取回测日志

    Args:
        backtest_id: 回测ID
        lines: 返回的日志行数（默认100）

    Returns:
        包含日志内容的响应
    """
    try:
        # 获取回测状态
        backtest_data = await backtest_task_service.get_backtest_task(backtest_id)

        if not backtest_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        # 获取日志（这里简化处理，实际可能需要从日志文件读取）
        logs = backtest_data.get("logs", [])
        if lines and len(logs) > lines:
            logs = logs[-lines:]

        return BacktestResponse(
            success=True,
            message="Logs retrieved successfully",
            data={
                "backtest_id": backtest_id,
                "logs": logs,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}",
        )
