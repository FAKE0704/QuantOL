"""
Parameter Extractor Service

Automatically extract and identify optimizable parameters from trading rules.

Example:
    Input: "SQRT(high*low, 2) - VWAP(15) < REF(Q(SQRT(high*low, 2) - VWAP(15), 0.2, 10), 1)"
    Output: [
        {"indicator": "VWAP", "parameter_name": "period", "current_value": 15},
        {"indicator": "Q", "parameter_name": "quantile", "current_value": 0.2},
        {"indicator": "Q", "parameter_name": "period", "current_value": 10},
        {"indicator": "REF", "parameter_name": "offset", "current_value": 1}
    ]
"""

import re
import logging
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class ExtractedParameter:
    """A parameter extracted from a trading rule."""
    indicator: str  # e.g., "VWAP", "Q", "REF"
    parameter_name: str  # e.g., "period", "quantile", "offset"
    current_value: Any  # Current value in the rule
    parameter_type: str  # "int" or "float"
    full_match: str  # The complete function call string
    suggested_range_type: str  # "range" or "custom"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ParameterType(Enum):
    """Parameter type classification."""
    WINDOW = "window"  # Window size (int): SMA, EMA, VWAP, etc.
    QUANTILE = "quantile"  # Quantile value (float 0-1): Q function
    OFFSET = "offset"  # Lookback offset (int): REF function
    MULTI_PARAM = "multi_param"  # Multiple parameters: MACD, etc.


class ParameterExtractor:
    """
    Extract optimizable parameters from trading rule strings.

    Uses regex pattern matching to identify function calls and their parameters.
    """

    # Indicator registry: indicator -> (parameter_names, parameter_types)
    INDICATOR_REGISTRY: Dict[str, Tuple[List[str], List[str]]] = {
        # Single parameter indicators
        "SMA": (["period"], [ParameterType.WINDOW.value]),
        "EMA": (["period"], [ParameterType.WINDOW.value]),
        "RSI": (["period"], [ParameterType.WINDOW.value]),
        "VWAP": (["period"], [ParameterType.WINDOW.value]),
        "C_P": (["period"], [ParameterType.WINDOW.value]),
        "STD": (["period"], [ParameterType.WINDOW.value]),
        "ATR": (["period"], [ParameterType.WINDOW.value]),

        # Multi-parameter indicators
        "MACD": (["fast_period", "slow_period", "signal_period"],
                 [ParameterType.WINDOW.value, ParameterType.WINDOW.value, ParameterType.WINDOW.value]),

        # Quantile function
        "Q": (["quantile", "period"],
              [ParameterType.QUANTILE.value, ParameterType.WINDOW.value]),

        # Reference function
        "REF": (["offset"], [ParameterType.OFFSET.value]),
    }

    # Pattern for matching function calls
    # Matches: FUNCTION_NAME(arg1, arg2, ...)
    FUNCTION_PATTERN = re.compile(r'([A-Z_][A-Z0-9_]*)\s*\(([^)]*)\)')

    @classmethod
    def extract_from_rule(cls, rule: str) -> List[ExtractedParameter]:
        """
        Extract all optimizable parameters from a single rule string.

        Args:
            rule: Trading rule string

        Returns:
            List of ExtractedParameter objects

        Examples:
            >>> extractor = ParameterExtractor()
            >>> params = extractor.extract_from_rule("VWAP(15) > SMA(5, 20)")
            >>> len(params)
            3
        """
        if not rule or not rule.strip():
            return []

        results: List[ExtractedParameter] = []

        for match in cls.FUNCTION_PATTERN.finditer(rule):
            indicator = match.group(1).upper()

            # Check if this indicator is in our registry
            if indicator not in cls.INDICATOR_REGISTRY:
                continue

            param_names, param_types = cls.INDICATOR_REGISTRY[indicator]

            # Parse arguments
            args_str = match.group(2).strip()
            if not args_str:
                continue

            # Split by comma, handle nested parentheses
            args = cls._parse_arguments(args_str)

            # Extract each parameter
            for i, (param_name, param_type) in enumerate(zip(param_names, param_types)):
                if i >= len(args):
                    break

                arg_value = args[i].strip()
                parsed_value = cls._parse_value(arg_value, param_type)

                if parsed_value is not None:
                    results.append(ExtractedParameter(
                        indicator=indicator,
                        parameter_name=param_name,
                        current_value=parsed_value,
                        parameter_type="int" if param_type in [ParameterType.WINDOW.value, ParameterType.OFFSET.value] else "float",
                        full_match=match.group(0),
                        suggested_range_type=cls._get_suggested_range_type(param_type, parsed_value)
                    ))

        return results

    @classmethod
    def extract_from_rules(cls, rules: Dict[str, str]) -> Dict[str, List[ExtractedParameter]]:
        """
        Extract parameters from multiple rules.

        Args:
            rules: Dictionary of rule_type -> rule_content

        Returns:
            Dictionary of rule_type -> list of extracted parameters
        """
        results = {}

        for rule_type, rule_content in rules.items():
            if rule_content and rule_content.strip():
                extracted = cls.extract_from_rule(rule_content)
                if extracted:
                    results[rule_type] = extracted

        return results

    @classmethod
    def get_unique_parameters(cls, rules: Dict[str, str]) -> List[ExtractedParameter]:
        """
        Get unique parameters from all rules (deduplicated).

        Args:
            rules: Dictionary of rules

        Returns:
            List of unique ExtractedParameter objects
        """
        all_params: List[ExtractedParameter] = []

        for rule_content in rules.values():
            if rule_content and rule_content.strip():
                all_params.extend(cls.extract_from_rule(rule_content))

        # Deduplicate by indicator + parameter_name
        unique_params = cls._deduplicate_parameters(all_params)
        return unique_params

    @classmethod
    def suggest_optimization_range(cls, param: ExtractedParameter) -> Dict[str, Any]:
        """
        Suggest an optimization range for a parameter.

        Args:
            param: ExtractedParameter object

        Returns:
            Dictionary with range configuration
        """
        current_value = float(param.current_value)

        if param.suggested_range_type == "custom":
            # For quantile parameters, use predefined list
            return {
                "type": "custom",
                "values": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            }

        # For window/offset parameters, generate range
        if current_value <= 1:
            # Small values
            min_val = max(2, int(current_value))
            max_val = min_val * 5
            step_val = 1
        else:
            # Larger values
            min_val = max(2, int(current_value * 0.5))
            max_val = int(current_value * 2)
            step_val = max(1, int(current_value * 0.1))

        return {
            "type": "range",
            "min": min_val,
            "max": max_val,
            "step": step_val
        }

    @classmethod
    def _parse_arguments(cls, args_str: str) -> List[str]:
        """
        Parse function arguments, handling nested parentheses.

        Args:
            args_str: String of arguments

        Returns:
            List of argument strings
        """
        args = []
        current_arg = []
        paren_depth = 0

        for char in args_str:
            if char == '(':
                paren_depth += 1
                current_arg.append(char)
            elif char == ')':
                paren_depth -= 1
                current_arg.append(char)
            elif char == ',' and paren_depth == 0:
                args.append(''.join(current_arg).strip())
                current_arg = []
            else:
                current_arg.append(char)

        if current_arg:
            args.append(''.join(current_arg).strip())

        return args

    @classmethod
    def _parse_value(cls, value_str: str, param_type: str) -> Any:
        """
        Parse a string value to the appropriate type.

        Args:
            value_str: String value to parse
            param_type: Expected parameter type

        Returns:
            Parsed value or None if parsing fails
        """
        value_str = value_str.strip()

        try:
            if param_type == ParameterType.WINDOW.value or param_type == ParameterType.OFFSET.value:
                return int(float(value_str))
            elif param_type == ParameterType.QUANTILE.value:
                return float(value_str)
            else:
                return float(value_str)
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse value: {value_str} as {param_type}")
            return None

    @classmethod
    def _get_suggested_range_type(cls, param_type: str, value: Any) -> str:
        """Determine if parameter should use range or custom list."""
        if param_type == ParameterType.QUANTILE.value:
            return "custom"
        return "range"

    @classmethod
    def _deduplicate_parameters(cls, params: List[ExtractedParameter]) -> List[ExtractedParameter]:
        """
        Remove duplicate parameters based on indicator + parameter_name.

        Args:
            params: List of parameters

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for param in params:
            key = f"{param.indicator}_{param.parameter_name}"
            if key not in seen:
                seen.add(key)
                unique.append(param)

        return unique


# Convenience functions
def extract_parameters(rule: str) -> List[Dict[str, Any]]:
    """Extract parameters from a single rule (convenience function)."""
    extractor = ParameterExtractor()
    params = extractor.extract_from_rule(rule)
    return [p.to_dict() for p in params]


def extract_all_parameters(rules: Dict[str, str]) -> List[Dict[str, Any]]:
    """Extract all unique parameters from rules (convenience function)."""
    extractor = ParameterExtractor()
    params = extractor.get_unique_parameters(rules)
    return [p.to_dict() for p in params]


def get_suggested_ranges(rules: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Get suggested optimization ranges for all parameters in rules.

    Returns a list of parameter range configurations ready for the optimization API.

    Args:
        rules: Dictionary of trading rules

    Returns:
        List of parameter range configurations

    Examples:
        >>> rules = {
        ...     "open_rule": "VWAP(15) > SMA(5, 20)"
        ... }
        >>> ranges = get_suggested_ranges(rules)
        >>> len(ranges) >= 2
        True
    """
    extractor = ParameterExtractor()
    params = extractor.get_unique_parameters(rules)

    range_configs = []
    for param in params:
        range_suggestion = extractor.suggest_optimization_range(param)

        config = {
            "indicator": param.indicator,
            "parameter_name": param.parameter_name,
            "type": range_suggestion["type"],
        }

        if range_suggestion["type"] == "range":
            config["min"] = range_suggestion["min"]
            config["max"] = range_suggestion["max"]
            config["step"] = range_suggestion["step"]
        else:
            config["values"] = range_suggestion["values"]

        range_configs.append(config)

    return range_configs
