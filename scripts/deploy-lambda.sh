#!/bin/bash
# Deploy Lambda functions to AWS
# Packages each Lambda function, uploads to S3, and updates function code

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="${PROJECT_ROOT}/lambda"
S3_BUCKET="${S3_BUCKET:-ytstudybuddy-lambda-deployments}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

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

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Install with: pip install awscli"
        exit 1
    fi

    if ! command -v zip &> /dev/null; then
        log_error "zip command not found"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Package a Lambda function
package_lambda() {
    local function_name=$1
    local function_dir="${LAMBDA_DIR}/${function_name}"
    local zip_file="${function_name}.zip"

    if [ ! -d "$function_dir" ]; then
        log_error "Function directory not found: ${function_dir}"
        return 1
    fi

    log_info "Packaging ${function_name}..."

    cd "$function_dir"

    # Remove old zip if exists
    rm -f "$zip_file"

    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        log_info "Installing dependencies for ${function_name}..."
        pip install -r requirements.txt -t . --upgrade
    fi

    # Create zip with all files
    zip -r "$zip_file" . -x "*.zip" -x "__pycache__/*" -x "*.pyc" -x ".git/*" -q

    local zip_size=$(du -h "$zip_file" | cut -f1)
    log_success "Packaged ${function_name} (${zip_size})"

    cd - > /dev/null
}

# Upload package to S3
upload_to_s3() {
    local function_name=$1
    local zip_file="${LAMBDA_DIR}/${function_name}/${function_name}.zip"
    local s3_key="${ENVIRONMENT}/lambda/${function_name}/$(date +%Y%m%d-%H%M%S)/${function_name}.zip"

    log_info "Uploading ${function_name} to S3..."

    # Create bucket if it doesn't exist
    if ! aws s3 ls "s3://${S3_BUCKET}" 2>&1 > /dev/null; then
        log_warning "Creating S3 bucket ${S3_BUCKET}..."
        aws s3 mb "s3://${S3_BUCKET}" --region "${AWS_REGION}"
    fi

    aws s3 cp "$zip_file" "s3://${S3_BUCKET}/${s3_key}" --region "${AWS_REGION}"

    echo "s3://${S3_BUCKET}/${s3_key}"
}

# Update Lambda function code
update_lambda_function() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"
    local zip_file="${LAMBDA_DIR}/${function_name}/${function_name}.zip"

    log_info "Updating Lambda function: ${aws_function_name}..."

    # Check if package is too large for direct upload (>50MB)
    local zip_size_bytes=$(stat -f%z "$zip_file" 2>/dev/null || stat -c%s "$zip_file")
    local zip_size_mb=$((zip_size_bytes / 1024 / 1024))

    if [ $zip_size_mb -gt 50 ]; then
        log_warning "Package size (${zip_size_mb}MB) > 50MB, uploading via S3..."
        local s3_location=$(upload_to_s3 "$function_name")

        aws lambda update-function-code \
            --function-name "$aws_function_name" \
            --s3-bucket "${S3_BUCKET}" \
            --s3-key "${s3_location#s3://${S3_BUCKET}/}" \
            --region "${AWS_REGION}" \
            > /dev/null
    else
        # Direct upload for smaller packages
        aws lambda update-function-code \
            --function-name "$aws_function_name" \
            --zip-file "fileb://${zip_file}" \
            --region "${AWS_REGION}" \
            > /dev/null
    fi

    log_success "Updated ${aws_function_name}"
}

# Update Lambda environment variables
update_env_vars() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"

    if [ ! -f "$env_file" ]; then
        log_warning "Environment file not found: ${env_file}"
        return 0
    fi

    log_info "Updating environment variables for ${aws_function_name}..."

    # Read .env file and build JSON
    local env_vars="{"
    local first=true

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Remove quotes from value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        if [ "$first" = true ]; then
            first=false
        else
            env_vars+=","
        fi

        env_vars+="\"$key\":\"$value\""
    done < "$env_file"

    env_vars+="}"

    # Only update if we have variables
    if [ "$env_vars" != "{}" ]; then
        aws lambda update-function-configuration \
            --function-name "$aws_function_name" \
            --environment "Variables=${env_vars}" \
            --region "${AWS_REGION}" \
            > /dev/null

        log_success "Updated environment variables"
    fi
}

# Test Lambda function
test_lambda_function() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"

    log_info "Testing ${aws_function_name}..."

    # Create test payload based on function type
    local test_payload="{}"

    case "$function_name" in
        "get_video")
            test_payload='{"pathParameters":{"video_id":"test-123"},"requestContext":{"authorizer":{"claims":{"sub":"test-user"}}}}'
            ;;
        "list_videos")
            test_payload='{"queryStringParameters":{},"requestContext":{"authorizer":{"claims":{"sub":"test-user"}}}}'
            ;;
        "get_note")
            test_payload='{"pathParameters":{"note_id":"test-123"},"requestContext":{"authorizer":{"claims":{"sub":"test-user"}}}}'
            ;;
        *)
            log_warning "No test payload defined for ${function_name}, skipping test"
            return 0
            ;;
    esac

    # Invoke function
    local response=$(aws lambda invoke \
        --function-name "$aws_function_name" \
        --payload "$test_payload" \
        --region "${AWS_REGION}" \
        /tmp/lambda-response.json 2>&1)

    # Check for errors
    if echo "$response" | grep -q "FunctionError"; then
        log_error "Function test failed: ${function_name}"
        cat /tmp/lambda-response.json
        return 1
    fi

    log_success "Test passed for ${function_name}"
}

# Get function URL
get_function_url() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"

    local url=$(aws lambda get-function-url-config \
        --function-name "$aws_function_name" \
        --region "${AWS_REGION}" \
        --query 'FunctionUrl' \
        --output text 2>/dev/null || echo "N/A")

    echo "$url"
}

# Main deployment function
deploy_function() {
    local function_name=$1

    echo ""
    log_info "=========================================="
    log_info "Deploying Lambda: ${function_name}"
    log_info "=========================================="

    # Package
    if ! package_lambda "$function_name"; then
        log_error "Failed to package ${function_name}"
        return 1
    fi

    # Update function
    if ! update_lambda_function "$function_name"; then
        log_error "Failed to update ${function_name}"
        return 1
    fi

    # Update environment variables
    update_env_vars "$function_name"

    # Wait for function to be ready
    log_info "Waiting for function to be ready..."
    aws lambda wait function-updated \
        --function-name "ytstudy-${ENVIRONMENT}-${function_name}" \
        --region "${AWS_REGION}" || true

    # Test function
    test_lambda_function "$function_name"

    # Get function URL
    local url=$(get_function_url "$function_name")
    if [ "$url" != "N/A" ]; then
        log_info "Function URL: ${url}"
    fi

    log_success "Successfully deployed ${function_name}"
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  Lambda Deployment Script"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Region: ${AWS_REGION}"
    echo "=========================================="
    echo ""

    # Check prerequisites
    check_prerequisites

    # Get list of Lambda functions
    local lambda_functions=()
    for dir in "${LAMBDA_DIR}"/*; do
        if [ -d "$dir" ] && [ "$(basename "$dir")" != "shared" ]; then
            lambda_functions+=("$(basename "$dir")")
        fi
    done

    if [ ${#lambda_functions[@]} -eq 0 ]; then
        log_error "No Lambda functions found in ${LAMBDA_DIR}"
        exit 1
    fi

    log_info "Found ${#lambda_functions[@]} Lambda functions:"
    for func in "${lambda_functions[@]}"; do
        echo "  - $func"
    done
    echo ""

    # Deploy specific function or all
    if [ $# -eq 0 ]; then
        # Deploy all functions
        local failed_functions=()

        for func in "${lambda_functions[@]}"; do
            if ! deploy_function "$func"; then
                failed_functions+=("$func")
            fi
        done

        # Summary
        echo ""
        echo "=========================================="
        echo "  Deployment Summary"
        echo "=========================================="

        local success_count=$((${#lambda_functions[@]} - ${#failed_functions[@]}))
        log_info "Deployed: ${success_count}/${#lambda_functions[@]} functions"

        if [ ${#failed_functions[@]} -gt 0 ]; then
            log_error "Failed functions:"
            for func in "${failed_functions[@]}"; do
                echo "  - $func"
            done
            exit 1
        else
            log_success "All functions deployed successfully!"
        fi
    else
        # Deploy specific function
        local function_name=$1

        if [[ ! " ${lambda_functions[@]} " =~ " ${function_name} " ]]; then
            log_error "Function not found: ${function_name}"
            log_info "Available functions: ${lambda_functions[*]}"
            exit 1
        fi

        deploy_function "$function_name"
    fi

    echo ""
    log_info "Deployment complete!"
    log_info "View logs with: aws logs tail /aws/lambda/ytstudy-${ENVIRONMENT}-FUNCTION_NAME --follow"
    echo ""
}

# Run main function
main "$@"
