"""Application configuration.

All runtime configuration is sourced from environment variables (optionally
loaded from a local ``.env`` file via :mod:`python-dotenv`). This keeps the
application 12-factor friendly and ready for one-click cloud deployment where
configuration is injected through the platform's environment settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

# Load variables from a local .env file if present. In production (Render,
# Railway, Fly.io, Hugging Face Spaces, ...) the platform injects real env vars
# and the missing .env file is simply ignored.
load_dotenv()


def _split_csv(value: str) -> list[str]:
    """Split a comma separated environment value into a clean list."""
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Strongly typed application settings."""

    # Server binding -------------------------------------------------------
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # CORS -----------------------------------------------------------------
    # Comma separated list of allowed origins. ``*`` allows any origin which is
    # convenient for local development.
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.getenv("CORS_ORIGINS", "*"))
    )

    # Static frontend ------------------------------------------------------
    # Absolute or relative path to the compiled Angular build. When the folder
    # exists FastAPI serves it as the application root, allowing the whole stack
    # to run as a single unified web service.
    frontend_dist: str = field(
        default_factory=lambda: os.getenv("FRONTEND_DIST", "../frontend/dist/live-dashboard/browser")
    )

    # External data providers ---------------------------------------------
    hyperliquid_ws_url: str = field(
        default_factory=lambda: os.getenv("HYPERLIQUID_WS_URL", "wss://api.hyperliquid.xyz/ws")
    )
    hyperliquid_rest_url: str = field(
        default_factory=lambda: os.getenv("HYPERLIQUID_REST_URL", "https://api.hyperliquid.xyz/info")
    )

    # Polling interval (seconds) for HTTP based sources such as yfinance.
    poll_interval_seconds: float = field(
        default_factory=lambda: float(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
