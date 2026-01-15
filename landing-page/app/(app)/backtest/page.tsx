"use client";

/**
 * Backtest Configuration Page
 *
 * Configure and run backtests with the QuantOL platform.
 */

import { useState, useEffect, useCallback } from "react";
import { useRequireAuth } from "@/lib/store";
import { useApi, BacktestConfig as ApiBacktestConfig } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Link from "next/link";
import { BacktestProgressBar } from "@/components/backtest/BacktestProgressBar";
import { BacktestResultsView } from "@/components/backtest/BacktestResultsView";
import { useBacktestWebSocket } from "@/lib/hooks/useBacktestWebSocket";

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

// Local storage keys
const STRATEGY_RULES_KEY = "quantol_strategy_rules";

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
      className={`bg-slate-900/50 border-slate-800 transition-all duration-300 ${
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
          <span className={`text-slate-400 transition-transform duration-300 ${isActive ? "rotate-180" : ""}`}>
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
  const { user, isLoading, token } = useRequireAuth();
  const {
    getStocks,
    runBacktest,
    listBacktestConfigs,
    createBacktestConfig,
    updateBacktestConfig,
    deleteBacktestConfig,
    getTradingStrategies,
    getPositionStrategies,
    logout,
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
      // 限制只能选择"市北高新"和"平安银行"（临时限制，以后需要恢复原逻辑）
      const allowedStocks = [
        { code: "600604", name: "市北高新" },
        { code: "000001", name: "平安银行" },
      ];
      // 根据搜索关键词过滤
      const filtered = allowedStocks.filter(
        s =>
          !search ||
          s.code.includes(search) ||
          s.name.includes(search)
      );
      setStocks(filtered);

      // 原逻辑（以后恢复时使用）：
      // const response = await getStocks(search, 100);
      // if (response.success && response.data) {
      //   setStocks(response.data);
      // }
    } catch (error) {
      console.error("Failed to search stocks:", error);
    } finally {
      setIsLoadingStocks(false);
    }
  };

  // Strategy rules management
  const [customStrategies, setCustomStrategies] = useState<Record<string, { label: string; rules: { open_rule: string; close_rule: string; buy_rule: string; sell_rule: string } }>>({});

  // Load custom strategies from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(STRATEGY_RULES_KEY);
      if (saved) {
        try {
          setCustomStrategies(JSON.parse(saved));
        } catch (e) {
          console.error("Failed to parse saved strategies:", e);
        }
      }
    }
  }, []);

  // Save custom strategies to localStorage
  const saveCustomStrategies = (strategies: typeof customStrategies) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STRATEGY_RULES_KEY, JSON.stringify(strategies));
      setCustomStrategies(strategies);
    }
  };

  // Get rules for a strategy (from custom strategies or defaults)
  const getStrategyRules = (strategyValue: string) => {
    // Check custom strategies first
    const customStrategy = Object.values(customStrategies).find(s => s.label === strategyValue);
    if (customStrategy) {
      return customStrategy.rules;
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
    const currentOption = tradingStrategyOptions.find(o => o.value === config.tradingStrategy);
    if (currentOption) {
      const rules = getStrategyRules(currentOption.label);
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
  const handleSaveToStrategy = () => {
    const currentOption = tradingStrategyOptions.find(o => o.value === config.tradingStrategy);
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
      const newStrategies = { ...customStrategies };
      newStrategies[config.tradingStrategy] = {
        label: newStrategies[config.tradingStrategy].label,
        rules,
      };
      saveCustomStrategies(newStrategies);
      alert("自定义策略已更新");
    } else {
      // For default strategies, we also save them to custom strategies
      // so users can modify the defaults
      const strategyKey = `custom_${config.tradingStrategy}`;
      const newStrategies = { ...customStrategies };
      newStrategies[strategyKey] = {
        label: currentOption.label,
        rules,
      };
      saveCustomStrategies(newStrategies);
      alert(`已保存规则到 "${currentOption.label}"`);
    }
  };

  // Handle saving current rules as a new strategy
  const handleSaveAsNewStrategy = () => {
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

    const newStrategies = {
      ...customStrategies,
      [strategyKey]: {
        label: newStrategyName.trim(),
        rules,
      },
    };
    saveCustomStrategies(newStrategies);

    // Switch to the new strategy
    setConfig({
      ...config,
      tradingStrategy: strategyKey,
    });

    alert(`新策略类型 "${newStrategyName.trim()}" 已创建`);
  };

  // Get all strategy options (default + custom)
  const getAllStrategyOptions = () => {
    const customOptions = Object.entries(customStrategies).map(([key, value]) => ({
      value: key,
      label: value.label,
    }));
    return [...tradingStrategyOptions, ...customOptions];
  };

  // Card order for collapse logic
  const cardOrder = ["stocks", "date-frequency", "basic-config", "position-strategy", "trading-strategy"];

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
    }, 1000);
  }, []);

  const handleBacktestError = useCallback((error: string) => {
    console.error("回测失败:", error);
    setShowProgress(false);
    setIsRunning(false);  // 确保按钮状态恢复
  }, []);

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
      console.log("listBacktestConfigs response:", response);
      if (response.success && response.data) {
        console.log("Setting saved configs:", response.data);
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
    console.log("handleLoadConfig called with configId:", configId);
    console.log("Current savedConfigs:", savedConfigs);
    const configToLoad = savedConfigs.find(c => c.id === configId);
    console.log("Found configToLoad:", configToLoad);
    if (!configToLoad) {
      console.error("Config not found in savedConfigs");
      return;
    }

    console.log("configToLoad.symbols:", configToLoad.symbols);

    // Convert backend format to frontend format
    const formatDate = (dateStr: string) => {
      // YYYYMMDD -> YYYY-MM-DD
      if (dateStr.length === 8) {
        return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
      }
      return dateStr;
    };

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
      openRule: configToLoad.open_rule || "",
      closeRule: configToLoad.close_rule || "",
      buyRule: configToLoad.buy_rule || "",
      sellRule: configToLoad.sell_rule || "",
    });

    // Update selected stocks
    const newSelectedStocks = new Set(configToLoad.symbols);
    console.log("Setting selectedStocks to:", newSelectedStocks);
    setSelectedStocks(newSelectedStocks);
    setSelectedConfigId(configId);

    // Trigger stock searches for all symbols in the config
    // This will populate the stocks array so they can be displayed
    const symbols = configToLoad.symbols;
    if (symbols && symbols.length > 0) {
      console.log("Searching for stocks:", symbols);
      // Search for each symbol to populate the stocks list
      for (const symbol of symbols) {
        await searchStocks(symbol, 100);
      }
      // Clear the search input after loading
      setStockSearch("");
    }

    console.log("Config loaded successfully");
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
      });

      if (response.success && response.data?.backtest_id) {
        setBacktestId(response.data.backtest_id);
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

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) return null;

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
              onClick={async () => {
                await logout();
                window.location.href = "/login";
              }}
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
            {/* Config Selector */}
            <Card className="p-4 bg-slate-900/50 border-slate-800">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-300">回测配置</h3>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowSaveDialog(true)}
                    className="h-7 px-2 text-xs border-sky-600 text-sky-400 hover:bg-sky-600/10"
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
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"
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
                      variant="outline"
                      onClick={handleUpdateConfig}
                      disabled={isUpdating}
                      className="flex-1 h-8 text-xs border-emerald-600 text-emerald-400 hover:bg-emerald-600/10 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUpdating ? "更新中..." : "更新配置"}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteConfig(selectedConfigId)}
                      className="flex-1 h-8 text-xs border-red-600 text-red-400 hover:bg-red-600/10"
                    >
                      删除配置
                    </Button>
                  </div>
                )}
              </div>
            </Card>

            {/* Stock Selection */}
            <CollapsibleCard id="stocks" title="选择交易标的" activeCard={activeCard} onCardClick={handleCardClick}>
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
                  ) : stocks.length === 0 ? (
                    <div className="text-center py-4 text-slate-500 text-sm">
                      {stockSearch.length === 0
                        ? "请输入股票代码或名称进行搜索"
                        : "未找到匹配的股票"}
                    </div>
                  ) : (
                    stocks.slice(0, 50).map((stock) => (
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
            </CollapsibleCard>

            {/* Date & Frequency */}
            <CollapsibleCard id="date-frequency" title="日期与频率" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="start-date" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                    开始日期
                  </label>
                  <input
                    id="start-date"
                    type="date"
                    value={config.startDate}
                    onChange={(e) =>
                      setConfig({ ...config, startDate: e.target.value })
                    }
                    onFocus={(e) => (e.target as HTMLInputElement).showPicker?.()}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white select-none cursor-pointer"
                  />
                </div>

                <div>
                  <label htmlFor="end-date" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                    结束日期
                  </label>
                  <input
                    id="end-date"
                    type="date"
                    value={config.endDate}
                    onChange={(e) =>
                      setConfig({ ...config, endDate: e.target.value })
                    }
                    onFocus={(e) => (e.target as HTMLInputElement).showPicker?.()}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white select-none cursor-pointer"
                  />
                </div>

                <div>
                  <label htmlFor="frequency" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                    数据频率
                  </label>
                  <select
                    id="frequency"
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
            </CollapsibleCard>

            {/* Basic Configuration */}
            <CollapsibleCard id="basic-config" title="基础配置" activeCard={activeCard} onCardClick={handleCardClick}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="initial-capital" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
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
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                    min="1000"
                    step="10000"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="commission-rate" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
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
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                      min="0"
                      max="0.1"
                      step="0.0001"
                    />
                  </div>

                  <div>
                    <label htmlFor="slippage" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
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
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
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
                  <label htmlFor="position-strategy" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
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
                    <label htmlFor="position-percent" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
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
                      <label htmlFor="kelly-win-rate" className="block text-sm text-slate-400 mb-1 cursor-pointer hover:text-slate-300">
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
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="0"
                        max="100"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label htmlFor="kelly-win-loss-ratio" className="block text-sm text-slate-400 mb-1 cursor-pointer hover:text-slate-300">
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
                      <label htmlFor="martingale-base-percent" className="block text-sm text-slate-400 mb-1 cursor-pointer hover:text-slate-300">
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
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                        min="0"
                        max="20"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label htmlFor="martingale-multiplier" className="block text-sm text-slate-400 mb-1 cursor-pointer hover:text-slate-300">
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
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
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
                  <label htmlFor="trading-strategy" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                    策略类型
                  </label>
                  <select
                    id="trading-strategy"
                    value={config.tradingStrategy}
                    onChange={(e) =>
                      setConfig({ ...config, tradingStrategy: e.target.value, openRule: "", closeRule: "", buyRule: "", sellRule: "" })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
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
                    <label htmlFor="open-rule" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                      开仓条件
                    </label>
                    <textarea
                      id="open-rule"
                      value={config.openRule}
                      onChange={(e) =>
                        setConfig({ ...config, openRule: e.target.value })
                      }
                      placeholder="如: close > ma20"
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 text-sm resize-y"
                    />
                  </div>

                  <div>
                    <label htmlFor="close-rule" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                      清仓条件
                    </label>
                    <textarea
                      id="close-rule"
                      value={config.closeRule}
                      onChange={(e) =>
                        setConfig({ ...config, closeRule: e.target.value })
                      }
                      placeholder="如: close < ma20"
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 text-sm resize-y"
                    />
                  </div>

                  <div>
                    <label htmlFor="buy-rule" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                      加仓条件
                    </label>
                    <textarea
                      id="buy-rule"
                      value={config.buyRule}
                      onChange={(e) =>
                        setConfig({ ...config, buyRule: e.target.value })
                      }
                      placeholder="如: rsi < 30"
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 text-sm resize-y"
                    />
                  </div>

                  <div>
                    <label htmlFor="sell-rule" className="block text-sm text-slate-400 mb-2 cursor-pointer hover:text-slate-300">
                      平仓条件
                    </label>
                    <textarea
                      id="sell-rule"
                      value={config.sellRule}
                      onChange={(e) =>
                        setConfig({ ...config, sellRule: e.target.value })
                      }
                      placeholder="如: rsi > 70"
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 text-sm resize-y"
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleSaveToStrategy}
                    variant="outline"
                    className="flex-1 border-sky-600 text-sky-400 hover:bg-sky-600/10"
                  >
                    保存到当前策略
                  </Button>
                  <Button
                    onClick={handleSaveAsNewStrategy}
                    variant="outline"
                    className="flex-1 border-emerald-600 text-emerald-400 hover:bg-emerald-600/10"
                  >
                    保存为新策略
                  </Button>
                </div>
              </div>
            </CollapsibleCard>

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

      {/* Save Config Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-slate-900 border-slate-800 w-96">
            <h3 className="text-lg font-semibold mb-4">保存为新配置</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="config-name" className="block text-sm text-slate-400 mb-2">
                  配置名称
                </label>
                <input
                  id="config-name"
                  type="text"
                  value={configNameInput}
                  onChange={(e) => setConfigNameInput(e.target.value)}
                  placeholder="输入配置名称"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500"
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
                  variant="outline"
                  onClick={() => {
                    setShowSaveDialog(false);
                    setConfigNameInput("");
                  }}
                  className="flex-1 border-slate-700 text-slate-300 hover:bg-slate-800"
                >
                  取消
                </Button>
                <Button
                  onClick={handleSaveAsNewConfig}
                  className="flex-1 bg-sky-600 hover:bg-sky-700 text-white"
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
