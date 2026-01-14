"""WebSocket router for real-time backtest progress updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.services.websocket_manager import websocket_manager
from src.services.backtest_state_service import backtest_state_service
from src.support.log.logger import logger

router = APIRouter()


@router.websocket("/ws/backtest/{backtest_id}")
async def websocket_backtest_progress(
    websocket: WebSocket,
    backtest_id: str,
    token: str = Query(...)
):
    """WebSocket端点 - 实时推送回测进度"""
    # TODO: 验证token有效性
    await websocket_manager.connect(websocket, backtest_id)

    try:
        # 发送当前状态
        current_status = backtest_state_service.get_backtest(backtest_id)
        if current_status:
            await websocket_manager.send_personal_message({
                "type": "status",
                "data": current_status
            }, websocket)

        # 保持连接并处理客户端消息
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息（如心跳、取消等）
            logger.debug(f"收到WebSocket消息: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket断开: backtest_id={backtest_id}")
        websocket_manager.disconnect(websocket, backtest_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        websocket_manager.disconnect(websocket, backtest_id)
        raise
