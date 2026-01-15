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
              📊 性能分析
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
            <SummaryTab results={results} />
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

function SummaryTab({ results }: { results: BacktestResults }) {
  // Check if required data exists - only check summary since performance_metrics may not be returned by backend
  if (!results.summary) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">回测摘要</h3>
        <div className="text-slate-400">回测数据不完整或正在生成中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">回测摘要</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="初始资金" value={`¥${(results.summary.initial_capital || 0).toLocaleString()}`} />
        <MetricCard label="最终资金" value={`¥${(results.summary.final_capital || 0).toLocaleString()}`} />
        <MetricCard label="总收益率" value={`${(results.summary.total_return || 0).toFixed(2)}%`} />
        <MetricCard label="最大回撤" value={`${(results.summary.max_drawdown || 0).toFixed(2)}%`} />
        <MetricCard label="交易次数" value={(results.summary.total_trades || 0).toString()} />
        <MetricCard label="胜率" value={`${((results.summary.win_rate || 0) * 100).toFixed(2)}%`} />
        <MetricCard label="夏普比率" value={results.performance_metrics?.sharpe_ratio?.toFixed(2) || 'N/A'} />
        <MetricCard label="仓位策略" value={results.summary.position_strategy_type || 'N/A'} />
      </div>
    </div>
  );
}

function TradesTab({ trades }: { trades: Trade[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">交易记录</h3>
      <div className="text-slate-400">交易记录图表 - 待实现</div>
      <div className="text-xs text-slate-500">Total trades: {trades.length}</div>
    </div>
  );
}

function PositionsTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">仓位明细</h3>
      <div className="text-slate-400">仓位饼图 - 待实现</div>
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
                formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name]}
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
                // @ts-expect-error - Recharts formatter type is overly strict
                formatter={(value: number) => [`¥${value.toLocaleString()}`, ""]}
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
            value={`${chartData[chartData.length - 1].return_pct.toFixed(2)}%`}
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
      <div className="text-slate-400">技术指标图表 - 待实现</div>
    </div>
  );
}

function PerformanceTab({ results }: { results: BacktestResults }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">性能分析</h3>
      <div className="text-slate-400">性能指标详情 - 待实现</div>
    </div>
  );
}

function DrawdownTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">回撤分析</h3>
      <div className="text-slate-400">回撤曲线图 - 待实现</div>
    </div>
  );
}

function ReturnsTab({ equityRecords }: { equityRecords: EquityRecord[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">收益分布</h3>
      <div className="text-slate-400">收益分布直方图 - 待实现</div>
    </div>
  );
}

function SignalsTab({ signals }: { signals?: unknown }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">交易信号分析</h3>
      <div className="text-slate-400">交易信号图 - 待实现</div>
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
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">详细数据</h3>
      <div className="text-slate-400">详细数据表格 - 待实现</div>
    </div>
  );
}

function DebugTab({ debugData }: { debugData?: Record<string, unknown> }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">规则解析器调试数据</h3>
      {debugData ? (
        <div className="text-slate-400">调试数据 - 待实现</div>
      ) : (
        <div className="text-slate-500 text-sm">无调试数据可用（仅在使用自定义规则策略时生成）</div>
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
