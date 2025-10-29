#!/bin/bash
# Deploy frontend React application
# Supports S3+CloudFront, Vercel, and Netlify deployments

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="${PROJECT_ROOT}/webapp/webapp/frontend"
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOY_TARGET="${DEPLOY_TARGET:-s3}"  # s3, vercel, or netlify

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

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: ${FRONTEND_DIR}"
        exit 1
    fi

    if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
        log_error "package.json not found in ${FRONTEND_DIR}"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."

    cd "$FRONTEND_DIR"

    npm ci --prefer-offline

    log_success "Dependencies installed"
}

# Load environment variables
load_env_vars() {
    log_info "Loading environment variables..."

    # Load from Terraform outputs if available
    local terraform_env="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$terraform_env" ]; then
        log_info "Loading Terraform outputs from ${terraform_env}"
        set -a
        source "$terraform_env"
        set +a
    fi

    # Load from environment-specific .env file
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    if [ -f "$env_file" ]; then
        log_info "Loading environment variables from ${env_file}"
        set -a
        source "$env_file"
        set +a
    fi

    # Create .env.production for Vite
    local vite_env="${FRONTEND_DIR}/.env.production"
    log_info "Creating Vite environment file: ${vite_env}"

    cat > "$vite_env" <<EOF
# Auto-generated environment file for ${ENVIRONMENT}
# Generated at: $(date)

VITE_API_URL=${API_GATEWAY_URL:-https://api.example.com}
VITE_WS_URL=${WEBSOCKET_URL:-wss://ws.example.com}
VITE_COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID:-}
VITE_COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID:-}
VITE_AWS_REGION=${AWS_REGION:-us-east-1}
VITE_STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:-}
VITE_ENVIRONMENT=${ENVIRONMENT}
EOF

    log_success "Environment variables loaded"
}

# Build frontend
build_frontend() {
    log_info "Building frontend for ${ENVIRONMENT}..."

    cd "$FRONTEND_DIR"

    # Run build
    npm run build

    # Verify build output
    if [ ! -d "dist" ]; then
        log_error "Build failed - dist directory not created"
        exit 1
    fi

    local build_size=$(du -sh dist | cut -f1)
    log_success "Frontend built successfully (${build_size})"
}

# Deploy to S3 + CloudFront
deploy_to_s3() {
    local bucket_name="${S3_FRONTEND_BUCKET:-ytstudybuddy-frontend-${ENVIRONMENT}}"
    local cloudfront_id="${CLOUDFRONT_DISTRIBUTION_ID:-}"

    log_info "Deploying to S3: ${bucket_name}..."

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    # Sync to S3
    aws s3 sync dist/ "s3://${bucket_name}/" \
        --delete \
        --cache-control "public,max-age=31536000,immutable" \
        --exclude "index.html"

    # Upload index.html separately with short cache
    aws s3 cp dist/index.html "s3://${bucket_name}/index.html" \
        --cache-control "public,max-age=0,must-revalidate"

    log_success "Files uploaded to S3"

    # Invalidate CloudFront cache
    if [ -n "$cloudfront_id" ]; then
        log_info "Invalidating CloudFront cache: ${cloudfront_id}..."

        aws cloudfront create-invalidation \
            --distribution-id "$cloudfront_id" \
            --paths "/*" \
            > /dev/null

        log_success "CloudFront cache invalidated"
    else
        log_warning "No CloudFront distribution ID provided, skipping cache invalidation"
    fi

    # Get CloudFront URL
    local cloudfront_url=$(aws cloudfront get-distribution \
        --id "$cloudfront_id" \
        --query 'Distribution.DomainName' \
        --output text 2>/dev/null || echo "N/A")

    echo ""
    log_success "Frontend deployed to S3!"
    echo ""
    echo "  S3 Bucket:      ${bucket_name}"
    echo "  CloudFront URL: https://${cloudfront_url}"
    echo ""
}

# Deploy to Vercel
deploy_to_vercel() {
    log_info "Deploying to Vercel..."

    if ! command -v vercel &> /dev/null; then
        log_error "Vercel CLI is not installed. Install with: npm install -g vercel"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    # Set environment variables for Vercel
    local env_args=""
    if [ -f ".env.production" ]; then
        while IFS='=' read -r key value; do
            [[ $key =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            env_args="${env_args} -e ${key}=${value}"
        done < .env.production
    fi

    # Deploy
    if [ "$ENVIRONMENT" = "production" ]; then
        vercel deploy --prod --yes ${env_args}
    else
        vercel deploy --yes ${env_args}
    fi

    log_success "Frontend deployed to Vercel!"

    # Get deployment URL
    local url=$(vercel ls --json | jq -r '.[0].url' 2>/dev/null || echo "Check Vercel dashboard")
    echo ""
    echo "  Deployment URL: https://${url}"
    echo ""
}

# Deploy to Netlify
deploy_to_netlify() {
    log_info "Deploying to Netlify..."

    if ! command -v netlify &> /dev/null; then
        log_error "Netlify CLI is not installed. Install with: npm install -g netlify-cli"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    # Deploy
    if [ "$ENVIRONMENT" = "production" ]; then
        netlify deploy --prod --dir=dist
    else
        netlify deploy --dir=dist
    fi

    log_success "Frontend deployed to Netlify!"
}

# Run smoke tests
run_smoke_tests() {
    local base_url=$1

    log_info "Running smoke tests..."

    # Test if site is accessible
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$base_url" || echo "000")

    if [ "$status" = "200" ]; then
        log_success "Smoke test passed - site is accessible"
    else
        log_error "Smoke test failed - received status code: ${status}"
        return 1
    fi

    # Test if assets are loading
    local asset_status=$(curl -s -o /dev/null -w "%{http_code}" "${base_url}/assets/index.js" || echo "000")

    if [ "$asset_status" = "200" ] || [ "$asset_status" = "404" ]; then
        log_info "Assets check completed"
    else
        log_warning "Unexpected asset status: ${asset_status}"
    fi
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  Frontend Deployment"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Target: ${DEPLOY_TARGET}"
    echo "=========================================="
    echo ""

    # Check prerequisites
    check_prerequisites

    # Install dependencies
    install_dependencies

    # Load environment variables
    load_env_vars

    # Build frontend
    build_frontend

    # Deploy based on target
    case "$DEPLOY_TARGET" in
        "s3")
            deploy_to_s3
            ;;
        "vercel")
            deploy_to_vercel
            ;;
        "netlify")
            deploy_to_netlify
            ;;
        *)
            log_error "Unknown deploy target: ${DEPLOY_TARGET}"
            echo ""
            echo "Supported targets: s3, vercel, netlify"
            echo "Set with: DEPLOY_TARGET=vercel $0"
            echo ""
            exit 1
            ;;
    esac

    # Run smoke tests if URL is available
    if [ -n "${FRONTEND_URL}" ]; then
        run_smoke_tests "${FRONTEND_URL}"
    fi

    echo ""
    log_success "Deployment complete!"
    echo ""
}

# Run main function
main "$@"
