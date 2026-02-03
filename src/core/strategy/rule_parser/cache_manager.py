"""缓存管理模块

提供带LRU驱逐的缓存管理器，分离时间无关和时间相关的缓存。
"""
import hashlib
from typing import Any, Dict, List
from collections import OrderedDict


class RuleCacheManager:
    """带LRU驱逐的缓存管理器

    改进点:
    - 时间无关/时间相关缓存分离
    - LRU驱逐防止内存膨胀
    - 基于哈希的键生成（更短更快）
    """

    def __init__(self, max_size: int = 1000):
        """初始化缓存管理器

        Args:
            max_size: 时间相关缓存的最大大小（LRU驱逐）
        """
        self.max_size = max_size

        # 时间无关缓存（参数相同，结果永远相同）
        self._param_cache: Dict[str, Any] = {}

        # 时间相关缓存（使用LRU策略）
        self._time_cache: 'OrderedDict[str, Any]' = OrderedDict()

        # 统计信息
        self.param_cache_hits = 0
        self.param_cache_misses = 0
        self.time_cache_hits = 0
        self.time_cache_misses = 0

    def get_time_independent_key(self, func_name: str, *args) -> str:
        """生成不包含index的缓存键

        Args:
            func_name: 函数名
            *args: 函数参数

        Returns:
            MD5哈希后的缓存键（16位）
        """
        key_str = f"{func_name}:{args}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def get_time_dependent_key(self, func_name: str, index: int, *args) -> str:
        """生成包含index的缓存键

        Args:
            func_name: 函数名
            index: 当前索引位置
            *args: 函数参数

        Returns:
            MD5哈希后的缓存键（16位）
        """
        key_str = f"{func_name}:{index}:{args}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def get_param_cached(self, key: str) -> Any:
        """从时间无关缓存获取值

        Args:
            key: 缓存键

        Returns:
            缓存的值，不存在返回None
        """
        if key in self._param_cache:
            self.param_cache_hits += 1
            return self._param_cache[key]
        self.param_cache_misses += 1
        return None

    def set_param_cached(self, key: str, value: Any) -> None:
        """设置时间无关缓存

        Args:
            key: 缓存键
            value: 要缓存的值
        """
        self._param_cache[key] = value

    def get_time_cached(self, key: str) -> Any:
        """从时间相关缓存获取值（LRU）

        Args:
            key: 缓存键

        Returns:
            缓存的值，不存在返回None
        """
        if key in self._time_cache:
            self.time_cache_hits += 1
            # 移到末尾（最近使用）
            self._time_cache.move_to_end(key)
            return self._time_cache[key]
        self.time_cache_misses += 1
        return None

    def set_time_cached(self, key: str, value: Any) -> None:
        """设置时间相关缓存（LRU驱逐）

        Args:
            key: 缓存键
            value: 要缓存的值
        """
        # 如果已存在，先删除（稍后移到末尾）
        if key in self._time_cache:
            del self._time_cache[key]

        # 添加到末尾
        self._time_cache[key] = value

        # 检查是否超过最大大小，移除最旧的（第一个）
        while len(self._time_cache) > self.max_size:
            self._time_cache.popitem(last=False)

    def clear_param_cache(self) -> None:
        """清除时间无关缓存"""
        self._param_cache.clear()

    def clear_time_cache(self) -> None:
        """清除时间相关缓存"""
        self._time_cache.clear()

    def clear_all(self) -> None:
        """清除所有缓存"""
        self.clear_param_cache()
        self.clear_time_cache()

    @property
    def param_cache_size(self) -> int:
        """获取时间无关缓存大小"""
        return len(self._param_cache)

    @property
    def time_cache_size(self) -> int:
        """获取时间相关缓存大小"""
        return len(self._time_cache)

    @property
    def total_cache_size(self) -> int:
        """获取总缓存大小"""
        return self.param_cache_size + self.time_cache_size

    @property
    def cache_hit_rate(self) -> float:
        """计算总缓存命中率"""
        total_hits = self.param_cache_hits + self.time_cache_hits
        total_misses = self.param_cache_misses + self.time_cache_misses
        total_requests = total_hits + total_misses
        if total_requests == 0:
            return 0.0
        return total_hits / total_requests

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            包含缓存统计信息的字典
        """
        return {
            "param_cache_size": self.param_cache_size,
            "time_cache_size": self.time_cache_size,
            "total_cache_size": self.total_cache_size,
            "param_cache_hits": self.param_cache_hits,
            "param_cache_misses": self.param_cache_misses,
            "time_cache_hits": self.time_cache_hits,
            "time_cache_misses": self.time_cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
        }
