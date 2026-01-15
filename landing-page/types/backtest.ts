/**
 * Backtest result type definitions
 *
 * Types for backtest results returned by the API
 */

/**
 * DataFrame serialization format (from Python pandas)
 * When pandas DataFrames are serialized via CustomEncoder in backtest_state_service.py
 */
export interface SerializedDataFrame {
  __type__: "DataFrame";
  __attrs__: Record<string, unknown>;
  __data__: Record<string, unknown>[];
}

/**
 * Check if value is a serialized DataFrame
 */
export function isSerializedDataFrame(value: unknown): value is SerializedDataFrame {
  return (
    typeof value === "object" &&
    value !== null &&
    "__type__" in value &&
    (value as { __type__: string }).__type__ === "DataFrame"
  );
}

/**
 * Equity record (净值记录)
 */
export interface EquityRecord {
  timestamp: string;
  price?: number;
  position: number;
  cash: number;
  total_value: number;
  positions_value?: number;
  position_cost?: number;
}

/**
 * Trade record (交易记录)
 */
export interface Trade {
  timestamp: string;
  symbol: string;
  type: "BUY" | "SELL" | "OPEN" | "CLOSE";
  price: number;
  quantity: number;
  amount: number;
  profit?: number;
  profit_pct?: number;
}

/**
 * Backtest summary (回测摘要)
 */
export interface BacktestSummary {
  initial_capital: number;
  final_capital: number;
  total_trades: number;
  win_rate: number;
  max_drawdown: number;
  total_return: number;
  current_drawdown: number;
  position_strategy_type: string;
}

/**
 * Performance metrics (性能指标)
 */
export interface PerformanceMetrics {
  total_return_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  volatility?: number;
  annual_return?: number;
}

/**
 * Position strategy config (仓位策略配置)
 */
export interface PositionStrategyConfig {
  type: string;
  params: Record<string, unknown>;
}

/**
 * Signal data (信号数据)
 */
export interface SignalData {
  timestamp: string;
  signal: number;
  signal_type: "BUY" | "SELL" | "HEDGE" | "REBALANCE";
  price: number;
  symbol: string;
}

/**
 * Combined equity data (组合净值数据 - 多符号模式)
 */
export interface CombinedEquity {
  timestamp: string;
  total_value: number;
  [symbol: string]: number | string; // 动态符号列
}

/**
 * Full backtest results (完整回测结果)
 */
export interface BacktestResults {
  // Summary metrics
  summary: BacktestSummary;

  // Trade records (array or serialized DataFrame)
  trades: Trade[] | SerializedDataFrame;

  // Equity records (array or serialized DataFrame)
  equity_records: EquityRecord[] | SerializedDataFrame;

  // Combined equity (multi-symbol mode)
  combined_equity?: CombinedEquity[] | SerializedDataFrame;

  // Performance metrics
  performance_metrics: PerformanceMetrics;

  // Position strategy config
  position_strategy_config: PositionStrategyConfig;

  // Price data (serialized DataFrame)
  price_data?: SerializedDataFrame;

  // Signals data (array or serialized DataFrame)
  signals?: SignalData[] | SerializedDataFrame;

  // Debug data (策略调试数据)
  debug_data?: Record<string, SerializedDataFrame>;

  // Errors
  errors: unknown[];

  // Default strategy (多符号模式)
  default_strategy?: Record<string, unknown>;
}

/**
 * API response wrapper
 */
export interface BacktestResultsResponse {
  success: boolean;
  message: string;
  data?: BacktestResults;
}

/**
 * Helper to convert serialized DataFrame to array
 */
export function dataframeToArray<T extends Record<string, unknown>>(
  data: T[] | SerializedDataFrame | undefined
): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (isSerializedDataFrame(data)) return data.__data__ as T[];
  return [];
}

/**
 * Helper to get timestamp from various formats
 */
export function getTimestamp(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return new Date(value).toISOString();
  if (value instanceof Date) return value.toISOString();
  return "";
}
