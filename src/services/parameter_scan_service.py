"""
Parameter Scan Service

Handles parameter space definition and generates parameter combinations
for optimization using random search.
"""

import random
import logging
from typing import Dict, List, Any, Generator, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ParameterRange:
    """
    Defines a parameter search space.

    A parameter range can be either:
    - A range with min, max, step (will generate values in that range)
    - A custom list of explicit values
    """
    indicator: str  # e.g., "SMA", "RSI", "MACD"
    parameter_name: str  # e.g., "fast_window", "slow_window", "period"
    values: List[int]  # List of possible values for this parameter

    @classmethod
    def from_range(
        cls,
        indicator: str,
        param_name: str,
        min_val: int,
        max_val: int,
        step: int = 1
    ) -> "ParameterRange":
        """
        Create a ParameterRange from min/max/step specification.

        Args:
            indicator: Indicator name
            param_name: Parameter name
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            step: Step size between values

        Returns:
            ParameterRange with generated values
        """
        values = list(range(min_val, max_val + 1, step))
        return cls(
            indicator=indicator,
            parameter_name=param_name,
            values=values
        )

    @classmethod
    def from_custom_values(
        cls,
        indicator: str,
        param_name: str,
        values: List[int]
    ) -> "ParameterRange":
        """
        Create a ParameterRange from a custom list of values.

        Args:
            indicator: Indicator name
            param_name: Parameter name
            values: List of possible values

        Returns:
            ParameterRange with custom values
        """
        return cls(
            indicator=indicator,
            parameter_name=param_name,
            values=values
        )

    def __len__(self) -> int:
        """Return the number of possible values for this parameter."""
        return len(self.values)

    def random_value(self) -> int:
        """Return a random value from this parameter's range."""
        return random.choice(self.values)

    def __repr__(self) -> str:
        return f"ParameterRange({self.indicator}.{self.parameter_name}, values={self.values})"


@dataclass
class ParameterCombination:
    """
    Represents a single combination of parameter values.
    """
    id: str  # Unique identifier for this combination
    parameters: Dict[str, int]  # Map of parameter_name -> value

    def __repr__(self) -> str:
        return f"ParameterCombination({self.id}, {self.parameters})"


@dataclass
class ScanStatistics:
    """Statistics about the parameter space."""
    total_combinations: int
    parameters: Dict[str, Dict[str, Any]]  # Statistics per parameter
    estimated_time_seconds: Optional[float] = None

    def __repr__(self) -> str:
        return f"ScanStatistics(total={self.total_combinations}, params={self.parameters})"


class ParameterScanService:
    """
    Service for managing parameter search spaces and generating parameter combinations.

    Supports:
    - Defining parameter ranges
    - Generating random parameter combinations
    - Calculating search space statistics
    """

    def __init__(self):
        self.parameter_ranges: List[ParameterRange] = []
        self._combination_cache: Optional[List[tuple]] = None

    def add_parameter_range(self, param_range: ParameterRange) -> None:
        """
        Add a parameter range to the search space.

        Args:
            param_range: ParameterRange to add
        """
        self.parameter_ranges.append(param_range)
        self._combination_cache = None  # Invalidate cache

    def clear_parameter_ranges(self) -> None:
        """Clear all parameter ranges."""
        self.parameter_ranges = []
        self._combination_cache = None

    def get_parameter_names(self) -> List[str]:
        """Get list of all parameter names in the search space."""
        return [p.parameter_name for p in self.parameter_ranges]

    def get_statistics(self, estimated_time_per_backtest: float = 0.5) -> ScanStatistics:
        """
        Calculate statistics about the parameter search space.

        Args:
            estimated_time_per_backtest: Estimated time per backtest in seconds

        Returns:
            ScanStatistics object
        """
        if not self.parameter_ranges:
            return ScanStatistics(
                total_combinations=0,
                parameters={}
            )

        # Calculate total combinations (cartesian product)
        total_combinations = 1
        param_stats = {}

        for param_range in self.parameter_ranges:
            count = len(param_range)
            total_combinations *= count

            param_stats[param_range.parameter_name] = {
                "indicator": param_range.indicator,
                "min": min(param_range.values),
                "max": max(param_range.values),
                "count": count,
                "values": param_range.values
            }

        # Estimate time
        estimated_time = None
        if total_combinations > 0:
            estimated_time = total_combinations * estimated_time_per_backtest

        return ScanStatistics(
            total_combinations=total_combinations,
            parameters=param_stats,
            estimated_time_seconds=estimated_time
        )

    def generate_random_combinations(
        self,
        n_samples: int,
        seed: Optional[int] = None
    ) -> Generator[ParameterCombination, None, None]:
        """
        Generate random parameter combinations.

        Args:
            n_samples: Number of random samples to generate
            seed: Random seed for reproducibility (optional)

        Yields:
            ParameterCombination objects

        Examples:
            >>> service = ParameterScanService()
            >>> service.add_parameter_range(ParameterRange.from_range("SMA", "fast_window", 5, 20, 5))
            >>> service.add_parameter_range(ParameterRange.from_range("SMA", "slow_window", 30, 50, 5))
            >>> for combo in service.generate_random_combinations(10):
            ...     print(combo)
        """
        if seed is not None:
            random.seed(seed)

        if not self.parameter_ranges:
            logger.warning("No parameter ranges defined, generating empty combinations")
            return

        param_names = [p.parameter_name for p in self.parameter_ranges]

        for i in range(n_samples):
            # Randomly sample each parameter
            params = {
                name: param_range.random_value()
                for name, param_range in zip(param_names, self.parameter_ranges)
            }

            yield ParameterCombination(
                id=f"combo_{i}",
                parameters=params
            )

    def generate_grid_combinations(
        self,
        max_combinations: Optional[int] = None
    ) -> Generator[ParameterCombination, None, None]:
        """
        Generate all parameter combinations using grid search.

        Warning: This can generate a very large number of combinations!
        Consider using max_combinations to limit the output.

        Args:
            max_combinations: Maximum number of combinations to generate (None for unlimited)

        Yields:
            ParameterCombination objects
        """
        import itertools

        if not self.parameter_ranges:
            return

        param_names = [p.parameter_name for p in self.parameter_ranges]
        param_values = [p.values for p in self.parameter_ranges]

        count = 0
        for i, combination in enumerate(itertools.product(*param_values)):
            if max_combinations is not None and count >= max_combinations:
                break

            params = dict(zip(param_names, combination))
            yield ParameterCombination(
                id=f"combo_{i}",
                parameters=params
            )
            count += 1

    def validate_configuration(self) -> List[str]:
        """
        Validate the current parameter scan configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.parameter_ranges:
            errors.append("No parameter ranges defined")
            return errors

        # Check for duplicate parameter names
        param_names = [p.parameter_name for p in self.parameter_ranges]
        duplicates = [name for name in set(param_names) if param_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate parameter names: {duplicates}")

        # Check each parameter range
        for param_range in self.parameter_ranges:
            if not param_range.values:
                errors.append(f"Parameter '{param_range.parameter_name}' has no values")

            if not param_range.parameter_name:
                errors.append(f"Parameter for indicator '{param_range.indicator}' has no name")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the current configuration to a dictionary for serialization.

        Returns:
            Dictionary representation of the service state
        """
        return {
            "parameter_ranges": [
                {
                    "indicator": pr.indicator,
                    "parameter_name": pr.parameter_name,
                    "values": pr.values
                }
                for pr in self.parameter_ranges
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterScanService":
        """
        Create a ParameterScanService from a dictionary.

        Args:
            data: Dictionary representation of the service

        Returns:
            ParameterScanService instance
        """
        service = cls()

        for pr_data in data.get("parameter_ranges", []):
            param_range = ParameterRange(
                indicator=pr_data["indicator"],
                parameter_name=pr_data["parameter_name"],
                values=pr_data["values"]
            )
            service.add_parameter_range(param_range)

        return service


def create_scan_service_from_config(
    parameter_ranges_config: List[Dict[str, Any]]
) -> ParameterScanService:
    """
    Create a ParameterScanService from a configuration dictionary.

    Args:
        parameter_ranges_config: List of parameter range configurations

    Returns:
        Configured ParameterScanService

    Examples:
        >>> config = [
        ...     {
        ...         "indicator": "SMA",
        ...         "parameter_name": "fast_window",
        ...         "type": "range",
        ...         "min": 5,
        ...         "max": 20,
        ...         "step": 5
        ...     }
        ... ]
        >>> service = create_scan_service_from_config(config)
    """
    service = ParameterScanService()

    for pr_config in parameter_ranges_config:
        if pr_config["type"] == "range":
            param_range = ParameterRange.from_range(
                indicator=pr_config["indicator"],
                param_name=pr_config["parameter_name"],
                min_val=pr_config["min"],
                max_val=pr_config["max"],
                step=pr_config.get("step", 1)
            )
        elif pr_config["type"] == "custom":
            param_range = ParameterRange.from_custom_values(
                indicator=pr_config["indicator"],
                param_name=pr_config["parameter_name"],
                values=pr_config["values"]
            )
        else:
            logger.warning(f"Unknown parameter range type: {pr_config['type']}")
            continue

        service.add_parameter_range(param_range)

    return service
