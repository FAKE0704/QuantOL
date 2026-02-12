"use client";

/**
 * Backtest History Page
 *
 * View and manage historical backtest results.
 */

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useRequireAuth } from "@/lib/store";
import { useApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Link } from "@/lib/routing";
import { BacktestResultsView } from "@/components/backtest/BacktestResultsView";
import { ThemeSwitcher } from "@/components/layout/ThemeSwitcher";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";

interface BacktestHistoryItem {
  backtest_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  total_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  progress?: number;
  current_time?: string;
}

export default function BacktestHistoryPage() {
  const t = useTranslations('backtest');
  const { user, isLoading } = useRequireAuth();
  const {
    getBacktestHistory,
    getBacktestDetail,
    deleteBacktest,
  } = useApi();

  const [history, setHistory] = useState<BacktestHistoryItem[]>([]);
  const [selectedBacktestId, setSelectedBacktestId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showResults, setShowResults] = useState(false);

  // Load backtest history
  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await getBacktestHistory(10, statusFilter || undefined);
      if (response.success && response.data) {
        setHistory(response.data);
      }
    } catch (error) {
      console.error("Failed to load backtest history:", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [statusFilter]);

  // Poll for running tasks every 2 seconds
  useEffect(() => {
    const runningTasks = history.filter(item => item.status === 'running' || item.status === 'pending');
    if (runningTasks.length === 0) return;

    const interval = setInterval(async () => {
      try {
        const response = await getBacktestHistory(10, statusFilter || undefined);
        if (response.success && response.data) {
          setHistory(response.data);
        }
      } catch (error) {
        console.error("Failed to refresh backtest history:", error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [history, statusFilter]);

  const handleViewResults = async (backtestId: string) => {
    setSelectedBacktestId(backtestId);
    setShowResults(true);
  };

  const handleBackToHistory = () => {
    setShowResults(false);
    setSelectedBacktestId(null);
  };

  const handleDelete = async (backtestId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("确定要删除此回测记录吗？")) {
      return;
    }

    try {
      const response = await deleteBacktest(backtestId);
      if (response.success) {
        await loadHistory();
      } else {
        alert("删除失败: " + response.message);
      }
    } catch (error) {
      console.error("Failed to delete backtest:", error);
      alert("删除失败: " + (error instanceof Error ? error.message : "未知错误"));
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("zh-CN");
  };

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return "-";
    return (value * 100).toFixed(2) + "%";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-emerald-400";
      case "running":
        return "text-blue-400";
      case "failed":
        return "text-red-400";
      case "pending":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成";
      case "running":
        return "运行中";
      case "failed":
        return "失败";
      case "pending":
        return "等待中";
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Show results view
  if (showResults && selectedBacktestId) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/backtest" className="text-muted-foreground hover:text-foreground">
                ← 返回回测
              </Link>
              <h1 className="text-xl font-semibold">回测结果</h1>
            </div>
            <div className="flex items-center gap-4">
              <ThemeSwitcher />
              <UserAccountMenu />
            </div>
          </div>
        </header>

        {/* Results */}
        <div className="container mx-auto px-4 py-6">
          <Button
            onClick={handleBackToHistory}
            variant="outline"
            className="mb-4"
          >
            ← 返回历史记录
          </Button>
          <BacktestResultsView backtestId={selectedBacktestId} />
        </div>
      </div>
    );
  }

  // History list view
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/backtest" className="text-muted-foreground hover:text-foreground">
              ← 返回回测
            </Link>
            <h1 className="text-xl font-semibold">回测历史</h1>
          </div>
          <div className="flex items-center gap-4">
            <ThemeSwitcher />
            <UserAccountMenu />
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Filters */}
        <Card className="p-4 mb-6 bg-card/50">
          <div className="flex items-center gap-4">
            <label className="text-sm text-muted-foreground">状态筛选:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-input border border-border rounded text-foreground"
            >
              <option value="">全部</option>
              <option value="completed">已完成</option>
              <option value="running">运行中</option>
              <option value="failed">失败</option>
              <option value="pending">等待中</option>
            </select>
          </div>
        </Card>

        {/* History List */}
        {isLoadingHistory ? (
          <div className="text-center py-12 text-muted-foreground">
            加载中...
          </div>
        ) : history.length === 0 ? (
          <Card className="p-12 text-center bg-card/50">
            <p className="text-muted-foreground mb-4">
              暂无回测历史记录
            </p>
            <Link href="/backtest">
              <Button>开始回测</Button>
            </Link>
          </Card>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <Card
                key={item.backtest_id}
                className="p-4 bg-card/50 hover:bg-card/80 transition-all cursor-pointer"
                onClick={() => handleViewResults(item.backtest_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm text-muted-foreground">
                        {item.backtest_id}
                      </span>
                      <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
                        {getStatusText(item.status)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(item.created_at)}
                      </span>
                    </div>

                    {item.status === "completed" && (
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">总收益:</span>
                          <span className={`ml-2 font-medium ${
                            (item.total_return ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                          }`}>
                            {formatPercent(item.total_return)}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">夏普比率:</span>
                          <span className="ml-2 font-medium">
                            {item.sharpe_ratio?.toFixed(2) ?? "-"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">最大回撤:</span>
                          <span className="ml-2 font-medium text-red-400">
                            {formatPercent(item.max_drawdown)}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">胜率:</span>
                          <span className="ml-2 font-medium">
                            {formatPercent(item.win_rate)}
                          </span>
                        </div>
                      </div>
                    )}

                    {(item.status === "running" || item.status === "pending") && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                          <span>进度</span>
                          <span>{item.progress?.toFixed(1) ?? 0}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-blue-500 h-full transition-all duration-300 ease-out"
                            style={{ width: `${item.progress ?? 0}%` }}
                          />
                        </div>
                        {item.current_time && (
                          <div className="text-xs text-muted-foreground mt-1">
                            当前时间: {item.current_time}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewResults(item.backtest_id);
                      }}
                    >
                      {item.status === "completed" ? "查看详情" : "查看进度"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-400 hover:text-red-300"
                      onClick={(e) => handleDelete(item.backtest_id, e)}
                    >
                      删除
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
