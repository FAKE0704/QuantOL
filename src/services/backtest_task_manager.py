"""Backtest task manager for async execution with WebSocket progress updates."""

import pandas as pd
from fastapi import BackgroundTasks
from datetime import datetime
import asyncio
from typing import TYPE_CHECKING, Any

from src.core.strategy.backtesting import BacktestConfig
from src.core.backtest import BacktestEngine
from src.core.strategy.indicators import IndicatorService
from src.database import get_db_adapter
from src.utils.encoders import to_json_string, convert_to_json_serializable
from src.utils.strategy_registry import StrategyRegistry
from src.services.backtest_state_service import backtest_state_service
from src.services.backtest_task_service import backtest_task_service
from src.services.websocket_manager import websocket_manager
from src.support.log.logger import logger

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from src.api.models.backtest_requests import BacktestRequest


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


class BacktestTaskManager:
    """回测任务管理器 - 处理后台异步执行并通过WebSocket推送进度"""

    async def submit_backtest(self, backtest_id: str, request: Any, background_tasks: BackgroundTasks, user_id: int = 1):
        """提交回测任务到后台执行"""
        logger.info(f"[submit_backtest] Starting submission for backtest_id={backtest_id}, user_id={user_id}")

        # 创建回测记录 (Redis)
        backtest_state_service.create_backtest(backtest_id, request.model_dump())

        # 创建回测任务记录 (数据库) - 等待创建完成，确保历史记录能立即显示
        logger.info(f"[submit_backtest] Creating DB task for backtest_id={backtest_id}, user_id={user_id}")
        result = await self._create_db_task(backtest_id, user_id, request.model_dump())
        logger.info(f"[submit_backtest] DB task creation result={result} for backtest_id={backtest_id}")

        # 提交后台任务
        background_tasks.add_task(self._execute_backtest_async, backtest_id, request, user_id)

    async def _create_db_task(self, backtest_id: str, user_id: int, config: dict):
        """Create database task record"""
        try:
            logger.info(f"[_create_db_task] Starting for backtest_id={backtest_id}, user_id={user_id}")
            # Generate log file path
            log_file_path = f"src/logs/backtests/{backtest_id}.log"

            result = await backtest_task_service.create_backtest_task(
                backtest_id=backtest_id,
                user_id=user_id,
                config=config,
                log_file_path=log_file_path,
            )
            logger.info(f"[_create_db_task] Result={result} for backtest_id={backtest_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create DB task for {backtest_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _execute_backtest_async(self, backtest_id: str, request: Any, user_id: int = 1):
        """异步执行回测的核心逻辑"""
        try:
            # 添加调试日志
            logger.debug(f"接收到的回测请求:")
            logger.debug(f"  start_date: {request.start_date} (type: {type(request.start_date)})")
            logger.debug(f"  end_date: {request.end_date} (type: {type(request.end_date)})")
            logger.debug(f"  symbols: {request.symbols}")

            # 更新状态为running (Redis + Database)
            backtest_state_service.update_status(backtest_id, "running")
            await backtest_task_service.update_backtest_task(backtest_id, status="running")

            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "running", "progress": 0.0}}
            )

            # 获取数据库适配器
            db = get_db_adapter()
            logger.debug(f"获取到的数据库适配器: {db}")
            logger.debug(f"数据库适配器类型: {type(db)}")

            # 处理策略配置
            strategy_config = request.strategy_config or {}
            if 'type' not in strategy_config:
                raise ValueError(
                    "策略配置中缺少 'type' 字段。请指定策略类型。"
                )
            strategy_type_label = strategy_config['type']

            # 使用 StrategyRegistry 映射前端策略标签到内部策略类型
            internal_strategy_type = StrategyRegistry.get_internal_strategy_type(strategy_type_label)

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
                preset_rules = StrategyRegistry.get_preset_rules(strategy_type_label)
                default_strategy.update(preset_rules)

            # 处理调仓周期配置
            rebalance_period_mode = "disabled"
            rebalance_period_params = {}
            if request.rebalance_period:
                rp = request.rebalance_period
                rebalance_period_mode = rp.mode
                if rp.trading_days_interval:
                    rebalance_period_params["interval"] = rp.trading_days_interval
                if rp.calendar_frequency:
                    rebalance_period_params["frequency"] = rp.calendar_frequency
                if rp.calendar_day:
                    rebalance_period_params["day"] = rp.calendar_day
                if rp.calendar_month:
                    rebalance_period_params["month"] = rp.calendar_month
                if rp.min_interval_days:
                    rebalance_period_params["min_interval_days"] = rp.min_interval_days
                rebalance_period_params["allow_first_rebalance"] = rp.allow_first_rebalance

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
                rebalance_period_mode=rebalance_period_mode,
                rebalance_period_params=rebalance_period_params,
            )

            logger.debug(f"BacktestConfig创建完成:")
            logger.debug(f"  strategy_type: {config.strategy_type}")
            logger.debug(f"  default_strategy: {config.default_strategy}")

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

            async def progress_callback(current_index: int, current_time, total: int = total_steps):
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
                    # 异步推送进度
                    await websocket_manager.broadcast_progress(
                        backtest_id,
                        {
                            "type": "status",
                            "data": {
                                "status": "running",
                                "progress": progress,
                                "current_time": str(current_time),
                            }
                        }
                    )

            # 使用 BacktestExecutionService 初始化引擎（会自动创建和注册策略）
            from src.frontend.backtest_execution_service import BacktestExecutionService

            # 创建简单的 session_state 模拟对象
            session_state = SimpleSessionState(db)

            # 创建 BacktestExecutionService 实例
            execution_service = BacktestExecutionService(session_state)

            # 初始化引擎（会自动创建和注册策略）
            engine = execution_service.initialize_engine(config, data, backtest_id=backtest_id)
            engine.progress_callback = progress_callback

            logger.debug(f"引擎初始化完成，已注册策略数量: {len(engine.strategies)}")

            start_date = datetime.strptime(config.start_date, "%Y%m%d")
            end_date = datetime.strptime(config.end_date, "%Y%m%d")

            # 统一使用run方法执行回测（单标的和多标的都支持）
            await engine.run(start_date, end_date)
            results = engine.get_results()

            # 更新为完成状态
            backtest_state_service.update_status(
                backtest_id,
                "completed",
                progress=1.0,
                result=results
            )

            # Save results to database and cleanup old backtests
            await backtest_task_service.update_backtest_task(
                backtest_id,
                status="completed",
                progress=100.0,
                result_summary=results,
            )
            await backtest_task_service.cleanup_old_backtests(user_id)

            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "completed", "progress": 1.0}}
            )
            logger.info(f"回测完成: {backtest_id}")

        except Exception as e:
            import traceback
            logger.error(f"回测执行失败: {backtest_id}, 错误: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            backtest_state_service.update_status(
                backtest_id,
                "failed",
                error=str(e)
            )
            await backtest_task_service.update_backtest_task(
                backtest_id,
                status="failed",
                error_message=str(e),
            )
            await websocket_manager.broadcast_progress(
                backtest_id,
                {"type": "status", "data": {"status": "failed", "error": str(e)}}
            )


# 全局单例
backtest_task_manager = BacktestTaskManager()
