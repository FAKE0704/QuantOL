"""通用 API 模型

包含共享的响应模型。
"""
from typing import Optional
from pydantic import BaseModel


class BacktestResponse(BaseModel):
    """回测响应模型"""

    success: bool
    message: str
    data: Optional[dict] = None


class BacktestListResponse(BaseModel):
    """回测列表响应模型"""

    success: bool
    message: str
    data: Optional[list] = None
