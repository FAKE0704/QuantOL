import { useTranslations } from 'next-intl'

export default function RulesZScorePage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">Z_SCORE - Z分数</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`Z_SCORE(close, n)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">计算公式</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`Z_SCORE = (close - SMA(close, n)) / STD(close, n)`}
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
          Z分数（Z-Score）用于标准化价格数据，表示当前价格相对于均线的偏离程度，以标准差为单位。
          Z_SCORE = 0 表示价格等于均线，Z_SCORE = 2 表示价格高于均值2倍标准差。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 均值回归：价格偏离均值超过2倍标准差时买入
Z_SCORE(close, 20) < -2

// 统计套利：价格处于高位时卖出
Z_SCORE(close, 20) > 2

// 动态阈值：根据波动率调整交易信号
Z_SCORE(close, 10) > 1.5

// 波动率标准化后的均值交叉
Z_SCORE(close, 5) > Z_SCORE(close, 20)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>均值回归策略：价格过度偏离均值时进行反向交易</li>
          <li>统计套利：识别价格异常波动</li>
          <li>动态入场点：根据统计显著性确定买卖时机</li>
          <li>风险管理：Z分数绝对值越大，风险越高</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">数值解释</h2>
        <table className="w-full border-collapse border border-slate-700 mb-6">
          <thead>
            <tr className="bg-slate-800">
              <th className="border border-slate-700 px-4 py-2 text-left">Z_SCORE范围</th>
              <th className="border border-slate-700 px-4 py-2 text-left">含义</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-slate-700 px-4 py-2">Z_SCORE &gt; 2</td>
              <td className="border border-slate-700 px-4 py-2">价格显著高于均值（超买）</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">0 &lt; Z_SCORE &lt; 2</td>
              <td className="border border-slate-700 px-4 py-2">价格高于均值但在正常范围</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">Z_SCORE ≈ 0</td>
              <td className="border border-slate-700 px-4 py-2">价格接近均值</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">-2 &lt; Z_SCORE &lt; 0</td>
              <td className="border border-slate-700 px-4 py-2">价格低于均值但在正常范围</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">Z_SCORE &lt; -2</td>
              <td className="border border-slate-700 px-4 py-2">价格显著低于均值（超卖）</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
