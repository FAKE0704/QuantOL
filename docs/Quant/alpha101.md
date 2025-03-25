# 定义：
## 函数及运算符定义：
(Below “{ }” stands for a placeholder. All expressions are case insensitive.) 
abs(x), log(x), sign(x) = standard definitions; same for the operators “+”, “-”, “*”, “/”, “>”, “<”, “==”, “||”, “x ? y : z”
rank(x) = cross-sectional rank 
delay(x, d) = value of x d days ago 
correlation(x, y, d) = time-serial correlation of x and y for the past d days 
covariance(x, y, d) = time-serial covariance of x and y for the past d days 
scale(x, a) = rescaled x such that sum(abs(x)) = a (the default is a = 1) 
delta(x, d) = today’s value of x minus the value of x d days ago 
signedpower(x, a) = x^a 
decay_linear(x, d) = weighted moving average over the past d days with linearly decaying weights d, d – 1, …, 1 (rescaled to sum up to 1) 
indneutralize(x, g) = x cross-sectionally neutralized against groups g (subindustries, industries, sectors, etc.), i.e., x is cross-sectionally demeaned within each group g 
ts_{O}(x, d) = operator O applied across the time-series for the past d days; non-integer number of days d is converted to floor(d) 
ts_min(x, d) = time-series min over the past d days 
ts_max(x, d) = time-series max over the past d days 
ts_argmax(x, d) = which day ts_max(x, d) occurred on 
ts_argmin(x, d) = which day ts_min(x, d) occurred on 
ts_rank(x, d) = time-series rank in the past d days 
min(x, d) = ts_min(x, d) 
max(x, d) = ts_max(x, d) 
sum(x, d) = time-series sum over the past d days
product(x, d) = time-series product over the past d days
stddev(x, d) = moving time-series standard deviation over the past d days 

## 输入数据定义：
returns = daily close-to-close returns 
open, close, high, low, volume = standard definitions for daily price and volume data 
vwap = daily volume-weighted average price 
cap = market cap 
adv{d} = average daily dollar volume for the past d days 
IndClass = a generic placeholder for a binary industry classification such as GICS, BICS, NAICS, SIC, etc., in indneutralize(x, IndClass.level), where level = sector, industry, subindustry, etc. 
Multiple IndClass in the same alpha need not correspond to the same industry classification. 

# 因子：
Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5) 
Alpha#2: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)) 
Alpha#3: (-1 * correlation(rank(open), rank(volume), 10)) 
Alpha#4: (-1 * Ts_Rank(rank(low), 9)) 
Alpha#5: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap))))) 
Alpha#6: (-1 * correlation(open, volume, 10)) 
Alpha#7: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1)) 
Alpha#8: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10)))) 
Alpha#9: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))) 
Alpha#10: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))) 
Alpha#11: ((rank(ts_max((vwap - close), 3)) + rank(ts_min((vwap - close), 3))) * rank(delta(volume, 3))) 
Alpha#12: (sign(delta(volume, 1)) * (-1 * delta(close, 1))) 
Alpha#13: (-1 * rank(covariance(rank(close), rank(volume), 5))) 
Alpha#14: ((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10)) 
Alpha#15: (-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)) 
Alpha#16: (-1 * rank(covariance(rank(high), rank(volume), 5))) 
Alpha#17: (((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) * rank(ts_rank((volume / adv20), 5))) 
Alpha#18: (-1 * rank(((stddev(abs((close - open)), 5) + (close - open)) + correlation(close, open, 10)))) 
Alpha#19: ((-1 * sign(((close - delay(close, 7)) + delta(close, 7)))) * (1 + rank((1 + sum(returns, 250))))) 
Alpha#20: (((-1 * rank((open - delay(high, 1)))) * rank((open - delay(close, 1)))) * rank((open - delay(low, 1)))) 
Alpha#21: ((((sum(close, 8) / 8) + stddev(close, 8)) < (sum(close, 2) / 2)) ? (-1 * 1) : (((sum(close, 2) / 2) < ((sum(close, 8) / 8) - stddev(close, 8))) ? 1 : (((1 < (volume / adv20)) || ((volume / adv20) == 1)) ? 1 : (-1 * 1)))) 
Alpha#22: (-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20)))) 
Alpha#23: (((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0) 
Alpha#24: ((((delta((sum(close, 100) / 100), 100) / delay(close, 100)) < 0.05) || ((delta((sum(close, 100) / 100), 100) / delay(close, 100)) == 0.05)) ? (-1 * (close - ts_min(close, 100))) : (-1 * delta(close, 3))) 
Alpha#25: rank(((((-1 * returns) * adv20) * vwap) * (high - close))) 
Alpha#26: (-1 * ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)) 
Alpha#27: ((0.5 < rank((sum(correlation(rank(volume), rank(vwap), 6), 2) / 2.0))) ? (-1 * 1) : 1) 
Alpha#28: scale(((correlation(adv20, low, 5) + ((high + low) / 2)) - close)) 
Alpha#29: (min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1 * rank(delta((close - 1), 5))))), 2), 1))))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5)) 
Alpha#30: (((1.0 - rank(((sign((close - delay(close, 1))) + sign((delay(close, 1) - delay(close, 2)))) + sign((delay(close, 2) - delay(close, 3)))))) * sum(volume, 5)) / sum(volume, 20)) 
Alpha#31: ((rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3)))) + sign(scale(correlation(adv20, low, 12)))) 
Alpha#32: (scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230)))) 
Alpha#33: rank((-1 * ((1 - (open / close))^1))) 
Alpha#34: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))
Alpha#35: ((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 - Ts_Rank(returns, 32))) 
Alpha#36: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sum(close, 200) / 200) - open) * (close - open))))) 
Alpha#37: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close))) 
Alpha#38: ((-1 * rank(Ts_Rank(close, 10))) * rank((close / open))) 
Alpha#39: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sum(returns, 250)))) 
Alpha#40: ((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10)) 
Alpha#41: (((high * low)^0.5) - vwap) 
Alpha#42: (rank((vwap - close)) / rank((vwap + close))) 
Alpha#43: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))
Alpha#44: (-1 * correlation(high, rank(volume), 5)) 
Alpha#45: (-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2)))) 
Alpha#46: ((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ? (-1 * 1) : (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < 0) ? 1 : ((-1 * 1) * (close - delay(close, 1))))) 
Alpha#47: ((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sum(high, 5) / 5))) - rank((vwap - delay(vwap, 5)))) 
Alpha#48: (indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) * delta(close, 1)) / close), IndClass.subindustry) / sum(((delta(close, 1) / delay(close, 1))^2), 250)) 
Alpha#49: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.1)) ? 1 : ((-1 * 1) * (close - delay(close, 1)))) 
Alpha#50: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5)) 
Alpha#51: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ? 1 : ((-1 * 1) * (close - delay(close, 1)))) 
Alpha#52: ((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) - sum(returns, 20)) / 220))) * ts_rank(volume, 5)) 
Alpha#53: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9)) 
Alpha#54: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5))) 
Alpha#55: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6)) 
Alpha#56: (0 - (1 * (rank((sum(returns, 10) / sum(sum(returns, 2), 3))) * rank((returns * cap))))) 
Alpha#57: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)))) 
Alpha#58: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291), 5.50322)) 
Alpha#59: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), IndClass.industry), volume, 4.25197), 16.2289), 8.19648)) 
Alpha#60: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))
Alpha#61: (rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282))) 
Alpha#62: ((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1) 
Alpha#63: ((rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 2.25164), 8.22237)) - rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180, 37.2467), 13.557), 12.2883))) * -1) 
Alpha#64: ((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 3.69741))) * -1) 
Alpha#65: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) < rank((open - ts_min(open, 13.635)))) * -1) 
Alpha#66: ((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + Ts_Rank(decay_linear(((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2))), 11.4157), 6.72611)) * -1) 
Alpha#67: ((rank((high - ts_min(high, 2.14593)))^rank(correlation(IndNeutralize(vwap, IndClass.sector), IndNeutralize(adv20, IndClass.subindustry), 6.02936))) * -1) 
Alpha#68: ((Ts_Rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333) < rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157))) * -1) 
Alpha#69: ((rank(ts_max(delta(IndNeutralize(vwap, IndClass.industry), 2.72412), 4.79344))^Ts_Rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416), 9.0615)) * -1) 
Alpha#70: ((rank(delta(vwap, 1.29456))^Ts_Rank(correlation(IndNeutralize(close, IndClass.industry), adv50, 17.8256), 17.9171)) * -1) 
Alpha#71: max(Ts_Rank(decay_linear(correlation(Ts_Rank(close, 3.43976), Ts_Rank(adv180, 12.0647), 18.0175), 4.20501), 15.6948), Ts_Rank(decay_linear((rank(((low + open) - (vwap + vwap)))^2), 16.4662), 4.4388)) 
Alpha#72: (rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519)) / rank(decay_linear(correlation(Ts_Rank(vwap, 3.72469), Ts_Rank(volume, 18.5188), 6.86671), 2.95011))) 
Alpha#73: (max(rank(decay_linear(delta(vwap, 4.72775), 2.91864)), Ts_Rank(decay_linear(((delta(((open * 0.147155) + (low * (1 - 0.147155))), 2.03608) / ((open * 0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411)) * -1) 
Alpha#74: ((rank(correlation(close, sum(adv30, 37.4843), 15.1365)) < rank(correlation(rank(((high * 0.0261661) + (vwap * (1 - 0.0261661)))), rank(volume), 11.4791))) * -1) 
Alpha#75: (rank(correlation(vwap, volume, 4.24304)) < rank(correlation(rank(low), rank(adv50), 12.4413))) 
Alpha#76: (max(rank(decay_linear(delta(vwap, 1.24383), 11.8259)), Ts_Rank(decay_linear(Ts_Rank(correlation(IndNeutralize(low, IndClass.sector), adv81, 8.14941), 19.569), 17.1543), 19.383)) * -1) 
Alpha#77: min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20.0451)), rank(decay_linear(correlation(((high + low) / 2), adv40, 3.1614), 5.64125))) 
Alpha#78: (rank(correlation(sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 19.7428), sum(adv40, 19.7428), 6.83313))^rank(correlation(rank(vwap), rank(volume), 5.77492))) 
Alpha#79: (rank(delta(IndNeutralize(((close * 0.60733) + (open * (1 - 0.60733))), IndClass.sector), 1.23438)) < rank(correlation(Ts_Rank(vwap, 3.60973), Ts_Rank(adv150, 9.18637), 14.6644))) 
Alpha#80: ((rank(Sign(delta(IndNeutralize(((open * 0.868128) + (high * (1 - 0.868128))), IndClass.industry), 4.04545)))^Ts_Rank(correlation(high, adv10, 5.11456), 5.53756)) * -1) 
Alpha#81: ((rank(Log(product(rank((rank(correlation(vwap, sum(adv10, 49.6054), 8.47743))^4)), 14.9655))) < rank(correlation(rank(vwap), rank(volume), 5.07914))) * -1) 
Alpha#82: (min(rank(decay_linear(delta(open, 1.46063), 14.8717)), Ts_Rank(decay_linear(correlation(IndNeutralize(volume, IndClass.sector), ((open * 0.634196) + (open * (1 - 0.634196))), 17.4842), 6.92131), 13.4283)) * -1) 
Alpha#83: ((rank(delay(((high - low) / (sum(close, 5) / 5)), 2)) * rank(rank(volume))) / (((high - low) / (sum(close, 5) / 5)) / (vwap - close))) 
Alpha#84: SignedPower(Ts_Rank((vwap - ts_max(vwap, 15.3217)), 20.7127), delta(close, 4.96796)) 
Alpha#85: (rank(correlation(((high * 0.876703) + (close * (1 - 0.876703))), adv30, 9.61331))^rank(correlation(Ts_Rank(((high + low) / 2), 3.70596), Ts_Rank(volume, 10.1595), 7.11408))) 
Alpha#86: ((Ts_Rank(correlation(close, sum(adv20, 14.7444), 6.00049), 20.4195) < rank(((open + close) - (vwap + open)))) * -1) 
Alpha#87: (max(rank(decay_linear(delta(((close * 0.369701) + (vwap * (1 - 0.369701))), 1.91233), 2.65461)), Ts_Rank(decay_linear(abs(correlation(IndNeutralize(adv81, IndClass.industry), close, 13.4132)), 4.89768), 14.4535)) * -1) 
Alpha#88: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8.06882)), Ts_Rank(decay_linear(correlation(Ts_Rank(close, 8.44728), Ts_Rank(adv60, 20.6966), 8.01266), 6.65053), 2.61957)) 
Alpha#89: (Ts_Rank(decay_linear(correlation(((low * 0.967285) + (low * (1 - 0.967285))), adv10, 6.94279), 5.51607), 3.79744) - Ts_Rank(decay_linear(delta(IndNeutralize(vwap, IndClass.industry), 3.48158), 10.1466), 15.3012)) 
Alpha#90: ((rank((close - ts_max(close, 4.66719)))^Ts_Rank(correlation(IndNeutralize(adv40, IndClass.subindustry), low, 5.38375), 3.21856)) * -1) 
Alpha#91: ((Ts_Rank(decay_linear(decay_linear(correlation(IndNeutralize(close, IndClass.industry), volume, 9.74928), 16.398), 3.83219), 4.8667) - rank(decay_linear(correlation(vwap, adv30, 4.01303), 2.6809))) * -1) 
Alpha#92: min(Ts_Rank(decay_linear(((((high + low) / 2) + close) < (low + open)), 14.7221), 18.8683), Ts_Rank(decay_linear(correlation(rank(low), rank(adv30), 7.58555), 6.94024), 6.80584)) 
Alpha#93: (Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.industry), adv81, 17.4193), 19.848), 7.54455) / rank(decay_linear(delta(((close * 0.524434) + (vwap * (1 - 0.524434))), 2.77377), 16.2664))) 
Alpha#94: ((rank((vwap - ts_min(vwap, 11.5783)))^Ts_Rank(correlation(Ts_Rank(vwap, 19.6462), Ts_Rank(adv60, 4.02992), 18.0926), 2.70756)) * -1) 
Alpha#95: (rank((open - ts_min(open, 12.4105))) < Ts_Rank((rank(correlation(sum(((high + low) / 2), 19.1351), sum(adv40, 19.1351), 12.8742))^5), 11.7584)) 
Alpha#96: (max(Ts_Rank(decay_linear(correlation(rank(vwap), rank(volume), 3.83878), 4.16783), 8.38151), Ts_Rank(decay_linear(Ts_ArgMax(correlation(Ts_Rank(close, 7.45404), Ts_Rank(adv60, 4.13242), 3.65459), 12.6556), 14.0365), 13.4143)) * -1) 
Alpha#97: ((rank(decay_linear(delta(IndNeutralize(((low * 0.721001) + (vwap * (1 - 0.721001))), IndClass.industry), 3.3705), 20.4523)) - Ts_Rank(decay_linear(Ts_Rank(correlation(Ts_Rank(low, 7.87871), Ts_Rank(adv60, 17.255), 4.97547), 18.5925), 15.7152), 6.71659)) * -1) 
Alpha#98: (rank(decay_linear(correlation(vwap, sum(adv5, 26.4719), 4.58418), 7.18088)) - rank(decay_linear(Ts_Rank(Ts_ArgMin(correlation(rank(open), rank(adv15), 20.8187), 8.62571), 6.95668), 8.07206))) 
Alpha#99: ((rank(correlation(sum(((high + low) / 2), 19.8975), sum(adv60, 19.8975), 8.8136)) < rank(correlation(low, volume, 6.28259))) * -1) 
Alpha#100: (0 - (1 * (((1.5 * scale(indneutralize(indneutralize(rank(((((close - low) - (high - close)) / (high - low)) * volume)), IndClass.subindustry), IndClass.subindustry))) - scale(indneutralize((correlation(close, rank(adv20), 5) - rank(ts_argmin(close, 30))), IndClass.subindustry))) * (volume / adv20)))) 
Alpha#101: ((close - open) / ((high - low) + .001)) 


这些因子（Alpha#1 到 Alpha#101）是量化投资中用于构建投资策略的数学表达式，它们通过对历史价格、成交量、市值等数据进行各种数学运算和统计分析，来尝试预测股票的未来表现。以下是对这些因子的通俗解释：

### Alpha#1
计算过去5天中，对每日的“如果当日收益率小于0，则取过去20天收益率的标准差，否则取收盘价”这一表达式的结果进行平方，然后找出这5天中该平方值最大的那一天的排名，最后将排名减去0.5。

### Alpha#2
计算过去6天中，每日“成交量的对数变化率”与“开盘价和收盘价的差值除以开盘价”之间的相关性，然后取其负数。

### Alpha#3
计算过去10天中，开盘价与成交量之间的相关性，然后取其负数。

### Alpha#4
计算过去9天中每日收盘价的最低值的排名，然后取其负数。

### Alpha#5
计算开盘价与过去10天的平均成交量加权平均价格（VWAP）之差的排名，再乘以收盘价与VWAP之差的绝对值的负数排名。

### Alpha#6
计算过去10天中开盘价与成交量之间的相关性，然后取其负数。

### Alpha#7
如果过去20天的平均成交量小于当日成交量，则计算过去60天中，每日收盘价与7天前收盘价之差的绝对值的移动平均值的排名，再乘以该差值的符号；否则，取-1。

### Alpha#8
计算过去5天的开盘价之和与过去5天的收益率之和的乘积，再减去10天前该乘积的值，最后取其负数排名。

### Alpha#9
如果过去5天中每日收盘价与前一日收盘价之差的最小值大于0，则取该最小值；如果最大值小于0，则取该最大值；否则，取该差值的负数。

### Alpha#10
对Alpha#9的结果进行排名。

### Alpha#11
计算过去3天中，VWAP与收盘价之差的最大值和最小值的排名，再乘以过去3天成交量变化的排名。

### Alpha#12
计算成交量与前一日成交量之差的符号，再乘以收盘价与前一日收盘价之差的负数。

### Alpha#13
计算过去5天中，收盘价排名与成交量排名之间的协方差，然后取其负数排名。

### Alpha#14
计算过去3天收益率变化的排名的负数，再乘以开盘价与成交量之间的相关性。

### Alpha#15
计算过去3天中，每日高价位排名与成交量排名之间的相关性的绝对值的排名，再取其负数。

### Alpha#16
计算过去5天中，高价位排名与成交量排名之间的协方差，再取其负数排名。

### Alpha#17
计算过去10天收盘价的排名的负数，乘以过去1天收盘价变化的排名，再乘以过去5天成交量与过去20天平均成交量之比的排名。

### Alpha#18
计算过去5天开盘价与收盘价差值的绝对值的标准差，加上开盘价与收盘价之差，再加上收益率之间的相关性，最后取其负数排名。

### Alpha#19
计算过去7天收盘价变化的符号，再乘以过去250天收益率之和加1的排名加1的负数。

### Alpha#20
计算开盘价与前一日高价位、收盘价、低价位之差的排名的乘积，再取其负数。

### Alpha#21
如果过去8天收盘价的平均值加上标准差小于过去2天收盘价的平均值，则取-1；如果过去2天收盘价的平均值小于过去8天平均值减去标准差，则取1；否则，如果当日成交量大于等于过去20天平均成交量，则取1，否则取-1。

### Alpha#22
计算过去5天高价位与成交量之间的相关性的变化率，再乘以过去20天收盘价标准差的排名，最后取其负数。

### Alpha#23
如果过去20天高价位的平均值小于今日高价位，则取高价位与2天前高价位之差的负数；否则取0。

### Alpha#24
如果过去100天收盘价平均值的变化率小于等于0.05，则取收盘价与过去100天收盘价最小值之差的负数；否则，取收盘价与3天前收盘价之差的负数。

### Alpha#25
计算收益率的负数乘以过去20天平均成交量、VWAP和高价位与收盘价之差的乘积，再进行排名。

### Alpha#26
计算过去3天中，过去5天成交量排名与高价位排名之间相关性的最大值，再取其负数。

### Alpha#27
如果过去2天相关性的平均值的排名小于0.5，则取-1，否则取1。

### Alpha#28
计算过去5天平均成交量与低价位的相关性，加上高低价位的平均值，再减去收盘价，最后进行缩放。

### Alpha#29
计算一系列复杂的嵌套函数，包括排名、缩放、对数求和等操作。

### Alpha#30
计算一系列与开盘价、高价位、低价位和成交量相关的排名和求和操作。

### Alpha#31
计算一系列与收盘价变化、排名和缩放相关的操作。

### Alpha#32
计算收盘价的移动平均与当前收盘价之差，加上VWAP与过去230天收盘价的相关性。

### Alpha#33
计算开盘价与收盘价比值的负数的排名。

### Alpha#34
计算收益率标准差比值和收盘价变化的相关性。

### Alpha#35
计算成交量、价格和收益率的排名和相关性。

### Alpha#36
计算一系列与收益率、价格和成交量相关的排名和相关性。

### Alpha#37
计算过去200天开盘价与收盘价差值的相关性，加上开盘价与收盘价的差值。

### Alpha#38
计算过去10天收盘价排名的负数乘以收盘价与开盘价比值的排名。

### Alpha#39
计算过去250天收盘价变化与收益率的相关性，再进行一系列复杂的运算。

### Alpha#40
计算过去10天高价位的标准差的负数乘以高价位与成交量的相关性。

### Alpha#41
计算高低价位的几何平均与VWAP的差值。

### Alpha#42
计算VWAP与收盘价之差的排名除以VWAP与收盘价之和的排名。

### Alpha#43
计算过去20天成交量与平均成交量的比值的排名，乘以过去8天收盘价变化的排名。

### Alpha#44
计算高价位与成交量排名之间的相关性的负数。

### Alpha#45
计算一系列与收盘价、成交量和收益率相关的排名和相关性。

### Alpha#46
根据过去20天、10天和当日收盘价的变化关系，决定取值为-1、1或与昨日收盘价之差的负数。

### Alpha#47
计算一系列与高价位、VWAP、成交量和收益率相关的排名和比值。

### Alpha#48
计算一系列与收益率、成交量和行业中性化相关的复杂运算。

### Alpha#49
根据过去20天、10天和当日收盘价的变化关系，决定取值为1或与昨日收盘价之差的负数。

### Alpha#50
计算过去5天中，成交量排名与VWAP排名之间相关性的最大值，再取其负数。

### Alpha#51
与Alpha#49类似，但阈值为-0.05。

### Alpha#52
计算过去5天最低价的最小值与5天前最小值之差，乘以收益率相关性和成交量排名。

### Alpha#53
计算过去9天中，（收盘价与低价位之差减去高价位与收盘价之差）的变化率的负数。

### Alpha#54
计算一系列与高价位、低价位和开盘价相关的比值。

### Alpha#55
计算过去6天中，（收盘价在高低价位区间中的相对位置）与成交量之间的相关性的负数。

### Alpha#56
计算一系列与收益率和市值相关的排名和求和操作。

### Alpha#57
计算收盘价与VWAP之差，除以过去2天VWAP排名的衰减线性组合。

### Alpha#58
计算一系列与VWAP、成交量和行业中性化相关的复杂运算。

### Alpha#59
与Alpha#58类似，但参数有所不同。

### Alpha#60
计算一系列与高低价位差值、成交量和收益率相关的排名和缩放操作。

### Alpha#61
比较VWAP与过去16天VWAP最小值的排名和VWAP与过去180天平均成交量的相关性排名。

### Alpha#62
比较一系列与VWAP、成交量和开盘价相关的排名和相关性。

### Alpha#63
计算一系列与收盘价、高低价位和行业中性化相关的复杂运算。

### Alpha#64
比较一系列与开盘价、高低价位和收益率相关的排名和相关性。

### Alpha#65
比较一系列与VWAP、成交量和开盘价相关的排名和相关性。

### Alpha#66
计算一系列与VWAP变化和高低价位相关的排名和衰减线性组合。

### Alpha#67
计算一系列与高价位、VWAP和行业中性化相关的排名和相关性。

### Alpha#68
比较一系列与收益率、高低价位和成交量相关的排名和相关性。

### Alpha#69
计算一系列与VWAP变化、高低价位和收益率相关的排名和相关性。

### Alpha#70
比较一系列与VWAP变化、行业中性化和收益率相关的排名和相关性。

### Alpha#71
计算一系列与VWAP变化和高低价位相关的排名和衰减线性组合的最大值。

### Alpha#72
比较一系列与高低价位和成交量相关的排名和衰减线性组合。

### Alpha#73
计算一系列与VWAP变化和高低价位相关的排名和衰减线性组合的最大值。

### Alpha#74
比较一系列与收益率和高低价位相关的排名和相关性。

### Alpha#75
比较VWAP与成交量的相关性和高低价位与成交量的相关性。

### Alpha#76
计算一系列与VWAP变化和高低价位相关的排名和衰减线性组合。

### Alpha#77
计算一系列与高低价位和成交量相关的排名和衰减线性组合的最小值。

### Alpha#78
计算一系列与高低价位和收益率相关的排名和相关性。

### Alpha#79
比较一系列与收益率和高低价位相关的排名和相关性。

### Alpha#80
计算一系列与收益率和高低价位相关的排名和相关性。

### Alpha#81
比较一系列与收益率和VWAP相关的排名和相关性。

### Alpha#82
计算一系列与开盘价变化和成交量相关的排名和衰减线性组合。

### Alpha#83
计算一系列与高低价位差值和成交量相关的排名和比值。

### Alpha#84
计算VWAP与过去15天VWAP最大值之差的排名的过去20天的幂。

### Alpha#85
计算一系列与高低价位和收益率相关的排名和相关性。

### Alpha#86
比较一系列与收益率和高低价位相关的排名和相关性。

### Alpha#87
计算一系列与收益率和高低价位相关的排名和衰减线性组合。

### Alpha#88
计算一系列与高低价位和收益率相关的排名和衰减线性组合的最小值。

### Alpha#89
计算一系列与高低价位和行业中性化相关的排名和衰减线性组合。

### Alpha#90
计算一系列与收益率和高低价位相关的排名和相关性。

### Alpha#91
计算一系列与收益率和VWAP相关的排名和衰减线性组合。

### Alpha#92
计算一系列与高低价位和成交量相关的排名和衰减线性组合的最小值。

### Alpha#93
计算一系列与收益率和VWAP相关的排名和衰减线性组合。

### Alpha#94
计算一系列与VWAP变化和收益率相关的排名和相关性。

### Alpha#95
比较一系列与收益率和高低价位相关的排名和相关性。

### Alpha#96
计算一系列与收益率和VWAP相关的排名和衰减线性组合的最大值。

### Alpha#97
计算一系列与收益率和高低价位相关的排名和衰减线性组合。

### Alpha#98
比较一系列与收益率和VWAP相关的排名和衰减线性组合。

### Alpha#99
比较一系列与收益率和高低价位相关的排名和相关性。

### Alpha#100
计算一系列与收益率、VWAP和行业中性化相关的复杂运算。

### Alpha#101
计算开盘价与收盘价之差，除以（高价位与低价位之差加上一个极小值0.001）。

