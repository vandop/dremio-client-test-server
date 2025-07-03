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
    
    @classmethod
    def validate_dremio_config(cls):
        """Validate that all required Dremio configuration is present."""
        required_vars = [
            'DREMIO_CLOUD_URL',
            'DREMIO_USERNAME', 
            'DREMIO_PASSWORD',
            'DREMIO_PROJECT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
