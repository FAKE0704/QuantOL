# 查看历史行情
频率映射字典`frequency_options`
stock_cache用于股票列表，history_data_cache用于行情数据
缓存键由股票代码+日期范围+频率组成，确保唯一性
下次rerun时会优先使用缓存数据，避免重复加载