import logging

# 全局logger实例
logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)

# 创建文件处理器
# 验证日志文件路径可写
import os
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.log')
try:
    with open(log_path, 'a') as f:
        f.write('')  # 测试写入权限
except Exception as e:
    raise RuntimeError(f"日志文件不可写: {log_path}. 错误: {str(e)}")

# 自定义Formatter，安全处理缺失的connection_id字段
class SafeFormatter(logging.Formatter):
    def format(self, record):
        # 确保connection_id字段存在
        if not hasattr(record, 'connection_id'):
            record.connection_id = 'N/A'
        return super().format(record)

# 创建文件处理器
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)  # 确保捕获warning及以上级别日志
file_handler.setFormatter(SafeFormatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] [conn:%(connection_id)s] %(message)s'
))

# 创建控制台处理器（PM2已添加时间戳，不需要重复）
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] [%(module)s] %(message)s'
))
console_handler.setLevel(logging.DEBUG)  # 确保捕获所有调试日志

# 添加处理器
logger.handlers.clear()  # 先清除所有handler
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def check_logger_status():
    """手动检查日志系统状态"""
    status = {
        "file_handler": {
            "level": logging.getLevelName(file_handler.level),
            "path": file_handler.baseFilename,
            "formatter": str(file_handler.formatter)
        },
        "effective_level": logging.getLevelName(logger.getEffectiveLevel())
    }
    logger.warning("Logger状态检查: %s", status, extra={'connection_id': 'SYSTEM'})
    return status


def _init_logger(self):
    """兼容旧版初始化方法"""
    self.logger = logger
