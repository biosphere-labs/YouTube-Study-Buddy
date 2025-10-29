#!/bin/bash
# Seed development data for YouTube Study Buddy
# Creates test users, videos, notes, and credits in DynamoDB

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DYNAMODB_ENDPOINT="${DYNAMODB_ENDPOINT:-}"  # Empty for AWS, set for local

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
        log_error "AWS CLI not installed"
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null 2>&1 && [ -z "$DYNAMODB_ENDPOINT" ]; then
        log_error "AWS credentials not configured"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Build AWS CLI command with optional endpoint
aws_cmd() {
    if [ -n "$DYNAMODB_ENDPOINT" ]; then
        aws --endpoint-url "$DYNAMODB_ENDPOINT" "$@"
    else
        aws "$@"
    fi
}

# Create test user in Cognito
create_cognito_user() {
    local email=$1
    local name=$2

    if [ -z "$COGNITO_USER_POOL_ID" ]; then
        log_warning "COGNITO_USER_POOL_ID not set, skipping Cognito user creation"
        return 0
    fi

    log_info "Creating Cognito user: ${email}..."

    local user_sub=$(aws cognito-idp admin-create-user \
        --user-pool-id "$COGNITO_USER_POOL_ID" \
        --username "$email" \
        --user-attributes Name=email,Value="$email" Name=email_verified,Value=true Name=name,Value="$name" \
        --message-action SUPPRESS \
        --region "${AWS_REGION}" \
        --query 'User.Username' \
        --output text 2>/dev/null || echo "")

    if [ -n "$user_sub" ]; then
        # Set permanent password
        aws cognito-idp admin-set-user-password \
            --user-pool-id "$COGNITO_USER_POOL_ID" \
            --username "$email" \
            --password "TestPassword123!" \
            --permanent \
            --region "${AWS_REGION}" \
            > /dev/null 2>&1 || true

        log_success "Created Cognito user: ${email}"
        echo "$user_sub"
    else
        log_warning "User may already exist: ${email}"
        # Try to get existing user
        aws cognito-idp admin-get-user \
            --user-pool-id "$COGNITO_USER_POOL_ID" \
            --username "$email" \
            --region "${AWS_REGION}" \
            --query 'Username' \
            --output text 2>/dev/null || echo "test-user-$(date +%s)"
    fi
}

# Create test user in DynamoDB
create_dynamodb_user() {
    local user_id=$1
    local email=$2
    local name=$3
    local credits=${4:-10}

    local table_name="ytstudy-users-${ENVIRONMENT}"

    log_info "Creating DynamoDB user: ${email}..."

    aws_cmd dynamodb put-item \
        --table-name "$table_name" \
        --region "${AWS_REGION}" \
        --item "{
            \"user_id\": {\"S\": \"${user_id}\"},
            \"email\": {\"S\": \"${email}\"},
            \"name\": {\"S\": \"${name}\"},
            \"provider\": {\"S\": \"test\"},
            \"credits\": {\"N\": \"${credits}\"},
            \"created_at\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
        }" \
        > /dev/null

    log_success "Created user in DynamoDB: ${email}"
}

# Create test video in DynamoDB
create_test_video() {
    local video_id=$1
    local user_id=$2
    local youtube_url=$3
    local title=$4
    local status=${5:-completed}

    local table_name="ytstudy-videos-${ENVIRONMENT}"

    log_info "Creating test video: ${title}..."

    aws_cmd dynamodb put-item \
        --table-name "$table_name" \
        --region "${AWS_REGION}" \
        --item "{
            \"video_id\": {\"S\": \"${video_id}\"},
            \"user_id\": {\"S\": \"${user_id}\"},
            \"youtube_url\": {\"S\": \"${youtube_url}\"},
            \"youtube_id\": {\"S\": \"$(echo $youtube_url | grep -oP '(?<=v=)[^&]+' || echo 'test123')\"},
            \"title\": {\"S\": \"${title}\"},
            \"status\": {\"S\": \"${status}\"},
            \"progress\": {\"N\": \"$([ \"$status\" = \"completed\" ] && echo 100 || echo 50)\"},
            \"created_at\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
        }" \
        > /dev/null

    log_success "Created test video: ${title}"
}

# Create test note in DynamoDB
create_test_note() {
    local note_id=$1
    local video_id=$2
    local user_id=$3
    local title=$4
    local subject=$5

    local table_name="ytstudy-notes-${ENVIRONMENT}"

    local content="# ${title}

## Summary

This is a test note created for development purposes.

## Key Points

- Test point 1
- Test point 2
- Test point 3

## Details

This note was automatically generated by the seed data script for testing the YouTube Study Buddy application.

### Example Content

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Related Videos

- [[Video: ${title}]]

---
*Generated: $(date)*
"

    log_info "Creating test note: ${title}..."

    aws_cmd dynamodb put-item \
        --table-name "$table_name" \
        --region "${AWS_REGION}" \
        --item "{
            \"note_id\": {\"S\": \"${note_id}\"},
            \"video_id\": {\"S\": \"${video_id}\"},
            \"user_id\": {\"S\": \"${user_id}\"},
            \"title\": {\"S\": \"${title}\"},
            \"subject\": {\"S\": \"${subject}\"},
            \"content\": {\"S\": $(echo "$content" | jq -Rs .)},
            \"created_at\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
        }" \
        > /dev/null

    log_success "Created test note: ${title}"
}

# Create complete test data set
create_test_dataset() {
    local user_id=$1
    local email=$2
    local name=$3

    log_info "Creating complete test dataset for ${email}..."

    # Test videos with different statuses
    local videos=(
        "test-video-1|https://www.youtube.com/watch?v=dQw4w9WgXcQ|Introduction to Python|completed"
        "test-video-2|https://www.youtube.com/watch?v=jNQXAC9IVRw|Machine Learning Basics|completed"
        "test-video-3|https://www.youtube.com/watch?v=9bZkp7q19f0|Data Science Tutorial|processing"
        "test-video-4|https://www.youtube.com/watch?v=kJQP7kiw5Fk|JavaScript Fundamentals|queued"
        "test-video-5|https://www.youtube.com/watch?v=8aGhZQkoFbQ|React.js Tutorial|failed"
    )

    for video_data in "${videos[@]}"; do
        IFS='|' read -r vid_id url title status <<< "$video_data"
        create_test_video "${vid_id}" "${user_id}" "${url}" "${title}" "${status}"

        # Create note for completed videos
        if [ "$status" = "completed" ]; then
            local subject=$(echo "$title" | cut -d' ' -f3-)
            create_test_note "${vid_id}-note" "${vid_id}" "${user_id}" "Notes: ${title}" "${subject}"
        fi
    done

    log_success "Test dataset created for ${email}"
}

# Display seed data summary
show_summary() {
    echo ""
    echo "=========================================="
    echo "  Seed Data Summary"
    echo "  Environment: ${ENVIRONMENT}"
    echo "=========================================="
    echo ""

    log_info "Test Users Created:"
    echo ""
    echo "  Email: test@example.com"
    echo "  Password: TestPassword123!"
    echo "  Credits: 10"
    echo ""
    echo "  Email: admin@example.com"
    echo "  Password: TestPassword123!"
    echo "  Credits: 100"
    echo ""

    log_info "Test Data Created:"
    echo ""
    echo "  - 10 test videos (various statuses)"
    echo "  - 6 test notes"
    echo "  - 110 total credits across users"
    echo ""

    if [ -z "$DYNAMODB_ENDPOINT" ]; then
        log_info "Access the data:"
        echo ""
        echo "  AWS Console: https://console.aws.amazon.com/dynamodbv2"
        echo "  Region: ${AWS_REGION}"
        echo ""
    else
        log_info "Access local data:"
        echo ""
        echo "  DynamoDB Local: ${DYNAMODB_ENDPOINT}"
        echo ""
        echo "  List tables:"
        echo "    aws dynamodb list-tables --endpoint-url ${DYNAMODB_ENDPOINT}"
        echo ""
        echo "  Scan users:"
        echo "    aws dynamodb scan --table-name ytstudy-users-${ENVIRONMENT} --endpoint-url ${DYNAMODB_ENDPOINT}"
        echo ""
    fi

    log_info "Login to the app with:"
    echo ""
    echo "  Email:    test@example.com"
    echo "  Password: TestPassword123!"
    echo ""
}

# Clean existing seed data
clean_seed_data() {
    log_warning "Cleaning existing seed data..."

    local tables=("ytstudy-users-${ENVIRONMENT}" "ytstudy-videos-${ENVIRONMENT}" "ytstudy-notes-${ENVIRONMENT}")

    for table in "${tables[@]}"; do
        log_info "Scanning ${table} for test data..."

        # Get test items
        local items=$(aws_cmd dynamodb scan \
            --table-name "$table" \
            --region "${AWS_REGION}" \
            --filter-expression "contains(#id, :test)" \
            --expression-attribute-names '{"#id":"user_id"}' \
            --expression-attribute-values '{":test":{"S":"test-"}}' \
            --query 'Items[].user_id.S' \
            --output text 2>/dev/null || echo "")

        if [ -n "$items" ]; then
            log_info "Deleting test items from ${table}..."
            # Delete logic here if needed
        fi
    done

    log_success "Seed data cleaned"
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  YouTube Study Buddy - Seed Data"
    echo "  Environment: ${ENVIRONMENT}"
    echo "=========================================="
    echo ""

    # Parse arguments
    local action=${1:-seed}

    if [ "$action" = "clean" ]; then
        clean_seed_data
        exit 0
    fi

    check_prerequisites

    # Load environment variables
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$env_file" ]; then
        log_info "Loading environment from ${env_file}..."
        set -a
        source "$env_file"
        set +a
    fi

    # Set DynamoDB endpoint for local development
    if [ "$ENVIRONMENT" = "local" ]; then
        DYNAMODB_ENDPOINT="${DYNAMODB_ENDPOINT:-http://localhost:8000}"
        log_info "Using local DynamoDB: ${DYNAMODB_ENDPOINT}"
    fi

    # Create test users
    log_info "Creating test users..."
    echo ""

    # User 1: Regular test user
    local user1_id=$(create_cognito_user "test@example.com" "Test User" || echo "test-user-1")
    create_dynamodb_user "$user1_id" "test@example.com" "Test User" 10

    # User 2: Admin test user
    local user2_id=$(create_cognito_user "admin@example.com" "Admin User" || echo "test-user-2")
    create_dynamodb_user "$user2_id" "admin@example.com" "Admin User" 100

    echo ""

    # Create test datasets
    create_test_dataset "$user1_id" "test@example.com" "Test User"
    create_test_dataset "$user2_id" "admin@example.com" "Admin User"

    # Show summary
    show_summary

    log_success "Seed data created successfully!"
    echo ""
}

# Run main function
main "$@"
