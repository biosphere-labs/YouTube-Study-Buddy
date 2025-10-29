"""
Lambda handler for getting video status.

This function retrieves video details and processing status:
1. Reads video record from DynamoDB
2. Verifies user ownership
3. Returns video details including progress and status

API Gateway Integration:
- Method: GET
- Path: /videos/{video_id}
- Authorization: Cognito User Pool
- Response: Video object with status, progress, etc.
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
    get_item,
    VIDEOS_TABLE
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle get video status request.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        API Gateway response with video details or error

    Example Event:
        {
            "pathParameters": {"video_id": "video_1698765432_abc123"},
            "headers": {"Authorization": "Bearer <jwt_token>"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }

    Example Response (Success):
        {
            "statusCode": 200,
            "body": {
                "video_id": "video_1698765432_abc123",
                "youtube_video_id": "dQw4w9WgXcQ",
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "status": "processing",
                "progress": 45,
                "status_message": "Generating study notes",
                "created_at": "2024-10-29T12:34:56.789Z",
                "updated_at": "2024-10-29T12:35:30.123Z"
            }
        }

    Example Response (Error - Not Found):
        {
            "statusCode": 404,
            "body": "{\"error\": \"Video not found\"}"
        }
    """
    try:
        logger.info(f"Received get video request: {json.dumps(event)}")

        # Extract user ID from JWT token
        user_id = extract_user_id_from_event(event)
        if not user_id:
            logger.warning("Unauthorized request - missing or invalid token")
            return error_response(401, "Unauthorized - Invalid or missing authentication token")

        logger.info(f"Processing request for user: {user_id}")

        # Get video_id from path parameters
        path_params = event.get('pathParameters', {})
        video_id = path_params.get('video_id')

        if not video_id:
            logger.warning("Missing video_id in path parameters")
            return error_response(400, "Missing video_id in path")

        logger.info(f"Retrieving video: {video_id}")

        # Get video from DynamoDB
        video = get_item(VIDEOS_TABLE, {'video_id': video_id})

        if not video:
            logger.warning(f"Video not found: {video_id}")
            return error_response(404, "Video not found")

        # Verify user ownership
        if video.get('user_id') != user_id:
            logger.warning(f"User {user_id} attempted to access video owned by {video.get('user_id')}")
            return error_response(403, "Forbidden - You do not have access to this video")

        logger.info(f"Successfully retrieved video {video_id} - status: {video.get('status')}")

        # Return video details
        return success_response({
            'video_id': video['video_id'],
            'youtube_video_id': video.get('youtube_video_id'),
            'url': video.get('url'),
            'status': video.get('status'),
            'progress': video.get('progress', 0),
            'status_message': video.get('status_message'),
            'note_id': video.get('note_id'),
            's3_uri': video.get('s3_uri'),
            'error': video.get('error'),
            'created_at': video.get('created_at'),
            'updated_at': video.get('updated_at'),
            'completed_at': video.get('completed_at')
        })

    except Exception as e:
        logger.error(f"Error retrieving video: {e}", exc_info=True)
        return error_response(500, "Internal server error",
                            details={'error': str(e)})


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "pathParameters": {"video_id": "video_test_123"},
        "headers": {"Authorization": "Bearer test_token"},
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "test_user_123"}
            }
        }
    }

    # Mock context
    class Context:
        request_id = "test-request-id"
        function_name = "get-video"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
