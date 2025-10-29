#!/bin/bash
# Complete deployment script for YouTube Study Buddy serverless architecture
# Orchestrates: Lambda layer build, infrastructure deployment, Lambda functions, and frontend

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DEPLOY_TARGET="${DEPLOY_TARGET:-s3}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo ""
    echo -e "${CYAN}=========================================="
    echo -e "  $1"
    echo -e "==========================================${NC}"
    echo ""
}

# Check if running in CI/CD
is_ci() {
    [ -n "${CI}" ] || [ -n "${GITHUB_ACTIONS}" ] || [ -n "${GITLAB_CI}" ]
}

# Deployment step tracking
TOTAL_STEPS=6
CURRENT_STEP=0

next_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    log_step "Step ${CURRENT_STEP}/${TOTAL_STEPS}: $1"
}

# Error handler
handle_error() {
    local exit_code=$?
    log_error "Deployment failed at step ${CURRENT_STEP}/${TOTAL_STEPS}"
    log_error "Error code: ${exit_code}"
    echo ""
    log_info "To rollback, run: ./scripts/rollback.sh"
    exit $exit_code
}

trap handle_error ERR

# Pre-deployment checks
pre_deployment_checks() {
    next_step "Pre-deployment Checks"

    log_info "Checking required tools..."

    local missing_tools=()

    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi

    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    fi

    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    fi

    if ! command -v npm &> /dev/null; then
        missing_tools+=("npm")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    # Check AWS credentials
    log_info "Verifying AWS credentials..."
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi

    local aws_account=$(aws sts get-caller-identity --query Account --output text)
    local aws_user=$(aws sts get-caller-identity --query Arn --output text)

    echo ""
    log_info "AWS Configuration:"
    echo "  Account:     ${aws_account}"
    echo "  User/Role:   ${aws_user}"
    echo "  Region:      ${AWS_REGION}"
    echo "  Environment: ${ENVIRONMENT}"
    echo ""

    # Confirmation for production
    if [ "$ENVIRONMENT" = "production" ] && ! is_ci; then
        log_warning "You are deploying to PRODUCTION!"
        echo ""
        read -p "Type 'production' to confirm: " confirm

        if [ "$confirm" != "production" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    log_success "Pre-deployment checks passed"
}

# Build Lambda layer
build_lambda_layer() {
    next_step "Building Lambda Layer"

    log_info "Building yt-study-buddy CLI Lambda layer..."

    cd "${PROJECT_ROOT}/lambda-layer"

    if [ ! -f "build.sh" ]; then
        log_error "Lambda layer build script not found"
        exit 1
    fi

    bash build.sh

    # Verify layer was created
    if [ ! -f "cli-layer.zip" ]; then
        log_error "Lambda layer build failed - zip file not created"
        exit 1
    fi

    local layer_size=$(du -h cli-layer.zip | cut -f1)
    log_success "Lambda layer built successfully (${layer_size})"
}

# Deploy infrastructure
deploy_infrastructure() {
    next_step "Deploying Infrastructure (Terraform)"

    log_info "Deploying AWS infrastructure..."

    export ENVIRONMENT
    export AWS_REGION

    if is_ci; then
        # Auto-approve in CI/CD
        bash "${SCRIPT_DIR}/deploy-infrastructure.sh" deploy true
    else
        # Interactive mode
        bash "${SCRIPT_DIR}/deploy-infrastructure.sh" deploy
    fi

    log_success "Infrastructure deployed"
}

# Deploy Lambda functions
deploy_lambda_functions() {
    next_step "Deploying Lambda Functions"

    log_info "Deploying all Lambda functions..."

    export ENVIRONMENT
    export AWS_REGION

    bash "${SCRIPT_DIR}/deploy-lambda.sh"

    log_success "Lambda functions deployed"
}

# Deploy frontend
deploy_frontend() {
    next_step "Deploying Frontend"

    log_info "Building and deploying frontend..."

    export ENVIRONMENT
    export DEPLOY_TARGET

    bash "${SCRIPT_DIR}/deploy-frontend.sh"

    log_success "Frontend deployed"
}

# Run smoke tests
run_smoke_tests() {
    next_step "Running Smoke Tests"

    log_info "Running post-deployment smoke tests..."

    # Load Terraform outputs
    local terraform_env="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$terraform_env" ]; then
        set -a
        source "$terraform_env"
        set +a
    fi

    local tests_passed=0
    local tests_failed=0

    # Test 1: API Gateway health
    if [ -n "${API_GATEWAY_URL}" ]; then
        log_info "Testing API Gateway: ${API_GATEWAY_URL}/health"
        local api_status=$(curl -s -o /dev/null -w "%{http_code}" "${API_GATEWAY_URL}/health" 2>/dev/null || echo "000")

        if [ "$api_status" = "200" ]; then
            log_success "API Gateway health check passed"
            tests_passed=$((tests_passed + 1))
        else
            log_error "API Gateway health check failed (status: ${api_status})"
            tests_failed=$((tests_failed + 1))
        fi
    fi

    # Test 2: Frontend accessibility
    if [ -n "${FRONTEND_URL}" ]; then
        log_info "Testing frontend: ${FRONTEND_URL}"
        local frontend_status=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")

        if [ "$frontend_status" = "200" ]; then
            log_success "Frontend accessibility check passed"
            tests_passed=$((tests_passed + 1))
        else
            log_error "Frontend accessibility check failed (status: ${frontend_status})"
            tests_failed=$((tests_failed + 1))
        fi
    fi

    # Test 3: DynamoDB tables
    if [ -n "${DYNAMODB_USERS_TABLE}" ]; then
        log_info "Testing DynamoDB tables..."
        if aws dynamodb describe-table --table-name "${DYNAMODB_USERS_TABLE}" &> /dev/null; then
            log_success "DynamoDB tables accessible"
            tests_passed=$((tests_passed + 1))
        else
            log_error "DynamoDB tables not accessible"
            tests_failed=$((tests_failed + 1))
        fi
    fi

    echo ""
    log_info "Smoke Test Results: ${tests_passed} passed, ${tests_failed} failed"

    if [ $tests_failed -gt 0 ]; then
        log_warning "Some smoke tests failed, but deployment completed"
    else
        log_success "All smoke tests passed!"
    fi
}

# Display deployment summary
show_summary() {
    echo ""
    echo -e "${MAGENTA}=========================================="
    echo "  Deployment Summary"
    echo "  Environment: ${ENVIRONMENT}"
    echo "==========================================${NC}"
    echo ""

    # Load Terraform outputs
    local terraform_env="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$terraform_env" ]; then
        set -a
        source "$terraform_env"
        set +a
    fi

    log_info "Deployed Resources:"
    echo ""

    # Infrastructure
    echo "  Infrastructure:"
    echo "    API Gateway:  ${API_GATEWAY_URL:-N/A}"
    echo "    WebSocket:    ${WEBSOCKET_URL:-N/A}"
    echo ""

    # Authentication
    echo "  Authentication:"
    echo "    Cognito Pool: ${COGNITO_USER_POOL_ID:-N/A}"
    echo "    Client ID:    ${COGNITO_CLIENT_ID:-N/A}"
    echo ""

    # Storage
    echo "  Storage:"
    echo "    Users Table:  ${DYNAMODB_USERS_TABLE:-N/A}"
    echo "    Videos Table: ${DYNAMODB_VIDEOS_TABLE:-N/A}"
    echo "    Notes Bucket: ${S3_NOTES_BUCKET:-N/A}"
    echo ""

    # Frontend
    echo "  Frontend:"
    echo "    URL:          ${FRONTEND_URL:-N/A}"
    echo "    Target:       ${DEPLOY_TARGET}"
    echo ""

    # Next steps
    log_info "Next Steps:"
    echo ""
    echo "  1. Configure OAuth providers in Cognito"
    echo "  2. Set up Stripe webhook endpoint"
    echo "  3. Seed development data: ./scripts/seed-data.sh"
    echo "  4. Monitor logs: aws logs tail /aws/lambda/ytstudy-${ENVIRONMENT}-FUNCTION_NAME --follow"
    echo ""

    # Save deployment info
    local deploy_info="${PROJECT_ROOT}/.deployment-${ENVIRONMENT}.txt"
    cat > "$deploy_info" <<EOF
YouTube Study Buddy - Deployment Information
============================================
Environment:   ${ENVIRONMENT}
Deployed At:   $(date)
Deployed By:   $(whoami)
AWS Account:   $(aws sts get-caller-identity --query Account --output text)
AWS Region:    ${AWS_REGION}

API Gateway:   ${API_GATEWAY_URL:-N/A}
Frontend:      ${FRONTEND_URL:-N/A}
Cognito Pool:  ${COGNITO_USER_POOL_ID:-N/A}

For detailed outputs, see: ${terraform_env}
EOF

    log_success "Deployment information saved to: ${deploy_info}"
}

# Main deployment flow
main() {
    local start_time=$(date +%s)

    echo ""
    echo -e "${MAGENTA}=========================================="
    echo "  YouTube Study Buddy"
    echo "  Serverless Deployment"
    echo "=========================================="
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Region:      ${AWS_REGION}"
    echo "  Target:      ${DEPLOY_TARGET}"
    echo "==========================================${NC}"
    echo ""

    # Execute deployment steps
    pre_deployment_checks
    build_lambda_layer
    deploy_infrastructure
    deploy_lambda_functions
    deploy_frontend
    run_smoke_tests

    # Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    echo ""
    log_success "Deployment completed successfully in ${minutes}m ${seconds}s"

    # Show summary
    show_summary

    echo ""
    echo -e "${GREEN}=========================================="
    echo "  All Done!"
    echo "==========================================${NC}"
    echo ""
}

# Run main function
main "$@"
