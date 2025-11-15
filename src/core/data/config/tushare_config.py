"""
Tushare配置管理器 - 负责tushare相关配置
职责：管理tushare数据源的配置信息，支持从环境变量和配置文件加载
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import logging


@dataclass
class TushareConfig:
    """
    Tushare配置管理
    """
    # 必需配置
    token: str

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 默认缓存1小时
    cache_dir: str = "./data/tushare/cache"

    # API调用配置
    rate_limit: int = 120  # 每分钟请求次数限制
    retry_times: int = 3  # 重试次数
    timeout: int = 30  # 请求超时时间（秒）

    # 请求间隔配置
    min_request_interval: float = 0.5  # 最小请求间隔（秒）
    max_request_interval: float = 2.0  # 最大请求间隔（秒）

    # 日志配置
    log_level: str = "INFO"
    log_requests: bool = False  # 是否记录每次请求

    # 数据获取配置
    default_start_date: str = "20200101"  # 默认开始日期
    max_records_per_request: int = 5000  # 每次请求最大记录数

    # 数据库配置
    save_to_db: bool = True
    db_batch_size: int = 1000  # 数据库批量写入大小

    # 其他配置
    user_agent: str = "TushareClient/1.0"
    proxy_url: Optional[str] = None  # 代理URL

    def __post_init__(self):
        """初始化后的验证和设置"""
        self.validate()

    @classmethod
    def from_env(cls, prefix: str = "TUSHARE_") -> 'TushareConfig':
        """
        从环境变量加载配置

        Args:
            prefix: 环境变量前缀

        Returns:
            TushareConfig实例
        """
        config_dict = {}

        # 环境变量映射
        env_mapping = {
            'TOKEN': 'token',
            'CACHE_ENABLED': 'cache_enabled',
            'CACHE_TTL': 'cache_ttl',
            'CACHE_DIR': 'cache_dir',
            'RATE_LIMIT': 'rate_limit',
            'RETRY_TIMES': 'retry_times',
            'TIMEOUT': 'timeout',
            'MIN_REQUEST_INTERVAL': 'min_request_interval',
            'MAX_REQUEST_INTERVAL': 'max_request_interval',
            'LOG_LEVEL': 'log_level',
            'LOG_REQUESTS': 'log_requests',
            'DEFAULT_START_DATE': 'default_start_date',
            'MAX_RECORDS_PER_REQUEST': 'max_records_per_request',
            'SAVE_TO_DB': 'save_to_db',
            'DB_BATCH_SIZE': 'db_batch_size',
            'USER_AGENT': 'user_agent',
            'PROXY_URL': 'proxy_url'
        }

        # 读取环境变量
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(f"{prefix}{env_key}")
            if env_value is not None:
                # 类型转换
                if config_key in ['cache_enabled', 'log_requests', 'save_to_db']:
                    config_dict[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ['cache_ttl', 'rate_limit', 'retry_times', 'timeout',
                                   'min_request_interval', 'max_request_interval',
                                   'max_records_per_request', 'db_batch_size']:
                    config_dict[config_key] = int(env_value)
                elif config_key == 'proxy_url':
                    config_dict[config_key] = env_value if env_value.strip() else None
                else:
                    config_dict[config_key] = env_value

        # 检查必需的token
        if 'token' not in config_dict:
            raise ValueError(f"环境变量 {prefix}TOKEN 未设置")

        return cls(**config_dict)

    @classmethod
    def from_file(cls, config_path: str) -> 'TushareConfig':
        """
        从配置文件加载配置

        Args:
            config_path: 配置文件路径（JSON格式）

        Returns:
            TushareConfig实例
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls(**config_dict)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def save_to_file(self, config_path: str) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            # 创建目录
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典并保存
            config_dict = self.to_dict()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False

    def validate(self) -> bool:
        """
        验证配置有效性

        Returns:
            配置是否有效

        Raises:
            ValueError: 配置无效时抛出
        """
        if not self.token or len(self.token.strip()) == 0:
            raise ValueError("Tushare token不能为空")

        if self.cache_ttl <= 0:
            raise ValueError("缓存时间必须大于0")

        if self.rate_limit <= 0:
            raise ValueError("请求频率限制必须大于0")

        if self.retry_times < 0:
            raise ValueError("重试次数不能为负数")

        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")

        if self.min_request_interval < 0:
            raise ValueError("最小请求间隔不能为负数")

        if self.max_request_interval < self.min_request_interval:
            raise ValueError("最大请求间隔必须大于等于最小请求间隔")

        if self.max_records_per_request <= 0:
            raise ValueError("最大记录数必须大于0")

        if self.db_batch_size <= 0:
            raise ValueError("数据库批量大小必须大于0")

        # 验证日志级别
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"日志级别必须是以下之一: {valid_log_levels}")

        # 验证缓存目录
        if self.cache_dir:
            cache_path = Path(self.cache_dir)
            # 检查是否可以创建缓存目录（但不实际创建）
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"无法创建缓存目录 {cache_path.parent}: {e}")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            配置字典
        """
        return {
            'token': self.token,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'cache_dir': self.cache_dir,
            'rate_limit': self.rate_limit,
            'retry_times': self.retry_times,
            'timeout': self.timeout,
            'min_request_interval': self.min_request_interval,
            'max_request_interval': self.max_request_interval,
            'log_level': self.log_level,
            'log_requests': self.log_requests,
            'default_start_date': self.default_start_date,
            'max_records_per_request': self.max_records_per_request,
            'save_to_db': self.save_to_db,
            'db_batch_size': self.db_batch_size,
            'user_agent': self.user_agent,
            'proxy_url': self.proxy_url
        }

    def update(self, **kwargs) -> 'TushareConfig':
        """
        更新配置并返回新的配置实例

        Args:
            **kwargs: 要更新的配置项

        Returns:
            更新后的TushareConfig实例
        """
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return TushareConfig(**current_dict)

    def get_cache_config(self) -> Dict[str, Any]:
        """
        获取缓存相关配置

        Returns:
            缓存配置字典
        """
        return {
            'enabled': self.cache_enabled,
            'ttl': self.cache_ttl,
            'cache_dir': self.cache_dir
        }

    def get_api_config(self) -> Dict[str, Any]:
        """
        获取API调用相关配置

        Returns:
            API配置字典
        """
        return {
            'token': self.token,
            'rate_limit': self.rate_limit,
            'retry_times': self.retry_times,
            'timeout': self.timeout,
            'min_request_interval': self.min_request_interval,
            'max_request_interval': self.max_request_interval,
            'user_agent': self.user_agent,
            'proxy_url': self.proxy_url
        }

    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库相关配置

        Returns:
            数据库配置字典
        """
        return {
            'save_to_db': self.save_to_db,
            'batch_size': self.db_batch_size
        }

    def get_log_config(self) -> Dict[str, Any]:
        """
        获取日志相关配置

        Returns:
            日志配置字典
        """
        return {
            'level': self.log_level.upper(),
            'log_requests': self.log_requests
        }

    def __str__(self) -> str:
        """字符串表示（隐藏敏感信息）"""
        return f"""TushareConfig:
    Token: {'*' * 10}{self.token[-4:] if self.token else 'None'}
    Cache: {'Enabled' if self.cache_enabled else 'Disabled'}
    Cache TTL: {self.cache_ttl}s
    Rate Limit: {self.rate_limit}/min
    Retry Times: {self.retry_times}
    Timeout: {self.timeout}s
    Log Level: {self.log_level}
    Save to DB: {'Yes' if self.save_to_db else 'No'}"""

    def clone(self) -> 'TushareConfig':
        """
        克隆配置实例

        Returns:
            新的TushareConfig实例
        """
        return TushareConfig(**self.to_dict())

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        获取默认配置模板

        Returns:
            默认配置字典
        """
        # 创建一个默认实例，然后获取字典
        default_instance = TushareConfig(
            token="your_tushare_token_here"
        )
        return default_instance.to_dict()

    @staticmethod
    def create_config_template(file_path: str) -> bool:
        """
        创建配置文件模板

        Args:
            file_path: 配置文件路径

        Returns:
            是否创建成功
        """
        try:
            default_config = TushareConfig.get_default_config()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)

            # 添加说明注释
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("""{
  "_comment": "Tushare配置文件 - 请修改以下配置项",
  "_comment_token": "在 https://tushare.pro 注册并获取token",
""")
                f.write(content)

            return True
        except Exception as e:
            logging.error(f"创建配置模板失败: {e}")
            return False


# 全局配置实例（可选，用于单例模式）
_global_config: Optional[TushareConfig] = None


def get_global_config() -> Optional[TushareConfig]:
    """
    获取全局配置实例

    Returns:
        全局配置实例
    """
    return _global_config


def set_global_config(config: TushareConfig) -> None:
    """
    设置全局配置实例

    Args:
        config: 配置实例
    """
    global _global_config
    _global_config = config


def init_global_config_from_env(prefix: str = "TUSHARE_") -> TushareConfig:
    """
    从环境变量初始化全局配置

    Args:
        prefix: 环境变量前缀

    Returns:
        配置实例
    """
    config = TushareConfig.from_env(prefix)
    set_global_config(config)
    return config