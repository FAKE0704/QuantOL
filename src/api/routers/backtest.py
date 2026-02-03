"""Backtest router for FastAPI.

Provides RESTful API endpoints for backtesting:
- POST /api/backtest/run - Run a backtest
- GET /api/backtest/results/{backtest_id} - Get backtest results
- GET /api/backtest/list - List all backtests
- POST /api/backtest/configs - Create backtest configuration
- GET /api/backtest/configs - List backtest configurations
- GET /api/backtest/configs/{id} - Get specific configuration
- PUT /api/backtest/configs/{id} - Update configuration
- DELETE /api/backtest/configs/{id} - Delete configuration
- POST /api/backtest/configs/{id}/set-default - Set default configuration
"""

from typing import Optional, List, AsyncGenerator
from datetime import datetime
import json
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.database import get_db_adapter
from src.services.backtest_config_service import BacktestConfigService
from src.core.auth.jwt_service import JWTService
from src.services.backtest_task_manager import backtest_task_manager
from src.services.backtest_state_service import backtest_state_service
from src.services.backtest_task_service import backtest_task_service
from fastapi import BackgroundTasks

# Router
router = APIRouter()

# Security
security = HTTPBearer()


def _filter_result_summary(result_summary: Optional[dict]) -> dict:
    """Filter result summary to only include summary information.

    This is used for the /status endpoint to avoid returning large result sets.
    Full results can be obtained from the /results/{backtest_id} endpoint.

    Handles both single-symbol and multi-symbol modes:
    - Single-symbol: result_summary has 'summary' and 'performance_metrics' at top level
    - Multi-symbol: result_summary has 'individual' dict with per-symbol results
    """
    if not result_summary or not isinstance(result_summary, dict):
        return {}

    # Check if this is multi-symbol mode (has 'individual' key)
    if "individual" in result_summary:
        # Multi-symbol mode: extract combined equity and individual summaries
        filtered = {
            "individual": {},
            "combined_equity": result_summary.get("combined_equity"),
        }

        # Extract summary from each individual symbol result
        individual_results = result_summary.get("individual", {})
        if isinstance(individual_results, dict):
            for symbol, symbol_result in individual_results.items():
                if isinstance(symbol_result, dict):
                    filtered["individual"][symbol] = {
                        "summary": symbol_result.get("summary", {}),
                        "performance_metrics": symbol_result.get("performance_metrics", {}),
                    }

        # Add strategy mapping if present
        if "strategy_mapping" in result_summary:
            filtered["strategy_mapping"] = result_summary["strategy_mapping"]
        if "default_strategy" in result_summary:
            filtered["default_strategy"] = result_summary["default_strategy"]

        return filtered

    # Single-symbol mode: only return summary and performance_metrics
    return {
        "summary": result_summary.get("summary", {}),
        "performance_metrics": result_summary.get("performance_metrics", {}),
    }

# Pydantic models


class RebalancePeriodConfig(BaseModel):
    """Rebalance period configuration."""
    mode: str = "disabled"  # "trading_days", "calendar_rule", "disabled"
    trading_days_interval: Optional[int] = None
    calendar_frequency: Optional[str] = None  # "weekly", "monthly", "quarterly", "yearly"
    calendar_day: Optional[int] = None
    calendar_month: Optional[int] = None
    min_interval_days: Optional[int] = 0
    allow_first_rebalance: bool = True


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

    # Rebalance period config
    rebalance_period: Optional[RebalancePeriodConfig] = None


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


# Backtest config models


class BacktestConfigCreate(BaseModel):
    """Backtest configuration create model."""

    name: str
    description: Optional[str] = None
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD
    frequency: str
    symbols: list[str]
    initial_capital: float
    commission_rate: float
    slippage: float
    min_lot_size: int
    position_strategy: str
    position_params: dict
    trading_strategy: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None
    is_default: bool = False


class BacktestConfigUpdate(BaseModel):
    """Backtest configuration update model."""

    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[str] = None
    symbols: Optional[list[str]] = None
    initial_capital: Optional[float] = None
    commission_rate: Optional[float] = None
    slippage: Optional[float] = None
    min_lot_size: Optional[int] = None
    position_strategy: Optional[str] = None
    position_params: Optional[dict] = None
    trading_strategy: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None
    is_default: Optional[bool] = None


class BacktestConfigResponse(BaseModel):
    """Backtest configuration response model."""

    success: bool
    message: str
    data: Optional[dict] = None


class BacktestConfigListResponse(BaseModel):
    """Backtest configuration list response model."""

    success: bool
    message: str
    data: Optional[list[dict]] = None


# Custom Strategy Models
class CustomStrategyCreate(BaseModel):
    """Custom strategy creation model."""

    strategy_key: str
    label: str
    open_rule: str
    close_rule: str
    buy_rule: str
    sell_rule: str


class CustomStrategyUpdate(BaseModel):
    """Custom strategy update model."""

    label: Optional[str] = None
    open_rule: Optional[str] = None
    close_rule: Optional[str] = None
    buy_rule: Optional[str] = None
    sell_rule: Optional[str] = None


class CustomStrategyResponse(BaseModel):
    """Custom strategy response model."""

    success: bool
    message: str
    data: Optional[dict] = None


class CustomStrategyListResponse(BaseModel):
    """Custom strategy list response model."""

    success: bool
    message: str
    data: Optional[list[dict]] = None


# In-memory storage for backtests (replace with database in production)
_backtests: dict[str, dict] = {}


# Auth dependency for getting current user
async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> dict:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials (optional)

    Returns:
        User info from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    import logging
    logger = logging.getLogger(__name__)

    if not credentials or not credentials.credentials:
        logger.warning("No authorization credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - No authorization credentials provided",
        )

    token = credentials.credentials
    logger.info(f"Token received: {token[:20]}..." if len(token) > 20 else f"Token received: {token}")
    jwt_service = JWTService()

    try:
        payload = jwt_service.verify_token(token)
        if payload is None:
            logger.warning("Token verification returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        logger.info(f"User authenticated: user_id={payload.get('user_id')}")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


# Endpoints


@router.post("/run", response_model=BacktestResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run a backtest with the given configuration (async execution with WebSocket progress).

    Args:
        request: Backtest configuration
        background_tasks: FastAPI background tasks

    Returns:
        Backtest response with backtest_id
    """
    try:
        # Generate unique backtest ID
        backtest_id = f"bt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Submit to background task manager (creates Redis record and starts async execution)
        backtest_task_manager.submit_backtest(backtest_id, request, background_tasks)

        return BacktestResponse(
            success=True,
            message=f"Backtest {backtest_id} started. Connect via WebSocket for progress updates.",
            data={"backtest_id": backtest_id},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start backtest: {str(e)}",
        )


async def _stream_json_response(data: dict) -> AsyncGenerator[bytes, None]:
    """Stream JSON response in chunks to avoid memory issues with large responses.

    Args:
        data: Data dictionary to serialize

    Yields:
        JSON bytes in chunks
    """
    # 使用 json.dumps 生成完整 JSON，但分块发送
    json_str = json.dumps(data, ensure_ascii=False, default=str)
    # 分块发送，每块 8KB
    chunk_size = 8192
    for i in range(0, len(json_str), chunk_size):
        yield json_str[i:i + chunk_size].encode('utf-8')


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """Get results and progress for a specific backtest.

    Uses streaming response for large result sets to avoid ERR_CONTENT_LENGTH_MISMATCH errors.

    Args:
        backtest_id: Backtest ID

    Returns:
        Streaming JSON response with backtest results
    """
    try:
        # First try Redis (for active/recent backtests)
        backtest = backtest_state_service.get_backtest(backtest_id)

        # Map 'result' field to 'result_summary' for frontend compatibility
        if backtest and "result" in backtest:
            backtest["result_summary"] = backtest.pop("result")

        # If not in Redis, try database (for completed backtests)
        if not backtest:
            task = await backtest_task_service.get_backtest_task(backtest_id)

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Backtest {backtest_id} not found",
                )

            # Convert database task to response format
            # Parse result_summary if it exists as JSON string
            result_summary = task.get("result_summary")
            if result_summary and isinstance(result_summary, str):
                try:
                    result_summary = json.loads(result_summary)
                except:
                    result_summary = None

            backtest = {
                "id": task["backtest_id"],
                "status": task["status"],
                "progress": task["progress"],
                "current_time": task.get("current_time"),
                "config": task.get("config"),
                "result_summary": result_summary,
                "error": task.get("error_message"),
                "created_at": task["created_at"],
                "started_at": task.get("started_at"),
                "completed_at": task.get("completed_at"),
            }

        response_data = {
            "success": True,
            "message": "Backtest results retrieved",
            "data": backtest,
        }

        # 使用流式响应
        return StreamingResponse(
            _stream_json_response(response_data),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
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
    """List all backtests from Redis.

    Args:
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        Backtest list response
    """
    try:
        # Get backtests from Redis
        backtest_list = backtest_state_service.list_backtests(limit)

        # Apply pagination
        paginated_list = backtest_list[offset : offset + limit]

        # Convert to response format
        results = []
        for bt in paginated_list:
            full_data = backtest_state_service.get_backtest(bt["id"], {})
            results.append(
                BacktestResult(
                    backtest_id=bt["id"],
                    status=bt["status"],
                    created_at=bt["created_at"],
                    completed_at=full_data.get("completed_at"),
                    total_return=full_data.get("result", {}).get("summary", {}).get("total_return"),
                    sharpe_ratio=full_data.get("result", {}).get("performance_metrics", {}).get("sharpe_ratio"),
                    max_drawdown=full_data.get("result", {}).get("performance_metrics", {}).get("max_drawdown_pct"),
                    win_rate=full_data.get("result", {}).get("summary", {}).get("win_rate"),
                )
            )

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


@router.get("/{backtest_id}/status", response_model=BacktestResponse)
async def get_backtest_status(backtest_id: str):
    """Get backtest status from Redis and database for state recovery.

    This endpoint is used by the frontend to recover state after page refresh.
    It checks both Redis (for active backtests) and database (for completed ones).

    Note: For completed backtests with large results, only a summary is returned.
      Full results can be obtained from the /results/{backtest_id} endpoint.

    Args:
        backtest_id: Backtest ID

    Returns:
        Backtest status response with current progress and results
    """
    try:
        # First try Redis (for active/recent backtests)
        backtest = backtest_state_service.get_backtest(backtest_id)

        if not backtest:
            # If not in Redis, try database (for completed backtests)
            task = await backtest_task_service.get_backtest_task(backtest_id)

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Backtest {backtest_id} not found",
                )

            # Convert database task to response format
            # Ensure result_summary is a dict (safe_json_loads already handles this)
            result_summary = task.get("result_summary")
            if result_summary is None:
                result_summary = {}

            backtest = {
                "id": task["backtest_id"],
                "status": task["status"],
                "progress": task["progress"],
                "current_time": task["current_time"],
                "config": task.get("config") or {},
                "created_at": task["created_at"],
                "started_at": task["started_at"],
                "completed_at": task["completed_at"],
                "result": _filter_result_summary(result_summary),
                "error": task.get("error_message"),
            }
        else:
            # For Redis data, strip out large fields to avoid response size issues
            # The full result is available via /results/{backtest_id}
            result = backtest.get("result", {})
            if isinstance(result, dict):
                # Only keep summary info, remove large data arrays
                filtered_result = {
                    "summary": result.get("summary", {}),
                }
                backtest["result"] = filtered_result

        return BacktestResponse(
            success=True,
            message="Backtest status retrieved",
            data=backtest,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest status: {str(e)}",
        )


@router.get("/history", response_model=BacktestListResponse)
async def get_backtest_history(
    limit: int = 5,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """Get current user's backtest history from database.

    This endpoint returns the user's historical backtests (max 5 completed),
    stored persistently in the database.

    Args:
        limit: Maximum number of results (default 5)
        status_filter: Optional status filter (pending/running/completed/failed)
        current_user: Current authenticated user

    Returns:
        Backtest history response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        # Get backtests from database
        tasks = await backtest_task_service.list_user_backtests(
            user_id=user_id,
            status=status_filter,
            limit=min(limit, 10),  # Cap at 10
        )

        # Convert to response format
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
# Backtest config management endpoints


async def get_config_service() -> BacktestConfigService:
    """Get backtest config service instance."""
    return BacktestConfigService()


@router.post("/configs", response_model=BacktestConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    request: BacktestConfigCreate,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Create a new backtest configuration.

    Args:
        request: Configuration data
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Created configuration response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        config = await config_service.create_config(
            user_id=user_id,
            name=request.name,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            symbols=request.symbols,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage=request.slippage,
            min_lot_size=request.min_lot_size,
            position_strategy=request.position_strategy,
            position_params=request.position_params,
            trading_strategy=request.trading_strategy,
            open_rule=request.open_rule,
            close_rule=request.close_rule,
            buy_rule=request.buy_rule,
            sell_rule=request.sell_rule,
            is_default=request.is_default,
        )

        if config is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create configuration",
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration created successfully",
            data=config,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}",
        )


@router.get("/configs", response_model=BacktestConfigListResponse)
async def list_configs(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """List all backtest configurations for the current user.

    Args:
        limit: Maximum number of results
        offset: Offset for pagination
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Configuration list response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        configs = await config_service.list_configs(user_id, limit, offset)

        return BacktestConfigListResponse(
            success=True,
            message=f"Found {len(configs)} configurations",
            data=configs,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}",
        )


@router.get("/configs/{config_id}", response_model=BacktestConfigResponse)
async def get_config(
    config_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Get a specific backtest configuration.

    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Configuration response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        config = await config_service.get_config_by_id(config_id, user_id)

        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found",
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration found",
            data=config,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}",
        )


@router.put("/configs/{config_id}", response_model=BacktestConfigResponse)
async def update_config(
    config_id: int,
    request: BacktestConfigUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Update a backtest configuration.

    Args:
        config_id: Configuration ID
        request: Update data
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Updated configuration response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        config = await config_service.update_config(
            config_id=config_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            symbols=request.symbols,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage=request.slippage,
            min_lot_size=request.min_lot_size,
            position_strategy=request.position_strategy,
            position_params=request.position_params,
            trading_strategy=request.trading_strategy,
            open_rule=request.open_rule,
            close_rule=request.close_rule,
            buy_rule=request.buy_rule,
            sell_rule=request.sell_rule,
            is_default=request.is_default,
        )

        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found",
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration updated successfully",
            data=config,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.delete("/configs/{config_id}", response_model=BacktestConfigResponse)
async def delete_config(
    config_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Delete a backtest configuration.

    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Delete confirmation response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        success = await config_service.delete_config(config_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found",
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}",
        )


@router.post("/configs/{config_id}/set-default", response_model=BacktestConfigResponse)
async def set_default_config(
    config_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Set a configuration as the default for the current user.

    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        config_service: Config service

    Returns:
        Success response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        success = await config_service.set_default_config(config_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found",
            )

        return BacktestConfigResponse(
            success=True,
            message="Default configuration set successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default configuration: {str(e)}",
        )


class RuleValidationRequest(BaseModel):
    """Rule validation request model."""
    rule: str


class RuleValidationResponse(BaseModel):
    """Rule validation response model."""
    valid: bool
    error: Optional[str] = None


@router.post("/validate-rule", response_model=RuleValidationResponse)
async def validate_rule(request: RuleValidationRequest):
    """Validate a trading rule syntax.

    Args:
        request: Rule validation request containing the rule to validate

    Returns:
        Validation result with error message if invalid
    """
    try:
        from src.core.strategy.rule_parser import RuleParser

        is_valid, error_message = RuleParser.validate_syntax(request.rule)

        return RuleValidationResponse(
            valid=is_valid,
            error=None if is_valid else error_message
        )

    except Exception as e:
        return RuleValidationResponse(
            valid=False,
            error=f"验证失败: {str(e)}"
        )


# Custom Strategy API Endpoints
@router.post("/custom-strategies", response_model=CustomStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_strategy(
    request: CustomStrategyCreate,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Create a custom trading strategy.

    Args:
        request: Custom strategy creation request
        current_user: Authenticated user
        config_service: Backtest config service instance

    Returns:
        Created custom strategy
    """
    try:
        result = await config_service.create_custom_strategy(
            user_id=current_user["user_id"],
            strategy_key=request.strategy_key,
            label=request.label,
            open_rule=request.open_rule,
            close_rule=request.close_rule,
            buy_rule=request.buy_rule,
            sell_rule=request.sell_rule,
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create custom strategy",
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy created successfully",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom strategy: {str(e)}",
        )


@router.get("/custom-strategies", response_model=CustomStrategyListResponse)
async def list_custom_strategies(
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """List all custom strategies for the current user.

    Args:
        current_user: Authenticated user
        config_service: Backtest config service instance

    Returns:
        List of custom strategies
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"list_custom_strategies called for user_id: {current_user.get('user_id')}")
    try:
        strategies = await config_service.list_custom_strategies(current_user["user_id"])

        return CustomStrategyListResponse(
            success=True,
            message="Custom strategies retrieved successfully",
            data=strategies,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list custom strategies: {str(e)}",
        )


@router.get("/custom-strategies/{strategy_key}", response_model=CustomStrategyResponse)
async def get_custom_strategy(
    strategy_key: str,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Get a custom strategy by key.

    Args:
        strategy_key: Strategy key
        current_user: Authenticated user
        config_service: Backtest config service instance

    Returns:
        Custom strategy data
    """
    try:
        strategy = await config_service.get_custom_strategy(current_user["user_id"], strategy_key)

        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom strategy not found",
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy retrieved successfully",
            data=strategy,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom strategy: {str(e)}",
        )


@router.put("/custom-strategies/{strategy_key}", response_model=CustomStrategyResponse)
async def update_custom_strategy(
    strategy_key: str,
    request: CustomStrategyUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Update a custom strategy.

    Args:
        strategy_key: Strategy key
        request: Update request
        current_user: Authenticated user
        config_service: Backtest config service instance

    Returns:
        Updated custom strategy
    """
    try:
        result = await config_service.update_custom_strategy(
            user_id=current_user["user_id"],
            strategy_key=strategy_key,
            label=request.label,
            open_rule=request.open_rule,
            close_rule=request.close_rule,
            buy_rule=request.buy_rule,
            sell_rule=request.sell_rule,
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom strategy not found",
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy updated successfully",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update custom strategy: {str(e)}",
        )


@router.delete("/custom-strategies/{strategy_key}", response_model=CustomStrategyResponse)
async def delete_custom_strategy(
    strategy_key: str,
    current_user: dict = Depends(get_current_user_from_token),
    config_service: BacktestConfigService = Depends(get_config_service),
):
    """Delete a custom strategy.

    Args:
        strategy_key: Strategy key
        current_user: Authenticated user
        config_service: Backtest config service instance

    Returns:
        Success response
    """
    try:
        success = await config_service.delete_custom_strategy(current_user["user_id"], strategy_key)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom strategy not found",
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete custom strategy: {str(e)}",
        )


# Generic backtest detail endpoints (must be AFTER specific routes like /configs and /custom-strategies)


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_detail(
    backtest_id: str,
    current_user: dict = Depends(get_current_user_from_token),
):
    """Get detailed backtest results from database.

    Args:
        backtest_id: Backtest ID
        current_user: Current authenticated user

    Returns:
        Full backtest details response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        # Get from database first (for completed backtests)
        task = await backtest_task_service.get_backtest_task(backtest_id)

        if not task:
            # If not in database, try Redis (for active backtests)
            backtest = backtest_state_service.get_backtest(backtest_id)

            if not backtest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Backtest {backtest_id} not found",
                )

            return BacktestResponse(
                success=True,
                message="Backtest details retrieved",
                data=backtest,
            )

        # Verify ownership
        if task["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this backtest",
            )

        return BacktestResponse(
            success=True,
            message="Backtest details retrieved",
            data=task,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest details: {str(e)}",
        )


@router.delete("/{backtest_id}", response_model=BacktestResponse)
async def delete_backtest(
    backtest_id: str,
    current_user: dict = Depends(get_current_user_from_token),
):
    """Delete a backtest from database.

    Args:
        backtest_id: Backtest ID
        current_user: Current authenticated user

    Returns:
        Deletion response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        # Delete from database
        deleted = await backtest_task_service.delete_backtest_task(backtest_id, user_id)

        # Also delete from Redis if exists
        backtest_state_service.delete_backtest(backtest_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found or access denied",
            )

        return BacktestResponse(
            success=True,
            message="Backtest deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backtest: {str(e)}",
        )


@router.get("/{backtest_id}/logs", response_model=BacktestResponse)
async def get_backtest_logs(
    backtest_id: str,
    line_start: int = 0,
    line_end: int = 1000,
    current_user: dict = Depends(get_current_user_from_token),
):
    """Get backtest log file content with pagination.

    Args:
        backtest_id: Backtest ID
        line_start: Start line number (0-indexed)
        line_end: End line number (exclusive)
        current_user: Current authenticated user

    Returns:
        Log content response
    """
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token",
            )

        # Get backtest task to find log file path
        task = await backtest_task_service.get_backtest_task(backtest_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found",
            )

        # Verify ownership
        if task["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this backtest",
            )

        # Read log file
        log_file_path = task.get("log_file_path")
        if not log_file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log file not found for this backtest",
            )

        import os
        if not os.path.exists(log_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log file does not exist",
            )

        # Read log file with pagination
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Apply pagination
            total_lines = len(lines)
            paginated_lines = lines[line_start:line_end]

            return BacktestResponse(
                success=True,
                message="Log content retrieved",
                data={
                    "backtest_id": backtest_id,
                    "total_lines": total_lines,
                    "line_start": line_start,
                    "line_end": min(line_end, total_lines),
                    "lines": paginated_lines,
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read log file: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch backtest logs: {str(e)}",
        )
