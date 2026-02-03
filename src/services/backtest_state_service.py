"""Backtest state storage service using Redis for persistent storage."""

import json
from datetime import datetime
from typing import Optional, Dict, Any
import redis
import pandas as pd
from src.support.log.logger import logger
from src.utils.encoders import QuantOLEncoder


class BacktestStateService:
    """回测状态存储服务 - 使用Redis持久化存储"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """初始化Redis连接"""
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = "backtest:"

    def _make_key(self, backtest_id: str) -> str:
        """生成Redis键"""
        return f"{self.key_prefix}{backtest_id}"

    def create_backtest(
        self,
        backtest_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """创建新的回测记录"""
        try:
            data = {
                "id": backtest_id,
                "status": "pending",
                "progress": "0.0",
                "current_time": "",  # 空字符串替代None
                "config": json.dumps(config),
                "created_at": datetime.utcnow().isoformat(),
                "result": "",  # 空字符串替代None
                "error": "",  # 空字符串替代None
            }
            self.redis_client.hset(
                self._make_key(backtest_id),
                mapping=data
            )
            return True
        except Exception as e:
            logger.error(f"创建回测记录失败: {e}")
            return False

    def update_status(
        self,
        backtest_id: str,
        status: str,
        progress: float = None,
        current_time: str = None,
        result: Any = None,
        error: str = None
    ) -> bool:
        """更新回测状态"""
        try:
            updates = {"status": status}
            if progress is not None:
                updates["progress"] = str(progress)
            if current_time is not None:
                updates["current_time"] = current_time
            if result is not None:
                # 使用QuantOLEncoder处理特殊类型
                updates["result"] = json.dumps(result, cls=QuantOLEncoder)
            if error is not None:
                updates["error"] = error

            if status == "running" and "started_at" not in self.get_backtest(backtest_id, {}):
                updates["started_at"] = datetime.utcnow().isoformat()
            elif status in ("completed", "failed"):
                updates["completed_at"] = datetime.utcnow().isoformat()

            self.redis_client.hset(
                self._make_key(backtest_id),
                mapping=updates
            )
            return True
        except Exception as e:
            logger.error(f"更新回测状态失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _restore_dataframe_attrs(self, obj: Any) -> Any:
        """递归恢复DataFrame的attrs属性"""
        if isinstance(obj, dict):
            # 检查是否是DataFrame序列化后的格式
            if obj.get("__type__") == "DataFrame":
                # 从序列化数据恢复DataFrame
                df = pd.DataFrame(obj.get("__data__", []))
                # 恢复attrs属性
                attrs = obj.get("__attrs__", {})
                if attrs:
                    df.attrs = attrs
                return df
            # 递归处理字典的值
            return {k: self._restore_dataframe_attrs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # 递归处理列表的元素
            return [self._restore_dataframe_attrs(item) for item in obj]
        else:
            return obj

    def get_backtest(self, backtest_id: str, default: Any = None, restore_dataframe: bool = False) -> Optional[Dict[str, Any]]:
        """获取回测记录

        Args:
            backtest_id: 回测ID
            default: 默认返回值
            restore_dataframe: 是否将DataFrame格式的字典恢复为pandas.DataFrame对象
                              API返回时应为False（保持字典格式），Streamlit使用时应为True
        """
        try:
            data = self.redis_client.hgetall(self._make_key(backtest_id))
            if not data:
                return default

            # 转换类型
            result = {}
            for key, value in data.items():
                if key in ("progress",):
                    result[key] = float(value)
                elif key in ("config", "result"):
                    parsed = json.loads(value) if value else None
                    # 根据参数决定是否恢复DataFrame对象
                    if restore_dataframe:
                        result[key] = self._restore_dataframe_attrs(parsed) if parsed else None
                    else:
                        result[key] = parsed  # 保持原始格式（包含__type__和__data__的字典）
                else:
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"获取回测记录失败: {e}")
            return default

    def delete_backtest(self, backtest_id: str) -> bool:
        """删除回测记录"""
        try:
            self.redis_client.delete(self._make_key(backtest_id))
            return True
        except Exception as e:
            logger.error(f"删除回测记录失败: {e}")
            return False

    def list_backtests(self, limit: int = 50) -> list:
        """列出所有回测记录"""
        try:
            keys = self.redis_client.keys(f"{self.key_prefix}*")
            backtests = []
            for key in keys[:limit]:
                data = self.redis_client.hgetall(key)
                if data:
                    backtests.append({
                        "id": data.get("id", key.split(":")[-1]),
                        "status": data.get("status", "unknown"),
                        "created_at": data.get("created_at"),
                    })
            return sorted(backtests, key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"列出回测记录失败: {e}")
            return []


# 全局单例
backtest_state_service = BacktestStateService()
