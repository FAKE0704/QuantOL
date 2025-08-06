# 日志系统设计

## 基本配置

```python
import logging
logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)
```

## 日志处理器

1. 文件处理器：
   - 路径: `/src/database.log`
   - 级别: WARNING及以上
   - 格式: `[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] [conn:%(connection_id)s] %(message)s`

2. 控制台处理器：
   - 格式: `[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s`

## 使用方法

```python
# 基本日志记录
logger.debug("调试信息", extra={'connection_id': 'CONN123'})
logger.info("普通信息", extra={'connection_id': 'CONN123'})
logger.warning("警告信息", extra={'connection_id': 'CONN123'})
logger.error("错误信息", extra={'connection_id': 'CONN123'})

# 必须包含connection_id参数
```

## 日志级别

| 级别 | 说明 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 普通运行信息 |
| WARNING | 警告信息(会记录到文件) |
| ERROR | 错误信息 |

## 连接追踪

所有日志记录必须包含`connection_id`参数，用于追踪请求链路：

```python
extra={'connection_id': '唯一连接ID'}
```

## 状态检查

```python
# 检查日志系统状态
status = {
    "file_handler": {
        "level": "WARNING",
        "path": "/src/database.log"
    },
    "effective_level": "DEBUG"
}
```

## 注意事项

1. 文件处理器会自动创建日志文件
2. 确保对日志目录有写入权限
3. 生产环境建议定期归档日志文件