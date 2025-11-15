"""
数据源配置管理器
管理多个数据源的配置，支持用户选择和配置不同的数据源
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum
import logging


class DataSourceType(Enum):
    """数据源类型枚举"""
    TUSHARE = "tushare"
    BAOSTOCK = "baostock"
    YAHOO = "yahoo"
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"


class DataSourcePriority(Enum):
    """数据源优先级枚举"""
    PRIMARY = "primary"      # 主要数据源
    SECONDARY = "secondary"  # 备用数据源
    FALLBACK = "fallback"    # 兜底数据源


@dataclass
class DataSourceCredentials:
    """数据源凭证配置"""
    api_key: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_url: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_times: int = 3


@dataclass
class DataSourceSettings:
    """数据源设置配置"""
    enabled: bool = True
    priority: DataSourcePriority = DataSourcePriority.SECONDARY
    cache_enabled: bool = True
    cache_ttl: int = 3600
    rate_limit: int = 120  # 每分钟请求次数
    max_concurrent_requests: int = 5
    use_as_backup: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSourceConfig:
    """单个数据源配置"""
    source_type: DataSourceType
    name: str
    description: str = ""
    credentials: DataSourceCredentials = field(default_factory=DataSourceCredentials)
    settings: DataSourceSettings = field(default_factory=DataSourceSettings)
    is_configured: bool = False
    last_test_time: Optional[str] = None
    test_status: Optional[str] = None

    def validate(self) -> bool:
        """验证配置是否完整有效"""
        if not self.settings.enabled:
            return True

        # 根据数据源类型验证必需的凭证
        if self.source_type == DataSourceType.TUSHARE:
            return bool(self.credentials.token)
        elif self.source_type == DataSourceType.YAHOO:
            return True  # Yahoo Finance通常不需要token
        elif self.source_type == DataSourceType.BAOSTOCK:
            return True  # Baostock通常不需要token
        else:
            return bool(self.credentials.api_key or self.credentials.token)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source_type': self.source_type.value,
            'name': self.name,
            'description': self.description,
            'credentials': {
                'api_key': self.credentials.api_key,
                'token': self.credentials.token,
                'username': self.credentials.username,
                'password': self.credentials.password,
                'proxy_url': self.credentials.proxy_url,
                'custom_headers': self.credentials.custom_headers,
                'timeout': self.credentials.timeout,
                'retry_times': self.credentials.retry_times
            },
            'settings': {
                'enabled': self.settings.enabled,
                'priority': self.settings.priority.value,
                'cache_enabled': self.settings.cache_enabled,
                'cache_ttl': self.settings.cache_ttl,
                'rate_limit': self.settings.rate_limit,
                'max_concurrent_requests': self.settings.max_concurrent_requests,
                'use_as_backup': self.settings.use_as_backup,
                'custom_params': self.settings.custom_params
            },
            'is_configured': self.is_configured,
            'last_test_time': self.last_test_time,
            'test_status': self.test_status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSourceConfig':
        """从字典创建配置"""
        credentials = DataSourceCredentials(**data.get('credentials', {}))
        settings_data = data.get('settings', {})
        settings_data['priority'] = DataSourcePriority(settings_data.get('priority', 'secondary'))
        settings = DataSourceSettings(**settings_data)

        return cls(
            source_type=DataSourceType(data['source_type']),
            name=data['name'],
            description=data.get('description', ''),
            credentials=credentials,
            settings=settings,
            is_configured=data.get('is_configured', False),
            last_test_time=data.get('last_test_time'),
            test_status=data.get('test_status')
        )


class DataSourceManager:
    """数据源配置管理器"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "data_sources.json"
        self.logger = logging.getLogger(__name__)

        # 创建配置目录
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 支持的数据源定义
        self.supported_sources = self._get_supported_sources()

        # 加载配置
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self.load_config()

        # 当前选择的数据源
        self.current_data_source: Optional[str] = None
        self._load_current_selection()

    def _get_supported_sources(self) -> Dict[DataSourceType, Dict[str, Any]]:
        """获取支持的数据源定义"""
        return {
            DataSourceType.TUSHARE: {
                'name': 'Tushare',
                'description': '国内专业金融数据接口，数据质量高，需要注册获取token',
                'website': 'https://tushare.pro',
                'requires_token': True,
                'rate_limit': 120,  # 每分钟
                'features': ['股票基本信息', '日线数据', '实时行情', '财务数据', '指数数据']
            },
            DataSourceType.BAOSTOCK: {
                'name': 'Baostock',
                'description': '免费、开源的证券数据平台',
                'website': 'https://baostock.com',
                'requires_token': False,
                'rate_limit': 100,  # 每分钟
                'features': ['股票基本信息', '日线数据', '复权数据']
            },
            DataSourceType.YAHOO: {
                'name': 'Yahoo Finance',
                'description': 'Yahoo财经接口，支持全球市场数据',
                'website': 'https://finance.yahoo.com',
                'requires_token': False,
                'rate_limit': 100,  # 每分钟
                'features': ['股票基本信息', '日线数据', '实时行情', '全球市场']
            },
            DataSourceType.AKSHARE: {
                'name': 'AKShare',
                'description': '基于Python的财经数据接口库',
                'website': 'https://akshare.akfamily.xyz',
                'requires_token': False,
                'rate_limit': 100,  # 每分钟
                'features': ['A股数据', '期货数据', '宏观经济', '行业数据']
            }
        }

    def get_supported_sources(self) -> Dict[DataSourceType, Dict[str, Any]]:
        """获取支持的数据源列表"""
        return self.supported_sources.copy()

    def add_data_source(self, config: DataSourceConfig) -> bool:
        """添加数据源配置"""
        try:
            if config.source_type not in self.supported_sources:
                self.logger.error(f"不支持的数据源类型: {config.source_type}")
                return False

            # 验证配置
            if not config.validate():
                self.logger.error(f"数据源配置验证失败: {config.name}")
                return False

            config.is_configured = True
            self.data_sources[config.name] = config
            self.save_config()

            self.logger.info(f"成功添加数据源配置: {config.name}")
            return True

        except Exception as e:
            self.logger.error(f"添加数据源配置失败: {e}")
            return False

    def update_data_source(self, name: str, config: DataSourceConfig) -> bool:
        """更新数据源配置"""
        if name not in self.data_sources:
            self.logger.error(f"数据源不存在: {name}")
            return False

        try:
            if not config.validate():
                self.logger.error(f"数据源配置验证失败: {config.name}")
                return False

            config.is_configured = True
            self.data_sources[name] = config
            self.save_config()

            self.logger.info(f"成功更新数据源配置: {name}")
            return True

        except Exception as e:
            self.logger.error(f"更新数据源配置失败: {e}")
            return False

    def remove_data_source(self, name: str) -> bool:
        """删除数据源配置"""
        if name not in self.data_sources:
            self.logger.error(f"数据源不存在: {name}")
            return False

        try:
            del self.data_sources[name]
            self.save_config()

            self.logger.info(f"成功删除数据源配置: {name}")
            return True

        except Exception as e:
            self.logger.error(f"删除数据源配置失败: {e}")
            return False

    def get_data_source(self, name: str) -> Optional[DataSourceConfig]:
        """获取指定数据源配置"""
        return self.data_sources.get(name)

    def get_all_data_sources(self) -> Dict[str, DataSourceConfig]:
        """获取所有数据源配置"""
        return self.data_sources.copy()

    def get_enabled_data_sources(self) -> Dict[str, DataSourceConfig]:
        """获取启用的数据源配置"""
        return {name: config for name, config in self.data_sources.items()
                if config.settings.enabled and config.is_configured}

    def get_data_sources_by_priority(self) -> List[DataSourceConfig]:
        """按优先级排序获取数据源"""
        enabled_sources = list(self.get_enabled_data_sources().values())

        # 按优先级排序
        priority_order = {
            DataSourcePriority.PRIMARY: 0,
            DataSourcePriority.SECONDARY: 1,
            DataSourcePriority.FALLBACK: 2
        }

        return sorted(enabled_sources,
                     key=lambda x: priority_order.get(x.settings.priority, 3))

    def set_primary_source(self, name: str) -> bool:
        """设置主要数据源"""
        if name not in self.data_sources:
            self.logger.error(f"数据源不存在: {name}")
            return False

        try:
            # 将所有其他数据源的优先级设为非主要
            for source_name, config in self.data_sources.items():
                if config.settings.priority == DataSourcePriority.PRIMARY:
                    config.settings.priority = DataSourcePriority.SECONDARY

            # 设置指定数据源为主要
            self.data_sources[name].settings.priority = DataSourcePriority.PRIMARY
            self.save_config()

            self.logger.info(f"成功设置主要数据源: {name}")
            return True

        except Exception as e:
            self.logger.error(f"设置主要数据源失败: {e}")
            return False

    def set_data_source_status(self, name: str, enabled: bool) -> bool:
        """设置数据源启用状态"""
        if name not in self.data_sources:
            self.logger.error(f"数据源不存在: {name}")
            return False

        try:
            self.data_sources[name].settings.enabled = enabled
            self.save_config()

            self.logger.info(f"成功设置数据源状态: {name} = {'启用' if enabled else '禁用'}")
            return True

        except Exception as e:
            self.logger.error(f"设置数据源状态失败: {e}")
            return False

    def update_test_status(self, name: str, success: bool, message: str = "") -> bool:
        """更新数据源测试状态"""
        if name not in self.data_sources:
            return False

        try:
            from datetime import datetime
            config = self.data_sources[name]
            config.last_test_time = datetime.now().isoformat()
            config.test_status = "成功" if success else f"失败: {message}"

            self.save_config()
            return True

        except Exception as e:
            self.logger.error(f"更新测试状态失败: {e}")
            return False

    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if not self.config_file.exists():
                # 创建默认配置
                self._create_default_config()
                return True

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.data_sources = {}
            for source_data in data.get('data_sources', []):
                config = DataSourceConfig.from_dict(source_data)
                self.data_sources[config.name] = config

            self.logger.info(f"成功加载 {len(self.data_sources)} 个数据源配置")
            return True

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return False

    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            data = {
                'version': '1.0',
                'data_sources': [config.to_dict() for config in self.data_sources.values()]
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False

    def _load_current_selection(self):
        """加载当前选择的数据源"""
        try:
            # 尝试从环境变量读取
            env_selection = os.getenv('SELECTED_DATA_SOURCE')
            if env_selection:
                self.current_data_source = env_selection
                self.logger.info(f"从环境变量加载数据源选择: {env_selection}")
                return

            # 从环境变量读取备选
            env_selection = os.getenv('DATA_SOURCE_TYPE')
            if env_selection:
                # 转换为标准名称
                if env_selection.lower() in ['tushare', 'baostock']:
                    self.current_data_source = env_selection.title()
                    self.logger.info(f"从备选环境变量加载数据源选择: {self.current_data_source}")
                    return

            # 默认选择第一个可用的数据源
            enabled_sources = self.get_enabled_data_sources()
            if enabled_sources:
                self.current_data_source = list(enabled_sources.keys())[0]
                self.logger.info(f"使用默认数据源: {self.current_data_source}")
            else:
                self.logger.warning("没有可用的数据源")

        except Exception as e:
            self.logger.error(f"加载数据源选择失败: {e}")
            self.current_data_source = "Baostock"  # 默认值

    def set_current_data_source(self, name: str) -> bool:
        """设置当前使用的数据源"""
        try:
            if name not in self.data_sources:
                self.logger.error(f"数据源不存在: {name}")
                return False

            if not self.data_sources[name].settings.enabled:
                self.logger.error(f"数据源未启用: {name}")
                return False

            self.current_data_source = name
            # 保存到环境变量
            os.environ['SELECTED_DATA_SOURCE'] = name

            self.logger.info(f"设置当前数据源: {name}")
            return True

        except Exception as e:
            self.logger.error(f"设置数据源失败: {e}")
            return False

    def get_current_data_source(self) -> Optional[str]:
        """获取当前使用的数据源名称"""
        return self.current_data_source

    def get_current_data_source_config(self) -> Optional[DataSourceConfig]:
        """获取当前使用的数据源配置"""
        if self.current_data_source:
            return self.data_sources.get(self.current_data_source)
        return None

    def _create_default_config(self):
        """创建默认配置"""
        # 从环境变量加载Tushare token
        tushare_token = os.getenv('TUSHARE_TOKEN')

        # 添加一些常用的数据源配置模板
        default_configs = [
            DataSourceConfig(
                source_type=DataSourceType.TUSHARE,
                name="Tushare",
                description="Tushare数据源",
                credentials=DataSourceCredentials(
                    token=tushare_token if tushare_token and tushare_token.strip() != "" else None
                ),
                settings=DataSourceSettings(
                    enabled=bool(tushare_token and tushare_token.strip() != ""),  # 有token则启用
                    priority=DataSourcePriority.PRIMARY
                )
            ),
            DataSourceConfig(
                source_type=DataSourceType.BAOSTOCK,
                name="Baostock",
                description="Baostock数据源",
                settings=DataSourceSettings(
                    enabled=True,  # 默认启用，不需要token
                    priority=DataSourcePriority.FALLBACK
                )
            )
        ]

        for config in default_configs:
            self.data_sources[config.name] = config

        # 记录Tushare配置状态
        if tushare_token and tushare_token.strip() != "":
            self.logger.info("从环境变量加载Tushare token，Tushare数据源已启用")
        else:
            self.logger.info("未找到有效的Tushare token，Tushare数据源保持禁用状态")

        self.save_config()

    def update_tushare_token_from_env(self):
        """从环境变量更新Tushare token"""
        try:
            tushare_token = os.getenv('TUSHARE_TOKEN')

            if 'Tushare' not in self.data_sources:
                self.logger.warning("Tushare数据源配置不存在")
                return False

            tushare_config = self.data_sources['Tushare']

            # 更新token
            old_token = tushare_config.credentials.token
            tushare_config.credentials.token = tushare_token if tushare_token and tushare_token.strip() != "" else None

            # 更新启用状态
            was_enabled = tushare_config.settings.enabled
            tushare_config.settings.enabled = bool(tushare_config.credentials.token)

            self.save_config()

            if old_token != tushare_config.credentials.token:
                self.logger.info(f"Tushare token已从环境变量更新")
                if tushare_config.credentials.token:
                    self.logger.info("Tushare数据源已启用")
                else:
                    self.logger.info("Tushare数据源已禁用（无有效token）")

            return True

        except Exception as e:
            self.logger.error(f"更新Tushare token失败: {e}")
            return False

    def export_config(self, file_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'version': '1.0',
                'data_sources': [config.to_dict() for config in self.data_sources.values()]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功导出配置到: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False

    def import_config(self, file_path: str, merge: bool = False) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if not merge:
                self.data_sources.clear()

            for source_data in import_data.get('data_sources', []):
                config = DataSourceConfig.from_dict(source_data)
                self.data_sources[config.name] = config

            self.save_config()
            self.logger.info(f"成功导入配置，共 {len(self.data_sources)} 个数据源")
            return True

        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        total_sources = len(self.data_sources)
        enabled_sources = len(self.get_enabled_data_sources())
        configured_sources = len([s for s in self.data_sources.values() if s.is_configured])
        primary_source = next((name for name, config in self.data_sources.items()
                             if config.settings.priority == DataSourcePriority.PRIMARY), None)

        return {
            'total_sources': total_sources,
            'enabled_sources': enabled_sources,
            'configured_sources': configured_sources,
            'primary_source': primary_source,
            'supported_types': [stype.value for stype in self.supported_sources.keys()]
        }


# 全局配置管理器实例
_global_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = DataSourceManager()
    return _global_manager


def init_data_source_manager(config_dir: str = "./config") -> DataSourceManager:
    """初始化全局数据源管理器"""
    global _global_manager
    _global_manager = DataSourceManager(config_dir)
    return _global_manager