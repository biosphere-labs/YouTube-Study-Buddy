# Serverless Lambda Architecture for YouTube Study Buddy

## Overview

This architecture uses AWS Lambda for serverless execution, eliminating the need for FastAPI backend servers, Celery workers, and container orchestration. The React frontend communicates with AWS services directly via API Gateway.

## Why Lambda?

**Advantages:**
- ✅ **No server management** - AWS handles all infrastructure
- ✅ **Pay per execution** - Only charged when processing videos (~$0.20 per million requests)
- ✅ **Auto-scaling** - Handles 1 or 1000 concurrent requests automatically
- ✅ **Built-in monitoring** - CloudWatch logs and metrics included
- ✅ **Simpler deployment** - No Docker, no Kubernetes, no server maintenance
- ✅ **Cost effective** - Estimated $10-50/month for 1000 videos/month vs $100+ for servers

**Perfect for this use case because:**
- Video processing is asynchronous and stateless
- Each video is independent (no shared state)
- Processing time is predictable (2-10 minutes per video)
- Traffic is bursty (not constant load)

## New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (Vercel/Netlify)                 │
│              - Authentication (Amplify/Auth0)                │
│              - Dashboard, Video Submission, Notes            │
│              - Stripe Elements for payments                  │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTPS
             │
┌────────────▼────────────────────────────────────────────────┐
│                    AWS API Gateway                           │
│  Routes:                                                     │
│  - POST /videos/submit → Lambda: SubmitVideo                │
│  - GET  /videos/{id} → Lambda: GetVideo                     │
│  - GET  /notes/{id} → Lambda: GetNote                       │
│  - POST /credits/purchase → Lambda: PurchaseCredits         │
│  - POST /webhooks/stripe → Lambda: StripeWebhook            │
└────────┬───────────────┬─────────────────────────────────────┘
         │               │
         │               │
    ┌────▼──────┐   ┌───▼────────────────────────────────────┐
    │ DynamoDB  │   │    Lambda Functions                     │
    │           │   │                                         │
    │ Tables:   │   │  1. SubmitVideo (API Gateway trigger)  │
    │ - Users   │   │     - Validates URL                    │
    │ - Videos  │   │     - Checks credits                   │
    │ - Notes   │   │     - Triggers ProcessVideo            │
    │ - Credits │   │                                         │
    └───────────┘   │  2. ProcessVideo (Async/SQS trigger)   │
                    │     - Spawns CLI subprocess            │
                    │     - Parses JSON progress             │
                    │     - Saves to S3 + DynamoDB           │
                    │                                         │
                    │  3. GetVideo/GetNote (API trigger)     │
                    │     - Read from DynamoDB               │
                    │                                         │
                    │  4. PurchaseCredits (API trigger)      │
                    │     - Stripe payment intent            │
                    │                                         │
                    │  5. StripeWebhook (Webhook trigger)    │
                    │     - Updates credits in DynamoDB      │
                    └────┬───────────────────────────────────┘
                         │
         ┌───────────────┼───────────────────────┐
         │               │                       │
    ┌────▼────┐     ┌───▼──────┐          ┌────▼─────┐
    │   S3    │     │   SQS    │          │ Secrets  │
    │         │     │          │          │ Manager  │
    │ Buckets:│     │ Queues:  │          │          │
    │ - Notes │     │ - Videos │          │ - Claude │
    │ - PDFs  │     └──────────┘          │ - Stripe │
    └─────────┘                           │ - OAuth  │
                                          └──────────┘
```

## Core Components

### 1. Lambda Functions

**A. SubmitVideo Lambda** (Node.js or Python)
```python
# lambda/submit_video.py
import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

def handler(event, context):
    """
    API Gateway trigger
    POST /videos/submit
    Body: {youtube_url, subject?, user_id}
    """
    body = json.loads(event['body'])
    user_id = event['requestContext']['authorizer']['claims']['sub']  # From Cognito

    # Validate credits
    users_table = dynamodb.Table('ytstudy-users')
    user = users_table.get_item(Key={'user_id': user_id})['Item']

    if user['credits'] < 1:
        return {
            'statusCode': 402,
            'body': json.dumps({'error': 'Insufficient credits'})
        }

    # Create video record
    video_id = str(uuid.uuid4())
    videos_table = dynamodb.Table('ytstudy-videos')
    videos_table.put_item(Item={
        'video_id': video_id,
        'user_id': user_id,
        'youtube_url': body['youtube_url'],
        'subject': body.get('subject'),
        'status': 'queued',
        'created_at': datetime.utcnow().isoformat()
    })

    # Deduct credit
    users_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET credits = credits - :dec',
        ExpressionAttributeValues={':dec': 1}
    )

    # Queue for processing
    sqs.send_message(
        QueueUrl=os.environ['VIDEO_QUEUE_URL'],
        MessageBody=json.dumps({
            'video_id': video_id,
            'user_id': user_id,
            'youtube_url': body['youtube_url'],
            'subject': body.get('subject')
        })
    )

    return {
        'statusCode': 202,
        'body': json.dumps({
            'video_id': video_id,
            'status': 'queued'
        })
    }
```

**B. ProcessVideo Lambda** (Python with CLI)
```python
# lambda/process_video.py
import json
import boto3
import subprocess
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    SQS trigger - processes video with CLI
    Timeout: 15 minutes (Lambda max)
    Memory: 2048 MB (for Claude API processing)
    """
    for record in event['Records']:
        message = json.loads(record['body'])
        video_id = message['video_id']
        user_id = message['user_id']
        youtube_url = message['youtube_url']
        subject = message.get('subject')

        # Update status
        videos_table = dynamodb.Table('ytstudy-videos')
        videos_table.update_item(
            Key={'video_id': video_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'processing'}
        )

        try:
            # Run CLI with JSON output
            cmd = [
                '/opt/bin/yt-study-buddy',  # Bundled in Lambda layer
                '--url', youtube_url,
                '--format', 'json-progress',
                '--output', f'/tmp/{video_id}'
            ]
            if subject:
                cmd.extend(['--subject', subject])

            # Execute and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Stream progress (could push to WebSocket via API Gateway)
            for line in process.stdout:
                try:
                    progress = json.loads(line)

                    # Update progress in DynamoDB
                    videos_table.update_item(
                        Key={'video_id': video_id},
                        UpdateExpression='SET progress = :progress, current_step = :step',
                        ExpressionAttributeValues={
                            ':progress': progress['progress'],
                            ':step': progress['step']
                        }
                    )

                    # Optionally: Push to WebSocket (via API Gateway WebSocket)
                    # send_websocket_update(user_id, progress)

                except json.JSONDecodeError:
                    continue

            process.wait()

            if process.returncode != 0:
                raise Exception(f"CLI failed: {process.stderr.read()}")

            # Upload note to S3
            note_path = f'/tmp/{video_id}/note.md'
            s3.upload_file(
                note_path,
                os.environ['NOTES_BUCKET'],
                f'{user_id}/{video_id}/note.md'
            )

            # Read note content
            with open(note_path, 'r') as f:
                note_content = f.read()

            # Save to DynamoDB
            notes_table = dynamodb.Table('ytstudy-notes')
            notes_table.put_item(Item={
                'note_id': video_id,
                'video_id': video_id,
                'user_id': user_id,
                'content': note_content,
                's3_url': f's3://{os.environ["NOTES_BUCKET"]}/{user_id}/{video_id}/note.md',
                'created_at': datetime.utcnow().isoformat()
            })

            # Update video status
            videos_table.update_item(
                Key={'video_id': video_id},
                UpdateExpression='SET #status = :status, completed_at = :completed',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':completed': datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            # Mark as failed
            videos_table.update_item(
                Key={'video_id': video_id},
                UpdateExpression='SET #status = :status, error = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':error': str(e)
                }
            )
            raise
```

**C. GetVideo Lambda**
```python
# lambda/get_video.py
import json
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """GET /videos/{video_id}"""
    video_id = event['pathParameters']['video_id']
    user_id = event['requestContext']['authorizer']['claims']['sub']

    videos_table = dynamodb.Table('ytstudy-videos')
    response = videos_table.get_item(Key={'video_id': video_id})

    if 'Item' not in response:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}

    video = response['Item']

    # Check ownership
    if video['user_id'] != user_id:
        return {'statusCode': 403, 'body': json.dumps({'error': 'Forbidden'})}

    return {
        'statusCode': 200,
        'body': json.dumps(video)
    }
```

### 2. DynamoDB Tables

**Users Table:**
```
Partition Key: user_id (String)

Attributes:
- email (String)
- name (String)
- provider (String) - google/github/discord
- credits (Number)
- created_at (String)
```

**Videos Table:**
```
Partition Key: video_id (String)
GSI: user_id-created_at-index

Attributes:
- user_id (String)
- youtube_url (String)
- youtube_id (String)
- title (String)
- status (String) - queued/processing/completed/failed
- progress (Number) - 0-100
- current_step (String)
- error (String)
- created_at (String)
- completed_at (String)
```

**Notes Table:**
```
Partition Key: note_id (String)
GSI: user_id-created_at-index

Attributes:
- video_id (String)
- user_id (String)
- content (String) - Markdown content
- s3_url (String)
- created_at (String)
```

**Credits Table (Transactions):**
```
Partition Key: transaction_id (String)
GSI: user_id-created_at-index

Attributes:
- user_id (String)
- amount (Number)
- type (String) - purchase/usage/refund
- video_id (String)
- stripe_payment_id (String)
- created_at (String)
```

### 3. Lambda Layer for CLI

Package the Python CLI as a Lambda Layer:

```bash
# Build layer
mkdir -p layer/python
cd layer/python

# Install CLI and dependencies
uv pip install --target . yt-study-buddy
uv pip install --target . youtube-transcript-api
uv pip install --target . anthropic

# Create layer zip
cd ..
zip -r cli-layer.zip python/

# Upload to AWS
aws lambda publish-layer-version \
  --layer-name yt-study-buddy-cli \
  --zip-file fileb://cli-layer.zip \
  --compatible-runtimes python3.13
```

### 4. Frontend Changes

React frontend connects to API Gateway instead of FastAPI:

```typescript
// src/api/client.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL; // API Gateway URL

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add Cognito JWT token to requests
apiClient.interceptors.request.use(async (config) => {
  const session = await Auth.currentSession();
  config.headers.Authorization = `Bearer ${session.getIdToken().getJwtToken()}`;
  return config;
});

// Submit video
export const submitVideo = async (youtubeUrl: string, subject?: string) => {
  const response = await apiClient.post('/videos/submit', {
    youtube_url: youtubeUrl,
    subject
  });
  return response.data;
};

// Poll for video status
export const getVideoStatus = async (videoId: string) => {
  const response = await apiClient.get(`/videos/${videoId}`);
  return response.data;
};
```

**Progress Polling** (instead of WebSocket):
```typescript
// Poll every 2 seconds for updates
const pollVideoProgress = async (videoId: string) => {
  const interval = setInterval(async () => {
    const video = await getVideoStatus(videoId);

    setProgress(video.progress);
    setCurrentStep(video.current_step);

    if (video.status === 'completed' || video.status === 'failed') {
      clearInterval(interval);
    }
  }, 2000);

  return () => clearInterval(interval);
};
```

Or **WebSocket via API Gateway WebSocket API** (optional):
- Create API Gateway WebSocket API
- Lambda function sends updates via connection ID
- Client subscribes to updates by video_id

## Infrastructure as Code (Terraform)

```hcl
# terraform/main.tf

# DynamoDB Tables
resource "aws_dynamodb_table" "users" {
  name           = "ytstudy-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "videos" {
  name           = "ytstudy-videos"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "user_id-created_at-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }
}

# S3 Bucket for notes
resource "aws_s3_bucket" "notes" {
  bucket = "ytstudy-notes"
}

# SQS Queue for video processing
resource "aws_sqs_queue" "videos" {
  name                      = "ytstudy-videos"
  visibility_timeout_seconds = 900  # 15 minutes
}

# Lambda Layer
resource "aws_lambda_layer_version" "cli" {
  filename   = "cli-layer.zip"
  layer_name = "yt-study-buddy-cli"

  compatible_runtimes = ["python3.13"]
}

# Submit Video Lambda
resource "aws_lambda_function" "submit_video" {
  filename      = "lambda/submit_video.zip"
  function_name = "ytstudy-submit-video"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      VIDEO_QUEUE_URL = aws_sqs_queue.videos.url
    }
  }
}

# Process Video Lambda
resource "aws_lambda_function" "process_video" {
  filename      = "lambda/process_video.zip"
  function_name = "ytstudy-process-video"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  timeout       = 900  # 15 minutes (Lambda max)
  memory_size   = 2048

  layers = [aws_lambda_layer_version.cli.arn]

  environment {
    variables = {
      NOTES_BUCKET     = aws_s3_bucket.notes.bucket
      CLAUDE_API_KEY   = var.claude_api_key
    }
  }
}

# SQS Trigger for Process Video Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.videos.arn
  function_name    = aws_lambda_function.process_video.arn
  batch_size       = 1
}

# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "ytstudy-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://yourdomain.com"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["*"]
  }
}

resource "aws_apigatewayv2_integration" "submit_video" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri  = aws_lambda_function.submit_video.invoke_arn
}

resource "aws_apigatewayv2_route" "submit_video" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /videos/submit"

  target = "integrations/${aws_apigatewayv2_integration.submit_video.id}"
}

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "ytstudy-users"

  # OAuth providers
  # ... configuration for Google, GitHub, Discord
}
```

## Deployment

### 1. Package Lambda Functions

```bash
# Submit Video Lambda
cd lambda/submit_video
zip -r ../submit_video.zip .

# Process Video Lambda
cd ../process_video
zip -r ../process_video.zip .
```

### 2. Deploy with Terraform

```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan \
  -var="claude_api_key=$CLAUDE_API_KEY" \
  -var="stripe_secret_key=$STRIPE_SECRET_KEY"

# Apply
terraform apply
```

### 3. Deploy Frontend

```bash
# Build
cd frontend
npm run build

# Deploy to Vercel
vercel deploy --prod

# Or Netlify
netlify deploy --prod --dir=dist
```

## Cost Estimation

**AWS Lambda:**
- 1000 videos/month × 5 minutes avg = 5000 minutes = 300,000 seconds
- Memory: 2048 MB = $0.0000133334 per second
- Cost: 300,000 × $0.0000133334 = **$4/month**

**DynamoDB:**
- 1000 videos + 1000 notes + 1000 transactions = 3000 write request units
- Reads: ~10,000 request units/month
- Cost: **$2-5/month** (pay-per-request)

**S3:**
- 1000 notes × 50KB = 50MB storage
- Storage: **$0.01/month**
- Data transfer: **$1-2/month**

**SQS:**
- 1000 messages/month: **Free tier**

**API Gateway:**
- 10,000 API calls/month: **Free tier** (first 1M free)

**CloudWatch Logs:**
- Log storage: **$2-5/month**

**Total: ~$10-20/month** for 1000 videos/month

Compare to server-based:
- EC2/ECS: $50-100/month minimum
- Database: $15-30/month
- Redis: $10-20/month
- Load balancer: $20/month
- **Total: $100-170/month**

**Savings: ~85%**

## Advantages Over FastAPI Approach

1. **No Infrastructure Management**
   - No Docker containers to maintain
   - No server OS updates
   - No scaling configuration
   - No load balancer setup

2. **Cost Effective**
   - Pay only for actual execution time
   - No idle server costs
   - Auto-scales from 0 to 1000+ concurrent

3. **Reliability**
   - AWS manages all availability
   - Built-in retry logic
   - Dead letter queues for failures

4. **Simplicity**
   - Fewer moving parts
   - Standard AWS services
   - Easier to understand and debug

5. **Development Speed**
   - No Docker setup for dev
   - No local database required
   - Deploy with one command

## Limitations

1. **Lambda Timeout**: 15 minutes max
   - Solution: If videos take longer, use Step Functions or ECS Fargate for long-running tasks

2. **Cold Starts**: First request may be slow (1-3 seconds)
   - Solution: Use provisioned concurrency for critical functions

3. **No Persistent WebSocket**: WebSocket requires API Gateway WebSocket API
   - Solution: Use polling or API Gateway WebSocket + Lambda

4. **CLI Size**: Lambda deployment package max 250MB
   - Solution: Use Lambda layers for dependencies

## Recommendation

**Use Lambda architecture if:**
- ✅ You want minimal operational overhead
- ✅ You want to minimize costs
- ✅ Video processing completes in <15 minutes
- ✅ You're comfortable with AWS services

**Use FastAPI (original plan) if:**
- ❌ Videos take >15 minutes to process
- ❌ You need persistent WebSocket connections
- ❌ You prefer self-hosted solutions
- ❌ You need more control over infrastructure

For YouTube Study Buddy, **Lambda is the better choice** - simpler, cheaper, and perfectly suited for the workload.

---

**Next Steps:**
1. Package CLI as Lambda layer
2. Write Lambda function handlers
3. Set up DynamoDB tables
4. Create API Gateway
5. Update React frontend to use API Gateway
6. Deploy with Terraform/SAM

Estimated implementation time: **4-6 hours** (vs 2-3 weeks for full FastAPI stack)
