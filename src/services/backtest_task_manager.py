"""Backtest task manager for async execution with WebSocket progress updates."""

import json
import pandas as pd
import numpy as np
from fastapi import BackgroundTasks
from datetime import datetime
import asyncio
from typing import TYPE_CHECKING, Callable, Optional, Any

from src.core.strategy.backtesting import BacktestConfig, BacktestEngine
from src.core.strategy.indicators import IndicatorService
from src.database import get_db_adapter
from src.services.backtest_state_service import backtest_state_service
from src.services.websocket_manager import websocket_manager
from src.support.log.logger import logger

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from src.api.routers.backtest import BacktestRequest


class SimpleSessionState:
    """简单的 session_state 模拟对象，用于 BacktestExecutionService"""

    def __init__(self, db_adapter):
        self.db = db_adapter
        # 不设置 indicator_service，让 BacktestExecutionService 初始化

    def get(self, key, default=None):
        """模拟 session_state.get()"""
        return getattr(self, key, default)

    def __contains__(self, key):
        """支持 'in' 操作符，只有属性存在且不为None时返回True"""
        return hasattr(self, key) and getattr(self, key, None) is not None


def convert_to_json_serializable(obj, max_depth=100):
    """将对象转换为JSON可序列化的格式"""
    if max_depth <= 0:
        return str(obj)

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        # 保存 DataFrame 的 attrs 属性，避免规则映射信息丢失
        result = {
            "__type__": "DataFrame",
            "__attrs__": getattr(obj, 'attrs', {}),
            "__data__": obj.to_dict('records')
        }
        return result
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v, max_depth - 1) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item, max_depth - 1) for item in obj]
    else:
        return obj


def to_json_string(obj):
    """将对象转换为JSON字符串，使用自定义编码器处理特殊类型"""
    class CustomEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, pd.Timestamp):
                return o.isoformat()
            elif isinstance(o, datetime):
                return o.isoformat()
            elif isinstance(o, np.integer):
                return int(o)
            elif isinstance(o, np.floating):
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

    return json.dumps(obj, cls=CustomEncoder)


class BacktestTaskManager:
    """回测任务管理器 - 处理后台异步执行并通过WebSocket推送进度"""

    def submit_backtest(self, backtest_id: str, request: Any, background_tasks: BackgroundTasks):
        """提交回测任务到后台执行"""
        # 创建回测记录
        backtest_state_service.create_backtest(backtest_id, request.model_dump())

        # 提交后台任务
        background_tasks.add_task(self._execute_backtest_async, backtest_id, request)

    async def _execute_backtest_async(self, backtest_id: str, request: Any):
        """异步执行回测的核心逻辑"""
        try:
            # 添加调试日志
            print(f"[DEBUG] 接收到的回测请求:")
            print(f"  start_date: {request.start_date} (type: {type(request.start_date)})")
            print(f"  end_date: {request.end_date} (type: {type(request.end_date)})")
            print(f"  symbols: {request.symbols}")

            # 更新状态为running
            backtest_state_service.update_status(backtest_id, "running")
            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "running", "progress": 0.0}}
            )

            # 获取数据库适配器
            db = get_db_adapter()

            # 处理策略配置
            strategy_config = request.strategy_config or {}
            strategy_type_label = strategy_config.get('type', '自定义策略')

            # 映射前端策略标签到内部策略类型
            strategy_label_to_type = {
                "月定投": "月定投",
                "自定义策略": "自定义规则",
                "移动平均线交叉": "自定义规则",
                "MACD交叉": "自定义规则",
                "RSI超买超卖": "自定义规则",
                "Martingale": "自定义规则",
            }

            internal_strategy_type = strategy_label_to_type.get(strategy_type_label, "自定义规则")

            # 构建默认策略配置
            default_strategy = {
                'buy_rule': strategy_config.get('buy_rule', ''),
                'sell_rule': strategy_config.get('sell_rule', ''),
                'open_rule': strategy_config.get('open_rule', ''),
                'close_rule': strategy_config.get('close_rule', ''),
            }

            # 如果没有提供规则，使用预设规则
            if not any([default_strategy['buy_rule'], default_strategy['sell_rule'],
                       default_strategy['open_rule'], default_strategy['close_rule']]):
                preset_rules = {
                    "移动平均线交叉": {
                        "open_rule": "(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))",
                        "close_rule": "(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))",
                    },
                    "MACD交叉": {
                        "open_rule": "MACD(close, 12, 26, 9) > MACD_SIGNAL(close, 12, 26, 9)",
                        "close_rule": "MACD(close, 12, 26, 9) < MACD_SIGNAL(close, 12, 26, 9)",
                    },
                    "RSI超买超卖": {
                        "open_rule": "(REF(RSI(close,5), 1) < 30) & (RSI(close,5) >= 30)",
                        "close_rule": "(REF(RSI(close,5), 1) >= 60) & (RSI(close,5) < 60)",
                    },
                    "Martingale": {
                        "open_rule": "(close < REF(SMA(close,5), 1)) & (close > SMA(close,5))",
                        "close_rule": "(close - (COST/POSITION))/(COST/POSITION) * 100 >= 5",
                        "buy_rule": "(close - (COST/POSITION))/(COST/POSITION) * 100 <= -5",
                    },
                }
                if strategy_type_label in preset_rules:
                    default_strategy.update(preset_rules[strategy_type_label])

            # 创建回测配置
            config = BacktestConfig(
                start_date=request.start_date,
                end_date=request.end_date,
                target_symbol=request.symbols[0],
                target_symbols=request.symbols,
                frequency=request.frequency,
                initial_capital=request.initial_capital,
                commission_rate=request.commission_rate,
                slippage=request.slippage,
                min_lot_size=request.min_lot_size,
                position_strategy_type=request.position_strategy,
                position_strategy_params=request.position_params,
                strategy_type=internal_strategy_type,
                default_strategy=default_strategy,
            )

            print(f"[DEBUG] BacktestConfig创建完成:")
            print(f"  strategy_type: {config.strategy_type}")
            print(f"  default_strategy: {config.default_strategy}")

            # 加载数据
            if config.is_multi_symbol():
                data = {}
                for symbol in config.get_symbols():
                    data[symbol] = await db.load_stock_data(symbol, config.start_date, config.end_date, config.frequency)
            else:
                data = await db.load_stock_data(config.target_symbol, config.start_date, config.end_date, config.frequency)

            # 定义进度回调函数（通过WebSocket推送）
            total_steps = len(data) if not config.is_multi_symbol() else sum(len(d) for d in data.values())
            last_broadcast_progress = -1

            def progress_callback(current_index: int, current_time, total: int = total_steps):
                nonlocal last_broadcast_progress
                progress = min(current_index / total, 1.0)

                # 降低阈值，让进度条更平滑（0.5%更新一次）
                if progress - last_broadcast_progress >= 0.005 or progress >= 1.0:
                    last_broadcast_progress = progress
                    backtest_state_service.update_status(
                        backtest_id,
                        "running",
                        progress=progress,
                        current_time=str(current_time)
                    )
                    # 异步推送进度（在后台任务中安全）
                    asyncio.create_task(websocket_manager.broadcast_progress(
                        backtest_id,
                        {
                            "type": "status",
                            "data": {
                                "status": "running",
                                "progress": progress,
                                "current_time": str(current_time),
                            }
                        }
                    ))

            # 使用 BacktestExecutionService 初始化引擎（会自动创建和注册策略）
            from src.frontend.backtest_execution_service import BacktestExecutionService

            # 创建简单的 session_state 模拟对象
            session_state = SimpleSessionState(db)

            # 创建 BacktestExecutionService 实例
            execution_service = BacktestExecutionService(session_state)

            # 初始化引擎（会自动创建和注册策略）
            engine = execution_service.initialize_engine(config, data, backtest_id=backtest_id)
            engine.progress_callback = progress_callback

            print(f"[DEBUG] 引擎初始化完成，已注册策略数量: {len(engine.strategies)}")

            start_date = datetime.strptime(config.start_date, "%Y%m%d")
            end_date = datetime.strptime(config.end_date, "%Y%m%d")

            if config.is_multi_symbol():
                results = await engine.run_multi_symbol(start_date, end_date)
            else:
                await engine.run(start_date, end_date)
                results = engine.get_results()

            # 更新为完成状态
            backtest_state_service.update_status(
                backtest_id,
                "completed",
                progress=1.0,
                result=results
            )
            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "completed", "progress": 1.0}}
            )
            logger.info(f"回测完成: {backtest_id}")

        except Exception as e:
            logger.error(f"回测执行失败: {backtest_id}, 错误: {e}")
            backtest_state_service.update_status(
                backtest_id,
                "failed",
                error=str(e)
            )
            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "failed", "error": str(e)}}
            )


# 全局单例
backtest_task_manager = BacktestTaskManager()
