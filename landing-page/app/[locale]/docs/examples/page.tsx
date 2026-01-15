import { useTranslations } from 'next-intl'

export default function ExamplesPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">示例代码</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">双均线策略</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300 overflow-x-auto">
{`from src.core.strategy import RuleBasedStrategy
from src.core.indicators import SMA
from src.core.events import SignalEvent

class DualMAStrategy(RuleBasedStrategy):
    def __init__(self, short_period=5, long_period=20):
        super().__init__()
        self.short_period = short_period
        self.long_period = long_period
        self.short_ma = SMA(short_period)
        self.long_ma = SMA(long_period)

    def generate_signals(self, market_data):
        # 计算均线
        short = self.short_ma.calculate(market_data['close'])
        long = self.long_ma.calculate(market_data['close'])

        # 金叉买入，死叉卖出
        if short[-1] > long[-1] and short[-2] <= long[-2]:
            return SignalEvent('BUY', market_data['symbol'])
        elif short[-1] < long[-1] and short[-2] >= long[-2]:
            return SignalEvent('SELL', market_data['symbol'])

        return None`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">运行回测</h2>
        <div className="bg-slate-900 rounded-lg p-4">
          <pre className="text-sm text-slate-300 overflow-x-auto">
{`from src.core.backtesting import BacktestEngine, BacktestConfig

# 配置回测参数
config = BacktestConfig(
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=100000,
    position_strategy_type="fixed_percent"
)

# 创建策略
strategy = DualMAStrategy(short_period=5, long_period=20)

# 运行回测
engine = BacktestEngine(config, strategy)
results = engine.run()

# 查看结果
print(f"年化收益率: {results.annual_return:.2%}")
print(f"夏普比率: {results.sharpe_ratio:.2f}")
print(f"最大回撤: {results.max_drawdown:.2%}")`}
          </pre>
        </div>
      </div>
    </div>
  )
}
