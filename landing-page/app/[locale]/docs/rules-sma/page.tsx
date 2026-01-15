import { useTranslations } from 'next-intl'

export default function RulesSmaPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">SMA - 简单移动平均</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`SMA(close, period)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">close</code></td>
              <td className="border border-slate-700 px-4 py-2">Series</td>
              <td className="border border-slate-700 px-4 py-2">收盘价序列</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">period</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">周期</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-slate-300 mb-6">
          计算简单移动平均线（Simple Moving Average），是最常用的技术指标之一。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 金叉买入信号
SMA(close, 5) > SMA(close, 20)

// 死叉卖出信号
SMA(close, 5) < SMA(close, 20)

// 价格在均线之上
close > SMA(close, 10)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-slate-300 space-y-2">
          <li>双均线交叉策略：短期均线上穿长期均线买入，下穿卖出</li>
          <li>趋势判断：价格在均线上方为上升趋势，下方为下降趋势</li>
          <li>支撑压力位：均线常用作动态支撑或压力位</li>
        </ul>
      </div>
    </div>
  )
}
