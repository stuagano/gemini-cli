# Gemini Enterprise Architect - Docker Deployment Guide

This directory contains optimized Docker configurations for the Gemini Enterprise Architect agents system, supporting both development and production deployments.

## 🏗️ Architecture Overview

The system consists of several containerized components:

- **Agent Server**: Python FastAPI server with all enhanced agents
- **CLI Container**: TypeScript/Node.js CLI environment  
- **Knowledge Base**: RAG system with vector database connectivity
- **Development Environment**: All-in-one container with hot reload
- **Supporting Services**: Redis, PostgreSQL, Qdrant, Nginx

## 📁 File Structure

```
docker/
├── agent-server.Dockerfile    # Multi-stage optimized agent server
├── cli.Dockerfile            # Minimal CLI container
├── dev.Dockerfile            # Development environment with hot reload
├── knowledge.Dockerfile      # RAG system with embedding models
├── configs/                  # Production configuration files
│   ├── redis.conf
│   ├── postgresql.conf
│   └── qdrant-config.yaml
├── nginx/                   # Reverse proxy configurations
│   ├── nginx.conf          # Development
│   ├── nginx.prod.conf     # Production
│   └── conf.d/
├── scripts/                 # Helper scripts for development
├── monitoring/             # Prometheus and Grafana configs
├── secrets/               # Secret files (create these)
└── init-scripts/         # Database initialization
```

## 🚀 Quick Start

### Development Environment

1. **Start the complete development stack:**
```bash
docker-compose up -d
```

2. **Start specific services:**
```bash
# Agent server only
docker-compose up agent-server

# Knowledge base only  
docker-compose up knowledge-base redis qdrant

# Development environment
docker-compose up dev-environment
```

3. **Access services:**
- Agent Server: http://localhost:8000
- Knowledge Base: http://localhost:8001
- API Documentation: http://localhost:8000/docs
- Development Proxy: http://localhost (via Nginx)

### Production Deployment

1. **Prepare secrets:**
```bash
# Create secret files
mkdir -p docker/secrets
echo "your_postgres_password" > docker/secrets/postgres_password.txt
echo "your_gemini_api_key" > docker/secrets/gemini_api_key.txt
echo "your_encryption_key" > docker/secrets/agent_encryption_key.txt
# ... add other secrets
```

2. **Configure environment:**
```bash
# Copy and edit production environment
cp docker/secrets/.env.prod.example docker/secrets/.env.prod
# Edit with your production values
```

3. **Deploy production stack:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Container Details

### Agent Server (`agent-server.Dockerfile`)

**Features:**
- Multi-stage build for optimization
- Python 3.11 with FastAPI
- All enhanced agents (Analyst, Architect, Developer, PM, PO, QA, Scout)
- Guardian system and killer demo components
- Non-root user for security
- Health checks and proper signal handling
- Resource limits and monitoring

**Build:**
```bash
docker build -f docker/agent-server.Dockerfile -t gemini/agent-server .
```

### CLI Container (`cli.Dockerfile`)

**Features:**
- Minimal Node.js 20 environment
- TypeScript compilation
- Agent client connectivity
- Development tools included
- Security hardened

**Build:**
```bash
docker build -f docker/cli.Dockerfile -t gemini/cli .
```

### Development Environment (`dev.Dockerfile`)

**Features:**
- Combined Python 3.11 + Node.js 20 environment
- Hot reload with supervisor
- Development tools (black, eslint, prettier, etc.)
- Jupyter notebooks
- Multi-service management
- Interactive debugging

**Usage:**
```bash
# Interactive shell
docker run -it -v $(pwd):/workspace gemini/dev-env

# Start all services
docker run -it -v $(pwd):/workspace gemini/dev-env all

# Start specific service
docker run -it -v $(pwd):/workspace gemini/dev-env agent-server
```

**Development Commands:**
- `dev-start-agent` - Start agent server with hot reload
- `dev-start-cli` - Start CLI development
- `dev-start-all` - Start all services with supervisor
- `dev-stop-all` - Stop all services
- `dev-logs [service]` - View logs
- `dev-status` - Check service status

### Knowledge Base (`knowledge.Dockerfile`)

**Features:**
- RAG system with embedding models
- Vector database connectivity (Qdrant, Chroma, Weaviate)
- Document processing (PDF, DOCX, etc.)
- Sentence transformers
- Redis caching integration
- Elasticsearch support

**Environment Variables:**
- `VECTOR_DB_TYPE` - qdrant/chroma/weaviate
- `EMBEDDING_MODEL` - Model name (default: all-MiniLM-L6-v2)
- `CHUNK_SIZE` - Text chunk size (default: 512)
- `CHUNK_OVERLAP` - Overlap between chunks (default: 50)

## 🔒 Security Features

### Container Security
- Non-root users (UID/GID 1000)
- Minimal base images (Alpine/slim)
- Security scanning compatible
- Read-only root filesystems where possible
- Dropped capabilities
- Network isolation

### Production Security
- TLS/SSL termination at Nginx
- Rate limiting and DDoS protection
- Security headers (HSTS, CSP, etc.)
- Secret management with Docker secrets
- Internal networks for service isolation
- Input validation and sanitization

### Network Security
- Separate networks for frontend/backend/monitoring
- Internal-only backend services
- Firewall-friendly port exposure
- WebSocket security for real-time communication

## 📊 Monitoring and Observability

### Metrics Collection
- Prometheus metrics from all services
- Custom business metrics
- Resource utilization monitoring
- Response time tracking

### Logging
- Structured JSON logging
- Centralized log collection
- Log rotation and retention
- Error tracking and alerting

### Health Checks
- Application-level health endpoints
- Database connectivity checks
- Service dependency validation
- Graceful degradation

## 🔧 Configuration Management

### Environment Variables
All services support configuration via environment variables:

**Common Variables:**
- `LOG_LEVEL` - debug/info/warning/error
- `PORT` - Service port
- `WORKERS` - Number of worker processes
- `REDIS_HOST/PORT` - Redis connection
- `POSTGRES_HOST/PORT/DB/USER` - Database connection

**Agent Server Specific:**
- `APP_ENV` - development/staging/production
- `GRACEFUL_TIMEOUT` - Graceful shutdown timeout
- `MAX_REQUESTS` - Max requests per worker
- `KNOWLEDGE_BASE_URL` - Knowledge base service URL

**Knowledge Base Specific:**
- `VECTOR_DB_HOST/PORT` - Vector database connection
- `EMBEDDING_MODEL` - Model for text embeddings
- `CHUNK_SIZE/OVERLAP` - Text processing parameters

### Secrets Management
Production deployments use Docker secrets for sensitive data:
- Database passwords
- API keys
- Encryption keys
- TLS certificates

## 🚀 Deployment Patterns

### Development
```bash
# Complete stack with hot reload
docker-compose up

# Individual service development
docker-compose up dev-environment
```

### Staging
```bash
# Production-like with debugging enabled
docker-compose -f docker-compose.prod.yml up
# Override LOG_LEVEL=debug for staging
```

### Production
```bash
# Full production stack
docker-compose -f docker-compose.prod.yml up -d

# Rolling updates
docker-compose -f docker-compose.prod.yml up -d --no-deps agent-server
```

### Scaling
```bash
# Scale specific services
docker-compose -f docker-compose.prod.yml up -d --scale agent-server=3

# Kubernetes deployment (future)
kubectl apply -f k8s/
```

## 🛠️ Maintenance

### Backup Procedures
```bash
# Database backup
docker-compose exec postgres pg_dump -U gemini gemini_enterprise > backup.sql

# Vector database backup
docker-compose exec qdrant tar -czf /backup/qdrant-$(date +%Y%m%d).tar.gz /qdrant/storage

# Redis backup
docker-compose exec redis redis-cli BGSAVE
```

### Updates and Patches
```bash
# Rebuild with latest dependencies
docker-compose build --no-cache

# Update specific service
docker-compose build agent-server
docker-compose up -d --no-deps agent-server
```

### Log Management
```bash
# View logs
docker-compose logs -f agent-server
docker-compose logs --tail=100 knowledge-base

# Clean up logs
docker system prune
```

## 🐛 Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check logs
docker-compose logs service-name

# Check health
docker-compose ps
docker inspect container-name
```

**Database Connection Issues:**
```bash
# Verify database is ready
docker-compose exec postgres pg_isready

# Check network connectivity
docker-compose exec agent-server nc -zv postgres 5432
```

**Performance Issues:**
```bash
# Check resource usage
docker stats

# Monitor service metrics
curl http://localhost:8000/api/v1/metrics
```

### Debug Mode
```bash
# Start services with debug logging
LOG_LEVEL=debug docker-compose up

# Attach to running container
docker-compose exec agent-server bash
docker-compose exec dev-environment bash
```

## 📈 Performance Optimization

### Resource Limits
Production containers include resource limits:
- Memory limits prevent OOM issues
- CPU limits ensure fair resource sharing
- Storage limits prevent disk exhaustion

### Caching Strategy
- Redis for application-level caching
- Nginx caching for static content
- Database query result caching
- Embedding vector caching

### Network Optimization
- Connection pooling
- Keep-alive connections
- Compression (gzip)
- CDN integration ready

## 🔮 Future Enhancements

- Kubernetes deployment manifests
- Helm charts for easy deployment
- Service mesh integration (Istio)
- Advanced monitoring (Jaeger tracing)
- Multi-region deployment support
- Auto-scaling based on metrics