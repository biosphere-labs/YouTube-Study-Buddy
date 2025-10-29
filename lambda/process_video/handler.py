"""
Lambda handler for video processing.

This function processes videos from SQS queue:
1. Reads message from SQS
2. Updates video status to "processing"
3. Spawns CLI subprocess to generate study notes
4. Streams JSON progress and updates DynamoDB
5. Uploads generated note to S3
6. Saves note metadata to DynamoDB
7. Updates video status to "completed" or "failed"

SQS Integration:
- Trigger: SQS queue (ytsb-video-queue)
- Batch size: 1 (process one video at a time)
- Timeout: 15 minutes (max Lambda timeout)
- Dead Letter Queue: ytsb-video-dlq

Note: This Lambda requires the yt-study-buddy package to be included in the deployment package
or Lambda Layer. The CLI must be available as: yt-study-buddy or youtube-study-buddy
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import (
    get_item,
    update_item,
    put_item,
    upload_to_s3,
    generate_id,
    get_timestamp,
    VIDEOS_TABLE,
    NOTES_TABLE,
    NOTES_BUCKET
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
CLI_COMMAND = os.environ.get('CLI_COMMAND', 'youtube-study-buddy')
PROCESSING_TIMEOUT = int(os.environ.get('PROCESSING_TIMEOUT', '840'))  # 14 minutes


class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""
    pass


def update_video_progress(video_id: str, progress: int, status: str = 'processing',
                         message: Optional[str] = None) -> None:
    """
    Update video processing progress in DynamoDB.

    Args:
        video_id: Video ID
        progress: Progress percentage (0-100)
        status: Processing status
        message: Optional status message
    """
    updates = {
        'status': status,
        'progress': progress,
        'updated_at': get_timestamp()
    }

    if message:
        updates['status_message'] = message

    update_item(VIDEOS_TABLE, {'video_id': video_id}, updates)
    logger.info(f"Updated video {video_id}: {status} - {progress}%")


def parse_json_progress_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON progress line from CLI output.

    Args:
        line: JSON line from CLI stdout

    Returns:
        Parsed JSON object or None if not valid JSON
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def process_video_with_cli(video_id: str, url: str, output_dir: Path) -> Dict[str, Any]:
    """
    Process video using the CLI subprocess.

    Args:
        video_id: Video ID
        url: YouTube URL
        output_dir: Output directory for notes

    Returns:
        Dictionary with processing results

    Raises:
        VideoProcessingError: If processing fails
    """
    logger.info(f"Starting CLI processing for video {video_id}")

    # Prepare CLI command
    # Format: youtube-study-buddy --url <url> --format json-progress --output <dir>
    cmd = [
        CLI_COMMAND,
        url,
        '--format', 'json-progress',
        '--base-dir', str(output_dir)
    ]

    logger.info(f"CLI command: {' '.join(cmd)}")

    try:
        # Start subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        output_file = None
        last_progress = 0

        # Stream output and parse JSON progress
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # Try to parse as JSON progress
            progress_data = parse_json_progress_line(line)

            if progress_data:
                event_type = progress_data.get('type')
                stage = progress_data.get('stage', '')
                progress = progress_data.get('progress', 0)

                logger.info(f"CLI Progress: {event_type} - {stage} - {progress}%")

                # Update DynamoDB with progress
                if progress > last_progress:
                    update_video_progress(video_id, progress, 'processing', stage)
                    last_progress = progress

                # Capture output file path
                if event_type == 'complete' and 'file' in progress_data:
                    output_file = progress_data['file']
                    logger.info(f"CLI completed - output file: {output_file}")

            else:
                # Log non-JSON output (for debugging)
                logger.debug(f"CLI output: {line}")

        # Wait for process to complete
        return_code = process.wait(timeout=PROCESSING_TIMEOUT)

        # Check for errors
        if return_code != 0:
            stderr = process.stderr.read()
            logger.error(f"CLI process failed with code {return_code}: {stderr}")
            raise VideoProcessingError(f"CLI process failed: {stderr[:200]}")

        if not output_file:
            raise VideoProcessingError("CLI did not return output file path")

        return {
            'success': True,
            'output_file': output_file,
            'return_code': return_code
        }

    except subprocess.TimeoutExpired:
        logger.error(f"CLI process timed out after {PROCESSING_TIMEOUT} seconds")
        process.kill()
        raise VideoProcessingError(f"Processing timeout after {PROCESSING_TIMEOUT} seconds")

    except Exception as e:
        logger.error(f"Error running CLI process: {e}", exc_info=True)
        raise VideoProcessingError(f"CLI execution error: {str(e)}")


def upload_note_to_s3(video_id: str, user_id: str, note_file: Path) -> str:
    """
    Upload generated note to S3.

    Args:
        video_id: Video ID
        user_id: User ID
        note_file: Path to note file

    Returns:
        S3 URI of uploaded note

    Raises:
        VideoProcessingError: If upload fails
    """
    try:
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # S3 key: user_id/video_id/note.md
        s3_key = f"{user_id}/{video_id}/note.md"

        s3_uri = upload_to_s3(NOTES_BUCKET, s3_key, content, content_type='text/markdown')
        logger.info(f"Uploaded note to S3: {s3_uri}")

        return s3_uri

    except Exception as e:
        logger.error(f"Error uploading note to S3: {e}", exc_info=True)
        raise VideoProcessingError(f"S3 upload failed: {str(e)}")


def save_note_metadata(video_id: str, user_id: str, s3_uri: str,
                      note_file: Path) -> str:
    """
    Save note metadata to DynamoDB.

    Args:
        video_id: Video ID
        user_id: User ID
        s3_uri: S3 URI of the note
        note_file: Path to note file (for extracting metadata)

    Returns:
        Note ID

    Raises:
        VideoProcessingError: If save fails
    """
    try:
        # Extract metadata from note file
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title (first H1 heading)
        title = "Untitled"
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Generate note ID
        note_id = generate_id('note')
        timestamp = get_timestamp()

        # Create note record
        note_record = {
            'note_id': note_id,
            'video_id': video_id,
            'user_id': user_id,
            'title': title,
            's3_uri': s3_uri,
            'content_length': len(content),
            'created_at': timestamp,
            'updated_at': timestamp
        }

        put_item(NOTES_TABLE, note_record)
        logger.info(f"Saved note metadata: {note_id}")

        return note_id

    except Exception as e:
        logger.error(f"Error saving note metadata: {e}", exc_info=True)
        raise VideoProcessingError(f"Failed to save note metadata: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle video processing from SQS queue.

    Args:
        event: SQS event containing video processing request
        context: Lambda context object

    Returns:
        Processing status dictionary

    Example Event:
        {
            "Records": [{
                "messageId": "msg123",
                "body": "{\"video_id\": \"video_123\", \"url\": \"https://youtube.com/watch?v=xyz\", \"user_id\": \"user123\"}"
            }]
        }
    """
    logger.info(f"Received SQS event: {json.dumps(event)}")

    # Process each record (usually just one with batch size 1)
    for record in event.get('Records', []):
        video_id = None

        try:
            # Parse SQS message
            message = json.loads(record['body'])
            video_id = message['video_id']
            url = message['url']
            user_id = message['user_id']

            logger.info(f"Processing video {video_id} for user {user_id}")

            # Update status to processing
            update_video_progress(video_id, 0, 'processing', 'Starting video processing')

            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)
                logger.info(f"Using temp directory: {output_dir}")

                # Process video with CLI
                result = process_video_with_cli(video_id, url, output_dir)

                # Upload note to S3
                note_file = Path(result['output_file'])
                if not note_file.exists():
                    raise VideoProcessingError(f"Output file not found: {note_file}")

                update_video_progress(video_id, 90, 'processing', 'Uploading to S3')
                s3_uri = upload_note_to_s3(video_id, user_id, note_file)

                # Save note metadata
                update_video_progress(video_id, 95, 'processing', 'Saving metadata')
                note_id = save_note_metadata(video_id, user_id, s3_uri, note_file)

                # Update video record with completion
                update_item(VIDEOS_TABLE, {'video_id': video_id}, {
                    'status': 'completed',
                    'progress': 100,
                    'note_id': note_id,
                    's3_uri': s3_uri,
                    'completed_at': get_timestamp(),
                    'updated_at': get_timestamp()
                })

                logger.info(f"Successfully processed video {video_id}")

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'video_id': video_id,
                        'note_id': note_id,
                        'status': 'completed'
                    })
                }

        except VideoProcessingError as e:
            logger.error(f"Video processing error: {e}", exc_info=True)

            if video_id:
                # Update video status to failed
                update_item(VIDEOS_TABLE, {'video_id': video_id}, {
                    'status': 'failed',
                    'error': str(e),
                    'updated_at': get_timestamp()
                })

            # Re-raise to send message to DLQ
            raise

        except Exception as e:
            logger.error(f"Unexpected error processing video: {e}", exc_info=True)

            if video_id:
                # Update video status to failed
                update_item(VIDEOS_TABLE, {'video_id': video_id}, {
                    'status': 'failed',
                    'error': f"Unexpected error: {str(e)}",
                    'updated_at': get_timestamp()
                })

            # Re-raise to send message to DLQ
            raise

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processing complete'})
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "Records": [{
            "messageId": "test-msg-123",
            "body": json.dumps({
                "video_id": "video_test_123",
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "user_id": "test_user_123"
            })
        }]
    }

    # Mock context
    class Context:
        request_id = "test-request-id"
        function_name = "process-video"

    result = lambda_handler(test_event, Context())
    print(json.dumps(result, indent=2))
