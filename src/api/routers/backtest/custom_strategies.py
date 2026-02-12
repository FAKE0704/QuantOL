"""策略端点路由

处理自定义策略管理相关的API端点。
"""
from fastapi import APIRouter, HTTPException, status, Depends

from src.api.models.backtest_requests import CustomStrategyCreate, CustomStrategyUpdate, RuleValidationRequest
from src.api.models.backtest_responses import CustomStrategyResponse, CustomStrategyListResponse, RuleValidationResponse
from src.services.backtest_config_service import BacktestConfigService
from src.api.utils import validate_rule_syntax
from src.api.deps import get_current_user

router = APIRouter()


@router.post("/validate-rule", response_model=RuleValidationResponse)
async def validate_rule(request: RuleValidationRequest):
    """验证规则语法

    Args:
        request: 包含规则表达式的请求

    Returns:
        验证结果响应
    """
    try:
        is_valid, message = validate_rule_syntax(request.rule)

        return RuleValidationResponse(
            success=is_valid,
            message=message,
            data={"rule": request.rule, "is_valid": is_valid}
        )

    except Exception as e:
        return RuleValidationResponse(
            success=False,
            message=f"Validation error: {str(e)}",
            data={"rule": request.rule, "is_valid": False}
        )


@router.post(
    "/custom-strategies",
    response_model=CustomStrategyResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_custom_strategy(
    strategy: CustomStrategyCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建自定义策略

    Args:
        strategy: 策略创建请求
        current_user: 当前认证用户

    Returns:
        创建的策略响应
    """
    try:
        config_service = BacktestConfigService()
        user_id = current_user["user_id"]

        # 检查策略键是否已存在
        existing = await config_service.get_custom_strategy(user_id, strategy.strategy_key)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Strategy with key '{strategy.strategy_key}' already exists"
            )

        # 验证规则语法
        rules_to_validate = [
            ("open_rule", strategy.open_rule),
            ("close_rule", strategy.close_rule),
            ("buy_rule", strategy.buy_rule),
            ("sell_rule", strategy.sell_rule),
        ]

        validation_errors = []
        for rule_name, rule_value in rules_to_validate:
            if rule_value:
                is_valid, message = validate_rule_syntax(rule_value)
                if not is_valid:
                    validation_errors.append(f"{rule_name}: {message}")

        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Rule validation failed",
                    "errors": validation_errors
                }
            )

        # 创建策略
        strategy_id = await config_service.create_custom_strategy(
            user_id=user_id,
            strategy_key=strategy.strategy_key,
            label=strategy.label,
            open_rule=strategy.open_rule,
            close_rule=strategy.close_rule,
            buy_rule=strategy.buy_rule,
            sell_rule=strategy.sell_rule,
        )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy created successfully",
            data={"strategy_key": strategy.strategy_key, "strategy_id": strategy_id}
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
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """列出所有自定义策略

    Args:
        current_user: 当前认证用户
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        策略列表响应
    """
    try:
        config_service = BacktestConfigService()
        strategies = await config_service.list_custom_strategies(
            current_user["user_id"]
        )

        # 手动处理分页
        if offset >= len(strategies):
            return CustomStrategyListResponse(
                success=True,
                message="No custom strategies found",
                data=[]
            )

        paginated_strategies = strategies[offset:offset + limit]

        return CustomStrategyListResponse(
            success=True,
            message=f"Retrieved {len(paginated_strategies)} custom strategies",
            data=paginated_strategies
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list custom strategies: {str(e)}",
        )


@router.get("/custom-strategies/{strategy_key}", response_model=CustomStrategyResponse)
async def get_custom_strategy(
    strategy_key: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定自定义策略

    Args:
        strategy_key: 策略键
        current_user: 当前认证用户

    Returns:
        策略响应
    """
    try:
        config_service = BacktestConfigService()
        user_id = current_user["user_id"]
        strategy = await config_service.get_custom_strategy(user_id, strategy_key)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom strategy '{strategy_key}' not found"
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy retrieved successfully",
            data=strategy
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve custom strategy: {str(e)}",
        )


@router.put("/custom-strategies/{strategy_key}", response_model=CustomStrategyResponse)
async def update_custom_strategy(
    strategy_key: str,
    update: CustomStrategyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新自定义策略

    Args:
        strategy_key: 策略键
        update: 更新数据
        current_user: 当前认证用户

    Returns:
        更新后的策略响应
    """
    try:
        config_service = BacktestConfigService()
        user_id = current_user["user_id"]

        # 检查策略是否存在
        existing = await config_service.get_custom_strategy(user_id, strategy_key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom strategy '{strategy_key}' not found"
            )

        # 验证规则语法（如果提供）
        if update.open_rule:
            is_valid, message = validate_rule_syntax(update.open_rule)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"open_rule validation failed: {message}"
                )

        if update.close_rule:
            is_valid, message = validate_rule_syntax(update.close_rule)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"close_rule validation failed: {message}"
                )

        if update.buy_rule:
            is_valid, message = validate_rule_syntax(update.buy_rule)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"buy_rule validation failed: {message}"
                )

        if update.sell_rule:
            is_valid, message = validate_rule_syntax(update.sell_rule)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"sell_rule validation failed: {message}"
                )

        # 调用更新方法
        result = await config_service.update_custom_strategy(
            user_id=user_id,
            strategy_key=strategy_key,
            label=update.label,
            open_rule=update.open_rule,
            close_rule=update.close_rule,
            buy_rule=update.buy_rule,
            sell_rule=update.sell_rule,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update custom strategy"
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy updated successfully",
            data={"strategy_key": strategy_key}
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
    current_user: dict = Depends(get_current_user)
):
    """删除自定义策略

    Args:
        strategy_key: 策略键
        current_user: 当前认证用户

    Returns:
        删除结果响应
    """
    try:
        config_service = BacktestConfigService()
        user_id = current_user["user_id"]

        # 检查策略是否存在
        existing = await config_service.get_custom_strategy(user_id, strategy_key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom strategy '{strategy_key}' not found"
            )

        success = await config_service.delete_custom_strategy(user_id, strategy_key)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete custom strategy"
            )

        return CustomStrategyResponse(
            success=True,
            message="Custom strategy deleted successfully",
            data={"strategy_key": strategy_key}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete custom strategy: {str(e)}",
        )
