# Contributing to FastAPI Xtrem

Thank you for your interest in contributing to FastAPI Xtrem! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project follows a standard code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Be patient with new contributors
- Maintain a harassment-free environment

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR-USERNAME/fastapi-xtrem.git
   cd fastapi-xtrem
   ```
3. **Set up upstream remote**
   ```bash
   git remote add upstream https://github.com/original-owner/fastapi-xtrem.git
   ```
4. **Create a new branch** for your feature
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

1. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Run the development server**
   ```bash
   uvicorn api.main:app --reload
   ```

## Coding Standards

This project follows these coding standards:

- **PEP 8** style guide for Python code
- **Type hints** for all function parameters and return values
- **Docstrings** for all functions, classes, and modules
- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting

Run the following before submitting:

```bash
# Format code
black api/
isort api/

# Check for issues
flake8 api/
mypy api/
```

## Pull Request Process

1. **Update your fork** with the latest changes
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

2. **Make your changes** and commit them
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a pull request** against the `main` branch
   - Include a descriptive title and detailed description
   - Link any related issues
   - Explain the changes and why they're needed

5. **Address review comments** if requested

6. **Update your branch** if needed
   ```bash
   git fetch upstream
   git merge upstream/main
   git push origin feature/your-feature-name
   ```

## Testing

All new features should include tests:

1. **Write tests** for your code
   ```bash
   # Create test files in api/tests/
   touch api/tests/test_your_feature.py
   ```

2. **Run tests** to ensure everything passes
   ```bash
   pytest
   ```

3. **Check test coverage**
   ```bash
   pytest --cov=api api/tests/
   ```

4. **Run integration tests**
   ```bash
   pytest api/tests/integration/ -v
   ```

## Documentation

Documentation is essential for new features:

1. **Update README.md** if needed
2. **Add docstrings** to all new functions and classes
3. **Include examples** for API endpoints
4. **Update API documentation** annotations

Example for documenting FastAPI routes:

```python
@router.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    
    Parameters:
    - **user**: User data to create
    
    Returns:
    - **User**: Created user data
    
    Raises:
    - **HTTPException(400)**: If user with email already exists
    """
    # Implementation...
```

Thank you for contributing to FastAPI Xtrem! 