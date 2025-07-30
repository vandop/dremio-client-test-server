#!/usr/bin/env python3
"""
Dremio REST API SQL Client
==========================

This module provides a client for executing SQL queries through Dremio's REST API.
It uses the /api/v3/sql endpoint to submit queries and the Job API to retrieve results.

Features:
- Submit SQL queries via REST API
- Poll for job completion
- Retrieve query results
- Handle authentication with Personal Access Tokens
- Support for query context and Nessie references
- Comprehensive error handling and logging

Usage:
    client = DremioRestSqlClient(
        base_url="https://api.dremio.cloud",
        pat="your-personal-access-token"
    )

    result = client.execute_query("SELECT 1 as test")
    print(result)
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DremioRestSqlClient:
    """
    Client for executing SQL queries through Dremio's REST API.

    This client uses the /api/v3/sql endpoint to submit queries and the Job API
    to retrieve results. It handles authentication, job polling, and result retrieval.
    """

    def __init__(self, base_url: str = None, pat: str = None, project_id: str = None):
        """
        Initialize the Dremio REST SQL client.

        Args:
            base_url: Dremio API base URL (e.g., "https://api.dremio.cloud")
            pat: Personal Access Token for authentication
            project_id: Dremio Cloud project ID (for Cloud deployments)
        """
        # Load environment variables
        load_dotenv()

        # Set configuration from parameters or environment
        self.base_url = base_url or os.getenv(
            "DREMIO_CLOUD_URL", "https://api.dremio.cloud"
        )
        self.pat = pat or os.getenv("DREMIO_PAT")
        self.project_id = project_id or os.getenv("DREMIO_PROJECT_ID")

        # Determine if this is Dremio Cloud or Dremio Software
        self.is_cloud = "dremio.cloud" in self.base_url

        # Format base URL based on deployment type
        if self.base_url.endswith("/"):
            self.base_url = self.base_url.rstrip("/")

        if self.is_cloud:
            # Dremio Cloud: https://api.dremio.cloud/v0/projects/{project-id}
            if not self.project_id:
                raise ValueError("project_id is required for Dremio Cloud")
            self.api_base = f"{self.base_url}/v0/projects/{self.project_id}"
        else:
            # Dremio Software: https://{hostname}/api/v3
            if not self.base_url.endswith("/api/v3"):
                self.api_base = self.base_url + "/api/v3"
            else:
                self.api_base = self.base_url

        # Set up session with authentication
        self.session = requests.Session()
        if self.pat:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.pat}",
                    "Content-Type": "application/json",
                }
            )

        # Configuration
        self.timeout = 30  # Request timeout in seconds
        self.poll_interval = 2  # Job polling interval in seconds
        self.max_poll_time = 300  # Maximum time to wait for job completion (5 minutes)

        logger.info(f"✓ Dremio REST SQL client initialized")
        logger.info(f"  Deployment: {'Cloud' if self.is_cloud else 'Software'}")
        logger.info(f"  API Base: {self.api_base}")
        logger.info(f"  Has PAT: {bool(self.pat)}")
        if self.is_cloud:
            # Mask project ID for security
            masked_project_id = (
                f"{self.project_id[:8]}...{self.project_id[-4:]}"
                if self.project_id
                else "None"
            )
            logger.info(f"  Project ID: {masked_project_id}")

    def submit_query(
        self,
        sql: str,
        context: List[str] = None,
        references: Dict[str, Dict[str, str]] = None,
    ) -> str:
        """
        Submit an SQL query to Dremio and return the job ID.

        Args:
            sql: SQL query to execute
            context: Path to the container where the query should run (optional)
            references: References to specific versions in Nessie sources (optional)

        Returns:
            Job ID for the submitted query

        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response is invalid
        """
        logger.info(f"Submitting SQL query via REST API...")
        logger.debug(f"SQL: {sql}")

        # Prepare request payload
        payload = {"sql": sql}

        if context:
            payload["context"] = context
            logger.debug(f"Context: {context}")

        if references:
            payload["references"] = references
            logger.debug(f"References: {references}")

        # Submit query
        url = f"{self.api_base}/sql"
        logger.debug(f"POST {url}")

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            job_id = result.get("id")

            if not job_id:
                raise ValueError("No job ID returned from SQL submission")

            logger.info(f"✓ Query submitted successfully, job ID: {job_id}")
            return job_id

        except requests.RequestException as e:
            logger.error(f"Failed to submit SQL query: {e}")
            raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Invalid response from SQL submission: {e}")
            raise ValueError(f"Invalid response: {e}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.

        Args:
            job_id: Job ID to check

        Returns:
            Job status information
        """
        url = f"{self.api_base}/job/{job_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Failed to get job status: {e}")
            raise

    def get_job_results(
        self, job_id: str, limit: int = 500, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get the results of a completed job.

        Args:
            job_id: Job ID to get results for
            limit: Maximum number of rows to return
            offset: Number of rows to skip

        Returns:
            Job results
        """
        url = f"{self.api_base}/job/{job_id}/results"
        params = {"limit": limit, "offset": offset}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Failed to get job results: {e}")
            raise

    def wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        """
        Wait for a job to complete and return its final status.

        Args:
            job_id: Job ID to wait for

        Returns:
            Final job status

        Raises:
            TimeoutError: If job doesn't complete within max_poll_time
        """
        logger.info(f"Waiting for job {job_id} to complete...")
        start_time = time.time()

        while time.time() - start_time < self.max_poll_time:
            job_status = self.get_job_status(job_id)
            state = job_status.get("jobState", "UNKNOWN")

            logger.debug(f"Job {job_id} state: {state}")

            if state in ["COMPLETED", "FAILED", "CANCELED"]:
                logger.info(f"✓ Job {job_id} finished with state: {state}")
                return job_status

            time.sleep(self.poll_interval)

        raise TimeoutError(
            f"Job {job_id} did not complete within {self.max_poll_time} seconds"
        )

    def execute_query(
        self,
        sql: str,
        context: List[str] = None,
        references: Dict[str, Dict[str, str]] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Execute an SQL query and return the results.

        This is a convenience method that combines query submission, job waiting,
        and result retrieval into a single call.

        Args:
            sql: SQL query to execute
            context: Path to the container where the query should run (optional)
            references: References to specific versions in Nessie sources (optional)
            limit: Maximum number of rows to return

        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Submit query
            job_id = self.submit_query(sql, context, references)

            # Wait for completion
            job_status = self.wait_for_completion(job_id)

            # Check if job completed successfully
            if job_status.get("jobState") != "COMPLETED":
                error_msg = job_status.get("errorMessage", "Unknown error")
                raise RuntimeError(f"Query failed: {error_msg}")

            # Get results
            results = self.get_job_results(job_id, limit=limit)

            # Format response
            return {
                "success": True,
                "job_id": job_id,
                "job_status": job_status,
                "results": results,
                "row_count": len(results.get("rows", [])),
                "query": sql,
                "driver": "rest_api",
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": sql,
                "driver": "rest_api",
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Dremio by executing a simple query.

        Returns:
            Connection test results
        """
        logger.info("Testing Dremio REST API connection...")

        try:
            # Test with a simple query
            result = self.execute_query("SELECT 1 as test_connection", limit=1)

            if result["success"]:
                logger.info("✓ REST API connection test successful")
                return {
                    "success": True,
                    "message": "Successfully connected to Dremio using REST API",
                    "driver": "rest_api",
                    "api_base": self.api_base,
                }
            else:
                logger.error(f"REST API connection test failed: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "driver": "rest_api",
                }

        except Exception as e:
            logger.error(f"REST API connection test failed: {e}")
            return {"success": False, "error": str(e), "driver": "rest_api"}


def main():
    """Test the REST SQL client."""
    print("🧪 Dremio REST API SQL Client Test")
    print("=" * 50)

    client = DremioRestSqlClient()

    # Test connection
    connection_result = client.test_connection()
    print(f"Connection test: {connection_result}")

    if connection_result["success"]:
        # Test a simple query
        print("\nTesting simple query...")
        result = client.execute_query(
            "SELECT 1 as test_value, 'Hello from REST API' as message"
        )
        print(f"Query result: {result}")


if __name__ == "__main__":
    main()
