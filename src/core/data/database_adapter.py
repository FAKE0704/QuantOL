from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import pandas as pd
from datetime import datetime, date, time
import os
from src.support.log.logger import logger


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        pass

    @abstractmethod
    async def create_connection_pool(self) -> Any:
        """创建连接池"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, *args) -> Any:
        """执行查询"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    async def save_stock_info(self, code: str, code_name: str, ipo_date: str,
                             stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息"""
        pass

    @abstractmethod
    async def check_data_completeness(self, symbol: str, start_date: date, end_date: date, frequency: str) -> list:
        """检查数据完整性"""
        pass

    @abstractmethod
    async def load_stock_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
        """加载股票数据"""
        pass

    @abstractmethod
    async def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票信息"""
        pass

    @abstractmethod
    async def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        pass

    @abstractmethod
    async def get_stock_name(self, code: str) -> str:
        """根据股票代码获取名称"""
        pass

    @abstractmethod
    async def save_stock_data(self, symbol: str, data: pd.DataFrame, frequency: str) -> bool:
        """保存股票数据"""
        pass

    @abstractmethod
    async def save_money_supply_data(self, data: pd.DataFrame) -> bool:
        """保存货币供应量数据"""
        pass

    @abstractmethod
    async def get_money_supply_data(self, start_month: str, end_month: str) -> pd.DataFrame:
        """获取货币供应量数据"""
        pass

    @abstractmethod
    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        pass

    # Backtest config CRUD operations
    @abstractmethod
    async def create_backtest_config(
        self,
        user_id: int,
        name: str,
        description: Optional[str],
        start_date: str,
        end_date: str,
        frequency: str,
        symbols: List[str],
        initial_capital: float,
        commission_rate: float,
        slippage: float,
        min_lot_size: int,
        position_strategy: str,
        position_params: dict,
        trading_strategy: Optional[str] = None,
        open_rule: Optional[str] = None,
        close_rule: Optional[str] = None,
        buy_rule: Optional[str] = None,
        sell_rule: Optional[str] = None,
        is_default: bool = False,
    ) -> Optional[dict]:
        """创建回测配置"""
        pass

    @abstractmethod
    async def get_backtest_config_by_id(self, config_id: int, user_id: int) -> Optional[dict]:
        """根据ID获取回测配置"""
        pass

    @abstractmethod
    async def list_backtest_configs(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[dict]:
        """列出回测配置"""
        pass

    @abstractmethod
    async def update_backtest_config(
        self,
        config_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        initial_capital: Optional[float] = None,
        commission_rate: Optional[float] = None,
        slippage: Optional[float] = None,
        min_lot_size: Optional[int] = None,
        position_strategy: Optional[str] = None,
        position_params: Optional[dict] = None,
        trading_strategy: Optional[str] = None,
        open_rule: Optional[str] = None,
        close_rule: Optional[str] = None,
        buy_rule: Optional[str] = None,
        sell_rule: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[dict]:
        """更新回测配置"""
        pass

    @abstractmethod
    async def delete_backtest_config(self, config_id: int, user_id: int) -> bool:
        """删除回测配置"""
        pass

    @abstractmethod
    async def set_default_backtest_config(self, config_id: int, user_id: int) -> bool:
        """设置默认回测配置"""
        pass

    # Custom trading strategy CRUD operations
    @abstractmethod
    async def create_custom_strategy(
        self,
        user_id: int,
        strategy_key: str,
        label: str,
        open_rule: str,
        close_rule: str,
        buy_rule: str,
        sell_rule: str,
    ) -> Optional[dict]:
        """创建自定义策略"""
        pass

    @abstractmethod
    async def get_custom_strategy(self, user_id: int, strategy_key: str) -> Optional[dict]:
        """获取自定义策略"""
        pass

    @abstractmethod
    async def list_custom_strategies(self, user_id: int) -> List[dict]:
        """列出用户的所有自定义策略"""
        pass

    @abstractmethod
    async def update_custom_strategy(
        self,
        user_id: int,
        strategy_key: str,
        label: Optional[str] = None,
        open_rule: Optional[str] = None,
        close_rule: Optional[str] = None,
        buy_rule: Optional[str] = None,
        sell_rule: Optional[str] = None,
    ) -> Optional[dict]:
        """更新自定义策略"""
        pass

    @abstractmethod
    async def delete_custom_strategy(self, user_id: int, strategy_key: str) -> bool:
        """删除自定义策略"""
        pass