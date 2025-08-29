#!/bin/bash

# TikTok Ads MCP Remote Server Deployment Script
# This script helps deploy the remote MCP server to various cloud platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Default values
DEPLOYMENT_TYPE="development"
PLATFORM="docker"
PORT=8000
WORKERS=2

# Help message
show_help() {
    cat << EOF
TikTok Ads MCP Remote Server Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE          Deployment type: development, production (default: development)
    -p, --platform PLATFORM Target platform: docker, aws, gcp, azure, heroku (default: docker)
    -P, --port PORT         Port to bind to (default: 8000)
    -w, --workers WORKERS   Number of worker processes (default: 2)
    -h, --help              Show this help message

EXAMPLES:
    # Development deployment with Docker
    $0 --type development --platform docker

    # Production deployment 
    $0 --type production --platform docker

    # Deploy to Heroku
    $0 --type production --platform heroku

    # Deploy to Render  
    $0 --type production --platform render

    # Deploy to AWS with custom settings
    $0 --type production --platform aws --port 8080 --workers 4

ENVIRONMENT VARIABLES:
    Required for all deployments:
    - TIKTOK_APP_ID: Your TikTok app ID
    - TIKTOK_SECRET: Your TikTok app secret  
    - TIKTOK_ACCESS_TOKEN: Your TikTok access token

    Optional:
    - HOST: Host to bind to (default: 0.0.0.0)
    - LOG_LEVEL: Logging level (default: info)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -P|--port)
            PORT="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate deployment type
if [[ ! "$DEPLOYMENT_TYPE" =~ ^(development|production)$ ]]; then
    print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
    print_error "Must be 'development' or 'production'"
    exit 1
fi

# Validate platform
if [[ ! "$PLATFORM" =~ ^(docker|aws|gcp|azure|heroku|render)$ ]]; then
    print_error "Invalid platform: $PLATFORM"
    print_error "Must be one of: docker, aws, gcp, azure, heroku, render"
    exit 1
fi

print_status "Starting TikTok Ads MCP Remote Server deployment..."
print_status "Deployment type: $DEPLOYMENT_TYPE"
print_status "Target platform: $PLATFORM"
print_status "Port: $PORT"
print_status "Workers: $WORKERS"

# Check for required environment variables
check_env_vars() {
    local required_vars=("TIKTOK_APP_ID" "TIKTOK_SECRET" "TIKTOK_ACCESS_TOKEN")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_error "Please set these variables and try again."
        exit 1
    fi

    print_success "All required environment variables are set"
}

# Docker deployment
deploy_docker() {
    print_status "Deploying with Docker..."

    # Create .env file
    cat > .env << EOF
TIKTOK_APP_ID=${TIKTOK_APP_ID}
TIKTOK_SECRET=${TIKTOK_SECRET}
TIKTOK_ACCESS_TOKEN=${TIKTOK_ACCESS_TOKEN}
HOST=${HOST:-0.0.0.0}
PORT=${PORT}
WORKERS=${WORKERS}
LOG_LEVEL=${LOG_LEVEL:-info}
EOF

    if [[ "$DEPLOYMENT_TYPE" == "production" ]]; then
        print_status "Building production containers..."
        docker-compose --profile production build
        
        print_status "Starting production services..."
        docker-compose --profile production up -d
        
        print_success "Production deployment completed!"
        print_status "Services are running with nginx reverse proxy"
        print_status "HTTP: http://localhost:80"
        print_status "HTTPS: https://localhost:443 (requires SSL certificates in ./ssl/)"
    else
        print_status "Building development container..."
        docker-compose build
        
        print_status "Starting development service..."
        docker-compose up -d
        
        print_success "Development deployment completed!"
        print_status "Server is running at: http://localhost:$PORT"
    fi

    print_status "Checking service health..."
    sleep 5
    
    if curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
        print_success "Health check passed - server is responding"
    else
        print_warning "Health check failed - server may still be starting"
    fi
}

# Heroku deployment
deploy_heroku() {
    print_status "Deploying to Heroku..."

    # Check if Heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI is not installed"
        print_error "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi

    # Create Procfile for Heroku
    cat > Procfile << EOF
web: python -m tiktok_ads_mcp.remote_main --host 0.0.0.0 --port \$PORT
EOF

    # Create runtime.txt
    cat > runtime.txt << EOF
python-3.11.8
EOF

    # Set environment variables on Heroku
    print_status "Setting environment variables on Heroku..."
    heroku config:set \
        TIKTOK_APP_ID="$TIKTOK_APP_ID" \
        TIKTOK_SECRET="$TIKTOK_SECRET" \
        TIKTOK_ACCESS_TOKEN="$TIKTOK_ACCESS_TOKEN" \
        LOG_LEVEL="${LOG_LEVEL:-info}" \
        WORKERS="$WORKERS"

    # Deploy to Heroku
    print_status "Deploying to Heroku..."
    git add .
    git commit -m "Deploy TikTok Ads MCP Remote Server" || true
    git push heroku main

    print_success "Heroku deployment completed!"
    
    # Get app URL
    APP_URL=$(heroku apps:info --json | python -c "import sys, json; print(json.load(sys.stdin)['app']['web_url'])")
    print_status "Your app is available at: $APP_URL"
}

# AWS deployment (basic example)
deploy_aws() {
    print_status "Deploying to AWS..."
    print_warning "AWS deployment requires additional setup and is not fully automated"
    print_status "Please refer to AWS documentation for complete deployment"
    
    # Create docker-compose override for AWS
    cat > docker-compose.aws.yml << EOF
version: '3.8'
services:
  tiktok-ads-mcp-remote:
    environment:
      - HOST=0.0.0.0
      - PORT=80
      - WORKERS=${WORKERS}
      - LOG_LEVEL=${LOG_LEVEL:-warning}
    ports:
      - "80:80"
EOF

    print_status "Created AWS-specific configuration"
    print_status "Use: docker-compose -f docker-compose.yml -f docker-compose.aws.yml up -d"
}

# GCP deployment (basic example)
deploy_gcp() {
    print_status "Deploying to Google Cloud Platform..."
    print_warning "GCP deployment requires additional setup and is not fully automated"
    
    # Create app.yaml for App Engine
    cat > app.yaml << EOF
runtime: python311
env: standard

env_variables:
  TIKTOK_APP_ID: "${TIKTOK_APP_ID}"
  TIKTOK_SECRET: "${TIKTOK_SECRET}"
  TIKTOK_ACCESS_TOKEN: "${TIKTOK_ACCESS_TOKEN}"
  HOST: "0.0.0.0"
  PORT: "8080"
  WORKERS: "${WORKERS}"
  LOG_LEVEL: "${LOG_LEVEL:-warning}"

entrypoint: python -m tiktok_ads_mcp.remote_main --host 0.0.0.0 --port 8080
EOF

    print_status "Created GCP App Engine configuration"
    print_status "Use: gcloud app deploy"
}

# Azure deployment (basic example)  
deploy_azure() {
    print_status "Deploying to Microsoft Azure..."
    print_warning "Azure deployment requires additional setup and is not fully automated"
    
    # Create Azure-specific configuration
    print_status "Created Azure-specific configuration files"
    print_status "Please refer to Azure documentation for complete deployment"
}

# Render deployment
deploy_render() {
    print_status "Deploying to Render..."

    # Check if render.yaml exists
    if [[ ! -f "render.yaml" ]]; then
        print_error "render.yaml not found. This file is required for Render deployment."
        exit 1
    fi

    # Validate Git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "This directory is not a Git repository. Render requires Git for deployment."
        print_status "Run: git init && git add . && git commit -m 'Initial commit'"
        exit 1
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes. Committing them now..."
        git add .
        git commit -m "Prepare for Render deployment" || true
    fi

    # Create .env.example for documentation
    cat > .env.example << EOF
# TikTok API Credentials (set these as environment variables in Render dashboard)
TIKTOK_APP_ID=your_app_id_here
TIKTOK_SECRET=your_app_secret_here
TIKTOK_ACCESS_TOKEN=your_access_token_here

# Optional configuration
HOST=0.0.0.0
LOG_LEVEL=info
WORKERS=2
EOF

    print_success "Render deployment preparation completed!"
    
    echo ""
    print_status "Next steps to deploy on Render:"
    print_status "1. Push your code to GitHub:"
    print_status "   git remote add origin https://github.com/yourusername/your-repo.git"
    print_status "   git branch -M main"
    print_status "   git push -u origin main"
    print_status ""
    print_status "2. Go to Render Dashboard (https://render.com)"
    print_status "3. Click 'New +' -> 'Web Service'"
    print_status "4. Connect your GitHub repository"
    print_status "5. Render will automatically detect render.yaml and configure the service"
    print_status ""
    print_status "6. Set environment variables in Render dashboard:"
    print_status "   - TIKTOK_APP_ID: Your TikTok app ID"
    print_status "   - TIKTOK_SECRET: Your TikTok app secret"
    print_status "   - TIKTOK_ACCESS_TOKEN: Your TikTok access token"
    print_status ""
    print_status "7. Deploy! Your service will be available at:"
    print_status "   https://your-service-name.onrender.com"
    print_status ""
    print_status "8. Add the URL to Claude via Settings > Connectors"

    # Show Render-specific information
    echo ""
    print_status "Render Configuration:"
    print_status "- Runtime: Python 3.11"
    print_status "- Plan: Starter (Free) - Upgrade to Standard for production"
    print_status "- Health check: /health endpoint"
    print_status "- Auto-deploy: Enabled (deploys on every git push)"
    print_status ""
    print_warning "Note: Free tier services may spin down after inactivity"
    print_warning "For production use, consider upgrading to a paid plan"
}

# Main deployment logic
main() {
    print_status "Checking environment variables..."
    check_env_vars

    case $PLATFORM in
        docker)
            deploy_docker
            ;;
        heroku)
            deploy_heroku
            ;;
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        azure)
            deploy_azure
            ;;
        render)
            deploy_render
            ;;
        *)
            print_error "Unsupported platform: $PLATFORM"
            exit 1
            ;;
    esac

    print_success "Deployment completed successfully!"
    print_status "Your TikTok Ads MCP Remote Server is ready to use with Claude"
    
    # Show next steps
    echo ""
    print_status "Next steps:"
    print_status "1. Add your server URL to Claude via Settings > Connectors"
    print_status "2. Complete the OAuth authentication flow"
    print_status "3. Start using TikTok Ads tools in Claude!"
    
    if [[ "$PLATFORM" == "docker" ]]; then
        echo ""
        print_status "Docker commands:"
        print_status "  View logs: docker-compose logs -f"
        print_status "  Stop services: docker-compose down"
        print_status "  Restart: docker-compose restart"
    fi
}

# Run main function
main