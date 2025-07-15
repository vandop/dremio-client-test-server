# Changelog

All notable changes to the Dremio Reporting Server project will be documented in this file.

## [2.0.0] - 2025-07-15 - Apache Arrow Flight SQL JDBC Driver Migration

### 🎉 Major Update: JDBC Driver Migration

This release represents a significant upgrade to the JDBC connectivity layer, resolving SSL issues and improving performance through the adoption of the Apache Arrow Flight SQL JDBC driver.

### ✅ Added
- **Apache Arrow Flight SQL JDBC Driver v17.0.0**: New primary JDBC driver from Maven Central
- **Intelligent Driver Selection**: Automatic prioritization of Apache Arrow Flight SQL JDBC over legacy driver
- **Enhanced JVM Configuration**: Java 17+ module access configuration for Arrow Flight SQL
- **SSL Compatibility Layer**: Resolves SSL negotiation failures with Dremio Cloud
- **Comprehensive Driver Testing**: New test suite for Apache Arrow Flight SQL JDBC driver
- **Updated Setup Script**: Automatic download of both Apache Arrow Flight SQL and legacy drivers
- **Enhanced Documentation**: Complete migration guide and troubleshooting documentation

### 🔧 Changed
- **Primary JDBC Driver**: Migrated from legacy Dremio JDBC driver to Apache Arrow Flight SQL JDBC driver
- **Connection URL Format**: Updated to use `jdbc:arrow-flight-sql://` protocol
- **Authentication Method**: Enhanced PAT token URL encoding for Flight SQL compatibility
- **Driver Class**: Changed to `org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver`
- **JVM Startup Parameters**: Added `--add-opens` flags for Java 17+ compatibility
- **Multi-Driver Client**: Enhanced to support both driver types with automatic selection

### 🐛 Fixed
- **SSL Negotiation Failures**: Completely resolved SSL issues with Dremio Cloud connections
- **Java 17 Compatibility**: Fixed module access issues with modern Java versions
- **Connection Reliability**: Improved connection stability and error handling
- **Authentication Issues**: Resolved PAT token authentication problems
- **Driver Loading**: Fixed JAR loading and class path issues

### 📚 Documentation Updates
- **README.md**: Updated with new driver information and migration details
- **JDBC_SSL_RESOLUTION.md**: Comprehensive documentation of the SSL issue resolution
- **Setup Guide**: Updated setup instructions for the new driver
- **Troubleshooting**: Enhanced troubleshooting guide with new driver specifics

### 🔄 Migration Details

#### Before (Legacy Dremio JDBC Driver)
- **Driver**: `dremio-jdbc-driver-LATEST.jar` (26.0.0, ~48MB)
- **Class**: `com.dremio.jdbc.Driver`
- **URL**: `jdbc:dremio:direct=data.dremio.cloud:443;ssl=true`
- **Issues**: SSL negotiation failures, large file size, compatibility issues

#### After (Apache Arrow Flight SQL JDBC Driver)
- **Driver**: `flight-sql-jdbc-driver-17.0.0.jar` (~3MB)
- **Class**: `org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver`
- **URL**: `jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true&token=<PAT>`
- **Benefits**: SSL compatibility, better performance, smaller size, modern protocol

### 🧪 Testing
- **New Test Suite**: `test_arrow_flight_sql_jdbc.py` for comprehensive driver testing
- **Multi-Driver Testing**: Enhanced testing for driver selection and fallback
- **SSL Compatibility Testing**: Verified SSL connections work correctly
- **Authentication Testing**: Confirmed PAT token authentication functions properly

### 📦 Dependencies
- **Added**: Apache Arrow Flight SQL JDBC driver v17.0.0 from Maven Central
- **Maintained**: Legacy Dremio JDBC driver as backup option
- **Enhanced**: JayDeBeApi integration for both driver types

### 🔒 Security
- **SSL Improvements**: Resolved SSL negotiation issues with modern TLS protocols
- **Authentication**: Enhanced PAT token handling with proper URL encoding
- **Certificate Validation**: Improved SSL certificate validation process

### 🚀 Performance
- **Data Transfer**: More efficient data transfer using Apache Arrow format
- **Connection Speed**: Faster connection establishment with Flight SQL protocol
- **Memory Usage**: Reduced memory footprint with smaller driver size
- **Query Performance**: Improved query execution performance

### 🛠️ Developer Experience
- **Automatic Setup**: Setup script handles driver download and configuration
- **Clear Logging**: Enhanced logging for driver selection and connection status
- **Error Messages**: Improved error messages and troubleshooting guidance
- **Documentation**: Comprehensive migration and usage documentation

### 📋 Compatibility
- **Java 17+**: Full compatibility with modern Java versions
- **Dremio Cloud**: Optimized for Dremio Cloud SSL configuration
- **Legacy Support**: Maintains backward compatibility with legacy driver as fallback
- **Multi-Platform**: Works across different operating systems and architectures

---

## [1.0.0] - 2025-07-14 - Initial Release

### Added
- Initial Flask-based web application for Dremio reporting
- Multi-driver support (PyArrow Flight SQL, JDBC, ADBC)
- Dremio Cloud integration with Personal Access Token authentication
- REST API endpoints for job queries and data retrieval
- Web interface for testing and monitoring
- DevContainer support for development
- Comprehensive setup and configuration scripts

### Features
- Hello World web application
- Dremio Cloud connectivity
- Job reports and analytics
- Environment-based configuration
- Docker container support
- Automatic driver detection
