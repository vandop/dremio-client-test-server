# Dremio Reporting Server

A Flask-based web application for connecting to Dremio Cloud and generating reports on job execution and analytics.

## Features

- 🚀 **Hello World Web App**: Clean, responsive Flask application
- 🔗 **Dremio Cloud Integration**: Connect using PyArrow and REST API
- 📊 **Job Reports**: View and analyze Dremio jobs and execution details
- 🐳 **DevContainer Ready**: Fully configured development environment
- 🌐 **External Access**: Web server accessible from outside the container
- ⚙️ **Environment Configuration**: Easy setup through environment variables

## Quick Start

### 1. Using DevContainer (Recommended)

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container" or use Command Palette: `Dev Containers: Reopen in Container`
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your Dremio Cloud credentials
5. Run the application:
   ```bash
   python app.py
   ```
6. Access the app at `http://localhost:5000`

### 2. Local Development

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
4. Run the application:
   ```bash
   python app.py
   ```

### 3. Using Docker Compose

1. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
2. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Configuration

Create a `.env` file based on `.env.example` and configure the following variables:

### Required Dremio Configuration
- `DREMIO_CLOUD_URL`: Your Dremio Cloud URL (e.g., `https://your-org.dremio.cloud`)
- `DREMIO_USERNAME`: Your Dremio Cloud username/email
- `DREMIO_PASSWORD`: Your Dremio Cloud password
- `DREMIO_PROJECT_ID`: Your Dremio project ID (found in project settings)

### Optional Flask Configuration
- `FLASK_DEBUG`: Enable debug mode (default: `true`)
- `FLASK_HOST`: Host to bind to (default: `0.0.0.0`)
- `FLASK_PORT`: Port to run on (default: `5000`)
- `SECRET_KEY`: Flask secret key for sessions

## Project Structure

```
dremio-reporting-server/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── dremio_client.py       # Dremio API client
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker Compose configuration
├── .env.example          # Environment variables template
├── .devcontainer/        # DevContainer configuration
│   ├── devcontainer.json
│   └── Dockerfile
├── templates/            # HTML templates
│   ├── index.html        # Hello world page
│   └── reports.html      # Jobs report page
├── static/               # Static assets
│   └── style.css         # Application styles
└── reports/              # Reports module
    ├── __init__.py
    └── dremio_jobs.py    # Job reporting logic
```

## API Endpoints

### Web Pages
- `GET /` - Hello world main page
- `GET /reports` - Dremio jobs report page

### API Endpoints
- `GET /api/test-connection` - Test Dremio Cloud connection
- `GET /api/jobs?limit=N` - Get list of Dremio jobs
- `GET /api/jobs/{job_id}` - Get details for specific job
- `GET /health` - Health check endpoint

## Usage

### Testing Connection
1. Navigate to the main page (`/`)
2. Click "Test Dremio Connection" to verify your configuration
3. Check the status message for connection results

### Viewing Job Reports
1. Navigate to the Reports page (`/reports`)
2. Click "Load Jobs" to fetch jobs from your Dremio project
3. Use the dropdown to adjust the number of jobs to display
4. Click on any job row to view additional details (feature can be expanded)

## Development

### DevContainer Features
The DevContainer includes:
- Python 3.11 with all dependencies
- VS Code extensions for Python development
- **Augment Code extension** for AI-powered coding assistance
- Auto-formatting with Black
- Linting with Flake8
- Port forwarding for external access

### Adding New Reports
1. Create new report functions in `reports/dremio_jobs.py`
2. Add API endpoints in `app.py`
3. Create corresponding UI in templates
4. Update styles in `static/style.css`

### Testing
Run tests using pytest:
```bash
pytest
```

## Troubleshooting

### Connection Issues
- Verify your `.env` file has correct Dremio Cloud credentials
- Check that your Dremio Cloud URL is correct and accessible
- Ensure your user has permissions to view jobs in the project

### Port Access Issues
- Make sure port 5000 is forwarded in your DevContainer
- Check firewall settings if accessing from external networks
- Verify the Flask app is binding to `0.0.0.0` not `127.0.0.1`

### Authentication Errors
- Double-check username and password in `.env`
- Verify the project ID is correct
- Check if your Dremio Cloud account has the necessary permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
