"""
Centralized configuration management for the application.

This module provides a singleton configuration class that loads and manages
environment variables and configuration settings for the application.
"""

import os
from typing import Any, Dict


class Config:
    """Configuration singleton for the application"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from environment variables"""
        # AWS Services
        self._config["REGION"] = "us-west-2"
        self._config["JOBS_TABLE_NAME"] = os.environ.get("JOBS_TABLE_NAME")
        self._config["RESEARCH_PROCESSOR_LAMBDA"] = os.environ.get(
            "RESEARCH_PROCESSOR_LAMBDA"
        )

        # Research Configuration - these can have defaults
        try:
            self._config["RESEARCH_ROUNDS"] = int(
                os.environ.get("RESEARCH_ROUNDS", "1")
            )
        except (ValueError, TypeError):
            self._config["RESEARCH_ROUNDS"] = 1

        self._config["KB_ID"] = os.environ.get("KB_ID")
        self._config["TAVILY_API_KEY"] = os.environ.get("TAVILY_API_KEY")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value

        Args:
            key: The configuration key
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)


def get_config() -> Config:
    """Get the configuration singleton

    Returns:
        Config: The configuration singleton
    """
    return Config()
