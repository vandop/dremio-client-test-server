"""
Enhanced Dremio client using PyArrow Flight SQL for direct SQL queries.
"""
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.flight as flight
import adbc_driver_flightsql.dbapi as flight_sql
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DremioFlightClient:
    """Enhanced Dremio client using PyArrow Flight SQL for direct queries."""
    
    def __init__(self):
        """Initialize the Dremio Flight SQL client."""
        self.base_url = self._normalize_base_url(Config.DREMIO_CLOUD_URL)
        self.username = Config.DREMIO_USERNAME
        self.password = Config.DREMIO_PASSWORD
        self.project_id = Config.DREMIO_PROJECT_ID
        self.pat = Config.DREMIO_PAT
        
        # Flight SQL connection details
        self.flight_endpoint = self._get_flight_endpoint()
        self.connection = None
        
        logger.info(f"✓ Dremio Flight SQL client initialized")
        logger.info(f"Flight endpoint: {self.flight_endpoint}")
    
    def _normalize_base_url(self, url: str) -> str:
        """Normalize the base URL for Dremio Cloud."""
        if not url:
            return url
            
        url = url.rstrip('/')
        
        # Convert REST API URLs to Flight endpoints
        url_corrections = {
            'https://api.dremio.cloud': 'grpc+tls://data.dremio.cloud:443',
            'https://api.eu.dremio.cloud': 'grpc+tls://data.eu.dremio.cloud:443',
            'https://app.dremio.cloud': 'grpc+tls://data.dremio.cloud:443',
            'https://app.eu.dremio.cloud': 'grpc+tls://data.eu.dremio.cloud:443',
        }
        
        if url in url_corrections:
            corrected_url = url_corrections[url]
            logger.info(f"🔧 URL auto-corrected for Flight SQL: {url} → {corrected_url}")
            return corrected_url
        
        # For custom domains, convert api.* to data.*
        if 'api.' in url:
            corrected_url = url.replace('api.', 'data.').replace('https://', 'grpc+tls://') + ':443'
            logger.info(f"🔧 URL auto-corrected for Flight: {url} → {corrected_url}")
            return corrected_url
            
        return url
    
    def _get_flight_endpoint(self) -> str:
        """Get the Flight endpoint from the base URL."""
        # The base URL should already be in the correct format after normalization
        return self.base_url
    
    def connect(self) -> Dict[str, Any]:
        """
        Establish connection to Dremio using Flight SQL.

        Returns:
            Dictionary with connection status and details
        """
        try:
            logger.info("Connecting to Dremio using Flight SQL...")

            # Prepare connection parameters for ADBC Flight SQL
            if self.pat:
                # Use Personal Access Token
                logger.info("Using Personal Access Token authentication")
                # For ADBC Flight SQL, we need to use the authorization header
                self.connection = flight_sql.connect(
                    self.flight_endpoint,
                    db_kwargs={
                        "adbc.flight.sql.authorization_header": f"Bearer {self.pat}",
                        "adbc.flight.sql.client_option.tls_skip_verify": "false"
                    }
                )
            else:
                # Use username/password
                logger.info("Using username/password authentication")
                self.connection = flight_sql.connect(
                    self.flight_endpoint,
                    db_kwargs={
                        "adbc.flight.sql.username": self.username,
                        "adbc.flight.sql.password": self.password,
                        "adbc.flight.sql.client_option.tls_skip_verify": "false"
                    }
                )
            
            # Test the connection with a simple query
            test_result = self.execute_query("SELECT 1 as test_connection")
            
            if test_result['success'] and len(test_result['data']) > 0:
                logger.info("✓ Flight SQL connection successful")
                return {
                    'success': True,
                    'message': 'Successfully connected to Dremio using Flight SQL',
                    'endpoint': self.flight_endpoint,
                    'auth_method': 'pat' if self.pat else 'credentials'
                }
            else:
                return {
                    'success': False,
                    'error_type': 'connection_test_failed',
                    'message': 'Connection established but test query failed',
                    'details': test_result
                }
                
        except Exception as e:
            logger.error(f"Flight SQL connection failed: {e}")
            return {
                'success': False,
                'error_type': 'connection_failed',
                'message': f'Failed to connect to Dremio Flight SQL: {str(e)}',
                'suggestions': [
                    'Check your DREMIO_CLOUD_URL is correct',
                    'Verify your PAT or credentials are valid',
                    'Ensure Flight SQL endpoint is accessible',
                    'Check network connectivity and firewall settings'
                ]
            }
    
    def execute_query(self, sql: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a SQL query using Flight SQL.
        
        Args:
            sql: SQL query to execute
            limit: Optional limit for results
            
        Returns:
            Dictionary with query results and metadata
        """
        if not self.connection:
            connect_result = self.connect()
            if not connect_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'error_type': 'no_connection',
                    'message': 'No active connection to Dremio',
                    'connection_details': connect_result
                }
        
        try:
            # Add LIMIT clause if specified
            if limit and 'LIMIT' not in sql.upper():
                sql = f"{sql} LIMIT {limit}"
            
            logger.info(f"Executing SQL query: {sql}")

            # Execute query and fetch results
            cursor = self.connection.cursor()
            cursor.execute(sql)

            # Fetch results as PyArrow table
            arrow_table = cursor.fetch_arrow_table()

            # Convert to pandas DataFrame for easier handling
            df = arrow_table.to_pandas()

            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')

            logger.info(f"✓ Query executed successfully, returned {len(data)} rows")
            
            return {
                'success': True,
                'data': data,
                'row_count': len(data),
                'columns': list(df.columns),
                'query': sql,
                'message': f'Query executed successfully, returned {len(data)} rows'
            }
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                'success': False,
                'data': [],
                'error_type': 'query_failed',
                'message': f'Query execution failed: {str(e)}',
                'query': sql,
                'suggestions': [
                    'Check SQL syntax',
                    'Verify table/column names exist',
                    'Ensure you have permissions to access the data',
                    'Check if the query is valid for your Dremio version'
                ]
            }
    
    def get_jobs(self, limit: int = 100, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get jobs by querying the SYS.Jobs table.
        
        Args:
            limit: Maximum number of jobs to retrieve
            status_filter: Optional status filter (e.g., 'COMPLETED', 'FAILED', 'RUNNING')
            
        Returns:
            Dictionary with jobs data and metadata
        """
        try:
            # Build the SQL query for SYS.Jobs
            sql = """
            SELECT 
                job_id,
                job_state,
                query_type,
                user_name,
                submitted_ts,
                attempt_started_ts,
                metadata_retrieval_ts,
                planning_start_ts,
                query_planning_ts,
                engine_start_ts,
                execution_planning_ts,
                execution_start_ts,
                final_state_ts,
                query_text,
                failure_info,
                cancelled_reason,
                engine_name,
                queue_name,
                engine_id,
                dataset_graph,
                planner_estimated_cost,
                rows_scanned,
                bytes_scanned,
                rows_returned,
                bytes_returned
            FROM SYS.Jobs
            """
            
            # Add status filter if specified
            if status_filter:
                sql += f" WHERE job_state = '{status_filter}'"
            
            # Add ordering and limit
            sql += " ORDER BY submitted_ts DESC"
            
            logger.info(f"Querying SYS.Jobs table with limit {limit}")
            
            result = self.execute_query(sql, limit=limit)
            
            if result['success']:
                # Process the job data
                jobs = result['data']
                
                # Convert timestamps to readable format and add metadata
                processed_jobs = []
                for job in jobs:
                    processed_job = {
                        'id': job.get('job_id'),
                        'jobState': job.get('job_state'),
                        'queryType': job.get('query_type'),
                        'user': job.get('user_name'),
                        'submittedTime': job.get('submitted_ts'),
                        'startTime': job.get('attempt_started_ts'),
                        'endTime': job.get('final_state_ts'),
                        'queryText': job.get('query_text'),
                        'failureInfo': job.get('failure_info'),
                        'engineName': job.get('engine_name'),
                        'queueName': job.get('queue_name'),
                        'rowsScanned': job.get('rows_scanned'),
                        'bytesScanned': job.get('bytes_scanned'),
                        'rowsReturned': job.get('rows_returned'),
                        'bytesReturned': job.get('bytes_returned'),
                        'plannerEstimatedCost': job.get('planner_estimated_cost')
                    }
                    processed_jobs.append(processed_job)
                
                return {
                    'success': True,
                    'jobs': processed_jobs,
                    'count': len(processed_jobs),
                    'message': f'Successfully retrieved {len(processed_jobs)} jobs from SYS.Jobs table',
                    'query_method': 'flight_sql',
                    'table_queried': 'SYS.Jobs'
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to get jobs from SYS.Jobs: {e}")
            return {
                'success': False,
                'jobs': [],
                'error_type': 'sys_jobs_query_failed',
                'message': f'Failed to query SYS.Jobs table: {str(e)}',
                'suggestions': [
                    'Verify you have permissions to access SYS.Jobs table',
                    'Check if your Dremio version supports SYS.Jobs',
                    'Ensure Flight SQL connection is working',
                    'Contact your Dremio administrator for access'
                ]
            }

    def get_projects(self) -> Dict[str, Any]:
        """
        Get projects by querying system tables or information schema.

        Returns:
            Dictionary with projects data
        """
        try:
            # Try different approaches to get project information
            queries_to_try = [
                # Try INFORMATION_SCHEMA first
                "SELECT * FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME NOT LIKE 'sys%'",
                # Try SYS tables
                "SELECT * FROM SYS.CATALOGS",
                # Try simple schema listing
                "SHOW SCHEMAS"
            ]

            for i, sql in enumerate(queries_to_try):
                logger.info(f"Trying project query {i+1}: {sql}")
                result = self.execute_query(sql, limit=50)

                if result['success'] and result['data']:
                    logger.info(f"✓ Successfully retrieved project data using query {i+1}")

                    # Process the results based on the query type
                    projects = []
                    for row in result['data']:
                        if 'SCHEMA_NAME' in row:
                            # INFORMATION_SCHEMA result
                            project = {
                                'id': row.get('SCHEMA_NAME'),
                                'name': row.get('SCHEMA_NAME'),
                                'description': f"Schema: {row.get('SCHEMA_NAME')}",
                                'type': 'schema'
                            }
                        elif 'CATALOG_NAME' in row:
                            # SYS.CATALOGS result
                            project = {
                                'id': row.get('CATALOG_NAME'),
                                'name': row.get('CATALOG_NAME'),
                                'description': f"Catalog: {row.get('CATALOG_NAME')}",
                                'type': 'catalog'
                            }
                        else:
                            # Generic result
                            first_col = list(row.keys())[0] if row else 'unknown'
                            project = {
                                'id': str(row.get(first_col, 'unknown')),
                                'name': str(row.get(first_col, 'unknown')),
                                'description': f"Project: {row.get(first_col, 'unknown')}",
                                'type': 'project'
                            }

                        projects.append(project)

                    return {
                        'success': True,
                        'projects': projects,
                        'total_count': len(projects),
                        'message': f'Found {len(projects)} projects/schemas',
                        'query_method': 'flight_sql',
                        'query_used': sql
                    }

            # If all queries failed
            return {
                'success': False,
                'projects': [],
                'error_type': 'no_project_data',
                'message': 'Unable to retrieve project information from any system table',
                'suggestions': [
                    'Check if you have permissions to access system tables',
                    'Verify your Dremio version supports these queries',
                    'Contact your Dremio administrator for access'
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return {
                'success': False,
                'projects': [],
                'error_type': 'projects_query_failed',
                'message': f'Failed to query project information: {str(e)}',
                'suggestions': [
                    'Check your Flight SQL connection',
                    'Verify permissions to access system tables',
                    'Ensure your Dremio instance is accessible'
                ]
            }

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job.

        Args:
            job_id: The ID of the job to retrieve

        Returns:
            Dictionary with job details
        """
        try:
            sql = f"""
            SELECT *
            FROM SYS.Jobs
            WHERE job_id = '{job_id}'
            """

            logger.info(f"Getting details for job: {job_id}")
            result = self.execute_query(sql)

            if result['success'] and result['data']:
                job_data = result['data'][0]  # Should be only one job
                return {
                    'success': True,
                    'job': job_data,
                    'message': f'Successfully retrieved details for job {job_id}',
                    'query_method': 'flight_sql'
                }
            else:
                return {
                    'success': False,
                    'job': None,
                    'error_type': 'job_not_found',
                    'message': f'Job {job_id} not found in SYS.Jobs table'
                }

        except Exception as e:
            logger.error(f"Failed to get job details for {job_id}: {e}")
            return {
                'success': False,
                'job': None,
                'error_type': 'job_details_query_failed',
                'message': f'Failed to query job details: {str(e)}'
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Flight SQL connection with comprehensive diagnostics.

        Returns:
            Dictionary with connection test results
        """
        logger.info("=== Starting Dremio Flight SQL Connection Test ===")

        # Step 1: Validate configuration
        try:
            Config.validate_dremio_config()
            logger.info("✓ Configuration validation passed")
        except ValueError as e:
            logger.error(f"✗ Configuration validation failed: {e}")
            return {
                'status': 'error',
                'step': 'configuration',
                'message': str(e),
                'suggestions': [
                    'Check your .env file configuration',
                    'Ensure all required variables are set',
                    'Verify your Dremio Cloud credentials'
                ]
            }

        # Step 2: Test Flight SQL connection
        logger.info("Testing Flight SQL connection...")
        connect_result = self.connect()

        if not connect_result['success']:
            logger.error(f"✗ Flight SQL connection failed: {connect_result['message']}")
            return {
                'status': 'error',
                'step': 'flight_sql_connection',
                'message': f"Flight SQL connection failed: {connect_result['message']}",
                'details': connect_result,
                'suggestions': connect_result.get('suggestions', [])
            }

        logger.info("✓ Flight SQL connection successful")

        # Step 3: Test SYS.Jobs access
        logger.info("Testing SYS.Jobs table access...")
        jobs_result = self.get_jobs(limit=1)

        if not jobs_result['success']:
            logger.warning(f"⚠ SYS.Jobs access failed: {jobs_result['message']}")
            # Don't fail the entire test, just warn
        else:
            logger.info(f"✓ SYS.Jobs access successful - found {jobs_result['count']} jobs")

        # Step 4: Test projects access
        logger.info("Testing project/schema access...")
        projects_result = self.get_projects()

        logger.info("=== Flight SQL Connection Test Completed Successfully ===")

        return {
            'status': 'success',
            'message': 'Successfully connected to Dremio using Flight SQL',
            'details': {
                'connection': connect_result,
                'jobs_access': jobs_result['success'],
                'jobs_count': jobs_result.get('count', 0),
                'projects_access': projects_result['success'],
                'projects_count': projects_result.get('total_count', 0),
                'flight_endpoint': self.flight_endpoint,
                'auth_method': connect_result.get('auth_method')
            },
            'steps_completed': ['configuration', 'flight_sql_connection', 'sys_jobs_test', 'projects_test']
        }

    def close(self):
        """Close the Flight SQL connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("✓ Flight SQL connection closed")
            except Exception as e:
                logger.warning(f"Warning: Error closing connection: {e}")
            finally:
                self.connection = None
