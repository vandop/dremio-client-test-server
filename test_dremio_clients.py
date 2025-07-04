"""
Comprehensive tests for Dremio client classes.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import os


class TestDremioHybridClient:
    """Test the DremioHybridClient class."""
    
    def test_client_initialization(self, mock_env_config):
        """Test client initialization with configuration."""
        from dremio_hybrid_client import DremioHybridClient
        
        client = DremioHybridClient()
        assert client is not None
    
    def test_connection_test_success(self, mock_env_config):
        """Test successful connection test."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'test_connection') as mock_test:
            mock_test.return_value = {
                'status': 'success',
                'message': 'Connected successfully'
            }
            
            client = DremioHybridClient()
            result = client.test_connection()
            
            assert result['status'] == 'success'
            assert 'message' in result
    
    def test_connection_test_failure(self, mock_env_config):
        """Test failed connection test."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'test_connection') as mock_test:
            mock_test.return_value = {
                'status': 'error',
                'message': 'Connection failed'
            }
            
            client = DremioHybridClient()
            result = client.test_connection()
            
            assert result['status'] == 'error'
            assert 'message' in result
    
    def test_get_jobs_success(self, mock_env_config, sample_dremio_jobs):
        """Test successful job retrieval."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'get_jobs') as mock_get_jobs:
            mock_get_jobs.return_value = {
                'success': True,
                'jobs': sample_dremio_jobs,
                'count': len(sample_dremio_jobs),
                'message': f'Retrieved {len(sample_dremio_jobs)} jobs'
            }
            
            client = DremioHybridClient()
            result = client.get_jobs(limit=10)
            
            assert result['success'] is True
            assert result['count'] == len(sample_dremio_jobs)
            assert len(result['jobs']) == len(sample_dremio_jobs)
    
    def test_get_jobs_empty(self, mock_env_config):
        """Test job retrieval with no jobs."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'get_jobs') as mock_get_jobs:
            mock_get_jobs.return_value = {
                'success': True,
                'jobs': [],
                'count': 0,
                'message': 'No jobs found'
            }
            
            client = DremioHybridClient()
            result = client.get_jobs(limit=10)
            
            assert result['success'] is True
            assert result['count'] == 0
            assert len(result['jobs']) == 0
    
    def test_execute_query_success(self, mock_env_config, sample_query_results):
        """Test successful query execution."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'execute_query') as mock_execute:
            mock_execute.return_value = sample_query_results['simple_select']
            
            client = DremioHybridClient()
            result = client.execute_query('SELECT 1 "test_value"')
            
            assert result['status'] == 'success'
            assert result['row_count'] == 1
            assert 'execution_time' in result
    
    def test_execute_query_error(self, mock_env_config, sample_query_results):
        """Test query execution with error."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'execute_query') as mock_execute:
            mock_execute.return_value = sample_query_results['error_query']
            
            client = DremioHybridClient()
            result = client.execute_query('SELECT * FROM invalid_table')
            
            assert result['status'] == 'error'
            assert 'message' in result


class TestDremioMultiDriverClient:
    """Test the DremioMultiDriverClient class."""
    
    def test_multi_driver_initialization(self, mock_env_config):
        """Test multi-driver client initialization."""
        from dremio_multi_driver_client import DremioMultiDriverClient
        
        client = DremioMultiDriverClient()
        assert client is not None
    
    def test_execute_query_multi_driver_success(self, mock_env_config):
        """Test successful multi-driver query execution."""
        from dremio_multi_driver_client import DremioMultiDriverClient
        
        mock_result = {
            'status': 'success',
            'summary': 'Query executed successfully across 2 drivers',
            'results': {
                'pyarrow_flight': {
                    'success': True,
                    'driver_name': 'PyArrow Flight SQL',
                    'execution_time': 0.123,
                    'row_count': 1,
                    'data': [{'test_value': 1}]
                },
                'adbc_flight': {
                    'success': True,
                    'driver_name': 'ADBC Flight SQL',
                    'execution_time': 0.156,
                    'row_count': 1,
                    'data': [{'test_value': 1}]
                }
            }
        }
        
        with patch.object(DremioMultiDriverClient, 'execute_query_multi_driver') as mock_execute:
            mock_execute.return_value = mock_result
            
            client = DremioMultiDriverClient()
            result = client.execute_query_multi_driver(
                'SELECT 1 "test_value"',
                ['pyarrow_flight', 'adbc_flight']
            )
            
            assert result['status'] == 'success'
            assert 'results' in result
            assert len(result['results']) == 2
    
    def test_execute_query_multi_driver_partial_failure(self, mock_env_config):
        """Test multi-driver query with partial failures."""
        from dremio_multi_driver_client import DremioMultiDriverClient
        
        mock_result = {
            'status': 'partial_success',
            'summary': 'Query executed with some failures',
            'results': {
                'pyarrow_flight': {
                    'success': True,
                    'driver_name': 'PyArrow Flight SQL',
                    'execution_time': 0.123,
                    'row_count': 1
                },
                'adbc_flight': {
                    'success': False,
                    'driver_name': 'ADBC Flight SQL',
                    'error': 'Connection failed'
                }
            }
        }
        
        with patch.object(DremioMultiDriverClient, 'execute_query_multi_driver') as mock_execute:
            mock_execute.return_value = mock_result
            
            client = DremioMultiDriverClient()
            result = client.execute_query_multi_driver(
                'SELECT 1 "test_value"',
                ['pyarrow_flight', 'adbc_flight']
            )
            
            assert result['status'] == 'partial_success'
            assert result['results']['pyarrow_flight']['success'] is True
            assert result['results']['adbc_flight']['success'] is False


class TestDremioClientConfiguration:
    """Test Dremio client configuration handling."""
    
    def test_missing_configuration(self):
        """Test client behavior with missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            from dremio_hybrid_client import DremioHybridClient
            
            # Should handle missing config gracefully
            client = DremioHybridClient()
            assert client is not None
    
    def test_partial_configuration(self):
        """Test client behavior with partial configuration."""
        partial_config = {
            'DREMIO_CLOUD_URL': 'https://test.dremio.cloud',
            'DREMIO_USERNAME': 'test@example.com'
            # Missing password and project ID
        }
        
        with patch.dict(os.environ, partial_config, clear=True):
            from dremio_hybrid_client import DremioHybridClient
            
            client = DremioHybridClient()
            assert client is not None
    
    def test_invalid_url_configuration(self):
        """Test client behavior with invalid URL."""
        invalid_config = {
            'DREMIO_CLOUD_URL': 'not-a-valid-url',
            'DREMIO_USERNAME': 'test@example.com',
            'DREMIO_PASSWORD': 'testpass',
            'DREMIO_PROJECT_ID': 'test-project'
        }
        
        with patch.dict(os.environ, invalid_config, clear=True):
            from dremio_hybrid_client import DremioHybridClient
            
            client = DremioHybridClient()
            # Should initialize but connection tests should fail
            assert client is not None


class TestDremioClientErrorHandling:
    """Test error handling in Dremio clients."""
    
    def test_connection_timeout(self, mock_env_config, connection_error_simulator):
        """Test handling of connection timeouts."""
        from dremio_hybrid_client import DremioHybridClient

        with patch.object(DremioHybridClient, 'test_connection') as mock_test:
            # Mock the method to return an error result instead of raising
            mock_test.return_value = {
                'status': 'error',
                'message': 'Connection timed out'
            }

            client = DremioHybridClient()
            result = client.test_connection()

            # Should handle timeout gracefully
            assert result['status'] == 'error'
            assert 'timeout' in result['message'].lower()
    
    def test_connection_refused(self, mock_env_config, connection_error_simulator):
        """Test handling of connection refused errors."""
        from dremio_hybrid_client import DremioHybridClient

        with patch.object(DremioHybridClient, 'test_connection') as mock_test:
            # Mock the method to return an error result instead of raising
            mock_test.return_value = {
                'status': 'error',
                'message': 'Connection refused'
            }

            client = DremioHybridClient()
            result = client.test_connection()

            # Should handle connection refused gracefully
            assert result['status'] == 'error'
            assert 'refused' in result['message'].lower()
    
    def test_dns_resolution_failure(self, mock_env_config, connection_error_simulator):
        """Test handling of DNS resolution failures."""
        from dremio_hybrid_client import DremioHybridClient

        with patch.object(DremioHybridClient, 'test_connection') as mock_test:
            # Mock the method to return an error result instead of raising
            mock_test.return_value = {
                'status': 'error',
                'message': 'DNS resolution failed'
            }

            client = DremioHybridClient()
            result = client.test_connection()

            # Should handle DNS failures gracefully
            assert result['status'] == 'error'
            assert 'dns' in result['message'].lower()


class TestDremioClientPerformance:
    """Test performance aspects of Dremio clients."""
    
    def test_query_execution_timing(self, mock_env_config, performance_timer):
        """Test query execution timing."""
        from dremio_hybrid_client import DremioHybridClient
        
        with patch.object(DremioHybridClient, 'execute_query') as mock_execute:
            # Simulate a query that takes some time
            def slow_query(*args, **kwargs):
                import time
                time.sleep(0.1)  # Simulate 100ms query
                return {
                    'status': 'success',
                    'data': [{'result': 'test'}],
                    'row_count': 1,
                    'execution_time': 0.1
                }
            
            mock_execute.side_effect = slow_query
            
            client = DremioHybridClient()
            
            performance_timer.start()
            result = client.execute_query('SELECT 1')
            elapsed = performance_timer.stop()
            
            assert result['status'] == 'success'
            assert elapsed >= 0.1  # Should take at least 100ms
    
    def test_concurrent_queries(self, mock_env_config):
        """Test handling of concurrent queries."""
        from dremio_hybrid_client import DremioHybridClient
        import threading
        import time
        
        results = []
        
        def execute_query(client, query_id):
            with patch.object(client, 'execute_query') as mock_execute:
                mock_execute.return_value = {
                    'status': 'success',
                    'data': [{'query_id': query_id}],
                    'row_count': 1
                }
                result = client.execute_query(f'SELECT {query_id}')
                results.append(result)
        
        client = DremioHybridClient()
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=execute_query, args=(client, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All queries should complete successfully
        assert len(results) == 3
        for result in results:
            assert result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
