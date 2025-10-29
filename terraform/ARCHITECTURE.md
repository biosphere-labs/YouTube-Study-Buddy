# YouTube Study Buddy - AWS Architecture

## Overview

YouTube Study Buddy is deployed as a serverless application on AWS, leveraging managed services for scalability, reliability, and cost-effectiveness.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                            │
│                    (CloudFront + S3 - Optional)                      │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     API Gateway (HTTP API)                           │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   /auth/*    │  │  /videos/*   │  │   /notes/*   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│         │   Cognito JWT Authorizer          │                       │
│         │                 │                  │                       │
└─────────┼─────────────────┼──────────────────┼───────────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Lambda Functions                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │    Auth     │  │   Videos     │  │    Notes     │               │
│  │  Handlers   │  │   Handlers   │  │   Handlers   │               │
│  └─────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│        │                 │                  │                        │
│  ┌─────┴──────┐  ┌──────┴───────┐  ┌──────┴────────┐               │
│  │  Credits   │  │     User     │  │   Webhooks    │               │
│  │  Handlers  │  │   Handlers   │  │   (Stripe)    │               │
│  └────────────┘  └──────────────┘  └───────────────┘               │
└────┬────────────────────┬────────────────────┬──────────────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DynamoDB Tables                               │
│  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌──────────────────┐      │
│  │  users   │  │ videos  │  │ notes  │  │ credit_transactions│     │
│  └──────────┘  └─────────┘  └────────┘  └──────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘

                     ┌──────────────┐
                     │  S3 Bucket   │
                     │  (Notes)     │
                     └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Asynchronous Processing                           │
│                                                                       │
│  Videos Submit ──▶ SQS Queue ──▶ Videos Process Lambda              │
│                                         │                             │
│                                         │ Uses CLI Layer             │
│                                         │ (YouTube-DL, Claude AI)    │
│                                         ▼                             │
│                                   Generates Notes                     │
│                                         │                             │
│                                         ├──▶ DynamoDB (metadata)     │
│                                         └──▶ S3 (markdown files)     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   Authentication & Authorization                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Cognito User Pool                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │  Email   │  │  Google  │  │  GitHub  │  │ Discord  │     │  │
│  │  │Password  │  │  OAuth   │  │  OAuth   │  │  OAuth   │     │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Cognito Identity Pool                           │  │
│  │         (Federated Identity Management)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Logging                              │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  CloudWatch      │  │  CloudWatch      │  │   CloudWatch     │ │
│  │  Logs            │  │  Alarms          │  │   Metrics        │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │  X-Ray Tracing   │  │  Budget Alerts   │                        │
│  │  (Production)    │  │  (Production)    │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. API Layer

#### API Gateway (HTTP API)
- **Type**: HTTP API (v2) - more cost-effective than REST API
- **Protocol**: HTTPS only
- **CORS**: Configured for frontend domains
- **Throttling**: 10,000 RPS, 5,000 burst
- **Authorization**: Cognito JWT authorizer for protected routes
- **Logging**: Full request/response logging to CloudWatch

#### Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/verify` - Token verification (protected)
- `POST /videos` - Submit video for processing (protected)
- `GET /videos` - List user's videos (protected)
- `GET /videos/{id}` - Get video details (protected)
- `DELETE /videos/{id}` - Delete video (protected)
- `GET /notes` - List user's notes (protected)
- `GET /notes/{id}` - Get note details (protected)
- `GET /notes/{id}/download` - Download note file (protected)
- `GET /credits` - Get credit balance (protected)
- `GET /credits/history` - Get transaction history (protected)
- `POST /credits/checkout` - Create checkout session (protected)
- `POST /webhooks/stripe` - Stripe webhook (public)
- `GET /user` - Get user profile (protected)
- `PUT /user` - Update user profile (protected)

### 2. Compute Layer

#### Lambda Functions
All functions use Python 3.13 runtime:

**Authentication Functions** (256 MB, 30s timeout)
- `auth_register`: Handle user registration with Cognito
- `auth_login`: Authenticate users and generate tokens
- `auth_refresh`: Refresh access tokens
- `auth_verify`: Verify JWT tokens

**Video Functions** (256 MB, 30s timeout)
- `videos_submit`: Validate and queue video for processing
- `videos_list`: List user's videos with pagination
- `videos_get`: Get video details and status
- `videos_delete`: Delete video and associated notes

**Video Processing Function** (512 MB, 5min timeout)
- `videos_process`: Process videos from SQS queue
  - Extract YouTube transcript
  - Generate study notes with Claude AI
  - Auto-categorize with sentence transformers
  - Create wiki-style links for Obsidian
  - Store in S3 and update DynamoDB

**Notes Functions** (256 MB, 30s timeout)
- `notes_get`: Get note metadata
- `notes_list`: List user's notes with filtering
- `notes_download`: Generate presigned S3 URL

**Credits Functions** (256 MB, 30s timeout)
- `credits_get`: Get user's credit balance
- `credits_history`: Get transaction history
- `credits_checkout`: Create Stripe checkout session
- `credits_webhook`: Handle Stripe webhook events

**User Functions** (256 MB, 30s timeout)
- `user_get`: Get user profile
- `user_update`: Update user preferences

#### Lambda Layer
- **CLI Layer**: Contains YouTube Study Buddy CLI and dependencies
  - anthropic (Claude API)
  - youtube-transcript-api
  - yt-dlp
  - sentence-transformers
  - scikit-learn
  - numpy
  - rich
  - pyyaml

### 3. Data Layer

#### DynamoDB Tables

**users**
- **Partition Key**: user_id (String)
- **GSI**: EmailIndex (email)
- **Attributes**: email, name, credits, preferences, created_at, updated_at
- **Billing**: PAY_PER_REQUEST

**videos**
- **Partition Key**: video_id (String)
- **GSI**: UserVideosIndex (user_id + created_at)
- **GSI**: StatusIndex (status + created_at)
- **Attributes**: user_id, url, title, duration, status, error, created_at
- **Billing**: PAY_PER_REQUEST
- **TTL**: Enabled for old videos

**notes**
- **Partition Key**: note_id (String)
- **GSI**: VideoNotesIndex (video_id)
- **GSI**: UserNotesIndex (user_id + created_at)
- **Attributes**: video_id, user_id, s3_key, size, category, tags, created_at
- **Billing**: PAY_PER_REQUEST
- **TTL**: Enabled for old notes

**credit_transactions**
- **Partition Key**: transaction_id (String)
- **GSI**: UserTransactionsIndex (user_id + created_at)
- **GSI**: TransactionTypeIndex (type + created_at)
- **Attributes**: user_id, type, amount, balance_after, metadata, created_at
- **Billing**: PAY_PER_REQUEST

#### S3 Bucket

**notes-bucket**
- **Encryption**: AES256
- **Versioning**: Enabled (production only)
- **Lifecycle Policies**:
  - 90 days → Standard-IA
  - 180 days → Glacier Instant Retrieval
- **Public Access**: Blocked
- **CORS**: Configured for frontend domains

### 4. Message Queue

#### SQS Queue (video-processing)
- **Visibility Timeout**: 15 minutes
- **Message Retention**: 14 days
- **Max Message Size**: 256 KB
- **Encryption**: SSE enabled
- **Dead Letter Queue**: 3 retries before DLQ
- **Long Polling**: 10 seconds

#### Dead Letter Queue (video-processing-dlq)
- **Purpose**: Failed video processing attempts
- **Retention**: 14 days
- **Alarm**: Triggers when messages appear

### 5. Authentication

#### Cognito User Pool
- **Sign-in Options**: Email, username
- **Password Policy**: 8+ chars, uppercase, lowercase, numbers, symbols
- **MFA**: Optional (TOTP)
- **Account Recovery**: Email verification
- **Advanced Security**: Enforced in production, audit in dev/staging

#### Identity Providers
- Email/Password (native)
- Google OAuth 2.0 (optional)
- GitHub OAuth 2.0 (optional)
- Discord OAuth 2.0 (optional)

#### Cognito Identity Pool
- **Purpose**: Federated identity management
- **Authenticated Role**: Limited AWS access (future: direct S3 access)

### 6. IAM Roles & Policies

#### Lambda Execution Role
Permissions:
- **CloudWatch Logs**: Write logs
- **DynamoDB**: Full access to project tables
- **S3**: Read/write notes bucket
- **SQS**: Send/receive/delete messages
- **Cognito**: Admin user operations
- **Secrets Manager**: Read API keys
- **X-Ray**: Write traces (production)

#### Cognito Authenticated Role
Permissions:
- **Cognito Identity**: Get credentials

### 7. Monitoring & Logging

#### CloudWatch Logs
- `/aws/lambda/*`: All Lambda function logs (30 days retention)
- `/aws/apigateway/*`: API Gateway access logs (30 days retention)

#### CloudWatch Alarms
- Lambda errors (> 5 in 5 minutes)
- Lambda throttles (> 0)
- API Gateway 5XX errors (> 10 in 5 minutes)
- DynamoDB throttles (> 10 in 5 minutes)
- SQS DLQ messages (> 0)

#### X-Ray Tracing (Production)
- End-to-end request tracing
- Service map visualization
- Performance insights

#### Budget Alerts (Production)
- 80% of budget threshold
- 100% of budget threshold

## Data Flow

### 1. User Registration
```
User → API Gateway → auth_register Lambda
                    → Cognito (create user)
                    → DynamoDB (create user record)
                    → DynamoDB (create credit transaction)
                    → Response with tokens
```

### 2. Video Submission
```
User → API Gateway → JWT Verification → videos_submit Lambda
                                        → Validate YouTube URL
                                        → DynamoDB (create video record)
                                        → SQS (send message)
                                        → Response with video_id
```

### 3. Video Processing
```
SQS → videos_process Lambda
     → Extract YouTube transcript
     → Call Claude API for notes generation
     → Auto-categorize with ML
     → S3 (store markdown file)
     → DynamoDB (update video status)
     → DynamoDB (create note record)
     → DynamoDB (deduct credits)
```

### 4. Note Retrieval
```
User → API Gateway → JWT Verification → notes_get Lambda
                                        → DynamoDB (get note metadata)
                                        → S3 (generate presigned URL)
                                        → Response with note data
```

### 5. Credit Purchase
```
User → API Gateway → JWT Verification → credits_checkout Lambda
                                        → Stripe (create checkout session)
                                        → Response with checkout URL

User completes payment → Stripe → credits_webhook Lambda
                                → Verify signature
                                → DynamoDB (add credits)
                                → DynamoDB (create transaction)
```

## Security

### Network Security
- All traffic over HTTPS
- API Gateway in AWS managed VPC
- Lambda functions in AWS managed VPC (can move to custom VPC if needed)

### Data Security
- **Encryption at rest**: All DynamoDB tables, S3 buckets, SQS queues
- **Encryption in transit**: TLS 1.2+
- **Secrets**: Stored in environment variables (consider AWS Secrets Manager)

### Access Control
- **Authentication**: Cognito JWT tokens
- **Authorization**: Lambda function validates user ownership
- **IAM**: Least privilege principle for all roles

### API Security
- **Rate limiting**: API Gateway throttling
- **CORS**: Restricted to known domains
- **Input validation**: All Lambda functions validate inputs
- **Webhook verification**: Stripe signature verification

## Scalability

### Automatic Scaling
- **API Gateway**: Scales automatically
- **Lambda**: Concurrent execution limit (default 1000, can increase)
- **DynamoDB**: On-demand capacity
- **SQS**: Unlimited messages

### Performance Optimization
- **Lambda**: Appropriate memory allocation
- **DynamoDB**: GSIs for efficient queries
- **S3**: CloudFront CDN (optional)
- **API Gateway**: Edge-optimized endpoints

## Cost Optimization

### Pay-per-use Services
- Lambda: Only charged for execution time
- API Gateway: Per request
- DynamoDB: On-demand billing
- S3: Storage + requests
- SQS: Per message

### Cost Reduction Strategies
- S3 lifecycle policies (move to cheaper storage)
- CloudWatch log retention (30 days)
- Destroy dev/staging when not in use
- Reserved capacity for predictable workloads (production)

## Disaster Recovery

### Backup Strategy
- **DynamoDB**: Point-in-time recovery (production)
- **S3**: Versioning enabled (production)
- **Terraform State**: S3 versioning enabled
- **CloudWatch Logs**: 30-day retention

### High Availability
- **Multi-AZ**: All services deployed across multiple AZs
- **No single point of failure**: All managed services are highly available

## Environment Strategy

### Development
- Lower memory/timeout for Lambda
- Audit mode for Cognito advanced security
- Reduced log retention
- No DynamoDB PITR

### Staging
- Similar to production
- Separate AWS account (recommended)
- Full testing before production deploy

### Production
- Full resources
- Enforced security
- Budget alerts
- PITR enabled
- Extended monitoring
