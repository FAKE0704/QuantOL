import { useTranslations } from 'next-intl'

export default function RulesRsiPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">RSI - 相对强弱指数</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`RSI(series, period)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">period</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">周期，默认 14</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          相对强弱指数（Relative Strength Index），用于衡量价格变动的速度和变化。
          返回值范围 0-100：RSI &gt; 70 为超买，RSI &lt; 30 为超卖。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 超卖买入
RSI(close, 14) < 30

// 超买卖出
RSI(close, 14) > 70

// RSI 多头排列
RSI(close, 14) > 50 & RSI(close, 5) > RSI(close, 14)

// RSI 底部背离
close < REF(close, 5) & RSI(close, 14) > REF(RSI(close, 14), 5)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>超买超卖判断：RSI 超过 70 或低于 30</li>
          <li>背离分析：价格创新高但 RSI 未创新高</li>
          <li>趋势确认：RSI 站上 50 视为多头趋势</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>在强趋势中，RSI 可能长期处于超买/超卖区域</li>
            <li>数据不足时返回 50（中性值）</li>
            <li>建议结合价格形态和成交量综合判断</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
