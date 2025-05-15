import logging

def _init_logger(self):
  """增强日志配置"""
  self.logger = logging.getLogger(__name__)
  self.logger.propagate = False
  self.logger.setLevel(logging.DEBUG)
  
  # 创建文件处理器
  file_handler = logging.FileHandler('database.log')
  file_handler.setFormatter(logging.Formatter(
      '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] [conn:%(connection_id)s] %(message)s'
  ))
  
  # 创建控制台处理器
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(logging.Formatter(
      '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s'
  ))
  
  # 添加处理器v仅当无 Handler 时添加
  if not self.logger.handlers:
      self.logger.addHandler(file_handler)
      self.logger.addHandler(console_handler)
  
  # 添加追踪ID的过滤器
  class ConnectionFilter(logging.Filter):
      def filter(self, record):
          record.connection_id = getattr(record, 'connection_id', 'N/A')
          return True
          
  self.logger.addFilter(ConnectionFilter())

