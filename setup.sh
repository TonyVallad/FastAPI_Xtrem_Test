#!/bin/bash

# FastAPI Xtrem Setup Script
# This script helps set up the development environment

set -e  # Exit on any error

# Function to display messages
print_message() {
    echo -e "\n\033[1;34m$1\033[0m"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or newer."
    exit 1
fi

# Create virtual environment
print_message "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
print_message "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
print_message "Installing dependencies..."
if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
else
    pip install -r requirements.txt
fi

# Create logs directory
print_message "Creating logs directory..."
mkdir -p logs

# Create data directory for SQLite
print_message "Creating data directory..."
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_message "Creating .env file from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please update the .env file with your configuration."
    else
        echo "SECRET_KEY=change_this_in_production" > .env
        echo "DATABASE_URL=sqlite:///./data/fastapi_xtrem.db" >> .env
        echo "LOG_LEVEL=DEBUG" >> .env
        echo "Please update the .env file with your configuration."
    fi
fi

# Set up pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    print_message "Setting up pre-commit hooks..."
    pre-commit install
fi

# Run tests to verify setup
print_message "Running tests to verify setup..."
pytest api/tests/ -v

print_message "Setup complete! 🚀"
print_message "To start the development server, run:"
echo "source .venv/bin/activate"
echo "uvicorn api.main:app --reload"

print_message "To start with Docker, run:"
echo "docker-compose up -d"

print_message "Visit http://localhost:8000/docs for API documentation." 