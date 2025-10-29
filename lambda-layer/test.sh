#!/bin/bash
# Test script for yt-study-buddy Lambda layer
# Creates a test Lambda function and verifies the CLI works

set -e  # Exit on error

echo "=========================================="
echo "  Testing yt-study-buddy Lambda Layer"
echo "=========================================="

# Configuration
LAYER_NAME="yt-study-buddy-cli"
FUNCTION_NAME="yt-study-buddy-test"
AWS_REGION="${AWS_REGION:-us-east-1}"
TEST_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Sample YouTube URL

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI is not installed"
    exit 1
fi

# Check if layer ARN file exists
if [ ! -f "layer-arn.txt" ]; then
    echo "❌ ERROR: layer-arn.txt not found"
    echo "   Run ./upload.sh first to upload the layer"
    exit 1
fi

LAYER_ARN=$(cat layer-arn.txt)
echo "Layer ARN: ${LAYER_ARN}"
echo ""

# Create test Lambda function code
echo "Creating test Lambda function..."
cat > /tmp/lambda_test.py <<'EOF'
import json
import subprocess
import os

def lambda_handler(event, context):
    """Test Lambda function to verify yt-study-buddy CLI works."""

    # Test 1: Check if CLI is available
    try:
        result = subprocess.run(
            ['/opt/bin/yt-study-buddy', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'CLI failed',
                    'stderr': result.stderr
                })
            }

        cli_help = result.stdout

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'CLI execution failed',
                'message': str(e)
            })
        }

    # Test 2: Check Python imports
    try:
        import anthropic
        import youtube_transcript_api
        import loguru

        imports_ok = True
    except ImportError as e:
        imports_ok = False
        import_error = str(e)

    # Return results
    response = {
        'cli_available': True,
        'cli_help_preview': cli_help[:200] + '...' if len(cli_help) > 200 else cli_help,
        'imports_ok': imports_ok,
        'python_version': os.sys.version,
        'layer_working': True
    }

    if not imports_ok:
        response['import_error'] = import_error
        response['layer_working'] = False

    return {
        'statusCode': 200,
        'body': json.dumps(response, indent=2)
    }
EOF

# Zip the test function
cd /tmp
zip -q lambda_test.zip lambda_test.py
echo "✓ Test function created"
echo ""

# Check if function exists
FUNCTION_EXISTS=$(aws lambda list-functions \
    --region ${AWS_REGION} \
    --query "Functions[?FunctionName=='${FUNCTION_NAME}'].FunctionName" \
    --output text 2>/dev/null || echo "")

if [ -n "${FUNCTION_EXISTS}" ]; then
    echo "Updating existing function..."

    # Update function code
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --zip-file fileb:///tmp/lambda_test.zip \
        --region ${AWS_REGION} \
        --output json > /dev/null

    # Update function configuration with layer
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --layers ${LAYER_ARN} \
        --region ${AWS_REGION} \
        --output json > /dev/null

    echo "✓ Function updated"
else
    echo "Creating new function..."

    # Get AWS account ID for IAM role
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    IAM_ROLE="arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"

    # Create function
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --runtime python3.13 \
        --role ${IAM_ROLE} \
        --handler lambda_test.lambda_handler \
        --zip-file fileb:///tmp/lambda_test.zip \
        --layers ${LAYER_ARN} \
        --timeout 30 \
        --memory-size 512 \
        --region ${AWS_REGION} \
        --output json > /dev/null

    echo "✓ Function created"
fi

echo ""
echo "Waiting for function to be ready..."
sleep 3

# Invoke the test function
echo "Invoking test function..."
echo ""

aws lambda invoke \
    --function-name ${FUNCTION_NAME} \
    --region ${AWS_REGION} \
    --payload '{}' \
    /tmp/lambda_response.json > /dev/null

# Display results
echo "=========================================="
echo "  Test Results"
echo "=========================================="
cat /tmp/lambda_response.json | jq '.' || cat /tmp/lambda_response.json
echo ""

# Check if test passed
LAYER_WORKING=$(cat /tmp/lambda_response.json | jq -r '.body' | jq -r '.layer_working' 2>/dev/null || echo "false")

if [ "${LAYER_WORKING}" == "true" ]; then
    echo "✓ Lambda layer is working correctly!"
    echo ""
    echo "Next steps:"
    echo "  1. Use the layer in your Lambda functions"
    echo "  2. Set CLAUDE_API_KEY environment variable in your Lambda"
    echo "  3. Call the CLI from your Lambda handler"
else
    echo "❌ Lambda layer test failed"
    echo "   Check the error messages above"
fi

echo "=========================================="

# Cleanup
rm -f /tmp/lambda_test.py /tmp/lambda_test.zip /tmp/lambda_response.json
