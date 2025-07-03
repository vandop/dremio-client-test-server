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
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Dremio Cloud configuration
    DREMIO_CLOUD_URL = os.environ.get('DREMIO_CLOUD_URL')
    DREMIO_USERNAME = os.environ.get('DREMIO_USERNAME')
    DREMIO_PASSWORD = os.environ.get('DREMIO_PASSWORD')
    DREMIO_PROJECT_ID = os.environ.get('DREMIO_PROJECT_ID')

    # Dremio Cloud Personal Access Token (preferred for Dremio Cloud)
    DREMIO_PAT = os.environ.get('DREMIO_PAT')

    # SSL/TLS Configuration
    DREMIO_SSL_VERIFY = os.environ.get('DREMIO_SSL_VERIFY', 'true').lower() == 'true'
    DREMIO_SSL_CERT_PATH = os.environ.get('DREMIO_SSL_CERT_PATH')  # Optional custom cert path
    
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

        if not has_pat and not has_username_password:
            raise ValueError(
                "Missing authentication credentials. Please provide either:\n"
                "  - DREMIO_PAT (Personal Access Token - recommended for Dremio Cloud)\n"
                "  - DREMIO_USERNAME and DREMIO_PASSWORD (for on-premise or legacy)"
            )

        return True
