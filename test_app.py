"""
Basic tests for the Dremio Reporting Server.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test the main index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello World - Dremio Reporting Server' in response.data


def test_reports_page(client):
    """Test the reports page loads correctly."""
    response = client.get('/reports')
    assert response.status_code == 200
    assert b'Dremio Jobs Report' in response.data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'Dremio Reporting Server'


@patch.dict(os.environ, {
    'DREMIO_CLOUD_URL': 'https://test.dremio.cloud',
    'DREMIO_USERNAME': 'test@example.com',
    'DREMIO_PASSWORD': 'testpass',
    'DREMIO_PROJECT_ID': 'test-project'
})
def test_test_connection_with_config(client):
    """Test the connection test endpoint with proper configuration."""
    with patch('dremio_client.DremioClient.test_connection') as mock_test:
        mock_test.return_value = {
            'status': 'success',
            'message': 'Successfully connected to Dremio Cloud'
        }
        
        response = client.get('/api/test-connection')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'


def test_test_connection_without_config(client):
    """Test the connection test endpoint without proper configuration."""
    # Clear environment variables
    with patch.dict(os.environ, {}, clear=True):
        response = client.get('/api/test-connection')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'error'


@patch.dict(os.environ, {
    'DREMIO_CLOUD_URL': 'https://test.dremio.cloud',
    'DREMIO_USERNAME': 'test@example.com',
    'DREMIO_PASSWORD': 'testpass',
    'DREMIO_PROJECT_ID': 'test-project'
})
def test_get_jobs_api(client):
    """Test the jobs API endpoint."""
    mock_jobs = [
        {
            'id': 'job-1',
            'jobState': 'COMPLETED',
            'queryType': 'SELECT',
            'user': 'test@example.com',
            'startTime': '2023-01-01T10:00:00Z',
            'endTime': '2023-01-01T10:01:00Z'
        }
    ]
    
    with patch('dremio_client.DremioClient.get_jobs') as mock_get_jobs:
        mock_get_jobs.return_value = mock_jobs
        
        response = client.get('/api/jobs?limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['count'] == 1
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['id'] == 'job-1'


if __name__ == '__main__':
    pytest.main([__file__])
