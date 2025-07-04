"""
Integration tests for Dremio Reporting Server.
Tests end-to-end workflows and component interactions.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
import threading


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_complete_reporting_workflow(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test complete workflow from connection test to report generation."""
        # Step 1: Test connection
        mock_dremio_hybrid_client.test_connection.return_value = {
            'status': 'success',
            'message': 'Connected successfully'
        }
        
        connection_response = client.get('/api/test-connection')
        assert connection_response.status_code == 200
        assert connection_response.get_json()['status'] == 'success'
        
        # Step 2: Fetch jobs
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': sample_dremio_jobs,
            'count': len(sample_dremio_jobs),
            'message': f'Retrieved {len(sample_dremio_jobs)} jobs'
        }
        
        jobs_response = client.get('/api/jobs?limit=10')
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.get_json()
        assert jobs_data['status'] == 'success'
        assert len(jobs_data['jobs']) == len(sample_dremio_jobs)
        
        # Step 3: Execute a query
        mock_dremio_hybrid_client.execute_query.return_value = {
            'status': 'success',
            'data': [{'count': len(sample_dremio_jobs)}],
            'row_count': 1,
            'execution_time': 0.123
        }
        
        query_response = client.post('/api/query',
                                   json={'sql': 'SELECT COUNT(*) "count" FROM sys.jobs'},
                                   headers={'Content-Type': 'application/json'})
        
        assert query_response.status_code == 200
        query_data = query_response.get_json()
        assert query_data['status'] == 'success'
    
    def test_error_recovery_workflow(self, client, mock_dremio_hybrid_client):
        """Test error recovery in workflows."""
        # Step 1: Connection fails
        mock_dremio_hybrid_client.test_connection.return_value = {
            'status': 'error',
            'message': 'Connection failed'
        }
        
        connection_response = client.get('/api/test-connection')
        assert connection_response.status_code == 200
        assert connection_response.get_json()['status'] == 'error'
        
        # Step 2: Jobs request should still work (might use cached data or different endpoint)
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': False,
            'jobs': [],
            'count': 0,
            'message': 'Failed to retrieve jobs due to connection error'
        }
        
        jobs_response = client.get('/api/jobs?limit=10')
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.get_json()
        assert jobs_data['status'] == 'error'
        
        # Step 3: Recovery - connection restored
        mock_dremio_hybrid_client.test_connection.return_value = {
            'status': 'success',
            'message': 'Connection restored'
        }
        
        recovery_response = client.get('/api/test-connection')
        assert recovery_response.status_code == 200
        assert recovery_response.get_json()['status'] == 'success'
    
    def test_multi_user_workflow_simulation(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test workflow simulation for multiple users."""
        # Simulate different users accessing the system
        user_jobs = {
            'user1': [job for job in sample_dremio_jobs if job['user'] == 'test@example.com'],
            'user2': [job for job in sample_dremio_jobs if job['user'] == 'admin@example.com'],
            'user3': [job for job in sample_dremio_jobs if job['user'] == 'analyst@example.com']
        }
        
        for user, jobs in user_jobs.items():
            # Mock user-specific job retrieval
            mock_dremio_hybrid_client.get_jobs.return_value = {
                'success': True,
                'jobs': jobs,
                'count': len(jobs),
                'message': f'Retrieved {len(jobs)} jobs for {user}'
            }
            
            # Simulate user request
            response = client.get(f'/api/jobs?limit=10&user={user}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'


class TestComponentIntegration:
    """Test integration between different components."""
    
    def test_client_and_app_integration(self, client, mock_env_config):
        """Test integration between Dremio clients and Flask app."""
        # Test that the app correctly uses the client
        with patch('app.dremio_client') as mock_client:
            mock_client.test_connection.return_value = {
                'status': 'success',
                'message': 'Integration test successful'
            }
            
            response = client.get('/api/test-connection')
            assert response.status_code == 200
            
            # Verify the client method was called
            mock_client.test_connection.assert_called_once()
    
    def test_config_and_client_integration(self, mock_env_config):
        """Test integration between configuration and client initialization."""
        from dremio_hybrid_client import DremioHybridClient
        
        # Test that client uses configuration correctly
        client = DremioHybridClient()
        assert client is not None
        
        # In a real implementation, you'd verify that the client
        # uses the configuration values correctly
    
    def test_reports_and_data_integration(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test integration between reports module and data retrieval."""
        # Mock data retrieval
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': sample_dremio_jobs,
            'count': len(sample_dremio_jobs),
            'message': 'Data retrieved for reports'
        }
        
        # Test reports page
        reports_response = client.get('/reports')
        assert reports_response.status_code == 200
        
        # Test API integration
        api_response = client.get('/api/jobs?limit=10')
        assert api_response.status_code == 200
        
        data = api_response.get_json()
        assert data['status'] == 'success'
        assert len(data['jobs']) == len(sample_dremio_jobs)


class TestPerformanceIntegration:
    """Test performance aspects of integrated components."""
    
    def test_concurrent_requests(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test handling of concurrent requests."""
        # Mock responses
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': sample_dremio_jobs,
            'count': len(sample_dremio_jobs),
            'message': 'Concurrent request handled'
        }
        
        results = []
        errors = []
        
        def make_request(request_id):
            """Make a request and store the result."""
            try:
                response = client.get(f'/api/jobs?limit=5&request_id={request_id}')
                results.append({
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_time': time.time()
                })
            except Exception as e:
                errors.append({
                    'request_id': request_id,
                    'error': str(e)
                })
        
        # Start multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests completed successfully
        assert len(results) == 5
        assert len(errors) == 0
        
        for result in results:
            assert result['status_code'] == 200
    
    def test_large_dataset_handling(self, client, mock_dremio_hybrid_client):
        """Test handling of large datasets."""
        # Create a large dataset
        large_job_list = []
        for i in range(1000):
            large_job_list.append({
                'id': f'job-{i:04d}',
                'jobState': 'COMPLETED',
                'queryType': 'SELECT',
                'user': f'user{i % 10}@example.com',
                'startTime': '2023-01-01T10:00:00Z',
                'endTime': '2023-01-01T10:01:00Z',
                'duration': 60000 + (i * 100),
                'sql': f'SELECT * FROM table_{i}'
            })
        
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': large_job_list,
            'count': len(large_job_list),
            'message': f'Retrieved {len(large_job_list)} jobs'
        }
        
        # Test with large dataset
        start_time = time.time()
        response = client.get('/api/jobs?limit=1000')
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['count'] == 1000
        
        # Verify reasonable response time (adjust threshold as needed)
        response_time = end_time - start_time
        assert response_time < 5.0  # Should complete within 5 seconds
    
    def test_memory_usage_during_operations(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test memory usage during various operations."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': sample_dremio_jobs,
            'count': len(sample_dremio_jobs),
            'message': 'Memory test'
        }
        
        # Make multiple requests
        for i in range(10):
            response = client.get('/api/jobs?limit=10')
            assert response.status_code == 200
        
        # Check memory usage after operations
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100 * 1024 * 1024  # 100MB


class TestDataConsistency:
    """Test data consistency across different operations."""
    
    def test_job_data_consistency(self, client, mock_dremio_hybrid_client, sample_dremio_jobs):
        """Test consistency of job data across different endpoints."""
        # Mock consistent data
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': sample_dremio_jobs,
            'count': len(sample_dremio_jobs),
            'message': 'Consistent data test'
        }
        
        # Get jobs from API
        api_response = client.get('/api/jobs?limit=10')
        assert api_response.status_code == 200
        api_data = api_response.get_json()
        
        # Verify data structure consistency
        for job in api_data['jobs']:
            assert 'id' in job
            assert 'jobState' in job
            assert 'user' in job
            assert 'queryType' in job
            
            # Verify data types
            assert isinstance(job['id'], str)
            assert isinstance(job['jobState'], str)
            assert isinstance(job['user'], str)
    
    def test_query_result_consistency(self, client, mock_dremio_hybrid_client):
        """Test consistency of query results."""
        consistent_result = {
            'status': 'success',
            'data': [{'test_value': 1, 'message': 'consistent'}],
            'row_count': 1,
            'execution_time': 0.123
        }
        
        mock_dremio_hybrid_client.execute_query.return_value = consistent_result
        
        # Execute same query multiple times
        query = 'SELECT 1 "test_value", \'consistent\' "message"'
        
        for i in range(3):
            response = client.post('/api/query',
                                 json={'sql': query},
                                 headers={'Content-Type': 'application/json'})
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Results should be consistent
            assert data['status'] == 'success'
            assert data['row_count'] == 1
            assert data['data'][0]['test_value'] == 1
            assert data['data'][0]['message'] == 'consistent'


class TestErrorPropagation:
    """Test error propagation across components."""
    
    def test_client_error_propagation(self, client, mock_dremio_hybrid_client):
        """Test that client errors are properly propagated to the API."""
        # Mock client error
        mock_dremio_hybrid_client.test_connection.side_effect = Exception("Client connection error")
        
        response = client.get('/api/test-connection')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Client connection error' in data['message']
    
    def test_configuration_error_propagation(self, client):
        """Test that configuration errors are properly handled."""
        # Test with missing configuration
        with patch.dict('os.environ', {}, clear=True):
            response = client.get('/api/test-connection')
            assert response.status_code == 200
            
            # Should handle missing config gracefully
            data = response.get_json()
            # The exact behavior depends on implementation
            assert 'status' in data
    
    def test_database_error_propagation(self, client, mock_dremio_hybrid_client):
        """Test that database errors are properly propagated."""
        # Mock database error
        mock_dremio_hybrid_client.execute_query.side_effect = Exception("Database query failed")
        
        response = client.post('/api/query',
                             json={'sql': 'SELECT * FROM invalid_table'},
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Database query failed' in data['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
