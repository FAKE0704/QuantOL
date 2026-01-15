import { useTranslations } from 'next-intl'

export default function StrategiesPage() {
  const t = useTranslations('docs')

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">{t('strategies')}</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">策略类型</h2>
        <p className="text-slate-300 mb-6">
          QuantOL 支持多种类型的量化交易策略：
        </p>

        <div className="space-y-4 mb-8">
          <div className="p-4 rounded-lg bg-card border border-border">
            <h3 className="text-lg font-semibold mb-2">规则策略 (RuleBasedStrategy)</h3>
            <p className="text-slate-400 text-sm">
              基于预定义规则的策略，适合技术指标驱动的交易信号
            </p>
          </div>

          <div className="p-4 rounded-lg bg-card border border-border">
            <h3 className="text-lg font-semibold mb-2">定投策略 (FixedInvestmentStrategy)</h3>
            <p className="text-slate-400 text-sm">
              定期定额投资策略，适合长期稳健投资
            </p>
          </div>

          <div className="p-4 rounded-lg bg-card border border-border">
            <h3 className="text-lg font-semibold mb-2">自定义策略</h3>
            <p className="text-slate-400 text-sm">
              继承策略基类，实现完全自定义的交易逻辑
            </p>
          </div>
        </div>

        <h2 className="text-2xl font-semibold mb-4">仓位管理策略</h2>
        <ul className="list-disc list-inside text-slate-300 space-y-2">
          <li>固定比例 (FixedPercentPositionStrategy)</li>
          <li>凯利公式 (KellyPositionStrategy)</li>
          <li>马丁格尔 (MartingalePositionStrategy)</li>
        </ul>
      </div>
    </div>
  )
}
