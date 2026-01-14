"""Backtest configuration management service.

Provides CRUD operations for backtest configurations.
"""

from typing import Optional, List

from src.support.log.logger import logger
from src.database import get_db_adapter


class BacktestConfigService:
    """Service for managing backtest configurations."""

    def __init__(self):
        self._db = None

    async def _get_db(self):
        """Get database adapter."""
        if self._db is None:
            self._db = get_db_adapter()
        return self._db

    async def create_config(
        self,
        user_id: int,
        name: str,
        description: Optional[str],
        start_date: str,
        end_date: str,
        frequency: str,
        symbols: List[str],
        initial_capital: float,
        commission_rate: float,
        slippage: float,
        min_lot_size: int,
        position_strategy: str,
        position_params: dict,
        trading_strategy: Optional[str] = None,
        open_rule: Optional[str] = None,
        close_rule: Optional[str] = None,
        buy_rule: Optional[str] = None,
        sell_rule: Optional[str] = None,
        is_default: bool = False,
    ) -> Optional[dict]:
        """Create a new backtest configuration."""
        try:
            db = await self._get_db()

            # Ensure database is initialized
            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.create_backtest_config(
                user_id=user_id,
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                symbols=symbols,
                initial_capital=initial_capital,
                commission_rate=commission_rate,
                slippage=slippage,
                min_lot_size=min_lot_size,
                position_strategy=position_strategy,
                position_params=position_params,
                trading_strategy=trading_strategy,
                open_rule=open_rule,
                close_rule=close_rule,
                buy_rule=buy_rule,
                sell_rule=sell_rule,
                is_default=is_default,
            )

        except Exception as e:
            logger.error(f"Failed to create backtest config: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def get_config_by_id(self, config_id: int, user_id: int) -> Optional[dict]:
        """Get a configuration by ID."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.get_backtest_config_by_id(config_id, user_id)

        except Exception as e:
            logger.error(f"Failed to get config {config_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def list_configs(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[dict]:
        """List all configurations for a user."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.list_backtest_configs(user_id, limit, offset)

        except Exception as e:
            logger.error(f"Failed to list configs for user {user_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def update_config(
        self,
        config_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        initial_capital: Optional[float] = None,
        commission_rate: Optional[float] = None,
        slippage: Optional[float] = None,
        min_lot_size: Optional[int] = None,
        position_strategy: Optional[str] = None,
        position_params: Optional[dict] = None,
        trading_strategy: Optional[str] = None,
        open_rule: Optional[str] = None,
        close_rule: Optional[str] = None,
        buy_rule: Optional[str] = None,
        sell_rule: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[dict]:
        """Update a configuration."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.update_backtest_config(
                config_id=config_id,
                user_id=user_id,
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                symbols=symbols,
                initial_capital=initial_capital,
                commission_rate=commission_rate,
                slippage=slippage,
                min_lot_size=min_lot_size,
                position_strategy=position_strategy,
                position_params=position_params,
                trading_strategy=trading_strategy,
                open_rule=open_rule,
                close_rule=close_rule,
                buy_rule=buy_rule,
                sell_rule=sell_rule,
                is_default=is_default,
            )

        except Exception as e:
            logger.error(f"Failed to update config {config_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def delete_config(self, config_id: int, user_id: int) -> bool:
        """Delete a configuration."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.delete_backtest_config(config_id, user_id)

        except Exception as e:
            logger.error(f"Failed to delete config {config_id}: {str(e)}")
            return False

    async def set_default_config(self, config_id: int, user_id: int) -> bool:
        """Set a configuration as the default."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            return await db.set_default_backtest_config(config_id, user_id)

        except Exception as e:
            logger.error(f"Failed to set default config {config_id}: {str(e)}")
            return False
