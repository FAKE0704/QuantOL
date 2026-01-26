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
    from src.support.log.logger import logger

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
    from src.support.log.logger import logger

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
