#!/bin/bash
# Deploy infrastructure using Terraform
# Validates, plans, and applies Terraform configuration

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"

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

    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Install from: https://www.terraform.io/downloads"
        exit 1
    fi

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Install with: pip install awscli"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi

    # Check if terraform directory exists
    if [ ! -d "$TERRAFORM_DIR" ]; then
        log_error "Terraform directory not found: ${TERRAFORM_DIR}"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Initialize Terraform
terraform_init() {
    log_info "Initializing Terraform..."

    cd "$TERRAFORM_DIR"

    terraform init \
        -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
        -reconfigure

    log_success "Terraform initialized"
}

# Validate Terraform configuration
terraform_validate() {
    log_info "Validating Terraform configuration..."

    cd "$TERRAFORM_DIR"

    if ! terraform validate; then
        log_error "Terraform validation failed"
        exit 1
    fi

    log_success "Terraform configuration is valid"
}

# Format Terraform files
terraform_fmt() {
    log_info "Formatting Terraform files..."

    cd "$TERRAFORM_DIR"

    terraform fmt -recursive

    log_success "Terraform files formatted"
}

# Plan Terraform changes
terraform_plan() {
    local plan_file="${TERRAFORM_DIR}/tfplan-${ENVIRONMENT}"

    log_info "Planning Terraform changes..."

    cd "$TERRAFORM_DIR"

    # Load environment-specific variables
    local var_file="${TERRAFORM_DIR}/environments/${ENVIRONMENT}.tfvars"
    local var_args=""

    if [ -f "$var_file" ]; then
        var_args="-var-file=${var_file}"
    else
        log_warning "Environment variable file not found: ${var_file}"
    fi

    # Load secrets from environment or .env file
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    if [ -f "$env_file" ]; then
        log_info "Loading environment variables from ${env_file}..."
        set -a
        source "$env_file"
        set +a
    fi

    # Run terraform plan
    terraform plan \
        -var="environment=${ENVIRONMENT}" \
        -var="aws_region=${AWS_REGION}" \
        ${var_args} \
        -out="$plan_file"

    log_success "Terraform plan created: ${plan_file}"
    echo "$plan_file"
}

# Apply Terraform changes
terraform_apply() {
    local plan_file=$1
    local auto_approve=${2:-false}

    log_info "Applying Terraform changes..."

    cd "$TERRAFORM_DIR"

    if [ "$auto_approve" = "true" ]; then
        terraform apply -auto-approve "$plan_file"
    else
        # Show plan summary
        echo ""
        log_warning "About to apply changes to ${ENVIRONMENT} environment"
        echo ""

        # Ask for confirmation
        read -p "Do you want to proceed? (yes/no): " confirm

        if [ "$confirm" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi

        terraform apply "$plan_file"
    fi

    log_success "Terraform changes applied successfully"
}

# Save Terraform outputs
save_outputs() {
    local output_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"

    log_info "Saving Terraform outputs..."

    cd "$TERRAFORM_DIR"

    # Get outputs in JSON format
    local outputs=$(terraform output -json)

    # Create .env format file
    echo "# Auto-generated Terraform outputs - ${ENVIRONMENT}" > "$output_file"
    echo "# Generated at: $(date)" >> "$output_file"
    echo "" >> "$output_file"

    # Parse JSON outputs to .env format
    echo "$outputs" | jq -r 'to_entries[] | "\(.key | ascii_upcase)=\(.value.value)"' >> "$output_file"

    log_success "Outputs saved to: ${output_file}"

    # Display key outputs
    echo ""
    log_info "Key Infrastructure Outputs:"
    echo ""

    # API Gateway URL
    local api_url=$(terraform output -raw api_gateway_url 2>/dev/null || echo "N/A")
    echo "  API Gateway URL:  ${api_url}"

    # DynamoDB Tables
    local users_table=$(terraform output -raw dynamodb_users_table 2>/dev/null || echo "N/A")
    echo "  Users Table:      ${users_table}"

    local videos_table=$(terraform output -raw dynamodb_videos_table 2>/dev/null || echo "N/A")
    echo "  Videos Table:     ${videos_table}"

    # S3 Buckets
    local notes_bucket=$(terraform output -raw s3_notes_bucket 2>/dev/null || echo "N/A")
    echo "  Notes Bucket:     ${notes_bucket}"

    # Cognito
    local user_pool_id=$(terraform output -raw cognito_user_pool_id 2>/dev/null || echo "N/A")
    echo "  Cognito Pool:     ${user_pool_id}"

    echo ""
}

# Show infrastructure state
show_state() {
    log_info "Current Infrastructure State:"
    echo ""

    cd "$TERRAFORM_DIR"

    terraform show -no-color | head -50

    echo ""
    log_info "Full state: terraform show"
}

# Destroy infrastructure
destroy_infrastructure() {
    log_warning "=========================================="
    log_warning "  DESTROY INFRASTRUCTURE"
    log_warning "  Environment: ${ENVIRONMENT}"
    log_warning "=========================================="
    echo ""

    log_error "This will DELETE all resources in ${ENVIRONMENT}!"
    echo ""
    read -p "Type the environment name to confirm: " confirm

    if [ "$confirm" != "$ENVIRONMENT" ]; then
        log_info "Destruction cancelled"
        exit 0
    fi

    echo ""
    read -p "Are you absolutely sure? (yes/no): " confirm2

    if [ "$confirm2" != "yes" ]; then
        log_info "Destruction cancelled"
        exit 0
    fi

    cd "$TERRAFORM_DIR"

    log_warning "Destroying infrastructure..."

    terraform destroy \
        -var="environment=${ENVIRONMENT}" \
        -var="aws_region=${AWS_REGION}" \
        -auto-approve

    log_success "Infrastructure destroyed"
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  Terraform Infrastructure Deployment"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Region: ${AWS_REGION}"
    echo "=========================================="
    echo ""

    # Parse command
    local command=${1:-deploy}

    case "$command" in
        "deploy")
            check_prerequisites
            terraform_init
            terraform_validate
            terraform_fmt
            local plan_file=$(terraform_plan)
            terraform_apply "$plan_file" "${2:-false}"
            save_outputs
            log_success "Deployment complete!"
            ;;

        "plan")
            check_prerequisites
            terraform_init
            terraform_validate
            terraform_plan
            ;;

        "init")
            check_prerequisites
            terraform_init
            ;;

        "validate")
            check_prerequisites
            terraform_validate
            ;;

        "fmt")
            terraform_fmt
            ;;

        "state")
            show_state
            ;;

        "outputs")
            save_outputs
            ;;

        "destroy")
            check_prerequisites
            terraform_init
            destroy_infrastructure
            ;;

        *)
            log_error "Unknown command: ${command}"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy      - Deploy infrastructure (default)"
            echo "  plan        - Show planned changes"
            echo "  init        - Initialize Terraform"
            echo "  validate    - Validate configuration"
            echo "  fmt         - Format Terraform files"
            echo "  state       - Show current state"
            echo "  outputs     - Save outputs to .env file"
            echo "  destroy     - Destroy infrastructure (DANGEROUS)"
            echo ""
            exit 1
            ;;
    esac

    echo ""
}

# Run main function
main "$@"
