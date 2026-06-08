"""User settings router for FastAPI.

Provides RESTful API endpoints for user-specific settings:
- GET /api/settings/data-source - Get user's data source configuration
- PUT /api/settings/data-source - Update user's data source configuration
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.core.auth import AuthService
from src.database import get_db_adapter
from src.support.log.logger import logger

# Router
router = APIRouter()

# Security
security = HTTPBearer()


# Pydantic models for request/response


class DataSourceRequest(BaseModel):
    """Data source configuration request model."""

    data_source: str = Field(..., description="Data source name (tushare, baostock, akshare, yahoo)")
    tushare_token: Optional[str] = Field(None, description="Tushare API token (required if data_source is tushare)")


class DataSourceResponse(BaseModel):
    """Data source configuration response model."""

    success: bool
    message: str
    data: Optional[dict] = None


class OKXConfigRequest(BaseModel):
    """OKX API configuration request model."""

    api_key: str = Field(..., description="OKX API key")
    secret_key: str = Field(..., description="OKX API secret key")
    passphrase: str = Field(..., description="OKX API passphrase")
    is_demo: bool = Field(True, description="Use demo trading environment")


class OKXConfigResponse(BaseModel):
    """OKX API configuration response model."""

    success: bool
    message: str
    data: Optional[dict] = None


# Dependencies


async def get_auth_service() -> AuthService:
    """Get auth service instance."""
    db = get_db_adapter()
    await db.initialize()
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = await auth_service.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


# Endpoints


@router.get("/data-source")
async def get_data_source_config(
    current_user: dict = Depends(get_current_user),
):
    """Get user's data source configuration.

    Returns the user's configured data source and associated credentials (like Tushare token).
    """
    db = get_db_adapter()
    await db.initialize()

    user_id = current_user["user_id"]

    try:
        async with db.pool as conn:
            # Query user settings
            query = """
                SELECT data_source, tushare_token
                FROM UserSettings
                WHERE user_id = ?
            """
            row = await conn.fetchrow(query, user_id)

            if row:
                # Return data without exposing the full token
                data = {
                    "data_source": row["data_source"],
                    "has_token": bool(row["tushare_token"]),
                    "token_preview": f"{row['tushare_token'][:8]}..." if row["tushare_token"] and len(row["tushare_token"]) > 8 else row["tushare_token"] if row["tushare_token"] else None
                }
                logger.info(f"User {user_id} data source config: {row['data_source']}")
                return {
                    "success": True,
                    "message": "Data source configuration retrieved",
                    "data": data
                }
            else:
                # Return default configuration for new users
                logger.info(f"User {user_id} has no data source config, returning default")
                return {
                    "success": True,
                    "message": "Using default data source",
                    "data": {
                        "data_source": "baostock",
                        "has_token": False,
                        "token_preview": None
                    }
                }
    except Exception as e:
        logger.error(f"Failed to get data source config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put("/data-source")
async def update_data_source_config(
    request: DataSourceRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update user's data source configuration.

    Validates that required credentials (like Tushare token) are provided when needed.
    """
    db = get_db_adapter()
    await db.initialize()

    user_id = current_user["user_id"]
    data_source = request.data_source.lower()
    tushare_token = request.tushare_token

    # Validate data source
    valid_sources = ["tushare", "baostock", "akshare", "yahoo"]
    if data_source not in valid_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data source. Must be one of: {', '.join(valid_sources)}"
        )

    # Validate Tushare token if Tushare is selected
    if data_source == "tushare" and not tushare_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tushare API token is required when using Tushare data source"
        )

    try:
        async with db.pool as conn:
            # Check if user settings exist
            check_query = "SELECT id FROM UserSettings WHERE user_id = ?"
            existing = await conn.fetchval(check_query, user_id)

            current_time = datetime.now().isoformat()

            if existing:
                # Update existing settings
                update_query = """
                    UPDATE UserSettings
                    SET data_source = ?, tushare_token = ?, updated_at = ?
                    WHERE user_id = ?
                """
                await conn.execute(update_query, data_source, tushare_token, current_time, user_id)
                logger.info(f"Updated data source config for user {user_id}: {data_source}")
            else:
                # Insert new settings
                insert_query = """
                    INSERT INTO UserSettings (user_id, data_source, tushare_token, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                await conn.execute(insert_query, user_id, data_source, tushare_token, current_time, current_time)
                logger.info(f"Created data source config for user {user_id}: {data_source}")

            return {
                "success": True,
                "message": "Data source configuration saved successfully",
                "data": {
                    "data_source": data_source,
                    "has_token": bool(tushare_token)
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update data source config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )


# ==================== OKX API Configuration ====================


@router.get("/okx")
async def get_okx_config(
    current_user: dict = Depends(get_current_user),
):
    """Get user's OKX API configuration.

    Returns whether the user has configured OKX API credentials.
    Does not return the actual secret key for security.
    """
    db = get_db_adapter()
    await db.initialize()

    user_id = current_user["user_id"]

    try:
        async with db.pool as conn:
            query = """
                SELECT okx_api_key, okx_passphrase, okx_is_demo
                FROM UserSettings
                WHERE user_id = ?
            """
            row = await conn.fetchrow(query, user_id)

            if row and row["okx_api_key"]:
                return {
                    "success": True,
                    "message": "OKX configuration found",
                    "data": {
                        "has_config": True,
                        "api_key_preview": f"{row['okx_api_key'][:8]}..." if len(row["okx_api_key"]) > 8 else "***",
                        "passphrase_preview": f"{row['okx_passphrase'][:2]}***" if row["okx_passphrase"] else None,
                        "is_demo": bool(row["okx_is_demo"]),
                    }
                }
            else:
                return {
                    "success": True,
                    "message": "No OKX configuration found",
                    "data": {
                        "has_config": False,
                        "api_key_preview": None,
                        "passphrase_preview": None,
                        "is_demo": True,
                    }
                }
    except Exception as e:
        logger.error(f"Failed to get OKX config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve OKX configuration: {str(e)}"
        )


@router.put("/okx")
async def update_okx_config(
    request: OKXConfigRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update user's OKX API configuration.

    Stores the API credentials securely in the database.
    """
    db = get_db_adapter()
    await db.initialize()

    user_id = current_user["user_id"]

    # Validate required fields
    if not request.api_key or not request.secret_key or not request.passphrase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key, secret key, and passphrase are all required"
        )

    try:
        async with db.pool as conn:
            # Check if user settings exist
            check_query = "SELECT id FROM UserSettings WHERE user_id = ?"
            existing = await conn.fetchval(check_query, user_id)

            current_time = datetime.now().isoformat()

            if existing:
                # Update existing settings
                update_query = """
                    UPDATE UserSettings
                    SET okx_api_key = ?, okx_secret_key = ?, okx_passphrase = ?, okx_is_demo = ?, updated_at = ?
                    WHERE user_id = ?
                """
                await conn.execute(
                    update_query,
                    request.api_key,
                    request.secret_key,
                    request.passphrase,
                    1 if request.is_demo else 0,
                    current_time,
                    user_id
                )
                logger.info(f"Updated OKX config for user {user_id}")
            else:
                # Insert new settings with OKX config
                insert_query = """
                    INSERT INTO UserSettings
                    (user_id, data_source, okx_api_key, okx_secret_key, okx_passphrase, okx_is_demo, created_at, updated_at)
                    VALUES (?, 'baostock', ?, ?, ?, ?, ?, ?)
                """
                await conn.execute(
                    insert_query,
                    user_id,
                    request.api_key,
                    request.secret_key,
                    request.passphrase,
                    1 if request.is_demo else 0,
                    current_time,
                    current_time
                )
                logger.info(f"Created OKX config for user {user_id}")

            return {
                "success": True,
                "message": "OKX configuration saved successfully",
                "data": {
                    "has_config": True,
                    "is_demo": request.is_demo
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update OKX config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save OKX configuration: {str(e)}"
        )


@router.delete("/okx")
async def delete_okx_config(
    current_user: dict = Depends(get_current_user),
):
    """Delete user's OKX API configuration."""
    db = get_db_adapter()
    await db.initialize()

    user_id = current_user["user_id"]

    try:
        async with db.pool as conn:
            update_query = """
                UPDATE UserSettings
                SET okx_api_key = NULL, okx_secret_key = NULL, okx_passphrase = NULL, okx_is_demo = NULL, updated_at = ?
                WHERE user_id = ?
            """
            await conn.execute(update_query, datetime.now().isoformat(), user_id)
            logger.info(f"Deleted OKX config for user {user_id}")

            return {
                "success": True,
                "message": "OKX configuration deleted",
                "data": None
            }
    except Exception as e:
        logger.error(f"Failed to delete OKX config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete OKX configuration: {str(e)}"
        )
