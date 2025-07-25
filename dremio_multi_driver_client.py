"""
Multi-driver Dremio client supporting PyArrow Flight, ADBC, PyODBC, and JDBC.
"""

import logging
import os
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
            "pyarrow_flight": {
                "name": "PyArrow Flight SQL",
                "available": self._check_pyarrow_flight(),
                "client": None,
            },
            "adbc_flight": {
                "name": "ADBC Flight SQL",
                "available": self._check_adbc_flight(),
                "client": None,
            },
            "pyodbc": {
                "name": "PyODBC",
                "available": self._check_pyodbc(),
                "client": None,
            },
            "jdbc": {
                "name": "JDBC (via JayDeBeApi)",
                "available": self._check_jdbc(),
                "client": None,
            },
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
            import glob

            # Check for any JDBC driver files
            jar_pattern = os.path.join("jdbc-drivers", "*.jar")
            jar_files = glob.glob(jar_pattern)

            if not jar_files:
                logger.info(
                    "No JDBC driver JAR files found - run setup script to download"
                )
                return False

            # Prioritize Apache Arrow Flight SQL JDBC driver
            flight_sql_driver = None
            dremio_driver = None

            for jar_file in jar_files:
                if "flight-sql-jdbc-driver" in jar_file:
                    flight_sql_driver = jar_file
                elif "dremio-jdbc-driver" in jar_file:
                    dremio_driver = jar_file

            if flight_sql_driver:
                logger.info(
                    f"Apache Arrow Flight SQL JDBC driver found: {flight_sql_driver}"
                )
            elif dremio_driver:
                logger.info(f"Legacy Dremio JDBC driver found: {dremio_driver}")
            else:
                logger.info(f"JDBC driver found: {jar_files[0]}")

            logger.info("JDBC driver available - dependencies and JAR file found")
            return True

        except ImportError as e:
            logger.info(f"JDBC dependencies not available: {e}")
            return False

    def get_available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available drivers, considering SSL workarounds."""
        import os

        available = {}

        for k, v in self.drivers.items():
            if v["available"]:
                # Check for JDBC SSL workaround
                if k == "jdbc" and os.path.exists(".jdbc_ssl_config"):
                    # Mark JDBC as unavailable due to SSL issues
                    available[k] = {
                        **v,
                        "available": False,
                        "status": "disabled_ssl_workaround",
                        "message": "JDBC disabled due to SSL negotiation issues",
                    }
                else:
                    available[k] = v

        return available

    def _create_pyarrow_flight_client(self):
        """Create PyArrow Flight client."""
        if not self.drivers["pyarrow_flight"]["available"]:
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
            self.drivers["pyarrow_flight"]["client"] = client
            return client
        finally:
            # Restore original config
            for key, value in original_config.items():
                setattr(Config, key, value)

    def _create_adbc_flight_client(self):
        """Create ADBC Flight SQL client."""
        if not self.drivers["adbc_flight"]["available"]:
            raise ImportError("ADBC Flight SQL not available")

        import adbc_driver_flightsql.dbapi as flight_sql

        # Get configuration
        base_url = self._get_config_value("DREMIO_CLOUD_URL")
        pat = self._get_config_value("DREMIO_PAT")

        # Convert URL to Flight endpoint
        if "api.dremio.cloud" in base_url:
            endpoint = "grpc+tls://data.dremio.cloud:443"
        else:
            endpoint = (
                base_url.replace("https://", "grpc+tls://").replace(
                    "http://", "grpc+tls://"
                )
                + ":443"
            )

        # Create connection
        if pat:
            connection = flight_sql.connect(
                endpoint,
                db_kwargs={
                    "adbc.flight.sql.authorization_header": f"Bearer {pat}",
                    "adbc.flight.sql.client_option.tls_skip_verify": "false",
                },
            )
        else:
            username = self._get_config_value("DREMIO_USERNAME")
            password = self._get_config_value("DREMIO_PASSWORD")
            connection = flight_sql.connect(
                endpoint,
                db_kwargs={
                    "adbc.flight.sql.username": username,
                    "adbc.flight.sql.password": password,
                    "adbc.flight.sql.client_option.tls_skip_verify": "false",
                },
            )

        self.drivers["adbc_flight"]["client"] = connection
        return connection

    def _create_pyodbc_client(self):
        """Create PyODBC client."""
        if not self.drivers["pyodbc"]["available"]:
            raise ImportError("PyODBC not available")

        import pyodbc

        # Get configuration
        base_url = self._get_config_value("DREMIO_CLOUD_URL")
        username = self._get_config_value("DREMIO_USERNAME")
        password = self._get_config_value("DREMIO_PASSWORD")
        pat = self._get_config_value("DREMIO_PAT")

        # Extract host from URL

        host = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        if 'api.dremio.cloud' in host:
            host = 'data.dremio.cloud'
        
        # Build connection string - try different driver paths and names
        # First, try to find the actual driver library path
        import subprocess

        driver_configs = []

        # Method 1: Try to find driver library paths
        try:
            import glob

            # Look for Arrow Flight SQL ODBC driver library with version numbers
            search_patterns = [
                "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so*",  # Primary location with version
                "/opt/arrow-flight-sql-odbc-driver/lib/libarrow-odbc.so*",   # Alternative lib directory
                "/usr/lib/x86_64-linux-gnu/libarrow-odbc.so*",               # System lib directory
                "/usr/local/lib/libarrow-odbc.so*"                           # Local lib directory
            ]

            logger.info(f"Searching for ODBC driver libraries in {len(search_patterns)} locations...")

            for pattern in search_patterns:
                logger.debug(f"Checking pattern: {pattern}")
                matching_files = glob.glob(pattern)
                if matching_files:
                    # Use the first matching file (usually the one with version number)
                    driver_path = matching_files[0]
                    driver_configs.append({
                        "type": "path",
                        "value": driver_path,
                        "description": f"Direct library path: {driver_path}"
                    })
                    logger.info(f"✅ Found ODBC driver library: {driver_path}")
                    logger.info(f"   All matches for pattern: {matching_files}")
                    break
                else:
                    logger.debug(f"   No matches for pattern: {pattern}")

            if not driver_configs:
                logger.warning("No ODBC driver library files found in standard locations")

        except Exception as e:
            logger.warning(f"Could not check driver library paths: {e}")

        # Method 2: Try driver names (fallback)
        driver_names = [
            "Arrow Flight SQL ODBC Driver",         # Most common name
            "Dremio Arrow Flight SQL ODBC Driver",  # Alternative name
            "Dremio ODBC Driver"                    # Legacy driver name
        ]

        for driver_name in driver_names:
            driver_configs.append({
                "type": "name",
                "value": driver_name,
                "description": f"Driver name: {driver_name}"
            })

        # Log all driver configurations that will be tried
        logger.info(f"Will try {len(driver_configs)} driver configurations:")
        for i, config in enumerate(driver_configs, 1):
            logger.info(f"  {i}. {config['description']}")

        # Try each driver configuration until one works
        connection = None
        last_error = None

        for config in driver_configs:
            try:
                driver_identifier = config["value"]
                config_type = config["type"]
                description = config["description"]

                logger.info(f"Trying PyODBC connection with: {description}")

                if pat:
                    # For Arrow Flight SQL ODBC driver with PAT: use TOKEN parameter
                    # According to official Dremio docs: "For TOKEN, specify a personal access token"
                    conn_str = f"DRIVER={driver_identifier};HOST={host};PORT=443;useEncryption=true;TOKEN={pat}"
                else:
                    conn_str = f"DRIVER={driver_identifier};HOST={host};PORT=443;UseEncryption=true;disableCertificateVerification=true;UID={username};PWD={password}"

                # Connect with autocommit disabled to avoid SQLSetConnectAttr issues
                logger.info(f"Trying connection string: {conn_str}")
                connection = pyodbc.connect(conn_str, autocommit=True)
                logger.info(f"PyODBC connected successfully using: {description}")
                break

            except Exception as e:
                last_error = e
                if 'file not found' in str(e):
                    continue  # Try next driver name
                else:
                    # If it's not a "driver not found" error, break and report it
                    break

        if connection is None:
            if last_error:
                raise last_error
            else:
                raise Exception("No compatible ODBC driver found")

        self.drivers['pyodbc']['client'] = connection
        return connection

    def _create_jdbc_client(self):
        """Create JDBC client."""
        if not self.drivers["jdbc"]["available"]:
            raise ImportError("JDBC (JayDeBeApi) not available")

        import jaydebeapi
        import jpype

        # Get configuration
        base_url = self._get_config_value("DREMIO_CLOUD_URL")
        username = self._get_config_value("DREMIO_USERNAME")
        password = self._get_config_value("DREMIO_PASSWORD")
        pat = self._get_config_value("DREMIO_PAT")

        # Get project ID for Dremio Cloud
        project_id = self._get_config_value("DREMIO_PROJECT_ID")

        # Extract host from URL and configure for Dremio Cloud
        host = base_url.replace("https://", "").replace("http://", "").split("/")[0]

        # JDBC URL and credentials for Arrow Flight SQL JDBC driver
        if 'dremio.cloud' in host:
            # Dremio Cloud uses data.dremio.cloud for Arrow Flight SQL connections
            jdbc_host = 'data.dremio.cloud'

            # Use Arrow Flight SQL JDBC driver with token authentication (same as test_jdbc_dremio_connection)
            if pat:
                jdbc_url = f"jdbc:arrow-flight-sql://{jdbc_host}:443?useEncryption=true"
                jdbc_arrow_flight_args = { "user": "", "token": pat }

                # Add project_id if available (required for Dremio Cloud)
                if project_id:
                    # Note: catalog parameter would need to be added to URL for project selection
                    # For now, using the default project
                    pass

                auth_user = None
                auth_pass = None
            else:
                # Fallback for username/password (though not recommended for Dremio Cloud)
                jdbc_url = f"jdbc:arrow-flight-sql://{jdbc_host}:443"
                jdbc_arrow_flight_args = { "user": username, "password": password }
                auth_user = username
                auth_pass = password
        else:
            # On-premise Dremio with Arrow Flight SQL (typically port 32010 for Flight SQL)
            jdbc_url = f"jdbc:arrow-flight-sql://{host}:32010"
            jdbc_arrow_flight_args = { "user": username, "password": password }
            auth_user = username
            auth_pass = password

        try:
            # Find JDBC driver JAR file
            import os
            import glob

            # Check for SSL workaround configuration
            ssl_workaround_file = ".jdbc_ssl_config"
            if os.path.exists(ssl_workaround_file):
                logger.warning(
                    "JDBC SSL workaround detected - JDBC disabled by default"
                )
                raise ConnectionError(
                    "JDBC disabled due to SSL negotiation issues. Use Flight SQL instead."
                )

            # Look for JDBC driver in jdbc-drivers directory
            jar_pattern = os.path.join("jdbc-drivers", "*.jar")
            jar_files = glob.glob(jar_pattern)

            if not jar_files:
                raise FileNotFoundError(
                    "No JDBC driver JAR files found in jdbc-drivers/ directory"
                )

            # Prioritize Apache Arrow Flight SQL JDBC driver over legacy Dremio driver
            flight_sql_driver = None
            dremio_driver = None

            for jar_file in jar_files:
                if "flight-sql-jdbc-driver" in jar_file:
                    flight_sql_driver = jar_file
                elif "dremio-jdbc-driver" in jar_file:
                    dremio_driver = jar_file

            # Select the best available driver
            if flight_sql_driver:
                jar_path = flight_sql_driver
                driver_type = "apache_arrow_flight_sql"
                logger.info(f"Using Apache Arrow Flight SQL JDBC driver: {jar_path}")
            elif dremio_driver:
                jar_path = dremio_driver
                driver_type = "dremio_legacy"
                logger.info(f"Using legacy Dremio JDBC driver: {jar_path}")
            else:
                jar_path = jar_files[0]
                driver_type = "unknown"
                logger.info(f"Using JDBC driver: {jar_path}")

            # Start JVM if not already started with enhanced configuration
            if not jpype.isJVMStarted():
                # Enhanced JVM startup with SSL and Arrow Flight SQL configuration
                jvm_args = [
                    "-Xmx1g",
                    # SSL/TLS configuration
                    "-Dhttps.protocols=TLSv1.2,TLSv1.3",
                    "-Djdk.tls.client.protocols=TLSv1.2,TLSv1.3",
                    "-Djdk.tls.disabledAlgorithms=",
                    "-Dcom.sun.net.ssl.checkRevocation=false",
                    # Apache Arrow Flight SQL JDBC driver requirements for Java 17+
                    "--add-opens=java.base/java.nio=org.apache.arrow.memory.core,ALL-UNNAMED",
                    "--add-opens=java.base/sun.nio.ch=org.apache.arrow.memory.core,ALL-UNNAMED",
                    "--add-opens=java.base/java.lang=org.apache.arrow.memory.core,ALL-UNNAMED",
                    "--add-opens=java.base/java.lang.reflect=org.apache.arrow.memory.core,ALL-UNNAMED",
                    "--add-opens=java.base/java.io=org.apache.arrow.memory.core,ALL-UNNAMED",
                    "--add-opens=java.base/java.util=org.apache.arrow.memory.core,ALL-UNNAMED",
                ]
                jpype.startJVM(classpath=[jar_path], *jvm_args)
                logger.info(
                    "JVM started with SSL and Arrow Flight SQL configuration for JDBC connectivity"
                )
            else:
                # If JVM is already started, we need to add the JAR to the classpath
                jpype.addClassPath(jar_path)


            # Configure connection based on driver type
            if driver_type == "apache_arrow_flight_sql":
                # Apache Arrow Flight SQL JDBC driver configuration
                connection_configs = self._get_flight_sql_jdbc_configs(
                    base_url, pat, auth_user, auth_pass, project_id
                )
                driver_class = "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver"
            else:
                # Legacy Dremio JDBC driver configuration
                connection_configs = self._get_dremio_jdbc_configs(
                    host, base_url, pat, auth_user, auth_pass, project_id
                )
                driver_class = "com.dremio.jdbc.Driver"

            last_error = None

            for config in connection_configs:
                try:
                    logger.info(f"Attempting JDBC connection to: {config['url']}")
                    logger.info(f"Using driver: {driver_class}")

                    # Connect using the selected JDBC driver
                    connection = jaydebeapi.connect(
                        driver_class,
                        config["url"],
                        config["auth"],
                        jar_path,
                    )

                    logger.info(f"JDBC connection successful with {driver_type} driver")
                    self.drivers["jdbc"]["client"] = connection
                    self.drivers["jdbc"]["driver_type"] = driver_type
                    return connection

                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    endpoint_name = config.get("endpoint", "unknown")

                    if "SSL negotiation failed" in error_msg:
                        logger.warning(
                            f"SSL negotiation failed for {endpoint_name}: {error_msg}"
                        )
                        # Create SSL workaround file to disable JDBC in future
                        with open(ssl_workaround_file, "w") as f:
                            f.write("DISABLE_JDBC_BY_DEFAULT=true\n")
                            f.write("SSL_WORKAROUND_APPLIED=true\n")
                            f.write(f"LAST_SSL_ERROR={error_msg}\n")
                        logger.warning(
                            "Created SSL workaround configuration - JDBC will be disabled by default"
                        )
                        break  # Don't try other endpoints if SSL is the issue
                    else:
                        logger.warning(
                            f"JDBC connection failed for {endpoint_name}: {error_msg}"
                        )
                        continue

            # All endpoints failed
            if last_error and "SSL negotiation failed" in str(last_error):
                logger.error(
                    "JDBC SSL negotiation failed - disabling JDBC for future connections"
                )
                logger.info(
                    "Recommendation: Use Flight SQL instead of JDBC for better compatibility"
                )
                raise ConnectionError(f"JDBC SSL negotiation failed: {last_error}")
            else:
                raise last_error

        except Exception as e:
            error_msg = str(e)
            if "SSL negotiation failed" in error_msg:
                logger.error(f"JDBC SSL error: {error_msg}")
                logger.info(
                    "JDBC has been disabled due to SSL issues. Flight SQL will be used instead."
                )
            else:
                logger.warning(f"JDBC connection failed: {error_msg}")

            raise

    def _get_flight_sql_jdbc_configs(
        self, base_url: str, pat: str, auth_user: str, auth_pass: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """Get Apache Arrow Flight SQL JDBC connection configurations."""
        configs = []

        # Extract host from base URL
        host = base_url.replace("https://", "").replace("http://", "").split("/")[0]

        if "dremio.cloud" in host:
            # Dremio Cloud Flight SQL endpoints
            endpoints = ["data.dremio.cloud"]
            port = 443
            use_tls = True
        else:
            # On-premise Dremio Flight SQL
            endpoints = [host]
            port = 32010  # Default Flight SQL port for on-premise
            use_tls = False

        for endpoint in endpoints:
            # Apache Arrow Flight SQL JDBC URL format
            if use_tls:
                jdbc_url = (
                    f"jdbc:arrow-flight-sql://{endpoint}:{port}?useEncryption=true"
                )
            else:
                jdbc_url = f"jdbc:arrow-flight-sql://{endpoint}:{port}"

            # Add authentication parameters
            if pat:
                # For Dremio Cloud with PAT, use token authentication in URL
                # URL-encode the PAT for proper transmission
                import urllib.parse

                encoded_pat = urllib.parse.quote(pat, safe="")
                jdbc_url += f"&token={encoded_pat}"
                auth_config = {}  # Token is in URL for Flight SQL JDBC
            else:
                # Username/password authentication (not typically used with Flight SQL)
                auth_config = {"user": auth_user, "password": auth_pass}

            configs.append({"url": jdbc_url, "auth": auth_config, "endpoint": endpoint})

        return configs

    def _get_dremio_jdbc_configs(
        self,
        host: str,
        base_url: str,
        pat: str,
        auth_user: str,
        auth_pass: str,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """Get legacy Dremio JDBC connection configurations."""
        configs = []

        if "dremio.cloud" in host:
            # Dremio Cloud legacy JDBC endpoints
            endpoints = ["data.dremio.cloud", "sql.dremio.cloud"]

            for endpoint in endpoints:
                jdbc_url = f"jdbc:dremio:direct={endpoint}:443;ssl=true"
                if project_id:
                    jdbc_url += f";PROJECT_ID={project_id}"

                if pat:
                    auth_config = {"user": auth_user, "password": auth_pass}
                else:
                    auth_config = [auth_user, auth_pass]

                configs.append(
                    {"url": jdbc_url, "auth": auth_config, "endpoint": endpoint}
                )
        else:
            # On-premise Dremio legacy JDBC
            jdbc_url = f"jdbc:dremio:direct={host}:31010;ssl=true"

            if pat:
                auth_config = {"user": auth_user, "password": auth_pass}
            else:
                auth_config = [auth_user, auth_pass]

            configs.append({"url": jdbc_url, "auth": auth_config, "endpoint": host})

        return configs

    def execute_query_multi_driver(
        self, sql: str, drivers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Execute query across multiple drivers."""
        results = {}

        for driver_name in drivers:
            if driver_name not in self.drivers:
                results[driver_name] = {
                    "success": False,
                    "error": f"Unknown driver: {driver_name}",
                    "execution_time": 0,
                }
                continue

            if not self.drivers[driver_name]["available"]:
                results[driver_name] = {
                    "success": False,
                    "error": f'Driver not available: {self.drivers[driver_name]["name"]}',
                    "execution_time": 0,
                }
                continue

            start_time = time.time()

            try:
                result = self._execute_query_single_driver(sql, driver_name)
                execution_time = time.time() - start_time

                results[driver_name] = {
                    "success": True,
                    "data": result["data"],
                    "row_count": result["row_count"],
                    "columns": result["columns"],
                    "execution_time": execution_time,
                    "driver_name": self.drivers[driver_name]["name"],
                }

            except Exception as e:
                execution_time = time.time() - start_time
                results[driver_name] = {
                    "success": False,
                    "error": str(e),
                    "execution_time": execution_time,
                    "driver_name": self.drivers[driver_name]["name"],
                }

        return results

    def _execute_query_single_driver(
        self, sql: str, driver_name: str
    ) -> Dict[str, Any]:
        """Execute query using a single driver."""
        if driver_name == "pyarrow_flight":
            return self._execute_pyarrow_flight(sql)
        elif driver_name == "adbc_flight":
            return self._execute_adbc_flight(sql)
        elif driver_name == "pyodbc":
            return self._execute_pyodbc(sql)
        elif driver_name == "jdbc":
            return self._execute_jdbc(sql)
        else:
            raise ValueError(f"Unknown driver: {driver_name}")

    def _execute_pyarrow_flight(self, sql: str) -> Dict[str, Any]:
        """Execute query using PyArrow Flight."""
        if not self.drivers["pyarrow_flight"]["client"]:
            self._create_pyarrow_flight_client()

        # Add driver comment (PyArrow client will add its own comment)
        client = self.drivers["pyarrow_flight"]["client"]
        result = client.execute_query(sql)

        if result["success"]:
            return {
                "data": result["data"],
                "row_count": result["row_count"],
                "columns": result["columns"],
            }
        else:
            raise Exception(result["message"])

    def _execute_adbc_flight(self, sql: str) -> Dict[str, Any]:
        """Execute query using ADBC Flight SQL."""
        if not self.drivers["adbc_flight"]["client"]:
            self._create_adbc_flight_client()

        # Add driver type and version as SQL comment
        try:
            import adbc_driver_flightsql

            adbc_version = adbc_driver_flightsql.__version__
        except:
            adbc_version = "unknown"

        driver_comment = f"/* Driver: ADBC Flight SQL v{adbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers["adbc_flight"]["client"]
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
            data = df.to_dict("records")
            columns = list(df.columns)
        else:
            data = []
            columns = []

        return {"data": data, "row_count": len(data), "columns": columns}

    def _infer_columns_from_sql(self, sql: str) -> List[str]:
        """Infer column names from SQL query as fallback."""
        import re

        # Simple regex to extract column aliases and expressions
        # This is a basic fallback - not perfect but better than nothing

        # Remove comments
        sql_clean = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # Extract SELECT clause
        select_match = re.search(
            r"SELECT\s+(.*?)\s+FROM", sql_clean, re.IGNORECASE | re.DOTALL
        )
        if not select_match:
            # No FROM clause, might be a simple SELECT
            select_match = re.search(
                r"SELECT\s+(.*)", sql_clean, re.IGNORECASE | re.DOTALL
            )

        if select_match:
            select_clause = select_match.group(1).strip()

            # Split by comma (basic - doesn't handle nested functions perfectly)
            columns = []
            parts = select_clause.split(",")

            for part in parts:
                part = part.strip()

                # Look for alias with quotes
                alias_match = re.search(r'"([^"]+)"$', part)
                if alias_match:
                    columns.append(alias_match.group(1))
                    continue

                # Look for alias with AS
                as_match = re.search(r"\s+AS\s+([^\s]+)$", part, re.IGNORECASE)
                if as_match:
                    alias = as_match.group(1).strip("\"'")
                    columns.append(alias)
                    continue

                # Look for simple alias (space separated)
                space_match = re.search(r"\s+([^\s]+)$", part)
                if space_match:
                    alias = space_match.group(1).strip("\"'")
                    columns.append(alias)
                    continue

                # No alias found, use the expression itself (simplified)
                expr = re.sub(r"^\s*\w+\s*\(.*\)\s*$", "EXPR$0", part)  # Function calls
                expr = re.sub(r"^\s*\d+\s*$", "EXPR$0", expr)  # Literals
                columns.append(expr.strip())

            return columns

        # Fallback
        return ["EXPR$0"]

    def _execute_pyodbc(self, sql: str) -> Dict[str, Any]:
        """Execute query using PyODBC."""
        if not self.drivers["pyodbc"]["client"]:
            self._create_pyodbc_client()

        # Add driver type and version as SQL comment
        try:
            import pyodbc

            pyodbc_version = pyodbc.version
        except:
            pyodbc_version = "unknown"

        driver_comment = f"/* Driver: PyODBC v{pyodbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers["pyodbc"]["client"]
        cursor = connection.cursor()
        cursor.execute(commented_sql)

        # Fetch column names
        columns = [column[0] for column in cursor.description]

        # Fetch all rows
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]

        return {"data": data, "row_count": len(data), "columns": columns}

    def _execute_jdbc(self, sql: str) -> Dict[str, Any]:
        """Execute query using JDBC."""
        if not self.drivers["jdbc"]["client"]:
            self._create_jdbc_client()

        # Add driver type and version as SQL comment
        try:
            import jaydebeapi

            jdbc_version = jaydebeapi.__version__
        except:
            jdbc_version = "unknown"

        # Determine driver type from connection
        driver_info = "JDBC (JayDeBeApi)"
        if hasattr(self.drivers["jdbc"], "driver_type"):
            if self.drivers["jdbc"]["driver_type"] == "apache_arrow_flight_sql":
                driver_info = "Apache Arrow Flight SQL JDBC"
            elif self.drivers["jdbc"]["driver_type"] == "dremio_legacy":
                driver_info = "Legacy Dremio JDBC"

        driver_comment = f"/* Driver: {driver_info} v{jdbc_version} */ "
        commented_sql = driver_comment + sql

        connection = self.drivers["jdbc"]["client"]
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
                elif hasattr(value, "__class__") and "java" in str(value.__class__):
                    # Handle Java objects by converting to string
                    row_dict[column_name] = str(value)
                else:
                    # Handle Python objects directly
                    row_dict[column_name] = value
            data.append(row_dict)

        return {"data": data, "row_count": len(data), "columns": columns}

    def get_projects(self) -> Dict[str, Any]:
        """Get projects using the most reliable method."""
        # Try PyArrow Flight first, then fall back to REST API
        try:
            if self.drivers["pyarrow_flight"]["available"]:
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
                "success": False,
                "projects": [],
                "error": str(e),
                "message": f"Failed to retrieve projects: {str(e)}",
            }

    def test_connection(self, drivers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Test connection across multiple drivers."""
        results = {}

        for driver_name in drivers:
            if driver_name not in self.drivers:
                results[driver_name] = {
                    "success": False,
                    "error": f"Unknown driver: {driver_name}",
                    "driver_name": driver_name,
                }
                continue

            if not self.drivers[driver_name]["available"]:
                results[driver_name] = {
                    "success": False,
                    "error": f'Driver not available: {self.drivers[driver_name]["name"]}',
                    "driver_name": self.drivers[driver_name]["name"],
                }
                continue

            try:
                # Test with a simple query
                test_result = self._execute_query_single_driver(
                    "SELECT 1 as test", driver_name
                )
                results[driver_name] = {
                    "success": True,
                    "message": f'Connection successful via {self.drivers[driver_name]["name"]}',
                    "driver_name": self.drivers[driver_name]["name"],
                    "test_result": test_result,
                }

            except Exception as e:
                results[driver_name] = {
                    "success": False,
                    "error": str(e),
                    "driver_name": self.drivers[driver_name]["name"],
                }

        return results

    def close_connections(self):
        """Close all active connections."""
        for driver_name, driver_info in self.drivers.items():
            if driver_info["client"]:
                try:
                    if driver_name == "pyarrow_flight":
                        # PyArrow Flight doesn't need explicit closing
                        pass
                    elif driver_name in ["adbc_flight", "pyodbc", "jdbc"]:
                        driver_info["client"].close()
                    driver_info["client"] = None
                except Exception as e:
                    logger.warning(f"Error closing {driver_name} connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connections()
