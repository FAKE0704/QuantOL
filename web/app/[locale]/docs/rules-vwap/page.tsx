import { useTranslations } from 'next-intl'

export default function RulesVwapPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">VWAP - 成交量加权平均价</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`VWAP(period)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">参数说明</h2>
        <table className="w-full border-collapse border border-slate-700 mb-6">
          <thead>
            <tr className="bg-slate-800">
              <th className="border border-slate-700 px-4 py-2 text-left">参数</th>
              <th className="border border-slate-700 px-4 py-2 text-left">类型</th>
              <th className="border border-slate-700 px-4 py-2 text-left">说明</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">period</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">周期</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          成交量加权平均价（Volume Weighted Average Price），反映在特定周期内投资者的平均成本。
          计算公式：Σ(典型价格 × 成交量) / Σ成交量，其中典型价格 = (最高价 + 最低价) / 2
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 价格在 VWAP 之上（强势）
close > VWAP(15)

// VWAP 突破策略
close > VWAP(20) & volume > REF(volume, 1)

// VWAP 作为支撑
close > VWAP(10) & REF(low, 1) > VWAP(10)

// 结合均线使用
close > VWAP(15) & close > SMA(close, 20)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>机构成本判断：VWAP 是机构平均成本线</li>
          <li>强弱判断：价格在 VWAP 之上为强势</li>
          <li>支撑压力：VWAP 常作为动态支撑或压力位</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>数据不足时返回 NaN</li>
            <li>适合日内交易和短线策略</li>
            <li>在震荡市中效果较好，趋势市中需结合其他指标</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
