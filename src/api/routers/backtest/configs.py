"""配置端点路由

处理回测配置管理相关的API端点。
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends

from src.api.models.backtest_requests import BacktestConfigCreate, BacktestConfigUpdate
from src.api.models.backtest_responses import BacktestConfigResponse, BacktestConfigListResponse
from src.services.backtest_config_service import BacktestConfigService
from src.api.deps import get_config_service

router = APIRouter()


@router.post(
    "/configs",
    response_model=BacktestConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_config(
    config: BacktestConfigCreate,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """创建回测配置

    Args:
        config: 配置创建请求
        config_service: 配置服务

    Returns:
        创建的配置响应
    """
    try:
        # 检查是否已存在同名配置
        existing = await config_service.get_by_name(config.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Configuration with name '{config.name}' already exists"
            )

        # 创建配置
        config_id = await config_service.create_config(config.model_dump())

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
    limit: int = 50,
    offset: int = 0,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """列出所有回测配置

    Args:
        limit: 返回数量限制
        offset: 偏移量
        config_service: 配置服务

    Returns:
        配置列表响应
    """
    try:
        configs = await config_service.list_configs(limit=limit, offset=offset)

        return BacktestConfigListResponse(
            success=True,
            message=f"Retrieved {len(configs)} configurations",
            data=configs
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}",
        )


@router.get("/configs/{config_id}", response_model=BacktestConfigResponse)
async def get_config(
    config_id: str,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """获取指定配置

    Args:
        config_id: 配置ID
        config_service: 配置服务

    Returns:
        配置响应
    """
    try:
        config = await config_service.get_config(config_id)

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}",
        )


@router.put("/configs/{config_id}", response_model=BacktestConfigResponse)
async def update_config(
    config_id: str,
    update: BacktestConfigUpdate,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """更新配置

    Args:
        config_id: 配置ID
        update: 更新数据
        config_service: 配置服务

    Returns:
        更新后的配置响应
    """
    try:
        # 检查配置是否存在
        existing = await config_service.get_config(config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # 过滤None值并更新
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        success = await config_service.update_config(config_id, update_data)

        if not success:
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.delete("/configs/{config_id}", response_model=BacktestConfigResponse)
async def delete_config(
    config_id: str,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """删除配置

    Args:
        config_id: 配置ID
        config_service: 配置服务

    Returns:
        删除结果响应
    """
    try:
        # 检查配置是否存在
        existing = await config_service.get_config(config_id)
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

        success = await config_service.delete_config(config_id)

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}",
        )


@router.post("/configs/{config_id}/set-default", response_model=BacktestConfigResponse)
async def set_default_config(
    config_id: str,
    config_service: BacktestConfigService = Depends(get_config_service)
):
    """设置默认配置

    Args:
        config_id: 配置ID
        config_service: 配置服务

    Returns:
        设置结果响应
    """
    try:
        # 检查配置是否存在
        existing = await config_service.get_config(config_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        success = await config_service.set_default(config_id)

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default configuration: {str(e)}",
        )
