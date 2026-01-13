"use client";

/**
 * Backtest Configuration Page
 *
 * Configure and run backtests with the QuantOL platform.
 */

import { useState, useEffect } from "react";
import { useRequireAuth } from "@/lib/store";
import { useApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Link from "next/link";

// Types
interface BacktestConfig {
  // Date config
  startDate: string;
  endDate: string;
  frequency: string;

  // Stock selection
  symbols: string[];

  // Basic config
  initialCapital: number;
  commissionRate: number;
  slippage: number;
  minLotSize: number;

  // Position strategy
  positionStrategy: "fixed_percent" | "kelly" | "martingale";
  positionParams: Record<string, number>;
}

interface Stock {
  code: string;
  name: string;
}

const defaultConfig: BacktestConfig = {
  startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split("T")[0],
  endDate: new Date().toISOString().split("T")[0],
  frequency: "d",
  symbols: [],
  initialCapital: 1000000,
  commissionRate: 0.0005,
  slippage: 0.0,
  minLotSize: 100,
  positionStrategy: "fixed_percent",
  positionParams: { percent: 0.1 },
};

// Frequency options
const frequencyOptions = [
  { value: "5", label: "5分钟" },
  { value: "15", label: "15分钟" },
  { value: "30", label: "30分钟" },
  { value: "60", label: "60分钟" },
  { value: "120", label: "120分钟" },
  { value: "d", label: "日线" },
  { value: "w", label: "周线" },
  { value: "m", label: "月线" },
];

// Position strategy options
const positionStrategyOptions = [
  { value: "fixed_percent", label: "固定比例" },
  { value: "kelly", label: "凯利公式" },
  { value: "martingale", label: "马丁格尔" },
];

export default function BacktestPage() {
  const { user, isLoading, token } = useRequireAuth();
  const { getStocks, runBacktest } = useApi();

  const [config, setConfig] = useState<BacktestConfig>(defaultConfig);
  const [isRunning, setIsRunning] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [backtestId, setBacktestId] = useState<string | null>(null);

  // Stock selection state
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [stockSearch, setStockSearch] = useState("");
  const [isLoadingStocks, setIsLoadingStocks] = useState(false);
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set());

  // Load stocks on mount
  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    setIsLoadingStocks(true);
    try {
      const response = await getStocks();
      if (response.success && response.data) {
        setStocks(response.data);
      }
    } catch (error) {
      console.error("Failed to load stocks:", error);
    } finally {
      setIsLoadingStocks(false);
    }
  };

  const handleStockToggle = (code: string) => {
    const newSelected = new Set(selectedStocks);
    if (newSelected.has(code)) {
      newSelected.delete(code);
    } else {
      newSelected.add(code);
    }
    setSelectedStocks(newSelected);
    setConfig({ ...config, symbols: Array.from(newSelected) });
  };

  const handleRunBacktest = async () => {
    if (config.symbols.length === 0) {
      alert("请至少选择一只股票");
      return;
    }

    setIsRunning(true);

    try {
      // Format dates for backend (YYYYMMDD)
      const formatDate = (dateStr: string) => {
        const [year, month, day] = dateStr.split("-");
        return `${year}${month}${day}`;
      };

      const response = await runBacktest({
        start_date: formatDate(config.startDate),
        end_date: formatDate(config.endDate),
        frequency: config.frequency,
        symbols: config.symbols,
        initial_capital: config.initialCapital,
        commission_rate: config.commissionRate,
        slippage: config.slippage,
        min_lot_size: config.minLotSize,
        position_strategy: config.positionStrategy,
        position_params: config.positionParams,
      });

      if (response.success && response.data?.backtest_id) {
        setBacktestId(response.data.backtest_id);
        setShowResults(true);
      }
    } catch (error) {
      console.error("Backtest failed:", error);
      alert("回测启动失败: " + (error instanceof Error ? error.message : "未知错误"));
    } finally {
      setIsRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) return null;

  // Filter stocks based on search
  const filteredStocks = stocks.filter(
    (stock) =>
      stock.code.toLowerCase().includes(stockSearch.toLowerCase()) ||
      stock.name.toLowerCase().includes(stockSearch.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/backtest"
                className="text-white hover:text-sky-400 transition-colors"
              >
                Backtesting
              </Link>
              <Link
                href="/trading"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                Trading
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">{user.username}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => (window.location.href = "/login")}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Backtesting</h1>
          <p className="text-slate-400">
            Configure and run backtests to validate your trading strategies.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1 space-y-6">
            {/* Stock Selection */}
            <Card className="p-6 bg-slate-900/50 border-slate-800">
              <h3 className="text-lg font-semibold mb-4">选择交易标的</h3>

              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="搜索股票代码或名称..."
                  value={stockSearch}
                  onChange={(e) => setStockSearch(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500"
                />

                <div className="max-h-48 overflow-y-auto space-y-1">
                  {isLoadingStocks ? (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500" />
                    </div>
                  ) : (
                    filteredStocks.slice(0, 50).map((stock) => (
                      <label
                        key={stock.code}
                        className="flex items-center gap-2 p-2 hover:bg-slate-800 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedStocks.has(stock.code)}
                          onChange={() => handleStockToggle(stock.code)}
                          className="rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
                        />
                        <span className="text-sm text-slate-300">{stock.code}</span>
                        <span className="text-xs text-slate-500 truncate">{stock.name}</span>
                      </label>
                    ))
                  )}
                </div>

                <p className="text-xs text-slate-500">
                  已选择 {selectedStocks.size} 只股票
                </p>
              </div>
            </Card>

            {/* Date & Frequency */}
            <Card className="p-6 bg-slate-900/50 border-slate-800">
              <h3 className="text-lg font-semibold mb-4">日期与频率</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    开始日期
                  </label>
                  <input
                    type="date"
                    value={config.startDate}
                    onChange={(e) =>
                      setConfig({ ...config, startDate: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    结束日期
                  </label>
                  <input
                    type="date"
                    value={config.endDate}
                    onChange={(e) =>
                      setConfig({ ...config, endDate: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    数据频率
                  </label>
                  <select
                    value={config.frequency}
                    onChange={(e) =>
                      setConfig({ ...config, frequency: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                  >
                    {frequencyOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </Card>

            {/* Basic Configuration */}
            <Card className="p-6 bg-slate-900/50 border-slate-800">
              <h3 className="text-lg font-semibold mb-4">基础配置</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    初始资金
                  </label>
                  <input
                    type="number"
                    value={config.initialCapital}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        initialCapital: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                    min="1000"
                    step="10000"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">
                      手续费率
                    </label>
                    <input
                      type="number"
                      value={config.commissionRate}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          commissionRate: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                      min="0"
                      max="0.1"
                      step="0.0001"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-400 mb-2">
                      滑点率
                    </label>
                    <input
                      type="number"
                      value={config.slippage}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          slippage: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                      min="0"
                      max="0.1"
                      step="0.0001"
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* Position Strategy */}
            <Card className="p-6 bg-slate-900/50 border-slate-800">
              <h3 className="text-lg font-semibold mb-4">仓位策略</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    策略类型
                  </label>
                  <select
                    value={config.positionStrategy}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        positionStrategy: e.target.value as any,
                        positionParams:
                          e.target.value === "fixed_percent"
                            ? { percent: 0.1 }
                            : e.target.value === "kelly"
                              ? {
                                  win_rate: 0.6,
                                  win_loss_ratio: 1.5,
                                  max_percent: 0.25,
                                }
                              : {
                                  multiplier: 2.0,
                                  max_doubles: 5,
                                  base_percent: 0.05,
                                },
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                  >
                    {positionStrategyOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {config.positionStrategy === "fixed_percent" && (
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">
                      仓位比例
                    </label>
                    <input
                      type="number"
                      value={(config.positionParams.percent || 0.1) * 100}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          positionParams: {
                            percent: Number(e.target.value) / 100,
                          },
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                      min="0"
                      max="100"
                      step="0.01"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      {((config.positionParams.percent || 0.1) * 100).toFixed(2)}%
                    </p>
                  </div>
                )}

                {config.positionStrategy === "kelly" && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">
                        预估胜率
                      </label>
                      <input
                        type="number"
                        value={(config.positionParams.win_rate || 0.6) * 100}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            positionParams: {
                              ...config.positionParams,
                              win_rate: Number(e.target.value) / 100,
                            },
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="0"
                        max="100"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">
                        预估盈亏比
                      </label>
                      <input
                        type="number"
                        value={config.positionParams.win_loss_ratio || 1.5}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            positionParams: {
                              ...config.positionParams,
                              win_loss_ratio: Number(e.target.value),
                            },
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="0.1"
                        max="5"
                        step="0.1"
                      />
                    </div>
                  </div>
                )}

                {config.positionStrategy === "martingale" && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">
                        基础仓位比例
                      </label>
                      <input
                        type="number"
                        value={(config.positionParams.base_percent || 0.05) * 100}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            positionParams: {
                              ...config.positionParams,
                              base_percent: Number(e.target.value) / 100,
                            },
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="0"
                        max="20"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-slate-400 mb-1">
                        加倍系数
                      </label>
                      <input
                        type="number"
                        value={config.positionParams.multiplier || 2.0}
                        onChange={(e) =>
                          setConfig({
                            ...config,
                            positionParams: {
                              ...config.positionParams,
                              multiplier: Number(e.target.value),
                            },
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="1"
                        max="5"
                        step="0.1"
                      />
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Button
                onClick={handleRunBacktest}
                disabled={isRunning || config.symbols.length === 0}
                className="flex-1 bg-sky-600 hover:bg-sky-700 text-white"
              >
                {isRunning ? "运行中..." : "运行回测"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setConfig(defaultConfig);
                  setSelectedStocks(new Set());
                }}
                className="border-slate-700 text-slate-300 hover:bg-slate-800"
              >
                重置
              </Button>
            </div>
          </div>

          {/* Results / Chart Area */}
          <div className="lg:col-span-2">
            {showResults && backtestId ? (
              <Card className="p-6 bg-slate-900/50 border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">回测结果</h3>
                  <span className="text-sm text-slate-400">ID: {backtestId}</span>
                </div>
                {/* Embed Streamlit chart with backtest results */}
                <div className="bg-slate-800 rounded-lg overflow-hidden" style={{ height: "600px" }}>
                  <iframe
                    src={`${typeof window !== "undefined" ? window.location.origin : ""}?headless=true&chart=backtest&backtest=${backtestId}&token=${token}`}
                    className="w-full h-full border-0"
                    title="Backtest Results"
                    sandbox="allow-scripts allow-same-origin"
                  />
                </div>
              </Card>
            ) : (
              <Card className="p-6 bg-slate-900/50 border-slate-800">
                <div className="aspect-video bg-slate-800/50 rounded flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-slate-400 mb-2">
                      配置回测参数后点击"运行回测"
                    </p>
                    <p className="text-sm text-slate-500">
                      结果将在此处显示
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
