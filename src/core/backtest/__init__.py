"""Refactored backtest engine package.

This package contains the refactored backtest engine with separated concerns,
following dependency injection and single responsibility principles.

The main BacktestEngine class now delegates to specialized services:
- EquityService: Tracks and calculates equity
- ResultsService: Aggregates results and metrics
- EventCoordinator: Manages event-driven communication
- OrderCoordinator: Handles order creation and execution
- BacktestDatabaseProvider: Provides database access
"""

from .engine import BacktestEngine

__all__ = ["BacktestEngine"]
