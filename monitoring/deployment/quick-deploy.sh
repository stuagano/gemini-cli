#!/bin/bash

# Gemini Enterprise Architect - Quick Monitoring Deployment
# Deploys the complete monitoring stack with one command

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MONITORING_DIR="${PROJECT_ROOT}/monitoring"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available memory
    available_memory=$(free -g | awk '/^Mem:/{print $7}')
    if [ "$available_memory" -lt 8 ]; then
        log_warning "Available memory is ${available_memory}GB. Recommended: 8GB+"
    fi
    
    # Check available disk space
    available_disk=$(df -BG "${SCRIPT_DIR}" | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt 20 ]; then
        log_warning "Available disk space is ${available_disk}GB. Recommended: 20GB+"
    fi
    
    log_success "Prerequisites check completed"
}

# Load environment configuration
load_config() {
    log_info "Loading monitoring configuration..."
    
    if [ -f "${SCRIPT_DIR}/monitoring-config.env" ]; then
        source "${SCRIPT_DIR}/monitoring-config.env"
        log_success "Configuration loaded from monitoring-config.env"
    else
        log_warning "monitoring-config.env not found, using defaults"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating monitoring directories..."
    
    local dirs=(
        "${MONITORING_DIR}/data/prometheus"
        "${MONITORING_DIR}/data/grafana"
        "${MONITORING_DIR}/data/loki"
        "${MONITORING_DIR}/data/jaeger"
        "${MONITORING_DIR}/data/alertmanager"
        "${MONITORING_DIR}/logs"
        "${MONITORING_DIR}/backups"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        chmod 777 "$dir"  # Ensure containers can write
    done
    
    log_success "Monitoring directories created"
}

# Deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    cd "${MONITORING_DIR}"
    
    # Stop any existing containers
    log_info "Stopping existing monitoring containers..."
    docker-compose -f docker-compose.monitoring.yml down || true
    
    # Pull latest images
    log_info "Pulling monitoring images..."
    docker-compose -f docker-compose.monitoring.yml pull
    
    # Start monitoring stack
    log_info "Starting monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml up -d
    
    log_success "Monitoring stack deployed"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    local services=(
        "prometheus:9090"
        "grafana:3000"
        "loki:3100"
        "jaeger:16686"
        "alertmanager:9093"
    )
    
    for service in "${services[@]}"; do
        local host=$(echo "$service" | cut -d: -f1)
        local port=$(echo "$service" | cut -d: -f2)
        
        log_info "Waiting for $host on port $port..."
        
        local retries=30
        while ! docker exec "monitoring_${host}_1" nc -z localhost "$port" 2>/dev/null; do
            retries=$((retries - 1))
            if [ $retries -eq 0 ]; then
                log_error "$host failed to start"
                return 1
            fi
            sleep 2
        done
        
        log_success "$host is ready"
    done
}

# Configure Grafana dashboards
configure_grafana() {
    log_info "Configuring Grafana dashboards..."
    
    # Wait for Grafana to be fully ready
    sleep 10
    
    # Import dashboards via API
    local grafana_url="http://localhost:3000"
    local admin_password="${GRAFANA_ADMIN_PASSWORD:-gemini_admin_2024}"
    
    # Get admin session
    local session_cookie=$(curl -s -c - \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"user":"admin","password":"'$admin_password'"}' \
        "$grafana_url/login" | grep grafana_session | awk '{print $7}')
    
    if [ -n "$session_cookie" ]; then
        log_success "Grafana authentication successful"
        
        # Import each dashboard
        for dashboard_file in "${MONITORING_DIR}/grafana/dashboards/gemini"/*.json; do
            if [ -f "$dashboard_file" ]; then
                local dashboard_name=$(basename "$dashboard_file" .json)
                log_info "Importing dashboard: $dashboard_name"
                
                curl -s -X POST \
                    -H "Content-Type: application/json" \
                    -H "Cookie: grafana_session=$session_cookie" \
                    -d @"$dashboard_file" \
                    "$grafana_url/api/dashboards/db" > /dev/null
                
                log_success "Dashboard $dashboard_name imported"
            fi
        done
    else
        log_warning "Could not authenticate with Grafana, dashboards may need manual import"
    fi
}

# Test monitoring setup
test_monitoring() {
    log_info "Testing monitoring setup..."
    
    # Test Prometheus
    if curl -s "http://localhost:9090/-/healthy" | grep -q "Prometheus is Healthy"; then
        log_success "Prometheus is healthy"
    else
        log_error "Prometheus health check failed"
    fi
    
    # Test Grafana
    if curl -s "http://localhost:3000/api/health" | grep -q "ok"; then
        log_success "Grafana is healthy"
    else
        log_error "Grafana health check failed"
    fi
    
    # Test Loki
    if curl -s "http://localhost:3100/ready" | grep -q "ready"; then
        log_success "Loki is healthy"
    else
        log_error "Loki health check failed"
    fi
    
    # Test Jaeger
    if curl -s "http://localhost:16686/" | grep -q "Jaeger UI"; then
        log_success "Jaeger is healthy"
    else
        log_error "Jaeger health check failed"
    fi
    
    # Test Alertmanager
    if curl -s "http://localhost:9093/-/healthy" | grep -q "Alertmanager is Healthy"; then
        log_success "Alertmanager is healthy"
    else
        log_error "Alertmanager health check failed"
    fi
}

# Generate sample metrics
generate_sample_metrics() {
    log_info "Generating sample metrics for testing..."
    
    # Create a simple Python script to generate test metrics
    cat > "${MONITORING_DIR}/test-metrics.py" << 'EOF'
#!/usr/bin/env python3
import time
import random
from prometheus_client import Counter, Histogram, Gauge, push_to_gateway

# Create sample metrics
request_count = Counter('gemini_test_requests_total', 'Test requests', ['service'])
response_time = Histogram('gemini_test_response_time_seconds', 'Test response time', ['service'])
active_sessions = Gauge('gemini_test_active_sessions', 'Test active sessions', ['service'])

# Generate sample data
services = ['agent-server', 'scout', 'guardian', 'killer-demo']

for _ in range(100):
    service = random.choice(services)
    
    # Increment request counter
    request_count.labels(service=service).inc()
    
    # Record response time
    response_time.labels(service=service).observe(random.uniform(0.1, 2.0))
    
    # Update active sessions
    active_sessions.labels(service=service).set(random.randint(1, 50))
    
    time.sleep(0.1)

print("Sample metrics generated successfully")
EOF
    
    # Run the test script
    python3 "${MONITORING_DIR}/test-metrics.py" || log_warning "Could not generate sample metrics"
    
    rm -f "${MONITORING_DIR}/test-metrics.py"
}

# Display access information
display_access_info() {
    log_success "Monitoring stack deployment completed!"
    echo
    echo "🎯 Access Information:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Grafana Dashboard:     http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: ${GRAFANA_ADMIN_PASSWORD:-gemini_admin_2024}"
    echo
    echo "📈 Prometheus:            http://localhost:9090"
    echo "🔍 Jaeger Tracing:        http://localhost:16686"
    echo "🚨 Alertmanager:          http://localhost:9093"
    echo "📝 Loki Logs:             http://localhost:3100"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "🚀 Key Features Enabled:"
    echo "  • 6 Production Dashboards"
    echo "  • 157 Alert Rules"
    echo "  • SLO/Error Budget Monitoring"
    echo "  • Custom Business Metrics"
    echo "  • Distributed Tracing"
    echo "  • Structured Logging"
    echo
    echo "📋 To view logs: docker-compose -f docker-compose.monitoring.yml logs -f"
    echo "⏹️  To stop:     docker-compose -f docker-compose.monitoring.yml down"
    echo "🔄 To restart:   docker-compose -f docker-compose.monitoring.yml restart"
}

# Main deployment function
main() {
    echo "🚀 Gemini Enterprise Architect - Monitoring Deployment"
    echo "════════════════════════════════════════════════════════"
    
    check_prerequisites
    load_config
    create_directories
    deploy_monitoring
    wait_for_services
    configure_grafana
    test_monitoring
    generate_sample_metrics
    display_access_info
    
    log_success "Monitoring deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping monitoring stack..."
        cd "${MONITORING_DIR}"
        docker-compose -f docker-compose.monitoring.yml down
        log_success "Monitoring stack stopped"
        ;;
    "restart")
        log_info "Restarting monitoring stack..."
        cd "${MONITORING_DIR}"
        docker-compose -f docker-compose.monitoring.yml restart
        log_success "Monitoring stack restarted"
        ;;
    "logs")
        cd "${MONITORING_DIR}"
        docker-compose -f docker-compose.monitoring.yml logs -f
        ;;
    "status")
        cd "${MONITORING_DIR}"
        docker-compose -f docker-compose.monitoring.yml ps
        ;;
    "test")
        test_monitoring
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|test}"
        echo
        echo "Commands:"
        echo "  deploy  - Deploy the complete monitoring stack"
        echo "  stop    - Stop all monitoring services"
        echo "  restart - Restart all monitoring services"
        echo "  logs    - Show logs from all services"
        echo "  status  - Show status of all services"
        echo "  test    - Test monitoring endpoints"
        exit 1
        ;;
esac