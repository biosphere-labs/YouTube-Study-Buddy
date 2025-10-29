# YouTube Study Buddy - Lambda Functions

This directory contains AWS Lambda function handlers for the YouTube Study Buddy serverless architecture.

## Architecture Overview

```
API Gateway → Lambda → DynamoDB
                ↓
              SQS Queue → Lambda → S3
                                 ↓
                            DynamoDB
```

### Flow:
1. User submits video via API Gateway
2. `submit_video` Lambda validates, deducts credit, creates record, sends to SQS
3. `process_video` Lambda processes video from SQS, generates notes, uploads to S3
4. User retrieves status via `get_video` Lambda
5. User retrieves note content via `get_note` Lambda

## Lambda Functions

### 1. submit_video
**Trigger:** API Gateway POST /videos
**Purpose:** Handle video submission requests

**Request:**
```json
POST /videos
Authorization: Bearer <cognito_jwt>
{
  "url": "https://youtube.com/watch?v=xyz123"
}
```

**Response:**
```json
{
  "video_id": "video_1698765432_abc123",
  "youtube_video_id": "xyz123",
  "status": "queued",
  "message": "Video submitted for processing"
}
```

**Environment Variables:**
- `USERS_TABLE`: DynamoDB users table name
- `VIDEOS_TABLE`: DynamoDB videos table name
- `VIDEO_QUEUE_URL`: SQS queue URL for video processing
- `COGNITO_USER_POOL_ID`: Cognito user pool ID
- `COGNITO_REGION`: AWS region for Cognito

### 2. process_video
**Trigger:** SQS queue (ytsb-video-queue)
**Purpose:** Process video and generate study notes

**SQS Message:**
```json
{
  "video_id": "video_1698765432_abc123",
  "youtube_video_id": "xyz123",
  "url": "https://youtube.com/watch?v=xyz123",
  "user_id": "user123"
}
```

**Environment Variables:**
- `VIDEOS_TABLE`: DynamoDB videos table name
- `NOTES_TABLE`: DynamoDB notes table name
- `NOTES_BUCKET`: S3 bucket for notes
- `CLI_COMMAND`: CLI command to run (default: youtube-study-buddy)
- `PROCESSING_TIMEOUT`: Processing timeout in seconds (default: 840)
- `CLAUDE_API_KEY` or `ANTHROPIC_API_KEY`: Claude API key

**Note:** This Lambda requires the yt-study-buddy package to be included in deployment.

### 3. get_video
**Trigger:** API Gateway GET /videos/{video_id}
**Purpose:** Retrieve video status and details

**Request:**
```
GET /videos/video_1698765432_abc123
Authorization: Bearer <cognito_jwt>
```

**Response:**
```json
{
  "video_id": "video_1698765432_abc123",
  "youtube_video_id": "xyz123",
  "url": "https://youtube.com/watch?v=xyz123",
  "status": "processing",
  "progress": 45,
  "status_message": "Generating study notes",
  "created_at": "2024-10-29T12:34:56.789Z",
  "updated_at": "2024-10-29T12:35:30.123Z"
}
```

### 4. get_note
**Trigger:** API Gateway GET /notes/{note_id}
**Purpose:** Retrieve note metadata and optionally full content

**Request:**
```
GET /notes/note_1698765432_xyz789?include_content=true
Authorization: Bearer <cognito_jwt>
```

**Response:**
```json
{
  "note_id": "note_1698765432_xyz789",
  "video_id": "video_1698765432_abc123",
  "title": "Introduction to Machine Learning",
  "content_length": 5432,
  "created_at": "2024-10-29T12:36:12.345Z",
  "content": "# Introduction to Machine Learning\n\n## Overview\n..."
}
```

### 5. list_videos
**Trigger:** API Gateway GET /videos
**Purpose:** List user's videos with pagination and filtering

**Request:**
```
GET /videos?limit=20&status=completed
Authorization: Bearer <cognito_jwt>
```

**Response:**
```json
{
  "videos": [
    {
      "video_id": "video_1698765432_abc123",
      "youtube_video_id": "xyz123",
      "url": "https://youtube.com/watch?v=xyz123",
      "status": "completed",
      "progress": 100,
      "note_id": "note_1698765432_xyz789",
      "created_at": "2024-10-29T12:34:56.789Z",
      "completed_at": "2024-10-29T12:36:12.345Z"
    }
  ],
  "count": 20,
  "last_key": "eyJ2aWRlb19pZCI6ICAidmlkZW9fMTIzIn0="
}
```

**Query Parameters:**
- `limit`: Number of items (1-100, default: 20)
- `status`: Filter by status (queued, processing, completed, failed)
- `last_key`: Pagination token (base64-encoded JSON)

### 6. purchase_credits
**Trigger:** API Gateway POST /credits/purchase
**Purpose:** Create Stripe payment intent for credit purchase

**Request:**
```json
POST /credits/purchase
Authorization: Bearer <cognito_jwt>
{
  "package": "standard"
}
```

**Available Packages:**
- `basic`: 10 credits for $9.99
- `standard`: 25 credits for $19.99
- `premium`: 50 credits for $29.99

**Response:**
```json
{
  "client_secret": "pi_1234567890_secret_abcdefgh",
  "payment_intent_id": "pi_1234567890",
  "amount": 1999,
  "credits": 25,
  "package": "standard"
}
```

**Environment Variables:**
- `STRIPE_SECRET_KEY`: Stripe secret key

### 7. stripe_webhook
**Trigger:** API Gateway POST /webhooks/stripe (from Stripe)
**Purpose:** Handle Stripe webhook events (payment completion)

**Webhook Events:**
- `payment_intent.succeeded`: Credits are added to user account
- `payment_intent.payment_failed`: Logged but no action

**Environment Variables:**
- `STRIPE_SECRET_KEY`: Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret
- `USERS_TABLE`: DynamoDB users table name
- `CREDITS_TABLE`: DynamoDB credits table name

**Security:** Webhook signature verification is required (no JWT auth needed)

## Shared Utilities

The `shared/utils.py` module provides common functionality:

### DynamoDB Helpers
- `get_item(table_name, key)`: Get item from DynamoDB
- `put_item(table_name, item)`: Put item to DynamoDB
- `update_item(table_name, key, updates)`: Update item
- `query_items(table_name, index_name, key_condition, ...)`: Query with pagination

### S3 Helpers
- `upload_to_s3(bucket, key, content)`: Upload content to S3
- `get_from_s3(bucket, key)`: Download content from S3
- `generate_presigned_url(bucket, key)`: Generate presigned URL

### SQS Helpers
- `send_sqs_message(queue_url, message_body)`: Send message to SQS

### Authentication
- `verify_jwt_token(token)`: Verify Cognito JWT token
- `extract_user_id_from_event(event)`: Extract user ID from API Gateway event

### Response Formatting
- `success_response(data, status_code)`: Format success response
- `error_response(status_code, message, details)`: Format error response

### Validation
- `validate_youtube_url(url)`: Validate YouTube URL and extract video ID
- `validate_required_fields(data, required_fields)`: Validate required fields

### Credit Management
- `get_user_credits(user_id)`: Get user's credit balance
- `deduct_credits(user_id, amount)`: Deduct credits (atomic operation)
- `add_credits(user_id, amount, transaction_id)`: Add credits (idempotent)

## Deployment

### Prerequisites
1. AWS Account with appropriate permissions
2. DynamoDB tables created:
   - `ytsb-users` (PK: user_id)
   - `ytsb-videos` (PK: video_id, GSI: user-index on user_id)
   - `ytsb-notes` (PK: note_id)
   - `ytsb-credits` (PK: transaction_id)
3. S3 bucket: `ytsb-notes`
4. SQS queue: `ytsb-video-queue` (with DLQ)
5. Cognito User Pool configured
6. Stripe account with API keys

### Installation

#### 1. Install Dependencies
```bash
cd lambda
pip install -r requirements.txt -t .
```

#### 2. Package Lambda Functions

For most Lambdas (except process_video):
```bash
cd submit_video
zip -r ../submit_video.zip handler.py ../shared/
```

For process_video Lambda:
```bash
# This Lambda requires the full yt-study-buddy package
# Option A: Include in deployment package (if < 250MB)
cd process_video
pip install -r ../../requirements.txt -t .
cp -r ../../src/yt_study_buddy .
zip -r ../process_video.zip .

# Option B: Use Lambda Layer (recommended)
# Create layer with yt-study-buddy and dependencies
mkdir python
pip install -r ../requirements.txt -t python/
cp -r ../src/yt_study_buddy python/
zip -r yt-study-buddy-layer.zip python/
```

#### 3. Deploy with AWS CLI

```bash
# Create Lambda function
aws lambda create-function \
  --function-name ytsb-submit-video \
  --runtime python3.13 \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --handler handler.lambda_handler \
  --zip-file fileb://submit_video.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    USERS_TABLE=ytsb-users,
    VIDEOS_TABLE=ytsb-videos,
    VIDEO_QUEUE_URL=https://sqs.region.amazonaws.com/account/ytsb-video-queue,
    COGNITO_USER_POOL_ID=region_xxxxx,
    COGNITO_REGION=us-east-1
  }"

# Repeat for other Lambdas...
```

#### 4. Configure API Gateway

```bash
# Create REST API
aws apigateway create-rest-api --name "YouTube Study Buddy API"

# Create resources and methods
# /videos (POST, GET)
# /videos/{video_id} (GET)
# /notes/{note_id} (GET)
# /credits/purchase (POST)
# /webhooks/stripe (POST)

# Attach Cognito authorizer to protected endpoints
# Configure Lambda integrations
```

#### 5. Configure SQS Trigger for process_video

```bash
aws lambda create-event-source-mapping \
  --function-name ytsb-process-video \
  --event-source-arn arn:aws:sqs:region:account:ytsb-video-queue \
  --batch-size 1 \
  --enabled
```

### Infrastructure as Code

For production deployment, use Terraform or AWS SAM:

```yaml
# template.yaml (AWS SAM example)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  SubmitVideoFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Runtime: python3.13
      CodeUri: lambda/submit_video/
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
          VIDEOS_TABLE: !Ref VideosTable
          VIDEO_QUEUE_URL: !GetAtt VideoQueue.QueueUrl
      Events:
        SubmitVideo:
          Type: Api
          Properties:
            Path: /videos
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer
```

## Testing

### Local Testing

Each Lambda handler includes a test harness at the bottom:

```bash
cd lambda/submit_video
python handler.py
```

### Integration Testing

Use AWS SAM CLI for local testing:

```bash
sam local start-api
sam local invoke SubmitVideoFunction --event events/submit_video.json
```

### Stripe Webhook Testing

Use Stripe CLI to forward webhooks to local Lambda:

```bash
stripe listen --forward-to http://localhost:3000/webhooks/stripe
stripe trigger payment_intent.succeeded
```

## Monitoring

### CloudWatch Logs

Each Lambda automatically logs to CloudWatch Logs:
- `/aws/lambda/ytsb-submit-video`
- `/aws/lambda/ytsb-process-video`
- etc.

### CloudWatch Metrics

Monitor these metrics:
- Lambda invocations, errors, duration
- SQS queue depth (ApproximateNumberOfMessagesVisible)
- DynamoDB read/write capacity
- S3 storage

### Alarms

Set up CloudWatch Alarms for:
- Lambda errors > threshold
- SQS queue age > 5 minutes
- DynamoDB throttling
- Lambda duration approaching timeout

## Security

### IAM Roles

Each Lambda requires appropriate IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:region:account:table/ytsb-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::ytsb-notes/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:region:account:ytsb-video-queue"
    }
  ]
}
```

### Secrets Management

Store sensitive values in AWS Secrets Manager or Parameter Store:
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `CLAUDE_API_KEY`

Access in Lambda:
```python
import boto3
secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='ytsb/stripe/secret-key')
```

## Troubleshooting

### Common Issues

1. **Lambda timeout in process_video**
   - Increase timeout to 15 minutes (max)
   - Optimize CLI processing
   - Consider Step Functions for longer workflows

2. **Credit deduction race condition**
   - Uses DynamoDB conditional updates (atomic)
   - Safe for concurrent requests

3. **Duplicate credit additions from webhook**
   - Idempotent handling using payment_intent_id
   - Safe for webhook retries

4. **SQS messages going to DLQ**
   - Check CloudWatch Logs for errors
   - Verify CLI is working correctly
   - Check Lambda timeout settings

### Debug Mode

Enable detailed logging by setting environment variable:
```
LOG_LEVEL=DEBUG
```

## Performance Optimization

### Cold Starts
- Keep deployment packages small
- Use Lambda Layers for large dependencies
- Consider Provisioned Concurrency for critical endpoints

### DynamoDB
- Use efficient query patterns with GSIs
- Enable auto-scaling for tables
- Use DAX for frequently accessed data

### S3
- Use CloudFront for note delivery
- Enable S3 Transfer Acceleration for uploads
- Consider S3 Intelligent-Tiering for cost optimization

## Cost Optimization

### Lambda
- Right-size memory allocation (affects price and performance)
- Use ARM architecture (Graviton2) for 20% cost savings
- Monitor unused functions

### DynamoDB
- Use on-demand billing for variable traffic
- Use provisioned capacity for predictable traffic
- Enable auto-scaling

### S3
- Use lifecycle policies to transition old notes to cheaper storage
- Enable S3 Intelligent-Tiering
- Delete incomplete multipart uploads

## License

See main project LICENSE file.

## Support

For issues, questions, or contributions, see the main project README.
