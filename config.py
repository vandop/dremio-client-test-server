"""
Configuration management for Dremio connection and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # Flask configuration
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # Security warning for production
    @classmethod
    def validate_production_config(cls):
        """Validate configuration for production deployment."""
        warnings = []
        if cls.DEBUG:
            warnings.append("DEBUG mode is enabled - disable in production")
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            warnings.append("Using default SECRET_KEY - change in production")
        return warnings

    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", 5001))

    # Dremio Cloud configuration
    DREMIO_CLOUD_URL = os.environ.get("DREMIO_CLOUD_URL")
    DREMIO_USERNAME = os.environ.get("DREMIO_USERNAME")
    DREMIO_PASSWORD = os.environ.get("DREMIO_PASSWORD")
    DREMIO_PROJECT_ID = os.environ.get("DREMIO_PROJECT_ID")

    # Dremio Cloud Personal Access Token (preferred for Dremio Cloud)
    DREMIO_PAT = os.environ.get("DREMIO_PAT")

    # SSL/TLS Configuration
    DREMIO_SSL_VERIFY = os.environ.get("DREMIO_SSL_VERIFY", "true").lower() == "true"
    DREMIO_SSL_CERT_PATH = os.environ.get(
        "DREMIO_SSL_CERT_PATH"
    )  # Optional custom cert path

    @classmethod
    def validate_dremio_config(cls):
        """Validate that all required Dremio configuration is present."""
        # Check for required base configuration
        if not cls.DREMIO_CLOUD_URL:
            raise ValueError("Missing required environment variable: DREMIO_CLOUD_URL")

        if not cls.DREMIO_PROJECT_ID:
            raise ValueError("Missing required environment variable: DREMIO_PROJECT_ID")

        # Check authentication method - either PAT or username/password
        has_pat = bool(cls.DREMIO_PAT)
        has_username_password = bool(cls.DREMIO_USERNAME and cls.DREMIO_PASSWORD)

        # For Dremio Cloud (api.dremio.cloud), PAT is required
        is_dremio_cloud = (
            cls.DREMIO_CLOUD_URL and "api.dremio.cloud" in cls.DREMIO_CLOUD_URL
        )

        if is_dremio_cloud and not has_pat:
            raise ValueError(
                "Dremio Cloud requires a Personal Access Token (PAT).\n"
                "Please set DREMIO_PAT in your .env file.\n"
                "Get your PAT from: Dremio Cloud UI > Account Settings > Personal Access Tokens"
            )
        elif not has_pat and not has_username_password:
            raise ValueError(
                "Missing authentication credentials. Please provide either:\n"
                "  - DREMIO_PAT (Personal Access Token - required for Dremio Cloud)\n"
                "  - DREMIO_USERNAME and DREMIO_PASSWORD (for on-premise Dremio)"
            )

        return True
