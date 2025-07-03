"""
Dremio client using native PyArrow Flight (without ADBC) for better compatibility.
"""
import logging
import pyarrow as pa
import pyarrow.flight as flight
from typing import Dict, List, Optional, Any
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DremioPyArrowClient:
    """Dremio client using native PyArrow Flight for direct SQL queries."""
    
    def __init__(self):
        """Initialize the Dremio PyArrow Flight client."""
        self.base_url = Config.DREMIO_CLOUD_URL
        self.username = Config.DREMIO_USERNAME
        self.password = Config.DREMIO_PASSWORD
        self.project_id = Config.DREMIO_PROJECT_ID
        self.pat = Config.DREMIO_PAT
        
        # Flight connection details
        self.flight_endpoint = self._get_flight_endpoint()
        self.client = None
        
        logger.info(f"✓ Dremio PyArrow Flight client initialized")
        logger.info(f"Flight endpoint: {self.flight_endpoint}")
    
    def _get_flight_endpoint(self) -> str:
        """Get the correct Flight endpoint for Dremio Cloud."""
        if not self.base_url:
            return "grpc+tls://data.dremio.cloud:443"
        
        # Convert common URLs to Flight endpoints
        url_mappings = {
            'https://api.dremio.cloud': 'data.dremio.cloud:443',
            'https://api.eu.dremio.cloud': 'data.eu.dremio.cloud:443',
            'https://app.dremio.cloud': 'data.dremio.cloud:443',
            'https://app.eu.dremio.cloud': 'data.eu.dremio.cloud:443',
        }
        
        base_clean = self.base_url.rstrip('/')
        if base_clean in url_mappings:
            endpoint = url_mappings[base_clean]
            logger.info(f"🔧 URL mapped to Flight endpoint: {base_clean} → {endpoint}")
            return endpoint
        
        # For custom domains, try to extract the host
        if 'dremio.cloud' in self.base_url:
            if 'api.' in self.base_url:
                endpoint = self.base_url.replace('https://api.', 'data.').replace('http://api.', 'data.') + ':443'
            else:
                endpoint = self.base_url.replace('https://', 'data.').replace('http://', 'data.') + ':443'
            logger.info(f"🔧 Custom URL mapped to Flight endpoint: {self.base_url} → {endpoint}")
            return endpoint
        
        # Default fallback
        return "data.dremio.cloud:443"
    
    def connect(self) -> Dict[str, Any]:
        """
        Connect to Dremio using PyArrow Flight.
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            logger.info(f"Connecting to Dremio Flight endpoint: {self.flight_endpoint}")
            
            # Create Flight client
            self.client = flight.FlightClient(f"grpc+tls://{self.flight_endpoint}")
            
            # Prepare authentication
            if self.pat:
                logger.info("Using Personal Access Token authentication")
                # Create bearer token for authentication
                bearer_token = flight.FlightCallOptions(headers=[
                    (b"authorization", f"Bearer {self.pat}".encode('utf-8'))
                ])
                self.call_options = bearer_token
            else:
                logger.info("Using username/password authentication")
                # Create basic auth
                basic_auth = flight.FlightCallOptions(headers=[
                    (b"authorization", f"Basic {self.username}:{self.password}".encode('utf-8'))
                ])
                self.call_options = basic_auth
            
            # Connection established successfully
            logger.info("✓ Flight client created successfully")
            return {
                'success': True,
                'message': 'Successfully connected to Dremio using PyArrow Flight',
                'endpoint': self.flight_endpoint,
                'auth_method': 'pat' if self.pat else 'credentials'
            }
                
        except Exception as e:
            logger.error(f"Flight connection failed: {e}")
            return {
                'success': False,
                'error_type': 'connection_failed',
                'message': f'Failed to connect to Dremio Flight: {str(e)}',
                'suggestions': [
                    'Check your network connection',
                    'Verify the Flight endpoint is accessible',
                    'Ensure firewall allows gRPC traffic on port 443'
                ]
            }
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SQL query using PyArrow Flight.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Dictionary with query results
        """
        if not self.client:
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
            logger.info(f"Executing SQL query: {sql}")
            
            # Create a FlightDescriptor for the SQL query
            flight_desc = flight.FlightDescriptor.for_command(sql.encode('utf-8'))
            
            # Get flight info
            flight_info = self.client.get_flight_info(flight_desc, options=self.call_options)
            
            # Get the data from the first endpoint
            if flight_info.endpoints:
                endpoint = flight_info.endpoints[0]
                flight_reader = self.client.do_get(endpoint.ticket, options=self.call_options)
                
                # Read all batches and convert to table
                table = flight_reader.read_all()
                
                # Convert to pandas DataFrame for easier handling
                df = table.to_pandas()
                
                # Convert to list of dictionaries
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
            else:
                return {
                    'success': False,
                    'data': [],
                    'error_type': 'no_endpoints',
                    'message': 'No flight endpoints available for query'
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
                    'Ensure you have permissions to access the data'
                ]
            }
    
    def get_jobs(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get jobs by querying the SYS.Jobs table.
        
        Args:
            limit: Maximum number of jobs to retrieve
            
        Returns:
            Dictionary with jobs data
        """
        sql = f"""
        SELECT 
            job_id,
            job_state,
            query_type,
            user_name,
            submitted_ts,
            attempt_started_ts,
            final_state_ts,
            query_text
        FROM SYS.Jobs
        ORDER BY submitted_ts DESC
        LIMIT {limit}
        """
        
        logger.info(f"Querying SYS.Jobs table with limit {limit}")
        result = self.execute_query(sql)
        
        if result['success']:
            # Process job data to match expected format
            jobs = []
            for job in result['data']:
                processed_job = {
                    'id': job.get('job_id'),
                    'jobState': job.get('job_state'),
                    'queryType': job.get('query_type'),
                    'user': job.get('user_name'),
                    'submittedTime': job.get('submitted_ts'),
                    'startTime': job.get('attempt_started_ts'),
                    'endTime': job.get('final_state_ts'),
                    'queryText': job.get('query_text')
                }
                jobs.append(processed_job)
            
            return {
                'success': True,
                'jobs': jobs,
                'count': len(jobs),
                'message': f'Successfully retrieved {len(jobs)} jobs from SYS.Jobs',
                'query_method': 'pyarrow_flight'
            }
        else:
            return result
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection with comprehensive diagnostics."""
        logger.info("=== Starting Dremio PyArrow Flight Connection Test ===")
        
        # Test connection
        connect_result = self.connect()
        if not connect_result['success']:
            return {
                'status': 'error',
                'step': 'connection',
                'message': connect_result['message'],
                'details': connect_result
            }
        
        # Test simple query
        test_result = self.execute_query("SELECT 1 as test")
        if not test_result['success']:
            return {
                'status': 'error', 
                'step': 'query_test',
                'message': test_result['message'],
                'details': test_result
            }
        
        # Test SYS.Jobs access
        jobs_result = self.get_jobs(limit=1)
        
        logger.info("=== PyArrow Flight Connection Test Completed ===")
        
        return {
            'status': 'success',
            'message': 'Successfully connected to Dremio using PyArrow Flight',
            'details': {
                'connection': connect_result,
                'query_test': test_result['success'],
                'jobs_access': jobs_result['success'],
                'jobs_count': jobs_result.get('count', 0),
                'flight_endpoint': self.flight_endpoint
            },
            'steps_completed': ['connection', 'query_test', 'jobs_test']
        }
