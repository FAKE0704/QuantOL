import { useTranslations } from 'next-intl'

export default function RulesSqrtPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">SQRT - 开方</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`SQRT(x, n)`}
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
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">x</code></td>
              <td className="border border-slate-700 px-4 py-2">float</td>
              <td className="border border-slate-700 px-4 py-2">底数</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2"><code className="text-sky-400">n</code></td>
              <td className="border border-slate-700 px-4 py-2">int</td>
              <td className="border border-slate-700 px-4 py-2">开方次数（2=平方根，3=立方根）</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-slate-300 mb-6">
          对 x 开 n 次方，计算公式：x^(1/n)。
          <br />
          例如：SQRT(9, 2) = 9^(1/2) = 3（平方根），SQRT(27, 3) = 27^(1/3) = 3（立方根）
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 计算高低价的几何平均值
SQRT(high * low, 2)

// 与 VWAP 结合使用
SQRT(high * low, 2) - VWAP(15)

// 动态筛选
SQRT(high * low, 2) < REF(Q(SQRT(high * low, 2) - VWAP(15), 0.8, 10), 1)

// 立方根（用于特殊指标）
SQRT(volume, 3)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-slate-300 space-y-2">
          <li>几何平均：计算多个数值的几何平均</li>
          <li>价格平滑：使用几何平均平滑价格波动</li>
          <li>复合指标：结合其他指标构建复杂策略</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-slate-300 space-y-1">
            <li>开偶数次方时，负数底数会返回 0.0</li>
            <li>n = 0 时返回 1.0（任何数的 0 次方都是 1）</li>
            <li>计算失败时返回 0.0</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
