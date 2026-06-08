import { useTranslations } from 'next-intl'

export default function RulesStdPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">STD - 标准差</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`STD(close, n)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">n</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">周期</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          计算收盘价在n个周期内的标准差（Standard Deviation），用于衡量价格的波动性。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 波动率突破策略：价格突破均值加2倍标准差时买入
close > SMA(close, 20) + 2 * STD(close, 20)

// 波动率下降：当前标准差小于前期标准差
STD(close, 10) < STD(close, 20)

// 布林带上轨
SMA(close, 20) + 2 * STD(close, 20)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>布林带：使用标准差构建动态通道</li>
          <li>波动率突破：在高波动时进行交易</li>
          <li>风险度量：标准差越大，价格波动越剧烈</li>
        </ul>
      </div>
    </div>
  )
}
