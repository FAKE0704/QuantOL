"""结果端点路由

处理回测结果查询和管理相关的API端点。
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.models.common import BacktestResponse, BacktestListResponse
from src.services.backtest_task_service import backtest_task_service
from src.services.backtest_state_service import backtest_state_service
from src.api.utils import filter_result_summary, stream_json_response

router = APIRouter()


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """获取回测结果

    使用流式响应处理大型结果集，避免 ERR_CONTENT_LENGTH_MISMATCH 错误。

    Args:
        backtest_id: 回测ID

    Returns:
        包含完整回测结果的流式JSON响应
    """
    try:
        # 从状态服务获取结果
        result_data = await backtest_state_service.get_result(backtest_id)

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        return StreamingResponse(
            stream_json_response(result_data),
            media_type="application/json"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve results: {str(e)}",
        )


@router.get("/list", response_model=BacktestListResponse)
async def list_backtests(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None
):
    """列出所有回测

    Args:
        limit: 返回数量限制
        offset: 偏移量
        status_filter: 状态过滤（pending, running, completed, failed）

    Returns:
        回测列表响应
    """
    try:
        # 从任务服务获取回测列表
        backtests = await backtest_task_service.list_backtests(
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )

        return BacktestListResponse(
            success=True,
            message=f"Retrieved {len(backtests)} backtests",
            data=backtests
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backtests: {str(e)}",
        )


@router.get("/{backtest_id}/status", response_model=BacktestResponse)
async def get_backtest_status(backtest_id: str):
    """获取回测状态

    返回回测的当前状态和摘要信息（不包含完整结果）。

    Args:
        backtest_id: 回测ID

    Returns:
        包含回测状态的响应
    """
    try:
        # 从状态服务获取状态
        status_data = await backtest_state_service.get_status(backtest_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        # 过滤结果摘要以避免大型响应
        result_summary = status_data.get("result_summary")
        if result_summary:
            status_data["result_summary"] = filter_result_summary(result_summary)

        return BacktestResponse(
            success=True,
            message="Status retrieved successfully",
            data=status_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve status: {str(e)}",
        )


@router.get("/history", response_model=BacktestListResponse)
async def get_backtest_history(
    limit: int = 20,
    offset: int = 0
):
    """获取回测历史

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        回测历史响应
    """
    try:
        # 从任务服务获取历史记录（已完成/失败的回测）
        history = await backtest_task_service.list_backtests(
            limit=limit,
            offset=offset,
            status_filter=None  # 获取所有状态
        )

        # 过滤出已完成的回测
        completed_history = [
            bt for bt in history
            if bt.get("status") in ["completed", "failed"]
        ]

        return BacktestListResponse(
            success=True,
            message=f"Retrieved {len(completed_history)} historical backtests",
            data=completed_history
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}",
        )


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_detail(backtest_id: str):
    """获取回测详情

    Args:
        backtest_id: 回测ID

    Returns:
        包含回测详情的响应
    """
    try:
        # 从任务服务获取详情
        detail = await backtest_task_service.get_backtest(backtest_id)

        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        return BacktestResponse(
            success=True,
            message="Detail retrieved successfully",
            data=detail
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve detail: {str(e)}",
        )


@router.delete("/{backtest_id}", response_model=BacktestResponse)
async def delete_backtest(backtest_id: str):
    """删除回测

    Args:
        backtest_id: 回测ID

    Returns:
        删除结果响应
    """
    try:
        # 从任务服务删除
        success = await backtest_task_service.delete_backtest(backtest_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        return BacktestResponse(
            success=True,
            message=f"Backtest {backtest_id} deleted successfully",
            data={"backtest_id": backtest_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backtest: {str(e)}",
        )
