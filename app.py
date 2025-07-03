"""
Main Flask application for Dremio Reporting Server.
"""
from flask import Flask, render_template, jsonify, request
from config import Config
from dremio_client import DremioClient
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Dremio client
dremio_client = DremioClient()


@app.route('/')
def index():
    """Main hello world page."""
    return render_template('index.html')


@app.route('/reports')
def reports():
    """Reports page showing Dremio jobs."""
    return render_template('reports.html')


@app.route('/api/test-connection')
def test_connection():
    """API endpoint to test Dremio connection."""
    try:
        result = dremio_client.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}'
        }), 500


@app.route('/api/jobs')
def get_jobs():
    """API endpoint to retrieve Dremio jobs."""
    try:
        limit = request.args.get('limit', 50, type=int)
        result = dremio_client.get_jobs(limit=limit)

        if result['success']:
            return jsonify({
                'status': 'success',
                'jobs': result['jobs'],
                'count': result['count'],
                'message': result['message']
            })
        else:
            # Return detailed error information
            return jsonify({
                'status': 'error',
                'message': result['message'],
                'error_type': result.get('error_type'),
                'details': result.get('details'),
                'suggestions': result.get('auth_details', {}).get('suggestions', [])
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'error_type': 'unexpected_error'
        }), 500


@app.route('/api/jobs/<job_id>')
def get_job_details(job_id):
    """API endpoint to get details for a specific job."""
    try:
        job_details = dremio_client.get_job_details(job_id)
        
        if job_details:
            return jsonify({
                'status': 'success',
                'job': job_details
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Job not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve job details: {str(e)}'
        }), 500


@app.route('/api/projects')
def get_projects():
    """API endpoint to retrieve accessible Dremio projects."""
    try:
        result = dremio_client.get_projects()

        if result['success']:
            return jsonify({
                'status': 'success',
                'projects': result['projects'],
                'total_count': result['total_count'],
                'current_project_found': result.get('current_project_found', False),
                'message': result['message']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message'],
                'error_type': result.get('error_type'),
                'details': result.get('details'),
                'suggestions': result.get('suggestions', [])
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'error_type': 'unexpected_error'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Dremio Reporting Server'
    })


if __name__ == '__main__':
    print("Starting Dremio Reporting Server...")
    print(f"Server will be accessible at http://{Config.HOST}:{Config.PORT}")
    
    # Check if Dremio configuration is available
    try:
        Config.validate_dremio_config()
        print("✓ Dremio configuration validated")
    except ValueError as e:
        print(f"⚠ Warning: {e}")
        print("The server will start but Dremio features may not work.")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
