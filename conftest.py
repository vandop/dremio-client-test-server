"""
Shared test fixtures and configuration for Dremio Reporting Server tests.
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from app import app


@pytest.fixture(scope='session')
def test_app():
    """Create a test Flask application."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask app."""
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def mock_env_config():
    """Mock environment configuration for testing."""
    test_config = {
        'DREMIO_CLOUD_URL': 'https://test.dremio.cloud',
        'DREMIO_USERNAME': 'test@example.com',
        'DREMIO_PASSWORD': 'testpass',
        'DREMIO_PROJECT_ID': 'test-project-123',
        'FLASK_DEBUG': 'true',
        'FLASK_HOST': '0.0.0.0',
        'FLASK_PORT': '5000'
    }
    
    with patch.dict(os.environ, test_config):
        yield test_config


@pytest.fixture
def sample_dremio_jobs():
    """Sample Dremio jobs data for testing."""
    return [
        {
            'id': 'job-001',
            'jobState': 'COMPLETED',
            'queryType': 'SELECT',
            'user': 'test@example.com',
            'startTime': '2023-01-01T10:00:00Z',
            'endTime': '2023-01-01T10:01:00Z',
            'duration': 60000,
            'sql': 'SELECT * FROM test_table LIMIT 10'
        },
        {
            'id': 'job-002',
            'jobState': 'FAILED',
            'queryType': 'CREATE',
            'user': 'admin@example.com',
            'startTime': '2023-01-01T11:00:00Z',
            'endTime': '2023-01-01T11:00:30Z',
            'duration': 30000,
            'sql': 'CREATE TABLE test AS SELECT * FROM source'
        },
        {
            'id': 'job-003',
            'jobState': 'RUNNING',
            'queryType': 'SELECT',
            'user': 'analyst@example.com',
            'startTime': '2023-01-01T12:00:00Z',
            'endTime': None,
            'duration': None,
            'sql': 'SELECT COUNT(*) FROM large_table'
        }
    ]


@pytest.fixture
def sample_query_results():
    """Sample query results for testing."""
    return {
        'simple_select': {
            'status': 'success',
            'data': [{'test_value': 1, 'message': 'Hello Dremio'}],
            'row_count': 1,
            'execution_time': 0.123,
            'columns': ['test_value', 'message']
        },
        'schema_query': {
            'status': 'success',
            'data': [
                {'schema_name': 'public', 'table_count': 5},
                {'schema_name': 'analytics', 'table_count': 12},
                {'schema_name': 'staging', 'table_count': 3}
            ],
            'row_count': 3,
            'execution_time': 0.456,
            'columns': ['schema_name', 'table_count']
        },
        'error_query': {
            'status': 'error',
            'message': 'Table not found: invalid_table',
            'error_code': 'TABLE_NOT_FOUND'
        }
    }


@pytest.fixture
def mock_dremio_hybrid_client():
    """Mock DremioHybridClient for testing."""
    with patch('app.dremio_client') as mock_client:
        # Configure default successful responses
        mock_client.test_connection.return_value = {
            'status': 'success',
            'message': 'Successfully connected to Dremio Cloud'
        }
        
        mock_client.get_jobs.return_value = {
            'success': True,
            'jobs': [],
            'count': 0,
            'message': 'No jobs found'
        }
        
        mock_client.execute_query.return_value = {
            'status': 'success',
            'data': [],
            'row_count': 0,
            'execution_time': 0.0
        }
        
        yield mock_client


@pytest.fixture
def mock_multi_driver_client():
    """Mock DremioMultiDriverClient for testing."""
    with patch('dremio_multi_driver_client.DremioMultiDriverClient') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        # Configure default responses
        mock_instance.execute_query_multi_driver.return_value = {
            'status': 'success',
            'summary': 'Query executed successfully',
            'results': {
                'pyarrow_flight': {
                    'success': True,
                    'driver_name': 'PyArrow Flight SQL',
                    'execution_time': 0.123,
                    'row_count': 1
                }
            }
        }
        
        yield mock_instance


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('config.Config') as mock_config_class:
        mock_config_class.DREMIO_CLOUD_URL = 'https://test.dremio.cloud'
        mock_config_class.DREMIO_USERNAME = 'test@example.com'
        mock_config_class.DREMIO_PASSWORD = 'testpass'
        mock_config_class.DREMIO_PROJECT_ID = 'test-project'
        mock_config_class.FLASK_DEBUG = True
        yield mock_config_class


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_job(job_id='test-job', state='COMPLETED', user='test@example.com'):
        """Create a test job object."""
        return {
            'id': job_id,
            'jobState': state,
            'queryType': 'SELECT',
            'user': user,
            'startTime': '2023-01-01T10:00:00Z',
            'endTime': '2023-01-01T10:01:00Z' if state == 'COMPLETED' else None,
            'duration': 60000 if state == 'COMPLETED' else None,
            'sql': f'SELECT * FROM test_table_{job_id}'
        }
    
    @staticmethod
    def create_query_result(row_count=1, success=True):
        """Create a test query result."""
        if success:
            return {
                'status': 'success',
                'data': [{'id': i, 'value': f'test_{i}'} for i in range(row_count)],
                'row_count': row_count,
                'execution_time': 0.123,
                'columns': ['id', 'value']
            }
        else:
            return {
                'status': 'error',
                'message': 'Query execution failed',
                'error_code': 'EXECUTION_ERROR'
            }


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Database/Connection testing helpers
@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing."""
    connection = MagicMock()
    connection.execute.return_value = MagicMock()
    connection.fetchall.return_value = []
    connection.fetchone.return_value = None
    return connection


# Error simulation fixtures
@pytest.fixture
def connection_error_simulator():
    """Simulate various connection errors."""
    def simulate_error(error_type='timeout'):
        if error_type == 'timeout':
            raise TimeoutError("Connection timed out")
        elif error_type == 'refused':
            raise ConnectionRefusedError("Connection refused")
        elif error_type == 'dns':
            raise Exception("DNS resolution failed")
        else:
            raise Exception(f"Unknown error: {error_type}")
    
    return simulate_error
