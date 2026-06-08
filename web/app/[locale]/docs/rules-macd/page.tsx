import { useTranslations } from 'next-intl'

export default function RulesMacdPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">MACD - 指标平滑异同移动平均线</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`MACD(field, signal_window, short_window, long_window)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">计算公式</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`DIF = EMA(field, short_window) - EMA(field, long_window)
DEA = EMA(DIF, signal_window)
MACD = 2 × (DIF - DEA)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">signal_window</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">信号线周期（默认9）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">short_window</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">短期周期（默认12）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">long_window</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">长期周期（默认26）</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          MACD（Moving Average Convergence Divergence）是趋势跟踪动量指标，由DIF、DEA和MACD柱状图组成。
          MACD柱状图 = 2 × (DIF - DEA)，显示DIF与DEA的差值，用于判断趋势强度和反转信号。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// MACD柱状图为正（多头市场）
MACD(close, 9, 12, 26) > 0

// MACD柱状图为负（空头市场）
MACD(close, 9, 12, 26) < 0

// MACD金叉：柱状图从负变正
MACD(close, 9, 12, 26) > 0 AND REF(MACD(close, 9, 12, 26), 1) < 0

// MACD红柱放大（买入信号）
MACD(close, 9, 12, 26) > REF(MACD(close, 9, 12, 26), 1) AND MACD(close, 9, 12, 26) > 0

// MACD顶背离（价格新高但MACD不创新高，警惕下跌）
close > REF(close, 10) AND MACD(close, 9, 12, 26) < REF(MACD(close, 9, 12, 26), 10)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>趋势判断：MACD为正表示多头，为负表示空头</li>
          <li>金叉死叉：MACD柱状图穿越零轴是重要信号</li>
          <li>背离分析：价格与MACD背离预示趋势反转</li>
          <li>强弱判断：柱状图长度反映趋势强度</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">MACD三要素</h2>
        <table className="w-full border-collapse border border-slate-700 mb-6">
          <thead>
            <tr className="bg-slate-800">
              <th className="border border-slate-700 px-4 py-2 text-left">要素</th>
              <th className="border border-slate-700 px-4 py-2 text-left">含义</th>
              <th className="border border-slate-700 px-4 py-2 text-left">作用</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><strong>DIF</strong></td>
              <td className="border border-slate-700 px-4 py-2">快线</td>
              <td className="border border-slate-700 px-4 py-2">反映短期趋势变化</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><strong>DEA</strong></td>
              <td className="border border-slate-700 px-4 py-2">慢线/信号线</td>
              <td className="border border-slate-700 px-4 py-2">平滑DIF，产生交易信号</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><strong>MACD</strong></td>
              <td className="border border-slate-700 px-4 py-2">柱状图</td>
              <td className="border border-slate-700 px-4 py-2">显示多空力量对比</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
