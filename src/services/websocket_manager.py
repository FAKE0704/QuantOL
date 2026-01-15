"""WebSocket connection manager for real-time backtest progress updates."""

from typing import Dict, Set
from fastapi import WebSocket
from src.support.log.logger import logger
import json
import pandas as pd
import numpy as np
from datetime import datetime


class CustomEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理pandas和numpy类型"""
    def default(self, o):
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        elif isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            # 处理 NaN 和 Inf，转换为 None
            if np.isnan(o) or np.isinf(o):
                return None
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        elif isinstance(o, pd.DataFrame):
            # 保存 DataFrame 的 attrs 属性，避免规则映射信息丢失
            result = {
                "__type__": "DataFrame",
                "__attrs__": getattr(o, 'attrs', {}),
                "__data__": o.to_dict('records')
            }
            return result
        elif isinstance(o, pd.Series):
            return o.tolist()
        return super().default(o)

    def iterencode(self, o, _one_shot=False):
        """重写 iterencode 以处理 NaN 值"""
        # 首先递归处理 NaN 值
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(v) for v in obj]
            elif isinstance(obj, (float, np.floating)):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return obj
            return obj

        cleaned_obj = clean_nan(o)
        return super().iterencode(cleaned_obj, _one_shot)


class WebSocketManager:
    """WebSocket连接管理器 - 用于实时推送回测进度"""

    def __init__(self):
        # backtest_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, backtest_id: str):
        """连接WebSocket并订阅回测进度"""
        await websocket.accept()
        if backtest_id not in self.active_connections:
            self.active_connections[backtest_id] = set()
        self.active_connections[backtest_id].add(websocket)
        logger.info(f"WebSocket连接建立: backtest_id={backtest_id}")

    def disconnect(self, websocket: WebSocket, backtest_id: str):
        """断开WebSocket连接"""
        if backtest_id in self.active_connections:
            self.active_connections[backtest_id].discard(websocket)
            if not self.active_connections[backtest_id]:
                del self.active_connections[backtest_id]
        logger.info(f"WebSocket连接断开: backtest_id={backtest_id}")

    async def broadcast_progress(self, backtest_id: str, data: dict):
        """向订阅该回测的所有连接广播进度更新"""
        if backtest_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[backtest_id]:
            try:
                # 使用自定义编码器序列化数据
                json_data = json.dumps(data, cls=CustomEncoder)
                await connection.send_text(json_data)
            except Exception as e:
                logger.error(f"发送进度更新失败: {e}")
                disconnected.add(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn, backtest_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """向单个连接发送消息"""
        try:
            # 使用自定义编码器序列化数据
            json_data = json.dumps(message, cls=CustomEncoder)
            await websocket.send_text(json_data)
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")


# 全局单例
websocket_manager = WebSocketManager()
