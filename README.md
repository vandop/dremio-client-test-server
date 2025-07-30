# Dremio Reporting Server

A Flask-based web application for connecting to Dremio Cloud and generating reports on job execution and analytics. Features modern Apache Arrow Flight SQL JDBC driver for reliable SSL connections and optimal performance.

## Features

- 🚀 **Hello World Web App**: Clean, responsive Flask application
- 🔗 **Multi-Driver Support**: Connect using PyArrow Flight SQL, ADBC, JDBC, PyODBC, and REST API
- 📊 **Job Reports**: View and analyze Dremio jobs and execution details
- 🐳 **DevContainer Ready**: Fully configured development environment
- 🌐 **External Access**: Web server accessible from outside the container
- ⚙️ **Environment Configuration**: Easy setup through environment variables
- 🔒 **SSL Compatible**: Uses Apache Arrow Flight SQL JDBC driver (v17.0.0) for reliable SSL connections
- 🔄 **Automatic Driver Selection**: Intelligently selects the best available driver

## ⚠️ Security Notice

**IMPORTANT**: This application handles sensitive Dremio Cloud credentials. Please:
- Never commit `.env` files to version control
- Use Personal Access Tokens (PAT) instead of passwords
- Disable debug mode in production environments
- Review logs before sharing as they may contain connection details

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

1. **Automated Setup** (Recommended):
   ```bash
   # Run the setup script (installs Java, Python deps, JDBC drivers)
   ./setup.sh

   # Copy and edit environment configuration
   cp .env.example .env
   # Edit .env with your Dremio Cloud credentials

   # Start the server
   ./run.sh
   ```

2. **Manual Setup**:
   ```bash
   # Install Python 3.11+ and Java 17+
   sudo apt update
   sudo apt install python3 python3-pip openjdk-17-jdk

   # Install Python dependencies
   pip install -r requirements.txt

   # Set up environment
   cp .env.example .env
   # Edit .env with your credentials

   # Set Java environment
   export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

   # Run the application
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

## JDBC Driver Migration ✅

This project has been successfully migrated from the legacy Dremio JDBC driver to the **Apache Arrow Flight SQL JDBC driver v17.0.0** for improved reliability and performance.

### Benefits of the New Driver
- **✅ SSL Compatibility**: Resolves SSL negotiation failures with Dremio Cloud
- **✅ Better Performance**: More efficient data transfer using Apache Arrow format
- **✅ Modern Protocol**: Built on gRPC and Flight SQL standards
- **✅ Smaller Size**: ~3MB vs ~48MB for the legacy driver
- **✅ Java 17+ Support**: Optimized for modern Java environments

### Driver Details
- **Driver**: Apache Arrow Flight SQL JDBC Driver
- **Version**: 17.0.0
- **Source**: Maven Central Repository
- **Class**: `org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver`
- **URL Format**: `jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true&token=<PAT>`

### Automatic Setup
The setup script automatically downloads both drivers:
1. **Primary**: Apache Arrow Flight SQL JDBC driver (preferred)
2. **Backup**: Legacy Dremio JDBC driver (fallback)

The application intelligently selects the best available driver, prioritizing the Apache Arrow Flight SQL JDBC driver.

## Supported Drivers

The Enhanced Dremio Reporting Server supports **5 different drivers** for maximum compatibility and performance comparison:

### 1. 🚀 **PyArrow Flight SQL** (Recommended)
- **Performance**: ⚡ Fastest for data queries
- **Protocol**: gRPC Flight SQL
- **Best for**: Large result sets, analytics workloads
- **Endpoint**: `data.dremio.cloud:443`

### 2. 🌐 **REST API** (New!)
- **Performance**: 🔄 Moderate (HTTP overhead)
- **Protocol**: HTTPS REST API
- **Best for**: Simple queries, web integrations, when Flight SQL is blocked
- **Endpoint**: `https://api.dremio.cloud/v0/projects/{project-id}/sql`
- **Features**: Job polling, comprehensive error handling

### 3. 🔧 **ADBC Flight SQL**
- **Performance**: ⚡ Fast (when working)
- **Protocol**: gRPC Flight SQL via ADBC
- **Best for**: Database-agnostic applications
- **Note**: May have schema validation issues with some queries

### 4. ☕ **JDBC (Apache Arrow Flight SQL)**
- **Performance**: 🔄 Good
- **Protocol**: JDBC over gRPC Flight SQL
- **Best for**: Java applications, legacy integrations
- **Driver**: `org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver`

### 5. 🗄️ **PyODBC** (Now Fully Supported!)
- **Performance**: 🔄 Good (when properly configured)
- **Protocol**: ODBC via Arrow Flight SQL ODBC Driver
- **Best for**: Legacy applications, ODBC-based integrations
- **Driver**: Dremio Arrow Flight SQL ODBC Driver (auto-installed)
- **Configuration**: Requires proper DSN setup with credentials

### Driver Selection Strategy

The application uses intelligent driver selection:

1. **Single Query**: Uses PyArrow Flight SQL (fastest)
2. **Multi-Driver Comparison**: Tests all available drivers
3. **Fallback**: Automatically tries alternative drivers if primary fails
4. **Performance Ranking**: Displays execution time comparison

### Performance Comparison

Based on typical query execution times:

```
PyArrow Flight SQL:  ~0.9s  🏆 Winner
ADBC Flight SQL:     ~1.1s  ⚡ Fast
JDBC:                ~2.5s  🔄 Good
REST API:            ~3.2s  🌐 Reliable
PyODBC:              ~4.0s  🗄️ Compatible
```

*Note: Times vary based on query complexity and network conditions*

## ODBC Driver Setup

The Enhanced Dremio Reporting Server now includes **automatic ODBC driver installation** for the PyODBC driver.

### 🔧 **Automatic Installation**

The setup script automatically:

1. **Downloads** the latest Dremio Arrow Flight SQL ODBC driver
2. **Installs** the driver system-wide
3. **Configures** ODBC driver registration
4. **Creates** sample DSN configurations

```bash
./setup.sh  # Automatically installs ODBC driver
```

### 📋 **Manual ODBC Configuration**

If you need to configure ODBC manually, edit `/etc/odbc.ini`:

```ini
[Dremio Cloud Flight SQL]
Description=Dremio Cloud via Arrow Flight SQL ODBC
Driver=Arrow Flight SQL ODBC Driver
HOST=data.dremio.cloud
PORT=443
useEncryption=true
TOKEN=your_personal_access_token_here

[Dremio Software Flight SQL]
Description=Dremio Software via Arrow Flight SQL ODBC
Driver=Arrow Flight SQL ODBC Driver
HOST=your-dremio-host
PORT=32010
useEncryption=false
UID=your_username
PWD=your_password
```

### 🧪 **Testing ODBC Setup**

Verify your ODBC installation:

```bash
# Test ODBC driver installation
python test_odbc_setup.py

# Check installed drivers
odbcinst -q -d

# Check configured DSNs
odbcinst -q -s

# Test PyODBC integration
python -c "import pyodbc; print('Drivers:', pyodbc.drivers())"
```

### 🔍 **ODBC Connection Strings**

For PyODBC connections, use these formats:

```python
# Using DSN
connection_string = "DSN=Dremio Cloud Flight SQL"

# Direct connection string
connection_string = (
    "DRIVER={Arrow Flight SQL ODBC Driver};"
    "HOST=data.dremio.cloud;"
    "PORT=443;"
    "useEncryption=true;"
    "TOKEN=your_pat_token"
)
```

## Troubleshooting

### Common Issues and Solutions

#### 1. `./run.sh` fails with Java errors

**Problem**: `JAVA_HOME directory not found` or Java-related errors

**Solutions**:
```bash
# Check Java installation
java -version

# If Java is not installed, run setup again
./setup.sh

# Load Java environment manually
source setup_env.sh

# Verify JAVA_HOME is set correctly
echo $JAVA_HOME
```

#### 2. Port already in use

**Problem**: `Port 5001 is already in use`

**Solutions**:
```bash
# Kill process on port and retry
./run.sh --kill-port

# Or use a different port
FLASK_PORT=5002 ./run.sh
```

#### 3. JDBC driver not found

**Problem**: JDBC-related errors or missing driver files

**Solutions**:
```bash
# Re-run setup to download drivers
./setup.sh

# Check driver files
ls -la jdbc-drivers/

# Test JDBC setup
python test_java_setup.py
```

#### 4. Python dependencies missing

**Problem**: Import errors or missing packages

**Solutions**:
```bash
# Install requirements
pip install -r requirements.txt

# Check specific packages
python -c "import flask; print('Flask OK')"
python -c "import pyarrow; print('PyArrow OK')"
```

#### 5. Environment variables not loaded

**Problem**: Configuration not found or credentials missing

**Solutions**:
```bash
# Check .env file exists
ls -la .env

# Load environment manually
source setup_env.sh

# Verify environment variables
python -c "import os; print('JAVA_HOME:', os.getenv('JAVA_HOME'))"
```

#### 5. PyODBC connection issues

**Problem**: `PyODBC driver not available` or connection failures

**Solutions**:
```bash
# Test ODBC setup
python test_odbc_setup.py

# Check if ODBC driver is installed
odbcinst -q -d

# Verify PyODBC can see the driver
python -c "import pyodbc; print('Drivers:', pyodbc.drivers())"

# Reinstall ODBC driver if needed
sudo dpkg -r arrow-flight-sql-odbc-driver
./setup.sh  # Will reinstall ODBC driver

# Check ODBC configuration files
cat /etc/odbcinst.ini
cat /etc/odbc.ini
```

**Common ODBC Issues**:
- **Driver not found**: Run `./setup.sh` to install the ODBC driver
- **Connection timeout**: Check your Dremio credentials in `.env`
- **Permission denied**: Ensure ODBC files have correct permissions
- **Library not found**: Verify driver library exists: `ls -la /opt/arrow-flight-sql-odbc-driver/lib64/`

### Quick Diagnostic Commands

```bash
# Full environment check
./setup.sh && ./run.sh

# Test individual components
python test_python_setup.py
python test_java_setup.py
python test_odbc_setup.py
python test_pyarrow_client.py
python test_adbc_simple.py

# Check server status
curl http://localhost:5001/

# View logs with debug mode
FLASK_DEBUG=1 ./run.sh
```

### Getting Help

If you're still experiencing issues:

1. **Check the logs**: Look for error messages in the terminal output
2. **Run diagnostics**: Use the test scripts to identify specific issues
3. **Environment reset**: Try `./setup.sh` followed by `./run.sh`
4. **Check documentation**: Review the setup instructions above
5. **File an issue**: Include error messages and system information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
