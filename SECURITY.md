# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainer directly at: vando.miguel@outlook.com
3. Include a detailed description of the vulnerability
4. Provide steps to reproduce the issue if possible

## Security Best Practices

When using this application:

### Credentials Management
- **Never commit** `.env` files to version control
- **Always use** Personal Access Tokens (PAT) instead of passwords when possible
- **Rotate credentials** regularly
- **Use environment variables** for all sensitive configuration

### Network Security
- **Use HTTPS/TLS** for all Dremio connections
- **Verify SSL certificates** in production environments
- **Restrict network access** to necessary ports only

### Application Security
- **Change default secret keys** in production
- **Disable debug mode** in production environments
- **Use proper authentication** for web interface access
- **Keep dependencies updated** regularly

## Known Security Considerations

1. **Debug Mode**: The application runs in debug mode by default for development. Disable this in production.
2. **Logging**: Connection strings may contain sensitive information in logs. Review log output before sharing.
3. **Web Interface**: The authentication page stores credentials in environment variables for the session.

## Dependency Security

This project uses several third-party dependencies. Keep them updated:
- Run `pip audit` to check for known vulnerabilities
- Update dependencies regularly with `pip install -r requirements.txt --upgrade`

## Contact

For security-related questions or concerns, contact: vando.miguel@outlook.com
