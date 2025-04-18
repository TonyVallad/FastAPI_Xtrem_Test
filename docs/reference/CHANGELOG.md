# Changelog

All notable changes to the FastAPI Xtrem project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-04-15

### Added
- Complete monitoring system with Prometheus, Grafana, and AlertManager
- Structured logging with Loguru with multiple output formats
- Health check endpoints for service monitoring
- System metrics collection and visualization
- Alerting system for critical events
- Custom middleware for detailed request logging
- Dashboard templates for Grafana
- Database query performance monitoring
- PostgreSQL support in Docker Compose
- Production deployment guide
- Contributor guidelines
- Timezone handling documentation with best practices

### Changed
- Enhanced security in Dockerfile with multi-stage builds
- Improved Docker Compose configuration
- Updated README with comprehensive documentation
- Optimized database operations with metrics
- Better environment variable management
- Improved error handling and reporting
- Fixed datetime timezone inconsistencies

### Fixed
- Fixed token refresh flow edge cases
- Improved error handling in monitoring middleware
- Fixed database connection issues in health checks
- Resolved timezone comparison issues in token validation

## [0.3.0] - 2025-03-15

### Added
- Secure refresh token rotation system
- Token revocation capabilities
- Background task for cleaning expired tokens
- Comprehensive test suite for token workflows
- IP tracking for token issuance
- Automatic token cleanup

### Changed
- Extended JWT token security
- Improved token storage and lifecycle
- Enhanced user authentication flow
- Updated documentation with token security practices

## [0.2.0] - 2025-03-01

### Added
- Scope-based authorization system
- Role-to-scope mapping for fine-grained permissions
- Enhanced JWT tokens with scope claims
- Route protection based on required scopes
- Tests for scope validation
- Admin-specific routes with scope requirements

### Changed
- Improved user role management
- Enhanced security middleware
- Better documentation of security features

## [0.1.0] - 2025-02-15

### Added
- Initial project structure and setup
- User authentication with JWT
- Basic user management (create, read, update, delete)
- Role-based access control
- Admin dashboard
- Activity logging
- SQLAlchemy ORM with SQLite
- Docker and Docker Compose support
- Basic test suite 