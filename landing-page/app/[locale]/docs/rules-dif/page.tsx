import { useTranslations } from 'next-intl'

export default function RulesDifPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">DIF - 快线</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`DIF(field, short_window, long_window)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">计算公式</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`DIF = EMA(field, short_window) - EMA(field, long_window)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">field</code></td>
              <td className="border border-slate-700 px-4 py-2">Series</td>
              <td className="border border-slate-700 px-4 py-2">价格序列（通常是close）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">short_window</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">短期EMA周期（默认12）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">long_window</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">长期EMA周期（默认26）</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          DIF（Difference）是MACD指标的快线，计算短期EMA与长期EMA的差值。
          DIF &gt; 0 表示短期均线在长期均线之上（上涨趋势），DIF &lt; 0 表示下跌趋势。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// DIF金叉：DIF从负变正
DIF(close, 12, 26) > 0

// DIF死叉：DIF从正变负
DIF(close, 12, 26) < 0

// DIF向上突破
DIF(close, 12, 26) > REF(DIF(close, 12, 26), 1)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>趋势判断：DIF为正表示上涨趋势，为负表示下跌趋势</li>
          <li>MACD组成部分：DIF是MACD指标的核心组成部分</li>
          <li>信号强度：DIF绝对值越大，趋势越强</li>
        </ul>
      </div>
    </div>
  )
}
