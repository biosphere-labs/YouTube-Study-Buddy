#!/bin/bash
# Build script for yt-study-buddy Lambda layer
# Creates a deployable Lambda layer with CLI and all dependencies

set -e  # Exit on error

echo "=========================================="
echo "  Building yt-study-buddy Lambda Layer"
echo "=========================================="

# Configuration
LAYER_NAME="cli-layer"
PYTHON_VERSION="3.13"
BUILD_DIR="build"
LAYER_DIR="${BUILD_DIR}/python"
OUTPUT_ZIP="${LAYER_NAME}.zip"

# Clean previous build
echo "Cleaning previous build..."
rm -rf ${BUILD_DIR}
rm -f ${OUTPUT_ZIP}

# Create layer directory structure
echo "Creating layer directory structure..."
mkdir -p ${LAYER_DIR}/lib/python${PYTHON_VERSION}/site-packages
mkdir -p ${BUILD_DIR}/bin

# Change to project root
cd "$(dirname "$0")/.."

# Install dependencies using uv in isolated environment
echo "Installing dependencies..."
python${PYTHON_VERSION} -m venv ${BUILD_DIR}/venv
source ${BUILD_DIR}/venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install the CLI and its dependencies
echo "Installing yt-study-buddy CLI..."
pip install -e . --target lambda-layer/${LAYER_DIR}/lib/python${PYTHON_VERSION}/site-packages

# Create CLI wrapper script for /opt/bin/
echo "Creating CLI wrapper..."
cat > lambda-layer/${BUILD_DIR}/bin/yt-study-buddy <<'EOF'
#!/opt/bin/python3.13
# -*- coding: utf-8 -*-
import sys
from yt_study_buddy.cli import main

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x lambda-layer/${BUILD_DIR}/bin/yt-study-buddy

# Optimize layer size
echo "Optimizing layer size..."
cd lambda-layer/${BUILD_DIR}

# Remove unnecessary files to reduce size
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "*.dist-info" -exec rm -rf {}/RECORD {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# Remove heavy ML model caches if present (sentence-transformers can be large)
find . -type d -name ".cache" -exec rm -rf {} + 2>/dev/null || true

# Create the zip file
echo "Creating layer zip file..."
zip -r ../${OUTPUT_ZIP} . -q

cd ..

# Show results
LAYER_SIZE=$(du -h ${OUTPUT_ZIP} | cut -f1)
echo ""
echo "=========================================="
echo "  Build Complete!"
echo "=========================================="
echo "Layer file: lambda-layer/${OUTPUT_ZIP}"
echo "Layer size: ${LAYER_SIZE}"
echo ""

# Check size constraint (Lambda layer limit is 250MB uncompressed, ~50MB compressed)
LAYER_SIZE_MB=$(stat -f%z ${OUTPUT_ZIP} 2>/dev/null || stat -c%s ${OUTPUT_ZIP})
LAYER_SIZE_MB=$((LAYER_SIZE_MB / 1024 / 1024))

if [ ${LAYER_SIZE_MB} -gt 50 ]; then
    echo "⚠️  WARNING: Layer size is ${LAYER_SIZE_MB}MB (>50MB)"
    echo "   Lambda layers have a 250MB uncompressed limit"
    echo "   Consider removing large dependencies"
else
    echo "✓ Layer size: ${LAYER_SIZE_MB}MB (within limits)"
fi

echo ""
echo "Next steps:"
echo "  1. Test locally: ./lambda-layer/test.sh"
echo "  2. Upload to AWS: ./lambda-layer/upload.sh"
echo "=========================================="
