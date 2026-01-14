"""Dashboard 统计 API 路由"""

from fastapi import APIRouter

from src.database import get_db_adapter
from src.services.backtest_state_service import backtest_state_service

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """获取 Dashboard 统计数据"""
    try:
        db = get_db_adapter()

        # 获取交易策略总数（排除 custom_strategy）
        all_strategies = await db.get_strategies(category='trading')
        total_strategies = len([s for s in all_strategies if s['code'] != 'custom_strategy'])

        # 获取运行中的回测数量
        all_backtests = backtest_state_service.list_backtests(limit=1000)
        active_backtests = sum(1 for bt in all_backtests if bt['status'] == 'running')

        return {
            "success": True,
            "message": "Dashboard stats retrieved",
            "data": {
                'total_strategies': total_strategies,
                'active_backtests': active_backtests
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": {'total_strategies': 0, 'active_backtests': 0}
        }
