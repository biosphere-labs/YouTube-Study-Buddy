#!/bin/bash
# Upload script for yt-study-buddy Lambda layer
# Deploys the layer to AWS Lambda

set -e  # Exit on error

echo "=========================================="
echo "  Uploading yt-study-buddy Lambda Layer"
echo "=========================================="

# Configuration
LAYER_NAME="yt-study-buddy-cli"
LAYER_ZIP="cli-layer.zip"
DESCRIPTION="YouTube Study Buddy CLI with dependencies (Python 3.13)"
COMPATIBLE_RUNTIMES="python3.13"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI is not installed"
    echo "   Install with: pip install awscli"
    exit 1
fi

# Check if layer zip exists
if [ ! -f "${LAYER_ZIP}" ]; then
    echo "❌ ERROR: Layer zip file not found: ${LAYER_ZIP}"
    echo "   Run ./build.sh first to create the layer"
    exit 1
fi

# Get layer size
LAYER_SIZE=$(du -h ${LAYER_ZIP} | cut -f1)
echo "Layer file: ${LAYER_ZIP}"
echo "Layer size: ${LAYER_SIZE}"
echo "AWS Region: ${AWS_REGION}"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ ERROR: AWS credentials not configured"
    echo "   Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account: ${ACCOUNT_ID}"
echo ""

# Publish layer
echo "Publishing Lambda layer..."
PUBLISH_OUTPUT=$(aws lambda publish-layer-version \
    --layer-name "${LAYER_NAME}" \
    --description "${DESCRIPTION}" \
    --zip-file "fileb://${LAYER_ZIP}" \
    --compatible-runtimes ${COMPATIBLE_RUNTIMES} \
    --region ${AWS_REGION} \
    --output json)

# Extract layer ARN and version
LAYER_ARN=$(echo ${PUBLISH_OUTPUT} | jq -r '.LayerArn')
LAYER_VERSION=$(echo ${PUBLISH_OUTPUT} | jq -r '.Version')
LAYER_VERSION_ARN=$(echo ${PUBLISH_OUTPUT} | jq -r '.LayerVersionArn')

echo ""
echo "=========================================="
echo "  Upload Complete!"
echo "=========================================="
echo "Layer Name: ${LAYER_NAME}"
echo "Layer Version: ${LAYER_VERSION}"
echo "Layer ARN: ${LAYER_ARN}"
echo ""
echo "Layer Version ARN:"
echo "${LAYER_VERSION_ARN}"
echo ""
echo "To use this layer in your Lambda function:"
echo ""
echo "1. Via AWS Console:"
echo "   - Go to your Lambda function"
echo "   - Click 'Layers' -> 'Add a layer'"
echo "   - Select 'Custom layers' and choose '${LAYER_NAME}'"
echo ""
echo "2. Via AWS CLI:"
echo "   aws lambda update-function-configuration \\"
echo "     --function-name YOUR_FUNCTION_NAME \\"
echo "     --layers ${LAYER_VERSION_ARN}"
echo ""
echo "3. In your Lambda function code:"
echo "   import subprocess"
echo "   result = subprocess.run(['/opt/bin/yt-study-buddy', '--help'], capture_output=True)"
echo ""
echo "=========================================="

# Save ARN to file for easy reference
echo "${LAYER_VERSION_ARN}" > layer-arn.txt
echo "✓ Layer ARN saved to: layer-arn.txt"
