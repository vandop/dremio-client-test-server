# Contributing to Dremio Reporting Server

Thank you for your interest in contributing to the Dremio Reporting Server! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Setup

### Prerequisites
- Python 3.11+
- Java 17+ (for JDBC drivers)
- Git

### Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/vandop/dremio-reporting-server.git
   cd dremio-reporting-server
   ```

2. Set up the development environment:
   ```bash
   ./setup.sh
   ```

3. Create your `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your Dremio credentials
   ```

4. Start the development server:
   ```bash
   ./run.sh
   ```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Security Guidelines

- **Never commit credentials** or sensitive information
- **Always use environment variables** for configuration
- **Mask sensitive data** in logs and error messages
- **Test security features** thoroughly
- **Follow the principle of least privilege**

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Test with multiple Dremio driver types
- Test both Dremio Cloud and Dremio Software scenarios

## Pull Request Process

1. **Create a descriptive title** for your PR
2. **Provide a detailed description** of your changes
3. **Reference any related issues** using `#issue-number`
4. **Ensure all tests pass**
5. **Update documentation** if needed
6. **Request review** from maintainers

## Reporting Issues

When reporting issues, please include:
- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Log output** (with sensitive information masked)

## Feature Requests

For feature requests, please:
- **Check existing issues** to avoid duplicates
- **Provide clear use case** and rationale
- **Describe the proposed solution**
- **Consider implementation complexity**

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a professional tone

## Questions?

If you have questions about contributing, please:
- Check the existing documentation
- Search through existing issues
- Create a new issue with the "question" label
- Contact the maintainers directly

Thank you for contributing!
