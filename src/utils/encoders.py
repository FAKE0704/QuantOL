"""Unified JSON encoders for QuantOL.

This module provides a single, reusable JSON encoder to replace
the 4 duplicate encoder classes across the codebase:
- BacktestResultEncoder in backtest_task_service.py
- CustomEncoder in backtest_task_manager.py
- CustomEncoder in websocket_manager.py
- CustomEncoder in backtest_state_service.py
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any


class QuantOLEncoder(json.JSONEncoder):
    """Unified JSON encoder for QuantOL-specific types.

    Handles:
    - pandas Timestamp, DataFrame, Series
    - numpy integer, floating, ndarray
    - datetime objects
    - dataclass objects
    - Custom types (SimpleStock, Position)
    """

    def default(self, obj: Any) -> Any:
        # Handle pandas types
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.DataFrame):
            # Preserve DataFrame attrs to avoid losing rule mapping info
            return {
                "__type__": "DataFrame",
                "__attrs__": getattr(obj, 'attrs', {}),
                "__data__": obj.to_dict('records')
            }
        elif isinstance(obj, pd.Series):
            return obj.tolist()

        # Handle numpy types
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            # Handle NaN and Inf
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()

        # Handle datetime
        elif isinstance(obj, datetime):
            return obj.isoformat()

        # Handle dataclass
        elif hasattr(obj, '__dataclass_fields__'):
            from dataclasses import asdict
            try:
                return asdict(obj)
            except Exception:
                # Fallback to dict representation
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}

        # Handle custom SimpleStock
        elif obj.__class__.__name__ == 'SimpleStock':
            return {'symbol': obj.symbol, 'last_price': obj.last_price}

        return super().default(obj)

    def iterencode(self, o, _one_shot=False):
        """Override to clean NaN/Inf values before encoding."""
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(v) for v in obj]
            elif isinstance(obj, (float, np.floating)):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return obj
            return obj

        cleaned_obj = clean_nan(o)
        return super().iterencode(cleaned_obj, _one_shot)


def to_json_string(obj: Any, **kwargs) -> str:
    """Convert object to JSON string using QuantOL encoder.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string
    """
    return json.dumps(obj, cls=QuantOLEncoder, **kwargs)


def convert_to_json_serializable(obj: Any, max_depth: int = 100) -> Any:
    """Convert object to JSON-serializable format recursively.

    This is useful for nested structures that need preprocessing
    before JSON serialization.

    Args:
        obj: Object to convert
        max_depth: Maximum recursion depth

    Returns:
        JSON-serializable version of the object
    """
    if max_depth <= 0:
        return str(obj)

    # Handle pandas types
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return {
            "__type__": "DataFrame",
            "__attrs__": getattr(obj, 'attrs', {}),
            "__data__": obj.to_dict('records')
        }
    elif isinstance(obj, pd.Series):
        return obj.tolist()

    # Handle collections
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v, max_depth - 1) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item, max_depth - 1) for item in obj]

    return obj
