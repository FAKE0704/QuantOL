import logging

# 全局logger实例
logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)

# 创建文件处理器
file_handler = logging.FileHandler('/Users/gaogao/Documents/vsc_work/awesome-Qsys/src/database.log')
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] [conn:%(connection_id)s] %(message)s'
))

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s'
))

# 添加处理器（仅当无Handler时添加）
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 添加追踪ID的过滤器
class ConnectionFilter(logging.Filter):
    def filter(self, record):
        record.connection_id = getattr(record, 'connection_id', 'N/A')
        return True
        
logger.addFilter(ConnectionFilter())

def _init_logger(self):
    """兼容旧版初始化方法"""
    self.logger = logger

