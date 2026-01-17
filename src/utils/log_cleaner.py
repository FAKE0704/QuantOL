"""
回测日志自动清理模块

功能：
- 自动监控日志目录大小
- 自动清理超过限制的日志文件
- 在回测开始前自动执行
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

# 日志目录
BACKTEST_LOG_DIR = Path("src/logs/backtests")

# 配置限制
MAX_LOG_SIZE_MB = 50           # 日志目录最大50MB
MAX_LOG_AGE_DAYS = 7           # 保留最近7天的日志
MAX_LOG_COUNT = 5              # 保留最近5个日志文件
CLEANUP_THRESHOLD_MB = 40      # 超过40MB时触发清理


def get_log_files_with_info(log_dir: Path = BACKTEST_LOG_DIR) -> List[Tuple[Path, datetime, int]]:
    """
    获取所有日志文件及其信息

    Returns:
        List[Tuple[文件路径, 修改时间, 文件大小(字节)]]
    """
    log_files = []
    for file_path in log_dir.glob("*.log"):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                size = stat.st_size
                log_files.append((file_path, mtime, size))
            except Exception as e:
                logger.warning(f"无法读取日志文件信息 {file_path}: {e}")

    # 按修改时间排序（最新的在前）
    log_files.sort(key=lambda x: x[1], reverse=True)
    return log_files


def get_log_directory_size(log_dir: Path = BACKTEST_LOG_DIR) -> int:
    """获取日志目录总大小（字节）"""
    total_size = 0
    for file_path in log_dir.glob("*.log"):
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except Exception:
                pass
    return total_size


def should_cleanup() -> bool:
    """检查是否需要清理日志"""
    try:
        current_size = get_log_directory_size()
        current_size_mb = current_size / 1024 / 1024
        return current_size_mb > CLEANUP_THRESHOLD_MB
    except Exception as e:
        logger.warning(f"检查日志目录大小失败: {e}")
        return False


def cleanup_old_logs(dry_run: bool = False) -> dict:
    """
    清理旧日志

    Args:
        dry_run: 是否只模拟运行

    Returns:
        dict: 清理统计信息
    """
    stats = {
        'deleted_count': 0,
        'freed_space': 0,
        'errors': []
    }

    try:
        log_files = get_log_files_with_info()
        if not log_files:
            return stats

        current_time = datetime.now()
        files_to_delete = []

        # 1. 删除超过天数的日志
        cutoff_time = current_time - timedelta(days=MAX_LOG_AGE_DAYS)
        for path, mtime, size in log_files:
            if mtime < cutoff_time:
                files_to_delete.append((path, size, 'age'))

        # 2. 如果数量超过限制，删除最旧的
        if len(log_files) > MAX_LOG_COUNT:
            excess_files = log_files[MAX_LOG_COUNT:]
            for path, mtime, size in excess_files:
                if path not in [f[0] for f in files_to_delete]:
                    files_to_delete.append((path, size, 'count'))

        # 3. 如果总大小超过限制，删除最旧的直到满足限制
        total_size = sum(size for _, _, size in log_files)
        max_size = MAX_LOG_SIZE_MB * 1024 * 1024
        if total_size > max_size:
            size_to_free = total_size - max_size
            freed = 0
            for path, mtime, size in reversed(log_files):
                if path not in [f[0] for f in files_to_delete]:
                    files_to_delete.append((path, size, 'size'))
                    freed += size
                    if freed >= size_to_free:
                        break

        # 执行删除
        for path, size, reason in files_to_delete:
            if dry_run:
                logger.info(f"[DRY RUN] 将删除日志: {path.name} ({size / 1024:.1f} KB, 原因: {reason})")
                stats['deleted_count'] += 1
                stats['freed_space'] += size
            else:
                try:
                    path.unlink()
                    stats['deleted_count'] += 1
                    stats['freed_space'] += size
                    logger.info(f"已清理日志: {path.name} ({size / 1024:.1f} KB)")
                except Exception as e:
                    error_msg = f"删除日志失败 {path.name}: {e}"
                    stats['errors'].append(error_msg)
                    logger.warning(error_msg)

        if stats['deleted_count'] > 0 and not dry_run:
            freed_mb = stats['freed_space'] / 1024 / 1024
            logger.info(f"日志清理完成: 删除 {stats['deleted_count']} 个文件, 释放 {freed_mb:.2f} MB")

    except Exception as e:
        error_msg = f"清理日志时出错: {e}"
        stats['errors'].append(error_msg)
        logger.error(error_msg)

    return stats


def auto_cleanup_on_backtest_start() -> None:
    """在回测开始时自动执行日志清理"""
    if not BACKTEST_LOG_DIR.exists():
        return

    try:
        # 检查是否需要清理
        if not should_cleanup():
            return

        current_size = get_log_directory_size()
        current_size_mb = current_size / 1024 / 1024

        logger.info(f"日志目录大小: {current_size_mb:.2f} MB，超过限制 ({CLEANUP_THRESHOLD_MB} MB)，开始自动清理...")

        stats = cleanup_old_logs(dry_run=False)

        if stats['errors']:
            logger.warning(f"日志清理遇到 {len(stats['errors'])} 个错误")

    except Exception as e:
        logger.error(f"自动清理日志失败: {e}")


def get_log_status() -> dict:
    """获取日志目录状态"""
    if not BACKTEST_LOG_DIR.exists():
        return {
            'exists': False,
            'file_count': 0,
            'total_size_mb': 0
        }

    log_files = get_log_files_with_info()
    total_size = sum(size for _, _, size in log_files)

    return {
        'exists': True,
        'file_count': len(log_files),
        'total_size_mb': total_size / 1024 / 1024,
        'needs_cleanup': should_cleanup()
    }
