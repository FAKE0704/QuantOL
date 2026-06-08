import { useTranslations } from 'next-intl'

export default function RulesDeaPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">DEA - 慢线/信号线</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`DEA(field, signal_window, short_window, long_window)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">计算公式</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`DEA = EMA(DIF(field, short_window, long_window), signal_window)`}
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
              <td className="border border-slate-700 px-4 py-2">信号线EMA周期（默认9）</td>
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
          DEA（Difference Exponential Average）是DIF的指数移动平均，也称为信号线或慢线。
          DEA用于平滑DIF的波动，产生更稳定的交易信号。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 金叉：DIF上穿DEA（买入信号）
DIF(close, 12, 26) > DEA(close, 9, 12, 26)

// 死叉：DIF下穿DEA（卖出信号）
DIF(close, 12, 26) < DEA(close, 9, 12, 26)

// DEA趋势判断
DEA(close, 9, 12, 26) > 0`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>金叉死叉：DIF与DEA的交叉是经典买卖信号</li>
          <li>趋势确认：DEA方向变化确认趋势转变</li>
          <li>支撑压力：DEA常作为DIF的动态支撑或压力位</li>
        </ul>
      </div>
    </div>
  )
}
