
# 数据库
## 存储
- 不同维度的数据应存储在独立的数据库表/集合中
- 调用数据时需明确指定维度（如`get_data(scope="daily")`）



## MoneySupplyData表




## StockData表
id SERIAL PRIMARY KEY,
code VARCHAR(20) NOT NULL,
date DATE NOT NULL,
time TIME NOT NULL,
open NUMERIC NOT NULL,
high NUMERIC NOT NULL,
low NUMERIC NOT NULL,
close NUMERIC NOT NULL,
volume NUMERIC NOT NULL,
amount NUMERIC,
adjustflag VARCHAR(10),
frequency VARCHAR(10) NOT NULL,
UNIQUE (code, date, time, frequency)