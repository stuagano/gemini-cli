#!/bin/bash

# Gemini Enterprise Architect Monitoring Stack Deployment Script
# Deploys complete observability stack with Prometheus, Grafana, Loki, Jaeger, and OpenTelemetry

set -euo pipefail

# Configuration
ENVIRONMENT=${ENVIRONMENT:-development}
NAMESPACE=${NAMESPACE:-gemini-monitoring}
COMPOSE_FILE="docker-compose.monitoring.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p {prometheus_data,grafana_data,alertmanager_data,loki_data}
    mkdir -p grafana/provisioning/{dashboards,datasources,notifiers,plugins}
    mkdir -p grafana/provisioning/dashboards/{gemini,system,business}
    
    log_success "Directories created"
}

# Function to set up environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        cat > .env << EOF
# Environment Configuration
ENVIRONMENT=${ENVIRONMENT}

# Database Configuration
POSTGRES_PASSWORD=gemini_secure_password_2024

# Slack Integration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email Configuration (Optional)
SMTP_PASSWORD=your_smtp_password

# PagerDuty Integration (Optional)
PAGERDUTY_INTEGRATION_KEY_CRITICAL=your_pagerduty_key
PAGERDUTY_INTEGRATION_KEY_WEEKEND=your_pagerduty_weekend_key

# External Monitoring (Optional)
HONEYCOMB_API_KEY=your_honeycomb_api_key
EOF
        log_warning "Created .env file with default values. Please update with your actual configuration."
    fi
    
    # Load environment variables
    if [[ -f .env ]]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    log_success "Environment variables configured"
}

# Function to copy dashboard files
copy_dashboards() {
    log_info "Copying dashboard files..."
    
    # Copy dashboard JSON files to Grafana provisioning directory
    if [[ -d dashboards ]]; then
        cp dashboards/*.json grafana/provisioning/dashboards/gemini/ 2>/dev/null || true
    fi
    
    log_success "Dashboard files copied"
}

# Function to deploy monitoring stack
deploy_monitoring_stack() {
    log_info "Deploying monitoring stack..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f ${COMPOSE_FILE} pull
    
    # Deploy the stack
    log_info "Starting monitoring services..."
    docker-compose -f ${COMPOSE_FILE} up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log_success "Monitoring stack deployed successfully"
}

# Function to check service health
check_service_health() {
    log_info "Checking service health..."
    
    local services=(
        "prometheus:9090"
        "grafana:3000"
        "alertmanager:9093"
        "loki:3100"
        "jaeger:16686"
        "otel-collector:13133"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        
        if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1 || \
           curl -sf "http://localhost:${port}/-/healthy" > /dev/null 2>&1 || \
           curl -sf "http://localhost:${port}/ready" > /dev/null 2>&1; then
            log_success "${name} is healthy"
        else
            log_warning "${name} health check failed (this may be normal during startup)"
        fi
    done
}

# Function to configure Grafana dashboards
configure_grafana() {
    log_info "Configuring Grafana dashboards..."
    
    # Wait for Grafana to be fully ready
    local grafana_url="http://localhost:3000"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "${grafana_url}/api/health" > /dev/null 2>&1; then
            break
        fi
        log_info "Waiting for Grafana to be ready... (attempt ${attempt}/${max_attempts})"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Grafana failed to become ready within expected time"
        return 1
    fi
    
    log_success "Grafana is ready and configured"
}

# Function to display access information
display_access_info() {
    log_success "Monitoring stack deployment completed!"
    echo
    echo "🎯 Access URLs:"
    echo "=================="
    echo "• Grafana (Dashboards):     http://localhost:3000"
    echo "  └─ Username: admin"
    echo "  └─ Password: gemini_admin_2024"
    echo
    echo "• Prometheus (Metrics):     http://localhost:9090"
    echo "• Alertmanager (Alerts):    http://localhost:9093"
    echo "• Jaeger (Tracing):         http://localhost:16686"
    echo "• Loki (Logs):              http://localhost:3100"
    echo
    echo "📊 Key Dashboards:"
    echo "=================="
    echo "• Agent Performance:        Gemini Enterprise Architect > Agent Performance"
    echo "• DORA Metrics:            Gemini Enterprise Architect > DORA Metrics"
    echo "• Killer Demo Findings:    Gemini Enterprise Architect > Killer Demo Findings"
    echo "• Scout Metrics:           Gemini Enterprise Architect > Scout Metrics"
    echo "• System Health:           System Monitoring > System Health"
    echo "• Business Impact:         Business Metrics > Business Impact"
    echo
    echo "🔔 Alerting:"
    echo "============"
    echo "• Configure Slack webhook in .env file for alert notifications"
    echo "• Configure PagerDuty keys for critical alerts"
    echo "• Alert rules are pre-configured for agent performance and system health"
    echo
    echo "📝 Next Steps:"
    echo "=============="
    echo "1. Update .env file with your actual configuration values"
    echo "2. Restart the stack: docker-compose -f ${COMPOSE_FILE} restart"
    echo "3. Import additional dashboards as needed"
    echo "4. Configure alert notification channels in Grafana"
    echo "5. Set up log forwarding from your applications to Loki"
    echo
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy     Deploy the complete monitoring stack (default)"
    echo "  stop       Stop all monitoring services"
    echo "  restart    Restart all monitoring services"
    echo "  logs       Show logs from all services"
    echo "  status     Show status of all services"
    echo "  cleanup    Remove all monitoring services and data"
    echo "  help       Show this help message"
    echo
    echo "Environment Variables:"
    echo "  ENVIRONMENT    Deployment environment (default: development)"
    echo "  NAMESPACE      Kubernetes namespace (default: gemini-monitoring)"
    echo
}

# Function to stop monitoring stack
stop_monitoring() {
    log_info "Stopping monitoring stack..."
    docker-compose -f ${COMPOSE_FILE} stop
    log_success "Monitoring stack stopped"
}

# Function to restart monitoring stack
restart_monitoring() {
    log_info "Restarting monitoring stack..."
    docker-compose -f ${COMPOSE_FILE} restart
    log_success "Monitoring stack restarted"
}

# Function to show logs
show_logs() {
    log_info "Showing monitoring stack logs..."
    docker-compose -f ${COMPOSE_FILE} logs -f --tail=100
}

# Function to show status
show_status() {
    log_info "Monitoring stack status:"
    docker-compose -f ${COMPOSE_FILE} ps
}

# Function to cleanup
cleanup_monitoring() {
    log_warning "This will remove all monitoring services and data. Are you sure? (y/N)"
    read -r response
    if [[ "${response}" =~ ^[Yy]$ ]]; then
        log_info "Cleaning up monitoring stack..."
        docker-compose -f ${COMPOSE_FILE} down -v --remove-orphans
        docker volume prune -f
        log_success "Monitoring stack cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main deployment function
main_deploy() {
    log_info "Starting Gemini Enterprise Architect Monitoring Stack Deployment"
    echo
    
    check_prerequisites
    create_directories
    setup_environment
    copy_dashboards
    deploy_monitoring_stack
    configure_grafana
    display_access_info
}

# Main script logic
main() {
    local command=${1:-deploy}
    
    case "${command}" in
        deploy)
            main_deploy
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            restart_monitoring
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup_monitoring
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: ${command}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"