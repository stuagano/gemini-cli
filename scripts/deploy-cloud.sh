#!/bin/bash
set -euo pipefail

# Gemini Enterprise Architect - Cloud Deployment Script
# This script deploys the complete infrastructure and application to GCP

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform/gcp"
K8S_DIR="$PROJECT_ROOT/k8s"

# Default values
ENVIRONMENT="dev"
PROJECT_ID=""
REGION="us-central1"
ZONE="us-central1-a"
DB_PASSWORD=""
SKIP_TERRAFORM="false"
SKIP_K8S="false"
DRY_RUN="false"

# Print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Gemini Enterprise Architect to Google Cloud Platform

OPTIONS:
    -p, --project-id        GCP Project ID (required)
    -e, --environment       Environment (dev|staging|production) [default: dev]
    -r, --region           GCP Region [default: us-central1]
    -z, --zone             GCP Zone [default: us-central1-a]
    --db-password          Database password (required)
    --skip-terraform       Skip Terraform deployment
    --skip-k8s            Skip Kubernetes deployment
    --dry-run             Show what would be deployed without actually deploying
    -h, --help            Show this help message

EXAMPLES:
    # Deploy to dev environment
    $0 -p my-project-id -e dev --db-password mypassword

    # Deploy to production
    $0 -p my-project-id -e production --db-password securepassword

    # Only deploy Kubernetes (assuming infrastructure exists)
    $0 -p my-project-id --skip-terraform

    # Dry run to see what would be deployed
    $0 -p my-project-id --dry-run

EOF
}

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

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -z|--zone)
                ZONE="$2"
                shift 2
                ;;
            --db-password)
                DB_PASSWORD="$2"
                shift 2
                ;;
            --skip-terraform)
                SKIP_TERRAFORM="true"
                shift
                ;;
            --skip-k8s)
                SKIP_K8S="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate arguments
validate_args() {
    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Project ID is required"
        usage
        exit 1
    fi

    if [[ -z "$DB_PASSWORD" && "$DRY_RUN" != "true" ]]; then
        log_error "Database password is required"
        usage
        exit 1
    fi

    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
        log_error "Environment must be one of: dev, staging, production"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required tools
    local tools=("gcloud" "terraform" "kubectl" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done

    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Please authenticate with gcloud: gcloud auth login"
        exit 1
    fi

    # Set project
    log_info "Setting GCP project to $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"

    # Enable required APIs (if not already enabled)
    log_info "Ensuring required APIs are enabled..."
    gcloud services enable \
        container.googleapis.com \
        compute.googleapis.com \
        aiplatform.googleapis.com \
        cloudbuild.googleapis.com \
        sqladmin.googleapis.com \
        redis.googleapis.com \
        secretmanager.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com \
        artifactregistry.googleapis.com

    log_success "Prerequisites check completed"
}

# Initialize Terraform
init_terraform() {
    if [[ "$SKIP_TERRAFORM" == "true" ]]; then
        log_info "Skipping Terraform initialization"
        return
    fi

    log_info "Initializing Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Create terraform.tfvars file
    cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
environment = "$ENVIRONMENT"
region = "$REGION"
zone = "$ZONE"
db_password = "$DB_PASSWORD"
terraform_state_bucket = "$PROJECT_ID-terraform-state"
name_prefix = "gemini-enterprise-$ENVIRONMENT"
EOF

    # Initialize Terraform
    terraform init
    
    log_success "Terraform initialized"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    if [[ "$SKIP_TERRAFORM" == "true" ]]; then
        log_info "Skipping infrastructure deployment"
        return
    fi

    log_info "Deploying infrastructure with Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - showing Terraform plan..."
        terraform plan
        return
    fi

    # Plan
    terraform plan -out=tfplan
    
    # Apply with confirmation
    echo
    read -p "Do you want to apply this Terraform plan? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        terraform apply tfplan
        log_success "Infrastructure deployment completed"
    else
        log_warning "Infrastructure deployment cancelled"
        exit 1
    fi
}

# Get infrastructure outputs
get_infrastructure_outputs() {
    if [[ "$SKIP_TERRAFORM" == "true" ]]; then
        log_warning "Terraform skipped - using placeholder values"
        # Set placeholder values
        CLUSTER_NAME="gemini-enterprise-$ENVIRONMENT-gke"
        POSTGRES_IP="10.0.0.2"
        REDIS_HOST="10.0.0.3"
        VERTEX_AI_ENDPOINT="projects/$PROJECT_ID/locations/$REGION/endpoints/123456"
        return
    fi

    log_info "Getting infrastructure outputs..."
    
    cd "$TERRAFORM_DIR"
    
    # Get Terraform outputs
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    POSTGRES_IP=$(terraform output -raw database_private_ip)
    REDIS_HOST=$(terraform output -raw redis_host)
    VERTEX_AI_ENDPOINT=$(terraform output -raw vertex_ai_endpoint_name)
    ARTIFACT_REGISTRY_URL=$(terraform output -raw artifact_registry_url)
    
    log_success "Infrastructure outputs retrieved"
}

# Configure kubectl
configure_kubectl() {
    if [[ "$SKIP_K8S" == "true" ]]; then
        log_info "Skipping kubectl configuration"
        return
    fi

    log_info "Configuring kubectl..."
    
    gcloud container clusters get-credentials "$CLUSTER_NAME" \
        --region "$REGION" \
        --project "$PROJECT_ID"
    
    log_success "kubectl configured"
}

# Deploy application to Kubernetes
deploy_application() {
    if [[ "$SKIP_K8S" == "true" ]]; then
        log_info "Skipping application deployment"
        return
    fi

    log_info "Deploying application to Kubernetes..."
    
    # Create temporary directory for processed manifests
    local temp_dir=$(mktemp -d)
    local processed_dir="$temp_dir/k8s"
    mkdir -p "$processed_dir"
    
    # Process Kubernetes manifests (substitute variables)
    for file in "$K8S_DIR"/*.yaml; do
        local filename=$(basename "$file")
        sed -e "s/\${PROJECT_ID}/$PROJECT_ID/g" \
            -e "s/\${ENVIRONMENT}/$ENVIRONMENT/g" \
            -e "s/\${REGION}/$REGION/g" \
            -e "s/\${POSTGRES_PRIVATE_IP}/$POSTGRES_IP/g" \
            -e "s/\${REDIS_HOST}/$REDIS_HOST/g" \
            -e "s/\${VERTEX_AI_ENDPOINT}/$VERTEX_AI_ENDPOINT/g" \
            "$file" > "$processed_dir/$filename"
    done
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - showing Kubernetes manifests..."
        kubectl diff -f "$processed_dir/" || true
        rm -rf "$temp_dir"
        return
    fi

    # Apply manifests
    kubectl apply -f "$processed_dir/"
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/gemini-agent-server -n gemini
    
    # Clean up temporary directory
    rm -rf "$temp_dir"
    
    log_success "Application deployment completed"
}

# Build and push container images
build_and_push_images() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - skipping image build"
        return
    fi

    log_info "Building and pushing container images..."
    
    cd "$PROJECT_ROOT"
    
    # Configure Docker for Artifact Registry
    gcloud auth configure-docker "$REGION-docker.pkg.dev"
    
    # Build agent server image
    local image_tag="$ARTIFACT_REGISTRY_URL/gemini-agent:$(git rev-parse --short HEAD)"
    
    docker build -t "$image_tag" .
    docker push "$image_tag"
    
    # Update deployment with new image
    kubectl set image deployment/gemini-agent-server \
        agent-server="$image_tag" \
        -n gemini
    
    log_success "Container images built and pushed"
}

# Verify deployment
verify_deployment() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - skipping deployment verification"
        return
    fi

    log_info "Verifying deployment..."
    
    # Check pod status
    kubectl get pods -n gemini
    
    # Check services
    kubectl get services -n gemini
    
    # Get external IP
    local external_ip=""
    local attempts=0
    while [[ -z "$external_ip" && $attempts -lt 30 ]]; do
        external_ip=$(kubectl get service gemini-agent-server -n gemini -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [[ -z "$external_ip" ]]; then
            log_info "Waiting for external IP... (attempt $((attempts + 1))/30)"
            sleep 10
            ((attempts++))
        fi
    done
    
    if [[ -n "$external_ip" ]]; then
        log_success "Deployment verified! External IP: $external_ip"
        log_info "API Documentation: http://$external_ip/docs"
        log_info "Health Check: http://$external_ip/api/v1/health"
    else
        log_warning "External IP not yet available. Check 'kubectl get services -n gemini' later."
    fi
}

# Run post-deployment tests
run_tests() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run - skipping tests"
        return
    fi

    log_info "Running post-deployment tests..."
    
    # Wait a bit for services to be fully ready
    sleep 30
    
    # Get service endpoint
    local service_ip=$(kubectl get service gemini-agent-server -n gemini -o jsonpath='{.spec.clusterIP}')
    
    # Test health endpoint
    if kubectl run test-pod --rm -i --restart=Never --image=curlimages/curl -- \
        curl -f "http://$service_ip/api/v1/health"; then
        log_success "Health check passed"
    else
        log_warning "Health check failed"
    fi
    
    # Test DORA metrics endpoint
    if kubectl run test-pod --rm -i --restart=Never --image=curlimages/curl -- \
        curl -f "http://$service_ip/api/v1/dora/metrics/gemini-cli"; then
        log_success "DORA metrics endpoint accessible"
    else
        log_warning "DORA metrics endpoint not accessible"
    fi
}

# Generate deployment summary
generate_summary() {
    log_info "Generating deployment summary..."
    
    cat << EOF

${GREEN}========================================
    DEPLOYMENT SUMMARY
========================================${NC}

Environment: $ENVIRONMENT
Project ID: $PROJECT_ID
Region: $REGION

Infrastructure:
- GKE Cluster: $CLUSTER_NAME
- PostgreSQL: $POSTGRES_IP
- Redis: $REDIS_HOST
- Vertex AI: $VERTEX_AI_ENDPOINT

Application Status:
$(kubectl get deployments -n gemini -o wide 2>/dev/null || echo "  Not deployed")

Next Steps:
1. Monitor deployment: kubectl get pods -n gemini
2. Check logs: kubectl logs -f deployment/gemini-agent-server -n gemini
3. Access API docs: kubectl port-forward service/gemini-agent-server 8080:80 -n gemini
   Then visit: http://localhost:8080/docs
4. Set up monitoring dashboards
5. Configure domain and SSL certificates

Useful Commands:
- View pods: kubectl get pods -n gemini
- Check logs: kubectl logs -f deployment/gemini-agent-server -n gemini
- Port forward: kubectl port-forward service/gemini-agent-server 8080:80 -n gemini
- Delete deployment: kubectl delete namespace gemini

EOF
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
        log_info "Check the logs above for details"
    fi
    exit $exit_code
}

# Main deployment function
main() {
    log_info "Starting Gemini Enterprise Architect deployment..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Parse and validate arguments
    parse_args "$@"
    validate_args
    
    # Check prerequisites
    check_prerequisites
    
    # Initialize and deploy infrastructure
    init_terraform
    deploy_infrastructure
    get_infrastructure_outputs
    
    # Deploy application
    configure_kubectl
    build_and_push_images
    deploy_application
    
    # Verify and test
    verify_deployment
    run_tests
    
    # Generate summary
    generate_summary
    
    log_success "Deployment completed successfully!"
}

# Run main function with all arguments
main "$@"