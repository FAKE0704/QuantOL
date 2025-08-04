

# 核心类
## DataSource抽象基类
- 定义数据源的基本接口
- 包含抽象方法：load_data, save_data, check_data_exists
- 提供通用的错误处理机制

## DataFactory工厂类
- 继承DataSource抽象基类
- 数据源注册机制(register_source)
- 通过名称获取数据源实例(get_source)
- 使用双重检查锁实现线程安全的单例模式
- 使用单独的锁保证数据源注册和获取的线程安全

## BaostockDataSource类
- 数据源是baostock api
- 继承自DataSource抽象基类
- 实现所有抽象方法(load_data, save_data, check_data_exists)
- 适配工厂模式架构

## MarketDataSource类
- 数据源支持Yahoo Finance和Tushare API
- 继承自DataSource抽象基类

- 适配工厂模式架构：
- 通过fetch_yahoo_data()和fetch_tushare_data()方法支持多数据源
- 统一通过_fetch_data()方法处理API请求
- 异步数据获取（使用aiohttp）