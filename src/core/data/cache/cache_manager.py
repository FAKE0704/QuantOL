"""
缓存管理器 - 负责数据缓存策略
职责：统一管理数据缓存，提高数据访问效率
"""

import os
import json
import pickle
import hashlib
import time
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from pathlib import Path


class CacheError(Exception):
    """缓存操作错误"""
    pass


class CacheManager:
    """缓存管理器 - 负责数据缓存策略"""

    def __init__(self, cache_dir: str = "./data/cache", default_ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
            default_ttl: 默认缓存时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)

        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存子目录
        self.data_cache_dir = self.cache_dir / "data"
        self.meta_cache_dir = self.cache_dir / "meta"

        self.data_cache_dir.mkdir(exist_ok=True)
        self.meta_cache_dir.mkdir(exist_ok=True)

        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

    def get_cache_key(self, method: str, **kwargs) -> str:
        """
        生成缓存键

        Args:
            method: 方法名
            **kwargs: 参数

        Returns:
            缓存键
        """
        # 创建参数字典
        params = {'method': method}
        params.update(kwargs)

        # 排序参数以确保一致性
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)

        # 生成MD5哈希
        hash_object = hashlib.md5(params_str.encode('utf-8'))
        return hash_object.hexdigest()

    def get_cache_path(self, cache_key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            cache_key: 缓存键

        Returns:
            缓存文件路径
        """
        return self.data_cache_dir / f"{cache_key}.pkl"

    def get_meta_path(self, cache_key: str) -> Path:
        """
        获取元数据文件路径

        Args:
            cache_key: 缓存键

        Returns:
            元数据文件路径
        """
        return self.meta_cache_dir / f"{cache_key}.json"

    def save(self, key: str, data: pd.DataFrame, ttl: int = None, tags: List[str] = None) -> bool:
        """
        保存数据到缓存

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 缓存时间（秒），None表示使用默认值
            tags: 缓存标签

        Returns:
            是否保存成功
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            cache_path = self.get_cache_path(key)
            meta_path = self.get_meta_path(key)

            # 保存数据
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # 保存元数据
            metadata = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                'ttl': ttl,
                'size': len(data),
                'tags': tags or [],
                'data_type': str(type(data)),
                'columns': list(data.columns) if hasattr(data, 'columns') else None
            }

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.stats['sets'] += 1
            self.logger.debug(f"缓存保存成功: {key}, 大小: {len(data)}")

            return True

        except Exception as e:
            self.logger.error(f"缓存保存失败: {e}")
            return False

    def load(self, key: str) -> Optional[pd.DataFrame]:
        """
        从缓存加载数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或过期返回None
        """
        try:
            cache_path = self.get_cache_path(key)
            meta_path = self.get_meta_path(key)

            # 检查缓存文件是否存在
            if not cache_path.exists() or not meta_path.exists():
                self.stats['misses'] += 1
                return None

            # 检查是否过期
            if self.is_expired(key):
                self.delete(key)
                self.stats['misses'] += 1
                return None

            # 加载数据
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)

            self.stats['hits'] += 1
            self.logger.debug(f"缓存命中: {key}")
            return data

        except Exception as e:
            self.logger.error(f"缓存加载失败: {e}")
            # 如果加载失败，删除损坏的缓存
            try:
                self.delete(key)
            except:
                pass
            self.stats['misses'] += 1
            return None

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            缓存是否存在且未过期
        """
        try:
            cache_path = self.get_cache_path(key)
            meta_path = self.get_meta_path(key)

            if not cache_path.exists() or not meta_path.exists():
                return False

            return not self.is_expired(key)

        except Exception:
            return False

    def is_expired(self, key: str) -> bool:
        """
        检查缓存是否过期

        Args:
            key: 缓存键

        Returns:
            是否过期
        """
        try:
            meta_path = self.get_meta_path(key)

            if not meta_path.exists():
                return True

            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            expires_at = datetime.fromisoformat(metadata['expires_at'])
            return datetime.now() > expires_at

        except Exception:
            # 如果无法读取元数据，认为已过期
            return True

    def delete(self, key: str) -> bool:
        """
        删除指定缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            cache_path = self.get_cache_path(key)
            meta_path = self.get_meta_path(key)

            deleted = False
            if cache_path.exists():
                cache_path.unlink()
                deleted = True

            if meta_path.exists():
                meta_path.unlink()
                deleted = True

            if deleted:
                self.logger.debug(f"缓存删除成功: {key}")

            return deleted

        except Exception as e:
            self.logger.error(f"缓存删除失败: {e}")
            return False

    def clear(self, pattern: str = None, tags: List[str] = None) -> int:
        """
        清理缓存

        Args:
            pattern: 缓存键模式，如果为None则清理所有缓存
            tags: 要清理的标签

        Returns:
            清理的缓存数量
        """
        try:
            deleted_count = 0

            # 获取所有缓存键
            cache_keys = self.list_cache_keys()

            for key in cache_keys:
                should_delete = False

                # 按模式匹配
                if pattern and pattern in key:
                    should_delete = True

                # 按标签匹配
                if tags:
                    metadata = self.get_metadata(key)
                    if metadata and any(tag in metadata.get('tags', []) for tag in tags):
                        should_delete = True

                # 如果没有指定条件，删除所有
                if pattern is None and tags is None:
                    should_delete = True

                if should_delete:
                    if self.delete(key):
                        deleted_count += 1

            self.logger.info(f"缓存清理完成，删除 {deleted_count} 个缓存项")
            return deleted_count

        except Exception as e:
            self.logger.error(f"缓存清理失败: {e}")
            return 0

    def clear_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存数量
        """
        try:
            deleted_count = 0
            cache_keys = self.list_cache_keys()

            for key in cache_keys:
                if self.is_expired(key):
                    if self.delete(key):
                        deleted_count += 1
                        self.stats['evictions'] += 1

            self.logger.info(f"过期缓存清理完成，删除 {deleted_count} 个缓存项")
            return deleted_count

        except Exception as e:
            self.logger.error(f"过期缓存清理失败: {e}")
            return 0

    def list_cache_keys(self) -> List[str]:
        """
        列出所有缓存键

        Returns:
            缓存键列表
        """
        try:
            cache_keys = []
            for meta_file in self.meta_cache_dir.glob("*.json"):
                key = meta_file.stem
                cache_keys.append(key)
            return cache_keys

        except Exception as e:
            self.logger.error(f"列出缓存键失败: {e}")
            return []

    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存元数据

        Args:
            key: 缓存键

        Returns:
            元数据字典
        """
        try:
            meta_path = self.get_meta_path(key)

            if not meta_path.exists():
                return None

            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            self.logger.error(f"获取缓存元数据失败: {e}")
            return None

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            total_keys = len(self.list_cache_keys())
            expired_keys = sum(1 for key in self.list_cache_keys() if self.is_expired(key))

            # 计算总缓存大小
            total_size = 0
            for cache_file in self.data_cache_dir.glob("*.pkl"):
                total_size += cache_file.stat().st_size

            return {
                'cache_dir': str(self.cache_dir),
                'total_keys': total_keys,
                'valid_keys': total_keys - expired_keys,
                'expired_keys': expired_keys,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'stats': self.stats.copy(),
                'hit_rate': round(self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) * 100, 2) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"获取缓存信息失败: {e}")
            return {}

    def optimize_cache(self, max_size_mb: float = 1024) -> Dict[str, Any]:
        """
        优化缓存：清理过期缓存和限制大小

        Args:
            max_size_mb: 最大缓存大小（MB）

        Returns:
            优化结果
        """
        try:
            result = {
                'expired_cleaned': 0,
                'size_limited_cleaned': 0,
                'total_cleaned': 0,
                'final_size_mb': 0
            }

            # 清理过期缓存
            result['expired_cleaned'] = self.clear_expired()

            # 如果缓存仍然过大，按LRU策略删除
            cache_info = self.get_cache_info()
            while cache_info['total_size_mb'] > max_size_mb:
                # 获取所有缓存的元数据并按最后访问时间排序
                cache_keys = self.list_cache_keys()
                if not cache_keys:
                    break

                # 这里简化处理，删除最旧的缓存
                oldest_key = None
                oldest_time = datetime.now()

                for key in cache_keys:
                    metadata = self.get_metadata(key)
                    if metadata:
                        created_at = datetime.fromisoformat(metadata['created_at'])
                        if created_at < oldest_time:
                            oldest_time = created_at
                            oldest_key = key

                if oldest_key and self.delete(oldest_key):
                    result['size_limited_cleaned'] += 1

                # 重新计算大小
                cache_info = self.get_cache_info()
                if cache_info['total_size_mb'] <= max_size_mb:
                    break

            result['total_cleaned'] = result['expired_cleaned'] + result['size_limited_cleaned']
            result['final_size_mb'] = self.get_cache_info()['total_size_mb']

            self.logger.info(f"缓存优化完成: {result}")
            return result

        except Exception as e:
            self.logger.error(f"缓存优化失败: {e}")
            return {}

    def export_cache_keys(self, file_path: str) -> bool:
        """
        导出缓存键列表

        Args:
            file_path: 导出文件路径

        Returns:
            是否导出成功
        """
        try:
            cache_keys_info = []
            for key in self.list_cache_keys():
                metadata = self.get_metadata(key)
                cache_keys_info.append({
                    'key': key,
                    'exists': self.exists(key),
                    'expired': self.is_expired(key),
                    'metadata': metadata
                })

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_keys_info, f, ensure_ascii=False, indent=2)

            self.logger.info(f"缓存键列表导出成功: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"缓存键列表导出失败: {e}")
            return False