"""
Tushare服务适配器 - 将TushareMarketService适配到DataFactory接口
职责：将新的细粒度tushare服务适配到现有的DataSource接口
"""

import pandas as pd
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, date
from ..data_source import DataSource
from src.services.data.tushare_market_service import TushareMarketService
from src.core.data.config.tushare_config import TushareConfig, init_global_config_from_env


class TushareServiceAdapter(DataSource):
    """
    Tushare服务适配器
    将TushareMarketService适配到DataSource接口，使其能够在DataFactory中使用
    """

    def __init__(self, config: Optional[TushareConfig] = None, **kwargs):
        """
        初始化适配器

        Args:
            config: Tushare配置，如果为None则从环境变量加载
            **kwargs: 其他配置参数
        """
        super().__init__()

        # 加载配置
        if config is None:
            try:
                self.config = init_global_config_from_env()
            except Exception:
                # 如果环境变量配置失败，尝试使用默认配置
                self.config = TushareConfig(
                    token=kwargs.get('token', ''),
                    cache_enabled=kwargs.get('cache_enabled', True),
                    cache_ttl=kwargs.get('cache_ttl', 3600),
                    rate_limit=kwargs.get('rate_limit', 120)
                )
        else:
            self.config = config

        # 初始化服务
        self.service = TushareMarketService(self.config)
        self._default_frequency = kwargs.get('default_frequency', 'D')

    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """
        实现DataSource抽象方法 - 加载数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率

        Returns:
            市场数据DataFrame
        """
        try:
            # 确保日期格式正确
            if isinstance(start_date, (date, datetime)):
                start_date_str = start_date.strftime('%Y%m%d')
            else:
                start_date_str = start_date.replace('-', '')

            if isinstance(end_date, (date, datetime)):
                end_date_str = end_date.strftime('%Y%m%d')
            else:
                end_date_str = end_date.replace('-', '')

            # 调用tushare服务
            data = await self.service.get_market_data(
                symbol_code=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                frequency=frequency
            )

            # 转换日期格式为系统标准格式
            if not data.empty and 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

            return data

        except Exception as e:
            raise RuntimeError(f"加载tushare数据失败: {e}")

    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """
        实现DataSource抽象方法 - 保存数据
        注意：这是一个同步方法包装异步服务

        Args:
            data: 要保存的数据
            symbol: 股票代码
            frequency: 频率

        Returns:
            是否保存成功
        """
        try:
            # 获取事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，需要使用其他方法
                # 这里简化处理，实际使用中可能需要更复杂的异步管理
                import warnings
                warnings.warn("在异步环境中调用同步save_data方法，结果可能不可靠", UserWarning)
                return False
            else:
                # 如果不在异步环境中，创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 如果配置了保存到数据库，调用保存逻辑
                    if self.config.save_to_db:
                        # 这里应该调用数据库保存逻辑
                        # 由于tushare服务主要是数据获取，暂时返回True
                        return True
                    return False
                finally:
                    loop.close()

        except Exception as e:
            print(f"保存数据失败: {e}")
            return False

    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """
        实现DataSource抽象方法 - 检查数据是否存在
        对于tushare数据源，总是返回True，因为数据是从远程API获取

        Args:
            symbol: 股票代码
            frequency: 频率

        Returns:
            是否存在数据（总是返回True）
        """
        return True

    async def get_stock_list(self, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """
        获取股票列表

        Args:
            exchange: 交易所代码
            list_status: 上市状态

        Returns:
            股票列表DataFrame
        """
        try:
            return await self.service.get_stock_list(exchange=exchange, list_status=list_status)
        except Exception as e:
            raise RuntimeError(f"获取股票列表失败: {e}")

    async def get_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单个股票的基本信息

        Args:
            symbol: 股票代码

        Returns:
            股票基本信息字典
        """
        try:
            stock_list = await self.get_stock_list()
            stock_info = stock_list[stock_list['symbol_code'] == symbol]

            if not stock_info.empty:
                return stock_info.iloc[0].to_dict()
            return None

        except Exception as e:
            raise RuntimeError(f"获取股票基本信息失败: {e}")

    async def get_realtime_quotes(self, symbols: list) -> pd.DataFrame:
        """
        获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            实时行情DataFrame
        """
        try:
            return await self.service.get_realtime_quotes(symbols)
        except Exception as e:
            raise RuntimeError(f"获取实时行情失败: {e}")

    async def get_financial_data(self, symbol: str, start_date: str, end_date: str,
                               report_type: str = '1') -> pd.DataFrame:
        """
        获取财务数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            report_type: 报告类型

        Returns:
            财务数据DataFrame
        """
        try:
            # 确保日期格式正确
            if isinstance(start_date, (date, datetime)):
                start_date_str = start_date.strftime('%Y%m%d')
            else:
                start_date_str = start_date.replace('-', '')

            if isinstance(end_date, (date, datetime)):
                end_date_str = end_date.strftime('%Y%m%d')
            else:
                end_date_str = end_date.replace('-', '')

            return await self.service.get_financial_data(
                symbol_code=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                report_type=report_type
            )

        except Exception as e:
            raise RuntimeError(f"获取财务数据失败: {e}")

    async def get_index_list(self, exchange: str = '', market: str = '') -> pd.DataFrame:
        """
        获取指数列表

        Args:
            exchange: 交易所代码
            market: 市场代码

        Returns:
            指数列表DataFrame
        """
        try:
            return await self.service.get_index_basic(exchange=exchange, market=market)
        except Exception as e:
            raise RuntimeError(f"获取指数列表失败: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接

        Returns:
            连接测试结果
        """
        return await self.service.test_connection()

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            服务统计信息
        """
        return await self.service.get_service_stats()

    async def clear_cache(self, pattern: str = None, tags: list = None) -> Dict[str, Any]:
        """
        清理缓存

        Args:
            pattern: 缓存键模式
            tags: 缓存标签

        Returns:
            清理结果
        """
        return await self.service.clear_cache(pattern=pattern, tags=tags)

    def get_available_fields(self, symbol: str) -> list:
        """
        获取可用数据字段

        Args:
            symbol: 股票代码

        Returns:
            可用字段列表
        """
        # 返回tushare市场数据的标准字段
        return [
            'symbol_code', 'date', 'open', 'high', 'low', 'close',
            'prev_close', 'change', 'pct_change', 'volume', 'amount',
            'transformed_at', 'data_source'
        ]

    def get_data(self, symbol: str, fields: list, start_date: str = None,
                end_date: str = None, frequency: str = 'D') -> pd.DataFrame:
        """
        同步获取数据（兼容旧接口）

        Args:
            symbol: 股票代码
            fields: 需要的字段列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率

        Returns:
            数据DataFrame
        """
        try:
            # 设置默认日期
            if start_date is None:
                start_date = self.config.default_start_date
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')

            # 获取事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在异步环境中，使用run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.load_data(symbol, start_date, end_date, frequency)
                        )
                        data = future.result()
                else:
                    # 如果不在异步环境中，直接运行
                    data = loop.run_until_complete(
                        self.load_data(symbol, start_date, end_date, frequency)
                    )
            except RuntimeError:
                # 如果没有事件循环，创建新的
                data = asyncio.run(self.load_data(symbol, start_date, end_date, frequency))

            # 过滤字段
            if not data.empty and fields:
                available_fields = [field for field in fields if field in data.columns]
                if available_fields:
                    data = data[available_fields]

            return data

        except Exception as e:
            raise RuntimeError(f"获取数据失败: {e}")

    def get_config(self) -> TushareConfig:
        """
        获取当前配置

        Returns:
            Tushare配置
        """
        return self.config

    def update_config(self, **kwargs) -> None:
        """
        更新配置

        Args:
            **kwargs: 配置参数
        """
        self.config = self.config.update(**kwargs)
        # 重新初始化服务
        self.service = TushareMarketService(self.config)