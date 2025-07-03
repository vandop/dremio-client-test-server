"""
Dremio jobs reporting functionality.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dremio_client import DremioClient


class DremioJobsReporter:
    """Class for generating reports on Dremio jobs."""
    
    def __init__(self):
        """Initialize the jobs reporter."""
        self.client = DremioClient()
    
    def get_jobs_summary(self, limit: int = 100) -> Dict:
        """
        Get a summary of jobs with statistics.
        
        Args:
            limit: Maximum number of jobs to analyze
            
        Returns:
            Dictionary containing job summary and statistics
        """
        jobs_result = self.client.get_jobs(limit=limit)

        if not jobs_result['success']:
            return {
                'total_jobs': 0,
                'jobs': [],
                'statistics': {},
                'error': jobs_result
            }

        jobs = jobs_result['jobs']

        if not jobs:
            return {
                'total_jobs': 0,
                'jobs': [],
                'statistics': {}
            }
        
        # Calculate statistics
        stats = self._calculate_job_statistics(jobs)
        
        return {
            'total_jobs': len(jobs),
            'jobs': jobs,
            'statistics': stats
        }
    
    def _calculate_job_statistics(self, jobs: List[Dict]) -> Dict:
        """
        Calculate statistics from a list of jobs.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary containing various statistics
        """
        if not jobs:
            return {}
        
        # Count jobs by status
        status_counts = {}
        query_type_counts = {}
        user_counts = {}
        total_duration = 0
        duration_count = 0
        
        for job in jobs:
            # Status counts
            status = job.get('jobState', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Query type counts
            query_type = job.get('queryType', 'Unknown')
            query_type_counts[query_type] = query_type_counts.get(query_type, 0) + 1
            
            # User counts
            user = job.get('user', 'Unknown')
            user_counts[user] = user_counts.get(user, 0) + 1
            
            # Duration calculation
            if job.get('startTime') and job.get('endTime'):
                try:
                    start = datetime.fromisoformat(job['startTime'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(job['endTime'].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                    total_duration += duration
                    duration_count += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate average duration
        avg_duration = total_duration / duration_count if duration_count > 0 else 0
        
        return {
            'status_distribution': status_counts,
            'query_type_distribution': query_type_counts,
            'user_distribution': user_counts,
            'average_duration_seconds': round(avg_duration, 2),
            'total_analyzed_jobs': len(jobs)
        }
    
    def get_recent_jobs(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get jobs from the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of recent job dictionaries
        """
        jobs_result = self.client.get_jobs(limit=limit)

        if not jobs_result['success']:
            return []

        all_jobs = jobs_result['jobs']

        if not all_jobs:
            return []
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_jobs = []
        for job in all_jobs:
            if job.get('startTime'):
                try:
                    start_time = datetime.fromisoformat(job['startTime'].replace('Z', '+00:00'))
                    if start_time.replace(tzinfo=None) >= cutoff_time:
                        recent_jobs.append(job)
                except (ValueError, TypeError):
                    # If we can't parse the time, include the job to be safe
                    recent_jobs.append(job)
        
        return recent_jobs
    
    def get_failed_jobs(self, limit: int = 50) -> List[Dict]:
        """
        Get jobs that have failed.
        
        Args:
            limit: Maximum number of jobs to check
            
        Returns:
            List of failed job dictionaries
        """
        jobs_result = self.client.get_jobs(limit=limit)

        if not jobs_result['success']:
            return []

        all_jobs = jobs_result['jobs']

        failed_jobs = [
            job for job in all_jobs
            if job.get('jobState', '').upper() in ['FAILED', 'CANCELLED']
        ]

        return failed_jobs
