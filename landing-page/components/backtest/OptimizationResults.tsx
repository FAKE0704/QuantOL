"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScreeningResult } from "@/types/optimization";
import { Trophy, TrendingUp, TrendingDown, Activity, Download } from "lucide-react";

interface OptimizationResultsProps {
  optimizationId: string;
  results: ScreeningResult[];
  status: "pending" | "screening" | "completed" | "failed";
  error?: string;
  onSelectResult?: (result: ScreeningResult) => void;
}

export function OptimizationResults({
  optimizationId,
  results,
  status,
  error,
  onSelectResult,
}: OptimizationResultsProps) {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: "asc" | "desc";
  }>({
    key: "rank",
    direction: "asc",
  });

  // Sort results
  const sortedResults = [...results].sort((a, b) => {
    const aValue = getSortValue(a, sortConfig.key);
    const bValue = getSortValue(b, sortConfig.key);
    if (sortConfig.direction === "asc") {
      return aValue > bValue ? 1 : -1;
    }
    return aValue < bValue ? 1 : -1;
  });

  // Best result
  const bestResult = sortedResults[0];

  const handleSort = (key: string) => {
    setSortConfig((prev) => ({
      key,
      direction:
        prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const handleExport = () => {
    const csv = [
      [
        "Rank",
        "Parameters",
        "Sharpe Ratio",
        "Total Return (%)",
        "Max Drawdown (%)",
        "Win Rate (%)",
        "Total Trades",
      ].join(","),
      ...sortedResults.map((r) =>
        [
          r.rank,
          JSON.stringify(r.parameters),
          r.metrics.sharpe_ratio?.toFixed(2) ?? "N/A",
          r.metrics.total_return?.toFixed(2) ?? "N/A",
          r.metrics.max_drawdown?.toFixed(2) ?? "N/A",
          r.metrics.win_rate?.toFixed(2) ?? "N/A",
          r.metrics.total_trades ?? 0,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `optimization_${optimizationId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (status === "failed" || error) {
    return (
      <Card className="p-6 bg-red-900/10 border-red-800">
        <div className="flex items-center gap-2 text-red-400">
          <TrendingDown className="w-5 h-5" />
          <h3 className="font-semibold">优化失败</h3>
        </div>
        <p className="text-red-300 mt-2">{error || "未知错误"}</p>
      </Card>
    );
  }

  if (status === "pending" || results.length === 0) {
    return (
      <Card className="p-8 bg-slate-900/50 border-slate-800">
        <div className="text-center text-slate-500">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>
            {status === "pending"
              ? "等待优化开始..."
              : "暂无优化结果"}
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Best Result Highlight */}
      {bestResult && (
        <Card className="p-4 bg-gradient-to-r from-sky-900/30 to-emerald-900/30 border-sky-700">
          <div className="flex items-center gap-2 mb-3">
            <Trophy className="w-5 h-5 text-yellow-400" />
            <h3 className="font-semibold text-slate-200">最佳参数组合</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="夏普比率"
              value={bestResult.metrics.sharpe_ratio}
              format="number"
              icon={<TrendingUp className="w-4 h-4" />}
              highlight
            />
            <MetricCard
              label="总收益率"
              value={bestResult.metrics.total_return}
              format="percent"
              icon={<TrendingUp className="w-4 h-4" />}
              highlight
            />
            <MetricCard
              label="最大回撤"
              value={bestResult.metrics.max_drawdown}
              format="percent"
              icon={<TrendingDown className="w-4 h-4" />}
              highlight
            />
            <MetricCard
              label="胜率"
              value={bestResult.metrics.win_rate}
              format="percent"
              icon={<Activity className="w-4 h-4" />}
              highlight
            />
          </div>
          <div className="mt-3 p-3 bg-slate-800/50 rounded-lg">
            <div className="text-xs text-slate-500 mb-1">参数值</div>
            <div className="font-mono text-sm text-sky-300">
              {formatParameters(bestResult.parameters)}
            </div>
          </div>
        </Card>
      )}

      {/* Results Table */}
      <Card className="bg-slate-900/50 border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-700 flex items-center justify-between">
          <h3 className="font-semibold text-slate-300">
            参数组合结果 ({sortedResults.length})
          </h3>
          <Button
            onClick={handleExport}
            size="sm"
            variant="outline"
            className="text-slate-400 border-slate-700"
          >
            <Download className="w-4 h-4 mr-1" />
            导出CSV
          </Button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <TableHeader
                  label="排名"
                  sortKey="rank"
                  currentSort={sortConfig}
                  onSort={handleSort}
                />
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">
                  参数
                </th>
                <TableHeader
                  label="夏普比率"
                  sortKey="sharpe_ratio"
                  currentSort={sortConfig}
                  onSort={handleSort}
                />
                <TableHeader
                  label="收益率"
                  sortKey="total_return"
                  currentSort={sortConfig}
                  onSort={handleSort}
                />
                <TableHeader
                  label="最大回撤"
                  sortKey="max_drawdown"
                  currentSort={sortConfig}
                  onSort={handleSort}
                />
                <TableHeader
                  label="胜率"
                  sortKey="win_rate"
                  currentSort={sortConfig}
                  onSort={handleSort}
                />
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-400">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {sortedResults.map((result) => (
                <tr
                  key={result.combination_id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                        result.rank === 1
                          ? "bg-yellow-500/20 text-yellow-400"
                          : result.rank === 2
                          ? "bg-slate-400/20 text-slate-300"
                          : result.rank === 3
                          ? "bg-orange-500/20 text-orange-400"
                          : "bg-slate-700/50 text-slate-400"
                      }`}
                    >
                      {result.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs text-slate-400">
                      {formatParameters(result.parameters)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <MetricValue
                      value={result.metrics.sharpe_ratio}
                      format="number"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <MetricValue
                      value={result.metrics.total_return}
                      format="percent"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <MetricValue
                      value={result.metrics.max_drawdown}
                      format="percent"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <MetricValue
                      value={result.metrics.win_rate}
                      format="percent"
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    {onSelectResult && (
                      <Button
                        onClick={() => onSelectResult(result)}
                        size="sm"
                        variant="ghost"
                        className="text-sky-400 hover:text-sky-300"
                      >
                        查看详情
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

// Helper Components
interface TableHeaderProps {
  label: string;
  sortKey: string;
  currentSort: { key: string; direction: "asc" | "desc" };
  onSort: (key: string) => void;
}

function TableHeader({
  label,
  sortKey,
  currentSort,
  onSort,
}: TableHeaderProps) {
  const isActive = currentSort.key === sortKey;
  return (
    <th className="px-4 py-3 text-left text-xs font-medium">
      <button
        onClick={() => onSort(sortKey)}
        className={`flex items-center gap-1 hover:text-slate-300 transition-colors ${
          isActive ? "text-sky-400" : "text-slate-400"
        }`}
      >
        {label}
        {isActive && (
          <span className="text-xs">
            {currentSort.direction === "asc" ? "↑" : "↓"}
          </span>
        )}
      </button>
    </th>
  );
}

interface MetricCardProps {
  label: string;
  value?: number;
  format: "number" | "percent";
  icon?: React.ReactNode;
  highlight?: boolean;
}

function MetricCard({ label, value, format, icon, highlight }: MetricCardProps) {
  const formattedValue = formatValue(value, format);
  const colorClass = getValueColorClass(value, format, highlight);

  return (
    <div>
      <div className="flex items-center gap-1 text-xs text-slate-500">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`text-lg font-semibold ${colorClass}`}>
        {formattedValue}
      </div>
    </div>
  );
}

function MetricValue({
  value,
  format,
}: {
  value?: number;
  format: "number" | "percent";
}) {
  const formattedValue = formatValue(value, format);
  const colorClass = getValueColorClass(value, format, false);

  return <span className={colorClass}>{formattedValue}</span>;
}

// Helper Functions
function getSortValue(result: ScreeningResult, key: string): number {
  switch (key) {
    case "rank":
      return result.rank;
    case "sharpe_ratio":
      return result.metrics.sharpe_ratio ?? -Infinity;
    case "total_return":
      return result.metrics.total_return ?? -Infinity;
    case "max_drawdown":
      return result.metrics.max_drawdown ?? -Infinity;
    case "win_rate":
      return result.metrics.win_rate ?? -Infinity;
    default:
      return 0;
  }
}

function formatValue(value?: number, format: "number" | "percent"): string {
  if (value === undefined || value === null) return "N/A";
  if (format === "percent") {
    return `${value.toFixed(2)}%`;
  }
  return value.toFixed(2);
}

function getValueColorClass(
  value?: number,
  format: "number" | "percent",
  highlight?: boolean
): string {
  if (value === undefined || value === null) return "text-slate-500";

  if (format === "percent") {
    if (value > 0) return highlight ? "text-emerald-400" : "text-emerald-300";
    if (value < 0) return "text-red-400";
    return "text-slate-400";
  }

  // For sharpe ratio and other metrics
  if (value > 1) return highlight ? "text-emerald-400" : "text-emerald-300";
  if (value > 0.5) return "text-sky-400";
  if (value < 0) return "text-red-400";
  return "text-slate-400";
}

function formatParameters(params: Record<string, number>): string {
  return Object.entries(params)
    .map(([key, value]) => `${key}=${value}`)
    .join(", ");
}
