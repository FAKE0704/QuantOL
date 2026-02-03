"""通用依赖模块

提供可复用的依赖注入函数，用于API路由。
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database import get_db_adapter
from src.services.backtest_config_service import BacktestConfigService
from src.core.auth.jwt_service import JWTService

# Security
security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """统一的认证依赖

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        JWT payload if valid

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

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
    """获取配置服务

    Returns:
        BacktestConfigService instance
    """
    return BacktestConfigService()
