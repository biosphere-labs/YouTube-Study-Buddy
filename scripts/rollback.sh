#!/bin/bash
# Rollback script for YouTube Study Buddy serverless deployment
# Supports rollback of Terraform, Lambda functions, and frontend

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
MAGENTA='\033[0;35m'
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
        log_error "AWS CLI not installed"
        exit 1
    fi

    if ! command -v terraform &> /dev/null; then
        log_error "Terraform not installed"
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# List available Lambda versions
list_lambda_versions() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"

    log_info "Available versions for ${function_name}:"
    echo ""

    aws lambda list-versions-by-function \
        --function-name "$aws_function_name" \
        --region "${AWS_REGION}" \
        --query 'Versions[?Version!=`$LATEST`].[Version,LastModified,Description]' \
        --output table

    echo ""
}

# Rollback Lambda function to previous version
rollback_lambda_function() {
    local function_name=$1
    local target_version=$2
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"

    if [ -z "$target_version" ]; then
        log_error "Target version not specified"
        return 1
    fi

    log_warning "Rolling back ${function_name} to version ${target_version}..."

    # Get current version
    local current_version=$(aws lambda get-function \
        --function-name "$aws_function_name" \
        --region "${AWS_REGION}" \
        --query 'Configuration.Version' \
        --output text)

    log_info "Current version: ${current_version}"
    log_info "Target version:  ${target_version}"

    # Update alias to point to target version
    if aws lambda get-alias \
        --function-name "$aws_function_name" \
        --name "live" \
        --region "${AWS_REGION}" &> /dev/null; then

        aws lambda update-alias \
            --function-name "$aws_function_name" \
            --name "live" \
            --function-version "$target_version" \
            --region "${AWS_REGION}" \
            > /dev/null

        log_success "Rolled back ${function_name} to version ${target_version}"
    else
        log_warning "No 'live' alias found, creating one..."

        aws lambda create-alias \
            --function-name "$aws_function_name" \
            --name "live" \
            --function-version "$target_version" \
            --region "${AWS_REGION}" \
            > /dev/null

        log_success "Created 'live' alias pointing to version ${target_version}"
    fi
}

# Rollback all Lambda functions
rollback_all_lambdas() {
    log_warning "Rolling back ALL Lambda functions..."
    echo ""

    # Get list of functions
    local lambda_dir="${PROJECT_ROOT}/lambda"
    local functions=()

    for dir in "${lambda_dir}"/*; do
        if [ -d "$dir" ] && [ "$(basename "$dir")" != "shared" ]; then
            functions+=("$(basename "$dir")")
        fi
    done

    log_info "Found ${#functions[@]} Lambda functions"
    echo ""

    for func in "${functions[@]}"; do
        log_info "Rolling back: ${func}"

        # Get previous version (2nd most recent)
        local previous_version=$(aws lambda list-versions-by-function \
            --function-name "ytstudy-${ENVIRONMENT}-${func}" \
            --region "${AWS_REGION}" \
            --query 'Versions[?Version!=`$LATEST`]|[-2].Version' \
            --output text 2>/dev/null || echo "")

        if [ -n "$previous_version" ] && [ "$previous_version" != "None" ]; then
            rollback_lambda_function "$func" "$previous_version"
        else
            log_warning "No previous version found for ${func}"
        fi
    done

    log_success "All Lambda functions rolled back"
}

# Rollback Terraform to previous state
rollback_terraform() {
    log_warning "Rolling back Terraform infrastructure..."

    cd "$TERRAFORM_DIR"

    # List available states
    log_info "Available Terraform state versions:"
    echo ""

    aws s3api list-object-versions \
        --bucket "ytstudybuddy-terraform-state" \
        --prefix "${ENVIRONMENT}/terraform.tfstate" \
        --query 'Versions[?IsLatest==`false`].[VersionId,LastModified]' \
        --output table \
        --region "${AWS_REGION}" 2>/dev/null || log_warning "No previous states found"

    echo ""
    read -p "Enter version ID to rollback to (or 'cancel'): " version_id

    if [ "$version_id" = "cancel" ] || [ -z "$version_id" ]; then
        log_info "Rollback cancelled"
        return 0
    fi

    # Download previous state
    log_info "Downloading previous state..."

    aws s3api get-object \
        --bucket "ytstudybuddy-terraform-state" \
        --key "${ENVIRONMENT}/terraform.tfstate" \
        --version-id "$version_id" \
        terraform.tfstate.rollback \
        --region "${AWS_REGION}"

    # Backup current state
    terraform state pull > terraform.tfstate.backup

    # Push previous state
    log_warning "Pushing previous state to Terraform..."
    terraform state push terraform.tfstate.rollback

    log_success "Terraform state rolled back to version: ${version_id}"
    log_info "Backup of current state saved to: terraform.tfstate.backup"

    # Apply the previous state
    echo ""
    read -p "Apply the previous state? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        terraform apply -auto-approve
        log_success "Previous infrastructure state applied"
    else
        log_info "State rollback complete, but not applied. Run 'terraform apply' to apply changes."
    fi
}

# Rollback frontend deployment
rollback_frontend() {
    log_warning "Rolling back frontend deployment..."

    local deploy_target="${DEPLOY_TARGET:-s3}"

    case "$deploy_target" in
        "s3")
            log_info "Listing S3 bucket versions..."

            local bucket="${S3_FRONTEND_BUCKET:-ytstudybuddy-frontend-${ENVIRONMENT}}"

            # Show recent versions
            aws s3api list-object-versions \
                --bucket "$bucket" \
                --prefix "index.html" \
                --max-items 10 \
                --region "${AWS_REGION}" \
                --query 'Versions[].[VersionId,LastModified,IsLatest]' \
                --output table

            echo ""
            log_warning "S3 versioning allows automatic rollback"
            log_info "To restore a specific version, use:"
            echo "  aws s3api copy-object --bucket $bucket --copy-source $bucket/index.html?versionId=VERSION_ID --key index.html"
            ;;

        "vercel")
            log_info "Rolling back Vercel deployment..."

            if ! command -v vercel &> /dev/null; then
                log_error "Vercel CLI not installed"
                return 1
            fi

            cd "${PROJECT_ROOT}/webapp/webapp/frontend"

            # List recent deployments
            vercel ls

            echo ""
            read -p "Enter deployment URL to rollback to: " deployment_url

            if [ -n "$deployment_url" ]; then
                vercel alias set "$deployment_url" "$(vercel ls --json | jq -r '.[0].alias[0]')"
                log_success "Frontend rolled back to: ${deployment_url}"
            fi
            ;;

        "netlify")
            log_info "Rolling back Netlify deployment..."

            if ! command -v netlify &> /dev/null; then
                log_error "Netlify CLI not installed"
                return 1
            fi

            cd "${PROJECT_ROOT}/webapp/webapp/frontend"

            # List recent deployments
            netlify deploy:list

            echo ""
            log_info "Use Netlify dashboard or CLI to rollback to a specific deployment"
            ;;

        *)
            log_error "Unknown deployment target: ${deploy_target}"
            ;;
    esac
}

# Rollback database migrations (DynamoDB)
rollback_database() {
    log_warning "Database rollback for DynamoDB..."
    log_info "DynamoDB is schemaless - no migrations to rollback"
    log_info "To restore data, use point-in-time recovery (PITR) or backups"

    echo ""
    log_info "Available options:"
    echo "  1. Point-in-time recovery (PITR) - if enabled"
    echo "  2. On-demand backups"
    echo ""

    local tables=("ytstudy-users-${ENVIRONMENT}" "ytstudy-videos-${ENVIRONMENT}" "ytstudy-notes-${ENVIRONMENT}")

    for table in "${tables[@]}"; do
        log_info "Table: ${table}"

        # Check if PITR is enabled
        local pitr_status=$(aws dynamodb describe-continuous-backups \
            --table-name "$table" \
            --region "${AWS_REGION}" \
            --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' \
            --output text 2>/dev/null || echo "N/A")

        echo "  PITR Status: ${pitr_status}"

        # List backups
        local backup_count=$(aws dynamodb list-backups \
            --table-name "$table" \
            --region "${AWS_REGION}" \
            --query 'length(BackupSummaries)' \
            --output text 2>/dev/null || echo "0")

        echo "  Backups: ${backup_count}"
        echo ""
    done

    log_info "To restore from PITR:"
    echo "  aws dynamodb restore-table-to-point-in-time --source-table-name TABLE --target-table-name TABLE_RESTORE --restore-date-time TIMESTAMP"
}

# Show rollback menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Rollback Menu"
    echo "  Environment: ${ENVIRONMENT}"
    echo "=========================================="
    echo ""
    echo "  1. Rollback single Lambda function"
    echo "  2. Rollback all Lambda functions"
    echo "  3. Rollback Terraform infrastructure"
    echo "  4. Rollback frontend deployment"
    echo "  5. Database rollback information"
    echo "  6. Complete rollback (all components)"
    echo "  0. Cancel"
    echo ""
    read -p "Select option: " option

    case "$option" in
        1)
            echo ""
            read -p "Enter Lambda function name: " function_name
            list_lambda_versions "$function_name"
            read -p "Enter version to rollback to: " version
            rollback_lambda_function "$function_name" "$version"
            ;;
        2)
            rollback_all_lambdas
            ;;
        3)
            rollback_terraform
            ;;
        4)
            rollback_frontend
            ;;
        5)
            rollback_database
            ;;
        6)
            log_warning "COMPLETE ROLLBACK - This will rollback all components"
            echo ""
            read -p "Are you sure? (yes/no): " confirm

            if [ "$confirm" = "yes" ]; then
                rollback_all_lambdas
                rollback_frontend
                log_warning "Infrastructure rollback requires manual confirmation"
                rollback_terraform
                log_success "Complete rollback finished"
            else
                log_info "Rollback cancelled"
            fi
            ;;
        0)
            log_info "Rollback cancelled"
            exit 0
            ;;
        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  YouTube Study Buddy - Rollback Script"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Region: ${AWS_REGION}"
    echo "=========================================="
    echo ""

    check_prerequisites

    # Load Terraform outputs
    local terraform_env="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$terraform_env" ]; then
        set -a
        source "$terraform_env"
        set +a
    fi

    # Check if specific component was requested
    if [ $# -eq 0 ]; then
        show_menu
    else
        local component=$1

        case "$component" in
            "lambda")
                if [ -n "$2" ]; then
                    rollback_lambda_function "$2" "$3"
                else
                    rollback_all_lambdas
                fi
                ;;
            "terraform"|"infrastructure")
                rollback_terraform
                ;;
            "frontend")
                rollback_frontend
                ;;
            "database")
                rollback_database
                ;;
            "all")
                rollback_all_lambdas
                rollback_frontend
                rollback_terraform
                ;;
            *)
                log_error "Unknown component: ${component}"
                echo ""
                echo "Usage: $0 [component] [options]"
                echo ""
                echo "Components:"
                echo "  lambda [name] [version]  - Rollback Lambda function(s)"
                echo "  terraform                - Rollback Terraform infrastructure"
                echo "  frontend                 - Rollback frontend deployment"
                echo "  database                 - Show database rollback info"
                echo "  all                      - Rollback all components"
                echo ""
                echo "Or run without arguments for interactive menu"
                exit 1
                ;;
        esac
    fi

    echo ""
    log_success "Rollback complete!"
    echo ""
}

# Run main function
main "$@"
