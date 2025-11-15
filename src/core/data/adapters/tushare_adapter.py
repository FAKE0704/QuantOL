"""
Tushare数据源适配器 - 只负责与tushare SDK交互
职责：封装tushare SDK调用，不包含业务逻辑
"""

import pandas as pd
from typing import List, Optional, Dict, Any
import logging
import time
from datetime import datetime, timedelta


class TushareAdapterError(Exception):
    """Tushare适配器错误"""
    pass


class TushareAdapter:
    """Tushare数据源适配器 - 只负责SDK调用"""

    def __init__(self, token: str):
        """
        初始化Tushare适配器

        Args:
            token: Tushare Pro API token
        """
        self.token = token
        self._pro = None
        self._last_request_time = 0
        self._min_request_interval = 0.05  # 最小请求间隔50ms，避免频率限制
        self.logger = logging.getLogger(__name__)

    def _get_pro(self):
        """
        获取tushare pro实例（懒加载）

        Returns:
            tushare pro实例
        """
        if self._pro is None:
            try:
                import tushare as ts
                self._pro = ts.pro_api(self.token)
                self.logger.info("Tushare Pro API 初始化成功")
            except ImportError as e:
                raise TushareAdapterError(f"Tushare库未安装: {e}")
            except Exception as e:
                raise TushareAdapterError(f"Tushare初始化失败: {e}")
        return self._pro

    def _rate_limit(self):
        """简单的频率控制"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def get_stock_basic(self, exchange: str = '', list_status: str = 'L',
                       fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取股票基本信息

        Args:
            exchange: 交易所代码 (SSE上交所, SZSE深交所, CFFEX中金所, SHFE上期所, DCE大商所, CZCE郑商所, INE上能源, CFXE中金所)
            list_status: 上市状态 (L上市, D退市, P暂停)
            fields: 需要返回的字段列表

        Returns:
            包含股票基本信息的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            # 默认字段
            if fields is None:
                fields = [
                    'ts_code', 'symbol', 'name', 'area', 'industry', 'cnspell',
                    'market', 'list_date', 'act_name', 'act_ent_type'
                ]

            params = {
                'exchange': exchange,
                'list_status': list_status,
                'fields': ','.join(fields)
            }

            self.logger.debug(f"获取股票基本信息: {params}")
            df = pro.stock_basic(**params)

            if df.empty:
                self.logger.warning("未获取到股票基本信息")

            self.logger.info(f"成功获取 {len(df)} 条股票基本信息")
            return df

        except Exception as e:
            self.logger.error(f"获取股票基本信息失败: {e}")
            raise TushareAdapterError(f"获取股票基本信息失败: {e}")

    def get_daily_data(self, ts_code: str, start_date: str, end_date: str,
                      fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            ts_code: 股票代码 (包含交易所后缀，如: 000001.SZ)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            fields: 需要返回的字段列表

        Returns:
            包含日线数据的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            # 默认字段
            if fields is None:
                fields = [
                    'ts_code', 'trade_date', 'open', 'high', 'low', 'close',
                    'pre_close', 'change', 'pct_chg', 'vol', 'amount'
                ]

            params = {
                'ts_code': ts_code,
                'start_date': start_date,
                'end_date': end_date
            }

            self.logger.debug(f"获取日线数据: {params}")
            df = pro.daily(**params)

            # 如果指定了字段，进行过滤
            if fields:
                df = df[fields] if not df.empty and all(col in df.columns for col in fields) else df

            if df.empty:
                self.logger.warning(f"未获取到股票 {ts_code} 的日线数据")

            self.logger.info(f"成功获取股票 {ts_code} {len(df)} 条日线数据")
            return df

        except Exception as e:
            self.logger.error(f"获取日线数据失败: {e}")
            raise TushareAdapterError(f"获取日线数据失败: {e}")

    def get_realtime_quote(self, ts_codes: List[str]) -> pd.DataFrame:
        """
        获取实时行情数据

        Args:
            ts_codes: 股票代码列表

        Returns:
            包含实时行情的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            # 将代码列表转换为逗号分隔的字符串
            ts_code_str = ','.join(ts_codes)

            params = {
                'ts_code': ts_code_str
            }

            self.logger.debug(f"获取实时行情: {params}")
            df = pro.realtime_quote(**params)

            if df.empty:
                self.logger.warning("未获取到实时行情数据")

            self.logger.info(f"成功获取 {len(df)} 条实时行情数据")
            return df

        except Exception as e:
            self.logger.error(f"获取实时行情失败: {e}")
            raise TushareAdapterError(f"获取实时行情失败: {e}")

    def get_financial_data(self, ts_code: str, start_date: str, end_date: str,
                          report_type: str = '1') -> pd.DataFrame:
        """
        获取财务数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            report_type: 报告类型 (1合并报表, 2单季合并, 3合并现金流量表, 4单季现金流量表)

        Returns:
            包含财务数据的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            params = {
                'ts_code': ts_code,
                'start_date': start_date,
                'end_date': end_date,
                'report_type': report_type
            }

            self.logger.debug(f"获取财务数据: {params}")
            df = pro.fina_indicator(**params)

            if df.empty:
                self.logger.warning(f"未获取到股票 {ts_code} 的财务数据")

            self.logger.info(f"成功获取股票 {ts_code} {len(df)} 条财务数据")
            return df

        except Exception as e:
            self.logger.error(f"获取财务数据失败: {e}")
            raise TushareAdapterError(f"获取财务数据失败: {e}")

    def get_index_basic(self, exchange: str = '', market: str = '') -> pd.DataFrame:
        """
        获取指数基本信息

        Args:
            exchange: 交易所代码
            market: 市场代码 (MSCI, CSI, SSE, SZSE, CICC, SW)

        Returns:
            包含指数基本信息的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            params = {
                'exchange': exchange,
                'market': market
            }

            self.logger.debug(f"获取指数基本信息: {params}")
            df = pro.index_basic(**params)

            if df.empty:
                self.logger.warning("未获取到指数基本信息")

            self.logger.info(f"成功获取 {len(df)} 条指数基本信息")
            return df

        except Exception as e:
            self.logger.error(f"获取指数基本信息失败: {e}")
            raise TushareAdapterError(f"获取指数基本信息失败: {e}")

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数日线行情

        Args:
            ts_code: 指数代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            包含指数日线数据的DataFrame
        """
        try:
            self._rate_limit()
            pro = self._get_pro()

            params = {
                'ts_code': ts_code,
                'start_date': start_date,
                'end_date': end_date
            }

            self.logger.debug(f"获取指数日线数据: {params}")
            df = pro.index_daily(**params)

            if df.empty:
                self.logger.warning(f"未获取到指数 {ts_code} 的日线数据")

            self.logger.info(f"成功获取指数 {ts_code} {len(df)} 条日线数据")
            return df

        except Exception as e:
            self.logger.error(f"获取指数日线数据失败: {e}")
            raise TushareAdapterError(f"获取指数日线数据失败: {e}")

    def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            连接是否成功
        """
        try:
            # 尝试获取少量数据来测试连接
            self.get_stock_basic(exchange='', list_status='L')
            self.logger.info("Tushare连接测试成功")
            return True
        except Exception as e:
            self.logger.error(f"Tushare连接测试失败: {e}")
            return False