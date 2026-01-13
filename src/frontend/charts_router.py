"""Streamlit Charts Router

This module provides headless chart rendering for embedding in Next.js.
When accessed with chart parameters, it renders only the chart without navigation.

Usage:
    streamlit run src.frontend.charts_router --server.port 8087
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import streamlit as st
from .utils.headless_mode import (
    setup_headless_page,
    get_auth_token,
    get_chart_params,
    validate_token,
    render_chart_container,
)

# Available chart types
CHART_TYPES = {
    "performance": "Portfolio Performance",
    "returns": "Returns Distribution",
    "drawdown": "Drawdown Analysis",
    "trades": "Trade History",
    "backtest": "Backtest Results",
    "history": "Price History",
    "indicators": "Technical Indicators",
}


def render_performance_chart():
    """Render portfolio performance chart."""
    # TODO: Fetch actual performance data
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    # Sample data
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    values = 100000 * (1 + np.cumsum(np.random.randn(len(dates)) * 0.01))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=dates, y=values, mode="lines", name="Portfolio Value", line=dict(color="#0ea5e9"))
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (¥)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_returns_chart():
    """Render returns distribution chart."""
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import numpy as np

    # Sample data
    monthly_returns = np.random.normal(0.02, 0.05, 12)
    months = pd.date_range(start="2024-01-01", periods=12, freq="MS")

    fig = go.Figure()
    colors = ["#0ea5e9" if r >= 0 else "#ef4444" for r in monthly_returns]
    fig.add_trace(
        go.Bar(x=months, y=monthly_returns * 100, name="Monthly Return", marker_color=colors)
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Month",
        yaxis_title="Return (%)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_drawdown_chart():
    """Render drawdown analysis chart."""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    # Sample data
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    cumulative_returns = np.cumsum(np.random.randn(len(dates)) * 0.01)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdown = (cumulative_returns - running_max) * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=dates, y=drawdown, fill="tozeroy", name="Drawdown", line=dict(color="#ef4444"))
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_trades_chart():
    """Render trade history chart."""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    # Sample data
    trades = pd.DataFrame({
        "date": pd.date_range(start="2024-01-01", periods=50, freq="3D"),
        "pnl": np.random.randn(50) * 1000,
    })

    fig = go.Figure()
    colors = ["#22c55e" if pnl >= 0 else "#ef4444" for pnl in trades["pnl"]]
    fig.add_trace(
        go.Bar(x=trades["date"], y=trades["pnl"], name="P&L", marker_color=colors)
    )
    fig.add_trace(
        go.Scatter(
            x=trades["date"],
            y=trades["pnl"].cumsum(),
            mode="lines",
            name="Cumulative P&L",
            line=dict(color="#0ea5e9"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Trade Date",
        yaxis_title="Profit/Loss (¥)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
        barmode="overlay",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_backtest_chart():
    """Render backtest results chart."""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    # Sample data - backtest equity curve
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    strategy_returns = 100000 * (1 + np.cumsum(np.random.randn(len(dates)) * 0.008))
    benchmark_returns = 100000 * (1 + np.cumsum(np.random.randn(len(dates)) * 0.005))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=dates, y=strategy_returns, mode="lines", name="Strategy", line=dict(color="#0ea5e9"))
    )
    fig.add_trace(
        go.Scatter(x=dates, y=benchmark_returns, mode="lines", name="Benchmark", line=dict(color="#64748b"))
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (¥)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=1.02, x=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_history_chart():
    """Render price history chart."""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    params = get_chart_params()
    symbol = params.get("symbol", "000001")

    # Sample data - price history
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    closes = 10 + np.cumsum(np.random.randn(len(dates)) * 0.1)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=dates,
            open=closes * (1 + np.random.randn(len(dates)) * 0.01),
            high=closes * (1 + abs(np.random.randn(len(dates)) * 0.01)),
            low=closes * (1 - abs(np.random.randn(len(dates)) * 0.01)),
            close=closes,
            name=symbol,
        )
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_indicators_chart():
    """Render technical indicators chart."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    import numpy as np

    # Sample data
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    closes = 10 + np.cumsum(np.random.randn(len(dates)) * 0.1)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # Price chart
    fig.add_trace(
        go.Scatter(x=dates, y=closes, mode="lines", name="Price", line=dict(color="#0ea5e9")),
        row=1, col=1
    )

    # RSI indicator
    rsi = 50 + np.cumsum(np.random.randn(len(dates)) * 2)
    rsi = np.clip(rsi, 0, 100)
    fig.add_trace(
        go.Scatter(x=dates, y=rsi, mode="lines", name="RSI", line=dict(color="#a855f7")),
        row=2, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


# Chart rendering registry
CHART_RENDERERS = {
    "performance": render_performance_chart,
    "returns": render_returns_chart,
    "drawdown": render_drawdown_chart,
    "trades": render_trades_chart,
    "backtest": render_backtest_chart,
    "history": render_history_chart,
    "indicators": render_indicators_chart,
}


def main():
    """Main entry point for headless chart rendering."""

    # Setup headless mode
    setup_headless_page(page_icon="📊", page_title="QuantOL Chart")

    # Get chart parameters from URL
    params = get_chart_params()
    chart_type = params.get("chart_type", "")

    # Validate authentication
    token = get_auth_token()
    if not validate_token(token):
        st.error("Authentication required")
        st.stop()

    # Render chart based on type
    if chart_type in CHART_RENDERERS:
        renderer = CHART_RENDERERS[chart_type]
        renderer()
    else:
        st.error(f"Unknown chart type: {chart_type}")
        st.write(f"Available chart types: {', '.join(CHART_TYPES.keys())}")


if __name__ == "__main__":
    main()
