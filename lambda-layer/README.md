# AWS Lambda Layer for yt-study-buddy CLI

This directory contains scripts to build, upload, and test an AWS Lambda layer that packages the yt-study-buddy CLI and all its dependencies.

## Overview

The Lambda layer provides:
- **yt-study-buddy CLI** - Fully functional CLI accessible at `/opt/bin/yt-study-buddy`
- **All dependencies** - anthropic, youtube-transcript-api, sentence-transformers, etc.
- **Python 3.13 support** - Compatible with Lambda's Python 3.13 runtime
- **Optimized size** - Stripped of unnecessary files to stay under Lambda's 250MB limit

## Prerequisites

### Local Requirements
- Python 3.13
- Docker (for containerized builds)
- AWS CLI configured with credentials
- `jq` for JSON parsing (install with: `apt-get install jq` or `brew install jq`)

### AWS Requirements
- AWS account with Lambda permissions
- IAM role for Lambda execution (for testing)
- AWS credentials configured (`aws configure`)

## Quick Start

### 1. Build the Layer

**Option A: Local Build (requires Python 3.13)**
```bash
cd lambda-layer
./build.sh
```

**Option B: Docker Build (works anywhere)**
```bash
cd lambda-layer
docker build -t yt-study-buddy-layer .
docker run -v $(pwd):/output yt-study-buddy-layer
```

This creates `cli-layer.zip` (~30-50MB compressed).

### 2. Upload to AWS Lambda

```bash
./upload.sh
```

This will:
- Upload the layer to AWS Lambda
- Create a new layer version
- Output the Layer Version ARN
- Save the ARN to `layer-arn.txt`

### 3. Test the Layer (Optional)

```bash
./test.sh
```

This will:
- Create a test Lambda function
- Attach the layer
- Invoke the function to verify the CLI works
- Display test results

## Usage in Lambda Functions

### Adding the Layer to Your Function

**Via AWS Console:**
1. Go to your Lambda function
2. Click **Layers** → **Add a layer**
3. Select **Custom layers**
4. Choose `yt-study-buddy-cli`
5. Select the latest version

**Via AWS CLI:**
```bash
aws lambda update-function-configuration \
  --function-name YOUR_FUNCTION_NAME \
  --layers $(cat layer-arn.txt)
```

**Via CloudFormation/SAM:**
```yaml
Resources:
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      Layers:
        - arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:yt-study-buddy-cli:1
```

### Using the CLI in Lambda Code

**Example 1: Basic Usage**
```python
import subprocess
import json

def lambda_handler(event, context):
    youtube_url = event.get('url', 'https://youtube.com/watch?v=...')

    # Run the CLI
    result = subprocess.run(
        ['/opt/bin/yt-study-buddy', youtube_url],
        capture_output=True,
        text=True,
        env={'CLAUDE_API_KEY': 'your-api-key'}  # Set from Lambda env vars
    )

    if result.returncode == 0:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Processing complete'})
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': result.stderr})
        }
```

**Example 2: Using as a Python Module**
```python
import os
import sys

# Add layer site-packages to Python path
sys.path.insert(0, '/opt/python/lib/python3.13/site-packages')

from yt_study_buddy.video_processor import VideoProcessor
from yt_study_buddy.study_notes_generator import StudyNotesGenerator

def lambda_handler(event, context):
    # Use the modules directly
    processor = VideoProcessor("tor")
    notes_generator = StudyNotesGenerator()

    # Your processing logic here
    video_id = processor.get_video_id(event['url'])
    transcript = processor.get_transcript(video_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'transcript': transcript['transcript'][:500]})
    }
```

**Example 3: Batch Processing**
```python
import subprocess
import json
import tempfile

def lambda_handler(event, context):
    urls = event.get('urls', [])

    # Write URLs to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for url in urls:
            f.write(f"{url}\n")
        urls_file = f.name

    # Process batch with parallel mode
    result = subprocess.run(
        [
            '/opt/bin/yt-study-buddy',
            '--parallel',
            '--workers', '3',
            '--file', urls_file,
            '--format', 'json-progress'
        ],
        capture_output=True,
        text=True,
        env={'CLAUDE_API_KEY': os.environ['CLAUDE_API_KEY']}
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(urls),
            'output': result.stdout
        })
    }
```

## Configuration

### Environment Variables

Set these in your Lambda function configuration:

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_API_KEY` | Yes | Anthropic Claude API key |
| `ANTHROPIC_API_KEY` | Alternative | Alternative to CLAUDE_API_KEY |
| `TOR_PROXY_URL` | No | Tor proxy URL (default: uses YouTube API directly) |

**Setting via AWS CLI:**
```bash
aws lambda update-function-configuration \
  --function-name YOUR_FUNCTION \
  --environment "Variables={CLAUDE_API_KEY=sk-ant-...}"
```

### Lambda Function Settings

Recommended configuration:

- **Runtime:** Python 3.13
- **Memory:** 1024 MB (minimum for sentence-transformers)
- **Timeout:** 300 seconds (5 minutes for processing)
- **Ephemeral storage:** 1024 MB (default is usually sufficient)

**Note:** The CLI downloads ML models on first run. Consider:
- Using `/tmp` for model cache (ephemeral storage)
- Pre-warming the function to download models before first real request
- Increasing timeout for first invocation

## File Structure

```
lambda-layer/
├── build.sh           # Build script (local)
├── Dockerfile         # Docker build (containerized)
├── requirements.txt   # Python dependencies
├── upload.sh          # Upload to AWS Lambda
├── test.sh            # Test the deployed layer
├── README.md          # This file
└── build/             # Build artifacts (created by build.sh)
    ├── python/        # Layer contents
    │   └── lib/python3.13/site-packages/
    └── bin/           # CLI executable
        └── yt-study-buddy
```

## Layer Structure

The layer follows AWS Lambda's standard structure:

```
/opt/
├── python/
│   └── lib/
│       └── python3.13/
│           └── site-packages/
│               ├── anthropic/
│               ├── youtube_transcript_api/
│               ├── yt_study_buddy/
│               └── ... (all dependencies)
└── bin/
    └── yt-study-buddy  # CLI executable
```

## Size Optimization

The build scripts automatically:
- Remove `__pycache__` directories
- Delete `.pyc` and `.pyo` files
- Strip test files and directories
- Remove ML model caches

**Current layer size:** ~30-50MB compressed (varies with dependencies)

**AWS Lambda limits:**
- Compressed: 50MB (direct upload)
- Compressed: 250MB (via S3)
- Uncompressed: 250MB

If the layer exceeds limits, consider:
1. Removing optional dependencies (PDF export, visualization)
2. Using slim versions of packages
3. Splitting into multiple layers

## Troubleshooting

### Build Issues

**Error: Python 3.13 not found**
```bash
# Install Python 3.13 or use Docker build
docker build -t yt-study-buddy-layer .
docker run -v $(pwd):/output yt-study-buddy-layer
```

**Error: Layer too large**
- Check `requirements.txt` - remove optional dependencies
- Ensure build script optimization runs
- Consider splitting heavy dependencies (ML models) into separate layer

### Upload Issues

**Error: AWS credentials not configured**
```bash
aws configure
# Enter your AWS Access Key, Secret Key, and region
```

**Error: Invalid permissions**
- Ensure your IAM user/role has `lambda:PublishLayerVersion` permission

### Runtime Issues

**Error: CLI not found in Lambda**
- Verify layer is attached to function
- Check path: `/opt/bin/yt-study-buddy`
- Ensure layer runtime matches function runtime (python3.13)

**Error: Import errors**
```python
# Add layer site-packages to path
import sys
sys.path.insert(0, '/opt/python/lib/python3.13/site-packages')
```

**Error: Model download timeout**
- Increase Lambda timeout to 300s (5 minutes)
- Pre-warm function with simple request
- Consider EFS mount for persistent model cache

**Error: CLAUDE_API_KEY not set**
```bash
# Set via AWS CLI
aws lambda update-function-configuration \
  --function-name YOUR_FUNCTION \
  --environment "Variables={CLAUDE_API_KEY=sk-ant-...}"
```

### Memory Issues

**Error: Out of memory**
- Increase Lambda memory to 1024 MB or higher
- Sentence-transformers requires significant memory for embeddings
- Consider disabling auto-categorization if not needed

## Updating the Layer

When the CLI is updated:

1. Rebuild the layer:
   ```bash
   ./build.sh
   ```

2. Upload new version:
   ```bash
   ./upload.sh
   ```

3. Update Lambda functions to use new version:
   ```bash
   aws lambda update-function-configuration \
     --function-name YOUR_FUNCTION \
     --layers $(cat layer-arn.txt)
   ```

## Cost Considerations

**Lambda Layer Storage:**
- Layers are stored in S3 (billed per GB-month)
- Each version is retained separately
- Clean up old versions to reduce costs

**Lambda Execution:**
- CLI processing takes ~30-60 seconds per video
- With 1024 MB memory, cost is ~$0.001-0.002 per video
- Parallel processing uses more memory but is faster

**API Costs:**
- Claude API charges per token
- YouTube transcript API is free (via youtube-transcript-api)

## Advanced Usage

### Custom Build Configuration

Edit `build.sh` to customize:
- Python version
- Dependency versions
- Optimization settings
- Layer structure

### Multi-Region Deployment

Deploy to multiple regions:
```bash
for region in us-east-1 us-west-2 eu-west-1; do
  AWS_REGION=$region ./upload.sh
done
```

### CI/CD Integration

Example GitHub Actions workflow:
```yaml
name: Deploy Lambda Layer

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build layer
        run: |
          cd lambda-layer
          ./build.sh
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Upload layer
        run: |
          cd lambda-layer
          ./upload.sh
```

## Support

For issues or questions:
- Check the main project README: `/README.md`
- Review CLI documentation: `youtube-study-buddy --help`
- Check Lambda CloudWatch logs for runtime errors

## License

Same as the main yt-study-buddy project (see `/LICENSE`).
