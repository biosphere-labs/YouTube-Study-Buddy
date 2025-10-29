"""
Lambda handler for listing user's videos.

This function retrieves a paginated list of videos for a user:
1. Queries DynamoDB using user_id GSI
2. Supports pagination (limit, last_key)
3. Supports filtering by status
4. Returns videos sorted by created_at desc

API Gateway Integration:
- Method: GET
- Path: /videos
- Query Parameters:
    - limit: Number of items to return (default: 20, max: 100)
    - last_key: Last evaluated key for pagination (JSON string)
    - status: Filter by status (queued, processing, completed, failed)
- Authorization: Cognito User Pool
- Response: List of videos with pagination info
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
    query_items,
    VIDEOS_TABLE
)

from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle list videos request.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        API Gateway response with list of videos or error

    Example Event:
        {
            "queryStringParameters": {
                "limit": "20",
                "status": "completed"
            },
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
                "videos": [
                    {
                        "video_id": "video_1698765432_abc123",
                        "youtube_video_id": "dQw4w9WgXcQ",
                        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                        "status": "completed",
                        "progress": 100,
                        "note_id": "note_1698765432_xyz789",
                        "created_at": "2024-10-29T12:34:56.789Z",
                        "completed_at": "2024-10-29T12:36:12.345Z"
                    },
                    ...
                ],
                "count": 20,
                "last_key": "eyJ2aWRlb19pZCI6ICAidmlkZW9fMTIzIn0=" (optional)
            }
        }
    """
    try:
        logger.info(f"Received list videos request: {json.dumps(event)}")

        # Extract user ID from JWT token
        user_id = extract_user_id_from_event(event)
        if not user_id:
            logger.warning("Unauthorized request - missing or invalid token")
            return error_response(401, "Unauthorized - Invalid or missing authentication token")

        logger.info(f"Processing request for user: {user_id}")

        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}

        # Get limit (default: 20, max: 100)
        try:
            limit = int(query_params.get('limit', '20'))
            limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        except (ValueError, TypeError):
            limit = 20

        # Get status filter (optional)
        status_filter = query_params.get('status')
        valid_statuses = ['queued', 'processing', 'completed', 'failed']
        if status_filter and status_filter not in valid_statuses:
            logger.warning(f"Invalid status filter: {status_filter}")
            return error_response(400, f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}")

        # Get pagination token (last_key)
        last_key = None
        last_key_param = query_params.get('last_key')
        if last_key_param:
            try:
                # Decode base64 JSON
                import base64
                decoded = base64.b64decode(last_key_param).decode('utf-8')
                last_key = json.loads(decoded)
                logger.info(f"Using pagination token: {last_key}")
            except Exception as e:
                logger.warning(f"Invalid pagination token: {e}")
                return error_response(400, "Invalid pagination token")

        logger.info(f"Querying videos for user {user_id} (limit={limit}, status={status_filter})")

        # Build query
        key_condition = Key('user_id').eq(user_id)
        filter_condition = None

        if status_filter:
            filter_condition = Attr('status').eq(status_filter)

        # Query DynamoDB
        result = query_items(
            VIDEOS_TABLE,
            index_name='user-index',  # GSI on user_id
            key_condition=key_condition,
            filter_condition=filter_condition,
            limit=limit,
            last_key=last_key
        )

        videos = result['items']
        logger.info(f"Found {len(videos)} videos")

        # Sort by created_at desc (in case GSI doesn't sort)
        videos.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Build response
        response_data = {
            'videos': [
                {
                    'video_id': v['video_id'],
                    'youtube_video_id': v.get('youtube_video_id'),
                    'url': v.get('url'),
                    'status': v.get('status'),
                    'progress': v.get('progress', 0),
                    'status_message': v.get('status_message'),
                    'note_id': v.get('note_id'),
                    'error': v.get('error'),
                    'created_at': v.get('created_at'),
                    'updated_at': v.get('updated_at'),
                    'completed_at': v.get('completed_at')
                }
                for v in videos
            ],
            'count': len(videos)
        }

        # Add pagination token if there are more results
        if 'last_key' in result:
            # Encode last_key as base64 JSON
            import base64
            encoded = base64.b64encode(
                json.dumps(result['last_key']).encode('utf-8')
            ).decode('utf-8')
            response_data['last_key'] = encoded
            logger.info("More results available - included pagination token")

        return success_response(response_data)

    except Exception as e:
        logger.error(f"Error listing videos: {e}", exc_info=True)
        return error_response(500, "Internal server error",
                            details={'error': str(e)})


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "queryStringParameters": {
            "limit": "10",
            "status": "completed"
        },
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
        function_name = "list-videos"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
