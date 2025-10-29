"""
Shared utilities for Lambda functions.

This module provides common functionality for all Lambda handlers including:
- DynamoDB helper functions
- S3 helper functions
- JWT token verification from Cognito
- Error response formatting
- Logging configuration
"""

import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import jwt
from jwt import PyJWKClient

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to int/float for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


# AWS Service Clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

# Environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'ytsb-users')
VIDEOS_TABLE = os.environ.get('VIDEOS_TABLE', 'ytsb-videos')
NOTES_TABLE = os.environ.get('NOTES_TABLE', 'ytsb-notes')
CREDITS_TABLE = os.environ.get('CREDITS_TABLE', 'ytsb-credits')
NOTES_BUCKET = os.environ.get('NOTES_BUCKET', 'ytsb-notes')
VIDEO_QUEUE_URL = os.environ.get('VIDEO_QUEUE_URL', '')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-1')


# ============================================================================
# DynamoDB Helper Functions
# ============================================================================

def get_dynamodb_table(table_name: str):
    """
    Get a DynamoDB table resource.

    Args:
        table_name: Name of the DynamoDB table

    Returns:
        DynamoDB table resource
    """
    return dynamodb.Table(table_name)


def get_item(table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get an item from DynamoDB.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of the item

    Returns:
        Item dictionary or None if not found

    Example:
        >>> item = get_item('ytsb-users', {'user_id': 'user123'})
        >>> print(item['credits'])
        10
    """
    try:
        table = get_dynamodb_table(table_name)
        response = table.get_item(Key=key)
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting item from {table_name}: {e}")
        raise


def put_item(table_name: str, item: Dict[str, Any]) -> bool:
    """
    Put an item in DynamoDB.

    Args:
        table_name: Name of the DynamoDB table
        item: Item to store

    Returns:
        True if successful

    Example:
        >>> put_item('ytsb-videos', {
        ...     'video_id': 'xyz123',
        ...     'user_id': 'user123',
        ...     'status': 'queued',
        ...     'created_at': datetime.now(timezone.utc).isoformat()
        ... })
    """
    try:
        table = get_dynamodb_table(table_name)
        table.put_item(Item=item)
        return True
    except ClientError as e:
        logger.error(f"Error putting item to {table_name}: {e}")
        raise


def update_item(table_name: str, key: Dict[str, Any],
                updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an item in DynamoDB.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of the item to update
        updates: Dictionary of attributes to update

    Returns:
        Updated item attributes

    Example:
        >>> update_item('ytsb-videos', {'video_id': 'xyz123'}, {
        ...     'status': 'processing',
        ...     'progress': 25
        ... })
    """
    try:
        table = get_dynamodb_table(table_name)

        # Build update expression
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
        expr_attr_names = {f"#{k}": k for k in updates.keys()}
        expr_attr_values = {f":{k}": v for k, v in updates.items()}

        response = table.update_item(
            Key=key,
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        return response['Attributes']
    except ClientError as e:
        logger.error(f"Error updating item in {table_name}: {e}")
        raise


def query_items(table_name: str, index_name: Optional[str] = None,
                key_condition: Optional[Any] = None,
                filter_condition: Optional[Any] = None,
                limit: int = 50,
                last_key: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Query items from DynamoDB with optional filtering and pagination.

    Args:
        table_name: Name of the DynamoDB table
        index_name: Name of GSI to query (optional)
        key_condition: Key condition expression
        filter_condition: Filter condition expression (optional)
        limit: Maximum number of items to return
        last_key: Exclusive start key for pagination (optional)

    Returns:
        Dictionary with 'items' and optional 'last_key' for pagination

    Example:
        >>> result = query_items(
        ...     'ytsb-videos',
        ...     index_name='user-index',
        ...     key_condition=Key('user_id').eq('user123'),
        ...     limit=20
        ... )
        >>> for video in result['items']:
        ...     print(video['video_id'])
    """
    try:
        table = get_dynamodb_table(table_name)

        query_kwargs = {
            'Limit': limit
        }

        if index_name:
            query_kwargs['IndexName'] = index_name

        if key_condition:
            query_kwargs['KeyConditionExpression'] = key_condition

        if filter_condition:
            query_kwargs['FilterExpression'] = filter_condition

        if last_key:
            query_kwargs['ExclusiveStartKey'] = last_key

        response = table.query(**query_kwargs)

        result = {
            'items': response['Items']
        }

        if 'LastEvaluatedKey' in response:
            result['last_key'] = response['LastEvaluatedKey']

        return result
    except ClientError as e:
        logger.error(f"Error querying items from {table_name}: {e}")
        raise


# ============================================================================
# S3 Helper Functions
# ============================================================================

def upload_to_s3(bucket: str, key: str, content: str,
                 content_type: str = 'text/plain') -> str:
    """
    Upload content to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        content: Content to upload
        content_type: Content type (default: text/plain)

    Returns:
        S3 URI of the uploaded object

    Example:
        >>> uri = upload_to_s3('ytsb-notes', 'user123/note1.md',
        ...                    '# Study Notes\\n...', 'text/markdown')
        >>> print(uri)
        s3://ytsb-notes/user123/note1.md
    """
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType=content_type
        )
        return f"s3://{bucket}/{key}"
    except ClientError as e:
        logger.error(f"Error uploading to S3: {e}")
        raise


def get_from_s3(bucket: str, key: str) -> str:
    """
    Download content from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Content as string

    Example:
        >>> content = get_from_s3('ytsb-notes', 'user123/note1.md')
        >>> print(content[:50])
        # Study Notes on Machine Learning
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        logger.error(f"Error getting from S3: {e}")
        raise


def generate_presigned_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for S3 object.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL

    Example:
        >>> url = generate_presigned_url('ytsb-notes', 'user123/note1.md')
        >>> # URL is valid for 1 hour
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise


# ============================================================================
# SQS Helper Functions
# ============================================================================

def send_sqs_message(queue_url: str, message_body: Dict[str, Any],
                     message_attributes: Optional[Dict] = None) -> str:
    """
    Send a message to SQS queue.

    Args:
        queue_url: SQS queue URL
        message_body: Message body as dictionary
        message_attributes: Optional message attributes

    Returns:
        Message ID

    Example:
        >>> message_id = send_sqs_message(VIDEO_QUEUE_URL, {
        ...     'video_id': 'xyz123',
        ...     'url': 'https://youtube.com/watch?v=xyz123',
        ...     'user_id': 'user123'
        ... })
    """
    try:
        kwargs = {
            'QueueUrl': queue_url,
            'MessageBody': json.dumps(message_body)
        }

        if message_attributes:
            kwargs['MessageAttributes'] = message_attributes

        response = sqs_client.send_message(**kwargs)
        return response['MessageId']
    except ClientError as e:
        logger.error(f"Error sending SQS message: {e}")
        raise


# ============================================================================
# JWT Token Verification
# ============================================================================

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token from Cognito and extract claims.

    Args:
        token: JWT token string

    Returns:
        Token claims if valid, None if invalid

    Example:
        >>> claims = verify_jwt_token(token)
        >>> if claims:
        ...     user_id = claims['sub']
        ...     email = claims['email']
    """
    try:
        # Get Cognito JWKs
        region = COGNITO_REGION
        user_pool_id = COGNITO_USER_POOL_ID

        jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
        jwks_client = PyJWKClient(jwks_url)

        # Get signing key
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify and decode token
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            options={'verify_exp': True}
        )

        return claims
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {e}")
        return None


def extract_user_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from API Gateway event.

    Supports both Cognito authorizer claims and manual JWT verification.

    Args:
        event: API Gateway event

    Returns:
        User ID or None if not found

    Example:
        >>> user_id = extract_user_id_from_event(event)
        >>> if not user_id:
        ...     return error_response(401, 'Unauthorized')
    """
    # Try to get from authorizer claims (API Gateway Cognito authorizer)
    if 'requestContext' in event and 'authorizer' in event['requestContext']:
        claims = event['requestContext']['authorizer'].get('claims', {})
        if 'sub' in claims:
            return claims['sub']

    # Try to verify JWT from Authorization header
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        claims = verify_jwt_token(token)
        if claims and 'sub' in claims:
            return claims['sub']

    return None


# ============================================================================
# Response Formatting
# ============================================================================

def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """
    Format a successful API response.

    Args:
        data: Response data
        status_code: HTTP status code (default: 200)

    Returns:
        API Gateway response dictionary

    Example:
        >>> return success_response({'video_id': 'xyz123', 'status': 'queued'})
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }


def error_response(status_code: int, message: str,
                  details: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Format an error API response.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Optional additional error details

    Returns:
        API Gateway response dictionary

    Example:
        >>> return error_response(400, 'Invalid YouTube URL',
        ...                       {'url': url, 'reason': 'missing video ID'})
    """
    error_data = {
        'error': message
    }

    if details:
        error_data['details'] = details

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(error_data)
    }


# ============================================================================
# Validation Functions
# ============================================================================

def validate_youtube_url(url: str) -> Optional[str]:
    """
    Validate YouTube URL and extract video ID.

    Args:
        url: YouTube URL to validate

    Returns:
        Video ID if valid, None if invalid

    Example:
        >>> video_id = validate_youtube_url('https://youtube.com/watch?v=xyz123')
        >>> print(video_id)
        xyz123
    """
    try:
        parsed = urlparse(url)

        # Handle youtube.com URLs
        if 'youtube.com' in parsed.netloc:
            if parsed.path == '/watch':
                from urllib.parse import parse_qs
                query = parse_qs(parsed.query)
                if 'v' in query:
                    return query['v'][0]

        # Handle youtu.be URLs
        elif 'youtu.be' in parsed.netloc:
            return parsed.path[1:]  # Remove leading slash

        return None
    except Exception:
        return None


def validate_required_fields(data: Dict[str, Any],
                             required_fields: List[str]) -> Optional[str]:
    """
    Validate that required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        Error message if validation fails, None if valid

    Example:
        >>> error = validate_required_fields(body, ['url', 'user_id'])
        >>> if error:
        ...     return error_response(400, error)
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


# ============================================================================
# Credit Management
# ============================================================================

def get_user_credits(user_id: str) -> int:
    """
    Get user's current credit balance.

    Args:
        user_id: User ID

    Returns:
        Credit balance (0 if user not found)

    Example:
        >>> credits = get_user_credits('user123')
        >>> print(f"User has {credits} credits")
    """
    user = get_item(USERS_TABLE, {'user_id': user_id})
    if user:
        return int(user.get('credits', 0))
    return 0


def deduct_credits(user_id: str, amount: int) -> bool:
    """
    Deduct credits from user account.

    Args:
        user_id: User ID
        amount: Number of credits to deduct

    Returns:
        True if successful, False if insufficient credits

    Example:
        >>> if deduct_credits('user123', 1):
        ...     print("Credit deducted successfully")
        ... else:
        ...     print("Insufficient credits")
    """
    try:
        table = get_dynamodb_table(USERS_TABLE)

        response = table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET credits = credits - :amount',
            ConditionExpression='credits >= :amount',
            ExpressionAttributeValues={':amount': amount},
            ReturnValues='ALL_NEW'
        )

        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Insufficient credits for user {user_id}")
            return False
        logger.error(f"Error deducting credits: {e}")
        raise


def add_credits(user_id: str, amount: int, transaction_id: str,
                reason: str = 'purchase') -> bool:
    """
    Add credits to user account and record transaction.

    Args:
        user_id: User ID
        amount: Number of credits to add
        transaction_id: Unique transaction ID (for idempotency)
        reason: Reason for credit addition

    Returns:
        True if successful

    Example:
        >>> add_credits('user123', 10, 'txn_xyz123', reason='purchase')
    """
    try:
        # Check if transaction already processed (idempotency)
        existing = get_item(CREDITS_TABLE, {'transaction_id': transaction_id})
        if existing:
            logger.info(f"Transaction {transaction_id} already processed")
            return True

        # Add credits to user
        table = get_dynamodb_table(USERS_TABLE)
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET credits = if_not_exists(credits, :zero) + :amount',
            ExpressionAttributeValues={':amount': amount, ':zero': 0}
        )

        # Record transaction
        put_item(CREDITS_TABLE, {
            'transaction_id': transaction_id,
            'user_id': user_id,
            'amount': amount,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        logger.info(f"Added {amount} credits to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        raise


# ============================================================================
# Utility Functions
# ============================================================================

def generate_id(prefix: str = '') -> str:
    """
    Generate a unique ID.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string

    Example:
        >>> video_id = generate_id('video')
        >>> print(video_id)
        video_1698765432123_abc123
    """
    import time
    import random
    import string

    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    if prefix:
        return f"{prefix}_{timestamp}_{random_str}"
    return f"{timestamp}_{random_str}"


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        ISO formatted timestamp string

    Example:
        >>> timestamp = get_timestamp()
        >>> print(timestamp)
        2024-10-29T12:34:56.789123+00:00
    """
    return datetime.now(timezone.utc).isoformat()
