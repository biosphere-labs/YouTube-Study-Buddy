"""Shared utilities for Lambda functions."""

from .utils import (
    # Response formatting
    success_response,
    error_response,

    # DynamoDB helpers
    get_item,
    put_item,
    update_item,
    query_items,

    # S3 helpers
    upload_to_s3,
    get_from_s3,
    generate_presigned_url,

    # SQS helpers
    send_sqs_message,

    # Authentication
    verify_jwt_token,
    extract_user_id_from_event,

    # Validation
    validate_youtube_url,
    validate_required_fields,

    # Credit management
    get_user_credits,
    deduct_credits,
    add_credits,

    # Utilities
    generate_id,
    get_timestamp,

    # Environment variables
    USERS_TABLE,
    VIDEOS_TABLE,
    NOTES_TABLE,
    CREDITS_TABLE,
    NOTES_BUCKET,
    VIDEO_QUEUE_URL,
    COGNITO_USER_POOL_ID,
    COGNITO_REGION
)

__all__ = [
    'success_response',
    'error_response',
    'get_item',
    'put_item',
    'update_item',
    'query_items',
    'upload_to_s3',
    'get_from_s3',
    'generate_presigned_url',
    'send_sqs_message',
    'verify_jwt_token',
    'extract_user_id_from_event',
    'validate_youtube_url',
    'validate_required_fields',
    'get_user_credits',
    'deduct_credits',
    'add_credits',
    'generate_id',
    'get_timestamp',
    'USERS_TABLE',
    'VIDEOS_TABLE',
    'NOTES_TABLE',
    'CREDITS_TABLE',
    'NOTES_BUCKET',
    'VIDEO_QUEUE_URL',
    'COGNITO_USER_POOL_ID',
    'COGNITO_REGION'
]
