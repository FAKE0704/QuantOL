import { useTranslations } from 'next-intl'

export default function RulesRankPage() {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">RANK - 横截面排名</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">函数定义</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`RANK(field)`}
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
              <td className="border border-slate-700 px-4 py-2">string</td>
              <td className="border border-slate-700 px-4 py-2">字段名，如 close、volume、high 等</td>
            </tr>
          </tbody>
        </table>

        <h2 className="text-2xl font-semibold mb-4">描述</h2>
        <p className="text-muted-foreground mb-6">
          计算当前股票的 <code className="text-sky-400">field</code> 值在所有股票中的横截面排名。
          返回整数排名（1=最高值，2=第二高，...），无数据时返回 0。
        </p>

        <h2 className="text-2xl font-semibold mb-4">使用示例</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`// 基本排名
// 买入今天收盘价排名前10的股票
RANK(close) <= 10

// 加仓成交量排名前一半的股票
RANK(volume) > len / 2

// 卖出收盘价排名后20的股票
RANK(close) >= 20

// 时间维度配合REF
// 持续排名前10（今天和5天前都在前10）
RANK(close) <= 10 and REF(RANK(close), 5) <= 10

// 排名上升趋势
RANK(close) < REF(RANK(close), 5)

// 逻辑组合
// 综合条件：排名前10且价格高于均线
(RANK(close) <= 10) and (close > SMA(close, 20))`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">典型应用</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>因子选股：基于横截面排名选择表现最好的股票</li>
          <li>动量策略：选择排名上升趋势的股票</li>
          <li>相对强弱：买入相对表现强势的股票</li>
          <li>多因子组合：结合多个排名指标进行筛选</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">注意事项</h2>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>RANK函数需要在多标模式下使用</li>
            <li>排名规则：值越大排名越前（降序排列）</li>
            <li>时间维度通过REF函数实现，RANK本身只计算当前时间点的横截面排名</li>
            <li>无横截面数据时返回 0</li>
            <li>建议配合其他条件使用，避免在数据不足时产生错误信号</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
