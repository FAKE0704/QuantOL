> [!important] Chan said
> 

# Quantitive Trading

## Fish for good ideas

###  
> [!important] Chan said
> Simple models are the best.
> - 参数越多，越容易发生数据窥视偏差（Data-snooping bias）
> - Make everything as simple as possible. But not simpler. ——Maybe Einstein.
### AI and Stock Picking 

> [!important] Chan said
> The prediction is applied to private instead of public targets
不要预测会被反馈影响的公共目标，这是因为，如果大家都预测到了会跌，那么就会同时出售，此时影响了你对它的预测。

> [!important] Chan said
> The features (predictors) that are used as input for predictions should be meaningful, numerous, and carefully scrubbed and engineered.


> [!important] Chan said
> Avoid those gigantic hedge funds.


> [!faq] Chan ask before you enter QT
• How much time do you have for babysitting your trading
programs?
• How good a programmer are you?
• How much capital do you have?
• Is your goal to earn steady monthly income or to strive for a large, long-term capital gain?

> [!faq] Chan ask before you BackTesting
• Does it outperform a benchmark?你中专毕业了么？
• Does it have a high enough Sharpe ratio?杠杆拉满。
• Does it have a small enough drawdown and short enough drawdown
duration?考虑每单位风险收益、风险控制。
• Does the backtest suffer from survivorship bias?完整性、幸存者偏差。
• Does the strategy lose steam in recent years compared to its earlier
years?花无百日红。
• Does the strategy have its own “niche” that protects it from
intense competition from large institutional money managers?不要站在巨人的前面，你会被踩死。
### Reference
Duhigg, Charles. 2006. “Street Scene; A Smarter Computer to Pick Stock.”
New York Times, November 24.

Sharpe, William. 1994. “The Sharpe Ratio.” The Journal of Portfolio
Management,Fall. Available at: www.stanford.edu/~wfsharpe/art/
sr/sr.htm.

## Back Testing

> [!important] Chan said
> BackTest it by yourself.
> 作用有三：1.确保你懂了 2.确保它没错 3.更容易优化策略

> [!important] Chan said
> Python is trash。
> 1.兼容问题 2.没有好用的统计包 3.真的慢 4.IDE垃圾

- 了解一下quant connect, blue shift
### Finding and Using Database


> [!example] Historical Databases
> Forex Date:Interactive Brokers
> Daily stock data: finance.yahoo.com


> [!important] Chan said
> I recommend getting historical data that are already split and dividend adjusted.
> 不然你就会发现每天的数据都有断层，这是因为公司的reverse split。

> [!faq] Chan Notice
> Databases that are free from **survivorship bias** are quite expensive and may not be affordable for you.


> [!important] Chan said
>Start collecting point-in-time data yourself for the benefit of your future backtest.
这样你就会有好数据来回测了。

> [!important] Chan said
> 越久远的时间，丢失的数据就越多，bias就越大。
> How to lessen the impact of survivorship bias? backtest your strategies on more recent data.

> [!important] Chan said
> A backtest that relies on high and low data is less reliable than one that relies on the open and close.
> 高低价的量非常小，即使你挂哪个点，都买卖不进去。

### Performance Measurement
> [!important] Chan said
> **[[Sharpe ratio]]**, **[[maximum drawdown]]**, and **[[MAR ratio]]** are the most important to compare across different strategies.

Sharpe ratios: should we or shouldn’t we subtract the risk-free rate from the returns of a dollarneutral portfolio? The answer is no. A dollar-neutral portfolio is selffinancing,
meaning the cash you get from selling short pays for the purchase of the long securities, so the financing cost (due to the spread between the credit and debit interest rates) is small and can be neglected for many backtesting purposes. Meanwhile, the margin
balance you have to maintain earns a credit interest close to the risk-free rate, $r_{F}$. So let’s say the strategy return (the portfolio return minus the contribution from the credit interest) is $R$, and the riskfree rate is $r_{F}$. Then the excess return used in calculating the Sharpe ratio is $R + r_{F}– r_{F} = R$. So, essentially, you can ignore the risk-free rate in the whole calculation and just focus on the returns due to your stock positions.
#### Sample size

> [!important] Chan said
> If you want to be statistically confident (at the 95 percent level)
that your true Sharpe ratio is equal to or greater than 0, you need
a backtest Sharpe ratio of 1 and a sample size of 681 data points
(e.g., 2.71 years of daily data).

> [!important] Chan said
>The higher the backtest Sharpe ratio, the smaller the sample size is needed. If your backtest Sharpe ratio is 2 or more, then you need only 174 data points (0.69 years of daily data) to be confident that your true Sharpe ratio is equal to or greater than 0.


> [!important] Chan said
If you want to be confident that your true Sharpe ratio is equal to or greater than 1, then you need a backtest Sharpe ratio of at least 1.5 and a sample size of 2,739 (10.87 years of daily data).

#### Out of Sample Testing

> [!important] Chan said

### Parameterless trading models



> [!important] Chan said
> A much more intelligent intelligent way to optimize parameters than just using a
moving lookback period parameter optimization or averaging over different
parameter values is a novel technique we developed called Conditional Param-
eter Optimization (CPO).




> [!important] Paper Trading
> Using test set to run models.

### Sensitivity Analysis



> [!important] Chan said
> In general, you should eliminate as many conditions, constraints, and parameters as possible as long as there is no significant decrease in performance in the test set, even though it may cdecrease performance on the training set. 

### Transaction Costs

### Strategy Refinement

## Setting up Your Business
### Retail or Proprietary?

> [!important] Chan said
> To avoid personal liability, I would recommend you set up a corporation as your trading vehicle and open an account through this entity at a retail brokerage. Your loss will then be limited to your initial investment, though you may have to file corporate bankruptcy when things go wrong. In the United States, a limited liability company or S-Corp. may Setting Up Your Business 83work best, as tax gains or losses can be passed directly to you personally. Even if you are not a US resident, you can still easily incorporate a US LLC for trading in a US brokerage account. I used bizfilings.com for that, but there are many other similar services, such as Stripe Atlas.


> [!important] Chan said
> Some of the rules and regulations imposed by proprietary trading firms are actually risk management measures for protection.


> [!important] Chan said
>  if you run a low-risk, market-neutral strategy that nevertheless requires a much higher leverage than allowed by Regulation T in order to generate good returns, a proprietary account may be better for you. However, if you engage in high-frequency futures trading that does not require too much capital, a retail account may save you a lot of costs and hassles. 
#### choosing a brokerage or proprietary trading firm

> [!important] Chan said
> Criterion of choosing: commission rate, speed of execution, dark-pool liquidity(暗盘资金？), the range of products you can trade, API, reputation and financial strength, 

#### Physical Infrastructure

> [!important] Chan said
> If you are a proprietary trader who requires minimal
coaching from your account manager and are confident in your ability to set up the physical trading infrastructure yourself, there is no reason not to trade remotely.


> [!important] Chan said
> All you need as a green hand are computer, high-speed internet connection, UPS(Uninterruptible Power Supply). As your business grows, you may upgrade your infrastructure gradually 


> [!important] Chan said
> You need professional real-time newsfeed: Thomason Reutrs, Dow Jones or Bloomberg.
> 

## Execution Systems
> [!important] Chan said
> Build your automated trading system(ATS) to deal.
### what an ATS can do for you
> [!important] Chan said
> - retrieve up-to-date data
> - run algorithm to generate orders
> - submit the orders for execution
> 	- minimizes human errors and delays
> - 

#### Building a semiautomated Trading System
> [!important] Chan said
> 

#### Hiring a programming consultant

#### Minimizing Transaction Costs
> [!important] Chan said
> 资产组合的权重，如果你持有多个公司的股票，那么市值最大的持有资本不应当大于10倍市值最小的持有资本。你应当使用$\sqrt[4]{ market\ cap}$作为权重去配比例。

> [!important] Chan said
> - Refrain from trading low-priced stocks.
> - Limit the size of your orders based on the liquidity of the stock(1% of average daily volume)
> - transaction cost: slippage

> [!important] Chan said
> If you are executing a large order, you can breake it down into many smaller orders.

#### Testing your system by paper trading 模拟交易
> [!important] Chan said
> 模拟交易可以发现look ahead bias，超过一个月的paper trading可能可以发现data-snooping bias

#### why actual performance diverge from expectation?
> [!important] Chan said
> Diagnosis:
> - Do you have bugs in your ATS?
> - Do the traders generated by your ATS match the backtest?
> - Are the execution costs much higher than you expected?
> - Are you trading illiquid stocks that caused  market impact?


> [!important] Chan said
> If there is no other mistakes, just believe in your strategy!
> If regime shifts recently, it may cause big impact to your strategy performance.
> 回测的时候也要注意，选择政策稳定的时间段。

## Money and Risk Management
### Optimal capital allocation and leverage
> [!important] Chan said
> the optimal allocation of n stratgies are given by $$F=C^{-1}M$$
> $r_{i}$:the return of the i-th strategy
> $m_{i}$:the mean return of the i-th strategy
> $C=\mathrm{Cov}(r_{i},r_{j})$
> $M=(m_{1},\dots,m_{n})^T$


> [!important] **Kelly Formula**
> Suppose $s_{i}$ are independent with each other. Then $C$ becomes diagonal with the diagonal elements be $\mathrm{Var}(s_{i})$. Then we have:
> $$f_{i}=\frac{m_{i}}{s_{i}^2}$$
> Since the return distributions are not really Gaussian, so traders prefer to cut half leverage for safety. This is called **half-Kelly betting**.
> + the application of the Kelly formula to continuous finance is premised on the assumption that return distribution is Gaussian.


> [!important] Maximum compounded growth rate
> $g$: compound rate of growth
> $S$: Sharpe ratio
> $$g=\frac{S^2}{2}+r$$
> 
### Risk Management


> [!important] Chan said
> Risk management always dictates that you should reduce your position size whenever there is a loss, even when it means realizing those losses.


> [!important] Chan said
> A lower leverage implies a smaller size of the selling required for risk management.


> [!important] Chan said
> You should also have in mind what is the maximum one-period drawdown on your equity that you are willing to suffer.

> [!important] Chan said
> when the movement of prices is due to news or other fundamental reasons (such as a company’s deteriorating revenue), one is likely to be in a momentum regime, and one should not “stand in front of a freight train,” in traders’ vernacular.
### pyschological preparedness
**endowment**:
**status quo bias**: 
**loss aversion**:

## Special Topics



> [!important] Chan said
> 

> [!important] Chan said
> 
