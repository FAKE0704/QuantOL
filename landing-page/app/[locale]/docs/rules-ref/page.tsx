import { useTranslations } from 'next-intl'

export default function RulesRefPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">REF - 引用历史数据</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`REF(expression, period)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">expression</code></td>
              <td className="border border-slate-700 px-4 py-2">Expression</td>
              <td className="border border-slate-700 px-4 py-2">任意表达式或值</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">period</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">向前引用的周期数</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          引用 <code className="text-sky-400">period</code> 个周期前的值。例如，<code className="text-sky-400">REF(close, 1)</code> 获取前一日的收盘价。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 昨日收盘价
REF(close, 1)

// 5天前的收盘价
REF(close, 5)

// 均线金叉：昨日短期均线在长期均线之下，今日之上
REF(SMA(close, 5), 1) < REF(SMA(close, 20), 1) &
SMA(close, 5) > SMA(close, 20)

// 引用另一个指标的值
REF(RSI(close, 14), 1) < 30 &
RSI(close, 14) >= 30`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>拐点检测：比较当前值与历史值的变化</li>
          <li>交叉确认：结合REF函数判断信号的有效性</li>
          <li>趋势反转：通过历史数据判断趋势是否改变</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>引用周期不能超过当前可用的历史数据长度</li>
            <li>在数据起始位置，REF可能返回空值</li>
            <li>建议配合其他条件使用，避免在数据不足时产生错误信号</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
