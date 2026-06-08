/**
 * Optimization Types
 *
 * Types for parameter optimization and rolling window analysis
 */

/**
 * Parameter range configuration
 * Defines the search space for a single parameter
 */
export interface ParameterRange {
  /** Indicator name (e.g., "SMA", "RSI", "MACD") */
  indicator: string;
  /** Parameter name (e.g., "fast_window", "slow_window", "period") */
  parameter_name: string;
  /** Range type: "range" for min/max/step, "custom" for explicit values */
  type: "range" | "custom";
  /** Minimum value (only for type="range") */
  min?: number;
  /** Maximum value (only for type="range") */
  max?: number;
  /** Step size (only for type="range") */
  step?: number;
  /** Custom list of values (only for type="custom") */
  values?: number[];
}

/**
 * Rule template with variable placeholders
 * Example: "SMA(close, {fast_window}) > SMA(close, {slow_window})"
 */
export interface RuleTemplate {
  /** Template unique identifier */
  template_id: string;
  /** Human-readable name */
  name: string;
  /** Description of the strategy */
  description?: string;

  /** Rule templates with variable placeholders */
  open_rule_template?: string;
  close_rule_template?: string;
  buy_rule_template?: string;
  sell_rule_template?: string;

  /** Variable definitions */
  variables: Record<string, {
    type: "int" | "float";
    default_value: number;
    description: string;
  }>;
}

/**
 * Optimization configuration
 */
export interface OptimizationConfig {
  /** Parameter search spaces */
  parameter_ranges: ParameterRange[];

  /** Scan method: "random" for random search */
  scan_method: "random";

  /** Number of random samples to generate */
  random_samples: number;

  /** Screening period for initial evaluation */
  screening_period: {
    start_date: string;
    end_date: string;
  };

  /** Metric to use for ranking results */
  screening_metric: "sharpe_ratio" | "total_return" | "max_drawdown";

  /** Number of top candidates to return */
  top_n_candidates: number;

  /** Performance thresholds (optional) */
  performance_thresholds?: {
    min_sharpe?: number;
    max_drawdown_limit?: number;
    min_win_rate?: number;
  };
}

/**
 * Single parameter combination
 */
export interface ParameterCombination {
  /** Combination unique identifier */
  combination_id: string;
  /** Parameter values */
  parameters: Record<string, number>;
}

/**
 * Screening result for a single parameter combination
 */
export interface ScreeningResult {
  /** Combination identifier */
  combination_id: string;
  /** Parameter values */
  parameters: Record<string, number>;
  /** Performance metrics */
  metrics: {
    sharpe_ratio: number;
    total_return: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
  };
  /** Rank based on screening metric */
  rank: number;
}

/**
 * Optimization result
 */
export interface OptimizationResult {
  /** Optimization task identifier */
  optimization_id: string;
  /** Task status */
  status: "pending" | "screening" | "completed" | "failed";

  /** Screening results (populated as optimization progresses) */
  screening_results?: ScreeningResult[];

  /** Best parameters (available after completion) */
  best_parameters?: Record<string, number>;
  /** Best metrics (available after completion) */
  best_metrics?: {
    sharpe_ratio: number;
    total_return: number;
    max_drawdown: number;
    win_rate: number;
  };

  /** Progress information */
  progress?: {
    current_stage: string;
    current_step: number;
    total_steps: number;
    percentage: number;
  };

  /** Error message (if failed) */
  error?: string;
}

/**
 * Request to start optimization
 */
export interface OptimizationRequest {
  /** Base backtest configuration */
  base_config: {
    start_date: string;
    end_date: string;
    frequency: string;
    symbols: string[];
    initial_capital: number;
    commission_rate: number;
    slippage: number;
    position_strategy: string;
    position_params: Record<string, number>;
  };

  /** Rule templates to optimize */
  rule_templates: {
    open_rule_template?: string;
    close_rule_template?: string;
    buy_rule_template?: string;
    sell_rule_template?: string;
  };

  /** Optimization configuration */
  optimization_config: OptimizationConfig;
}

/**
 * Response when starting optimization
 */
export interface OptimizationResponse {
  /** Optimization task identifier */
  optimization_id: string;
  /** Initial status */
  status: string;
  /** Message */
  message: string;
}

/**
 * Optimization progress update (for WebSocket)
 */
export interface OptimizationProgress {
  /** Optimization identifier */
  optimization_id: string;
  /** Current stage */
  stage: "screening" | "completed" | "failed";
  /** Current combination index */
  current: number;
  /** Total combinations */
  total: number;
  /** Percentage complete */
  percentage: number;
  /** Latest result (optional) */
  latest_result?: ScreeningResult;
}

/**
 * Predefined strategy templates library
 */
export const STRATEGY_TEMPLATES: Record<string, RuleTemplate> = {
  ma_crossover: {
    template_id: "ma_crossover",
    name: "Moving Average Crossover",
    description: "Classic MA crossover strategy - buy when fast MA crosses above slow MA",
    open_rule_template: "(REF(SMA(close, {fast_window}), 1) < REF(SMA(close, {slow_window}), 1)) & (SMA(close, {fast_window}) > SMA(close, {slow_window}))",
    close_rule_template: "(REF(SMA(close, {fast_window}), 1) > REF(SMA(close, {slow_window}), 1)) & (SMA(close, {fast_window}) < SMA(close, {slow_window}))",
    variables: {
      fast_window: {
        type: "int",
        default_value: 5,
        description: "Fast moving average window"
      },
      slow_window: {
        type: "int",
        default_value: 20,
        description: "Slow moving average window"
      }
    }
  },
  rsi_overbought_oversold: {
    template_id: "rsi_overbought_oversold",
    name: "RSI Overbought/Oversold",
    description: "Buy when RSI exits oversold, sell when enters overbought",
    open_rule_template: "(REF(RSI(close, {period}), 1) < {oversold_threshold}) & (RSI(close, {period}) >= {oversold_threshold})",
    close_rule_template: "(REF(RSI(close, {period}), 1) >= {overbought_threshold}) & (RSI(close, {period}) < {overbought_threshold})",
    variables: {
      period: {
        type: "int",
        default_value: 14,
        description: "RSI calculation period"
      },
      oversold_threshold: {
        type: "int",
        default_value: 30,
        description: "Oversold threshold"
      },
      overbought_threshold: {
        type: "int",
        default_value: 70,
        description: "Overbought threshold"
      }
    }
  },
  macd_crossover: {
    template_id: "macd_crossover",
    name: "MACD Crossover",
    description: "MACD signal line crossover strategy",
    open_rule_template: "MACD(close, {fast_period}, {slow_period}, {signal_period}) > MACD_SIGNAL(close, {fast_period}, {slow_period}, {signal_period})",
    close_rule_template: "MACD(close, {fast_period}, {slow_period}, {signal_period}) < MACD_SIGNAL(close, {fast_period}, {slow_period}, {signal_period})",
    variables: {
      fast_period: {
        type: "int",
        default_value: 12,
        description: "MACD fast EMA period"
      },
      slow_period: {
        type: "int",
        default_value: 26,
        description: "MACD slow EMA period"
      },
      signal_period: {
        type: "int",
        default_value: 9,
        description: "MACD signal line period"
      }
    }
  }
};
