"""Strategy type registry and mapping utilities.

Centralizes strategy type mappings to avoid duplication across services.
Currently duplicated in backtest_task_manager.py and backtest_execution_service.py.
"""

from typing import Dict, Optional


class StrategyRegistry:
    """Registry for strategy type mappings and validation."""

    # Map frontend strategy labels to internal strategy types
    STRATEGY_LABEL_TO_TYPE: Dict[str, str] = {
        "月定投": "月定投",
        "自定义策略": "自定义规则",
        "移动平均线交叉": "自定义规则",
        "MACD交叉": "自定义规则",
        "RSI超买超卖": "自定义规则",
        "Martingale": "自定义规则",
    }

    # Preset rules for built-in strategies
    PRESET_RULES: Dict[str, Dict[str, str]] = {
        "移动平均线交叉": {
            "open_rule": "(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))",
            "close_rule": "(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))",
        },
        "MACD交叉": {
            "open_rule": "MACD(close, 12, 26, 9) > MACD_SIGNAL(close, 12, 26, 9)",
            "close_rule": "MACD(close, 12, 26, 9) < MACD_SIGNAL(close, 12, 26, 9)",
        },
        "RSI超买超卖": {
            "open_rule": "(REF(RSI(close,5), 1) < 30) & (RSI(close,5) >= 30)",
            "close_rule": "(REF(RSI(close,5), 1) >= 60) & (RSI(close,5) < 60)",
        },
        "Martingale": {
            "open_rule": "(close < REF(SMA(close,5), 1)) & (close > SMA(close,5))",
            "close_rule": "(close - (COST/POSITION))/(COST/POSITION) * 100 >= 5",
            "buy_rule": "(close - (COST/POSITION))/(COST/POSITION) * 100 <= -5",
        },
    }

    @classmethod
    def get_internal_strategy_type(cls, strategy_label: str) -> str:
        """Get internal strategy type from frontend label.

        Args:
            strategy_label: Frontend strategy label (e.g., "月定投", "custom_123456")

        Returns:
            Internal strategy type (e.g., "月定投", "自定义规则")

        Raises:
            ValueError: If strategy label is not supported
        """
        # Support dynamic custom strategies (custom_1234567890)
        if strategy_label.startswith("custom_"):
            return "自定义规则"

        if strategy_label not in cls.STRATEGY_LABEL_TO_TYPE:
            supported = list(cls.STRATEGY_LABEL_TO_TYPE.keys()) + ["custom_XXX (自定义策略)"]
            raise ValueError(
                f"Unsupported strategy type: '{strategy_label}'. "
                f"Supported types: {', '.join(supported)}"
            )

        return cls.STRATEGY_LABEL_TO_TYPE[strategy_label]

    @classmethod
    def get_preset_rules(cls, strategy_label: str) -> Dict[str, str]:
        """Get preset rules for a built-in strategy.

        Args:
            strategy_label: Frontend strategy label

        Returns:
            Dictionary of preset rules (buy_rule, sell_rule, etc.)
        """
        return cls.PRESET_RULES.get(strategy_label, {})

    @classmethod
    def validate_strategy_type(cls, strategy_type: str) -> bool:
        """Validate if a strategy type is supported.

        Args:
            strategy_type: Strategy type to validate

        Returns:
            True if supported, False otherwise
        """
        if strategy_type.startswith("custom_"):
            return True
        return strategy_type in cls.STRATEGY_LABEL_TO_TYPE
