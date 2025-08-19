#!/bin/bash

# AgentFlow Setup Script
# Multi-Agent AI System for Automated Documentation and Testing
# 
# This script will:
# 1. Check prerequisites
# 2. Set up the project structure
# 3. Configure environment variables
# 4. Start the system with Docker
# 5. Run initial setup and tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("Docker")
    else
        print_success "Docker found: $(docker --version)"
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        missing_deps+=("Docker Compose")
    else
        print_success "Docker Compose found: $(docker-compose --version)"
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_deps+=("Git")
    else
        print_success "Git found: $(git --version)"
    fi
    
    # Check if ports are available
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 8000 is already in use"
    fi
    
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 5000 is already in use"
    fi
    
    if lsof -Pi :3306 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 3306 is already in use"
    fi
    
    # Report missing dependencies
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    print_success "All prerequisites are satisfied!"
}

# Function to create project structure
create_project_structure() {
    print_status "Creating project structure..."
    
    # Create necessary directories
    mkdir -p laravel-app/storage/{app,framework,logs}
    mkdir -p laravel-app/bootstrap/cache
    mkdir -p python-agents/logs
    mkdir -p python-agents/.cache
    
    # Set proper permissions
    chmod -R 755 laravel-app/storage
    chmod -R 755 laravel-app/bootstrap/cache
    
    print_success "Project structure created!"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Environment file created from template"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    else
        print_warning ".env file already exists, skipping..."
    fi
    
    # Generate Laravel application key
    if [ -f laravel-app/artisan ]; then
        print_status "Generating Laravel application key..."
        cd laravel-app
        php artisan key:generate --no-interaction || print_warning "Could not generate Laravel key (PHP not available)"
        cd ..
    fi
    
    print_success "Environment setup completed!"
}

# Function to configure AgentFlow
configure_agentflow() {
    print_status "Configuring AgentFlow..."
    
    # Copy configuration file if it doesn't exist
    if [ ! -f .agentflow.yaml ]; then
        if [ -f config/agentflow.yaml.example ]; then
            cp config/agentflow.yaml.example .agentflow.yaml
            print_success "AgentFlow configuration created from template"
        else
            print_warning "AgentFlow configuration template not found, skipping..."
        fi
    else
        print_warning ".agentflow.yaml already exists, skipping..."
    fi
    
    print_success "AgentFlow configuration completed!"
}

# Function to start Docker services
start_services() {
    print_status "Starting Docker services..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build and start services
    print_status "Building Docker images..."
    docker-compose -f docker/docker-compose.yml build
    
    print_status "Starting services..."
    docker-compose -f docker/docker-compose.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    print_success "Docker services started!"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    local services=("mysql" "redis" "python-agents" "laravel-app")
    local healthy=true
    
    for service in "${services[@]}"; do
        if docker-compose -f docker/docker-compose.yml ps | grep -q "$service.*Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
            healthy=false
        fi
    done
    
    if [ "$healthy" = false ]; then
        print_error "Some services are not healthy. Check logs with: docker-compose -f docker/docker-compose.yml logs"
        return 1
    fi
    
    print_success "All services are healthy!"
}

# Function to run initial setup
run_initial_setup() {
    print_status "Running initial setup..."
    
    # Wait a bit more for services to be fully ready
    sleep 10
    
    # Check if we can connect to the services
    print_status "Testing service connectivity..."
    
    # Test MySQL connection
    if docker-compose -f docker/docker-compose.yml exec -T mysql mysqladmin ping -h localhost >/dev/null 2>&1; then
        print_success "MySQL connection successful"
    else
        print_warning "MySQL connection failed"
    fi
    
    # Test Python API
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        print_success "Python API connection successful"
    else
        print_warning "Python API connection failed"
    fi
    
    # Test Laravel app
    if curl -s http://localhost:8000 >/dev/null 2>&1; then
        print_success "Laravel app connection successful"
    else
        print_warning "Laravel app connection failed"
    fi
    
    print_success "Initial setup completed!"
}

# Function to display next steps
display_next_steps() {
    echo
    echo -e "${GREEN}🎉 AgentFlow setup completed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Open your browser and navigate to: http://localhost:8000"
    echo "2. Create your first project"
    echo "3. Upload some PHP files or connect a Git repository"
    echo "4. Watch the AI agents analyze your code!"
    echo
    echo -e "${BLUE}Useful commands:${NC}"
    echo "• View logs: docker-compose -f docker/docker-compose.yml logs -f"
    echo "• Stop services: docker-compose -f docker/docker-compose.yml down"
    echo "• Restart services: docker-compose -f docker/docker-compose.yml restart"
    echo "• View running containers: docker-compose -f docker/docker-compose.yml ps"
    echo
    echo -e "${BLUE}Configuration:${NC}"
    echo "• Edit .env file to customize environment variables"
    echo "• Edit .agentflow.yaml to customize AI agent behavior"
    echo "• Check docker/docker-compose.yml for service configuration"
    echo
    echo -e "${YELLOW}Important:${NC}"
    echo "• Make sure to set your OPENROUTER_API_KEY in the .env file"
    echo "• The system will not work without a valid API key"
    echo
}

# Function to cleanup on error
cleanup() {
    print_error "Setup failed! Cleaning up..."
    docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
    exit 1
}

# Set trap for cleanup
trap cleanup ERR

# Main setup function
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    AgentFlow Setup Script                    ║"
    echo "║                                                              ║"
    echo "║  Multi-Agent AI System for Automated Documentation and      ║"
    echo "║  Testing                                                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_status "Starting AgentFlow setup..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create project structure
    create_project_structure
    
    # Setup environment
    setup_environment
    
    # Configure AgentFlow
    configure_agentflow
    
    # Start services
    start_services
    
    # Check service health
    check_service_health
    
    # Run initial setup
    run_initial_setup
    
    # Display next steps
    display_next_steps
    
    print_success "AgentFlow setup completed successfully!"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --clean    Clean up existing setup before installing"
    echo "  -s, --skip     Skip certain setup steps"
    echo
    echo "Examples:"
    echo "  $0              # Full setup"
    echo "  $0 --clean      # Clean setup"
    echo "  $0 --help       # Show help"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            print_status "Cleaning up existing setup..."
            docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
            docker system prune -f 2>/dev/null || true
            print_success "Cleanup completed!"
            shift
            ;;
        -s|--skip)
            print_warning "Skip option not implemented yet"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main setup
main
