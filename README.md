# FastAPI Xtrem

A powerful FastAPI application with advanced features: JWT authentication, refresh tokens, role-based access control, monitoring, and more.

## ✨ Features

- **🔐 Advanced Authentication**: OAuth2 with JWT, refresh token rotation, token revocation
- **🛡️ Granular Authorization**: Role and scope-based permissions system
- **👤 User Management**: Complete user lifecycle with profiles and role management
- **📊 Admin Dashboard**: User statistics and system monitoring
- **📝 Audit Logging**: Comprehensive activity tracking and security logs
- **🔍 Health Monitoring**: Prometheus metrics, Grafana dashboards, and alerting
- **🐳 Docker Support**: Complete containerization for all services
- **🧪 Testing**: Comprehensive test suite with pytest

## 📂 Project Structure

```
fastapi_xtrem/
├── api/                      # Backend FastAPI
│   ├── auth/                 # Authentication module
│   │   ├── dependencies.py   # Auth dependencies
│   │   ├── scopes.py         # Authorization scopes
│   │   └── security.py       # JWT and password hashing
│   ├── db/                   # Database module
│   │   ├── database.py       # Database configuration
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   └── routes.py         # Database routes
│   ├── logs/                 # Logging
│   │   └── logger.py         # Advanced Loguru config
│   ├── middleware/           # Middlewares
│   │   ├── error_handler.py  # Error handlers
│   │   └── logging_middleware.py # Request logging
│   ├── monitoring/           # Monitoring
│   │   ├── health.py         # Health check endpoints
│   │   └── prometheus.py     # Prometheus metrics
│   ├── tasks/                # Background tasks
│   │   └── token_cleanup.py  # Token cleanup task
│   ├── tests/                # Unit and integration tests
│   │   ├── conftest.py       # PyTest fixtures
│   │   ├── test_admin.py     # Admin routes tests
│   │   ├── test_auth.py      # Authentication tests
│   │   ├── test_health.py    # Health endpoints tests
│   │   ├── test_token_rotation.py # Token tests
│   │   └── test_users.py     # User routes tests
│   ├── users/                # User management
│   │   ├── admin_routes.py   # Admin-specific routes
│   │   ├── crud.py           # CRUD operations
│   │   ├── routes.py         # User routes
│   │   └── schemas.py        # Pydantic models
│   └── main.py               # Main FastAPI application
├── frontend/                 # Streamlit frontend (optional)
├── monitoring/               # Monitoring configs
│   ├── alertmanager/         # AlertManager configuration
│   ├── grafana/              # Grafana dashboards
│   └── prometheus/           # Prometheus configuration
├── logs/                     # Log files directory
├── docker-compose.yaml       # Main Docker Compose config
├── docker-compose-monitoring.yml # Monitoring stack
├── Dockerfile                # Backend Dockerfile
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL (optional, SQLite used by default)

### Installation

#### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastapi-xtrem.git
   cd fastapi-xtrem
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create an `.env` file with environment variables:
   ```
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   DATABASE_URL=sqlite:///./fastapi_xtrem.db
   LOG_LEVEL=INFO
   ```

5. Start the API:
   ```bash
   uvicorn api.main:app --reload
   ```

6. Access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs)

#### Docker Deployment

1. Build and start the services:
   ```bash
   docker-compose up --build
   ```

2. For the monitoring stack:
   ```bash
   docker-compose -f docker-compose-monitoring.yml up
   ```

3. Access services:
   - API: [http://localhost:8000](http://localhost:8000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Grafana: [http://localhost:3000](http://localhost:3000) (admin/admin)
   - AlertManager: [http://localhost:9093](http://localhost:9093)

## 📘 API Guide

### Authentication & Authorization

The API uses JWT tokens for authentication with refresh token rotation:

#### User Registration

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "user@example.com", "password": "strongpassword"}'
```

#### Login (Get Access & Refresh Tokens)

```bash
curl -X POST http://localhost:8000/users/token \
  -d "username=newuser&password=strongpassword" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "refresh_token": "eyJ0eXAi...",
  "expires_in": 1800
}
```

#### Using the Access Token

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJ0eXAi..."
```

#### Refreshing Tokens

```bash
curl -X POST http://localhost:8000/users/refresh-token \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ0eXAi..."}'
```

#### Revoking a Refresh Token

```bash
curl -X POST http://localhost:8000/users/revoke-token \
  -H "Authorization: Bearer eyJ0eXAi..." \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ0eXAi..."}'
```

### User Management

#### Get Current User

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJ0eXAi..."
```

#### Update User Profile

```bash
curl -X PUT http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJ0eXAi..." \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe", "bio": "Software Developer"}'
```

#### Change Password

```bash
curl -X POST http://localhost:8000/users/change-password \
  -H "Authorization: Bearer eyJ0eXAi..." \
  -H "Content-Type: application/json" \
  -d '{"current_password": "oldpassword", "new_password": "newpassword"}'
```

### Admin Operations

Admin routes require admin privileges:

#### Get User Dashboard

```bash
curl http://localhost:8000/admin/dashboard \
  -H "Authorization: Bearer eyJ0eXAi..."
```

#### List All Users

```bash
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer eyJ0eXAi..."
```

#### Get User Stats

```bash
curl http://localhost:8000/admin/stats \
  -H "Authorization: Bearer eyJ0eXAi..."
```

### Health & Monitoring

#### Basic Health Check

```bash
curl http://localhost:8000/health
```

#### Complete Health Metrics

```bash
curl http://localhost:8000/health/metrics
```

#### Prometheus Metrics

```bash
curl http://localhost:8000/metrics/prometheus
```

## 🛠️ Development

### Documentation

All project documentation is organized in the `docs/` directory:

- **User Guides**: For deployment and usage instructions
- **Reference**: Technical documentation and project information
- **Development Guides**: For contributors and developers

To browse the documentation:
1. Check the [documentation index](docs/index.md) for an overview
2. For deployment instructions, see the [Deployment Guide](docs/guides/DEPLOYMENT.md)
3. For project architecture, see the [Project Roadmap](docs/reference/Project_Roadmap.md)

To build the documentation as a website:
```bash
# Install documentation dependencies
pip install -r requirements-dev.txt

# Build documentation
mkdocs build

# Or serve documentation locally
mkdocs serve
```

### Running Tests

Run the test suite:

```bash
pytest api/tests/
```

Run with coverage:

```bash
pytest --cov=api api/tests/
```