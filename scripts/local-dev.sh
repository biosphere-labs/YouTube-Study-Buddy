#!/bin/bash
# Local development setup for serverless Lambda functions
# Uses AWS SAM Local or LocalStack to run Lambda functions locally

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="${PROJECT_ROOT}/lambda"
LOCAL_PORT="${LOCAL_PORT:-3001}"
LOCAL_DYNAMO_PORT="${LOCAL_DYNAMO_PORT:-8000}"
MODE="${MODE:-sam}"  # sam or localstack

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

    local missing=()

    if [ "$MODE" = "sam" ]; then
        if ! command -v sam &> /dev/null; then
            missing+=("aws-sam-cli")
        fi
    elif [ "$MODE" = "localstack" ]; then
        if ! command -v localstack &> /dev/null; then
            missing+=("localstack")
        fi
        if ! command -v awslocal &> /dev/null; then
            missing+=("awscli-local")
        fi
    fi

    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi

    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        echo ""
        echo "Install instructions:"
        echo "  aws-sam-cli:    pip install aws-sam-cli"
        echo "  localstack:     pip install localstack"
        echo "  awscli-local:   pip install awscli-local"
        echo "  docker:         https://docs.docker.com/get-docker/"
        echo ""
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create SAM template
create_sam_template() {
    log_info "Creating SAM template..."

    local template_file="${PROJECT_ROOT}/template.yaml"

    cat > "$template_file" <<'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: YouTube Study Buddy - Local Development

Globals:
  Function:
    Timeout: 900
    MemorySize: 2048
    Runtime: python3.13
    Environment:
      Variables:
        DYNAMODB_ENDPOINT: http://host.docker.internal:8000
        AWS_REGION: us-east-1
        ENVIRONMENT: local

Resources:
  SubmitVideoFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/submit_video/
      Handler: index.handler
      Events:
        SubmitVideo:
          Type: Api
          Properties:
            Path: /videos/submit
            Method: post

  ProcessVideoFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/process_video/
      Handler: index.handler
      Layers:
        - !Ref CliLayer
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt VideoQueue.Arn
            BatchSize: 1

  GetVideoFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/get_video/
      Handler: index.handler
      Events:
        GetVideo:
          Type: Api
          Properties:
            Path: /videos/{video_id}
            Method: get

  ListVideosFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/list_videos/
      Handler: index.handler
      Events:
        ListVideos:
          Type: Api
          Properties:
            Path: /videos
            Method: get

  GetNoteFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/get_note/
      Handler: index.handler
      Events:
        GetNote:
          Type: Api
          Properties:
            Path: /notes/{note_id}
            Method: get

  PurchaseCreditsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/purchase_credits/
      Handler: index.handler
      Events:
        PurchaseCredits:
          Type: Api
          Properties:
            Path: /credits/purchase
            Method: post

  StripeWebhookFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/stripe_webhook/
      Handler: index.handler
      Events:
        StripeWebhook:
          Type: Api
          Properties:
            Path: /webhooks/stripe
            Method: post

  CliLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      ContentUri: lambda-layer/cli-layer.zip
      CompatibleRuntimes:
        - python3.13

  VideoQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: ytstudy-videos-local
      VisibilityTimeout: 900

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
EOF

    log_success "SAM template created: ${template_file}"
}

# Start DynamoDB Local
start_dynamodb_local() {
    log_info "Starting DynamoDB Local on port ${LOCAL_DYNAMO_PORT}..."

    # Check if already running
    if lsof -Pi :${LOCAL_DYNAMO_PORT} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        log_warning "DynamoDB Local already running on port ${LOCAL_DYNAMO_PORT}"
        return 0
    fi

    # Start DynamoDB Local with Docker
    docker run -d \
        --name ytstudy-dynamodb-local \
        -p ${LOCAL_DYNAMO_PORT}:8000 \
        amazon/dynamodb-local \
        -jar DynamoDBLocal.jar -sharedDb -inMemory \
        > /dev/null 2>&1 || true

    # Wait for DynamoDB to be ready
    log_info "Waiting for DynamoDB Local to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:${LOCAL_DYNAMO_PORT} > /dev/null 2>&1; then
            log_success "DynamoDB Local is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    log_error "DynamoDB Local failed to start"
    return 1
}

# Create local DynamoDB tables
create_local_tables() {
    log_info "Creating local DynamoDB tables..."

    local endpoint="http://localhost:${LOCAL_DYNAMO_PORT}"

    # Users table
    aws dynamodb create-table \
        --table-name ytstudy-users-local \
        --attribute-definitions \
            AttributeName=user_id,AttributeType=S \
        --key-schema \
            AttributeName=user_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url "$endpoint" \
        --region us-east-1 \
        > /dev/null 2>&1 || log_warning "Users table may already exist"

    # Videos table
    aws dynamodb create-table \
        --table-name ytstudy-videos-local \
        --attribute-definitions \
            AttributeName=video_id,AttributeType=S \
            AttributeName=user_id,AttributeType=S \
            AttributeName=created_at,AttributeType=S \
        --key-schema \
            AttributeName=video_id,KeyType=HASH \
        --global-secondary-indexes \
            "IndexName=user_id-created_at-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url "$endpoint" \
        --region us-east-1 \
        > /dev/null 2>&1 || log_warning "Videos table may already exist"

    # Notes table
    aws dynamodb create-table \
        --table-name ytstudy-notes-local \
        --attribute-definitions \
            AttributeName=note_id,AttributeType=S \
            AttributeName=user_id,AttributeType=S \
            AttributeName=created_at,AttributeType=S \
        --key-schema \
            AttributeName=note_id,KeyType=HASH \
        --global-secondary-indexes \
            "IndexName=user_id-created_at-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url "$endpoint" \
        --region us-east-1 \
        > /dev/null 2>&1 || log_warning "Notes table may already exist"

    log_success "DynamoDB tables created"
}

# Start SAM Local
start_sam_local() {
    log_info "Starting SAM Local API on port ${LOCAL_PORT}..."

    cd "$PROJECT_ROOT"

    # Load environment variables
    local env_file="${PROJECT_ROOT}/.env.local"
    if [ -f "$env_file" ]; then
        log_info "Loading environment from ${env_file}"
        export $(grep -v '^#' "$env_file" | xargs)
    fi

    log_info "Starting SAM Local API..."
    log_info "API will be available at: http://localhost:${LOCAL_PORT}"
    echo ""

    sam local start-api \
        --port ${LOCAL_PORT} \
        --warm-containers EAGER \
        --docker-network host

    # This blocks until interrupted
}

# Start LocalStack
start_localstack() {
    log_info "Starting LocalStack..."

    # Check if already running
    if docker ps | grep -q localstack; then
        log_warning "LocalStack already running"
        docker logs -f localstack
        return 0
    fi

    # Start LocalStack
    docker run -d \
        --name localstack \
        -p 4566:4566 \
        -p 4571:4571 \
        -e SERVICES=lambda,dynamodb,s3,sqs,apigateway,cognito-idp \
        -e DEBUG=1 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        localstack/localstack

    log_info "Waiting for LocalStack to be ready..."
    sleep 10

    log_success "LocalStack started"
    log_info "Dashboard: http://localhost:4566/_localstack/health"

    # Follow logs
    docker logs -f localstack
}

# Stop local services
stop_local_services() {
    log_info "Stopping local services..."

    # Stop DynamoDB Local
    docker stop ytstudy-dynamodb-local 2>/dev/null || true
    docker rm ytstudy-dynamodb-local 2>/dev/null || true

    # Stop LocalStack
    docker stop localstack 2>/dev/null || true
    docker rm localstack 2>/dev/null || true

    log_success "Local services stopped"
}

# Show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start local development environment (default)"
    echo "  stop        - Stop all local services"
    echo "  restart     - Restart local services"
    echo "  logs        - Show logs from running services"
    echo "  tables      - Create DynamoDB tables"
    echo ""
    echo "Environment Variables:"
    echo "  MODE              - Development mode (sam|localstack) [default: sam]"
    echo "  LOCAL_PORT        - API port [default: 3001]"
    echo "  LOCAL_DYNAMO_PORT - DynamoDB port [default: 8000]"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  MODE=localstack $0 start"
    echo "  LOCAL_PORT=4000 $0 start"
}

# Main script
main() {
    local command=${1:-start}

    case "$command" in
        "start")
            echo ""
            echo "=========================================="
            echo "  Local Development Environment"
            echo "  Mode: ${MODE}"
            echo "=========================================="
            echo ""

            check_prerequisites

            if [ "$MODE" = "sam" ]; then
                # Build Lambda layer if needed
                if [ ! -f "${PROJECT_ROOT}/lambda-layer/cli-layer.zip" ]; then
                    log_warning "Lambda layer not found, building..."
                    bash "${PROJECT_ROOT}/lambda-layer/build.sh"
                fi

                create_sam_template
                start_dynamodb_local
                create_local_tables

                echo ""
                log_info "Local environment ready!"
                log_info "DynamoDB: http://localhost:${LOCAL_DYNAMO_PORT}"
                log_info "API will start on: http://localhost:${LOCAL_PORT}"
                echo ""
                log_info "Press Ctrl+C to stop"
                echo ""

                start_sam_local
            elif [ "$MODE" = "localstack" ]; then
                start_localstack
            fi
            ;;

        "stop")
            stop_local_services
            ;;

        "restart")
            stop_local_services
            sleep 2
            main start
            ;;

        "logs")
            if [ "$MODE" = "sam" ]; then
                docker logs -f ytstudy-dynamodb-local
            else
                docker logs -f localstack
            fi
            ;;

        "tables")
            start_dynamodb_local
            create_local_tables
            ;;

        "help"|"--help"|"-h")
            show_usage
            ;;

        *)
            log_error "Unknown command: ${command}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Cleanup on exit
cleanup() {
    log_info "Cleaning up..."
    # Don't stop services on exit, user can manually stop
}

trap cleanup EXIT

# Run main function
main "$@"
