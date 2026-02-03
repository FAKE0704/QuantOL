"""Rebalance period service for controlling when rebalancing should occur.

This service provides flexible rebalancing scheduling based on either:
1. Trading days interval (e.g., rebalance every 5 trading days)
2. Calendar rules (e.g., rebalance every Monday, first trading day of month)
"""

import pandas as pd
from typing import Dict, Any, Optional
from src.support.log.logger import logger


class RebalancePeriodService:
    """Service for determining when rebalancing should occur based on configurable rules."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the rebalance period service.

        Args:
            config: Configuration dictionary containing:
                - mode: "trading_days" | "calendar_rule" | "disabled"
                - interval: Number of trading days between rebalances (for trading_days mode)
                - frequency: "weekly" | "monthly" (for calendar_rule mode)
                - day: Day of week/month (for calendar_rule mode)
                - min_interval_days: Minimum calendar days between rebalances
                - allow_first_rebalance: Whether to force rebalance on first trading day
        """
        self.mode = config.get("mode", "disabled")
        self.trading_days_interval = config.get("interval", 5)
        self.calendar_frequency = config.get("frequency", "weekly")
        self.calendar_day = config.get("day", 1)
        self.min_interval_days = config.get("min_interval_days", 0)
        self.allow_first_rebalance = config.get("allow_first_rebalance", True)

        self.trading_days_count = 0
        self.last_rebalance_date = None

    def should_rebalance(self, current_time: pd.Timestamp, is_new_day: bool) -> bool:
        """Determine if rebalancing should occur at the current time.

        Args:
            current_time: Current timestamp in the backtest
            is_new_day: Whether this is a new trading day (vs same day, different bar)

        Returns:
            True if rebalancing should occur, False otherwise
        """
        # Track trading days
        if is_new_day:
            self.trading_days_count += 1

        # First rebalance decision
        if self.last_rebalance_date is None:
            if self.allow_first_rebalance:
                self._update_last_rebalance(current_time)
                logger.debug(f"[调仓周期] 首次调仓允许: {current_time.date()}")
                return True
            else:
                logger.debug(f"[调仓周期] 首次调仓跳过，当前交易日计数: {self.trading_days_count}")
                return False

        # Check minimum interval
        if self.min_interval_days > 0:
            days_since_last = (current_time.date() - self.last_rebalance_date).days
            if days_since_last < self.min_interval_days:
                logger.debug(f"[调仓周期] 距上次调仓仅 {days_since_last} 天，最小间隔要求 {self.min_interval_days} 天")
                return False

        # Determine based on mode
        if self.mode == "trading_days":
            return self._should_rebalance_by_trading_days(current_time, is_new_day)
        elif self.mode == "calendar_rule":
            return self._should_rebalance_by_calendar_rule(current_time)
        else:
            return True  # disabled = every data point can rebalance

    def _should_rebalance_by_trading_days(self, current_time: pd.Timestamp, is_new_day: bool) -> bool:
        """Check if should rebalance based on trading days interval.

        Args:
            current_time: Current timestamp
            is_new_day: Whether this is a new trading day

        Returns:
            True if trading days count is a multiple of the interval
        """
        should_rebalance = self.trading_days_count % self.trading_days_interval == 0
        if should_rebalance and is_new_day:
            logger.debug(f"[调仓周期] 第 {self.trading_days_count} 个交易日，间隔 {self.trading_days_interval}，触发调仓")
            self._update_last_rebalance(current_time)
        return should_rebalance

    def _should_rebalance_by_calendar_rule(self, current_time: pd.Timestamp) -> bool:
        """Check if should rebalance based on calendar rules.

        Args:
            current_time: Current timestamp

        Returns:
            True if current date matches the calendar rule
        """
        current_date = current_time.date()
        weekday = current_date.weekday()  # 0=Monday, 6=Sunday
        day_of_month = current_date.day

        should_rebalance = False

        if self.calendar_frequency == "weekly":
            # calendar_day: 1=Monday, 7=Sunday (user-facing), convert to 0-6
            target_weekday = (self.calendar_day - 1) % 7
            should_rebalance = weekday == target_weekday
            if should_rebalance:
                logger.debug(f"[调仓周期] 周{['一','二','三','四','五','六','日'][weekday]}，触发调仓")

        elif self.calendar_frequency == "monthly":
            should_rebalance = day_of_month == self.calendar_day
            if should_rebalance:
                logger.debug(f"[调仓周期] 每月第 {day_of_month} 天，触发调仓")

        if should_rebalance:
            self._update_last_rebalance(current_time)

        return should_rebalance

    def _update_last_rebalance(self, current_time: pd.Timestamp):
        """Update the last rebalance date.

        Args:
            current_time: Current timestamp to record as last rebalance time
        """
        self.last_rebalance_date = current_time.date()
        logger.debug(f"[调仓周期] 更新上次调仓日期: {self.last_rebalance_date}")
