# Deployment Guide

This guide provides instructions for deploying FastAPI Xtrem in various production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Manual Deployment](#manual-deployment)
- [Configuration](#configuration)
- [Security Considerations](#security-considerations)
- [Monitoring Setup](#monitoring-setup)

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL database (recommended for production)
- Domain name and SSL certificate (for HTTPS)
- Sufficient server resources (min. 1 CPU, 2GB RAM)

## Docker Deployment

The easiest way to deploy FastAPI Xtrem is using Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastapi-xtrem.git
   cd fastapi-xtrem
   ```

2. Create and configure the `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your production settings
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Start the monitoring stack (optional):
   ```bash
   docker-compose -f docker-compose-monitoring.yml up -d
   ```

### Docker with Traefik Reverse Proxy

For a production setup with Traefik:

1. Add the following to your existing `docker-compose.yaml`:
   ```yaml
   services:
     api:
       # ... existing config ...
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.fastapi.rule=Host(`api.yourdomain.com`)"
         - "traefik.http.routers.fastapi.entrypoints=websecure"
         - "traefik.http.routers.fastapi.tls.certresolver=myresolver"
   
     traefik:
       image: traefik:v2.9
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
         - ./traefik:/etc/traefik
       networks:
         - app-network
   ```

2. Configure Traefik for automatic SSL:
   ```bash
   mkdir -p traefik
   cat > traefik/traefik.yml << EOF
   api:
     dashboard: true
   
   entryPoints:
     web:
       address: ":80"
       http:
         redirections:
           entryPoint:
             to: websecure
             scheme: https
   
     websecure:
       address: ":443"
   
   providers:
     docker:
       endpoint: "unix:///var/run/docker.sock"
       exposedByDefault: false
   
   certificatesResolvers:
     myresolver:
       acme:
         email: your-email@example.com
         storage: /etc/traefik/acme.json
         httpChallenge:
           entryPoint: web
   EOF
   
   touch traefik/acme.json
   chmod 600 traefik/acme.json
   ```

## Kubernetes Deployment

For larger scale deployments, you can use Kubernetes:

1. Create Kubernetes manifests:
   ```bash
   mkdir -p k8s
   ```

2. Create a deployment YAML (`k8s/deployment.yaml`):
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: fastapi-xtrem
     labels:
       app: fastapi-xtrem
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: fastapi-xtrem
     template:
       metadata:
         labels:
           app: fastapi-xtrem
       spec:
         containers:
         - name: api
           image: your-registry/fastapi-xtrem:latest
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: fastapi-xtrem-secrets
                 key: database-url
           # Add other environment variables from secrets/configmaps
           livenessProbe:
             httpGet:
               path: /health/liveness
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health/readiness
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 10
   ```

3. Create a service YAML (`k8s/service.yaml`):
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: fastapi-xtrem
   spec:
     selector:
       app: fastapi-xtrem
     ports:
     - port: 80
       targetPort: 8000
     type: ClusterIP
   ```

4. Create an ingress YAML (`k8s/ingress.yaml`):
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: fastapi-xtrem
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt-prod
   spec:
     tls:
     - hosts:
       - api.yourdomain.com
       secretName: fastapi-xtrem-tls
     rules:
     - host: api.yourdomain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: fastapi-xtrem
               port:
                 number: 80
   ```

5. Deploy to Kubernetes:
   ```bash
   kubectl apply -f k8s/
   ```

## Manual Deployment

For manual deployment on a server:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastapi-xtrem.git
   cd fastapi-xtrem
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create and configure the `.env` file.

5. Set up a PostgreSQL database.

6. Run the application with Gunicorn:
   ```bash
   pip install gunicorn uvicorn
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

7. Set up Nginx as a reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

8. Set up SSL with Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d api.yourdomain.com
   ```

9. Set up systemd service:
   ```
   [Unit]
   Description=FastAPI Xtrem Service
   After=network.target
   
   [Service]
   User=fastapi
   Group=fastapi
   WorkingDirectory=/path/to/fastapi-xtrem
   Environment="PATH=/path/to/fastapi-xtrem/.venv/bin"
   EnvironmentFile=/path/to/fastapi-xtrem/.env
   ExecStart=/path/to/fastapi-xtrem/.venv/bin/gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   Restart=on-failure
   RestartSec=5s
   
   [Install]
   WantedBy=multi-user.target
   ```

## Configuration

### Environment Variables

Key environment variables for production:

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | JWT signing key (must be secure) | None |
| DATABASE_URL | Database connection string | sqlite:///./fastapi_xtrem.db |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiration | 7 |
| LOG_LEVEL | Logging level | INFO |
| API_HOST | API host | 0.0.0.0 |
| API_PORT | API port | 8000 |

### Database Migration

If migrating from SQLite to PostgreSQL:

1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE fastapi_xtrem;
   CREATE USER fastapi_user WITH ENCRYPTED PASSWORD 'securepassword';
   GRANT ALL PRIVILEGES ON DATABASE fastapi_xtrem TO fastapi_user;
   ```

2. Update the DATABASE_URL:
   ```
   DATABASE_URL=postgresql://fastapi_user:securepassword@localhost/fastapi_xtrem
   ```

## Security Considerations

For production deployment, ensure:

1. **Use secure passwords** for all services
2. **Generate a strong SECRET_KEY**:
   ```bash
   openssl rand -hex 32
   ```
3. **Always enable HTTPS** in production
4. **Restrict access** to admin endpoints
5. **Use separate database credentials** for production
6. **Regularly update dependencies**:
   ```bash
   pip list --outdated
   ```
7. **Enable firewall** and only expose necessary ports
8. **Set up proper logging** and monitoring
9. **Implement regular backups**

## Monitoring Setup

The monitoring stack includes:

- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **AlertManager**: For alerts

Access these services at:
- Grafana: https://your-domain.com:3000 (default admin/admin)
- Prometheus: https://your-domain.com:9090
- AlertManager: https://your-domain.com:9093

For comprehensive monitoring, also consider:

1. **Log aggregation** with ELK or Loki
2. **Distributed tracing** with Jaeger or Zipkin 
3. **Uptime monitoring** with Uptime Robot or Better Uptime 