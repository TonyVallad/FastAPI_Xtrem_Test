# FastAPI Xtrem Setup Script for Windows
# This script helps set up the development environment on Windows

# Function to display messages
function Print-Message {
    param ([string]$message)
    Write-Host "`n$message" -ForegroundColor Blue
}

# Check if Python is installed
try {
    $pythonVersion = python --version
    Print-Message "Found $pythonVersion"
} catch {
    Write-Host "Python not found. Please install Python 3.8 or newer." -ForegroundColor Red
    exit 1
}

# Create and activate virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv .venv
..\.venv\Scripts\Activate.ps1

# Upgrade pip
Print-Message "Upgrading pip..."
python -m pip install --upgrade pip

# Install development dependencies
Print-Message "Installing dependencies..."
if (Test-Path "requirements-dev.txt") {
    pip install -r requirements-dev.txt
} else {
    pip install -r requirements.txt
}

# Create logs directory
Print-Message "Creating logs directory..."
New-Item -ItemType Directory -Force -Path "logs"

# Create data directory for SQLite
Print-Message "Creating data directory..."
New-Item -ItemType Directory -Force -Path "data"

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Print-Message "Creating .env file from example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" -Destination ".env"
        Write-Host "Please update the .env file with your configuration." -ForegroundColor Yellow
    } else {
        @"
SECRET_KEY=change_this_in_production
DATABASE_URL=sqlite:///./data/fastapi_xtrem.db
LOG_LEVEL=DEBUG
"@ | Out-File -FilePath ".env" -Encoding utf8
        Write-Host "Please update the .env file with your configuration." -ForegroundColor Yellow
    }
}

# Set up pre-commit hooks if available
try {
    $preCommitVersion = pre-commit --version
    Print-Message "Setting up pre-commit hooks..."
    pre-commit install
} catch {
    Write-Host "pre-commit not found. Skipping pre-commit setup."
}

# Run tests to verify setup
Print-Message "Running tests to verify setup..."
pytest api/tests/ -v

Print-Message "Setup complete! 🚀"
Print-Message "To start the development server, run:"
Write-Host "..\.venv\Scripts\Activate.ps1"
Write-Host "uvicorn api.main:app --reload"

Print-Message "To start with Docker, run:"
Write-Host "docker-compose up -d"

Print-Message "Visit http://localhost:8000/docs for API documentation."

Write-Host "Activate the virtual environment with:" -ForegroundColor Green
Write-Host "..\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow 