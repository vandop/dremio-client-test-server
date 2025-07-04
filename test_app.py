"""
Comprehensive tests for the Dremio Reporting Server Flask application.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_dremio_client():
    """Mock Dremio client for testing."""
    with patch('app.dremio_client') as mock_client:
        yield mock_client


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


def test_test_connection_with_config(client, mock_dremio_client):
    """Test the connection test endpoint with proper configuration."""
    # Mock successful connection
    mock_dremio_client.test_connection.return_value = {
        'status': 'success',
        'message': 'Successfully connected to Dremio Cloud'
    }

    response = client.get('/api/test-connection')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data


def test_test_connection_with_error(client, mock_dremio_client):
    """Test the connection test endpoint when connection fails."""
    # Mock failed connection
    mock_dremio_client.test_connection.return_value = {
        'status': 'error',
        'message': 'Failed to connect to Dremio Cloud'
    }

    response = client.get('/api/test-connection')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data


def test_test_connection_exception(client, mock_dremio_client):
    """Test the connection test endpoint when an exception occurs."""
    # Mock exception
    mock_dremio_client.test_connection.side_effect = Exception("Connection error")

    response = client.get('/api/test-connection')
    assert response.status_code == 500  # App returns 500 for exceptions
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Connection error' in data['message']


def test_get_jobs_api_success(client, mock_dremio_client):
    """Test the jobs API endpoint with successful response."""
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

    # Mock the return format
    mock_result = {
        'success': True,
        'jobs': mock_jobs,
        'count': len(mock_jobs),
        'message': 'Successfully retrieved 1 jobs'
    }

    mock_dremio_client.get_jobs.return_value = mock_result

    response = client.get('/api/jobs?limit=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['count'] == 1
    assert len(data['jobs']) == 1
    assert data['jobs'][0]['id'] == 'job-1'


def test_get_jobs_api_error(client, mock_dremio_client):
    """Test the jobs API endpoint with error response."""
    mock_result = {
        'success': False,
        'jobs': [],
        'count': 0,
        'message': 'Failed to retrieve jobs'
    }

    mock_dremio_client.get_jobs.return_value = mock_result

    response = client.get('/api/jobs?limit=10')
    assert response.status_code == 400  # App returns 400 for failed operations
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Failed to retrieve jobs' in data['message']


def test_get_jobs_api_exception(client, mock_dremio_client):
    """Test the jobs API endpoint when an exception occurs."""
    mock_dremio_client.get_jobs.side_effect = Exception("API error")

    response = client.get('/api/jobs?limit=10')
    assert response.status_code == 500  # App returns 500 for exceptions
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'API error' in data['message']


def test_query_page(client):
    """Test the query page loads correctly."""
    response = client.get('/query')
    assert response.status_code == 200
    assert b'SQL Query' in response.data or b'Query' in response.data


def test_debug_page(client):
    """Test the debug page loads correctly."""
    response = client.get('/debug')
    assert response.status_code == 200


def test_api_query_endpoint(client, mock_dremio_client):
    """Test the SQL query API endpoint."""
    mock_result = {
        'success': True,
        'data': [{'test_value': 1}],
        'row_count': 1,
        'columns': ['test_value'],
        'query': 'SELECT 1 "test_value" LIMIT 1000',
        'message': 'Query executed successfully'
    }

    mock_dremio_client.execute_query.return_value = mock_result

    response = client.post('/api/query',
                          json={'sql': 'SELECT 1 "test_value"'},
                          headers={'Content-Type': 'application/json'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['row_count'] == 1


def test_api_query_multi_driver(client):
    """Test the multi-driver query API endpoint."""
    with patch('app.DremioMultiDriverClient') as mock_multi_client:
        mock_instance = MagicMock()
        mock_multi_client.return_value = mock_instance

        # Mock available drivers
        mock_instance.get_available_drivers.return_value = {
            'pyarrow_flight': {'name': 'PyArrow Flight SQL', 'available': True}
        }

        # Mock query execution results
        mock_result = {
            'pyarrow_flight': {
                'success': True,
                'driver_name': 'PyArrow Flight SQL',
                'execution_time': 0.123
            }
        }

        mock_instance.execute_query_multi_driver.return_value = mock_result

        response = client.post('/api/query-multi-driver',
                              json={
                                  'sql': 'SELECT 1 "test_value"',
                                  'drivers': ['pyarrow_flight']
                              },
                              headers={'Content-Type': 'application/json'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'


def test_invalid_json_request(client):
    """Test API endpoints with invalid JSON."""
    response = client.post('/api/query',
                          data='invalid json',
                          headers={'Content-Type': 'application/json'})

    assert response.status_code == 500  # Flask returns 500 for JSON decode errors


def test_missing_sql_parameter(client):
    """Test query API endpoint with missing SQL parameter."""
    response = client.post('/api/query',
                          json={},
                          headers={'Content-Type': 'application/json'})

    assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__])
