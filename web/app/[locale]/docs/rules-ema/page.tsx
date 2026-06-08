import { useTranslations } from 'next-intl'

export default function RulesEmaPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">EMA - 指数移动平均线</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`EMA(close, n)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">计算公式</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`EMA = (当前价格 × 平滑系数) + (前一日EMA × (1 - 平滑系数))
平滑系数 = 2 / (n + 1)`}
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
          指数移动平均线（Exponential Moving Average）给予近期价格更高的权重，相比SMA更能快速响应价格变化。
          常用周期包括EMA12（短期）、EMA26（中期）、EMA50（中期）和EMA200（长期）。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// EMA金叉：短期均线上穿长期均线
EMA(close, 12) > EMA(close, 26)

// EMA死叉：短期均线下穿长期均线
EMA(close, 12) < EMA(close, 26)

// 趋势过滤：价格在长期EMA之上为上升趋势
close > EMA(close, 200)

// MACD的基础
EMA(close, 12) - EMA(close, 26)`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>MACD指标：使用EMA12和EMA26计算</li>
          <li>趋势判断：EMA200常用于判断长期趋势</li>
          <li>交叉策略：EMA金叉死叉交易信号</li>
          <li>动态支撑压力：EMA线常用作动态支撑或压力位</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">EMA vs SMA</h2>
        <table className="w-full border-collapse border border-slate-700 mb-6">
          <thead>
            <tr className="bg-slate-800">
              <th className="border border-slate-700 px-4 py-2 text-left">特性</th>
              <th className="border border-slate-700 px-4 py-2 text-left">EMA</th>
              <th className="border border-slate-700 px-4 py-2 text-left">SMA</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-slate-700 px-4 py-2">权重分配</td>
              <td className="border border-slate-700 px-4 py-2">近期权重高</td>
              <td className="border border-slate-700 px-4 py-2">所有数据权重相等</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">响应速度</td>
              <td className="border border-slate-700 px-4 py-2">更快</td>
              <td className="border border-slate-700 px-4 py-2">较慢</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">滞后性</td>
              <td className="border border-slate-700 px-4 py-2">较小</td>
              <td className="border border-slate-700 px-4 py-2">较大</td>
            </tr>
            <tr>
              <td className="border border-slate-700 px-4 py-2">适用场景</td>
              <td className="border border-slate-700 px-4 py-2">短线交易、快速响应</td>
              <td className="border border-slate-700 px-4 py-2">长线趋势、稳定信号</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
