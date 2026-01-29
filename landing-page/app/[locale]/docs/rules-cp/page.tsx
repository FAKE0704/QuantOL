import { useTranslations } from 'next-intl'

export default function RulesCpPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">C_P - 典型价格</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`C_P(period)`}
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
              <td className="border border-slate-700 px-4 py-2">向前回溯的期数（0 表示当期）</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          典型价格（Typical Price），计算公式：(最高价 + 最低价) / 2。
          相比收盘价，典型价格更能反映当日价格的核心区域。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 当前典型价格
C_P(0)

// 前一日典型价格
C_P(1)

// 价格高于典型价格（强势）
close > C_P(0)

// 使用典型价格计算均线
SMA(C_P(0), 10)

// 典型价格突破
close > C_P(0) & close > REF(close, 1)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>价格分析：作为收盘价的补充指标</li>
          <li>均线计算：基于典型价格计算均线更平滑</li>
          <li>VWAP计算：典型价格是VWAP的基础</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>数据不足时返回 0.0</li>
            <li>period 参数超出范围时返回 0.0</li>
            <li>常与其他指标结合使用</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
