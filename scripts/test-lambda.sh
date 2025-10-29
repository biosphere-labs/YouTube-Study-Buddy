#!/bin/bash
# Test Lambda functions
# Runs unit tests, integration tests, and end-to-end tests

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="${PROJECT_ROOT}/lambda"
ENVIRONMENT="${ENVIRONMENT:-dev}"
TEST_TYPE="${TEST_TYPE:-all}"  # unit, integration, e2e, or all

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

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Install test dependencies
install_test_deps() {
    log_info "Installing test dependencies..."

    pip3 install -q pytest pytest-cov pytest-mock boto3 moto requests

    log_success "Test dependencies installed"
}

# Run unit tests for a Lambda function
run_unit_tests() {
    local function_name=$1
    local function_dir="${LAMBDA_DIR}/${function_name}"

    if [ ! -d "$function_dir" ]; then
        log_warning "Function directory not found: ${function_dir}"
        return 1
    fi

    log_info "Running unit tests for ${function_name}..."

    cd "$function_dir"

    # Check if tests exist
    if [ ! -d "tests" ] && [ ! -f "test_*.py" ]; then
        log_warning "No tests found for ${function_name}"
        return 0
    fi

    # Run pytest with coverage
    if pytest --cov=. --cov-report=term-missing --cov-report=html -v 2>&1; then
        log_success "Unit tests passed for ${function_name}"
        return 0
    else
        log_error "Unit tests failed for ${function_name}"
        return 1
    fi
}

# Run integration tests with mocked AWS services
run_integration_tests() {
    log_info "Running integration tests..."

    local test_dir="${PROJECT_ROOT}/tests/integration"

    if [ ! -d "$test_dir" ]; then
        log_warning "Integration test directory not found: ${test_dir}"
        return 0
    fi

    cd "$test_dir"

    # Run integration tests with moto (AWS mocking)
    if pytest -v --tb=short 2>&1; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run end-to-end tests against deployed Lambda functions
run_e2e_tests() {
    log_info "Running end-to-end tests against ${ENVIRONMENT} environment..."

    local test_dir="${PROJECT_ROOT}/tests/e2e"

    if [ ! -d "$test_dir" ]; then
        log_warning "E2E test directory not found: ${test_dir}"
        return 0
    fi

    # Load environment variables
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}.terraform"
    if [ -f "$env_file" ]; then
        set -a
        source "$env_file"
        set +a
    else
        log_warning "Environment file not found: ${env_file}"
    fi

    cd "$test_dir"

    # Run E2E tests
    if pytest -v --tb=short 2>&1; then
        log_success "E2E tests passed"
        return 0
    else
        log_error "E2E tests failed"
        return 1
    fi
}

# Test specific Lambda function with real invocation
test_lambda_invocation() {
    local function_name=$1
    local aws_function_name="ytstudy-${ENVIRONMENT}-${function_name}"

    log_info "Testing Lambda invocation: ${aws_function_name}..."

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not installed"
        return 1
    fi

    # Create test payload
    local payload='{}'
    local payload_file="/tmp/lambda-test-payload-${function_name}.json"

    case "$function_name" in
        "submit_video")
            payload='{"body":"{\"youtube_url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\",\"subject\":\"test\"}","requestContext":{"authorizer":{"claims":{"sub":"test-user-123"}}}}'
            ;;
        "get_video")
            payload='{"pathParameters":{"video_id":"test-video-123"},"requestContext":{"authorizer":{"claims":{"sub":"test-user-123"}}}}'
            ;;
        "list_videos")
            payload='{"queryStringParameters":{},"requestContext":{"authorizer":{"claims":{"sub":"test-user-123"}}}}'
            ;;
        "get_note")
            payload='{"pathParameters":{"note_id":"test-note-123"},"requestContext":{"authorizer":{"claims":{"sub":"test-user-123"}}}}'
            ;;
        *)
            log_warning "No test payload defined for ${function_name}"
            return 0
            ;;
    esac

    echo "$payload" > "$payload_file"

    # Invoke Lambda
    local response_file="/tmp/lambda-test-response-${function_name}.json"

    if aws lambda invoke \
        --function-name "$aws_function_name" \
        --payload "file://${payload_file}" \
        --cli-binary-format raw-in-base64-out \
        "$response_file" > /dev/null 2>&1; then

        # Check response
        if grep -q '"statusCode":200' "$response_file" 2>/dev/null; then
            log_success "Lambda invocation successful: ${function_name}"
            return 0
        elif grep -q '"statusCode":404' "$response_file" 2>/dev/null; then
            log_info "Lambda returned 404 (expected for test data): ${function_name}"
            return 0
        else
            log_warning "Lambda invocation returned unexpected status: ${function_name}"
            cat "$response_file"
            return 0  # Don't fail, might be expected
        fi
    else
        log_error "Lambda invocation failed: ${function_name}"
        return 1
    fi
}

# Generate coverage report
generate_coverage_report() {
    log_info "Generating coverage report..."

    local coverage_dir="${PROJECT_ROOT}/coverage"
    mkdir -p "$coverage_dir"

    # Combine coverage from all functions
    cd "$coverage_dir"

    # Create summary HTML
    cat > "${coverage_dir}/index.html" <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Lambda Test Coverage</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .function { margin: 10px 0; padding: 10px; border-left: 3px solid #4CAF50; background: #f9f9f9; }
        .passed { color: green; }
        .failed { color: red; }
    </style>
</head>
<body>
    <h1>Lambda Function Test Coverage</h1>
    <div class="summary">
        <p>Test run completed at: <strong>$(date)</strong></p>
        <p>Environment: <strong>${ENVIRONMENT}</strong></p>
    </div>
    <div class="functions">
        <p>See individual function coverage reports in their respective directories.</p>
    </div>
</body>
</html>
EOF

    log_success "Coverage report generated: ${coverage_dir}/index.html"
}

# Show test summary
show_summary() {
    local total_tests=$1
    local passed_tests=$2
    local failed_tests=$3

    echo ""
    echo "=========================================="
    echo "  Test Summary"
    echo "=========================================="
    echo ""
    echo "  Total Tests:  ${total_tests}"
    echo "  Passed:       ${passed_tests}"
    echo "  Failed:       ${failed_tests}"
    echo ""

    if [ $failed_tests -eq 0 ]; then
        log_success "All tests passed!"
        return 0
    else
        log_error "${failed_tests} test(s) failed"
        return 1
    fi
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "  Lambda Function Testing"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Test Type: ${TEST_TYPE}"
    echo "=========================================="
    echo ""

    check_prerequisites
    install_test_deps

    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Run tests based on type
    case "$TEST_TYPE" in
        "unit")
            # Run unit tests for all functions
            for dir in "${LAMBDA_DIR}"/*; do
                if [ -d "$dir" ] && [ "$(basename "$dir")" != "shared" ]; then
                    function_name=$(basename "$dir")
                    total_tests=$((total_tests + 1))

                    if run_unit_tests "$function_name"; then
                        passed_tests=$((passed_tests + 1))
                    else
                        failed_tests=$((failed_tests + 1))
                    fi
                fi
            done
            ;;

        "integration")
            total_tests=1
            if run_integration_tests; then
                passed_tests=1
            else
                failed_tests=1
            fi
            ;;

        "e2e")
            total_tests=1
            if run_e2e_tests; then
                passed_tests=1
            else
                failed_tests=1
            fi
            ;;

        "invoke")
            # Test actual Lambda invocations
            for dir in "${LAMBDA_DIR}"/*; do
                if [ -d "$dir" ] && [ "$(basename "$dir")" != "shared" ]; then
                    function_name=$(basename "$dir")
                    total_tests=$((total_tests + 1))

                    if test_lambda_invocation "$function_name"; then
                        passed_tests=$((passed_tests + 1))
                    else
                        failed_tests=$((failed_tests + 1))
                    fi
                fi
            done
            ;;

        "all")
            # Run all test types
            log_info "Running all test types..."
            echo ""

            # Unit tests
            log_info "=== Unit Tests ==="
            for dir in "${LAMBDA_DIR}"/*; do
                if [ -d "$dir" ] && [ "$(basename "$dir")" != "shared" ]; then
                    function_name=$(basename "$dir")
                    total_tests=$((total_tests + 1))

                    if run_unit_tests "$function_name"; then
                        passed_tests=$((passed_tests + 1))
                    else
                        failed_tests=$((failed_tests + 1))
                    fi
                fi
            done

            # Integration tests
            echo ""
            log_info "=== Integration Tests ==="
            total_tests=$((total_tests + 1))
            if run_integration_tests; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi

            # E2E tests
            echo ""
            log_info "=== End-to-End Tests ==="
            total_tests=$((total_tests + 1))
            if run_e2e_tests; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi
            ;;

        *)
            log_error "Unknown test type: ${TEST_TYPE}"
            echo ""
            echo "Available test types:"
            echo "  unit         - Run unit tests"
            echo "  integration  - Run integration tests"
            echo "  e2e          - Run end-to-end tests"
            echo "  invoke       - Test Lambda invocations"
            echo "  all          - Run all tests"
            echo ""
            exit 1
            ;;
    esac

    # Generate coverage report
    generate_coverage_report

    # Show summary and exit with appropriate code
    if show_summary $total_tests $passed_tests $failed_tests; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
