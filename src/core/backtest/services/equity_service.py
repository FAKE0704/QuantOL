"""Equity tracking and calculation service.

This service manages equity calculation and tracking throughout backtest execution,
extracted from BacktestEngine._update_equity and related methods.
"""

from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import numpy as np
from src.support.log.logger import logger


class EquityService:
    """Service for tracking and calculating equity-related metrics.

    Extracted from BacktestEngine._update_equity and related methods.
    """

    def __init__(self, portfolio, initial_capital: float):
        """Initialize equity service.

        Args:
            portfolio: Portfolio manager instance
            initial_capital: Initial capital for backtest
        """
        self.portfolio = portfolio
        self.initial_capital = initial_capital
        self._logger = logger.getChild('EquityService')

        # Equity records storage
        self.equity_records = pd.DataFrame(columns=[
            'timestamp', 'price', 'position', 'position_cost', 'cash', 'total_value'
        ])
        self._peak_value = initial_capital
        self._max_drawdown = 0.0

    def update_equity(self, timestamp: datetime, price: float) -> None:
        """Update equity record at a specific timestamp.

        Args:
            timestamp: Current timestamp
            price: Current price for equity calculation
        """
        if price is None:
            self._logger.warning(f"Skipping equity update: price is None at {timestamp}")
            return

        try:
            close_price = float(price)
            available_cash = float(self.portfolio.get_available_cash())

            # Get position info
            all_positions = self.portfolio.get_all_positions()
            position_quantity = 0.0
            position_avg_cost = 0.0

            # Handle single symbol mode (most common case)
            if hasattr(self.portfolio, 'config') and hasattr(self.portfolio.config, 'target_symbol'):
                target_symbol = self.portfolio.config.target_symbol
                if target_symbol in all_positions:
                    position = all_positions[target_symbol]
                    position_quantity = position.quantity
                    position_avg_cost = position.avg_cost

            # Handle multi-symbol mode
            else:
                for symbol, position in all_positions.items():
                    position_quantity += position.quantity

            position_value = position_quantity * close_price
            total_value = available_cash + position_value

            # Calculate drawdown
            if total_value > self._peak_value:
                self._peak_value = total_value

            current_drawdown = (self._peak_value - total_value) / self._peak_value if self._peak_value > 0 else 0
            self._max_drawdown = max(self._max_drawdown, current_drawdown)

            # Create equity record
            record = {
                'timestamp': timestamp,
                'price': close_price,
                'position': position_quantity,
                'position_cost': position_avg_cost,
                'cash': available_cash,
                'total_value': total_value
            }

            # Append to records
            if self.equity_records.empty:
                self.equity_records = pd.DataFrame([record])
            else:
                self.equity_records = pd.concat([
                    self.equity_records,
                    pd.DataFrame([record])
                ], ignore_index=True)

        except Exception as e:
            self._logger.error(f"Failed to update equity: {e}")
            raise

    def get_equity_history(self) -> List[Dict[str, Any]]:
        """Get equity history as list of dictionaries.

        Returns:
            List of equity records with timestamp, price, position, cash, total_value
        """
        return self.equity_records.to_dict('records')

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity history.

        Returns:
            Maximum drawdown as a percentage (0-1)
        """
        if self.equity_records.empty:
            return 0.0
        peak = self.equity_records['total_value'].max()
        trough = self.equity_records['total_value'].min()
        return (peak - trough) / peak if peak != 0 else 0.0

    def get_current_equity(self) -> float:
        """Get current total equity value.

        Returns:
            Current equity value
        """
        if self.equity_records.empty:
            return self.initial_capital
        return float(self.equity_records.iloc[-1]['total_value'])

    def get_peak_value(self) -> float:
        """Get the peak equity value.

        Returns:
            Peak equity value
        """
        return self._peak_value

    def reset(self) -> None:
        """Reset equity tracking state (for testing)."""
        self.equity_records = pd.DataFrame(columns=[
            'timestamp', 'price', 'position', 'position_cost', 'cash', 'total_value'
        ])
        self._peak_value = self.initial_capital
        self._max_drawdown = 0.0
