

# 创建任务
@/docs/system-design/文件结构.md 我正在开发一个量化交易系统，由于数据模块(core/data)涉及多个外部api数据接口，是否建议使用工厂(factory)的设计，我原本的打算是一个api接口建立一个类，如baostock_source.py就对应baostock数据源