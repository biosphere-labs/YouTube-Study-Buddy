#!/bin/bash
# Build Lambda layer with YouTube Study Buddy CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LAYER_DIR="$SCRIPT_DIR/../lambda_layers"
BUILD_DIR="$LAYER_DIR/python"

echo "Building Lambda layer..."

# Create directories
mkdir -p "$BUILD_DIR"
mkdir -p "$LAYER_DIR"

# Clean previous build
rm -rf "$BUILD_DIR"/*
rm -f "$LAYER_DIR/cli_layer.zip"

echo "Installing dependencies..."

# Install YouTube Study Buddy CLI and dependencies
cd "$PROJECT_ROOT"

# Create a temporary virtual environment
python3.13 -m venv "$BUILD_DIR/.venv"
source "$BUILD_DIR/.venv/bin/activate"

# Install dependencies
uv pip install --target "$BUILD_DIR" \
    anthropic \
    youtube-transcript-api \
    yt-dlp \
    sentence-transformers \
    scikit-learn \
    numpy \
    rich \
    pyyaml

# Install the CLI package
uv pip install --target "$BUILD_DIR" -e .

# Clean up unnecessary files
cd "$BUILD_DIR"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Remove the temporary venv
rm -rf .venv

echo "Creating ZIP archive..."

# Create ZIP file
cd "$LAYER_DIR"
zip -r cli_layer.zip python -x "*.pyc" "*__pycache__*"

# Get size
SIZE=$(du -h cli_layer.zip | cut -f1)
echo "Lambda layer created: cli_layer.zip ($SIZE)"

# Check size limit (250MB uncompressed, 50MB compressed)
UNCOMPRESSED=$(unzip -l cli_layer.zip | tail -1 | awk '{print $1}')
if [ "$UNCOMPRESSED" -gt 262144000 ]; then
    echo "WARNING: Layer size ($UNCOMPRESSED bytes) exceeds 250MB uncompressed limit"
fi

echo "Build complete!"
