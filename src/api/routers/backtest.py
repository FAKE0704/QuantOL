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

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.database import get_db_adapter
from src.services.backtest_config_service import BacktestConfigService
from src.core.auth.jwt_service import JWTService
from src.services.backtest_task_manager import backtest_task_manager
from src.services.backtest_state_service import backtest_state_service
from fastapi import BackgroundTasks

# Router
router = APIRouter()

# Security
security = HTTPBearer()

# Pydantic models


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


# In-memory storage for backtests (replace with database in production)
_backtests: dict[str, dict] = {}


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


@router.get("/results/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_results(backtest_id: str):
    """Get results and progress for a specific backtest from Redis.

    Args:
        backtest_id: Backtest ID

    Returns:
        Backtest results response
    """
    try:
        backtest = backtest_state_service.get_backtest(backtest_id)

        if not backtest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found",
            )

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


# Backtest config management endpoints


# Auth dependency for getting current user
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User info from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    jwt_service = JWTService()

    try:
        payload = jwt_service.verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


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
