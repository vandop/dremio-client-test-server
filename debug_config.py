"""
Debug configuration manager for Dremio connection settings.
"""
import logging
from typing import Dict, Any, Optional, List
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DebugConfigManager:
    """Manages debug configuration overrides for Dremio connections."""
    
    def __init__(self):
        """Initialize debug config manager."""
        self.session_config = {}
        self.available_projects = []
        self.connection_tested = False
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration with debug overrides."""
        config = {
            'dremio_url': self.session_config.get('DREMIO_CLOUD_URL', Config.DREMIO_CLOUD_URL),
            'dremio_type': self.session_config.get('DREMIO_TYPE', self._detect_dremio_type()),
            'username': self.session_config.get('DREMIO_USERNAME', Config.DREMIO_USERNAME),
            'password': self.session_config.get('DREMIO_PASSWORD', Config.DREMIO_PASSWORD),
            'pat': self.session_config.get('DREMIO_PAT', Config.DREMIO_PAT),
            'project_id': self.session_config.get('DREMIO_PROJECT_ID', Config.DREMIO_PROJECT_ID),
            'ssl_verify': self.session_config.get('DREMIO_SSL_VERIFY', getattr(Config, 'DREMIO_SSL_VERIFY', True))
        }
        return config
    
    def _detect_dremio_type(self) -> str:
        """Detect if this is Dremio Cloud or Dremio Software."""
        url = self.session_config.get('DREMIO_CLOUD_URL', Config.DREMIO_CLOUD_URL)
        if url and 'dremio.cloud' in url:
            return 'cloud'
        else:
            return 'software'
    
    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update debug configuration."""
        # Validate and sanitize inputs
        valid_keys = {
            'DREMIO_CLOUD_URL', 'DREMIO_TYPE', 'DREMIO_USERNAME', 
            'DREMIO_PASSWORD', 'DREMIO_PAT', 'DREMIO_PROJECT_ID', 'DREMIO_SSL_VERIFY'
        }
        
        for key, value in config_updates.items():
            if key in valid_keys:
                if value is not None and value != '':
                    self.session_config[key] = value
                elif key in self.session_config:
                    # Remove empty values
                    del self.session_config[key]
        
        # Reset connection test status when config changes
        self.connection_tested = False
        self.available_projects = []
        
        return {
            'success': True,
            'message': 'Configuration updated successfully',
            'current_config': self.get_current_config()
        }
    
    def test_connection_and_fetch_projects(self) -> Dict[str, Any]:
        """Test connection and fetch available projects."""
        try:
            from dremio_multi_driver_client import DremioMultiDriverClient
            
            # Create client with debug config
            client = DremioMultiDriverClient(config_override=self.session_config)
            
            # Test connection with PyArrow Flight (most reliable)
            connection_results = client.test_connection(['pyarrow_flight'])
            
            if connection_results.get('pyarrow_flight', {}).get('success', False):
                # Fetch projects
                projects_result = client.get_projects()
                
                if projects_result.get('success', False):
                    self.available_projects = projects_result['projects']
                    self.connection_tested = True
                    
                    return {
                        'success': True,
                        'message': 'Connection successful',
                        'projects': self.available_projects,
                        'connection_details': connection_results['pyarrow_flight']
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Connection successful but failed to fetch projects: {projects_result.get("message", "Unknown error")}',
                        'connection_details': connection_results['pyarrow_flight'],
                        'projects': []
                    }
            else:
                error_msg = connection_results.get('pyarrow_flight', {}).get('error', 'Unknown connection error')
                return {
                    'success': False,
                    'message': f'Connection failed: {error_msg}',
                    'connection_details': connection_results.get('pyarrow_flight', {}),
                    'projects': []
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'projects': [],
                'error': str(e)
            }
    
    def get_available_projects(self) -> List[Dict[str, Any]]:
        """Get cached available projects."""
        return self.available_projects
    
    def set_project_id(self, project_id: str) -> Dict[str, Any]:
        """Set the project ID after fetching projects."""
        if not self.available_projects:
            return {
                'success': False,
                'message': 'No projects available. Please test connection first.'
            }
        
        # Validate project ID exists
        valid_project = any(p['id'] == project_id for p in self.available_projects)
        
        if not valid_project:
            return {
                'success': False,
                'message': f'Invalid project ID: {project_id}',
                'available_projects': [{'id': p['id'], 'name': p['name']} for p in self.available_projects]
            }
        
        self.session_config['DREMIO_PROJECT_ID'] = project_id
        
        return {
            'success': True,
            'message': f'Project ID set to: {project_id}',
            'current_config': self.get_current_config()
        }
    
    def reset_config(self) -> Dict[str, Any]:
        """Reset debug configuration to defaults."""
        self.session_config = {}
        self.available_projects = []
        self.connection_tested = False
        
        return {
            'success': True,
            'message': 'Configuration reset to defaults',
            'current_config': self.get_current_config()
        }
    
    def get_config_for_client(self) -> Dict[str, Any]:
        """Get configuration dictionary suitable for client override."""
        return self.session_config.copy()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        config = self.get_current_config()
        issues = []
        
        # Check required fields
        if not config['dremio_url']:
            issues.append('Dremio URL is required')
        
        # Check authentication
        has_pat = bool(config['pat'])
        has_credentials = bool(config['username'] and config['password'])
        
        if not has_pat and not has_credentials:
            issues.append('Either PAT or username/password is required')
        
        # Check project ID for Dremio Cloud
        if config['dremio_type'] == 'cloud' and not config['project_id']:
            issues.append('Project ID is required for Dremio Cloud')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'config': config
        }
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information."""
        return {
            'session_config': self.session_config,
            'current_config': self.get_current_config(),
            'available_projects': self.available_projects,
            'connection_tested': self.connection_tested,
            'validation': self.validate_config()
        }


# Global debug config manager instance
debug_config_manager = DebugConfigManager()
