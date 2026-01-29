import { useTranslations } from 'next-intl'

export default function RulesQPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">Q - 分位数计算</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`Q(series, quantile, period)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">series</code></td>
              <td className="border border-slate-700 px-4 py-2">Series</td>
              <td className="border border-slate-700 px-4 py-2">价格序列（如 close）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">quantile</code></td>
              <td className="border border-slate-700 px-4 py-2">float</td>
              <td className="border border-slate-700 px-4 py-2">分位数 [0-1]（0.1=10%, 0.5=中位数, 0.9=90%）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">period</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">周期</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          计算指定周期内序列的分位数值。分位数用于识别价格在历史分布中的位置。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 价格高于 90 分位数（强势）
close > Q(close, 0.9, 20)

// 价格低于 10 分位数（弱势）
close < Q(close, 0.1, 20)

// 中位数突破
close > Q(close, 0.5, 20)

// 分位数值本身的变化
Q(close, 0.8, 10) > REF(Q(close, 0.8, 10), 1)

// 动态筛选
SQRT(high*low, 2) < REF(Q(SQRT(high*low, 2)-VWAP(15), 0.8, 10), 1)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>强势股筛选：价格高于 90% 分位数</li>
          <li>弱势股筛选：价格低于 10% 分位数</li>
          <li>动态阈值：使用分位数作为动态买卖点</li>
          <li>相对强度：比较当前价格在历史分布中的位置</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>quantile 必须在 [0, 1] 范围内</li>
            <li>数据不足时返回 NaN</li>
            <li>常用分位数：0.1（下限）、0.5（中位数）、0.9（上限）</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
