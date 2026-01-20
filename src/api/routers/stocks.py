"""Stock data router for FastAPI.

Provides RESTful API endpoints for stock data:
- GET /api/stocks - List all stocks
- GET /api/stocks/search - Search stocks by code or name
- GET /api/stocks/{code} - Get stock info
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.database import get_db_adapter

# Router
router = APIRouter()

# Pydantic models


class StockInfo(BaseModel):
    """Stock information model."""

    code: str
    name: str
    ipo_date: Optional[str] = None
    out_date: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class StockListItem(BaseModel):
    """Stock list item model."""

    code: str
    name: str


class StockListResponse(BaseModel):
    """Stock list response model."""

    success: bool
    message: str
    data: Optional[List[StockListItem]] = None


class StockDetailResponse(BaseModel):
    """Stock detail response model."""

    success: bool
    message: str
    data: Optional[StockInfo] = None


class StockDataRangeResponse(BaseModel):
    """Stock data range response model."""

    success: bool
    message: str
    data: Optional[dict] = None


# Endpoints


@router.get("/stocks", response_model=StockListResponse)
async def list_stocks(
    search: Optional[str] = Query(None, description="Search by code or name"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
):
    """Get list of stocks.

    Args:
        search: Optional search query to filter stocks
        limit: Maximum number of results to return

    Returns:
        Stock list response
    """
    try:
        db = get_db_adapter()

        # Get all stocks from database
        stocks_df = await db.get_all_stocks()

        if stocks_df is None or stocks_df.empty:
            return StockListResponse(
                success=True, message="No stocks found", data=[]
            )

        # Filter by search query if provided
        if search:
            search_lower = search.lower()
            mask = stocks_df["code"].str.contains(
                search, case=False, na=False
            ) | stocks_df["code_name"].str.contains(
                search_lower, na=False
            )
            stocks_df = stocks_df[mask]

        # Limit results
        stocks_df = stocks_df.head(limit)

        # Convert to response format
        stocks = [
            StockListItem(
                code=str(row["code"]), name=str(row["code_name"])
            )
            for _, row in stocks_df.iterrows()
        ]

        return StockListResponse(
            success=True,
            message=f"Found {len(stocks)} stocks",
            data=stocks,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stocks: {str(e)}",
        )


@router.get("/stocks/search", response_model=StockListResponse)
async def search_stocks(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
):
    """Search stocks by code or name.

    Args:
        q: Search query
        limit: Maximum number of results to return

    Returns:
        Stock list response
    """
    return await list_stocks(search=q, limit=limit)


@router.get("/stocks/{code}", response_model=StockDetailResponse)
async def get_stock_info(code: str):
    """Get detailed information for a specific stock.

    Args:
        code: Stock code

    Returns:
        Stock detail response
    """
    try:
        db = get_db_adapter()

        # Get stock info from database
        stock_info = await db.get_stock_info(code)

        if not stock_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {code} not found",
            )

        return StockDetailResponse(
            success=True,
            message="Stock found",
            data=StockInfo(
                code=stock_info.get("code", code),
                name=stock_info.get("code_name", ""),
                ipo_date=stock_info.get("ipoDate"),
                out_date=stock_info.get("outDate"),
                type=stock_info.get("type"),
                status=stock_info.get("status"),
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stock info: {str(e)}",
        )


@router.get("/stocks/{code}/data-range", response_model=StockDataRangeResponse)
async def get_stock_data_range(code: str, frequency: str = Query("d", description="Data frequency")):
    """Get available date range for a specific stock.

    Args:
        code: Stock code
        frequency: Data frequency (d/w/m)

    Returns:
        Stock data range with min_date and max_date
    """
    try:
        db = get_db_adapter()
        await db.initialize()

        # 直接查询数据库获取日期范围
        import sqlite3
        import os

        db_path = os.environ.get("SQLITE_DB_PATH", "./data/quantdb.sqlite")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT MIN(date), MAX(date), COUNT(*), data_source
               FROM StockData
               WHERE code = ? AND frequency = ?
               GROUP BY data_source
               ORDER BY COUNT(*) DESC
               LIMIT 1""",
            (code, frequency)
        )
        result = cursor.fetchone()

        conn.close()

        if not result or result[2] == 0:
            return StockDataRangeResponse(
                success=False,
                message=f"No data found for {code}",
                data=None
            )

        return StockDataRangeResponse(
            success=True,
            message=f"Data range found for {code}",
            data={
                "code": code,
                "min_date": result[0],
                "max_date": result[1],
                "record_count": result[2],
                "data_source": result[3]
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data range: {str(e)}",
        )
