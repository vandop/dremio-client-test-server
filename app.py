"""
Main Flask application for Dremio Reporting Server.
"""
from flask import Flask, render_template, jsonify, request, session
from config import Config
from dremio_hybrid_client import DremioHybridClient
from dremio_multi_driver_client import DremioMultiDriverClient
from debug_config import debug_config_manager
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY', 'debug-secret-key-change-in-production')

# Initialize Dremio hybrid client (Flight SQL + REST API)
dremio_client = DremioHybridClient()


@app.route('/')
def index():
    """Main hello world page."""
    return render_template('index.html')


@app.route('/reports')
def reports():
    """Reports page showing Dremio jobs."""
    return render_template('reports.html')


@app.route('/query')
def query():
    """SQL Query interface page."""
    return render_template('query.html')


@app.route('/debug')
def debug():
    """Debug configuration page."""
    return render_template('debug.html')


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


@app.route('/api/query', methods=['POST'])
def execute_query():
    """API endpoint to execute SQL queries using Flight SQL."""
    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing SQL query in request body',
                'error_type': 'missing_sql'
            }), 400

        sql = data['sql']
        limit = data.get('limit', 1000)  # Default limit for safety

        # Add limit if not present and query is a SELECT
        if limit and 'LIMIT' not in sql.upper() and sql.strip().upper().startswith('SELECT'):
            sql = f"{sql} LIMIT {limit}"

        result = dremio_client.execute_query(sql)

        if result['success']:
            return jsonify({
                'status': 'success',
                'data': result['data'],
                'row_count': result['row_count'],
                'columns': result['columns'],
                'query': result['query'],
                'message': result['message'],
                'query_method': 'flight_sql'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message'],
                'error_type': result.get('error_type'),
                'query': result.get('query'),
                'suggestions': result.get('suggestions', [])
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'error_type': 'unexpected_error'
        }), 500


@app.route('/api/query-multi-driver', methods=['POST'])
def execute_query_multi_driver():
    """Execute SQL query across multiple drivers."""
    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing SQL query in request body'
            }), 400

        sql = data['sql']
        drivers = data.get('drivers', ['pyarrow_flight'])  # Default to PyArrow Flight

        if not drivers:
            return jsonify({
                'status': 'error',
                'message': 'At least one driver must be selected'
            }), 400

        # Create multi-driver client with debug config if available
        config_override = debug_config_manager.get_config_for_client()
        client = DremioMultiDriverClient(config_override=config_override)

        # Get available drivers
        available_drivers = client.get_available_drivers()

        # Filter requested drivers to only available ones
        valid_drivers = [d for d in drivers if d in available_drivers]

        if not valid_drivers:
            return jsonify({
                'status': 'error',
                'message': 'None of the requested drivers are available',
                'requested_drivers': drivers,
                'available_drivers': list(available_drivers.keys())
            }), 400

        # Execute query across multiple drivers
        results = client.execute_query_multi_driver(sql, valid_drivers)

        # Close connections
        client.close_connections()

        # Ensure all results are JSON serializable
        def make_json_serializable(obj):
            """Convert objects to JSON serializable format."""
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: make_json_serializable(value) for key, value in obj.items()}
            else:
                # Convert any other object to string
                return str(obj)

        serializable_results = make_json_serializable(results)

        return jsonify({
            'status': 'success',
            'sql': sql,
            'drivers_tested': valid_drivers,
            'results': serializable_results,
            'summary': {
                'total_drivers': len(valid_drivers),
                'successful': len([r for r in serializable_results.values() if r.get('success', False)]),
                'failed': len([r for r in serializable_results.values() if not r.get('success', False)])
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Multi-driver query failed: {str(e)}'
        }), 500


@app.route('/api/drivers')
def get_available_drivers():
    """Get available database drivers."""
    try:
        # Create client with debug config
        config_override = debug_config_manager.get_config_for_client()
        client = DremioMultiDriverClient(config_override=config_override)

        available_drivers = client.get_available_drivers()

        return jsonify({
            'status': 'success',
            'drivers': available_drivers,
            'count': len(available_drivers)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get drivers: {str(e)}'
        }), 500


@app.route('/api/schemas')
def get_schemas():
    """API endpoint to get available schemas using Flight SQL."""
    try:
        result = dremio_client.get_schemas()

        if result['success']:
            return jsonify({
                'status': 'success',
                'schemas': result['schemas'],
                'count': result['count'],
                'message': result['message'],
                'query_method': result['query_method']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message'],
                'error_type': result.get('error_type'),
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


@app.route('/api/debug/config', methods=['GET', 'POST'])
def debug_config():
    """Debug configuration management."""
    try:
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'config': debug_config_manager.get_current_config(),
                'debug_info': debug_config_manager.get_debug_info()
            })

        elif request.method == 'POST':
            data = request.get_json() or {}
            result = debug_config_manager.update_config(data)
            return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Debug config error: {str(e)}'
        }), 500


@app.route('/api/debug/test-connection', methods=['POST'])
def debug_test_connection():
    """Test connection and fetch projects with debug config."""
    try:
        result = debug_config_manager.test_connection_and_fetch_projects()
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}'
        }), 500


@app.route('/api/debug/projects', methods=['GET'])
def debug_get_projects():
    """Get available projects from debug config."""
    try:
        projects = debug_config_manager.get_available_projects()
        return jsonify({
            'status': 'success',
            'projects': projects,
            'count': len(projects)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get projects: {str(e)}'
        }), 500


@app.route('/api/debug/set-project', methods=['POST'])
def debug_set_project():
    """Set project ID after fetching projects."""
    try:
        data = request.get_json()
        if not data or 'project_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing project_id in request'
            }), 400

        result = debug_config_manager.set_project_id(data['project_id'])
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to set project: {str(e)}'
        }), 500


@app.route('/api/debug/reset', methods=['POST'])
def debug_reset_config():
    """Reset debug configuration to defaults."""
    try:
        result = debug_config_manager.reset_config()
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to reset config: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Allow port override via environment variable
    port = int(os.environ.get('PORT', Config.PORT))

    print("Starting Dremio Reporting Server...")
    print(f"Server will be accessible at http://{Config.HOST}:{port}")

    # Check if Dremio configuration is available
    try:
        Config.validate_dremio_config()
        print("✓ Dremio configuration validated")
    except ValueError as e:
        print(f"⚠ Warning: {e}")
        print("The server will start but Dremio features may not work.")

    app.run(
        host=Config.HOST,
        port=port,
        debug=Config.DEBUG
    )
