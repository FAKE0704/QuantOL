# Tushare数据接口设计文档

## 1. 项目概述

### 1.1 设计目标
基于现有量化交易系统的统一数据接口架构，集成Tushare Pro数据源，提供高质量的金融数据服务。

### 1.2 设计原则
- **SOLID原则**: 遵循单一职责、开闭原则、依赖倒置等设计原则
- **DRY原则**: 避免代码重复，复用现有接口设计
- **一致性**: 与现有Baostock和AkShare接口保持一致的使用模式
- **可扩展性**: 支持Tushare丰富的API功能扩展
- **性能优化**: 合理的缓存机制和API调用限制管理

## 2. Tushare API分析

### 2.1 核心API接口

#### 2.1.1 股票基础信息接口
- **接口名称**: `stock_basic`
- **权限要求**: 2000积分起
- **主要参数**:
  - `ts_code`: TS股票代码
  - `name`: 股票名称
  - `market`: 市场类别 (主板/创业板/科创板/CDR/北交所)
  - `list_status`: 上市状态 (L上市 D退市 P暂停上市)
  - `exchange`: 交易所 (SSE上交所 SZSE深交所 BSE北交所)
- **返回字段**: ts_code, symbol, name, area, industry, market, exchange, list_status, list_date等

#### 2.1.2 股票历史数据接口
- **接口名称**: `pro_bar` (通用行情接口)
- **权限要求**: 分钟数据需要600积分试用
- **主要参数**:
  - `ts_code`: 证券代码（必选）
  - `start_date`: 开始日期（可选）
  - `end_date`: 结束日期（可选）
  - `asset`: 资产类别（E股票/I指数/C数字货币/FT期货/FD基金/O期权/CB可转债）
  - `freq`: 数据频度（分钟/min/日D/周W/月M）
  - `adj`: 复权类型（None未复权/qfq前复权/hfq后复权）
- **数据更新**: 股票和指数通常在15点～17点之间更新

#### 2.1.3 备用基础数据接口
- **接口名称**: `bak_basic`
- **权限要求**: 正式权限需要5000积分
- **主要参数**:
  - `trade_date`: 交易日期
  - `ts_code`: 股票代码
- **使用限制**: 单次最大7000条

### 2.2 API特点分析
- ✅ **数据质量高**: 专业金融数据服务，数据准确度高
- ✅ **数据覆盖全**: 支持股票、指数、基金、期货等多种资产
- ✅ **实时性较好**: 日线数据15-17点更新
- ✅ **复权支持**: 支持前复权、后复权
- ⚠️ **积分限制**: 需要积分才能访问不同级别的数据
- ⚠️ **调用限制**: 有频率和次数限制
- ⚠️ **认证要求**: 需要API token认证

## 3. 接口设计方案

### 3.1 类结构设计

```python
class TushareDataSource(DataSource):
    """Tushare数据源实现"""

    def __init__(self, token: str, cache_dir: Optional[str] = None):
        """
        初始化Tushare数据源

        Args:
            token: Tushare Pro API token
            cache_dir: 缓存目录路径
        """

    async def async_init(self):
        """异步初始化，验证token和连接"""

    async def load_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
        """加载股票历史数据"""

    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据到本地缓存"""

    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """检查本地缓存数据是否存在"""

    async def get_stock_basic(self) -> pd.DataFrame:
        """获取股票基础信息"""

    async def get_stock_list(self, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """获取股票列表"""

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据格式转换和标准化"""

    def _handle_api_limits(self):
        """API调用频率限制管理"""
```

### 3.2 核心功能设计

#### 3.2.1 认证与初始化
- 实现API token管理和验证
- 异步初始化测试连接可用性
- 错误处理和重连机制

#### 3.2.2 数据获取策略
- **股票代码转换**: 处理tushare专用代码格式(ts_code)
- **频率映射**: 将系统频率映射到tushare的freq参数
- **复权处理**: 支持前复权、后复权、未复权
- **数据完整性**: 处理停牌、退市等特殊情况

#### 3.2.3 缓存机制
- 本地文件缓存（parquet格式）
- 缓存过期策略
- 增量数据更新

#### 3.2.4 API限制管理
- 调用频率控制
- 积分余量检查
- 错误重试机制
- 降级策略

### 3.3 字段映射设计

#### 3.3.1 统一字段标准
```python
TUSHARE_FIELD_MAPPING = {
    # 基础交易数据
    'trade_date': 'date',        # 交易日期
    'ts_code': 'symbol',         # 股票代码
    'open': 'open',              # 开盘价
    'high': 'high',              # 最高价
    'low': 'low',                # 最低价
    'close': 'close',            # 收盘价
    'vol': 'volume',             # 成交量
    'amount': 'amount',          # 成交额

    # 复权数据
    'adj_open': 'adj_open',      # 复权开盘价
    'adj_high': 'adj_high',      # 复权最高价
    'adj_low': 'adj_low',        # 复权最低价
    'adj_close': 'adj_close',    # 复权收盘价

    # 基础信息
    'name': 'name',              # 股票名称
    'industry': 'industry',      # 所属行业
    'area': 'area',              # 地域
    'market': 'market',          # 市场类型
    'exchange': 'exchange',      # 交易所
    'list_status': 'list_status', # 上市状态
    'list_date': 'list_date',    # 上市日期
}
```

#### 3.3.2 频率映射
```python
FREQUENCY_MAPPING = {
    '1': '1min',     # 1分钟
    '5': '5min',     # 5分钟
    '15': '15min',   # 15分钟
    '30': '30min',   # 30分钟
    '60': '60min',   # 1小时
    'D': 'D',        # 日线
    'W': 'W',        # 周线
    'M': 'M',        # 月线
}
```

## 4. 实现细节

### 4.1 错误处理策略
- **网络错误**: 自动重试机制
- **认证错误**: token验证和提醒
- **积分不足**: 优雅降级和提示
- **数据缺失**: 日志记录和跳过处理
- **格式错误**: 数据清洗和异常值处理

### 4.2 性能优化
- **并发控制**: 合理的异步并发数量
- **批量请求**: 减少API调用次数
- **内存管理**: 大数据集分块处理
- **缓存策略**: 智能缓存和更新机制

### 4.3 日志和监控
- 详细的API调用日志
- 数据获取成功率统计
- 性能指标监控
- 错误报告和告警

## 5. 配置管理

### 5.1 配置文件结构
```python
TUSHARE_CONFIG = {
    'token': 'your_tushare_token_here',
    'default_frequency': 'D',
    'default_adjust': 'qfq',  # 默认前复权
    'cache_enabled': True,
    'cache_dir': './data/tushare',
    'cache_expire_days': 7,
    'rate_limit': {
        'calls_per_minute': 120,
        'retry_times': 3,
        'retry_delay': 1.0
    },
    'timeout': 30,
}
```

### 5.2 环境变量支持
- `TUSHARE_TOKEN`: API token
- `TUSHARE_CACHE_DIR`: 缓存目录
- `TUSHARE_LOG_LEVEL`: 日志级别

## 6. 集成方案

### 6.1 工厂模式注册
```python
# 在tushare_source.py文件末尾
DataFactory.register_source("tushare", TushareDataSource)
```

### 6.2 使用示例
```python
# 获取tushare数据源实例
factory = DataFactory()
tushare_source = factory.get_source("tushare", token="your_token")

# 异步初始化
await tushare_source.async_init()

# 获取股票历史数据
data = await tushare_source.load_data(
    symbol="000001.SZ",
    start_date="2024-01-01",
    end_date="2024-01-31",
    frequency="D"
)

# 获取股票基础信息
stock_list = await tushare_source.get_stock_basic()
```

## 7. 测试策略

### 7.1 单元测试
- 数据格式转换测试
- 错误处理测试
- 缓存机制测试
- 配置管理测试

### 7.2 集成测试
- API连接测试
- 数据获取完整性测试
- 性能压力测试
- 并发访问测试

### 7.3 Mock测试
- API响应模拟
- 网络异常模拟
- 限制条件模拟

## 8. 部署和维护

### 8.1 依赖管理
```python
requirements = [
    "tushare>=1.2.89",
    "pandas>=1.3.0",
    "aiohttp>=3.8.0",
    "tenacity>=8.0.0",
]
```

### 8.2 部署注意事项
- API token安全管理
- 缓存目录权限设置
- 日志文件轮转
- 监控指标配置

### 8.3 维护计划
- 定期更新tushare SDK
- 监控API调用限额
- 清理过期缓存数据
- 优化性能瓶颈

## 9. 风险评估与对策

### 9.1 技术风险
- **API变更**: 建立适配层，快速响应API变化
- **服务不稳定**: 实现多数据源备份机制
- **性能瓶颈**: 优化缓存策略和并发控制

### 9.2 业务风险
- **积分不足**: 建立积分监控和预警机制
- **数据质量**: 实现数据验证和清洗流程
- **合规风险**: 确保数据使用符合Tushare服务条款

### 9.3 运维风险
- **token泄露**: 加强密钥管理和访问控制
- **服务中断**: 建立健康检查和自动恢复机制
- **资源耗尽**: 实现资源监控和限流保护

## 10. 总结

本设计方案基于现有系统的优秀架构，充分考虑了Tushare API的特点和限制，采用了一致的设计模式，确保了：

1. **架构一致性**: 与现有Baostock和AkShare接口保持统一
2. **功能完整性**: 支持Tushare的核心功能和高级特性
3. **性能可靠性**: 通过缓存和优化策略保证性能
4. **扩展灵活性**: 为未来功能扩展预留空间
5. **运维友好性**: 完善的监控、日志和错误处理

该方案将为量化交易系统提供高质量、稳定可靠的Tushare数据源支持。