"""执行端点路由

处理回测执行相关的API端点。
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends

from src.api.models.backtest_requests import BacktestRequest
from src.api.models.common import BacktestResponse
from src.services.backtest_task_manager import backtest_task_manager
from src.api.deps import get_current_user

router = APIRouter()


@router.post(
    "/run",
    response_model=BacktestResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """运行回测

    Args:
        request: 回测配置
        background_tasks: FastAPI 后台任务
        current_user: 当前认证用户

    Returns:
        包含 backtest_id 的响应
    """
    try:
        # 从token获取user_id
        user_id = current_user.get("user_id", 1)

        # 测试日志
        import logging
        logging.warning(f"[/run] TEST LOG - user_id={user_id}")

        # 导入logger（与history.py相同的方式）
        from src.support.log.logger import logger
        logger.info(f"[/run] user_id={user_id}, current_user={current_user}")

        # 生成唯一的回测ID
        backtest_id = f"bt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"[/run] Generated backtest_id={backtest_id}")

        # 提交到后台任务管理器
        await backtest_task_manager.submit_backtest(
            backtest_id, request, background_tasks, user_id
        )

        return BacktestResponse(
            success=True,
            message=f"Backtest {backtest_id} started. "
                    f"Connect via WebSocket for progress updates.",
            data={"backtest_id": backtest_id},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start backtest: {str(e)}",
        )
