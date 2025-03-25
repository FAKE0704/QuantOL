

## ADX(Average Directional Movement Index)

- 由Welles Wilder发明，一个指标天才
- 

1. 当ADX线上升时，表明市场存在趋势，这个趋势既可能是上涨的，也可能是下跌的。
2. 当ADX线下降时，说明当前趋势正在衰竭，甚至是陷入区间震荡。
3. +DI上穿-DI发出买入信号，-DI上穿+DI发出卖出信号。
4. 我们并不是在预测市场，而是市场规律性的东西具备一定的预见性。

**ADX可以识别趋势的强度**  
**ADX不能衡量趋势的方向**  
**ADX较为滞后**

### Logic

1. Calculate True Range (TR)  
   DIF1=high-low  
   DIF2=|high-close(t-1)|  
   DIF3=|low-close(t-2)|  
   TR = MAX(DIF1,DIF2,DIF3)  
   TR_avg = (TR_1+TR_2+...+TR_n)/TR_n
2. Calculate Direction Movement (DM)  
   DF1=high-high(t-1)  
   DF2=low(t-1)-low  
   if DF1>DF2:  
   DM_p=DF1;DM_n=0  
   else:  
   DM_p=0;DM_n=DF2

DM_p_avg = (DM_p(1)+DM_p(2)+...+DM_p(n))/n #正向动量的移动平均值  
DM_n_avg = (DM_n(1)+DM_n(2)+...+DM_n(n))/n

3. Calculate Direction Indicator(DI)  
   DI_p = (DM_p_avg/TR_avg)*100%  
   DI_n = (DM_n_avg/TR_avg)*100%  
   DI度量市场在变化趋势中的力度  
   DI_p>DI_n表明上升趋势
4. Calculate ADX  
   DX = (DI_p-DI_n)/(DI_p+DI_n)*100%  
   ADX = DX_avg = (ADX(1)+ADX(2)+...+ADX(n))/n

### 缺点

- 最主要的局限性是其滞后性,ADX是基于历史数据的，因此其反应可能滞后于市场的实际变化
- 在波动较小或无明显趋势的市场中，ADX可能不够有效
- 短期移动平均线更适合短线交易，而长期移动平均线则更适用于长期投资分析
- 多条不同周期的移动平均线的交叉，常常被视为买入或卖出的信号
# Definition基础定义

## $p$ 价格(Price)

> 价格(Price)  
$p(i)$简写为$p_{i}$，表示时间$i$的收盘价格。
$o(i)$简写为$o_{i}$，表示时间$i$的开盘价格。
$h(i)$简写为$h_{i}$，表示时间$i$的最高价。
$l(i)$简写为$l_{i}$，表示时间$i$的最低价。


## $r$ 波动率(Volatility)
> 波动率(Volatility)
$r(i)=\frac{p_{i}-p_{i-1}}{p_{i-1}}$

## $m$ 动量(Momentum)

> [!NOTE] 动量(Momentum)  
$m_{n}(i)=p_{i}-p_{i-n}$
表示第$i$时的$n$窗口的动量，表示？。

1窗口动量$m_1(i)$简写为$m_{i}$，表示时间$i$的收盘价格

> 动量累积效应：  
$m_{n}(i)=p_{i}-p_{i-n}=\sum\limits_{ k = 1 }^{n}p_{i-n+k-2}-p_{i-n+k-3}=\sum\limits_{ k = 1}^{n}m(i-n+k-1)$

> 从$i-n$到$i-1$时的动量累积，等于每日动量的累积。

## $v$ 成交量(Volume)

# 指标
## 动量指标
### VWAP 成交量加权平均(Volume Weighted Average Price)
$$VWAP_{n}(i)= \frac{\sum\limits_{ k = 1 }^{n}v_{i-n+k-1}p_{i-n+k-1}}{\sum\limits_{ k = 1 }^{n}v_{i-n+k-1}}
$$

### SMA 移动平均(Moving Average)

> [!NOTE] 移动平均MA(Moving Average)  
$SMA_{n}(i)= \frac{1}{n}\sum\limits_{ k = 1 }^{n}p_{i-n+k-1}$

$SMA_{n}(i)$表示从$i-n$到$i-1$时的价格均值。

缺点：滞后性。

### EMA (Exponential Moving Average)

EMA使用的权重不同于MA的平等权重，会更多地关注最近的价格数据，因此在价格急剧变动时反应更快

> [!NOTE] 广义EMA
第$i$时刻，window为$n$的EMA如何计算：
对于初始时刻$i-n+1$：$$EMA_n(i-n+1)=p(i-n+1)$$
对于其他时刻$t\in[i-n+2,i]$:
$$
EMA_{n}(t) = (1-\alpha)\cdot p(t)+\alpha \cdot EMA_{n}(t-1)
$$
通式：
$$
EMA_{n}(t)=\begin{cases}
    (1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-2}\alpha^{-i+k}p(t+i-k)\right]+\alpha^{n-i-1+t} \cdot p(i-n+1),\quad t\in [i-n+2,i]\\
    p(t),\quad t=i-n+1
\end{cases}
$$

Proof:
$$
\begin{align}
    EMA_{n}(t)
    &= (1-\alpha)\cdot p(t)+\alpha \cdot EMA_{n}(t-1)\\
    &= (1-\alpha)\cdot p(t)+\alpha \cdot \left[(1-\alpha)\cdot p(t-1)+\alpha \cdot EMA_{n}(t-2)\right]\\
    &= (1-\alpha)\cdot \left[p(t)+\alpha p(t-1)\right]+\alpha^2 \cdot EMA_{n}(t-2)\\
    &= ...\\
    &= (1-\alpha)\cdot \left[\sum\limits_{k=i-n+2}^{t}\alpha^{n-i-2+k}p(t+i-n+2-k)\right]+\alpha^{n-i-1+t} \cdot EMA_{n}(i-n+1)\\
    &= (1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-2}\alpha^{-i+k}p(t+i-k)\right]+\alpha^{n-i-1+t} \cdot p(i-n+1)\\
\end{align}
$$


> - 注意到当$n\to \infty\implies EMA_{n}(i)=EMA_{n}(i-1)$  
>   通常取$\alpha=\frac{n-1}{n+1}$，$EMA_{n}(i) =\frac{2}{n+1}p(k) + \frac{n-1}{n+1}EMA_{n}(i-1)$


>$\nabla EMA_n(t)$ 代表EMA的变化量？
$$
\begin{align}
\nabla EMA_n(t)
&= EMA_{n}(t)-EMA_{n}(t-1)\\
&= (1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-2}\alpha^{-i+k}p(t+i-k)\right]+\alpha^{n-i-1+t} \cdot p(i-n+1)- (1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-3}\alpha^{-i+k}p(t-1+i-k)\right]-\alpha^{n-i-1+t-1} \cdot p(i-n+1)\\
&= (1-\alpha)\cdot \left\{\sum\limits_{k=i}^{t+n-3}\left[\alpha^{-i+k}p(t+i-k)-\alpha^{-i+k}p(t+i-k-1)\right]+\alpha^{-i+t+n-2}p(i+n-2)+\right\}+\alpha^{n-i-1+t} \cdot p(i-n+1)--\alpha^{n-i-1+t-1} \cdot p(i-n+1)\\
&= (1-\alpha)\cdot \left\{\sum\limits_{k=i}^{t+n-3}\left[\alpha^{-i+k}\nablap(t+i-k)\right]+\alpha^{-i+t+n-2}p(i+n-2)+\right\}+\alpha^{n-i-1+t} \cdot p(i-n+1)--\alpha^{n-i-1+t-1} \cdot p(i-n+1)
\end{align}
$$


> [!NOTE] Proposition of EMA , when $\alpha=\frac{n-1}{n+1}$
> 1. $EMA_{n}(i)-EMA_{n}(i-1)=\sum\limits_{ i = 1 }^{n-1}\alpha^{i-1}(1-\alpha) p(k+i-1)-\sum\limits_{ i = 1 }^{n-1}\alpha^{i-1}(1-\alpha) p(k+i)-\alpha^{n-1}p(k+n)+\alpha^{n-1}p(k+n-1)=\sum\limits_{ i = 1 }^{n-1}\alpha^{i-1}(1-\alpha) p(k+i-1)-\sum\limits_{ i = 1 }^{n-1}\alpha^{i-1}(1-\alpha) p(k+i)-\alpha^{n-1}p(k+n)+\alpha^{n-1}p(k+n-1)$

### WMA (Weight Moving Average)









## MACD(Moving Average Convergence/Divergence)

### DIF 差离值(Difference)
>**DIF 差离值(Difference)**
$DIF_{(n_1,n_2)}(i)=EMA_{n_{1}}(i)-EMA_{n_{2}}(i)$
其中$n_i$代表周期,如12EMA指过去12次的指数移动平均。$n_1<n_2$

>$\nabla DIF_{(n_1,n_2)}(i)>0$代表什么？
$$\begin{align}
\nabla DIF_{(n_1,n_2)}(i) 
&= DIF_{(n_1,n_2)}(i)-DIF_{(n_1,n_2)}(i-1) \\
&=\left[EMA_{n_{1}}(i)-EMA_{n_{2}}(i)\right]-\left[EMA_{n_{1}}(i-1)-EMA_{n_{2}}(i-1)\right] \\
&=\left[EMA_{n_{1}}(i)-EMA_{n_{1}}(i-1)\right]-\left[EMA_{n_{2}}(i)-EMA_{n_{2}}(i-1)\right] \\
&=\nabla EMA_{n_{1}}(i) - \nabla EMA_{n_{2}}(i)>0
\end{align}
$$

**|DIF|代表趋势大小：短期均价与长期均价的差值**
- 反转讯号：DIF的绝对值越大，代表趋势越大，DIF的绝对值越小，代表趋势越小。当绝对值达到一个值时，就代表了趋势反转的讯号。通常以9EMA作为趋势反转的信号。
- 持续的涨势：DIF为正，且越来越大。
- 最常使用的是：DIF=12EMA-26EMA
- 背离信号。当指数曲线的走势向上，而 DIF、MACD曲线走势与之背道而弛，则发生大势即将转跌的信号。

### 差离平均值DEA(Difference in Exponential Average)

> [!NOTE] 差离平均值DEA(Difference in Exponential Average)  
$$DEA_{(n_{1},n_{2},n)}(i) = (1-\alpha)\cdot DIF_{(n_1,n_2)}(i) + \alpha\cdot DEA_{(n_{1},n_{2},n-1)}(i-1)$$
$$
DEA_{(n_{1},n_{2},n)}(t)=
\begin{cases}
    (1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-2}\alpha^{-i+k}DIF_{(n_1,n_2)}(t+i-k)\right]+\alpha^{n-i-1+t} \cdot DIF_{(n_1,n_2)}(i-n+1),\quad t\in [i-n+2,i]\\
    DIF_{(n_1,n_2)}(t),\quad t=i-n+1
\end{cases}
$$

通常取

其中$DIF(n)$表示倒退$n$天的$DIF$值。

**|nDEA|代表DIF的预估值：过去n天的DIF均值**

- 最常使用9DEA

> [!NOTE] ## MACD(Moving Average Convergence/Divergence)
$$
MACD_{(n_1,n_2,n)}(i) = 2\left[DIF_{(n_1,n_2)}(i)-DEA_{(n_{1},n_{2},n)}(i)\right]
$$

> [!NOTE] What does $\nabla MACD_{n_1,n_2,n}(t)>0$ means?  
$$
\begin{align}
MACD_{(n_{1},n_{2},n)}(t)-MACD_{(n_{1},n_{2},n)}(t-1)&=2\left[DIF_{(n_1,n_2)}(t)-\frac{1}{n}\sum\limits_{i=1}^{n}DIF_{(n_1,n_2)}(t+k-1)-DIF_{(n_1,n_2)}(t-1)+\frac{1}{n}\sum\limits_{i=1}^{n}DIF_{(n_1,n_2)}(t+k)\right]\\
&=2\left[DIF_{(n_1,n_2)}(t)-DIF_{(n_1,n_2)}(t-1)-\frac{1}{n}DIF_{(n_1,n_2)}(t)+\frac{1}{n}DIF_{(n_1,n_2)}(k+n)\right]\\
&=2\left[DIF_{(n_1,n_2)}(t)-DIF_{(n_1,n_2)}(t-1)-\frac{DIF_{(n_1,n_2)}(t)-DIF_{(n_1,n_2)}(k+n)}{n}\right]
\end{align}
$$


MACD画成柱状图。
**MACD柱表示预估偏差：DIF与nDEA的差值2倍**
若MACD>0
则$DIF_{(n_1,n_2)}(t)>DEA_{(n_{1},n_{2},n)}(t)$
则$DIF_{(n_1,n_2)}(t)>(1-\alpha)\cdot \left[\sum\limits_{k=i}^{t+n-2}\alpha^{-i+k}DIF_{(n_1,n_2)}(t+i-k)\right]+\alpha^{n-i-1+t} \cdot DIF_{(n_1,n_2)}(i-n+1)$
则$\alpha\cdot DIF_{(n_1,n_2)}(t) > (1-\alpha)\cdot\left[\sum\limits_{k=i+1}^{t+n-2}\alpha^{-i+k}DIF_{(n_1,n_2)}(t+i-k)\right]+\alpha^{n-i-1+t} \cdot DIF_{(n_1,n_2)}(i-n+1)$

所以$0>\sum\limits_{i=2}^{n}DIF_{(n_1,n_2)}(i)=\sum\limits_{i=2}^{n}EMA_{n_{1}}(i)-EMA_{n_{2}}(i)$  
即$\sum\limits_{i=2}^{n}EMA_{n_{1}}(i)<\sum\limits_{i=2}^{n}EMA_{n_{2}}(i)$







### meaning

- MACD的意义和双移动平均线基本相同，即由快、慢均线的离散、聚合表征当前的多空状态和股价可能的发展变化趋势，但阅读起来更方便。
- MACD的变化代表着市场趋势的变化，不同K线级别的MACD代表当前级别周期中的买卖趋势。

## MO (Momentum Oscillator)

测量了股价动量的速度  
当股价变动得“足够”剧烈时，表明出现了超买卖，那么反转信号就有了。  
$nMO(t)=\frac{p(t)-p(t-n)}{p(t-n)}=nVolality(t)=\frac{p{(t)}}{p(t-n)}-1$

波动率的变化率  
$slope(t)=Volality(t-1,t)-Volality(t-2,t-1)=\frac{p(t)}{p(t-1)}-\frac{p(t-1)}{p(t-2)}$

- $slope\sim Volality$?
  类似于物理中的加速度。钟摆运动发生转向前，必然加速度会经历0。


## RSI (Relative Strength Index)相对强弱指标

《技术交易系统新思路》by Welles Wilder,1978  
测量一段时间间内股价上涨总幅度占股价变化总幅度平均值的百分比，评估多空力量的强弱程度， 能够反映出市场在一定时期内的景气程度

- 多空力量：卖出量表示空头力量，买入量表示多头力量。

### RS 相对强度（Relative Strength）

$n$天内，每日价格波动分别为$m_{i}$，其中涨的时间指标集合假设为$\mathbb{U}$，跌的为$\mathbb{D}$

> RS 相对强度（Relative Strength）
$$RS = \frac{n日平均涨幅}{n日平均跌幅}$$
$RS_n=\frac{\sum\limits_{u\in \mathbb{U}}r_u}{-\sum\limits_{d\in \mathbb{D}}r_d}, |\mathbb{U}|+|\mathbb{D}|=n$

> - $RS_n=\frac{\sum\limits_{u\in \mathbb{U}}r_u}{-\sum\limits_{d\in \mathbb{D}}r_d}=\frac{\sum\limits_{u\in \mathbb{U}}p_u-p_{u-1}}{-\sum\limits_{d\in \mathbb{D}}p_d-p_{d-1}}$
> - $RS_n\in (0,+\infty)$

> RS 的意义
> 衡量市场力量：
> RS 反映了市场**上涨力量和下跌力量的对比**。
> 如果 RS 较大，说明市场上涨力量较强；如果 RS 较小，说明市场下跌力量较强。

### RSI

- RSI其实就是将RS映射到$(0,100)$区间

$RSI_{n}(i) = \frac{1}{1+\frac{1}{RS}}=\frac{\sum\limits_{u\in \mathbb{U}}r_u}{-\sum\limits_{d\in \mathbb{D}}r_d+\sum\limits_{u\in \mathbb{U}}r_u}$

> - $RS_n\in (0,100)$

#### usage

- $|RSI-50| > 20$会出现high & low，也就是会出现反转

> [!faq] Discussion  
Why $|nRSI-50| >20$ means high probability of reversal?  
Proof:  
$nRSI=\frac{1}{1+\frac{1}{RS}}*100=x, x\in (0,100)$  
$\frac{100}{x}=\frac{\mathrm{1}}{\mathrm{RS}}+1$  
$\frac{x}{100-x} = \mathrm{RS}$
> 
> if $x < 30$, then$RS<\frac{3}{7}$  
which means $\sum\limits_{u\in \mathbb{U}}r_u:\sum\limits_{d\in \mathbb{D}}r_d < 3:7$

> - n天中涨幅与跌幅比例小于3:7，说明空头力量强于多头力量，未来反转的概率大
为什么是70？

### RSI divergence 背离
- 背离的意思就是不一致性，**顶背离**指价格在顶点时发生了不一致。
举例：RSI顶背离：价格创新高时RSI并未创新高，发生了顶背离，说明市场是短期超买，预示着即将下跌。
- 在某些情况下，**背离可能不会导致价格反转**，而是价格继续沿原趋势运行。

支撑位和阻挡位经常在K线之前就在RSI上面显现了
RSI和股价的divergence是一个很强的反转指示信号

## KDJ (stochastic oscillator)

### 未成熟随机值（RSV）

第$i$天收盘价为$p(i)$, 假设$n$日内最低价(最高价)为$pmax_n(pmin_n)$,  
$RSV_{n}(i)=\frac{p(i)-pmin_{n}(i)}{p(i)-pmax_{n}(i)}, \mathbb{U}+\mathbb{D}=\mathbb{N}$  
$K_n(i)=\frac{2}{3}K_{n}(i-1)+\frac{1}{3}RSV_{n}(i)$  
$D_n(i)=\frac{2}{3}D_{n}(i-1)+\frac{1}{3}K_{n}(i)$  
$J_n(i)=3K_{n}(i)-2D_{n}(i)$
## BOLL
约翰·布林格（John Bollinger）在 1980 年代提出一种基于统计学原理的技术分析工具,它通过计算价格的移动平均线和标准差，构建一个动态的价格通道，用于衡量价格波动性和识别潜在的趋势反转点


上下轨 = $SMA_n(i)\pm k\cdot \sigma(n)$

$\sigma(n)$:p的标准差，standard error。
>**BOLL**
设$X_i=p_{i-k+1}-SMA_n(i)$
$\sigma(n)= \sqrt{\frac{1}{n}\sum\limits_{k = 1}^{n}(X_i)^2}$


## 神奇九转

“神奇九转”指标源自技术分析大师汤姆·迪马克（Tom DeMark）开发的 TD 序列。该指标的核心思想是，当股价连续9天保持同向运动时，往往预示着趋势即将发生转折。这一理论基于对历史数据的跟踪回测，发现数字“9”的出现通常与价格的反转相关联。

“神奇九转”是一种股票市场中的技术指标，用于预测股价走势的转向点。该指标基于连续9天的收盘价，其中每一天的收盘价都高于（或低于）前4天的收盘价。当满足这些条件时，生成数列1、2、3、4、5、6、7、8、9，并依次标注在当日K线的上方或下方。

- 尤其适用于震荡市场

### 指标逻辑

- **上升九转**：连续出现的9根K线，每根K线的收盘价均比各自前面的第4根K线的收盘价高。当形成上升九转后，行情一般会在接下来的几个交易日内逆转走弱，开启下跌。
- **下降九转**：连续出现的9根K线，每根K线的收盘价均比各自前面的第4根K线的收盘价低。下降九转成立后，行情一般会在接下来的几个交易日内逆转走强，开启反弹。

### 使用方法

1. **判断趋势**：通过观察神奇九转指标的指标线走势，可以判断市场当前的趋势是上涨还是下跌。当指标线由红色柱状图转变为绿色柱状图时，表示市场可能出现下跌趋势；反之，当指标线由绿色柱状图转变为红色柱状图时，表示市场可能出现上涨趋势[^28^]。
2. **交易策略**：

   - 在股价上涨过程中形成的九转结构称之为上涨9结构，此时可以考虑减仓卖出。
   - 在股价下跌过程中形成的九转结构称之为下跌9结构，此时可以考虑加仓买入[^15^][^20^]。


### 注意事项

- 神奇九转指标适用于震荡市、弱牛市和弱熊市。在极端的大牛市和大熊市中，其指示作用可能相对模糊，因此在评估当前走势时，应该综合考虑市场情绪、基本面分析以及其他指标[^20^][^21^]。
- 使用神奇九转时，需要注意其滞后性，建议结合基本面或其他技术指标进行进一步确认[^19^]。

### 数学定义

汤姆·迪马克的TD序列由两个主要部分组成：TD准备期和TD计数期。

#### 1. TD准备期（TD Setup）

假设我们有一个股票价格序列 $\{P_{i}\}, i =1,\ldots,n.$ 其中 $p_i$ 表示第 $i$天的收盘价。

**TD准备期**是一个长度为9的子序列，满足以下条件：

$P_{i+1} \leq P_{i+4-1}\forall i = 1, 2, \ldots, 9$  
这意味着，对于序列中的每一天，它的收盘价都应该低于或等于它**4天前**的收盘价。

#### 2. TD计数期（TD Countdown）

一旦我们确定了TD准备期，我们就开始一个TD计数期，这是一个计数序列 $C = \{C_1, C_2, \ldots, C_9\}$。

计数期的每一天，如果满足以下条件:  
$C_i = C_{i-1} + 1：P_i \leq P_{i-2}$ and $P_i \leq P_{i-1}$  
这意味着，如果当前天的收盘价低于它前一天和前两天的收盘价，计数就增加1。

#### 3. TD序列完成

当计数期的计数达到9时，我们说TD序列完成。这通常被视为一个潜在的趋势反转信号。

### TD序列的交易信号

- **买入信号**：如果在下跌趋势中完成一个TD序列，这可能是一个买入信号，因为趋势可能会反转向上。
- **卖出信号**：如果在上升趋势中完成一个TD序列，这可能是一个卖出信号，因为趋势可能会反转向下。

### 示例

假设我们有以下股票价格序列：

[ P = {100, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87} ]

在这个序列中，我们可以看到每一天的收盘价都低于它4天前的收盘价，所以我们可以确定一个TD准备期。然后，我们开始计数，直到我们达到9，这将给我们一个买入信号。

### coding

```python
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 假设df是你的股票数据
# df = pd.read_csv('your_stock_data.csv')  # 如果你的数据在CSV文件中

# 显示数据的前几行
st.write("## 股票数据")
st.dataframe(df.head())

# 计算TD序列
def calculate_td_sequence(df):
    df['TD Setup'] = (df['close'] > df['close'].shift(4)).astype(int)
    df['TD Count'] = df['TD Setup'].cumsum()
    df['TD Sequence'] = df['TD Count'].apply(lambda x: 1 if x > 8 else 0)  # 序列完成时标记为1

    # 标记序列
    sequences = []
    for i in range(len(df)):
        if df['TD Sequence'].iloc[i] == 1:
            sequences.append((i, df['time'].iloc[i]))

    return sequences

# 绘制神奇九转图
def plot_td_sequence(df, sequences):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(df['time'], df['close'], label='Close Price')

    # 绘制序列标记
    for sequence in sequences:
        start, end_time = sequence
        ax.axvline(x=end_time, color='r', linestyle='--', label='TD Sequence' if start == 0 else "")

    ax.set_title('神奇九转图')
    ax.set_xlabel('时间')
    ax.set_ylabel('收盘价')
    ax.legend()

    st.pyplot(fig)

# 计算序列
sequences = calculate_td_sequence(df)

# 绘制图表
plot_td_sequence(df, sequences)
```
## 贪婪恐惧指数（Fear and Greed Index）
$$
FGI = \frac{MV+SP+SPM+JH+MM+BDI+VIX}{7}
$$
其中
$MV$：市场波动性（Market Volatility）
$SP$：股票价格强度（Stock Price Strength）
$SPM$：市场动量（Market Momentum）
$JH$：避险需求（Safe Haven Demand）
$MM$：垃圾债券需求（Junk Bond Demand）
$BDI$：市场交易量广度（Volume Breadth）
$VIX$：VIX指数（CBOE Volatility Index）
# 收益与风险指标

## 日收益率Daily Return

$R_t$:Daily Return

$R_t = \frac{P_t-P{t-1}}{P{t-1}}$

```python
daily_return = df['close'].pct_change()

# 将时间列转换为 datetime 类型
df['time'] = pd.to_datetime(df['time'])

# 按天聚合，取每天的收盘价
daily_df = df.resample('D', on='time').agg({'close': 'last'}).dropna()

# 计算日收益率
daily_df['daily_return'] = daily_df['close'].pct_change().dropna()
```

## 累计收益率

```python

cum_return = (1 + daily_return).cumprod() - 1

```

## 年化平均回报率

$\bar{R}$:日平均收益率  
$N$:交易日数，一般取252  
$\mu_{Annual}=\bar{R} * N$

## 年化波动率

$\sigma_{Annual}$  
$\sigma_{Daily}$

$\sigma_{Annual}=\sigma_{Daily}*\sqrt{N}$

annualized_volatility = df['Daily_Return'].std() * np.sqrt(TradeDay)

## Sharpe 比率

$r_f$是无风险收益率（如国债收益率）

$\mathbf{Sharpe\ Ratio} = \frac{\mu_{Annual}-r_f}{\sigma_{Annual}}$

```python

# 假设无风险收益率为 0
risk_free_rate = 0

# 计算 Sharpe 比率
sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
```

## 最大回撤

$MDD = \mathop{\mathrm{max}}\limits_{t\in [0,T]}\frac{P_{peak}-P_{t}}{P_{peak}}$:

```python
# 计算累计最大值
daily_df['cumulative_max'] = daily_df['close'].cummax()

# 计算回撤
daily_df['drawdown'] = (daily_df['close'] - daily_df['cumulative_max']) / daily_df['cumulative_max']

# 计算最大回撤
max_drawdown = daily_df['drawdown'].min()
```





# Item and Strategies

buy price: $p_{b}$  
sell price: $p_{s}$  
trading volume: $n$  
service rate: $\lambda$  
capital: $C$

profit = $(p_{s}-p_{b})*n*(1-\lambda)$

## strategy 1

1st buy = $p_{b1},\rho_{1}*C$  
2st buy = $p_{b2},\rho_{2}*C$  
sell = $p_{b3}$  
profit = $(p_{b3}-p_{b1})*(\rho_{1}*C/p_{b1})+(p_{b3}-p_{b2})*(\rho_{2}*C/p_{b2})$

if $p_{b1}+p_{b2}=p_{b3}, \rho_1=\rho_2$

profit = $p_{b2}*(\rho_{1}*C/p_{b1})+p_{b1}*(\rho_{2}*C/p_{b2})$  
= $(\frac{p_{b2}*\rho_1}{p_{b1}}+\frac{p_{b1}*\rho_2}{p_{b2}})*C$  
= $(\frac{p_{b2}^2*\rho_1+p_{b1}^2*\rho_2}{p_{b1}p_{b2}})*C$  
= $(\frac{p_{b2}^2+p_{b1}^2}{p_{b1}p_{b2}})*C*\rho_1\ge 2C*\rho_1$

conclusion:如果分两次买入相同金额的股票，当你在两次买入价之和的地方卖出，你至少可以赚到2倍于本金的钱。

## strategy 1

1st buy = $p_{b1},C$  
2st buy = $p_{b2},C$  
sell = $p_{b3}$  
profit = $(p_{b3}-p_{b1})*(C/p_{b1})+(p_{b3}-p_{b2})*(C/p_{b2})$

if $p_{b1}+p_{b2}=p_{b3}$

profit = $p_{b2}*(C/p_{b1})+p_{b1}*(C/p_{b2})$  
= $(\frac{p_{b2}}{p_{b1}}+\frac{p_{b1}}{p_{b2}})*C$  
= $(\frac{p_{b2}^2+p_{b1}^2}{p_{b1}p_{b2}})*C\ge 2C$

conclusion:如果分两次买入相同金额的股票，当你在两次买入价之和的地方卖出，你至少可以赚到2倍于本金的钱。

## strategy 2

1st buy = $p_{b1},C$  
2st buy = $p_{b2},C$  
sell = $p_{b3}$  
profit = $(p_{b3}-p_{b1})*(C/p_{b1})+(p_{b3}-p_{b2})*(C/p_{b2})$  
= $(\frac{p_{b2}p_{b3}-p_{b1}p_{b2}+p_{b1}p_{b3}-p_{b1}p_{b2}}{p_{b1}p_{b2}})*C$  
= $(\frac{(p_{b1}+p_{b2})p_{b3}-2*p_{b1}p_{b2}}{p_{b1}p_{b2}})*C$  
= $(\frac{(p_{b1}+p_{b2})p_{b3}}{p_{b1}p_{b2}})*C-2C$

if $p_{b1}+p_{b2}=\frac{p_{b3}}{2}$

profit = $p_{b2}*(\rho_{1}*C/p_{b1})+p_{b1}*(\rho_{2}*C/p_{b2})$  
= $(\frac{p_{b2}*\rho_1}{p_{b1}}+\frac{p_{b1}*\rho_2}{p_{b2}})*C$  
= $(\frac{p_{b2}^2*\rho_1+p_{b1}^2*\rho_2}{p_{b1}p_{b2}})*C$  
= $(\frac{p_{b2}^2+p_{b1}^2}{p_{b1}p_{b2}})*C*\rho_1\ge 2C*\rho_1$

## strategy

如果信心不强，那么需要从高位换到低位。  
因为信息不强，因此预期下行，此时若能够在+X%的位置出售，在-Y%的位置买入，就实现了换位。

- 单日涨跌幅最大约为10%
- 子弹不应该少  
  策略：  
  1.一般而言，个股买入卖出的子弹应该保持一致。当行情较好时，可以使买入的子弹占比更多。  
  对于个股，可买入股数：可卖出股数=$n_b:n_s$

2.建仓  
寻找fair value

3.由于单日涨跌幅最大约20%，因此可分5次买卖，买卖应呈指数变化，价格应当在?%左右。  
$n_{b1}:n_{b2}:n_{b3}:n_{b4}:n_{b5}=1:\sigma:\sigma^2:\sigma^3:\sigma^4$  
$\sum\limits_{i=0}^{4}\sigma^{i}=\frac{\sigma^{5}-1}{\sigma-1}$  
若取$\sigma=2$，那么最大股数应当为2*31。

4.买入与卖出

- 在保险线内，看形势选择是否出售
- 

test：  
29.5 buy = 31*100**格子=0.59（2%）**28.91 buy = 1*100  
28.32 未到达  
29.5 sell = 1*100  
1.45



## strategy

如果信心较强，那么需要在-Y%的位置买入，卖出位置不明？





# Python

## BIGTRADER

bigtrader中initialize函数和handle_data函数

## Alltick

api token:4947d4f3947c7ac1d7c50ca8a76f6704-c-app

## Tushare(收费)

[https://tushare.pro/](https://tushare.pro/)  
api token:a2fb17ef3159218fabee30c54f270a64b4e6a448252436e6b548da5c

## MyData

[https://www.mairui.club/hsdata.html](https://www.mairui.club/hsdata.html)  
DB54D6DD-1CBC-426F-827C-9C71457FCB90

## package

### pyfolio

#### plotting

```python
returns = pd.Series(...)  # 你的策略回报率数据
# 创建完整的tear sheet
pf.create_full_tear_sheet(returns)
```



#### create_simple_tear_sheet

```python
pf.create_simple_tear_sheet((df.close.pct_change()).fillna(0).tz_localize('UTC'))

```

### talib

### Zipline

以趋势指标ADX结合均线和MACD指标构建交易策略进行量化回测。ADX是一种常用的趋势衡量指标，指标值越大代表趋势越强，但指标本身无法告诉你趋势的发展方向，**与均线和MACD指标配合运用，可以确认市场是否存在趋势，并衡量趋势的强度**。下面以13、55、89日均线（斐波那契数列），MACD（12,26,9）和ADX（阈值设置为前值和25）指标为例，得到下列回测结果

```python
def adx_strategy(df,ma1=13,ma2=55,ma3=89,adx=25):
    #计算MACD指标和ADX指标
    df('EMA1') = ta.EMA(df.close,ma1)
    df('EMA2') = ta.EMA(df.close,ma2)
    df('EMA3') = ta.EMA(df.close,ma3)
    df('MACD'),df('MACDSignal'),df('MACDHist') = ta.MACD(df.close,12,26,9)
    df('ADX') = ta.ADX(df.high,df.low,df.close,14)
    #设计买卖信号:21日均线大于42日均线且42日均线大于63日均线;ADX大于前值小于25；MACD大于前值
    df('Buy_Sig') =(df('EMA1')>df('EMA2'))&(df('EMA2')>df('EMA3'))&(df('ADX')<=adx)\
                    &(df('ADX')>df('ADX').shift(1))&(df('MACDHist')>df('MACDHist').shift(1))
    df.loc(df.Buy_Sig,'Buy_Trade') = 1
    df.loc(df.Buy_Trade.shift(1)==1,'Buy_Trade') = " "
    #避免最后三天内出现交易
    df.Buy_Trade.iloc(-3:)  = " " 

    #计算回报
    ## 以收盘价买入
    df.loc(df.Buy_Trade==1,'Buy_Price') = df.close
    df.Buy_Price = df.Buy_Price.ffill()
    ## 日收益率=(收盘余额-买入金额)/买入总金额
    df('Buy_Daily_Return')= (df.close - df.Buy_Price)/df.Buy_Price
    df.loc(df.Buy_Trade.shift(3)==1,'Sell_Trade') = -1
    df.loc(df.Sell_Trade==-1,'Buy_Total_Return') = df.Buy_Daily_Return
    df.loc((df.Sell_Trade==-1)&(df.Buy_Daily_Return==0),'Buy_Total_Return') = \
                                (df.Buy_Price - df.Buy_Price.shift(1))/df.Buy_Price.shift(1)
    df.loc((df.Sell_Trade==-1)&(df.Buy_Trade.shift(1)==1),'Buy_Total_Return') = \
                                (df.close-df.Buy_Price.shift(2))/df.Buy_Price.shift(2)
    #返回策略的日收益率
    return df.Buy_Total_Return.fillna(0)
```





# 自己的思考

| 符号        | 含义                      |
| ----------- | ------------------------- |
| $\alpha_n$  | 第n天变化率               |
| $p_i$       | 第i天的收盘价             |
| $b$         | 买入量                    |
| $B$         | 买入金额                  |
| $s$         | 卖出量                    |
| $S$         | 卖出金额                  |
| $h$         | 持有量                    |
| $H$         | 持有金额                  |
| $C$         | 总资金                    |
| $\lambda$   | 服务费率                  |
| $\lambda_0$ | 固定的服务费金额，一般为5 |

开盘买入总金额：  
$B=b*p_o$

收盘卖出总金额：  
$S=s*p_c$



变化率满足：  
$\alpha = \frac{p_c-p_o}{p_o}$

收盘时结算部分的收益：  
$s*(p_c-p_o)=s*p_o*\alpha$

Example 1:我希望在变化率为3%时一笔收益为100元

即$100 = s*p_o*3\%\rightarrow 投入金额得有3300$；

- 若$\alpha$为$3\%$,则当股价价格较高时，对应的价差也就越高，所以买股价低的好

我的想法：n天的视角下，速度要到0了且平均加速度变号了

# 

# 其他

### 二次回调信号

第一次回调之后，市场小幅回升，又下降，如果触底确认支撑点，将会有一个月左右的上升期。  
成交量缩量下跌，成交量整体呈下降趋势，如果成交量开始逐步回升，那么就是一个关键信号。  
如果近期K线能保持稳定，则说明二次探底已经结束。如果出现成交量上涨，那么第二波上涨行情就启动了。  
第二次回调往往比第一次回调时间更长。

### MyFactor

日线、15分钟线转向，且1分钟转向

$$

$$