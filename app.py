"""
Main Flask application for Dremio Reporting Server.
"""
from flask import Flask, render_template, jsonify, request, session, redirect
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


def is_auth_configured():
    """Check if authentication is properly configured."""
    # Check session first
    if session.get('auth_configured'):
        return True

    # Check environment variables
    dremio_url = os.environ.get('DREMIO_CLOUD_URL') or os.environ.get('DREMIO_URL')
    pat = os.environ.get('DREMIO_PAT')
    username = os.environ.get('DREMIO_USERNAME')
    password = os.environ.get('DREMIO_PASSWORD')

    # Must have URL and either PAT or username/password
    has_url = bool(dremio_url)
    has_auth = bool(pat) or (bool(username) and bool(password))

    return has_url and has_auth


def get_current_config():
    """Get current configuration for pre-populating the form."""
    return {
        'dremio_url': os.environ.get('DREMIO_CLOUD_URL') or os.environ.get('DREMIO_URL', ''),
        'project_id': os.environ.get('DREMIO_PROJECT_ID', ''),
        'username': os.environ.get('DREMIO_USERNAME', ''),
        'password': os.environ.get('DREMIO_PASSWORD', ''),
        'pat': os.environ.get('DREMIO_PAT', '')
    }


@app.route('/')
def index():
    """Main hello world page - redirects to auth if not configured."""
    # Check if authentication is configured
    if not is_auth_configured():
        return redirect('/auth')
    return render_template('index.html')


@app.route('/reports')
def reports():
    """Reports page showing Dremio jobs."""
    if not is_auth_configured():
        return redirect('/auth')
    return render_template('reports.html')


@app.route('/query')
def query():
    """SQL Query interface page."""
    if not is_auth_configured():
        return redirect('/auth')
    return render_template('query.html')


@app.route('/debug')
def debug():
    """Debug configuration page."""
    if not is_auth_configured():
        return redirect('/auth')
    return render_template('debug.html')


@app.route('/auth')
def auth():
    """Authentication configuration page."""
    config = get_current_config()
    return render_template('auth.html', config=config)


@app.route('/api/configure-auth', methods=['POST'])
def configure_auth():
    """API endpoint to configure authentication."""
    try:
        dremio_type = request.form.get('dremio_type')
        auth_method = request.form.get('auth_method')
        dremio_url = request.form.get('dremio_url')
        project_id = request.form.get('project_id', '')

        if not dremio_type or not auth_method or not dremio_url:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            })

        # Validate URL format
        if not dremio_url.startswith(('http://', 'https://')):
            return jsonify({
                'success': False,
                'error': 'URL must start with http:// or https://'
            })

        # Set environment variables for this session
        os.environ['DREMIO_CLOUD_URL'] = dremio_url
        os.environ['DREMIO_URL'] = dremio_url

        if project_id:
            os.environ['DREMIO_PROJECT_ID'] = project_id

        if auth_method == 'pat':
            pat = request.form.get('pat')
            if not pat:
                return jsonify({
                    'success': False,
                    'error': 'Personal Access Token is required'
                })
            os.environ['DREMIO_PAT'] = pat
            # Clear username/password
            os.environ.pop('DREMIO_USERNAME', None)
            os.environ.pop('DREMIO_PASSWORD', None)

        elif auth_method == 'credentials':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                return jsonify({
                    'success': False,
                    'error': 'Username and password are required'
                })
            os.environ['DREMIO_USERNAME'] = username
            os.environ['DREMIO_PASSWORD'] = password
            # Clear PAT
            os.environ.pop('DREMIO_PAT', None)

        # Test the connection
        try:
            # Reinitialize the client with new config
            global dremio_client
            dremio_client = DremioHybridClient()

            # Test connection
            result = dremio_client.test_connection()

            if result.get('success'):
                # Mark as configured in session
                session['auth_configured'] = True

                return jsonify({
                    'success': True,
                    'message': f'Successfully connected to {dremio_type.title()} using {auth_method.upper()}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Connection test failed: {result.get("error", "Unknown error")}'
                })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Connection test failed: {str(e)}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Configuration error: {str(e)}'
        })


@app.route('/api/test-connection')
def test_connection():
    """API endpoint to test Dremio connection."""
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
    if not is_auth_configured():
        return jsonify({
            'status': 'error',
            'message': 'Authentication not configured'
        }), 401

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
