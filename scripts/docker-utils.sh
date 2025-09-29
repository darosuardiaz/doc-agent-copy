#!/bin/bash

# Docker utility scripts for AI Financial Document Processing System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_info "Please edit .env file with your API keys before continuing."
            exit 1
        else
            print_error ".env.example not found. Please create .env file manually."
            exit 1
        fi
    fi
}

# Build all Docker images
build() {
    print_info "Building Docker images..."
    check_docker
    docker-compose build --no-cache
    print_success "Docker images built successfully!"
}

# Start services in production mode
start() {
    print_info "Starting services in production mode..."
    check_docker
    check_env
    docker-compose up -d
    print_success "Services started successfully!"
    print_info "Frontend: http://localhost:3000"
    print_info "Backend API: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
}

# Start services in development mode
dev() {
    print_info "Starting services in development mode..."
    check_docker
    check_env
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    print_success "Development services started successfully!"
    print_info "Frontend: http://localhost:3000 (with hot reload)"
    print_info "Backend API: http://localhost:8000 (with hot reload)"
}

# Stop all services
stop() {
    print_info "Stopping all services..."
    check_docker
    docker-compose down
    print_success "Services stopped successfully!"
}

# Stop services and remove volumes
clean() {
    print_warning "This will stop services and remove all data (volumes)!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping services and removing volumes..."
        check_docker
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Show service logs
logs() {
    check_docker
    if [ -z "$1" ]; then
        print_info "Showing logs for all services..."
        docker-compose logs -f
    else
        print_info "Showing logs for service: $1"
        docker-compose logs -f "$1"
    fi
}

# Show service status
status() {
    check_docker
    print_info "Service status:"
    docker-compose ps
    echo
    print_info "Resource usage:"
    docker stats --no-stream
}

# Health check for all services
health() {
    check_docker
    print_info "Checking service health..."
    
    # Check backend health
    if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend API: Healthy"
    else
        print_error "Backend API: Unhealthy"
    fi
    
    # Check frontend
    if curl -f -s http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend: Healthy"
    else
        print_error "Frontend: Unhealthy"
    fi
    
    # Check database
    if docker-compose exec -T postgres pg_isready -U doc_agent >/dev/null 2>&1; then
        print_success "Database: Healthy"
    else
        print_error "Database: Unhealthy"
    fi
}

# Database operations
db_backup() {
    check_docker
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_info "Creating database backup: $backup_file"
    docker-compose exec -T postgres pg_dump -U doc_agent financial_docs > "$backup_file"
    print_success "Database backup created: $backup_file"
}

db_restore() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file: ./docker-utils.sh db_restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    check_docker
    print_warning "This will restore database from: $1"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring database from: $1"
        docker-compose exec -T postgres psql -U doc_agent financial_docs < "$1"
        print_success "Database restored successfully!"
    else
        print_info "Restore cancelled."
    fi
}

# Show help
help() {
    echo "Docker Utilities for AI Financial Document Processing System"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  build          Build all Docker images"
    echo "  start          Start services in production mode"
    echo "  dev            Start services in development mode"
    echo "  stop           Stop all services"
    echo "  clean          Stop services and remove volumes"
    echo "  logs [service] Show logs (all services or specific service)"
    echo "  status         Show service status and resource usage"
    echo "  health         Check health of all services"
    echo "  db_backup      Create database backup"
    echo "  db_restore     Restore database from backup file"
    echo "  help           Show this help message"
    echo
    echo "Examples:"
    echo "  $0 dev                    # Start in development mode"
    echo "  $0 logs backend          # Show backend logs"
    echo "  $0 db_backup             # Create database backup"
    echo "  $0 db_restore backup.sql # Restore from backup"
}

# Main command dispatcher
case "${1:-help}" in
    build)
        build
        ;;
    start)
        start
        ;;
    dev)
        dev
        ;;
    stop)
        stop
        ;;
    clean)
        clean
        ;;
    logs)
        logs "$2"
        ;;
    status)
        status
        ;;
    health)
        health
        ;;
    db_backup)
        db_backup
        ;;
    db_restore)
        db_restore "$2"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        help
        exit 1
        ;;
esac