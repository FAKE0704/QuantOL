"""
Optimization Service

Coordinates parameter optimization workflow including:
1. Parameter space configuration
2. Random search parameter scanning
3. Backtest execution for each parameter combination
4. Result ranking and selection
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from src.services.template_service import TemplateService
from src.services.parameter_scan_service import (
    ParameterScanService,
    ParameterCombination,
    create_scan_service_from_config
)
from src.core.strategy.backtesting import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    """Result of screening a single parameter combination."""
    combination_id: str
    parameters: Dict[str, int]
    metrics: Dict[str, float]
    rank: int = 0

    def __repr__(self) -> str:
        return f"ScreeningResult(id={self.combination_id}, rank={self.rank}, sharpe={self.metrics.get('sharpe_ratio', 0):.2f})"


@dataclass
class OptimizationConfig:
    """Configuration for parameter optimization."""
    # Parameter search spaces
    parameter_ranges: List[Dict[str, Any]]

    # Scan method
    scan_method: str = "random"  # Currently only "random" is supported
    random_samples: int = 50

    # Screening configuration
    screening_start: str = ""  # Format: YYYYMMDD
    screening_end: str = ""    # Format: YYYYMMDD
    screening_metric: str = "sharpe_ratio"  # "sharpe_ratio" | "total_return"
    top_n: int = 5

    # Performance thresholds (optional)
    min_sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    min_win_rate: Optional[float] = None


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    optimization_id: str
    status: str  # "pending", "screening", "completed", "failed"

    # Results
    screening_results: List[ScreeningResult] = field(default_factory=list)
    best_parameters: Optional[Dict[str, int]] = None
    best_metrics: Optional[Dict[str, float]] = None

    # Progress tracking
    progress: Dict[str, Any] = field(default_factory=dict)

    # Error handling
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "optimization_id": self.optimization_id,
            "status": self.status,
            "screening_results": [
                {
                    "combination_id": r.combination_id,
                    "parameters": r.parameters,
                    "metrics": r.metrics,
                    "rank": r.rank
                }
                for r in self.screening_results
            ],
            "best_parameters": self.best_parameters,
            "best_metrics": self.best_metrics,
            "progress": self.progress,
            "error": self.error
        }


class OptimizationService:
    """
    Service for running parameter optimization.

    Workflow:
    1. Parse parameter range configuration
    2. Generate random parameter combinations
    3. For each combination:
       a. Render rule templates with parameters
       b. Run backtest
       c. Collect performance metrics
    4. Rank results by screening metric
    5. Return top N candidates
    """

    def __init__(self):
        self.scan_service: Optional[ParameterScanService] = None
        self._optimization_tasks: Dict[str, asyncio.Task] = {}

    def _setup_parameter_ranges(self, ranges_config: List[Dict[str, Any]]) -> None:
        """
        Set up parameter search space from configuration.

        Args:
            ranges_config: List of parameter range configurations
        """
        self.scan_service = create_scan_service_from_config(ranges_config)

        # Validate configuration
        errors = self.scan_service.validate_configuration()
        if errors:
            raise ValueError(f"Invalid parameter configuration: {errors}")

        logger.info(f"Parameter scan service configured with {len(self.scan_service.parameter_ranges)} parameters")

    async def run_optimization(
        self,
        config: OptimizationConfig,
        rule_templates: Dict[str, str],
        base_config: BacktestConfig,
        data: pd.DataFrame,
        progress_callback: Optional[Callable[[int, int, ScreeningResult], None]] = None
    ) -> OptimizationResult:
        """
        Run parameter optimization.

        Args:
            config: Optimization configuration
            rule_templates: Rule templates with variable placeholders
            base_config: Base backtest configuration
            data: Historical data for backtesting
            progress_callback: Optional callback for progress updates
                               Args: (current_step, total_steps, latest_result)

        Returns:
            OptimizationResult with screening results
        """
        optimization_id = f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = OptimizationResult(
            optimization_id=optimization_id,
            status="screening"
        )

        try:
            # Step 1: Set up parameter search space
            self._setup_parameter_ranges(config.parameter_ranges)

            # Step 2: Generate parameter combinations
            total_combinations = config.random_samples
            combinations = list(
                self.scan_service.generate_random_combinations(
                    n_samples=total_combinations,
                    seed=42  # For reproducibility
                )
            )

            logger.info(f"Generated {len(combinations)} parameter combinations for optimization")

            # Step 3: Run backtest for each combination
            screening_results = []

            for i, combo in enumerate(combinations):
                # Update progress
                result.progress = {
                    "current_stage": "screening",
                    "current_step": i + 1,
                    "total_steps": total_combinations,
                    "percentage": ((i + 1) / total_combinations) * 100
                }

                try:
                    # Render rules with parameters
                    rendered_rules = TemplateService.render_rules(rule_templates, combo.parameters)

                    # Create backtest config for this combination
                    combo_config = self._create_backtest_config(
                        base_config=base_config,
                        parameters=combo.parameters,
                        rendered_rules=rendered_rules
                    )

                    # Run backtest
                    screening_result = await self._run_single_backtest(
                        combination=combo,
                        config=combo_config,
                        data=data,
                        screening_start=config.screening_start,
                        screening_end=config.screening_end
                    )

                    screening_results.append(screening_result)

                    # Progress callback
                    if progress_callback:
                        progress_callback(i + 1, total_combinations, screening_result)

                except Exception as e:
                    logger.error(f"Failed to backtest combination {combo.id}: {e}")
                    # Continue with next combination
                    continue

            # Step 4: Rank results
            ranked_results = self._rank_results(
                screening_results,
                metric=config.screening_metric,
                thresholds={
                    "min_sharpe": config.min_sharpe,
                    "max_drawdown": config.max_drawdown,
                    "min_win_rate": config.min_win_rate
                }
            )

            # Step 5: Select top N
            top_results = ranked_results[:config.top_n]

            result.screening_results = top_results
            result.status = "completed"

            if top_results:
                result.best_parameters = top_results[0].parameters
                result.best_metrics = top_results[0].metrics

            logger.info(f"Optimization completed. Best result: {top_results[0] if top_results else 'None'}")

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            result.status = "failed"
            result.error = str(e)

        return result

    def _create_backtest_config(
        self,
        base_config: BacktestConfig,
        parameters: Dict[str, int],
        rendered_rules: Dict[str, str]
    ) -> BacktestConfig:
        """
        Create a backtest configuration for a specific parameter combination.

        Args:
            base_config: Base configuration
            parameters: Parameter values
            rendered_rules: Rendered rule strings

        Returns:
            BacktestConfig for this combination
        """
        # Create a new config with rendered rules
        config_dict = {
            "start_date": base_config.start_date,
            "end_date": base_config.end_date,
            "target_symbol": base_config.target_symbol,
            "frequency": base_config.frequency,
            "initial_capital": base_config.initial_capital,
            "commission_rate": base_config.commission_rate,
            "slippage": base_config.slippage,
            "position_strategy_type": base_config.position_strategy_type,
            "position_strategy_params": base_config.position_strategy_params,
            "custom_rules": rendered_rules
        }

        # Handle target_symbols if present
        if hasattr(base_config, 'target_symbols') and base_config.target_symbols:
            config_dict["target_symbols"] = base_config.target_symbols

        return BacktestConfig(**config_dict)

    async def _run_single_backtest(
        self,
        combination: ParameterCombination,
        config: BacktestConfig,
        data: pd.DataFrame,
        screening_start: str,
        screening_end: str
    ) -> ScreeningResult:
        """
        Run a single backtest for a parameter combination.

        Args:
            combination: Parameter combination
            config: Backtest configuration
            data: Full historical data
            screening_start: Screening start date (YYYYMMDD)
            screening_end: Screening end date (YYYYMMDD)

        Returns:
            ScreeningResult with performance metrics
        """
        # Filter data to screening period
        screening_data = data[
            (data.index >= screening_start) &
            (data.index <= screening_end)
        ].copy()

        if screening_data.empty:
            raise ValueError(f"No data available for screening period {screening_start} to {screening_end}")

        # Create backtest engine
        engine = BacktestEngine(config, screening_data)

        # Run backtest (synchronous for now, can be made async)
        start_date = datetime.strptime(screening_start, "%Y%m%d")
        end_date = datetime.strptime(screening_end, "%Y%m%d")
        await engine.run(start_date, end_date)

        # Get results
        results = engine.get_results()
        metrics = results.get("performance_metrics", {})

        return ScreeningResult(
            combination_id=combination.id,
            parameters=combination.parameters,
            metrics=metrics
        )

    def _rank_results(
        self,
        results: List[ScreeningResult],
        metric: str = "sharpe_ratio",
        thresholds: Optional[Dict[str, Optional[float]]] = None
    ) -> List[ScreeningResult]:
        """
        Rank screening results by metric and apply thresholds.

        Args:
            results: List of screening results
            metric: Metric to rank by
            thresholds: Optional performance thresholds

        Returns:
            Ranked and filtered list of results
        """
        # Apply thresholds if specified
        filtered = results
        if thresholds:
            filtered = [
                r for r in results
                if self._meets_thresholds(r.metrics, thresholds)
            ]

        # Sort by metric (descending for sharpe_ratio and total_return)
        reverse = metric in ["sharpe_ratio", "total_return", "win_rate"]
        sorted_results = sorted(
            filtered,
            key=lambda r: r.metrics.get(metric, -float('inf')),
            reverse=reverse
        )

        # Assign ranks
        for i, result in enumerate(sorted_results):
            result.rank = i + 1

        return sorted_results

    def _meets_thresholds(
        self,
        metrics: Dict[str, float],
        thresholds: Dict[str, Optional[float]]
    ) -> bool:
        """
        Check if metrics meet the specified thresholds.

        Args:
            metrics: Performance metrics
            thresholds: Threshold requirements

        Returns:
            True if all thresholds are met
        """
        # Minimum Sharpe ratio
        if thresholds.get("min_sharpe") is not None:
            if metrics.get("sharpe_ratio", -float('inf')) < thresholds["min_sharpe"]:
                return False

        # Maximum drawdown
        if thresholds.get("max_drawdown") is not None:
            # Note: drawdown is negative, so we use >= for "not worse than"
            if metrics.get("max_drawdown_pct", 0) < -thresholds["max_drawdown"]:
                return False

        # Minimum win rate
        if thresholds.get("min_win_rate") is not None:
            if metrics.get("win_rate", 0) < thresholds["min_win_rate"]:
                return False

        return True

    async def run_parallel_optimization(
        self,
        config: OptimizationConfig,
        rule_templates: Dict[str, str],
        base_config: BacktestConfig,
        data: pd.DataFrame,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable[[int, int, ScreeningResult], None]] = None
    ) -> OptimizationResult:
        """
        Run optimization with parallel backtest execution.

        This is an optimized version that runs multiple backtests concurrently.

        Args:
            config: Optimization configuration
            rule_templates: Rule templates
            base_config: Base backtest configuration
            data: Historical data
            max_concurrent: Maximum concurrent backtests
            progress_callback: Optional progress callback

        Returns:
            OptimizationResult
        """
        optimization_id = f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = OptimizationResult(
            optimization_id=optimization_id,
            status="screening"
        )

        try:
            # Set up parameter search space
            self._setup_parameter_ranges(config.parameter_ranges)

            # Generate combinations
            total_combinations = config.random_samples
            combinations = list(
                self.scan_service.generate_random_combinations(
                    n_samples=total_combinations,
                    seed=42
                )
            )

            # Semaphore to limit concurrent tasks
            semaphore = asyncio.Semaphore(max_concurrent)

            async def run_with_limit(
                combo: ParameterCombination,
                index: int
            ) -> Optional[ScreeningResult]:
                async with semaphore:
                    try:
                        # Render rules
                        rendered_rules = TemplateService.render_rules(rule_templates, combo.parameters)

                        # Create config
                        combo_config = self._create_backtest_config(
                            base_config=base_config,
                            parameters=combo.parameters,
                            rendered_rules=rendered_rules
                        )

                        # Run backtest
                        screening_result = await self._run_single_backtest(
                            combination=combo,
                            config=combo_config,
                            data=data,
                            screening_start=config.screening_start,
                            screening_end=config.screening_end
                        )

                        # Progress callback
                        if progress_callback:
                            progress_callback(index + 1, total_combinations, screening_result)

                        return screening_result

                    except Exception as e:
                        logger.error(f"Failed to backtest {combo.id}: {e}")
                        return None

            # Run all backtests concurrently
            tasks = [
                run_with_limit(combo, i)
                for i, combo in enumerate(combinations)
            ]

            screening_results = await asyncio.gather(*tasks)

            # Filter out failed results
            screening_results = [r for r in screening_results if r is not None]

            # Rank and select top N
            ranked_results = self._rank_results(
                screening_results,
                metric=config.screening_metric,
                thresholds={
                    "min_sharpe": config.min_sharpe,
                    "max_drawdown": config.max_drawdown,
                    "min_win_rate": config.min_win_rate
                }
            )

            top_results = ranked_results[:config.top_n]

            result.screening_results = top_results
            result.status = "completed"

            if top_results:
                result.best_parameters = top_results[0].parameters
                result.best_metrics = top_results[0].metrics

            logger.info(f"Parallel optimization completed. {len(top_results)} top results found.")

        except Exception as e:
            logger.error(f"Parallel optimization failed: {e}")
            result.status = "failed"
            result.error = str(e)

        return result
