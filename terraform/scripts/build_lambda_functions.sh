#!/bin/bash
# Build all Lambda function packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMBDA_DIR="$SCRIPT_DIR/../lambda_functions"

echo "Building Lambda functions..."

# Create lambda_functions directory
mkdir -p "$LAMBDA_DIR"

# Array of Lambda function names
FUNCTIONS=(
    "auth_register"
    "auth_login"
    "auth_refresh"
    "auth_verify"
    "videos_submit"
    "videos_list"
    "videos_get"
    "videos_delete"
    "videos_process"
    "notes_get"
    "notes_list"
    "notes_download"
    "credits_get"
    "credits_history"
    "credits_checkout"
    "credits_webhook"
    "user_get"
    "user_update"
)

# Build each function
for FUNC in "${FUNCTIONS[@]}"; do
    echo "Building $FUNC..."

    BUILD_DIR="$LAMBDA_DIR/${FUNC}_build"
    mkdir -p "$BUILD_DIR"

    # Create handler.py (placeholder - replace with actual implementation)
    cat > "$BUILD_DIR/handler.py" << 'EOF'
"""
Lambda function handler
This is a placeholder - replace with actual implementation
"""
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda handler function
    """
    logger.info(f"Event: {json.dumps(event)}")

    # TODO: Implement actual handler logic

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'message': 'Function not yet implemented',
            'function': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
        })
    }
EOF

    # Create requirements.txt for functions that need dependencies
    if [[ "$FUNC" == "videos_process" ]]; then
        # This function uses the CLI layer
        cat > "$BUILD_DIR/requirements.txt" << 'EOF'
# Dependencies are provided by Lambda layer
EOF
    else
        # Standard dependencies for API handlers
        cat > "$BUILD_DIR/requirements.txt" << 'EOF'
boto3>=1.28.0
botocore>=1.31.0
EOF
    fi

    # Install dependencies if needed
    if [ -s "$BUILD_DIR/requirements.txt" ]; then
        pip install -r "$BUILD_DIR/requirements.txt" -t "$BUILD_DIR" --quiet
    fi

    # Clean up
    cd "$BUILD_DIR"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

    # Create ZIP
    zip -r "../${FUNC}.zip" . -q

    # Clean up build directory
    cd ..
    rm -rf "${FUNC}_build"

    SIZE=$(du -h "${FUNC}.zip" | cut -f1)
    echo "  ✓ Created ${FUNC}.zip ($SIZE)"
done

echo ""
echo "All Lambda functions built successfully!"
echo ""
echo "Next steps:"
echo "1. Implement actual handler logic in each function"
echo "2. Run 'terraform plan' to verify configuration"
echo "3. Run 'terraform apply' to deploy"
