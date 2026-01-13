"""Streamlit headless mode utilities.

This module provides utilities for running Streamlit in "headless mode"
- embedding charts in iframe without navigation/sidebar
- receiving parameters from URL (e.g., auth token)
- rendering clean chart-only views
"""

import os
from typing import Optional
import streamlit as st


def is_headless_mode() -> bool:
    """Check if running in headless/embedded mode.

    Returns:
        True if running in headless mode
    """
    # Check URL parameter or environment variable
    url_params = st.query_params
    return (
        url_params.get("headless", "false").lower() == "true"
        or os.getenv("STREAMLIT_HEADLESS", "false").lower() == "true"
    )


def get_auth_token() -> Optional[str]:
    """Get JWT token from URL parameters.

    Returns:
        JWT token if present, None otherwise
    """
    url_params = st.query_params
    token = url_params.get("token", "")
    return token if token else None


def hide_ui_elements():
    """Hide Streamlit UI elements in headless mode."""
    if is_headless_mode():
        # Inject CSS to hide unwanted elements
        hide_elements = """
        <style>
            /* Hide main menu and footer */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}

            /* Hide streamlit default padding */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            /* Hide deploy button */
            .stDeployButton {display: none;}

            /* Full width for embedded charts */
            .main .block-container {
                max-width: 100%;
                padding: 1rem;
            }
        </style>
        """
        st.markdown(hide_elements, unsafe_allow_html=True)


def render_chart_container(
    chart_id: str,
    content_html: str,
    height: str = "600px",
):
    """Render a chart in a clean container for iframe embedding.

    Args:
        chart_id: Unique identifier for the chart
        content_html: HTML content of the chart
        height: Height of the chart container
    """
    container_html = f"""
    <div id="chart-{chart_id}" style="
        width: 100%;
        height: {height};
        overflow: hidden;
        background: transparent;
    ">
        {content_html}
    </div>

    <script>
        // Post message to parent when chart is ready
        window.addEventListener('load', function() {{
            if (window.parent !== window) {{
                window.parent.postMessage({{
                    type: 'chartReady',
                    chartId: '{chart_id}',
                    height: document.documentElement.scrollHeight
                }}, '*');
            }}
        }});

        // Notify parent on resize
        new ResizeObserver(function(entries) {{
            for (let entry of entries) {{
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'chartResize',
                        chartId: '{chart_id}',
                        height: entry.contentRect.height
                    }}, '*');
                }}
            }}
        }}).observe(document.body);
    </script>
    """
    st.markdown(container_html, unsafe_allow_html=True)


def setup_headless_page(
    page_title: str = "QuantOL Chart",
    page_icon: Optional[str] = None,
):
    """Setup Streamlit page configuration for headless mode.

    Args:
        page_title: Title of the page
        page_icon: Optional emoji or icon for the page
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon or "📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Apply headless mode styling
    hide_ui_elements()


def validate_token(token: str) -> bool:
    """Validate JWT token (simple validation).

    For production, this should call the auth service to properly validate.

    Args:
        token: JWT token string

    Returns:
        True if token appears valid, False otherwise
    """
    if not token:
        return False

    # Basic format check
    parts = token.split(".")
    if len(parts) != 3:
        return False

    # For production, use:
    # from src.core.auth import AuthService
    # auth_service = AuthService(get_db_adapter())
    # payload = await auth_service.verify_token(token)
    # return payload is not None

    return True


def require_auth():
    """Require authentication for headless mode.

    Raises:
        Exception: If authentication fails
    """
    if not is_headless_mode():
        return  # Not in headless mode, skip auth check

    token = get_auth_token()

    if not validate_token(token):
        st.error("Authentication required. Please provide a valid token.")
        st.stop()


def get_chart_params() -> dict:
    """Get chart parameters from URL.

    Returns:
        Dictionary of chart parameters
    """
    url_params = st.query_params
    return {
        "chart_type": url_params.get("chart", ""),
        "symbol": url_params.get("symbol", ""),
        "start_date": url_params.get("start", ""),
        "end_date": url_params.get("end", ""),
        "strategy_id": url_params.get("strategy", ""),
    }
