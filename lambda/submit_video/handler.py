"""
Lambda handler for video submission endpoint.

This function handles video submission requests from the API Gateway:
1. Validates YouTube URL
2. Checks user credits in DynamoDB
3. Deducts 1 credit from user account
4. Creates video record with status "queued"
5. Sends message to SQS queue for processing
6. Returns video_id and status to client

API Gateway Integration:
- Method: POST
- Path: /videos
- Authorization: Cognito User Pool
- Request body: { "url": "https://youtube.com/watch?v=xyz" }
- Response: { "video_id": "xyz123", "status": "queued" }
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import (
    success_response,
    error_response,
    extract_user_id_from_event,
    validate_youtube_url,
    get_user_credits,
    deduct_credits,
    put_item,
    send_sqs_message,
    generate_id,
    get_timestamp,
    VIDEOS_TABLE,
    VIDEO_QUEUE_URL
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle video submission request.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        API Gateway response with video details or error

    Example Event:
        {
            "body": "{\"url\": \"https://youtube.com/watch?v=xyz123\"}",
            "headers": {"Authorization": "Bearer <jwt_token>"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123", "email": "user@example.com"}
                }
            }
        }

    Example Response (Success):
        {
            "statusCode": 201,
            "body": "{\"video_id\": \"video_1698765432_abc123\", \"status\": \"queued\"}"
        }

    Example Response (Error - Insufficient Credits):
        {
            "statusCode": 402,
            "body": "{\"error\": \"Insufficient credits\", \"details\": {\"required\": 1, \"available\": 0}}"
        }
    """
    try:
        logger.info(f"Received video submission request: {json.dumps(event)}")

        # Extract user ID from JWT token
        user_id = extract_user_id_from_event(event)
        if not user_id:
            logger.warning("Unauthorized request - missing or invalid token")
            return error_response(401, "Unauthorized - Invalid or missing authentication token")

        logger.info(f"Processing request for user: {user_id}")

        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return error_response(400, "Invalid JSON in request body")

        # Validate YouTube URL
        url = body.get('url', '').strip()
        if not url:
            logger.warning("Missing URL in request")
            return error_response(400, "Missing required field: url")

        video_id = validate_youtube_url(url)
        if not video_id:
            logger.warning(f"Invalid YouTube URL: {url}")
            return error_response(400, "Invalid YouTube URL",
                                details={'url': url, 'reason': 'Could not extract video ID'})

        logger.info(f"Validated YouTube URL - video_id: {video_id}")

        # Check if video already exists for this user
        from shared.utils import get_item
        existing_video = get_item(VIDEOS_TABLE, {'video_id': video_id, 'user_id': user_id})
        if existing_video:
            logger.info(f"Video {video_id} already exists for user {user_id}")
            return success_response({
                'video_id': video_id,
                'status': existing_video['status'],
                'message': 'Video already submitted'
            }, status_code=200)

        # Check user credits
        credits = get_user_credits(user_id)
        logger.info(f"User {user_id} has {credits} credits")

        if credits < 1:
            logger.warning(f"Insufficient credits for user {user_id}")
            return error_response(402, "Insufficient credits",
                                details={'required': 1, 'available': credits})

        # Deduct credit
        if not deduct_credits(user_id, 1):
            logger.error(f"Failed to deduct credit for user {user_id}")
            return error_response(500, "Failed to deduct credit - please try again")

        logger.info(f"Deducted 1 credit from user {user_id}")

        # Generate internal video ID
        internal_video_id = generate_id('video')
        timestamp = get_timestamp()

        # Create video record in DynamoDB
        video_record = {
            'video_id': internal_video_id,
            'user_id': user_id,
            'youtube_video_id': video_id,
            'url': url,
            'status': 'queued',
            'progress': 0,
            'created_at': timestamp,
            'updated_at': timestamp
        }

        put_item(VIDEOS_TABLE, video_record)
        logger.info(f"Created video record: {internal_video_id}")

        # Send message to SQS queue for processing
        message_body = {
            'video_id': internal_video_id,
            'youtube_video_id': video_id,
            'url': url,
            'user_id': user_id,
            'submitted_at': timestamp
        }

        message_id = send_sqs_message(VIDEO_QUEUE_URL, message_body)
        logger.info(f"Sent SQS message: {message_id}")

        # Return success response
        return success_response({
            'video_id': internal_video_id,
            'youtube_video_id': video_id,
            'status': 'queued',
            'message': 'Video submitted for processing'
        }, status_code=201)

    except Exception as e:
        logger.error(f"Error processing video submission: {e}", exc_info=True)
        return error_response(500, "Internal server error",
                            details={'error': str(e)})


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "body": json.dumps({"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}),
        "headers": {"Authorization": "Bearer test_token"},
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "test_user_123", "email": "test@example.com"}
            }
        }
    }

    # Mock context
    class Context:
        request_id = "test-request-id"
        function_name = "submit-video"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
