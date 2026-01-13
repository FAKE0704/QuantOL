"""Backtest configuration management service.

Provides CRUD operations for backtest configurations.
"""

from typing import Optional, List
from datetime import datetime
import json

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

            async with db.pool as conn:
                # If this is default, unset other defaults for this user
                if is_default:
                    await conn.execute(
                        """UPDATE BacktestConfigs
                           SET is_default = 0
                           WHERE user_id = $1""",
                        user_id
                    )

                # Convert symbols list to JSON string
                symbols_json = json.dumps(symbols)

                # Check if config already exists
                existing = await conn.fetchval(
                    "SELECT id FROM BacktestConfigs WHERE user_id = $1 AND name = $2",
                    user_id, name
                )

                if existing:
                    # Update existing config
                    await conn.execute(
                        """UPDATE BacktestConfigs
                           SET description = $1, start_date = $2, end_date = $3,
                               frequency = $4, symbols = $5, initial_capital = $6,
                               commission_rate = $7, slippage = $8, min_lot_size = $9,
                               position_strategy = $10, position_params = $11,
                               trading_strategy = $12, open_rule = $13, close_rule = $14,
                               buy_rule = $15, sell_rule = $16, is_default = $17,
                               updated_at = datetime('now')
                           WHERE user_id = $18 AND name = $19""",
                        description, start_date, end_date, frequency, symbols_json,
                        initial_capital, commission_rate, slippage, min_lot_size,
                        position_strategy, json.dumps(position_params), trading_strategy,
                        open_rule, close_rule, buy_rule, sell_rule, 1 if is_default else 0,
                        user_id, name
                    )
                    config_id = existing
                else:
                    # Insert new config
                    cursor = await conn.execute(
                        """INSERT INTO BacktestConfigs
                           (user_id, name, description, start_date, end_date, frequency,
                            symbols, initial_capital, commission_rate, slippage, min_lot_size,
                            position_strategy, position_params, trading_strategy,
                            open_rule, close_rule, buy_rule, sell_rule, is_default)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)""",
                        user_id, name, description, start_date, end_date, frequency,
                        symbols_json, initial_capital, commission_rate, slippage, min_lot_size,
                        position_strategy, json.dumps(position_params), trading_strategy,
                        open_rule, close_rule, buy_rule, sell_rule, 1 if is_default else 0
                    )
                    # Get the inserted ID using lastrowid
                    config_id = cursor.lastrowid

                logger.info(f"Created backtest config '{name}' for user {user_id}, config_id={config_id}")

                # Query the config in the same connection (transaction)
                row = await conn.fetchrow(
                    """SELECT id, user_id, name, description, start_date, end_date, frequency,
                              symbols, initial_capital, commission_rate, slippage, min_lot_size,
                              position_strategy, position_params, trading_strategy,
                              open_rule, close_rule, buy_rule, sell_rule,
                              is_default, created_at, updated_at
                       FROM BacktestConfigs
                       WHERE id = $1 AND user_id = $2""",
                    config_id, user_id
                )

                if row:
                    result = self._row_to_dict(row)
                else:
                    result = None

                logger.info(f"get_config_by_id returned: {result}")
                return result

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

            async with db.pool as conn:
                # First, check if config exists
                exists = await conn.fetchval(
                    "SELECT id FROM BacktestConfigs WHERE id = $1",
                    config_id
                )
                logger.info(f"Config {config_id} exists in DB: {exists}")

                row = await conn.fetchrow(
                    """SELECT id, user_id, name, description, start_date, end_date, frequency,
                              symbols, initial_capital, commission_rate, slippage, min_lot_size,
                              position_strategy, position_params, trading_strategy,
                              open_rule, close_rule, buy_rule, sell_rule,
                              is_default, created_at, updated_at
                       FROM BacktestConfigs
                       WHERE id = $1 AND user_id = $2""",
                    config_id, user_id
                )

                logger.info(f"Fetchrow result for config {config_id}, user {user_id}: {row}")

                if not row:
                    return None

                return self._row_to_dict(row)

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

            async with db.pool as conn:
                # Debug: check if table has any data
                total_count = await conn.fetchval("SELECT COUNT(*) FROM BacktestConfigs")
                logger.info(f"Total configs in database: {total_count}")
                user_count = await conn.fetchval("SELECT COUNT(*) FROM BacktestConfigs WHERE user_id = $1", user_id)
                logger.info(f"Configs for user {user_id}: {user_count}")

                rows = await conn.fetch(
                    """SELECT id, user_id, name, description, start_date, end_date, frequency,
                              symbols, initial_capital, commission_rate, slippage, min_lot_size,
                              position_strategy, position_params, trading_strategy,
                              open_rule, close_rule, buy_rule, sell_rule,
                              is_default, created_at, updated_at
                       FROM BacktestConfigs
                       WHERE user_id = $1
                       ORDER BY is_default DESC, updated_at DESC
                       LIMIT $2 OFFSET $3""",
                    user_id, limit, offset
                )

                logger.info(f"list_configs query returned {len(rows)} rows")

                result = [self._row_to_dict(row) for row in rows]
                logger.info(f"list_configs returning: {result}")
                return result

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

            async with db.pool as conn:
                # Build update query dynamically
                updates = []
                params = []
                param_count = 1

                fields = {
                    "name": name,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "frequency": frequency,
                    "initial_capital": initial_capital,
                    "commission_rate": commission_rate,
                    "slippage": slippage,
                    "min_lot_size": min_lot_size,
                    "position_strategy": position_strategy,
                    "trading_strategy": trading_strategy,
                    "open_rule": open_rule,
                    "close_rule": close_rule,
                    "buy_rule": buy_rule,
                    "sell_rule": sell_rule,
                    "is_default": 1 if is_default else 0 if is_default is not None else None,
                }

                for field, value in fields.items():
                    if value is not None:
                        updates.append(f"{field} = ${param_count}")
                        params.append(value)
                        param_count += 1

                if symbols is not None:
                    updates.append(f"symbols = ${param_count}")
                    params.append(json.dumps(symbols))
                    param_count += 1

                if position_params is not None:
                    updates.append(f"position_params = ${param_count}")
                    params.append(json.dumps(position_params))
                    param_count += 1

                if not updates:
                    return await self.get_config_by_id(config_id, user_id)

                # Add updated_at
                updates.append(f"updated_at = datetime('now')")

                # Add WHERE params
                params.extend([config_id, user_id])

                query = f"""UPDATE BacktestConfigs
                           SET {', '.join(updates)}
                           WHERE id = ${param_count} AND user_id = ${param_count + 1}
                           RETURNING id"""

                result_id = await conn.fetchval(query, *params)

                if result_id:
                    logger.info(f"Updated backtest config {config_id} for user {user_id}")
                    return await self.get_config_by_id(config_id, user_id)

                return None

        except Exception as e:
            logger.error(f"Failed to update config {config_id}: {str(e)}")
            return None

    async def delete_config(self, config_id: int, user_id: int) -> bool:
        """Delete a configuration."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            async with db.pool as conn:
                result = await conn.execute(
                    """DELETE FROM BacktestConfigs
                       WHERE id = $1 AND user_id = $2""",
                    config_id, user_id
                )

                # Check if any rows were deleted
                # SQLite and PostgreSQL return different result formats
                if result and hasattr(result, 'rowcount'):
                    deleted = result.rowcount > 0
                else:
                    # For SQLite, check if config still exists
                    check = await conn.fetchval(
                        "SELECT id FROM BacktestConfigs WHERE id = $1", config_id
                    )
                    deleted = check is None

                if deleted:
                    logger.info(f"Deleted backtest config {config_id} for user {user_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to delete config {config_id}: {str(e)}")
            return False

    async def set_default_config(self, config_id: int, user_id: int) -> bool:
        """Set a configuration as the default."""
        try:
            db = await self._get_db()

            if hasattr(db, '_initialized') and not db._initialized:
                await db.initialize()

            async with db.pool as conn:
                # Unset other defaults for this user
                await conn.execute(
                    """UPDATE BacktestConfigs
                       SET is_default = 0
                       WHERE user_id = $1""",
                    user_id
                )

                # Set new default
                await conn.execute(
                    """UPDATE BacktestConfigs
                       SET is_default = 1, updated_at = datetime('now')
                       WHERE id = $1 AND user_id = $2""",
                    config_id, user_id
                )

                logger.info(f"Set config {config_id} as default for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to set default config {config_id}: {str(e)}")
            return False

    def _row_to_dict(self, row) -> dict:
        """Convert database row to dict."""
        # Helper to safely parse JSON
        def safe_json_loads(val):
            if not val or val == "":
                return {}
            try:
                return json.loads(val)
            except:
                return {}

        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "description": row["description"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "frequency": row["frequency"],
            "symbols": safe_json_loads(row["symbols"]),
            "initial_capital": float(row["initial_capital"]),
            "commission_rate": float(row["commission_rate"]),
            "slippage": float(row["slippage"]),
            "min_lot_size": row["min_lot_size"],
            "position_strategy": row["position_strategy"],
            "position_params": safe_json_loads(row["position_params"]),
            "trading_strategy": row["trading_strategy"],
            "open_rule": row["open_rule"],
            "close_rule": row["close_rule"],
            "buy_rule": row["buy_rule"],
            "sell_rule": row["sell_rule"],
            "is_default": bool(row["is_default"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
