"""Results aggregation and metrics calculation service.

This service calculates and aggregates backtest results,
extracted from BacktestEngine.get_results and related methods.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from src.support.log.logger import logger


class ResultsService:
    """Service for calculating and aggregating backtest results.

    Extracted from BacktestEngine.get_results and related methods.
    """

    def __init__(self, portfolio, equity_service):
        """Initialize results service.

        Args:
            portfolio: Portfolio manager instance
            equity_service: Equity service instance
        """
        self.portfolio = portfolio
        self.equity_service = equity_service
        self._logger = logger.getChild('ResultsService')

    def get_results(
        self,
        trades: List[Dict],
        debug_data: Optional[Dict] = None,
        parser_data: Optional[Dict] = None,
        price_data: Optional[pd.DataFrame] = None,
        signals_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Aggregate and format backtest results.

        Args:
            trades: List of executed trades
            debug_data: Strategy debug data
            parser_data: Parser data with indicators
            price_data: Price data with signals
            signals_data: Signals data

        Returns:
            Dictionary containing all backtest results and metrics
        """
        # Get portfolio performance metrics
        performance_metrics = self.portfolio.get_performance_metrics()

        # Add advanced metrics
        performance_metrics.update(self.calculate_advanced_metrics(trades))

        # Build results dictionary
        results = {
            "summary": {
                "initial_capital": performance_metrics.get('initial_capital', 0),
                "final_capital": performance_metrics.get('final_capital', 0),
                "total_trades": len(trades),
                "win_rate": self._calculate_win_rate(trades),
                "max_drawdown": performance_metrics.get('max_drawdown_pct', 0),
                "total_return": performance_metrics.get('total_return_pct', 0),
                "current_drawdown": performance_metrics.get('current_drawdown_pct', 0),
                "position_strategy_type": performance_metrics.get('position_strategy_type', '')
            },
            "trades": trades,
            "errors": [],  # Will be populated by caller
            "equity_records": self.equity_service.get_equity_history(),
            "performance_metrics": performance_metrics,
            "debug_data": debug_data,
            "parser_data": parser_data,
            "price_data": price_data,
            "signals": signals_data
        }

        return results

    def calculate_advanced_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced performance metrics.

        Args:
            trades: List of trades with profit/loss information

        Returns:
            Dictionary of metrics (sharpe_ratio, win_rate, max_drawdown, etc.)
        """
        metrics = {}

        # Get equity history
        equity_records = self.equity_service.equity_records
        if equity_records.empty:
            return metrics

        # Calculate daily returns
        returns = self._calculate_daily_returns(equity_records)
        if not returns:
            return metrics

        returns_array = np.array(returns)

        # Calculate metrics
        metrics['daily_volatility'] = float(returns_array.std() * np.sqrt(252) * 100)
        metrics['annualized_return'] = self._calculate_annual_return(equity_records)
        metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(returns_array, metrics['daily_volatility'])
        metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns_array)
        metrics['calmar_ratio'] = self._calculate_calmar_ratio(returns_array)
        metrics['win_rate'] = self._calculate_win_rate(trades)
        metrics['max_drawdown'] = float(self.equity_service.calculate_max_drawdown() * 100)

        return metrics

    def _calculate_daily_returns(self, equity_records: pd.DataFrame) -> List[float]:
        """Calculate daily returns from equity records.

        Args:
            equity_records: DataFrame with equity history

        Returns:
            List of daily return percentages
        """
        returns = []
        for i in range(1, len(equity_records)):
            prev_value = equity_records.iloc[i - 1]['total_value']
            curr_value = equity_records.iloc[i]['total_value']
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
        return returns

    def _calculate_annual_return(self, equity_records: pd.DataFrame) -> float:
        """Calculate annualized return from equity records.

        Args:
            equity_records: DataFrame with equity history

        Returns:
            Annualized return as percentage
        """
        if equity_records.empty:
            return 0.0

        initial_value = equity_records.iloc[0]['total_value']
        final_value = equity_records.iloc[-1]['total_value']
        total_return = (final_value - initial_value) / initial_value if initial_value > 0 else 0

        # Calculate annualized return based on actual days passed
        start_time = pd.to_datetime(equity_records.iloc[0]['timestamp'])
        end_time = pd.to_datetime(equity_records.iloc[-1]['timestamp'])
        days = (end_time - start_time).days

        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
            return annual_return * 100
        return 0.0

    def _calculate_sharpe_ratio(self, returns_array: np.ndarray, daily_volatility: float) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns_array: Array of daily returns
            daily_volatility: Annualized daily volatility

        Returns:
            Sharpe ratio or 0 if volatility is 0
        """
        if daily_volatility == 0:
            return 0.0

        mean_return = float(np.mean(returns_array)) * 252  # Annualize
        return mean_return / daily_volatility if daily_volatility > 0 else 0.0

    def _calculate_sortino_ratio(self, returns_array: np.ndarray) -> float:
        """Calculate Sortino ratio (downside risk).

        Args:
            returns_array: Array of daily returns

        Returns:
            Sortino ratio or 0 if no downside volatility
        """
        # Calculate downside deviation
        negative_returns = returns_array[returns_array < 0]
        if len(negative_returns) == 0:
            return 0.0

        downside_deviation = float(np.std(negative_returns) * np.sqrt(252))
        mean_return = float(np.mean(returns_array) * 252)

        if downside_deviation == 0:
            return 0.0

        return mean_return / downside_deviation

    def _calculate_calmar_ratio(self, returns_array: np.ndarray) -> float:
        """Calculate Calmar ratio (annual return / max drawdown).

        Args:
            returns_array: Array of daily returns

        Returns:
            Calmar ratio or 0 if max drawdown is 0
        """
        max_dd = self.equity_service.calculate_max_drawdown()
        if max_dd == 0:
            return 0.0

        annual_return = self._calculate_annual_return(self.equity_service.equity_records)
        return annual_return / max_dd

    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate trade win rate.

        Args:
            trades: List of trades

        Returns:
            Win rate as percentage (0-1)
        """
        if not trades:
            return 0.0
        winning_trades = len([t for t in trades if t.get('profit', 0) > 0])
        return winning_trades / len(trades)

    def get_equity_records_dataframe(self) -> pd.DataFrame:
        """Get equity records as DataFrame.

        Returns:
            DataFrame with equity history
        """
        return self.equity_records.equity_records.copy()
