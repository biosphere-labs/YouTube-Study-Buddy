"""
Lambda handler for getting note content.

This function retrieves note metadata and optionally full content:
1. Reads note record from DynamoDB
2. Verifies user ownership
3. Optionally fetches full markdown content from S3
4. Returns note with metadata and content

API Gateway Integration:
- Method: GET
- Path: /notes/{note_id}
- Query Parameters: ?include_content=true (optional)
- Authorization: Cognito User Pool
- Response: Note object with metadata and optional content
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
    get_from_s3,
    NOTES_TABLE,
    NOTES_BUCKET
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_s3_key_from_uri(s3_uri: str) -> str:
    """
    Extract S3 key from S3 URI.

    Args:
        s3_uri: S3 URI (e.g., s3://bucket/key)

    Returns:
        S3 key
    """
    # Format: s3://bucket/key
    if s3_uri.startswith('s3://'):
        parts = s3_uri[5:].split('/', 1)
        if len(parts) == 2:
            return parts[1]
    return s3_uri


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle get note request.

    Args:
        event: API Gateway event containing request data
        context: Lambda context object

    Returns:
        API Gateway response with note details or error

    Example Event:
        {
            "pathParameters": {"note_id": "note_1698765432_abc123"},
            "queryStringParameters": {"include_content": "true"},
            "headers": {"Authorization": "Bearer <jwt_token>"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }

    Example Response (Success with content):
        {
            "statusCode": 200,
            "body": {
                "note_id": "note_1698765432_abc123",
                "video_id": "video_1698765432_abc123",
                "title": "Introduction to Machine Learning",
                "content_length": 5432,
                "created_at": "2024-10-29T12:34:56.789Z",
                "content": "# Introduction to Machine Learning\\n\\n## Overview\\n..."
            }
        }

    Example Response (Success without content):
        {
            "statusCode": 200,
            "body": {
                "note_id": "note_1698765432_abc123",
                "video_id": "video_1698765432_abc123",
                "title": "Introduction to Machine Learning",
                "content_length": 5432,
                "created_at": "2024-10-29T12:34:56.789Z"
            }
        }
    """
    try:
        logger.info(f"Received get note request: {json.dumps(event)}")

        # Extract user ID from JWT token
        user_id = extract_user_id_from_event(event)
        if not user_id:
            logger.warning("Unauthorized request - missing or invalid token")
            return error_response(401, "Unauthorized - Invalid or missing authentication token")

        logger.info(f"Processing request for user: {user_id}")

        # Get note_id from path parameters
        path_params = event.get('pathParameters', {})
        note_id = path_params.get('note_id')

        if not note_id:
            logger.warning("Missing note_id in path parameters")
            return error_response(400, "Missing note_id in path")

        # Check if content should be included
        query_params = event.get('queryStringParameters', {}) or {}
        include_content = query_params.get('include_content', '').lower() == 'true'

        logger.info(f"Retrieving note: {note_id} (include_content={include_content})")

        # Get note from DynamoDB
        note = get_item(NOTES_TABLE, {'note_id': note_id})

        if not note:
            logger.warning(f"Note not found: {note_id}")
            return error_response(404, "Note not found")

        # Verify user ownership
        if note.get('user_id') != user_id:
            logger.warning(f"User {user_id} attempted to access note owned by {note.get('user_id')}")
            return error_response(403, "Forbidden - You do not have access to this note")

        # Build response
        response_data = {
            'note_id': note['note_id'],
            'video_id': note.get('video_id'),
            'title': note.get('title'),
            'content_length': note.get('content_length', 0),
            's3_uri': note.get('s3_uri'),
            'created_at': note.get('created_at'),
            'updated_at': note.get('updated_at')
        }

        # Fetch content from S3 if requested
        if include_content:
            s3_uri = note.get('s3_uri')
            if s3_uri:
                try:
                    logger.info(f"Fetching content from S3: {s3_uri}")
                    s3_key = extract_s3_key_from_uri(s3_uri)
                    content = get_from_s3(NOTES_BUCKET, s3_key)
                    response_data['content'] = content
                    logger.info(f"Successfully fetched content ({len(content)} bytes)")
                except Exception as e:
                    logger.error(f"Error fetching content from S3: {e}", exc_info=True)
                    response_data['content_error'] = f"Failed to fetch content: {str(e)}"
            else:
                logger.warning("Note has no S3 URI")
                response_data['content_error'] = "Note content not available"

        logger.info(f"Successfully retrieved note {note_id}")

        return success_response(response_data)

    except Exception as e:
        logger.error(f"Error retrieving note: {e}", exc_info=True)
        return error_response(500, "Internal server error",
                            details={'error': str(e)})


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "pathParameters": {"note_id": "note_test_123"},
        "queryStringParameters": {"include_content": "true"},
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
        function_name = "get-note"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
