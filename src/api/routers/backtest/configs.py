"""配置端点路由

处理回测配置管理相关的API端点。
"""
from fastapi import APIRouter, HTTPException, status, Depends

from src.api.models.backtest_requests import BacktestConfigCreate, BacktestConfigUpdate
from src.api.models.backtest_responses import BacktestConfigResponse, BacktestConfigListResponse
from src.services.backtest_config_service import BacktestConfigService
from src.api.deps import get_config_service, get_current_user

router = APIRouter()


@router.post(
    "/configs",
    response_model=BacktestConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_config(
    config: BacktestConfigCreate,
    current_user: dict = Depends(get_current_user),
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """创建回测配置

    Args:
        config: 配置创建请求
        current_user: 当前认证用户
        config_service: 配置服务

    Returns:
        创建的配置响应
    """
    try:
        user_id = current_user["user_id"]

        # 检查是否已存在同名配置
        existing = await config_service.get_by_name(user_id, config.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Configuration with name '{config.name}' already exists"
            )

        # 创建配置
        config_id = await config_service.create_config(
            user_id=user_id,
            name=config.name,
            description=config.description,
            start_date=config.start_date,
            end_date=config.end_date,
            frequency=config.frequency,
            symbols=config.symbols,
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage=config.slippage,
            min_lot_size=config.min_lot_size,
            position_strategy=config.position_strategy,
            position_params=config.position_params,
            trading_strategy=config.trading_strategy,
            open_rule=config.open_rule,
            close_rule=config.close_rule,
            buy_rule=config.buy_rule,
            sell_rule=config.sell_rule,
            is_default=config.is_default,
        )

        return BacktestConfigResponse(
            success=True,
            message="Configuration created successfully",
            data={"config_id": config_id}
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
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """列出所有回测配置

    Args:
        current_user: 当前认证用户
        limit: 返回数量限制
        offset: 偏移量
        config_service: 配置服务

    Returns:
        配置列表响应
    """
    try:
        user_id = current_user["user_id"]
        configs = await config_service.list_configs(user_id, limit=limit, offset=offset)

        return BacktestConfigListResponse(
            success=True,
            message=f"Retrieved {len(configs)} configurations",
            data=configs
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
    config_id: str,
    current_user: dict = Depends(get_current_user),
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """获取指定配置

    Args:
        config_id: 配置ID
        current_user: 当前认证用户
        config_service: 配置服务

    Returns:
        配置响应
    """
    try:
        user_id = current_user["user_id"]
        config = await config_service.get_config_by_id(int(config_id), user_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration retrieved successfully",
            data=config
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid config_id: {config_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}",
        )


@router.put("/configs/{config_id}", response_model=BacktestConfigResponse)
async def update_config(
    config_id: str,
    update: BacktestConfigUpdate,
    current_user: dict = Depends(get_current_user),
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """更新配置

    Args:
        config_id: 配置ID
        update: 更新数据
        current_user: 当前认证用户
        config_service: 配置服务

    Returns:
        更新后的配置响应
    """
    try:
        user_id = current_user["user_id"]

        # 检查配置是否存在
        existing = await config_service.get_config_by_id(int(config_id), user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # 调用更新方法
        result = await config_service.update_config(
            user_id=user_id,
            config_id=int(config_id),
            name=update.name,
            description=update.description,
            start_date=update.start_date,
            end_date=update.end_date,
            frequency=update.frequency,
            symbols=update.symbols,
            initial_capital=update.initial_capital,
            commission_rate=update.commission_rate,
            slippage=update.slippage,
            min_lot_size=update.min_lot_size,
            position_strategy=update.position_strategy,
            position_params=update.position_params,
            trading_strategy=update.trading_strategy,
            open_rule=update.open_rule,
            close_rule=update.close_rule,
            buy_rule=update.buy_rule,
            sell_rule=update.sell_rule,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update configuration"
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration updated successfully",
            data={"config_id": config_id}
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid config_id: {config_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.delete("/configs/{config_id}", response_model=BacktestConfigResponse)
async def delete_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """删除配置

    Args:
        config_id: 配置ID
        current_user: 当前认证用户
        config_service: 配置服务

    Returns:
        删除结果响应
    """
    try:
        user_id = current_user["user_id"]

        # 检查配置是否存在
        existing = await config_service.get_config_by_id(int(config_id), user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # 检查是否为默认配置
        if existing.get("is_default"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default configuration"
            )

        success = await config_service.delete_config(int(config_id), user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete configuration"
            )

        return BacktestConfigResponse(
            success=True,
            message="Configuration deleted successfully",
            data={"config_id": config_id}
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid config_id: {config_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}",
        )


@router.post("/configs/{config_id}/set-default", response_model=BacktestConfigResponse)
async def set_default_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """设置默认配置

    Args:
        config_id: 配置ID
        current_user: 当前认证用户
        config_service: 配置服务

    Returns:
        设置结果响应
    """
    try:
        user_id = current_user["user_id"]

        # 检查配置是否存在
        existing = await config_service.get_config_by_id(int(config_id), user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        success = await config_service.set_default_config(int(config_id), user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set default configuration"
            )

        return BacktestConfigResponse(
            success=True,
            message="Default configuration set successfully",
            data={"config_id": config_id}
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid config_id: {config_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default configuration: {str(e)}",
        )
