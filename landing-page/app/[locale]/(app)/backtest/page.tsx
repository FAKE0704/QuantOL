"use client";

/**
 * Backtest Configuration Page
 *
 * Configure and run backtests with the QuantOL platform.
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslations } from "next-intl";
import { useRequireAuth } from "@/lib/store";
import { useApi, BacktestConfig as ApiBacktestConfig } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Link } from "@/lib/routing";
import { BacktestProgressBar } from "@/components/backtest/BacktestProgressBar";
import { BacktestResultsView } from "@/components/backtest/BacktestResultsView";
import { ParameterConfig } from "@/components/backtest/ParameterConfig";
import { OptimizationResults, ScreeningResult } from "@/components/backtest/OptimizationResults";
import { useBacktestWebSocket, type BacktestProgress } from "@/lib/hooks/useBacktestWebSocket";
import { ThemeSwitcher } from "@/components/layout/ThemeSwitcher";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";
import { CoffeeModal } from "@/components/layout/CoffeeModal";
import { OptimizationConfig, STRATEGY_TEMPLATES } from "@/types/optimization";

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

  // Trading strategy
  tradingStrategy: string;
  openRule: string;
  closeRule: string;
  buyRule: string;
  sellRule: string;
}

interface Stock {
  code: string;
  name: string;
}

const defaultConfig: BacktestConfig = {
  startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
    .toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" })
    .replace(/\//g, "-"),
  endDate: new Date()
    .toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" })
    .replace(/\//g, "-"),
  frequency: "d",
  symbols: [],
  initialCapital: 1000000,
  commissionRate: 0.0005,
  slippage: 0.0,
  minLotSize: 100,
  positionStrategy: "fixed_percent",
  positionParams: { percent: 0.1 },
  tradingStrategy: "monthly_investment",
  openRule: "",
  closeRule: "",
  buyRule: "",
  sellRule: "",
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

// Default strategy rules (fallback if API fails)
const fallbackDefaultStrategyRules: Record<string, { open_rule: string; close_rule: string; buy_rule: string; sell_rule: string }> = {
  monthly_investment: {
    open_rule: "",
    close_rule: "",
    buy_rule: "",
    sell_rule: "",
  },
  ma_crossover: {
    open_rule: "(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))",
    close_rule: "(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))",
    buy_rule: "",
    sell_rule: "",
  },
  macd_crossover: {
    open_rule: "MACD(close, 12, 26, 9) > MACD_SIGNAL(close, 12, 26, 9)",
    close_rule: "MACD(close, 12, 26, 9) < MACD_SIGNAL(close, 12, 26, 9)",
    buy_rule: "",
    sell_rule: "",
  },
  rsi: {
    open_rule: "(REF(RSI(close,5), 1) < 30) & (RSI(close,5) >= 30)",
    close_rule: "(REF(RSI(close,5), 1) >= 60) & (RSI(close,5) < 60)",
    buy_rule: "",
    sell_rule: "",
  },
  martingale: {
    open_rule: "(close < REF(SMA(close,5), 1)) & (close > SMA(close,5))",
    close_rule: "(close - (COST/POSITION))/(COST/POSITION) * 100 >= 5",
    buy_rule: "(close - (COST/POSITION))/(COST/POSITION) * 100 <= -5",
    sell_rule: "",
  },
  custom_strategy: {
    open_rule: "",
    close_rule: "",
    buy_rule: "",
    sell_rule: "",
  },
};

// Debounce hook for search input
function useDebounce(value: string, delay: number): string {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Collapsible Card Component
interface CollapsibleCardProps {
  id: string;
  title: string;
  activeCard: string | null;
  onCardClick: (id: string) => void;
  children: React.ReactNode;
}

function CollapsibleCard({ id, title, activeCard, onCardClick, children }: CollapsibleCardProps) {
  const isCollapsed = activeCard !== null && activeCard !== id;
  const isActive = activeCard === id;

  return (
    <Card
      className={`bg-[#FFEFD5] dark:bg-card border-border transition-all duration-300 ${
        isActive ? "ring-2 ring-sky-500/50" : ""
      } ${isCollapsed ? "cursor-pointer" : ""}`}
      onClick={() => isCollapsed && onCardClick(id)}
    >
      <div className="p-4">
        <div
          className={`flex items-center justify-between ${isCollapsed ? "cursor-pointer" : ""}`}
          onClick={() => !isCollapsed && onCardClick(id)}
        >
          <h3 className="text-lg font-semibold">{title}</h3>
          <span className={`text-muted-foreground transition-transform duration-300 ${isActive ? "rotate-180" : ""}`}>
            {isCollapsed ? "▶" : "▼"}
          </span>
        </div>
        {!isCollapsed && (
          <div className="mt-4">
            {children}
          </div>
        )}
      </div>
    </Card>
  );
}

export default function BacktestPage() {
  const t = useTranslations('backtest')
  const { user, isLoading, token, logout } = useRequireAuth();
  const {
    getStocks,
    runBacktest,
    listBacktestConfigs,
    createBacktestConfig,
    updateBacktestConfig,
    deleteBacktestConfig,
    getTradingStrategies,
    getPositionStrategies,
    validateRule,
    startOptimization,
    getOptimizationResults,
    listCustomStrategies,
    createCustomStrategy,
    getBacktestStatus,
  } = useApi();

  const [config, setConfig] = useState<BacktestConfig>(defaultConfig);
  const [isRunning, setIsRunning] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [backtestId, setBacktestId] = useState<string | null>(null);

  // Strategy types state
  const [tradingStrategyOptions, setTradingStrategyOptions] = useState<
    Array<{ value: string; label: string; default_params?: any }>
  >([]);
  const [positionStrategyOptions, setPositionStrategyOptions] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [defaultStrategyRules, setDefaultStrategyRules] = useState<
    Record<string, { open_rule: string; close_rule: string; buy_rule: string; sell_rule: string }>
  >({});
  const [isLoadingStrategies, setIsLoadingStrategies] = useState(true);

  // WebSocket进度追踪状态
  const [backtestProgress, setBacktestProgress] = useState<any>(null);
  const [showProgress, setShowProgress] = useState(false);

  // Stock selection state
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [stockSearch, setStockSearch] = useState("");
  const [isLoadingStocks, setIsLoadingStocks] = useState(false);
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set());

  // Card collapse state - track which card is currently active
  const [activeCard, setActiveCard] = useState<string | null>(null);

  // Backtest config management state
  const [savedConfigs, setSavedConfigs] = useState<ApiBacktestConfig[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<number | null>(null);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(false);
  const [configNameInput, setConfigNameInput] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Rebalance period state
  const [rebalancePeriod, setRebalancePeriod] = useState<{
    mode: 'disabled' | 'trading_days' | 'calendar_rule';
    tradingDaysInterval?: number;
    calendarFrequency?: 'weekly' | 'monthly';
    calendarDay?: number;
    minIntervalDays?: number;
    allowFirstRebalance: boolean;
  }>({ mode: 'disabled', allowFirstRebalance: true });

  // Show toast message
  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 2000);
  };

  // Max date for date inputs (today, updated periodically)
  const [maxDate, setMaxDate] = useState(() => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  });

  // Update maxDate every minute to handle midnight crossing
  useEffect(() => {
    const updateMaxDate = () => {
      const today = new Date();
      setMaxDate(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`);
    };

    const interval = setInterval(updateMaxDate, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Rule validation state
  const [ruleValidation, setRuleValidation] = useState<Record<string, { valid: boolean; error: string | null }>>({});

  // Optimization state
  const [showOptimization, setShowOptimization] = useState(false);
  const [optimizationConfig, setOptimizationConfig] = useState<OptimizationConfig>({
    parameter_ranges: [],
    scan_method: "random",
    random_samples: 50,
    screening_period: {
      start_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0].replace(/-/g, ""),
      end_date: new Date().toISOString().split("T")[0].replace(/-/g, ""),
    },
    screening_metric: "sharpe_ratio",
    top_n_candidates: 5,
  });
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [optimizationId, setOptimizationId] = useState<string>("");
  const [optimizationResults, setOptimizationResults] = useState<ScreeningResult[]>([]);
  const [optimizationStatus, setOptimizationStatus] = useState<"pending" | "screening" | "completed" | "failed">("pending");
  const [optimizationError, setOptimizationError] = useState<string>();

  // Debounced rule validation
  const validateRuleDebounced = useCallback(
    (ruleKey: string, ruleValue: string) => {
      if (!ruleValue.trim()) {
        setRuleValidation(prev => ({ ...prev, [ruleKey]: { valid: true, error: null } }));
        return;
      }

      // Debounce validation with 500ms delay
      const timer = setTimeout(async () => {
        try {
          const response = await validateRule(ruleValue);
          // Handle both wrapped and unwrapped response formats
          const validationData = response.data || response;
          if (validationData && typeof validationData.valid === 'boolean') {
            setRuleValidation(prev => ({ ...prev, [ruleKey]: { valid: validationData.valid, error: validationData.error } }));
          }
        } catch (error) {
          // Silently fail on validation errors
        }
      }, 500);

      return () => clearTimeout(timer);
    },
    [validateRule]
  );

  // Debounce search input
  const debouncedSearch = useDebounce(stockSearch, 500);

  // Load strategy types on mount
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const [tradingRes, positionRes] = await Promise.all([
          getTradingStrategies(),
          getPositionStrategies(),
        ]);

        if (tradingRes.success && tradingRes.data) {
          setTradingStrategyOptions(tradingRes.data);

          const rules: Record<string, any> = {};
          tradingRes.data.forEach((strategy) => {
            if (strategy.default_params) {
              rules[strategy.value] = {
                open_rule: strategy.default_params.open_rule || '',
                close_rule: strategy.default_params.close_rule || '',
                buy_rule: strategy.default_params.buy_rule || '',
                sell_rule: strategy.default_params.sell_rule || '',
              };
            }
          });
          // If no default_params from API, use fallback
          if (Object.keys(rules).length === 0) {
            setDefaultStrategyRules(fallbackDefaultStrategyRules);
          } else {
            setDefaultStrategyRules(rules);
          }
        }

        if (positionRes.success && positionRes.data) {
          setPositionStrategyOptions(positionRes.data);
        }
      } catch (error) {
        console.error('Failed to load strategies:', error);
        // Fallback to hardcoded options
        setTradingStrategyOptions([
          { value: 'monthly_investment', label: '月定投' },
          { value: 'ma_crossover', label: '移动平均线交叉' },
          { value: 'macd_crossover', label: 'MACD交叉' },
          { value: 'rsi', label: 'RSI超买超卖' },
          { value: 'martingale', label: 'Martingale' },
          { value: 'custom_strategy', label: '自定义策略' },
        ]);
        setPositionStrategyOptions([
          { value: 'fixed_percent', label: '固定比例' },
          { value: 'kelly', label: '凯利公式' },
          { value: 'martingale', label: '马丁格尔' },
        ]);
        setDefaultStrategyRules(fallbackDefaultStrategyRules);
      } finally {
        setIsLoadingStrategies(false);
      }
    };

    loadStrategies();
  }, []);

  // Search stocks when debounced input changes
  useEffect(() => {
    if (debouncedSearch.length >= 1) {
      searchStocks(debouncedSearch);
    } else {
      setStocks([]);
    }
  }, [debouncedSearch]);

  const searchStocks = async (search: string) => {
    setIsLoadingStocks(true);
    try {
      const response = await getStocks(search, 100);
      if (response.success && response.data) {
        setStocks(response.data);
      }
    } catch (error) {
      console.error("Failed to search stocks:", error);
    } finally {
      setIsLoadingStocks(false);
    }
  };

  // Strategy rules management
  const [customStrategies, setCustomStrategies] = useState<Record<string, { label: string; rules: { open_rule: string; close_rule: string; buy_rule: string; sell_rule: string } }>>({});
  const [isLoadingCustomStrategies, setIsLoadingCustomStrategies] = useState(false);

  // Load custom strategies from server on mount
  useEffect(() => {
    const loadCustomStrategies = async () => {
      setIsLoadingCustomStrategies(true);
      try {
        const response = await listCustomStrategies();
        if (response.success && response.data) {
          const strategies: typeof customStrategies = {};
          for (const strategy of response.data) {
            strategies[strategy.strategy_key] = {
              label: strategy.label,
              rules: {
                open_rule: strategy.open_rule || "",
                close_rule: strategy.close_rule || "",
                buy_rule: strategy.buy_rule || "",
                sell_rule: strategy.sell_rule || "",
              },
            };
          }
          setCustomStrategies(strategies);
        }
      } catch (error) {
        console.error("Failed to load custom strategies:", error);
      } finally {
        setIsLoadingCustomStrategies(false);
      }
    };

    loadCustomStrategies();
  }, []);

  // Save custom strategy to server
  const saveCustomStrategy = async (strategyKey: string, label: string, rules: { open_rule: string; close_rule: string; buy_rule: string; sell_rule: string }) => {
    try {
      const response = await createCustomStrategy({
        strategy_key: strategyKey,
        label,
        open_rule: rules.open_rule,
        close_rule: rules.close_rule,
        buy_rule: rules.buy_rule,
        sell_rule: rules.sell_rule,
      });

      if (response.success) {
        // Update local state
        setCustomStrategies(prev => ({
          ...prev,
          [strategyKey]: { label, rules },
        }));
        return true;
      }
      return false;
    } catch (error) {
      console.error("Failed to save custom strategy:", error);
      return false;
    }
  };

  // Sync all custom strategies to server (called when needed)
  const syncCustomStrategies = async () => {
    const response = await listCustomStrategies();
    if (response.success && response.data) {
      const strategies: typeof customStrategies = {};
      for (const strategy of response.data) {
        strategies[strategy.strategy_key] = {
          label: strategy.label,
          rules: {
            open_rule: strategy.open_rule || "",
            close_rule: strategy.close_rule || "",
            buy_rule: strategy.buy_rule || "",
            sell_rule: strategy.sell_rule || "",
          },
        };
      }
      setCustomStrategies(strategies);
    }
  };

  // Get rules for a strategy (from custom strategies or defaults)
  const getStrategyRules = (strategyValue: string) => {
    // Check custom strategies first (by value/key)
    if (customStrategies[strategyValue]) {
      return customStrategies[strategyValue].rules;
    }
    // Also check by label for backward compatibility
    const customStrategyByLabel = Object.values(customStrategies).find(s => s.label === strategyValue);
    if (customStrategyByLabel) {
      return customStrategyByLabel.rules;
    }
    // Check default strategies
    const defaultOption = tradingStrategyOptions.find(o => o.label === strategyValue || o.value === strategyValue);
    if (defaultOption) {
      return defaultStrategyRules[defaultOption.value] || defaultStrategyRules.custom_strategy;
    }
    return defaultStrategyRules.custom_strategy;
  };

  // Auto-fill rules when strategy type changes
  useEffect(() => {
    // Get the current option from all strategy options (default + custom)
    const currentOption = getAllStrategyOptions().find(o => o.value === config.tradingStrategy);
    if (currentOption) {
      const rules = getStrategyRules(config.tradingStrategy);
      // Only auto-fill if current rules are empty
      if (!config.openRule && !config.closeRule && !config.buyRule && !config.sellRule) {
        setConfig({
          ...config,
          openRule: rules.open_rule,
          closeRule: rules.close_rule,
          buyRule: rules.buy_rule,
          sellRule: rules.sell_rule,
        });
      }
    }
  }, [config.tradingStrategy]);

  // Handle saving current rules to the selected strategy
  const handleSaveToStrategy = async () => {
    const currentOption = getAllStrategyOptions().find(o => o.value === config.tradingStrategy);
    if (!currentOption) return;

    const rules = {
      open_rule: config.openRule,
      close_rule: config.closeRule,
      buy_rule: config.buyRule,
      sell_rule: config.sellRule,
    };

    // Check if this is a custom strategy (not in default options)
    const isCustomStrategy = config.tradingStrategy.startsWith("custom_");

    if (isCustomStrategy) {
      // Update existing custom strategy
      const label = customStrategies[config.tradingStrategy]?.label || currentOption.label;
      const success = await saveCustomStrategy(config.tradingStrategy, label, rules);
      if (success) {
        showToast("自定义策略已更新");
      } else {
        showToast("保存失败", "error");
      }
    } else {
      // For default strategies, we also save them to custom strategies
      // so users can modify the defaults
      const strategyKey = `custom_${config.tradingStrategy}`;
      const success = await saveCustomStrategy(strategyKey, currentOption.label, rules);
      if (success) {
        // Auto-switch to the custom strategy so the saved rules take effect immediately
        setConfig({
          ...config,
          tradingStrategy: strategyKey,
        });
        showToast(`已保存规则到 "${currentOption.label}"`);
      } else {
        showToast("保存失败", "error");
      }
    }
  };

  // Handle saving current rules as a new strategy
  const handleSaveAsNewStrategy = async () => {
    const newStrategyName = prompt("请输入新策略类型的名称:");
    if (!newStrategyName || !newStrategyName.trim()) {
      return;
    }

    const strategyKey = `custom_${Date.now()}`;
    const rules = {
      open_rule: config.openRule,
      close_rule: config.closeRule,
      buy_rule: config.buyRule,
      sell_rule: config.sellRule,
    };

    const success = await saveCustomStrategy(strategyKey, newStrategyName.trim(), rules);
    if (success) {
      // Switch to the new strategy
      setConfig({
        ...config,
        tradingStrategy: strategyKey,
      });
      alert(`新策略类型 "${newStrategyName.trim()}" 已创建`);
    } else {
      alert("创建失败");
    }
  };

  // Get all strategy options (default + custom)
  // Custom strategies override default strategies with the same label
  const getAllStrategyOptions = () => {
    const customOptions = Object.entries(customStrategies).map(([key, value]) => ({
      value: key,
      label: value.label,
    }));

    // Filter out default strategies that are overridden by custom strategies
    const customLabels = new Set(customOptions.map(o => o.label));
    const filteredDefaultOptions = tradingStrategyOptions.filter(
      o => !customLabels.has(o.label)
    );

    return [...filteredDefaultOptions, ...customOptions];
  };

  // Card order for collapse logic
  const cardOrder = ["stocks", "date-frequency", "rebalance-period", "basic-config", "position-strategy", "trading-strategy"];

  // Check if a card should be collapsed
  const shouldCollapseCard = (cardId: string) => {
    if (!activeCard) return false;
    const activeIndex = cardOrder.indexOf(activeCard);
    const currentIndex = cardOrder.indexOf(cardId);
    return currentIndex < activeIndex;
  };

  // Handle card activation
  const handleCardClick = (cardId: string) => {
    // Toggle: if clicking the already active card, collapse it
    if (activeCard === cardId) {
      setActiveCard(null);
    } else {
      setActiveCard(cardId);
    }
  };

  // Load saved configs on mount
  useEffect(() => {
    loadSavedConfigs();
  }, []);

  // State recovery: Check localStorage for saved backtest_id and restore state
  useEffect(() => {
    const restoreBacktestState = async () => {
      const savedBacktestId = localStorage.getItem('running_backtest_id');
      if (!savedBacktestId) {
        return;
      }

      try {
        const response = await getBacktestStatus(savedBacktestId);

        if (response.success && response.data) {
          const data = response.data as any;

          // Restore backtest ID
          setBacktestId(savedBacktestId);

          // Handle different states
          if (data.status === 'completed') {
            // Show results immediately
            setShowResults(true);
            setShowProgress(false);
            setIsRunning(false);
          } else if (data.status === 'running') {
            // Show progress and let WebSocket connect
            setShowProgress(true);
            setIsRunning(true);
            setBacktestProgress({
              status: 'running',
              progress: data.progress || 0,
              current_time: data.current_time,
            });
          } else if (data.status === 'failed') {
            // Show error
            setIsRunning(false);
            setShowProgress(false);
          }
          // For 'pending' status, just set the ID and wait for WebSocket
        } else {
          localStorage.removeItem('running_backtest_id');
        }
      } catch (error) {
        console.error('[State Recovery] Failed to restore backtest state:', error);
        localStorage.removeItem('running_backtest_id');
      }
    };

    restoreBacktestState();
  }, [getBacktestStatus]);

  // WebSocket回调函数（使用useCallback避免重复创建导致重连）
  const handleBacktestProgress = useCallback((progress: BacktestProgress) => {
    setBacktestProgress(progress);
    setShowProgress(true);
    // 当回测开始运行时，确保按钮状态正确
    if (progress.status === 'running') {
      setIsRunning(true);
    }
  }, []);

  const handleBacktestComplete = useCallback(() => {
    // 延迟显示结果，让用户看到进度条达到 100%
    setTimeout(() => {
      setShowResults(true);
      setShowProgress(false);
      setIsRunning(false);  // 确保按钮状态恢复
      // Clear localStorage as backtest is complete
      localStorage.removeItem('running_backtest_id');
    }, 1000);
  }, []);

  const handleBacktestError = useCallback((error: string) => {
    console.error("回测失败:", error);
    showToast(error, "error");
    setShowProgress(false);
    setIsRunning(false);  // 确保按钮状态恢复
    // Clear localStorage on error
    localStorage.removeItem('running_backtest_id');
  }, [showToast]);

  // WebSocket连接回测进度
  useBacktestWebSocket({
    backtestId: backtestId,
    onProgress: handleBacktestProgress,
    onComplete: handleBacktestComplete,
    onError: handleBacktestError,
  });

  // Load saved configs from API
  const loadSavedConfigs = async () => {
    setIsLoadingConfigs(true);
    try {
      const response = await listBacktestConfigs();
      if (response.success && response.data) {
        setSavedConfigs(response.data);
      } else {
        console.log("Response not successful or no data:", response);
      }
    } catch (error) {
      console.error("Failed to load configs:", error);
    } finally {
      setIsLoadingConfigs(false);
    }
  };

  // Load a config and populate the form
  const handleLoadConfig = async (configId: number) => {
    const configToLoad = savedConfigs.find(c => c.id === configId);
    if (!configToLoad) {
      console.error("Config not found in savedConfigs");
      return;
    }

    // Sync custom strategies from server before loading config
    await syncCustomStrategies();

    // Convert backend format to frontend format
    const formatDate = (dateStr: string) => {
      // YYYYMMDD -> YYYY-MM-DD
      if (dateStr.length === 8) {
        return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
      }
      return dateStr;
    };

    // Extract rules
    const openRule = configToLoad.open_rule || "";
    const closeRule = configToLoad.close_rule || "";
    const buyRule = configToLoad.buy_rule || "";
    const sellRule = configToLoad.sell_rule || "";

    // Update the form state
    setConfig({
      startDate: formatDate(configToLoad.start_date),
      endDate: formatDate(configToLoad.end_date),
      frequency: configToLoad.frequency,
      symbols: configToLoad.symbols,
      initialCapital: configToLoad.initial_capital,
      commissionRate: configToLoad.commission_rate,
      slippage: configToLoad.slippage,
      minLotSize: configToLoad.min_lot_size,
      positionStrategy: configToLoad.position_strategy as "fixed_percent" | "kelly" | "martingale",
      positionParams: configToLoad.position_params as Record<string, number>,
      tradingStrategy: configToLoad.trading_strategy || "monthly_investment",
      openRule,
      closeRule,
      buyRule,
      sellRule,
    });

    // Validate all rules immediately after loading (bypass debounce)
    const rulesToValidate: [string, string][] = [];
    if (openRule) rulesToValidate.push(['openRule', openRule]);
    if (closeRule) rulesToValidate.push(['closeRule', closeRule]);
    if (buyRule) rulesToValidate.push(['buyRule', buyRule]);
    if (sellRule) rulesToValidate.push(['sellRule', sellRule]);
    // Validate all rules in parallel
    for (const [key, rule] of rulesToValidate) {
      try {
        const response = await validateRule(rule);
        // Handle both wrapped and unwrapped response formats
        const validationData = response.data || response;
        if (validationData && typeof validationData.valid === 'boolean') {
          setRuleValidation(prev => ({ ...prev, [key]: { valid: validationData.valid, error: validationData.error } }));
        }
      } catch (error) {
        // Silently fail on validation errors
      }
    }

    // Update selected stocks
    const newSelectedStocks = new Set(configToLoad.symbols);
    setSelectedStocks(newSelectedStocks);
    setSelectedConfigId(configId);

    // Trigger stock searches for all symbols in the config
    // This will populate the stocks array so they can be displayed
    const symbols = configToLoad.symbols;
    if (symbols && symbols.length > 0) {
      // Search for each symbol to populate the stocks list
      for (const symbol of symbols) {
        await searchStocks(symbol);
      }
      // Clear the search input after loading
      setStockSearch("");
    }
  };

  // Save current config as new
  const handleSaveAsNewConfig = async () => {
    const name = configNameInput.trim();
    if (!name) {
      alert("请输入配置名称");
      return;
    }

    try {
      const formatDate = (dateStr: string) => {
        const [year, month, day] = dateStr.split("-");
        return `${year}${month}${day}`;
      };

      const response = await createBacktestConfig({
        name,
        description: `回测配置 - ${new Date().toLocaleDateString()}`,
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
        trading_strategy: config.tradingStrategy,
        open_rule: config.openRule || undefined,
        close_rule: config.closeRule || undefined,
        buy_rule: config.buyRule || undefined,
        sell_rule: config.sellRule || undefined,
      });

      if (response.success) {
        alert("配置已保存");
        setShowSaveDialog(false);
        setConfigNameInput("");
        await loadSavedConfigs();
      } else {
        alert("保存失败: " + response.message);
      }
    } catch (error) {
      console.error("Failed to save config:", error);
      alert("保存失败: " + (error instanceof Error ? error.message : "未知错误"));
    }
  };

  // Update existing config with current form values
  const handleUpdateConfig = async () => {
    if (!selectedConfigId) {
      alert("请先选择一个配置");
      return;
    }

    // Prevent multiple simultaneous updates
    if (isUpdating) {
      return;
    }

    setIsUpdating(true);

    try {
      const formatDate = (dateStr: string) => {
        const [year, month, day] = dateStr.split("-");
        return `${year}${month}${day}`;
      };

      const response = await updateBacktestConfig(selectedConfigId, {
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
        trading_strategy: config.tradingStrategy,
        open_rule: config.openRule || undefined,
        close_rule: config.closeRule || undefined,
        buy_rule: config.buyRule || undefined,
        sell_rule: config.sellRule || undefined,
      });

      if (response.success) {
        alert("配置已更新");
        await loadSavedConfigs();
      } else {
        alert("更新失败: " + response.message);
      }
    } catch (error) {
      console.error("Failed to update config:", error);
      alert("更新失败: " + (error instanceof Error ? error.message : "未知错误"));
    } finally {
      setIsUpdating(false);
    }
  };

  // Delete config
  const handleDeleteConfig = async (configId: number) => {
    if (!confirm("确定要删除此配置吗？")) {
      return;
    }

    try {
      const response = await deleteBacktestConfig(configId);
      if (response.success) {
        if (selectedConfigId === configId) {
          setSelectedConfigId(null);
        }
        alert("配置已删除");
        await loadSavedConfigs();
      } else {
        alert("删除失败: " + response.message);
      }
    } catch (error) {
      console.error("Failed to delete config:", error);
      alert("删除失败: " + (error instanceof Error ? error.message : "未知错误"));
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

    // 验证日期：结束日期不能超过今天
    const today = new Date();
    today.setHours(0, 0, 0, 0);  // 重置时间为00:00:00

    const endDate = new Date(config.endDate);
    endDate.setHours(0, 0, 0, 0);

    if (endDate > today) {
      const todayStr = today.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).replace(/\//g, "-");
      showToast(`结束日期不能超过今天（${todayStr}）`, "error");
      return;
    }

    // 验证开始日期早于结束日期
    const startDate = new Date(config.startDate);
    startDate.setHours(0, 0, 0, 0);

    if (startDate > endDate) {
      showToast("开始日期不能晚于结束日期", "error");
      return;
    }

    setIsRunning(true);
    setShowResults(false);  // 隐藏之前的结果
    setBacktestProgress(null);  // 重置进度
    setShowProgress(true);  // 显示进度区域

    try {
      // Format dates for backend (YYYYMMDD)
      const formatDate = (dateStr: string) => {
        const [year, month, day] = dateStr.split("-");
        return `${year}${month}${day}`;
      };

      // Get strategy type label
      const strategyTypeLabel = tradingStrategyOptions.find(
        (opt) => opt.value === config.tradingStrategy
      )?.label || config.tradingStrategy;

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
        strategy_config: {
          type: strategyTypeLabel,
          open_rule: config.openRule,
          close_rule: config.closeRule,
          buy_rule: config.buyRule,
          sell_rule: config.sellRule,
        },
        rebalance_period: rebalancePeriod.mode === 'disabled' ? undefined : {
          mode: rebalancePeriod.mode,
          trading_days_interval: rebalancePeriod.tradingDaysInterval,
          calendar_frequency: rebalancePeriod.calendarFrequency,
          calendar_day: rebalancePeriod.calendarDay,
          min_interval_days: rebalancePeriod.minIntervalDays,
          allow_first_rebalance: rebalancePeriod.allowFirstRebalance,
        },
      });

      if (response.success && response.data?.backtest_id) {
        const newBacktestId = response.data.backtest_id;
        setBacktestId(newBacktestId);
        // Save to localStorage for state recovery
        localStorage.setItem('running_backtest_id', newBacktestId);
        // WebSocket会自动连接并开始接收进度更新，完成后自动显示结果
        // 注意：不在这里设置 setIsRunning(false)，而是等待WebSocket回调
      } else {
        // 如果启动失败，恢复按钮状态
        setIsRunning(false);
        setShowProgress(false);
        alert("回测启动失败: " + (response.message || "未知错误"));
      }
    } catch (error) {
      console.error("Backtest failed:", error);
      alert("回测启动失败: " + (error instanceof Error ? error.message : "未知错误"));
      setShowProgress(false);
      setIsRunning(false);  // 只有在错误时才恢复按钮状态
    }
    // 移除 finally 块，避免立即恢复按钮状态
  };

  const handleRunOptimization = async () => {
    if (optimizationConfig.parameter_ranges.length === 0) {
      alert("请至少配置一个参数范围");
      return;
    }

    if (config.symbols.length === 0) {
      alert("请至少选择一只股票");
      return;
    }

    setOptimizationStatus("screening");
    setOptimizationError(undefined);

    try {
      // Get template rules
      const template = selectedTemplate ? STRATEGY_TEMPLATES[selectedTemplate] : null;
      const ruleTemplates = {
        open_rule_template: template?.open_rule_template || config.openRule || undefined,
        close_rule_template: template?.close_rule_template || config.closeRule || undefined,
        buy_rule_template: template?.buy_rule_template || config.buyRule || undefined,
        sell_rule_template: template?.sell_rule_template || config.sellRule || undefined,
      };

      // Format dates for backend (YYYYMMDD)
      const formatDate = (dateStr: string) => {
        const [year, month, day] = dateStr.split("-");
        return `${year}${month}${day}`;
      };

      const response = await startOptimization({
        base_config: {
          start_date: formatDate(config.startDate),
          end_date: formatDate(config.endDate),
          frequency: config.frequency,
          symbols: config.symbols,
          initial_capital: config.initialCapital,
          commission_rate: config.commissionRate,
          slippage: config.slippage,
          position_strategy: config.positionStrategy,
          position_params: config.positionParams,
        },
        rule_templates: ruleTemplates,
        optimization_config: {
          parameter_ranges: optimizationConfig.parameter_ranges,
          scan_method: optimizationConfig.scan_method,
          random_samples: optimizationConfig.random_samples,
          screening_period: optimizationConfig.screening_period,
          screening_metric: optimizationConfig.screening_metric,
          top_n_candidates: optimizationConfig.top_n_candidates,
          performance_thresholds: optimizationConfig.performance_thresholds,
        },
      });

      if (response.success && response.data?.optimization_id) {
        setOptimizationId(response.data.optimization_id);

        // Poll for results
        pollOptimizationResults(response.data.optimization_id);
      } else {
        setOptimizationStatus("failed");
        setOptimizationError(response.message || "优化启动失败");
        alert("优化启动失败: " + (response.message || "未知错误"));
      }
    } catch (error) {
      console.error("Optimization failed:", error);
      setOptimizationStatus("failed");
      setOptimizationError(error instanceof Error ? error.message : "未知错误");
      alert("优化启动失败: " + (error instanceof Error ? error.message : "未知错误"));
    }
  };

  const pollOptimizationResults = async (optId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await getOptimizationResults(optId);

        if (response.success && response.data) {
          const { status, screening_results, error } = response.data;

          if (status === "completed" && screening_results) {
            setOptimizationStatus("completed");
            setOptimizationResults(screening_results);
            clearInterval(pollInterval);
          } else if (status === "failed") {
            setOptimizationStatus("failed");
            setOptimizationError(error || "优化失败");
            clearInterval(pollInterval);
          }
          // Still screening, continue polling
        }
      } catch (error) {
        console.error("Failed to poll optimization results:", error);
        setOptimizationStatus("failed");
        setOptimizationError(error instanceof Error ? error.message : "获取结果失败");
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(pollInterval);
  };

  const handleSelectOptimizationResult = (result: ScreeningResult) => {
    // Apply the selected parameters to the current configuration
    if (selectedTemplate) {
      const template = STRATEGY_TEMPLATES[selectedTemplate];

      // Render rules with selected parameters
      const renderTemplate = (templateStr: string | undefined) => {
        if (!templateStr) return "";
        let rendered = templateStr;
        Object.entries(result.parameters).forEach(([key, value]) => {
          rendered = rendered.replace(new RegExp(`\\{${key}\\}`, "g"), String(value));
        });
        return rendered;
      };

      setConfig({
        ...config,
        openRule: renderTemplate(template.open_rule_template),
        closeRule: renderTemplate(template.close_rule_template),
        buyRule: renderTemplate(template.buy_rule_template),
        sellRule: renderTemplate(template.sell_rule_template),
      });

      showToast(`已应用参数组合 #${result.rank}`, "success");
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

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-24 left-1/2 -translate-x-1/2 z-[9999] px-6 py-3 rounded-lg shadow-xl text-sm font-medium transition-opacity duration-300 ${
          toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
        }`}>
          {toast.message}
        </div>
      )}

      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-muted-foreground hover:text-sky-400 transition-colors"
              >
                {t('dashboard')}
              </Link>
              <Link
                href="/backtest"
                className="text-foreground hover:text-sky-400 transition-colors"
              >
                {t('backtesting')}
              </Link>
              <Link
                href="/trading"
                className="text-muted-foreground hover:text-sky-400 transition-colors"
              >
                {t('trading')}
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <ThemeSwitcher />
            <CoffeeModal />
            <UserAccountMenu
              username={user.username}
              onLogout={async () => {
                await logout();
                window.location.href = "/login";
              }}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">{t('title')}</h1>
          <p className="text-muted-foreground">
            {t('description')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1 space-y-6">
            {/* Config Selector */}
            <Card className="p-4 bg-[#FFEFD5] dark:bg-card/50 shadow-md hover:shadow-lg transition-all">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">回测配置</h3>
                  <Button
                    size="sm"
                    onClick={() => setShowSaveDialog(true)}
                    className="h-7 px-2 text-xs bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                  >
                    保存为新配置
                  </Button>
                </div>

                <select
                  value={selectedConfigId || "custom"}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === "custom") {
                      setSelectedConfigId(null);
                    } else {
                      handleLoadConfig(Number(val));
                    }
                  }}
                  className="w-full px-3 py-2 bg-input border border-border rounded text-foreground text-sm"
                >
                  <option value="custom">自定义配置</option>
                  {savedConfigs.map((cfg) => (
                    <option key={cfg.id} value={cfg.id}>
                      {cfg.name} {cfg.is_default ? "(默认)" : ""}
                    </option>
                  ))}
                </select>

                {/* Action buttons for selected config */}
                {selectedConfigId && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={handleUpdateConfig}
                      disabled={isUpdating}
                      className="flex-1 h-8 text-xs bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUpdating ? "更新中..." : "更新配置"}
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleDeleteConfig(selectedConfigId)}
                      className="flex-1 h-8 text-xs bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                    >
                      删除配置
                    </Button>
                  </div>
                )}
              </div>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Button
                onClick={handleRunBacktest}
                disabled={isRunning || config.symbols.length === 0}
                className="flex-1 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRunning ? "运行中..." : "运行回测"}
              </Button>
              <Button
                onClick={() => {
                  setConfig(defaultConfig);
                  setSelectedStocks(new Set());
                }}
                className="bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
              >
                重置
              </Button>
            </div>

            {/* View History Button */}
            <Link href="/backtest-history" className="block">
              <Button
                variant="outline"
                className="w-full bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
              >
                📜 查看历史记录
              </Button>
            </Link>

            {/* Stock Selection */}
            <CollapsibleCard id="stocks" title="选择交易标的" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="搜索股票代码或名称..."
                  value={stockSearch}
                  onChange={(e) => setStockSearch(e.target.value)}
                  className="w-full px-3 py-2 bg-input border border-border rounded text-foreground placeholder-muted-foreground"
                />

                <div className="max-h-48 overflow-y-auto space-y-1">
                  {isLoadingStocks ? (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500" />
                    </div>
                  ) : stocks.length === 0 ? (
                    <div className="text-center py-4 text-muted-foreground text-sm">
                      {stockSearch.length === 0
                        ? "请输入股票代码或名称进行搜索"
                        : "未找到匹配的股票"}
                    </div>
                  ) : (
                    stocks.slice(0, 50).map((stock) => (
                      <label
                        key={stock.code}
                        className="flex items-center gap-2 p-2 hover:bg-muted rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedStocks.has(stock.code)}
                          onChange={() => handleStockToggle(stock.code)}
                          className="rounded border-border bg-input text-sky-500 focus:ring-sky-500"
                        />
                        <span className="text-sm text-foreground">{stock.code}</span>
                        <span className="text-xs text-muted-foreground truncate">{stock.name}</span>
                      </label>
                    ))
                  )}
                </div>

                <p className="text-xs text-muted-foreground">
                  已选择 {selectedStocks.size} 只股票
                </p>
              </div>
            </CollapsibleCard>

            {/* Date & Frequency */}
            <CollapsibleCard id="date-frequency" title="日期与频率" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="start-date" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    开始日期
                  </label>
                  <input
                    id="start-date"
                    type="date"
                    max={maxDate}
                    value={config.startDate}
                    onChange={(e) =>
                      setConfig({ ...config, startDate: e.target.value })
                    }
                    onFocus={(e) => (e.target as HTMLInputElement).showPicker?.()}
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground select-none cursor-pointer"
                  />
                </div>

                <div>
                  <label htmlFor="end-date" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    结束日期
                  </label>
                  <input
                    id="end-date"
                    type="date"
                    max={maxDate}
                    value={config.endDate}
                    onChange={(e) =>
                      setConfig({ ...config, endDate: e.target.value })
                    }
                    onFocus={(e) => (e.target as HTMLInputElement).showPicker?.()}
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground select-none cursor-pointer"
                  />
                </div>

                <div>
                  <label htmlFor="frequency" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    数据频率
                  </label>
                  <select
                    id="frequency"
                    value={config.frequency}
                    onChange={(e) =>
                      setConfig({ ...config, frequency: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                  >
                    {frequencyOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CollapsibleCard>

            {/* Rebalance Period */}
            <CollapsibleCard id="rebalance-period" title="调仓周期" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="rebalance-mode" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    调仓模式
                  </label>
                  <select
                    id="rebalance-mode"
                    value={rebalancePeriod.mode}
                    onChange={(e) => setRebalancePeriod({
                      ...rebalancePeriod,
                      mode: e.target.value as 'disabled' | 'trading_days' | 'calendar_rule'
                    })}
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                  >
                    <option value="disabled">不限制（每个数据点检查）</option>
                    <option value="trading_days">按交易日数</option>
                    <option value="calendar_rule">按固定日期</option>
                  </select>
                </div>

                {rebalancePeriod.mode === 'trading_days' && (
                  <div>
                    <label htmlFor="trading-days-interval" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                      每隔N个交易日调仓
                    </label>
                    <input
                      id="trading-days-interval"
                      type="number"
                      value={rebalancePeriod.tradingDaysInterval || 5}
                      onChange={(e) => setRebalancePeriod({
                        ...rebalancePeriod,
                        tradingDaysInterval: Number(e.target.value)
                      })}
                      min="1"
                      step="1"
                      className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                    />
                  </div>
                )}

                {rebalancePeriod.mode === 'calendar_rule' && (
                  <>
                    <div>
                      <label htmlFor="calendar-frequency" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                        频率
                      </label>
                      <select
                        id="calendar-frequency"
                        value={rebalancePeriod.calendarFrequency || 'weekly'}
                        onChange={(e) => setRebalancePeriod({
                          ...rebalancePeriod,
                          calendarFrequency: e.target.value as 'weekly' | 'monthly'
                        })}
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                      >
                        <option value="weekly">每周</option>
                        <option value="monthly">每月</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="calendar-day" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                        {rebalancePeriod.calendarFrequency === 'weekly' ? '星期几 (1-7, 1=周一)' : '日期 (1-31)'}
                      </label>
                      <input
                        id="calendar-day"
                        type="number"
                        value={rebalancePeriod.calendarDay || 1}
                        onChange={(e) => setRebalancePeriod({
                          ...rebalancePeriod,
                          calendarDay: Number(e.target.value)
                        })}
                        min="1"
                        max={rebalancePeriod.calendarFrequency === 'weekly' ? 7 : 31}
                        step="1"
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                      />
                    </div>
                  </>
                )}

                {rebalancePeriod.mode !== 'disabled' && (
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="allow-first-rebalance"
                      checked={rebalancePeriod.allowFirstRebalance}
                      onChange={(e) => setRebalancePeriod({
                        ...rebalancePeriod,
                        allowFirstRebalance: e.target.checked
                      })}
                      className="w-4 h-4 rounded border-border"
                    />
                    <label htmlFor="allow-first-rebalance" className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                      首次交易日强制调仓
                    </label>
                  </div>
                )}
              </div>
            </CollapsibleCard>

            {/* Basic Configuration */}
            <CollapsibleCard id="basic-config" title="基础配置" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="initial-capital" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    初始资金
                  </label>
                  <input
                    id="initial-capital"
                    type="number"
                    value={config.initialCapital}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        initialCapital: Number(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                    min="1000"
                    step="10000"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="commission-rate" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                      手续费率
                    </label>
                    <input
                      id="commission-rate"
                      type="number"
                      value={config.commissionRate}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          commissionRate: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                      min="0"
                      max="0.1"
                      step="0.0001"
                    />
                  </div>

                  <div>
                    <label htmlFor="slippage" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                      滑点率
                    </label>
                    <input
                      id="slippage"
                      type="number"
                      value={config.slippage}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          slippage: Number(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                      min="0"
                      max="0.1"
                      step="0.0001"
                    />
                  </div>
                </div>
              </div>
            </CollapsibleCard>

            {/* Position Strategy */}
            <CollapsibleCard id="position-strategy" title="仓位策略" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="position-strategy" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    策略类型
                  </label>
                  <select
                    id="position-strategy"
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
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
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
                    <label htmlFor="position-percent" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                      仓位比例
                    </label>
                    <input
                      id="position-percent"
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
                      className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
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
                      <label htmlFor="kelly-win-rate" className="block text-sm text-muted-foreground mb-1 cursor-pointer hover:text-foreground">
                        预估胜率
                      </label>
                      <input
                        id="kelly-win-rate"
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
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                        min="0"
                        max="100"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label htmlFor="kelly-win-loss-ratio" className="block text-sm text-muted-foreground mb-1 cursor-pointer hover:text-foreground">
                        预估盈亏比
                      </label>
                      <input
                        id="kelly-win-loss-ratio"
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
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
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
                      <label htmlFor="martingale-base-percent" className="block text-sm text-muted-foreground mb-1 cursor-pointer hover:text-foreground">
                        基础仓位比例
                      </label>
                      <input
                        id="martingale-base-percent"
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
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                        min="0"
                        max="20"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label htmlFor="martingale-multiplier" className="block text-sm text-muted-foreground mb-1 cursor-pointer hover:text-foreground">
                        加倍系数
                      </label>
                      <input
                        id="martingale-multiplier"
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
                        className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                        min="1"
                        max="5"
                        step="0.1"
                      />
                    </div>
                  </div>
                )}
              </div>
            </CollapsibleCard>

            {/* Trading Strategy */}
            <CollapsibleCard id="trading-strategy" title="交易策略配置" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="trading-strategy" className="block text-sm text-muted-foreground mb-2 cursor-pointer hover:text-foreground">
                    策略类型
                  </label>
                  <select
                    id="trading-strategy"
                    value={config.tradingStrategy}
                    onChange={(e) =>
                      setConfig({ ...config, tradingStrategy: e.target.value, openRule: "", closeRule: "", buyRule: "", sellRule: "" })
                    }
                    className="w-full px-3 py-2 bg-input border border-border rounded text-foreground"
                  >
                    {getAllStrategyOptions().map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label htmlFor="open-rule" className="block text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        开仓条件
                      </label>
                      {config.openRule && ruleValidation.openRule && (
                        <span className={`text-xs ${ruleValidation.openRule.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                          {ruleValidation.openRule.valid ? '✓ 语法正确' : `✗ ${ruleValidation.openRule.error || '语法错误'}`}
                        </span>
                      )}
                    </div>
                    <textarea
                      id="open-rule"
                      value={config.openRule}
                      onChange={(e) => {
                        setConfig({ ...config, openRule: e.target.value });
                        validateRuleDebounced('openRule', e.target.value);
                      }}
                      placeholder="如: close > SMA(close, 20)"
                      rows={3}
                      className={`w-full px-3 py-2 bg-input border rounded text-foreground placeholder-muted-foreground text-sm resize-y ${
                        config.openRule && ruleValidation.openRule
                          ? ruleValidation.openRule.valid
                            ? 'border-emerald-600'
                            : 'border-red-600'
                          : 'border-border'
                      }`}
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label htmlFor="close-rule" className="block text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        清仓条件
                      </label>
                      {config.closeRule && ruleValidation.closeRule && (
                        <span className={`text-xs ${ruleValidation.closeRule.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                          {ruleValidation.closeRule.valid ? '✓ 语法正确' : `✗ ${ruleValidation.closeRule.error || '语法错误'}`}
                        </span>
                      )}
                    </div>
                    <textarea
                      id="close-rule"
                      value={config.closeRule}
                      onChange={(e) => {
                        setConfig({ ...config, closeRule: e.target.value });
                        validateRuleDebounced('closeRule', e.target.value);
                      }}
                      placeholder="如: close < SMA(close, 20)"
                      rows={3}
                      className={`w-full px-3 py-2 bg-input border rounded text-foreground placeholder-muted-foreground text-sm resize-y ${
                        config.closeRule && ruleValidation.closeRule
                          ? ruleValidation.closeRule.valid
                            ? 'border-emerald-600'
                            : 'border-red-600'
                          : 'border-border'
                      }`}
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label htmlFor="buy-rule" className="block text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        加仓条件
                      </label>
                      {config.buyRule && ruleValidation.buyRule && (
                        <span className={`text-xs ${ruleValidation.buyRule.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                          {ruleValidation.buyRule.valid ? '✓ 语法正确' : `✗ ${ruleValidation.buyRule.error || '语法错误'}`}
                        </span>
                      )}
                    </div>
                    <textarea
                      id="buy-rule"
                      value={config.buyRule}
                      onChange={(e) => {
                        setConfig({ ...config, buyRule: e.target.value });
                        validateRuleDebounced('buyRule', e.target.value);
                      }}
                      placeholder="如: RSI(close, 14) < 30"
                      rows={3}
                      className={`w-full px-3 py-2 bg-input border rounded text-foreground placeholder-muted-foreground text-sm resize-y ${
                        config.buyRule && ruleValidation.buyRule
                          ? ruleValidation.buyRule.valid
                            ? 'border-emerald-600'
                            : 'border-red-600'
                          : 'border-border'
                      }`}
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label htmlFor="sell-rule" className="block text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        平仓条件
                      </label>
                      {config.sellRule && ruleValidation.sellRule && (
                        <span className={`text-xs ${ruleValidation.sellRule.valid ? 'text-emerald-400' : 'text-red-400'}`}>
                          {ruleValidation.sellRule.valid ? '✓ 语法正确' : `✗ ${ruleValidation.sellRule.error || '语法错误'}`}
                        </span>
                      )}
                    </div>
                    <textarea
                      id="sell-rule"
                      value={config.sellRule}
                      onChange={(e) => {
                        setConfig({ ...config, sellRule: e.target.value });
                        validateRuleDebounced('sellRule', e.target.value);
                      }}
                      placeholder="如: RSI(close, 14) > 70"
                      rows={3}
                      className={`w-full px-3 py-2 bg-input border rounded text-foreground placeholder-muted-foreground text-sm resize-y ${
                        config.sellRule && ruleValidation.sellRule
                          ? ruleValidation.sellRule.valid
                            ? 'border-emerald-600'
                            : 'border-red-600'
                          : 'border-border'
                      }`}
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleSaveToStrategy}
                    className="flex-1 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                  >
                    保存到当前策略
                  </Button>
                  <Button
                    onClick={handleSaveAsNewStrategy}
                    className="flex-1 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                  >
                    保存为新策略
                  </Button>
                </div>
              </div>
            </CollapsibleCard>

            {/* Parameter Optimization */}
            <CollapsibleCard id="optimization" title="参数优化" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                {/* Toggle optimization */}
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground">启用参数优化</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      自动搜索最优参数组合
                    </p>
                  </div>
                  <button
                    onClick={() => setShowOptimization(!showOptimization)}
                    className="px-4 py-2 rounded-full text-sm font-medium transition-all bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white shadow-md hover:shadow-lg"
                  >
                    {showOptimization ? "已启用" : "已禁用"}
                  </button>
                </div>

                {/* Optimization Configuration */}
                {showOptimization && (
                  <>
                    {/* Template Selection */}
                    <div className="border-t border-border pt-4">
                      <ParameterConfig
                        config={optimizationConfig}
                        onConfigChange={setOptimizationConfig}
                        selectedTemplate={selectedTemplate}
                        onTemplateChange={setSelectedTemplate}
                        currentRules={{
                          openRule: config.openRule,
                          closeRule: config.closeRule,
                          buyRule: config.buyRule,
                          sellRule: config.sellRule,
                        }}
                      />
                    </div>

                    {/* Run Optimization Button */}
                    <Button
                      onClick={handleRunOptimization}
                      disabled={optimizationConfig.parameter_ranges.length === 0 || optimizationStatus === "screening"}
                      className="w-full bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {optimizationStatus === "screening" ? "优化中..." : "开始参数优化"}
                    </Button>

                    {/* Optimization Results */}
                    {optimizationId && (
                      <div className="border-t border-border pt-4">
                        <OptimizationResults
                          optimizationId={optimizationId}
                          results={optimizationResults}
                          status={optimizationStatus}
                          error={optimizationError}
                          onSelectResult={handleSelectOptimizationResult}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            </CollapsibleCard>
          </div>

          {/* Results / Chart Area */}
          <div className="lg:col-span-2">
            {/* 进度条 - 使用WebSocket实时更新 */}
            {showProgress && backtestProgress && (
              <BacktestProgressBar
                progress={backtestProgress.progress * 100}
                currentTime={backtestProgress.current_time}
                status={backtestProgress.status}
                error={backtestProgress.error}
              />
            )}

            {showResults && backtestId ? (
              <BacktestResultsView backtestId={backtestId} />
            ) : (
              <Card className="p-6 bg-[#FFEFD5] dark:bg-card/50 shadow-md hover:shadow-lg transition-all">
                <div className="aspect-video bg-muted/50 rounded flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-muted-foreground mb-2">
                      配置回测参数后点击"运行回测"
                    </p>
                    <p className="text-sm text-muted-foreground">
                      结果将在此处显示
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>

      {/* Save Config Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-[#FFEFD5] dark:bg-card shadow-md hover:shadow-lg transition-all w-96">
            <h3 className="text-lg font-semibold mb-4">保存为新配置</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="config-name" className="block text-sm text-muted-foreground mb-2">
                  配置名称
                </label>
                <input
                  id="config-name"
                  type="text"
                  value={configNameInput}
                  onChange={(e) => setConfigNameInput(e.target.value)}
                  placeholder="输入配置名称"
                  className="w-full px-3 py-2 bg-input border border-border rounded text-foreground placeholder-muted-foreground"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSaveAsNewConfig();
                    }
                  }}
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setShowSaveDialog(false);
                    setConfigNameInput("");
                  }}
                  className="flex-1 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                >
                  取消
                </Button>
                <Button
                  onClick={handleSaveAsNewConfig}
                  className="flex-1 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full font-medium transition-all shadow-md hover:shadow-lg"
                >
                  保存
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
