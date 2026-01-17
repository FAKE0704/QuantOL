"use client";

/**
 * BacktestResultsView - Display backtest results using React + Recharts
 *
 * This component replaces the iframe-based Streamlit chart display,
 * providing a unified scrolling experience with full control over layout.
 */

import { useEffect, useState } from "react";
import { useApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  BacktestResults,
  dataframeToArray,
  EquityRecord,
  Trade,
  isSerializedDataFrame,
} from "@/types/backtest";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";

interface BacktestResultsViewProps {
  backtestId: string;
}

export function BacktestResultsView({ backtestId }: BacktestResultsViewProps) {
  const { getBacktestResults } = useApi();
  const [results, setResults] = useState<BacktestResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Fetch backtest results with retry logic
  useEffect(() => {
    const fetchResults = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getBacktestResults(backtestId);
        if (response.success && response.data) {
          // 后端返回的数据结构：data.result 包含实际的回测结果
          const data = response.data as { result?: BacktestResults };
          if (data.result) {
            setResults(data.result);
          } else {
            // 兼容：如果没有 result 字段，直接使用 data
            setResults(response.data as unknown as BacktestResults);
          }
        } else {
          setError(response.message || "Failed to load backtest results");
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
        setError(errorMsg);

        // Auto-retry for timeout or network errors (max 3 retries)
        const isTimeout = errorMsg.toLowerCase().includes('timeout');
        const isNetworkError = errorMsg.toLowerCase().includes('fetch') ||
                               errorMsg.toLowerCase().includes('network');

        if ((isTimeout || isNetworkError) && retryCount < 3) {
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
          }, 2000);  // Retry after 2 seconds
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [backtestId, retryCount]);

  // Loading state
  if (isLoading) {
    return (
      <Card className="p-8 bg-slate-900/50 border-slate-800">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
            <p className="text-slate-400">
              {retryCount > 0 ? `Retrying... (${retryCount}/3)` : 'Loading backtest results...'}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    const isTimeout = error.toLowerCase().includes('timeout');
    return (
      <Card className="p-8 bg-slate-900/50 border-slate-800">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-red-400 mb-2">
              {isTimeout ? '加载超时' : '加载结果时出错'}
            </p>
            <p className="text-slate-500 text-sm mb-4">{error}</p>
            <button
              onClick={() => setRetryCount(prev => prev + 1)}
              className="px-4 py-2 bg-sky-600 text-white rounded hover:bg-sky-700 transition-colors"
            >
              重新加载
            </button>
          </div>
        </div>
      </Card>
    );
  }

  // No results state
  if (!results) {
    return (
      <Card className="p-8 bg-slate-900/50 border-slate-800">
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-400">No results available</p>
        </div>
      </Card>
    );
  }

  // Get equity records as array
  const equityRecords = (results.equity_records && isSerializedDataFrame(results.equity_records)
    ? (results.equity_records.__data__ as unknown as EquityRecord[])
    : (results.equity_records as unknown as EquityRecord[])) || [];

  const trades = (results.trades && isSerializedDataFrame(results.trades)
    ? (results.trades.__data__ as unknown as Trade[])
    : (results.trades as unknown as Trade[])) || [];

  const combinedEquity = (results.combined_equity && isSerializedDataFrame(results.combined_equity)
    ? (results.combined_equity.__data__ as unknown as EquityRecord[])
    : (results.combined_equity as unknown as EquityRecord[])) || [];

  return (
    <Card className="bg-slate-900/50 border-slate-800 overflow-hidden">
      <Tabs defaultValue="summary" className="w-full">
        {/* Tab Headers */}
        <div className="border-b border-slate-700 bg-slate-900/30 px-4">
          <TabsList className="bg-transparent h-auto flex-wrap gap-1">
            <TabsTrigger value="summary" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📊 回测摘要
            </TabsTrigger>
            <TabsTrigger value="trades" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              💱 交易记录
            </TabsTrigger>
            <TabsTrigger value="positions" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📈 仓位明细
            </TabsTrigger>
            <TabsTrigger value="equity" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📉 净值曲线
            </TabsTrigger>
            <TabsTrigger value="indicators" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📈 技术指标
            </TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📊 风险收益指标
            </TabsTrigger>
            <TabsTrigger value="drawdown" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📉 回撤分析
            </TabsTrigger>
            <TabsTrigger value="returns" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              📊 收益分布
            </TabsTrigger>
            <TabsTrigger value="signals" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              🎯 交易信号
            </TabsTrigger>
            <TabsTrigger value="details" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              🔍 详细数据
            </TabsTrigger>
            <TabsTrigger value="debug" className="data-[state=active]:bg-sky-600/20 data-[state=active]:text-sky-400">
              🐛 调试数据
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Contents */}
        <div className="p-4">
          {/* 1. 回测摘要 */}
          <TabsContent value="summary" className="mt-0">
            <SummaryTab results={results} trades={trades} equityRecords={equityRecords} />
          </TabsContent>

          {/* 2. 交易记录 */}
          <TabsContent value="trades" className="mt-0">
            <TradesTab trades={trades} />
          </TabsContent>

          {/* 3. 仓位明细 */}
          <TabsContent value="positions" className="mt-0">
            <PositionsTab equityRecords={equityRecords} />
          </TabsContent>

          {/* 4. 净值曲线 */}
          <TabsContent value="equity" className="mt-0">
            <EquityTab equityRecords={equityRecords} combinedEquity={combinedEquity} />
          </TabsContent>

          {/* 5. 技术指标 */}
          <TabsContent value="indicators" className="mt-0">
            <IndicatorsTab priceData={results.price_data} />
          </TabsContent>

          {/* 6. 性能分析 */}
          <TabsContent value="performance" className="mt-0">
            <PerformanceTab results={results} />
          </TabsContent>

          {/* 7. 回撤分析 */}
          <TabsContent value="drawdown" className="mt-0">
            <DrawdownTab equityRecords={equityRecords} />
          </TabsContent>

          {/* 8. 收益分布 */}
          <TabsContent value="returns" className="mt-0">
            <ReturnsTab equityRecords={equityRecords} />
          </TabsContent>

          {/* 9. 交易信号 */}
          <TabsContent value="signals" className="mt-0">
            <SignalsTab signals={results.signals} />
          </TabsContent>

          {/* 10. 详细数据 */}
          <TabsContent value="details" className="mt-0">
            <DetailsTab equityRecords={equityRecords} trades={trades} />
          </TabsContent>

          {/* 11. 调试数据 */}
          <TabsContent value="debug" className="mt-0">
            <DebugTab debugData={results.debug_data} />
          </TabsContent>
        </div>
      </Tabs>
    </Card>
  );
}

// ============================================================================
// Tab Components (Placeholder implementations)
// ============================================================================

function SummaryTab({ results, trades, equityRecords }: { results: BacktestResults; trades: Trade[]; equityRecords: EquityRecord[] }) {
  // Check if required data exists - only check summary since performance_metrics may not be returned by backend
  if (!results.summary) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">回测摘要</h3>
        <div className="text-slate-400">回测数据不完整或正在生成中...</div>
      </div>
    );
  }

  // 计算盈亏交易笔数比
  const winCount = trades.filter(t => (t.profit ?? 0) > 0).length;
  const lossCount = trades.filter(t => (t.profit ?? 0) < 0).length;
  const winLossCountRatio = lossCount > 0 ? (winCount / lossCount).toFixed(2) : '∞';

  // 计算最大连续盈利/亏损天数
  let maxConsecutiveWinDays = 0;
  let maxConsecutiveLossDays = 0;
  let currentWinStreak = 0;
  let currentLossStreak = 0;

  for (let i = 1; i < equityRecords.length; i++) {
    const prevValue = equityRecords[i - 1].total_value;
    const currValue = equityRecords[i].total_value;
    const dailyReturn = currValue - prevValue;

    if (dailyReturn > 0) {
      currentWinStreak++;
      currentLossStreak = 0;
      maxConsecutiveWinDays = Math.max(maxConsecutiveWinDays, currentWinStreak);
    } else if (dailyReturn < 0) {
      currentLossStreak++;
      currentWinStreak = 0;
      maxConsecutiveLossDays = Math.max(maxConsecutiveLossDays, currentLossStreak);
    }
  }

  // 获取盈亏比（后端已计算）
  const profitLossRatio = results.performance_metrics?.profit_loss_ratio;
  const profitLossRatioDisplay = profitLossRatio != null
    ? (profitLossRatio === Infinity ? '∞' : profitLossRatio.toFixed(2))
    : 'N/A';

  // 获取年化收益率（后端已计算）
  const annualReturn = results.performance_metrics?.annual_return;
  const annualReturnDisplay = annualReturn != null ? `${annualReturn.toFixed(2)}%` : 'N/A';

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">回测摘要</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* 基础指标 */}
        <MetricCard label="初始资金" value={`¥${(results.summary.initial_capital || 0).toLocaleString()}`} />
        <MetricCard label="最终资金" value={`¥${(results.summary.final_capital || 0).toLocaleString()}`} />
        <MetricCard label="总收益率" value={`${(results.summary.total_return || 0).toFixed(2)}%`} />
        <MetricCard label="最大回撤" value={`${(results.summary.max_drawdown || 0).toFixed(2)}%`} />

        {/* 交易统计 */}
        <MetricCard label="交易次数" value={(results.summary.total_trades || 0).toString()} />
        <MetricCard label="胜率" value={`${((results.summary.win_rate || 0) * 100).toFixed(2)}%`} />
        <MetricCard label="盈亏比" value={profitLossRatioDisplay} />
        <MetricCard label="盈亏笔数比" value={winLossCountRatio} />

        {/* 收益指标 */}
        <MetricCard label="夏普比率" value={results.performance_metrics?.sharpe_ratio?.toFixed(2) || 'N/A'} />
        <MetricCard label="年化收益率" value={annualReturnDisplay} />
        <MetricCard label="最大连盈天数" value={maxConsecutiveWinDays > 0 ? `${maxConsecutiveWinDays}天` : '0天'} />
        <MetricCard label="最大连亏天数" value={maxConsecutiveLossDays > 0 ? `${maxConsecutiveLossDays}天` : '0天'} />

        {/* 策略信息 */}
        <MetricCard label="仓位策略" value={results.summary.position_strategy_type || 'N/A'} />
      </div>
    </div>
  );
}

function TradesTab({ trades }: { trades: Trade[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">交易记录</h3>
      {trades.length === 0 ? (
        <div className="text-slate-400 text-sm">无交易记录</div>
      ) : (
        <>
          <div className="text-xs text-slate-500 mb-2">共 {trades.length} 笔交易</div>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-2 text-left text-slate-300">时间</th>
                  <th className="px-4 py-2 text-left text-slate-300">股票</th>
                  <th className="px-4 py-2 text-left text-slate-300">类型</th>
                  <th className="px-4 py-2 text-right text-slate-300">价格</th>
                  <th className="px-4 py-2 text-right text-slate-300">数量</th>
                  <th className="px-4 py-2 text-right text-slate-300">金额</th>
                  <th className="px-4 py-2 text-right text-slate-300">收益</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {trades.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50">
                    <td className="px-4 py-2 text-slate-300">
                      {trade.timestamp ? new Date(trade.timestamp).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-2 text-slate-300">{trade.symbol || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        trade.direction === 'BUY' || trade.direction === 'OPEN'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.direction || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-slate-300">
                      {trade.price != null ? `¥${trade.price.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-300">
                      {trade.quantity ?? '-'}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-300">
                      {trade.amount !== undefined ? `¥${trade.amount.toLocaleString()}` : '-'}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {trade.profit != null ? (
                        <span className={trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {trade.profit >= 0 ? '+' : ''}¥{trade.profit.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function PositionsTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  // Calculate average position allocation from equity records
  const avgAllocation = equityRecords.length > 0
    ? equityRecords.reduce((sum, record) => {
        const ratio = record.total_value && record.total_value > 0
          ? (record.positions_value || 0) / record.total_value
          : 0;
        return sum + ratio;
      }, 0) / equityRecords.length
    : 0;

  const avgCash = 1 - avgAllocation;

  const pieData = [
    { name: '平均持仓占比', value: avgAllocation * 100 },
    { name: '平均现金占比', value: avgCash * 100 },
  ];

  const COLORS = ['#1f77b4', '#2ca02c'];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">仓位明细</h3>
      {equityRecords.length === 0 ? (
        <div className="text-slate-400 text-sm">无仓位数据</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
              <h4 className="text-sm font-medium text-slate-400 mb-3">平均资产配置占比</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${isFinite(percent) ? (percent * 100).toFixed(1) : '0.0'}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                    formatter={(value: number) => [`${isFinite(value) ? value.toFixed(2) : '0.00'}%`, '']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Summary Stats */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-400">配置统计</h4>
              <div className="grid grid-cols-2 gap-3">
                <MetricCard
                  label="平均持仓占比"
                  value={`${(avgAllocation * 100).toFixed(2)}%`}
                />
                <MetricCard
                  label="平均现金占比"
                  value={`${(avgCash * 100).toFixed(2)}%`}
                />
                <MetricCard
                  label="最高持仓占比"
                  value={`${Math.max(...equityRecords.map(r => r.total_value > 0 ? ((r.positions_value || 0) / r.total_value) * 100 : 0)).toFixed(2)}%`}
                />
                <MetricCard
                  label="最低持仓占比"
                  value={`${Math.min(...equityRecords.map(r => r.total_value > 0 ? ((r.positions_value || 0) / r.total_value) * 100 : 0)).toFixed(2)}%`}
                />
              </div>

              {/* Current Position */}
              {equityRecords.length > 0 && (
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                  <h5 className="text-xs text-slate-400 mb-2">最新持仓</h5>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-300">持仓市值</span>
                      <span className="text-sm font-semibold text-sky-400">
                        ¥{equityRecords[equityRecords.length - 1].positions_value?.toLocaleString() || '0'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-300">现金</span>
                      <span className="text-sm font-semibold text-green-400">
                        ¥{equityRecords[equityRecords.length - 1].cash.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-300">总资产</span>
                      <span className="text-sm font-semibold text-white">
                        ¥{equityRecords[equityRecords.length - 1].total_value.toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function EquityTab({
  equityRecords,
  combinedEquity,
}: {
  equityRecords: EquityRecord[];
  combinedEquity: EquityRecord[];
}) {
  const hasCombined = combinedEquity && combinedEquity.length > 0;

  // Calculate return percentage from initial value
  const calculateReturnData = (records: EquityRecord[]) => {
    if (records.length === 0) return [];
    const initialValue = records[0].total_value;
    return records.map((record) => ({
      ...record,
      return_pct: ((record.total_value - initialValue) / initialValue) * 100,
      allocation_pct: ((record.positions_value || 0) / record.total_value) * 100,
    }));
  };

  const equityData = hasCombined ? combinedEquity : equityRecords;
  const chartData = calculateReturnData(equityData);

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">净值曲线</h3>

      {/* 净值百分比变化与资产配置 */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-3">📊 净值百分比变化与资产配置</h4>
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="timestamp"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                label={{ value: "百分比 (%)", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                labelStyle={{ color: "#94a3b8" }}
                // @ts-expect-error - Recharts formatter type is overly strict
                formatter={(value: number, name: string) => [`${isFinite(value) ? value.toFixed(2) : '0.00'}%`, name]}
                labelFormatter={(value: any) => new Date(value).toLocaleString()}
              />
              <Legend wrapperStyle={{ color: "#94a3b8" }} />
              <Line
                type="monotone"
                dataKey="return_pct"
                stroke="#1f77b4"
                strokeWidth={2}
                name="净值变化 (%)"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="allocation_pct"
                stroke="#ff7f0e"
                strokeWidth={2}
                name="资产配置比例 (%)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 绝对净值金额 */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-3">📈 绝对净值变化</h4>
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="timestamp"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                label={{ value: "金额 (¥)", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                labelStyle={{ color: "#94a3b8" }}
                formatter={(value: number) => `¥${value.toLocaleString()}`}
                labelFormatter={(value: any) => new Date(value).toLocaleString()}
              />
              <Legend wrapperStyle={{ color: "#94a3b8" }} />
              <Line
                type="monotone"
                dataKey="total_value"
                stroke="#1f77b4"
                strokeWidth={2.5}
                name="总资产"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="positions_value"
                stroke="#ff7f0e"
                strokeWidth={2}
                name="持仓市值"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="cash"
                stroke="#2ca02c"
                strokeWidth={1.5}
                strokeDasharray="5 5"
                name="现金"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Metrics */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            label="初始总资产"
            value={`¥${chartData[0].total_value.toLocaleString()}`}
          />
          <MetricCard
            label="最终总资产"
            value={`¥${chartData[chartData.length - 1].total_value.toLocaleString()}`}
          />
          <MetricCard
            label="总收益"
            value={`${(chartData[chartData.length - 1].return_pct ?? 0).toFixed(2)}%`}
          />
        </div>
      )}
    </div>
  );
}

function IndicatorsTab({ priceData }: { priceData?: unknown }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">技术指标分析</h3>
      <div className="text-slate-400 text-sm">
        技术指标图表需要从价格数据中计算生成
      </div>
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <div className="text-xs text-slate-500 mb-2">支持的指标：</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-400">
          <div className="bg-slate-700/50 rounded px-2 py-1">SMA</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">EMA</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">MACD</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">RSI</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">布林带</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">KDJ</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">成交量</div>
          <div className="bg-slate-700/50 rounded px-2 py-1">ATR</div>
        </div>
      </div>
    </div>
  );
}

function PerformanceTab({ results }: { results: BacktestResults }) {
  const metrics = results.performance_metrics || {};

  // 辅助函数：格式化数字，处理 NaN 和 Infinity
  const formatNumber = (value: number | undefined, decimals: number = 3): string | undefined => {
    if (value == null || isNaN(value) || !isFinite(value)) {
      return undefined;
    }
    return value.toFixed(decimals);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">风险收益指标</h3>
      {Object.keys(metrics).length === 0 ? (
        <div className="text-slate-400 text-sm">无性能指标数据</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <MetricCard
            label="夏普比率"
            value={formatNumber(metrics.sharpe_ratio) || 'N/A'}
          />
          <MetricCard
            label="索提诺比率"
            value={formatNumber(metrics.sortino_ratio) || 'N/A'}
          />
          <MetricCard
            label="卡玛比率"
            value={formatNumber(metrics.calmar_ratio) || 'N/A'}
          />
          <MetricCard
            label="最大回撤"
            value={`${(metrics.max_drawdown_pct || 0).toFixed(2)}%`}
          />
          <MetricCard
            label="年化收益"
            value={`${(metrics.annual_return || 0).toFixed(2)}%`}
          />
          <MetricCard
            label="波动率"
            value={formatNumber(metrics.volatility) || 'N/A'}
          />
          <MetricCard
            label="总收益"
            value={`${(metrics.total_return_pct || 0).toFixed(2)}%`}
          />
          <MetricCard
            label="总盈亏金额"
            value={`¥${(metrics.total_profit_amount || 0).toLocaleString()}`}
          />
          <MetricCard
            label="盈亏比"
            value={
              metrics.profit_loss_ratio == null || isNaN(metrics.profit_loss_ratio)
                ? 'N/A'
                : !isFinite(metrics.profit_loss_ratio)
                ? '∞'
                : metrics.profit_loss_ratio.toFixed(2)
            }
          />
          <MetricCard
            label="平均持仓天数"
            value={
              metrics.avg_holding_days != null && !isNaN(metrics.avg_holding_days)
                ? `${metrics.avg_holding_days.toFixed(1)}天`
                : 'N/A'
            }
          />
        </div>
      )}
    </div>
  );
}

function DrawdownTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  // Calculate drawdown for each point
  const drawdownData = equityRecords.map((record, idx) => {
    const peakSoFar = Math.max(...equityRecords.slice(0, idx + 1).map(r => r.total_value));
    const drawdown = ((peakSoFar - record.total_value) / peakSoFar) * 100;
    return {
      timestamp: record.timestamp,
      drawdown: Math.max(0, drawdown),
      peak: peakSoFar,
      value: record.total_value,
    };
  });

  const maxDrawdown = Math.max(...drawdownData.map(d => d.drawdown));

  // Handle edge cases where maxDrawdown might be NaN or -Infinity
  const safeMaxDrawdown = isFinite(maxDrawdown) ? maxDrawdown : 0;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">回撤分析</h3>
      {equityRecords.length === 0 ? (
        <div className="text-slate-400 text-sm">无净值数据</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <MetricCard label="最大回撤" value={`${safeMaxDrawdown.toFixed(2)}%`} />
            <MetricCard
              label="回撤次数"
              value={drawdownData.filter(d => d.drawdown > 0).length.toString()}
            />
            <MetricCard
              label="平均回撤"
              value={`${(drawdownData.reduce((sum, d) => sum + d.drawdown, 0) / drawdownData.filter(d => d.drawdown > 0).length || 0).toFixed(2)}%`}
            />
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={drawdownData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  label={{ value: "回撤 (%)", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
                  domain={[0, 'dataMax']}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                  labelStyle={{ color: "#94a3b8" }}
                  formatter={(value: number) => [`${isFinite(value) ? value.toFixed(2) : '0.00'}%`, '回撤']}
                  labelFormatter={(value: any) => new Date(value).toLocaleString()}
                />
                <Area
                  type="monotone"
                  dataKey="drawdown"
                  stroke="#ef4444"
                  fill="#ef4444"
                  fillOpacity={0.3}
                  name="回撤 (%)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

function ReturnsTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  // Calculate daily returns
  const returns = equityRecords.slice(1).map((record, idx) => {
    const prevValue = equityRecords[idx].total_value;
    const dailyReturn = prevValue !== 0 ? ((record.total_value - prevValue) / prevValue) * 100 : 0;
    return {
      timestamp: record.timestamp,
      return: dailyReturn,
    };
  });

  // Check if we have valid returns data
  if (returns.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">收益分布</h3>
        <div className="text-slate-400 text-sm">数据不足，无法计算收益分布</div>
      </div>
    );
  }

  // Filter out NaN and Infinity values
  const validReturns = returns.filter(r => isFinite(r.return));

  if (validReturns.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">收益分布</h3>
        <div className="text-slate-400 text-sm">无有效收益数据</div>
      </div>
    );
  }

  // Create histogram data
  const bins = 20;
  const minReturn = Math.min(...validReturns.map(r => r.return));
  const maxReturn = Math.max(...validReturns.map(r => r.return));
  const binSize = (maxReturn - minReturn) / bins;

  const histogram = Array.from({ length: bins }, (_, i) => {
    const binStart = minReturn + i * binSize;
    const binEnd = binStart + binSize;
    const count = validReturns.filter(r => r.return >= binStart && r.return < binEnd).length;
    return {
      range: `${binStart.toFixed(2)}% - ${binEnd.toFixed(2)}%`,
      count,
      fill: count > 0 ? (binStart >= 0 ? '#22c55e' : '#ef4444') : '#334155',
    };
  });

  const avgReturn = validReturns.reduce((sum, r) => sum + r.return, 0) / validReturns.length;
  const positiveReturns = validReturns.filter(r => r.return > 0).length;
  const negativeReturns = validReturns.filter(r => r.return < 0).length;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">收益分布</h3>
      {equityRecords.length < 2 ? (
        <div className="text-slate-400 text-sm">数据不足，无法计算收益分布</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <MetricCard
              label="平均日收益"
              value={`${avgReturn.toFixed(3)}%`}
            />
            <MetricCard
              label="盈利天数"
              value={`${positiveReturns}天`}
            />
            <MetricCard
              label="亏损天数"
              value={`${negativeReturns}天`}
            />
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={histogram}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="range"
                  tick={{ fill: "#94a3b8", fontSize: 10 }}
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  label={{ value: "天数", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Bar dataKey="count" name="天数" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

function SignalsTab({ signals }: { signals?: unknown }) {
  // Parse signals data
  const signalsData = signals && isSerializedDataFrame(signals)
    ? (signals.__data__ as unknown as Array<{ timestamp: string; signal: number; signal_type: string; price: number; symbol: string }>)
    : (signals as unknown as Array<{ timestamp: string; signal: number; signal_type: string; price: number; symbol: string }>) || [];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">交易信号分析</h3>
      {signalsData.length === 0 ? (
        <div className="text-slate-400 text-sm">无交易信号数据</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <MetricCard
              label="总信号数"
              value={signalsData.length.toString()}
            />
            <MetricCard
              label="买入信号"
              value={signalsData.filter(s => s.signal > 0).length.toString()}
            />
            <MetricCard
              label="卖出信号"
              value={signalsData.filter(s => s.signal < 0).length.toString()}
            />
            <MetricCard
              label="涉及股票"
              value={[...new Set(signalsData.map(s => s.symbol))].length.toString()}
            />
          </div>
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-sm">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-2 text-left text-slate-300">时间</th>
                  <th className="px-4 py-2 text-left text-slate-300">股票</th>
                  <th className="px-4 py-2 text-left text-slate-300">信号类型</th>
                  <th className="px-4 py-2 text-right text-slate-300">价格</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {signalsData.map((signal, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50">
                    <td className="px-4 py-2 text-slate-300">
                      {signal.timestamp ? new Date(signal.timestamp).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-2 text-slate-300">{signal.symbol || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        signal.signal > 0
                          ? 'bg-green-500/20 text-green-400'
                          : signal.signal < 0
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {signal.signal_type || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-slate-300">
                      {signal.price != null ? `¥${signal.price.toFixed(2)}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function DetailsTab({
  equityRecords,
  trades,
}: {
  equityRecords: EquityRecord[];
  trades: Trade[];
}) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">详细数据</h3>

      {/* Equity Records Section */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-2">净值记录</h4>
        {equityRecords.length === 0 ? (
          <div className="text-slate-500 text-sm">无净值记录</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-700 max-h-64 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-800 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left text-slate-300">时间</th>
                  <th className="px-3 py-2 text-right text-slate-300">总资产</th>
                  <th className="px-3 py-2 text-right text-slate-300">持仓市值</th>
                  <th className="px-3 py-2 text-right text-slate-300">现金</th>
                  <th className="px-3 py-2 text-right text-slate-300">持仓占比</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {equityRecords.slice(-100).map((record, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50">
                    <td className="px-3 py-2 text-slate-300">
                      {record.timestamp ? new Date(record.timestamp).toLocaleString() : '-'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-300">
                      {record.total_value !== undefined ? `¥${record.total_value.toLocaleString()}` : '-'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-300">
                      ¥{(record.positions_value || 0).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-300">
                      {record.cash !== undefined ? `¥${record.cash.toLocaleString()}` : '-'}
                    </td>
                    <td className="px-3 py-2 text-right text-slate-300">
                      {record.total_value && isFinite(record.total_value) && record.total_value > 0 ? `${(((record.positions_value || 0) / record.total_value) * 100).toFixed(2)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {equityRecords.length > 100 && (
              <div className="text-xs text-slate-500 text-center py-2">
                仅显示最近100条记录（共{equityRecords.length}条）
              </div>
            )}
          </div>
        )}
      </div>

      {/* Trades Section */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-2">交易记录</h4>
        {trades.length === 0 ? (
          <div className="text-slate-500 text-sm">无交易记录</div>
        ) : (
          <div className="text-xs text-slate-500">
            共 {trades.length} 笔交易，详见"交易记录"标签页
          </div>
        )}
      </div>
    </div>
  );
}

function DebugTab({ debugData }: { debugData?: Record<string, unknown> }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">规则解析器调试数据</h3>
      {!debugData || Object.keys(debugData).length === 0 ? (
        <div className="text-slate-500 text-sm">
          无调试数据可用（仅在使用自定义规则策略时生成）
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(debugData).map(([strategyName, data]) => {
            if (!isSerializedDataFrame(data)) return null;
            const records = data.__data__ as Record<string, unknown>[];
            const columns = records.length > 0 ? Object.keys(records[0]) : [];

            return (
              <div key={strategyName} className="space-y-2">
                <h4 className="text-sm font-medium text-slate-400">策略: {strategyName}</h4>
                <div className="text-xs text-slate-500 mb-1">
                  {records.length} 条记录, {columns.length} 个字段
                </div>
                <div className="overflow-x-auto rounded-lg border border-slate-700 max-h-64 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-800 sticky top-0">
                      <tr>
                        {columns.slice(0, 10).map((col) => (
                          <th key={col} className="px-3 py-2 text-left text-slate-300">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {records.slice(0, 50).map((record, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/50">
                          {columns.slice(0, 10).map((col) => (
                            <td key={col} className="px-3 py-2 text-slate-300">
                              {record[col]?.toString().slice(0, 50) || '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {records.length > 50 && (
                    <div className="text-xs text-slate-500 text-center py-2">
                      仅显示前50条记录（共{records.length}条）
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Helper component for metric display
function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="text-lg font-semibold text-sky-400">{value}</div>
    </div>
  );
}
