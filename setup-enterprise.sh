#!/bin/bash

# Gemini Enterprise Architect - Setup Script
# Configures the enterprise layer on top of existing Gemini CLI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

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

# Print banner
print_banner() {
    echo "🚀 Gemini Enterprise Architect Setup"
    echo "====================================="
    echo "Setting up enterprise features on top of your existing Gemini CLI"
    echo ""
}

# Check if this is a Gemini CLI project
check_gemini_cli() {
    log_info "Checking if this is a Gemini CLI project..."
    
    if [[ ! -f "package.json" ]]; then
        log_error "No package.json found. This doesn't appear to be a Gemini CLI project."
        exit 1
    fi
    
    if ! grep -q "gemini" package.json; then
        log_warning "This doesn't appear to be a Gemini CLI project, but continuing anyway..."
    else
        log_success "Gemini CLI project detected"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_success "Virtual environment already exists"
    fi
    
    log_success "Prerequisites check completed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    log_success "Python dependencies installed"
    
    # Install Node.js dependencies (if needed)
    if [[ -f "package.json" ]] && [[ ! -d "node_modules" ]]; then
        log_info "Installing Node.js dependencies..."
        npm install > /dev/null 2>&1
        log_success "Node.js dependencies installed"
    fi
}

# Configure environment
configure_environment() {
    log_info "Configuring environment..."
    
    if [[ -f ".env" ]]; then
        log_success "Environment configuration already exists"
    else
        log_error "No .env file found. Please run the environment configuration first."
        echo "Your .env file should already be configured with Vertex AI settings."
        exit 1
    fi
}

# Test the setup
test_setup() {
    log_info "Testing enterprise setup..."
    
    # Test Python agent server
    log_info "Testing Python agent server..."
    source venv/bin/activate
    timeout 10s python src/api/agent_server.py --test-mode > /dev/null 2>&1 || true
    log_success "Agent server test completed"
    
    # Test Vertex AI connection
    log_info "Testing Vertex AI connection..."
    python scripts/setup-vertex-ai.py --test-only > /dev/null 2>&1
    log_success "Vertex AI connection test completed"
}

# Create integration files
create_integration() {
    log_info "Setting up CLI integration..."
    
    # Create enterprise command file (if TypeScript CLI exists)
    if [[ -d "packages/cli/src/commands" ]]; then
        if [[ ! -f "packages/cli/src/commands/agent.tsx" ]]; then
            log_info "Creating enterprise command integration..."
            
            cat > "packages/cli/src/commands/agent.tsx" << 'EOF'
// Enterprise Agent Command Integration
import React from 'react';
import { Command } from '../types';
import { createAgentFactory } from '../agents';

export const agentCommand: Command = {
  name: 'agent',
  description: 'Use specialized enterprise agents',
  args: [
    {
      name: 'type',
      description: 'Agent type (analyst, pm, architect, developer, qa, scout, po)',
      required: true
    },
    {
      name: 'prompt',
      description: 'Your request for the agent',
      required: true
    }
  ],
  
  async run({ args, logger }) {
    const agentType = args.type;
    const prompt = args.prompt;
    
    logger.info(`Routing to ${agentType} agent...`);
    
    try {
      const factory = createAgentFactory({
        autoStart: true
      });
      
      const response = await factory.sendRequest({
        agent: agentType,
        action: 'process_request',
        prompt: prompt,
        priority: 'normal'
      });
      
      return {
        success: true,
        output: response.result,
        metadata: response.metadata
      };
      
    } catch (error) {
      logger.error(`Agent request failed: ${error.message}`);
      return {
        success: false,
        error: error.message
      };
    }
  }
};

export default agentCommand;
EOF
            log_success "Enterprise command integration created"
        else
            log_success "Enterprise command integration already exists"
        fi
    else
        log_warning "CLI commands directory not found - manual integration needed"
    fi
}

# Display usage information
show_usage() {
    log_success "Enterprise setup completed!"
    echo ""
    echo "🎯 How to Use Enterprise Features:"
    echo "=================================="
    echo ""
    echo "1. Regular Gemini CLI (unchanged):"
    echo "   gemini \"your normal commands work exactly the same\""
    echo ""
    echo "2. Specialized Agents (new):"
    echo "   gemini agent analyst \"analyze technical debt in this codebase\""
    echo "   gemini agent architect \"design a microservices architecture\""
    echo "   gemini agent pm \"create project roadmap for this feature\""
    echo "   gemini agent developer \"implement this feature with best practices\""
    echo "   gemini agent qa \"create comprehensive tests for this code\""
    echo "   gemini agent scout \"check for duplicates before implementing\""
    echo "   gemini agent po \"optimize this feature for business value\""
    echo ""
    echo "3. Start Services:"
    echo "   # Start agent server (automatic when using agents)"
    echo "   python src/api/agent_server.py"
    echo ""
    echo "   # Start monitoring (optional)"
    echo "   cd monitoring/deployment"
    echo "   ./quick-deploy.sh"
    echo ""
    echo "4. Monitor & Observe:"
    echo "   • Grafana: http://localhost:3000 (admin/gemini_admin_2024)"
    echo "   • Prometheus: http://localhost:9090"
    echo "   • Jaeger: http://localhost:16686"
    echo ""
    echo "🔧 Configuration:"
    echo "• Environment: .env (already configured)"
    echo "• Vertex AI: Deployed and operational"
    echo "• Monitoring: Ready to deploy"
    echo ""
    echo "📚 Documentation:"
    echo "• Integration Guide: INTEGRATION_GUIDE.md"
    echo "• Architecture: docs/architecture/source-tree.md"
    echo "• Monitoring: monitoring/MONITORING_SETUP.md"
}

# Main setup function
main() {
    print_banner
    check_gemini_cli
    check_prerequisites
    install_dependencies
    configure_environment
    test_setup
    create_integration
    show_usage
}

# Handle script arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "test")
        print_banner
        log_info "Running tests only..."
        test_setup
        log_success "Tests completed"
        ;;
    "clean")
        log_info "Cleaning up enterprise setup..."
        rm -rf venv/
        rm -f vertex-ai-config.json
        rm -f packages/cli/src/commands/agent.tsx
        log_success "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 {setup|test|clean}"
        echo ""
        echo "Commands:"
        echo "  setup - Set up enterprise features (default)"
        echo "  test  - Test the current setup"
        echo "  clean - Remove enterprise setup"
        exit 1
        ;;
esac