"""
Dremio Cloud API client for connecting and retrieving job information.
"""
import requests
import json
from typing import Dict, List, Optional
from config import Config


class DremioClient:
    """Client for interacting with Dremio Cloud API."""
    
    def __init__(self):
        """Initialize the Dremio client with configuration."""
        self.base_url = Config.DREMIO_CLOUD_URL
        self.username = Config.DREMIO_USERNAME
        self.password = Config.DREMIO_PASSWORD
        self.project_id = Config.DREMIO_PROJECT_ID
        self.token = None
        self.session = requests.Session()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Dremio Cloud and obtain access token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            auth_url = f"{self.base_url}/apiv2/login"
            auth_data = {
                "userName": self.username,
                "password": self.password
            }
            
            response = self.session.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.token = auth_result.get('token')
            
            if self.token:
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'_dremio{self.token}',
                    'Content-Type': 'application/json'
                })
                return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_jobs(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve jobs from the Dremio project.
        
        Args:
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of job dictionaries
        """
        if not self.token:
            if not self.authenticate():
                return []
        
        try:
            jobs_url = f"{self.base_url}/api/v3/projects/{self.project_id}/jobs"
            params = {
                'limit': limit,
                'offset': 0
            }
            
            response = self.session.get(jobs_url, params=params)
            response.raise_for_status()
            
            jobs_data = response.json()
            return jobs_data.get('jobs', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve jobs: {e}")
            return []
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific job.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            Job details dictionary or None if not found
        """
        if not self.token:
            if not self.authenticate():
                return None
        
        try:
            job_url = f"{self.base_url}/api/v3/projects/{self.project_id}/jobs/{job_id}"
            
            response = self.session.get(job_url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve job {job_id}: {e}")
            return None
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test the connection to Dremio Cloud.
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            Config.validate_dremio_config()
            
            if self.authenticate():
                # Try to get a small number of jobs to test the connection
                jobs = self.get_jobs(limit=1)
                return {
                    'status': 'success',
                    'message': 'Successfully connected to Dremio Cloud',
                    'jobs_accessible': len(jobs) >= 0
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Authentication failed'
                }
                
        except ValueError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection test failed: {str(e)}'
            }
