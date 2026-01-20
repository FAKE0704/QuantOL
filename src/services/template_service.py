"""
Rule Template Service

Handles rule template rendering and parameter substitution.
Converts rule templates with placeholders like {var_name} into executable rules.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VariableDefinition:
    """Variable definition in a template"""
    name: str
    var_type: str  # "int" or "float"
    default_value: Any
    description: str


@dataclass
class RuleTemplate:
    """Rule template definition"""
    template_id: str
    name: str
    description: Optional[str] = None
    open_rule_template: Optional[str] = None
    close_rule_template: Optional[str] = None
    buy_rule_template: Optional[str] = None
    sell_rule_template: Optional[str] = None
    variables: Dict[str, VariableDefinition] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


class TemplateService:
    """
    Service for rendering rule templates with parameter substitution.

    Supports:
    - Simple variable substitution: {var_name} -> value
    - Type validation (int/float)
    - Template validation
    """

    # Pattern to match template variables like {var_name}
    VARIABLE_PATTERN = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """
        Extract all variable names from a template string.

        Args:
            template: Template string with placeholders like {var_name}

        Returns:
            List of variable names found in the template

        Examples:
            >>> TemplateService.extract_variables("SMA(close, {fast_window}) > SMA(close, {slow_window})")
            ['fast_window', 'slow_window']
        """
        return TemplateService.VARIABLE_PATTERN.findall(template)

    @staticmethod
    def render_template(template: str, params: Dict[str, Any]) -> str:
        """
        Render a template by replacing variable placeholders with actual values.

        Args:
            template: Template string with placeholders like {var_name}
            params: Dictionary mapping variable names to values

        Returns:
            Rendered template string with placeholders replaced

        Raises:
            ValueError: If a required variable is missing from params

        Examples:
            >>> TemplateService.render_template(
            ...     "SMA(close, {fast_window}) > SMA(close, {slow_window})",
            ...     {"fast_window": 10, "slow_window": 30}
            ... )
            'SMA(close, 10) > SMA(close, 30)'
        """
        result = template

        # Find all variables in the template
        variables = TemplateService.extract_variables(template)

        # Check for missing variables
        missing_vars = set(variables) - set(params.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        # Replace each variable
        for var_name in variables:
            value = params[var_name]
            # Convert to string and replace
            result = result.replace(f"{{{var_name}}}", str(value))

        return result

    @staticmethod
    def render_rules(
        rule_templates: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render multiple rule templates with the same parameters.

        Args:
            rule_templates: Dictionary of rule type to template string
                           e.g., {"open_rule": "SMA(close, {fast_window}) > 0"}
            params: Parameter dictionary

        Returns:
            Dictionary of rendered rules

        Examples:
            >>> TemplateService.render_rules(
            ...     {"open_rule": "SMA(close, {fast}) > SMA(close, {slow})"},
            ...     {"fast": 10, "slow": 30}
            ... )
            {'open_rule': 'SMA(close, 10) > SMA(close, 30)'}
        """
        rendered = {}
        for rule_type, template in rule_templates.items():
            if template:  # Only render non-empty templates
                try:
                    rendered[rule_type] = TemplateService.render_template(template, params)
                except ValueError as e:
                    logger.warning(f"Failed to render {rule_type}: {e}")
                    rendered[rule_type] = template  # Keep original if rendering fails
            else:
                rendered[rule_type] = ""
        return rendered

    @staticmethod
    def validate_template(template: str, variables: Dict[str, VariableDefinition]) -> List[str]:
        """
        Validate a template against variable definitions.

        Args:
            template: Template string to validate
            variables: Dictionary of variable definitions

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Extract variables from template
        template_vars = set(TemplateService.extract_variables(template))
        defined_vars = set(variables.keys())

        # Check for undefined variables
        undefined = template_vars - defined_vars
        if undefined:
            errors.append(f"Undefined variables in template: {undefined}")

        # Check for unused variables (warning only)
        unused = defined_vars - template_vars
        if unused:
            logger.warning(f"Unused variable definitions: {unused}")

        return errors

    @staticmethod
    def validate_parameters(
        params: Dict[str, Any],
        variables: Dict[str, VariableDefinition]
    ) -> List[str]:
        """
        Validate parameter values against variable definitions.

        Args:
            params: Parameter values to validate
            variables: Variable definitions

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for var_name, var_def in variables.items():
            if var_name not in params:
                errors.append(f"Missing required parameter: {var_name}")
                continue

            value = params[var_name]

            # Type validation
            if var_def.var_type == "int":
                if not isinstance(value, int):
                    errors.append(f"Parameter '{var_name}' must be an integer, got {type(value).__name__}")
            elif var_def.var_type == "float":
                if not isinstance(value, (int, float)):
                    errors.append(f"Parameter '{var_name}' must be a number, got {type(value).__name__}")

            # Range validation for window parameters (should be positive)
            if isinstance(value, (int, float)) and value <= 0:
                errors.append(f"Parameter '{var_name}' must be positive, got {value}")

        return errors

    @staticmethod
    def create_template_from_dict(template_dict: Dict[str, Any]) -> RuleTemplate:
        """
        Create a RuleTemplate object from a dictionary (e.g., from JSON).

        Args:
            template_dict: Dictionary containing template definition

        Returns:
            RuleTemplate object
        """
        variables = {}
        if "variables" in template_dict:
            for var_name, var_def in template_dict["variables"].items():
                variables[var_name] = VariableDefinition(
                    name=var_name,
                    var_type=var_def.get("type", "int"),
                    default_value=var_def.get("default_value"),
                    description=var_def.get("description", "")
                )

        return RuleTemplate(
            template_id=template_dict.get("template_id", ""),
            name=template_dict.get("name", ""),
            description=template_dict.get("description"),
            open_rule_template=template_dict.get("open_rule_template"),
            close_rule_template=template_dict.get("close_rule_template"),
            buy_rule_template=template_dict.get("buy_rule_template"),
            sell_rule_template=template_dict.get("sell_rule_template"),
            variables=variables
        )


# Predefined strategy templates library
PREDEFINED_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ma_crossover": {
        "template_id": "ma_crossover",
        "name": "Moving Average Crossover",
        "description": "Classic MA crossover strategy - buy when fast MA crosses above slow MA",
        "open_rule_template": "(REF(SMA(close, {fast_window}), 1) < REF(SMA(close, {slow_window}), 1)) & (SMA(close, {fast_window}) > SMA(close, {slow_window}))",
        "close_rule_template": "(REF(SMA(close, {fast_window}), 1) > REF(SMA(close, {slow_window}), 1)) & (SMA(close, {fast_window}) < SMA(close, {slow_window}))",
        "variables": {
            "fast_window": {
                "type": "int",
                "default_value": 5,
                "description": "Fast moving average window"
            },
            "slow_window": {
                "type": "int",
                "default_value": 20,
                "description": "Slow moving average window"
            }
        }
    },
    "rsi_overbought_oversold": {
        "template_id": "rsi_overbought_oversold",
        "name": "RSI Overbought/Oversold",
        "description": "Buy when RSI exits oversold, sell when enters overbought",
        "open_rule_template": "(REF(RSI(close, {period}), 1) < {oversold_threshold}) & (RSI(close, {period}) >= {oversold_threshold})",
        "close_rule_template": "(REF(RSI(close, {period}), 1) >= {overbought_threshold}) & (RSI(close, {period}) < {overbought_threshold})",
        "variables": {
            "period": {
                "type": "int",
                "default_value": 14,
                "description": "RSI calculation period"
            },
            "oversold_threshold": {
                "type": "int",
                "default_value": 30,
                "description": "Oversold threshold"
            },
            "overbought_threshold": {
                "type": "int",
                "default_value": 70,
                "description": "Overbought threshold"
            }
        }
    },
    "macd_crossover": {
        "template_id": "macd_crossover",
        "name": "MACD Crossover",
        "description": "MACD signal line crossover strategy",
        "open_rule_template": "MACD(close, {fast_period}, {slow_period}, {signal_period}) > MACD_SIGNAL(close, {fast_period}, {slow_period}, {signal_period})",
        "close_rule_template": "MACD(close, {fast_period}, {slow_period}, {signal_period}) < MACD_SIGNAL(close, {fast_period}, {slow_period}, {signal_period})",
        "variables": {
            "fast_period": {
                "type": "int",
                "default_value": 12,
                "description": "MACD fast EMA period"
            },
            "slow_period": {
                "type": "int",
                "default_value": 26,
                "description": "MACD slow EMA period"
            },
            "signal_period": {
                "type": "int",
                "default_value": 9,
                "description": "MACD signal line period"
            }
        }
    }
}


def get_template(template_id: str) -> Optional[RuleTemplate]:
    """
    Get a predefined template by ID.

    Args:
        template_id: Template identifier

    Returns:
        RuleTemplate object or None if not found
    """
    if template_id in PREDEFINED_TEMPLATES:
        return TemplateService.create_template_from_dict(PREDEFINED_TEMPLATES[template_id])
    return None


def list_templates() -> List[str]:
    """List all available template IDs."""
    return list(PREDEFINED_TEMPLATES.keys())
