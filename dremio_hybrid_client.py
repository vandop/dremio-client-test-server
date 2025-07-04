"""
Hybrid Dremio client using both PyArrow Flight SQL and REST API.
- PyArrow Flight SQL for data queries and analytics
- REST API for job information and metadata
"""
import logging
from typing import Dict, List, Optional, Any
from dremio_pyarrow_client import DremioPyArrowClient
from dremio_client import DremioClient
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DremioHybridClient:
    """
    Hybrid Dremio client combining PyArrow Flight SQL and REST API.
    
    Uses:
    - PyArrow Flight SQL for data queries, analytics, and schema discovery
    - REST API for job information, project metadata, and system operations
    """
    
    def __init__(self):
        """Initialize both Flight SQL and REST API clients."""
        self.flight_client = DremioPyArrowClient()
        self.rest_client = DremioClient()
        
        logger.info("✓ Hybrid Dremio client initialized")
        logger.info("  - PyArrow Flight SQL for data queries")
        logger.info("  - REST API for job information")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test both Flight SQL and REST API connections.
        
        Returns:
            Comprehensive connection test results
        """
        logger.info("=== Starting Hybrid Dremio Connection Test ===")
        
        # Test Flight SQL connection
        logger.info("Testing PyArrow Flight SQL connection...")
        flight_result = self.flight_client.test_connection()
        
        # Test REST API connection
        logger.info("Testing REST API connection...")
        rest_result = self.rest_client.test_connection()
        
        # Combine results
        both_successful = (
            flight_result.get('status') == 'success' and 
            rest_result.get('status') == 'success'
        )
        
        if both_successful:
            logger.info("✓ Both Flight SQL and REST API connections successful")
            return {
                'status': 'success',
                'message': 'Successfully connected using hybrid approach (Flight SQL + REST API)',
                'details': {
                    'flight_sql': flight_result['details'],
                    'rest_api': rest_result['details'],
                    'capabilities': {
                        'data_queries': True,
                        'job_information': True,
                        'project_metadata': True,
                        'schema_discovery': True
                    }
                },
                'steps_completed': ['flight_sql_test', 'rest_api_test']
            }
        else:
            # Determine which failed
            failed_components = []
            if flight_result.get('status') != 'success':
                failed_components.append('Flight SQL')
            if rest_result.get('status') != 'success':
                failed_components.append('REST API')
            
            return {
                'status': 'error',
                'message': f'Connection failed for: {", ".join(failed_components)}',
                'details': {
                    'flight_sql': flight_result,
                    'rest_api': rest_result
                },
                'failed_components': failed_components
            }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query using PyArrow Flight SQL.

        Args:
            sql: SQL query to execute

        Returns:
            Query results
        """
        logger.info(f"Executing SQL query via Hybrid Client (Flight SQL): {sql}")
        # The PyArrow Flight client will add its own driver comment
        return self.flight_client.execute_query(sql)
    
    def get_jobs(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get jobs using REST API (since SYS.Jobs is not available in Dremio Cloud).
        
        Args:
            limit: Maximum number of jobs to retrieve
            
        Returns:
            Jobs data from REST API
        """
        logger.info(f"Getting jobs via REST API (limit: {limit})")
        return self.rest_client.get_jobs(limit=limit)
    
    def get_projects(self) -> Dict[str, Any]:
        """
        Get projects using REST API.
        
        Returns:
            Projects data from REST API
        """
        logger.info("Getting projects via REST API")
        return self.rest_client.get_projects()
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details using REST API.
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            Job details from REST API
        """
        logger.info(f"Getting job details via REST API: {job_id}")
        return self.rest_client.get_job_details(job_id)
    
    def get_schemas(self) -> Dict[str, Any]:
        """
        Get available schemas using Flight SQL.
        
        Returns:
            Schema information from Flight SQL
        """
        logger.info("Getting schemas via Flight SQL")
        result = self.flight_client.execute_query("SHOW SCHEMAS")
        
        if result['success']:
            schemas = [row.get('Schema', row.get('SCHEMA_NAME', str(row))) for row in result['data']]
            return {
                'success': True,
                'schemas': schemas,
                'count': len(schemas),
                'message': f'Found {len(schemas)} schemas',
                'query_method': 'flight_sql'
            }
        else:
            return result
    
    def query_data_source(self, source_name: str, limit: int = 100) -> Dict[str, Any]:
        """
        Query a data source using Flight SQL.
        
        Args:
            source_name: Name of the data source/table to query
            limit: Maximum number of rows to return
            
        Returns:
            Query results
        """
        sql = f"SELECT * FROM {source_name} LIMIT {limit}"
        logger.info(f"Querying data source via Flight SQL: {source_name}")
        return self.flight_client.execute_query(sql)
    
    def get_table_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get table information for a schema using Flight SQL.
        
        Args:
            schema_name: Schema name to explore
            
        Returns:
            Table information
        """
        sql = f"SHOW TABLES IN {schema_name}"
        logger.info(f"Getting table info via Flight SQL for schema: {schema_name}")
        return self.flight_client.execute_query(sql)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this hybrid client.
        
        Returns:
            Dictionary describing available capabilities
        """
        return {
            'flight_sql_capabilities': [
                'Execute SQL queries on data sources',
                'Schema and table discovery',
                'High-performance data analytics',
                'Native Arrow format results',
                'Streaming large datasets'
            ],
            'rest_api_capabilities': [
                'Job information and history',
                'Project metadata and permissions',
                'System configuration',
                'User and security management',
                'Reflection and acceleration info'
            ],
            'combined_benefits': [
                'Best of both worlds - SQL queries + metadata',
                'Optimal performance for different use cases',
                'Complete Dremio Cloud functionality',
                'Fallback options for different operations'
            ]
        }
    
    def close(self):
        """Close connections for both clients."""
        try:
            if hasattr(self.flight_client, 'client') and self.flight_client.client:
                # PyArrow Flight client doesn't need explicit closing
                logger.info("✓ Flight SQL client connection closed")
            
            if hasattr(self.rest_client, 'session') and self.rest_client.session:
                self.rest_client.session.close()
                logger.info("✓ REST API client connection closed")
                
        except Exception as e:
            logger.warning(f"Warning: Error closing connections: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
