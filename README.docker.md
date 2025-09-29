# Docker Setup Guide

This guide will help you run the AI-powered Financial Document Processing System using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB of available RAM
- 10GB of available disk space

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd doc-agent
cp .env.example .env
```

### 2. Configure Environment Variables

Edit the `.env` file with your API keys:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional: LangSmith for tracing
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

### 3. Run with Docker Compose

**Production Mode:**
```bash
docker-compose up -d
```

**Development Mode (with hot reload):**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: doc_agent, password: doc_agent_password)

## Service Architecture

The Docker setup includes the following services:

### Backend (Python/FastAPI)
- **Port**: 8000
- **Health Check**: http://localhost:8000/health
- **Features**: Document processing, AI agents, vector search
- **Volumes**: 
  - `./uploads:/app/uploads` (document storage)
  - `./app:/app/app` (dev mode only)

### Frontend (Next.js)
- **Port**: 3000
- **Features**: Modern React UI, file upload, chat interface
- **Build**: Multi-stage Docker build for production

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: financial_docs
- **Credentials**: doc_agent / doc_agent_password
- **Persistence**: Docker volume `postgres_data`

### Redis (Optional Caching)
- **Port**: 6379
- **Purpose**: Session storage, caching
- **Persistence**: Docker volume `redis_data`

## Development Workflow

### Development Mode

Start in development mode with hot reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This provides:
- **Backend**: Auto-reload on code changes
- **Frontend**: Next.js development server with hot reload
- **Database**: Persistent development data

### Building Images

**Build all services:**
```bash
docker-compose build
```

**Build specific service:**
```bash
docker-compose build backend
docker-compose build frontend
```

**Force rebuild (no cache):**
```bash
docker-compose build --no-cache
```

## Data Management

### Database Initialization

The database will be automatically initialized on first run. To reset:

```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Recreate with fresh data
```

### Backup Data

**PostgreSQL Backup:**
```bash
docker-compose exec postgres pg_dump -U doc_agent financial_docs > backup.sql
```

**Restore from Backup:**
```bash
docker-compose exec -T postgres psql -U doc_agent financial_docs < backup.sql
```

### File Uploads

Documents are stored in `./uploads` directory which is mounted to the backend container.

## Troubleshooting

### Common Issues

**1. Port Conflicts**
```bash
# Check what's using the ports
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5432

# Stop conflicting services or change ports in docker-compose.yml
```

**2. Database Connection Issues**
```bash
# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**3. Backend API Not Responding**
```bash
# Check backend logs
docker-compose logs backend

# Check health endpoint
curl http://localhost:8000/health
```

**4. Frontend Build Issues**
```bash
# Clear Next.js cache and rebuild
docker-compose exec frontend rm -rf .next
docker-compose restart frontend
```

**5. Memory Issues**
```bash
# Check resource usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

### Logs and Debugging

**View all logs:**
```bash
docker-compose logs -f
```

**View specific service logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

**Execute commands in containers:**
```bash
# Backend shell
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U doc_agent financial_docs

# Frontend shell
docker-compose exec frontend sh
```

## Production Deployment

### Security Considerations

1. **Change default passwords:**
   ```yaml
   # In docker-compose.yml
   POSTGRES_PASSWORD: your_secure_password_here
   ```

2. **Use environment files:**
   ```bash
   # Create production .env file
   cp .env.example .env.production
   # Edit with production values
   ```

3. **Enable SSL/TLS:**
   - Use reverse proxy (nginx/traefik)
   - Configure HTTPS certificates
   - Update CORS settings

### Performance Optimization

1. **Resource Limits:**
   ```yaml
   # Add to services in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

2. **Health Checks:**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

### Scaling

**Scale specific services:**
```bash
docker-compose up -d --scale backend=3
```

**Use Docker Swarm for production:**
```bash
docker stack deploy -c docker-compose.yml doc-agent
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `PINECONE_API_KEY` | Pinecone API key (required) | - |
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured |
| `DEBUG` | Enable debug mode | false |
| `LANGSMITH_API_KEY` | LangSmith tracing key | - |
| `UPLOAD_DIRECTORY` | Document upload path | /app/uploads |

## Support

For issues related to Docker setup:

1. Check the troubleshooting section above
2. Review Docker and container logs
3. Ensure all required API keys are configured
4. Verify system requirements are met

For application-specific issues, refer to the main README.md file.