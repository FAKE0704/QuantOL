# 数据源字段映射文档

## 概述

本文档定义了不同数据源的字段如何映射到数据库表中的标准字段，确保系统在切换数据源时的一致性。

## 数据库表结构

### StockInfo表（股票基本信息）

| 字段名 | 数据类型 | 描述 | 示例 |
|--------|----------|------|------|
| code | TEXT PRIMARY KEY | 统一的股票代码（不带交易所后缀） | 000001 |
| code_name | TEXT NOT NULL | 股票名称 | 平安银行 |
| ipoDate | TEXT NOT NULL | 上市日期 | 1991-04-03 |
| outDate | TEXT | 退市日期 | null |
| type | TEXT | 股票类型 | 股票 |
| status | TEXT | 上市状态 | 上市 |

## 数据源字段映射

### 1. Baostock数据源

| 数据源字段 | 数据库字段 | 转换规则 | 说明 |
|------------|------------|----------|------|
| code | code | 直接映射 | 不带交易所后缀的6位数字代码 |
| code_name | code_name | 直接映射 | 股票中文名称 |
| ipoDate | ipoDate | 格式统一 | YYYY-MM-DD格式 |
| outDate | outDate | 格式统一 | YYYY-MM-DD格式，null表示未退市 |
| type | type | 直接映射 | 股票类型 |
| - | status | 默认值'上市' | Baostock返回的都是上市股票 |

### 2. Tushare数据源

| 数据源字段 | 数据库字段 | 转换规则 | 说明 |
|------------|------------|----------|------|
| symbol | code | 直接映射 | 不带交易所后缀的6位数字代码 |
| ts_code | - | 交易所信息提取 | 用于判断交易所，不存入数据库 |
| name | code_name | 直接映射 | 股票中文名称 |
| list_date | ipoDate | 格式转换 | YYYYMMDD → YYYY-MM-DD |
| - | outDate | 默认null | Tushare股票列表通常不包含退市信息 |
| - | type | 默认'股票' | 统一设置为股票 |
| list_status | status | 值映射 | L→'上市', D→'退市', P→'暂停' |
| market | - | 交易所信息 | SSE(上交所), SZSE(深交所) |
| industry | - | 行业信息 | 可选，暂不存入数据库 |
| area | - | 地区信息 | 可选，暂不存入数据库 |

## 字段转换规则

### 1. 股票代码统一化

- **目标格式**: 6位数字代码（如：000001）
- **Baostock**: 已经是目标格式，直接使用
- **Tushare**: 使用`symbol`字段，去除交易所后缀

### 2. 日期格式统一化

- **目标格式**: YYYY-MM-DD
- **Baostock**: 已经是目标格式，直接使用
- **Tushare**: 从YYYYMMDD转换为YYYY-MM-DD

### 3. 状态字段标准化

| 数据源 | 原值 | 标准值 |
|--------|------|--------|
| Baostock | - | '上市' |
| Tushare | L | '上市' |
| Tushare | D | '退市' |
| Tushare | P | '暂停' |

### 4. 股票类型标准化

- **统一值**: '股票'
- **原因**: 当前系统主要处理股票数据，保持类型一致

## 数据源特殊处理

### Baostock特点
- 返回的都是当前有效的上市股票
- 字段较少，信息相对简单
- 不需要额外的状态判断

### Tushare特点
- 可以获取所有股票（包括退市、暂停）
- 字段丰富，包含行业、地区等详细信息
- 需要处理list_status字段的状态映射
- 支持按交易所过滤

## 兼容性策略

### 1. 字段缺失处理

| 数据库字段 | Baostock | Tushare | 处理方式 |
|------------|----------|---------|----------|
| code | ✓ | ✓ | 必需字段 |
| code_name | ✓ | ✓ | 必需字段 |
| ipoDate | ✓ | ✓ | 必需字段 |
| outDate | ✓ | null | Baostock有，Tushare设null |
| type | ✓ | '股票' | Tushare统一设置 |
| status | '上市' | ✓ | Baostock设默认值 |

### 2. 数据验证规则

- **code**: 6位数字，必须存在
- **code_name**: 非空字符串，必须存在
- **ipoDate**: 有效日期格式，必须存在
- **outDate**: 有效日期格式或null
- **status**: '上市'/'退市'/'暂停'之一
- **type**: 目前固定为'股票'

## 实现建议

### 1. 映射器类设计

```python
class DataSourceFieldMapper:
    """数据源字段映射器"""

    @staticmethod
    def map_to_standard_fields(df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """将数据源字段映射为数据库字段"""
        pass

    @staticmethod
    def validate_required_fields(df: pd.DataFrame) -> bool:
        """验证必需字段是否存在"""
        pass
```

### 2. 错误处理策略

- **字段缺失**: 记录警告并跳过该记录
- **格式错误**: 记录错误并跳过该记录
- **转换失败**: 使用默认值并记录警告

### 3. 性能考虑

- 批量处理映射转换
- 预编译正则表达式
- 缓存映射配置

## 测试用例

### 1. Baostock数据示例

```python
# 输入数据
baostock_data = {
    'code': ['000001', '000002'],
    'code_name': ['平安银行', '万科A'],
    'ipoDate': ['1991-04-03', '1991-01-29'],
    'type': ['1', '1']
}

# 期望输出
expected_output = {
    'code': ['000001', '000002'],
    'code_name': ['平安银行', '万科A'],
    'ipoDate': ['1991-04-03', '1991-01-29'],
    'outDate': [None, None],
    'type': ['股票', '股票'],
    'status': ['上市', '上市']
}
```

### 2. Tushare数据示例

```python
# 输入数据
tushare_data = {
    'symbol': ['000001', '000002'],
    'ts_code': ['000001.SZ', '000002.SZ'],
    'name': ['平安银行', '万科A'],
    'list_date': ['19910403', '19910129'],
    'list_status': ['L', 'L']
}

# 期望输出
expected_output = {
    'code': ['000001', '000002'],
    'code_name': ['平安银行', '万科A'],
    'ipoDate': ['1991-04-03', '1991-01-29'],
    'outDate': [None, None],
    'type': ['股票', '股票'],
    'status': ['上市', '上市']
}
```

## 未来扩展

### 1. 支持更多数据源

- **东方财富**: 字段映射配置
- **Yahoo Finance**: 国际股票字段映射
- **Wind**: 专业金融数据源映射

### 2. 增强字段支持

- **行业分类**: 统一行业标准代码
- **财务指标**: 标准化财务数据字段
- **技术指标**: 标准化技术分析字段

### 3. 动态配置

- **配置文件**: 外部化映射配置
- **运行时更新**: 支持热更新映射规则
- **版本管理**: 映射规则的版本控制