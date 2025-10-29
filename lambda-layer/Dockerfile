# Dockerfile for building yt-study-buddy Lambda layer
# Builds in a consistent environment matching AWS Lambda runtime

FROM python:3.13-slim

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    zip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy project files
COPY . /build/

# Create layer directory structure
RUN mkdir -p /layer/python/lib/python3.13/site-packages && \
    mkdir -p /layer/bin

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . --target /layer/python/lib/python3.13/site-packages

# Create CLI wrapper script
RUN echo '#!/opt/bin/python3.13\n\
# -*- coding: utf-8 -*-\n\
import sys\n\
from yt_study_buddy.cli import main\n\
\n\
if __name__ == "__main__":\n\
    sys.exit(main())' > /layer/bin/yt-study-buddy && \
    chmod +x /layer/bin/yt-study-buddy

# Optimize layer size
RUN cd /layer && \
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete && \
    find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type d -name ".cache" -exec rm -rf {} + 2>/dev/null || true

# Create zip file
RUN cd /layer && \
    zip -r /build/cli-layer.zip . -q

# Set output directory
VOLUME ["/output"]

# Default command copies the zip to output
CMD ["sh", "-c", "cp /build/cli-layer.zip /output/ && ls -lh /output/cli-layer.zip"]
