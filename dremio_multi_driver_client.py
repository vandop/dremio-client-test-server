"""
Multi-driver Dremio client supporting PyArrow Flight, ADBC, PyODBC, and JDBC.
"""
import logging
import time
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DremioMultiDriverClient:
    """Multi-driver Dremio client supporting various connection methods."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration override."""
        self.config_override = config_override or {}
        self.drivers = {}
        self._init_drivers()
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with override support."""
        return self.config_override.get(key, getattr(Config, key, default))
    
    def _init_drivers(self):
        """Initialize available drivers."""
        self.drivers = {
            'pyarrow_flight': {
                'name': 'PyArrow Flight SQL',
                'available': self._check_pyarrow_flight(),
                'client': None
            },
            'adbc_flight': {
                'name': 'ADBC Flight SQL',
                'available': self._check_adbc_flight(),
                'client': None
            },
            'pyodbc': {
                'name': 'PyODBC',
                'available': self._check_pyodbc(),
                'client': None
            },
            'jdbc': {
                'name': 'JDBC (via JayDeBeApi)',
                'available': self._check_jdbc(),
                'client': None
            }
        }
    
    def _check_pyarrow_flight(self) -> bool:
        """Check if PyArrow Flight is available."""
        try:
            import pyarrow.flight
            return True
        except ImportError:
            return False
    
    def _check_adbc_flight(self) -> bool:
        """Check if ADBC Flight SQL is available."""
        try:
            import adbc_driver_flightsql.dbapi
            return True
        except ImportError:
            return False
    
    def _check_pyodbc(self) -> bool:
        """Check if PyODBC is available."""
        try:
            import pyodbc
            return True
        except ImportError:
            return False
    
    def _check_jdbc(self) -> bool:
        """Check if JDBC (JayDeBeApi) is available."""
        try:
            import jaydebeapi
            import jpype
            import os

            # Check if JDBC driver file exists
            jdbc_driver_path = "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
            if not os.path.exists(jdbc_driver_path):
                logger.info("JDBC driver JAR file not found - run setup script to download")
                return False

            # Simple availability check - let the user decide when to use it
            logger.info("JDBC driver available - dependencies and JAR file found")
            return True

        except ImportError as e:
            logger.info(f"JDBC dependencies not available: {e}")
            return False
    
    def get_available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available drivers."""
        return {k: v for k, v in self.drivers.items() if v['available']}
    
    def _create_pyarrow_flight_client(self):
        """Create PyArrow Flight client."""
        if not self.drivers['pyarrow_flight']['available']:
            raise ImportError("PyArrow Flight not available")
        
        from dremio_pyarrow_client import DremioPyArrowClient
        
        # Create client with config override
        original_config = {}
        if self.config_override:
            for key, value in self.config_override.items():
                if hasattr(Config, key):
                    original_config[key] = getattr(Config, key)
                    setattr(Config, key, value)
        
        try:
            client = DremioPyArrowClient()
            self.drivers['pyarrow_flight']['client'] = client
            return client
        finally:
            # Restore original config
            for key, value in original_config.items():
                setattr(Config, key, value)
    
    def _create_adbc_flight_client(self):
        """Create ADBC Flight SQL client."""
        if not self.drivers['adbc_flight']['available']:
            raise ImportError("ADBC Flight SQL not available")

        import adbc_driver_flightsql.dbapi as flight_sql

        # Get configuration
        base_url = self._get_config_value('DREMIO_CLOUD_URL')
        pat = self._get_config_value('DREMIO_PAT')

        # Convert URL to Flight endpoint
        if 'api.dremio.cloud' in base_url:
            endpoint = 'grpc+tls://data.dremio.cloud:443'
        else:
            endpoint = base_url.replace('https://', 'grpc+tls://').replace('http://', 'grpc+tls://') + ':443'

        # Create connection
        if pat:
            connection = flight_sql.connect(
                endpoint,
                db_kwargs={
                    "adbc.flight.sql.authorization_header": f"Bearer {pat}",
                    "adbc.flight.sql.client_option.tls_skip_verify": "false"
                }
            )
        else:
            username = self._get_config_value('DREMIO_USERNAME')
            password = self._get_config_value('DREMIO_PASSWORD')
            connection = flight_sql.connect(
                endpoint,
                db_kwargs={
                    "adbc.flight.sql.username": username,
                    "adbc.flight.sql.password": password,
                    "adbc.flight.sql.client_option.tls_skip_verify": "false"
                }
            )

        self.drivers['adbc_flight']['client'] = connection
        return connection
    
    def _create_pyodbc_client(self):
        """Create PyODBC client."""
        if not self.drivers['pyodbc']['available']:
            raise ImportError("PyODBC not available")
        
        import pyodbc
        
        # Get configuration
        base_url = self._get_config_value('DREMIO_CLOUD_URL')
        username = self._get_config_value('DREMIO_USERNAME')
        password = self._get_config_value('DREMIO_PASSWORD')
        pat = self._get_config_value('DREMIO_PAT')
        
        # Extract host from URL
        host = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        if 'api.dremio.cloud' in host:
            host = 'data.dremio.cloud'
        
        # Build connection string
        if pat:
            conn_str = f"DRIVER={{Dremio ODBC Driver}};HOST={host};PORT=443;SSL=1;AuthenticationType=Basic Authentication;UID=token;PWD={pat}"
        else:
            conn_str = f"DRIVER={{Dremio ODBC Driver}};HOST={host};PORT=443;SSL=1;AuthenticationType=Basic Authentication;UID={username};PWD={password}"
        
        try:
            connection = pyodbc.connect(conn_str)
            self.drivers['pyodbc']['client'] = connection
            return connection
        except Exception as e:
            logger.warning(f"PyODBC connection failed (driver may not be installed): {e}")
            raise
    
    def _create_jdbc_client(self):
        """Create JDBC client."""
        if not self.drivers['jdbc']['available']:
            raise ImportError("JDBC (JayDeBeApi) not available")
        
        import jaydebeapi
        import jpype
        
        # Get configuration
        base_url = self._get_config_value('DREMIO_CLOUD_URL')
        username = self._get_config_value('DREMIO_USERNAME')
        password = self._get_config_value('DREMIO_PASSWORD')
        pat = self._get_config_value('DREMIO_PAT')
        
        # Get project ID for Dremio Cloud
        project_id = self._get_config_value('DREMIO_PROJECT_ID')

        # Extract host from URL and configure for Dremio Cloud
        host = base_url.replace('https://', '').replace('http://', '').split('/')[0]

        # JDBC URL and credentials for Dremio Cloud
        if 'dremio.cloud' in host:
            # Dremio Cloud uses sql.dremio.cloud for JDBC connections (not data.dremio.cloud)
            jdbc_host = 'sql.dremio.cloud'
            jdbc_url = f"jdbc:dremio:direct={jdbc_host}:443;ssl=true"

            # Add project_id if available (required for Dremio Cloud)
            if project_id:
                jdbc_url += f";PROJECT_ID={project_id}"
        else:
            # On-premise Dremio typically uses port 31010
            jdbc_url = f"jdbc:dremio:direct={host}:31010;ssl=true"

        # Authentication configuration for Dremio Cloud
        if pat:
            # For Dremio Cloud with PAT: use "$token" as username and PAT as password
            auth_user = "$token"
            auth_pass = pat
        else:
            auth_user = username
            auth_pass = password
        
        try:
            # Find JDBC driver JAR file
            import os
            import glob

            # Look for JDBC driver in jdbc-drivers directory
            jar_pattern = os.path.join(os.path.dirname(__file__), 'jdbc-drivers', '*.jar')
            jar_files = glob.glob(jar_pattern)

            if not jar_files:
                raise FileNotFoundError("No JDBC driver JAR files found in jdbc-drivers/ directory")

            # Use the first JAR file found (should be the Dremio driver)
            jar_path = jar_files[0]
            logger.info(f"Using JDBC driver: {jar_path}")

            # Start JVM if not already started with the JAR in classpath
            if not jpype.isJVMStarted():
                jpype.startJVM(classpath=[jar_path])
            else:
                # If JVM is already started, we need to add the JAR to the classpath
                jpype.addClassPath(jar_path)

            # Connect using the Dremio JDBC driver JAR file
            # For Dremio Cloud, use Properties-based authentication as shown in Java examples
            if 'dremio.cloud' in base_url and pat:
                # Use Properties approach for Dremio Cloud with PAT
                connection = jaydebeapi.connect(
                    "com.dremio.jdbc.Driver",
                    jdbc_url,
                    {"user": auth_user, "password": auth_pass},
                    jar_path
                )
            else:
                # Use array approach for on-premise or username/password auth
                connection = jaydebeapi.connect(
                    "com.dremio.jdbc.Driver",
                    jdbc_url,
                    [auth_user, auth_pass],
                    jar_path
                )
            self.drivers['jdbc']['client'] = connection
            return connection
        except Exception as e:
            logger.warning(f"JDBC connection failed (driver may not be available): {e}")
            raise
    
    def execute_query_multi_driver(self, sql: str, drivers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Execute query across multiple drivers."""
        results = {}
        
        for driver_name in drivers:
            if driver_name not in self.drivers:
                results[driver_name] = {
                    'success': False,
                    'error': f'Unknown driver: {driver_name}',
                    'execution_time': 0
                }
                continue
            
            if not self.drivers[driver_name]['available']:
                results[driver_name] = {
                    'success': False,
                    'error': f'Driver not available: {self.drivers[driver_name]["name"]}',
                    'execution_time': 0
                }
                continue
            
            start_time = time.time()
            
            try:
                result = self._execute_query_single_driver(sql, driver_name)
                execution_time = time.time() - start_time
                
                results[driver_name] = {
                    'success': True,
                    'data': result['data'],
                    'row_count': result['row_count'],
                    'columns': result['columns'],
                    'execution_time': execution_time,
                    'driver_name': self.drivers[driver_name]['name']
                }
                
            except Exception as e:
                execution_time = time.time() - start_time
                results[driver_name] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': execution_time,
                    'driver_name': self.drivers[driver_name]['name']
                }
        
        return results

    def _execute_query_single_driver(self, sql: str, driver_name: str) -> Dict[str, Any]:
        """Execute query using a single driver."""
        if driver_name == 'pyarrow_flight':
            return self._execute_pyarrow_flight(sql)
        elif driver_name == 'adbc_flight':
            return self._execute_adbc_flight(sql)
        elif driver_name == 'pyodbc':
            return self._execute_pyodbc(sql)
        elif driver_name == 'jdbc':
            return self._execute_jdbc(sql)
        else:
            raise ValueError(f"Unknown driver: {driver_name}")

    def _execute_pyarrow_flight(self, sql: str) -> Dict[str, Any]:
        """Execute query using PyArrow Flight."""
        if not self.drivers['pyarrow_flight']['client']:
            self._create_pyarrow_flight_client()

        # Add driver comment (PyArrow client will add its own comment)
        client = self.drivers['pyarrow_flight']['client']
        result = client.execute_query(sql)

        if result['success']:
            return {
                'data': result['data'],
                'row_count': result['row_count'],
                'columns': result['columns']
            }
        else:
            raise Exception(result['message'])

    def _execute_adbc_flight(self, sql: str) -> Dict[str, Any]:
        """Execute query using ADBC Flight SQL."""
        if not self.drivers['adbc_flight']['client']:
            self._create_adbc_flight_client()

        # Add driver type and version as SQL comment
        try:
            import adbc_driver_flightsql
            adbc_version = adbc_driver_flightsql.__version__
        except:
            adbc_version = "unknown"

        driver_comment = f"/* Driver: ADBC Flight SQL v{adbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers['adbc_flight']['client']
        cursor = connection.cursor()
        cursor.execute(commented_sql)

        # Execute query and fetch results
        import pandas as pd
        arrow_table = cursor.fetch_arrow_table()
        df = arrow_table.to_pandas()

        # Replace NaN values with None for JSON compatibility
        import numpy as np
        if not df.empty:
            df = df.replace({np.nan: None})
            data = df.to_dict('records')
            columns = list(df.columns)
        else:
            data = []
            columns = []

        return {
            'data': data,
            'row_count': len(data),
            'columns': columns
        }

    def _infer_columns_from_sql(self, sql: str) -> List[str]:
        """Infer column names from SQL query as fallback."""
        import re

        # Simple regex to extract column aliases and expressions
        # This is a basic fallback - not perfect but better than nothing

        # Remove comments
        sql_clean = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # Extract SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_clean, re.IGNORECASE | re.DOTALL)
        if not select_match:
            # No FROM clause, might be a simple SELECT
            select_match = re.search(r'SELECT\s+(.*)', sql_clean, re.IGNORECASE | re.DOTALL)

        if select_match:
            select_clause = select_match.group(1).strip()

            # Split by comma (basic - doesn't handle nested functions perfectly)
            columns = []
            parts = select_clause.split(',')

            for part in parts:
                part = part.strip()

                # Look for alias with quotes
                alias_match = re.search(r'"([^"]+)"$', part)
                if alias_match:
                    columns.append(alias_match.group(1))
                    continue

                # Look for alias with AS
                as_match = re.search(r'\s+AS\s+([^\s]+)$', part, re.IGNORECASE)
                if as_match:
                    alias = as_match.group(1).strip('"\'')
                    columns.append(alias)
                    continue

                # Look for simple alias (space separated)
                space_match = re.search(r'\s+([^\s]+)$', part)
                if space_match:
                    alias = space_match.group(1).strip('"\'')
                    columns.append(alias)
                    continue

                # No alias found, use the expression itself (simplified)
                expr = re.sub(r'^\s*\w+\s*\(.*\)\s*$', 'EXPR$0', part)  # Function calls
                expr = re.sub(r'^\s*\d+\s*$', 'EXPR$0', expr)  # Literals
                columns.append(expr.strip())

            return columns

        # Fallback
        return ['EXPR$0']

    def _execute_pyodbc(self, sql: str) -> Dict[str, Any]:
        """Execute query using PyODBC."""
        if not self.drivers['pyodbc']['client']:
            self._create_pyodbc_client()

        # Add driver type and version as SQL comment
        try:
            import pyodbc
            pyodbc_version = pyodbc.version
        except:
            pyodbc_version = "unknown"

        driver_comment = f"/* Driver: PyODBC v{pyodbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers['pyodbc']['client']
        cursor = connection.cursor()
        cursor.execute(commented_sql)

        # Fetch column names
        columns = [column[0] for column in cursor.description]

        # Fetch all rows
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]

        return {
            'data': data,
            'row_count': len(data),
            'columns': columns
        }

    def _execute_jdbc(self, sql: str) -> Dict[str, Any]:
        """Execute query using JDBC."""
        if not self.drivers['jdbc']['client']:
            self._create_jdbc_client()

        # Add driver type and version as SQL comment
        try:
            import jaydebeapi
            jdbc_version = jaydebeapi.__version__
        except:
            jdbc_version = "unknown"

        driver_comment = f"/* Driver: JDBC (JayDeBeApi) v{jdbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers['jdbc']['client']
        cursor = connection.cursor()
        cursor.execute(commented_sql)

        # Fetch column names and convert Java strings to Python strings
        columns = [str(desc[0]) for desc in cursor.description]

        # Fetch all rows
        rows = cursor.fetchall()

        # Convert Java objects to JSON-serializable Python objects
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                # Ensure column name is a Python string
                column_name = str(columns[i])

                # Convert Java objects to Python equivalents
                if value is None:
                    row_dict[column_name] = None
                elif hasattr(value, '__class__') and 'java' in str(value.__class__):
                    # Handle Java objects by converting to string
                    row_dict[column_name] = str(value)
                else:
                    # Handle Python objects directly
                    row_dict[column_name] = value
            data.append(row_dict)

        return {
            'data': data,
            'row_count': len(data),
            'columns': columns
        }

    def get_projects(self) -> Dict[str, Any]:
        """Get projects using the most reliable method."""
        # Try PyArrow Flight first, then fall back to REST API
        try:
            if self.drivers['pyarrow_flight']['available']:
                # Use REST API for projects as Flight SQL doesn't expose this
                from dremio_client import DremioClient

                # Create client with config override
                original_config = {}
                if self.config_override:
                    for key, value in self.config_override.items():
                        if hasattr(Config, key):
                            original_config[key] = getattr(Config, key)
                            setattr(Config, key, value)

                try:
                    client = DremioClient()
                    return client.get_projects()
                finally:
                    # Restore original config
                    for key, value in original_config.items():
                        setattr(Config, key, value)
            else:
                raise Exception("No suitable driver available for project listing")

        except Exception as e:
            return {
                'success': False,
                'projects': [],
                'error': str(e),
                'message': f'Failed to retrieve projects: {str(e)}'
            }

    def test_connection(self, drivers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Test connection across multiple drivers."""
        results = {}

        for driver_name in drivers:
            if driver_name not in self.drivers:
                results[driver_name] = {
                    'success': False,
                    'error': f'Unknown driver: {driver_name}',
                    'driver_name': driver_name
                }
                continue

            if not self.drivers[driver_name]['available']:
                results[driver_name] = {
                    'success': False,
                    'error': f'Driver not available: {self.drivers[driver_name]["name"]}',
                    'driver_name': self.drivers[driver_name]['name']
                }
                continue

            try:
                # Test with a simple query
                test_result = self._execute_query_single_driver("SELECT 1 as test", driver_name)
                results[driver_name] = {
                    'success': True,
                    'message': f'Connection successful via {self.drivers[driver_name]["name"]}',
                    'driver_name': self.drivers[driver_name]['name'],
                    'test_result': test_result
                }

            except Exception as e:
                results[driver_name] = {
                    'success': False,
                    'error': str(e),
                    'driver_name': self.drivers[driver_name]['name']
                }

        return results

    def close_connections(self):
        """Close all active connections."""
        for driver_name, driver_info in self.drivers.items():
            if driver_info['client']:
                try:
                    if driver_name == 'pyarrow_flight':
                        # PyArrow Flight doesn't need explicit closing
                        pass
                    elif driver_name in ['adbc_flight', 'pyodbc', 'jdbc']:
                        driver_info['client'].close()
                    driver_info['client'] = None
                except Exception as e:
                    logger.warning(f"Error closing {driver_name} connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connections()
