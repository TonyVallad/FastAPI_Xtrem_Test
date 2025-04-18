FROM python:3.11-slim as python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Build stage for dependencies
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry - dependency management
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project files
WORKDIR $PYSETUP_PATH
COPY requirements.txt ./

# Create virtualenv and install dependencies
RUN python -m venv $VENV_PATH \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Production stage
FROM python-base as production

# Create a non-root user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Create application directory
WORKDIR /app

# Copy Python dependencies and project files
COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --chown=appuser:appuser . .

# Create log and data directories and set permissions
RUN mkdir -p logs data \
    && chown -R appuser:appuser logs data

# Set user
USER appuser

# Expose API port
EXPOSE 8000

# Run the application with proper settings
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"] 