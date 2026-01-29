import { useTranslations } from 'next-intl'

export default function ApiPage() {
  const t = useTranslations('docs')

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">{t('categories.api')}</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">事件系统 API</h2>

        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`# 事件类型
from src.core.events import (
    MarketDataEvent,
    SignalEvent,
    OrderEvent,
    FillEvent
)

# 创建自定义事件处理器
class CustomEventHandler:
    def handle_event(self, event: Event):
        # 处理事件逻辑
        pass`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">数据接口 API</h2>
        <p className="text-muted-foreground mb-6">
          统一的数据管理器接口，支持多种数据源无缝切换：
        </p>

        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`from src.core.data import DataManager

# 初始化数据管理器
data_manager = DataManager(source='tushare')

# 获取历史数据
data = data_manager.get_bar_data(
    symbol='sh.600000',
    start_date='2023-01-01',
    end_date='2024-01-01'
)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">策略基类 API</h2>
        <p className="text-muted-foreground">
          所有策略都继承自基类 Strategy，需实现以下方法：
        </p>
      </div>
    </div>
  )
}
