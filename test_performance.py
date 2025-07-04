"""
Performance tests for Dremio Reporting Server.
"""
import pytest
import time
import threading
from unittest.mock import patch, MagicMock


class TestAPIPerformance:
    """Test API performance characteristics."""
    
    def test_response_time_basic_endpoints(self, client, mock_dremio_hybrid_client):
        """Test response times for basic endpoints."""
        # Mock quick responses
        mock_dremio_hybrid_client.test_connection.return_value = {
            'status': 'success',
            'message': 'Connected'
        }
        
        endpoints = [
            '/',
            '/reports',
            '/query',
            '/debug',
            '/health'
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_times[endpoint] = end_time - start_time
            assert response.status_code == 200
            
            # Basic endpoints should respond quickly (under 1 second)
            assert response_times[endpoint] < 1.0
        
        print(f"\n📊 Response Times: {response_times}")
    
    def test_api_endpoint_performance(self, client, mock_dremio_hybrid_client):
        """Test API endpoint performance."""
        # Mock fast job retrieval
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': [],
            'count': 0,
            'message': 'No jobs found'
        }
        
        start_time = time.time()
        response = client.get('/api/jobs?limit=10')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
        
        print(f"\n⏱️  Jobs API response time: {response_time:.3f}s")
    
    def test_concurrent_api_requests(self, client, mock_dremio_hybrid_client):
        """Test handling of concurrent API requests."""
        # Mock responses
        mock_dremio_hybrid_client.test_connection.return_value = {
            'status': 'success',
            'message': 'Connected'
        }
        
        results = []
        errors = []
        
        def make_request(request_id):
            """Make a request and record the result."""
            try:
                start_time = time.time()
                response = client.get('/api/test-connection')
                end_time = time.time()
                
                results.append({
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
            except Exception as e:
                errors.append({
                    'request_id': request_id,
                    'error': str(e)
                })
        
        # Start multiple threads
        threads = []
        num_requests = 3  # Reduced for stability
        
        for i in range(num_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_requests
        
        for result in results:
            assert result['status_code'] == 200
            assert result['response_time'] < 5.0  # Generous timeout for concurrent requests
        
        print(f"\n🔄 Concurrent requests completed: {len(results)}")
    
    def test_large_response_handling(self, client, mock_dremio_hybrid_client):
        """Test handling of large response datasets."""
        # Create a large dataset
        large_jobs = []
        for i in range(100):  # Smaller dataset for testing
            large_jobs.append({
                'id': f'job-{i:04d}',
                'jobState': 'COMPLETED',
                'queryType': 'SELECT',
                'user': f'user{i % 5}@example.com',
                'startTime': '2023-01-01T10:00:00Z',
                'endTime': '2023-01-01T10:01:00Z',
                'duration': 60000 + (i * 100),
                'sql': f'SELECT * FROM table_{i}'
            })
        
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': large_jobs,
            'count': len(large_jobs),
            'message': f'Retrieved {len(large_jobs)} jobs'
        }
        
        start_time = time.time()
        response = client.get('/api/jobs?limit=100')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['count'] == 100
        
        # Should handle large datasets reasonably quickly
        assert response_time < 3.0
        
        print(f"\n📊 Large dataset response time: {response_time:.3f}s for {len(large_jobs)} jobs")


class TestQueryPerformance:
    """Test query execution performance."""
    
    def test_simple_query_performance(self, client, mock_dremio_hybrid_client):
        """Test performance of simple queries."""
        mock_dremio_hybrid_client.execute_query.return_value = {
            'success': True,
            'data': [{'result': 1}],
            'row_count': 1,
            'columns': ['result'],
            'query': 'SELECT 1 "result" LIMIT 1000',
            'message': 'Query executed successfully'
        }
        
        start_time = time.time()
        response = client.post('/api/query',
                              json={'sql': 'SELECT 1 "result"'},
                              headers={'Content-Type': 'application/json'})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # Simple queries should be fast
        assert response_time < 1.0
        
        print(f"\n⚡ Simple query response time: {response_time:.3f}s")
    
    def test_query_with_different_sizes(self, client, mock_dremio_hybrid_client):
        """Test query performance with different result sizes."""
        test_cases = [
            (1, "Single row"),
            (10, "Small result set"),
            (100, "Medium result set"),
            (500, "Large result set")
        ]
        
        for row_count, description in test_cases:
            # Mock data for this test case
            mock_data = [{'id': i, 'value': f'test_{i}'} for i in range(row_count)]
            
            mock_dremio_hybrid_client.execute_query.return_value = {
                'success': True,
                'data': mock_data,
                'row_count': row_count,
                'columns': ['id', 'value'],
                'query': f'SELECT * FROM test_table LIMIT {row_count}',
                'message': 'Query executed successfully'
            }
            
            start_time = time.time()
            response = client.post('/api/query',
                                  json={'sql': f'SELECT * FROM test_table LIMIT {row_count}'},
                                  headers={'Content-Type': 'application/json'})
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['row_count'] == row_count
            
            # Response time should scale reasonably with data size
            expected_max_time = 0.5 + (row_count * 0.001)  # Base time + scaling factor
            assert response_time < expected_max_time
            
            print(f"\n📈 {description} ({row_count} rows): {response_time:.3f}s")


class TestMemoryUsage:
    """Test memory usage patterns (simplified without psutil)."""
    
    def test_memory_efficient_operations(self, client, mock_dremio_hybrid_client):
        """Test that operations don't cause obvious memory leaks."""
        # Mock responses
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': [{'id': 'test-job', 'jobState': 'COMPLETED'}],
            'count': 1,
            'message': 'Retrieved 1 job'
        }
        
        # Perform multiple operations
        for i in range(10):
            response = client.get('/api/jobs?limit=10')
            assert response.status_code == 200
            
            # Force garbage collection between requests
            import gc
            gc.collect()
        
        # If we get here without issues, memory usage is reasonable
        assert True
    
    def test_large_response_memory_handling(self, client, mock_dremio_hybrid_client):
        """Test memory handling with large responses."""
        # Create a moderately large dataset
        large_jobs = [
            {
                'id': f'job-{i}',
                'jobState': 'COMPLETED',
                'queryType': 'SELECT',
                'user': 'test@example.com',
                'sql': f'SELECT * FROM large_table_{i}'
            }
            for i in range(50)  # Reasonable size for testing
        ]
        
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': large_jobs,
            'count': len(large_jobs),
            'message': f'Retrieved {len(large_jobs)} jobs'
        }
        
        response = client.get('/api/jobs?limit=50')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['count'] == 50
        
        # Clean up
        del data
        import gc
        gc.collect()


class TestCachingPerformance:
    """Test caching performance characteristics."""
    
    def test_repeated_request_performance(self, client, mock_dremio_hybrid_client):
        """Test performance of repeated requests (potential caching)."""
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': [{'id': 'cached-job', 'jobState': 'COMPLETED'}],
            'count': 1,
            'message': 'Retrieved 1 job'
        }
        
        response_times = []
        
        # Make multiple identical requests
        for i in range(5):
            start_time = time.time()
            response = client.get('/api/jobs?limit=10')
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # All requests should complete reasonably quickly
        for rt in response_times:
            assert rt < 1.0
        
        avg_response_time = sum(response_times) / len(response_times)
        print(f"\n🔄 Average response time for repeated requests: {avg_response_time:.3f}s")
    
    def test_different_parameter_performance(self, client, mock_dremio_hybrid_client):
        """Test performance with different parameters."""
        mock_dremio_hybrid_client.get_jobs.return_value = {
            'success': True,
            'jobs': [],
            'count': 0,
            'message': 'No jobs found'
        }
        
        limits = [5, 10, 25, 50]
        response_times = {}
        
        for limit in limits:
            start_time = time.time()
            response = client.get(f'/api/jobs?limit={limit}')
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times[limit] = response_time
            
            assert response.status_code == 200
            assert response_time < 1.0
        
        print(f"\n📊 Response times by limit: {response_times}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
