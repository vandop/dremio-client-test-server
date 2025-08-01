# JDBC Drivers Directory

This directory is for storing JDBC driver JAR files needed for database connectivity.

## Arrow Flight SQL JDBC Driver

To use the JDBC driver functionality with Dremio, you need the Arrow Flight SQL JDBC driver:

### Download Instructions

1. **Visit Dremio Downloads**: https://www.dremio.com/drivers/
2. **Download Arrow Flight SQL JDBC Driver**: Get the latest Arrow Flight SQL JDBC driver JAR file
3. **Place in this directory**: Copy the JAR file to this `jdbc-drivers/` directory

### Expected Files

After downloading, you should have:
```
jdbc-drivers/
├── README.md (this file)
└── flight-sql-jdbc-driver-17.0.0.jar
```

### Example Download Commands

```bash
# Download the Arrow Flight SQL JDBC driver from Maven Central
cd jdbc-drivers/
wget https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar

# Or using curl
curl -O https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar
```

### Configuration

Once the JAR file is in place, the JDBC driver will be automatically detected and used by the multi-driver client.

### Verification

You can verify the JDBC driver is working by:

1. Starting the server: `python app.py`
2. Testing JDBC connectivity: `python test_java_setup.py`
3. Using the multi-driver query interface at: http://localhost:5000/query

### Docker Usage

When using Docker, the `jdbc-drivers/` directory is mounted as a volume, so JAR files placed here will be available inside the container.

### Troubleshooting

If you encounter issues:

1. **Check Java Installation**: Ensure Java 11+ is installed
2. **Verify JAR File**: Ensure the JAR file is not corrupted
3. **Check Permissions**: Ensure the JAR file is readable
4. **Review Logs**: Check application logs for JDBC-related errors

For more information, see the main project documentation.
