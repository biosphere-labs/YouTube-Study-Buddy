# YouTube Study Buddy CLI - Architecture and Dependencies

## Overview

**YouTube Study Buddy CLI** is a Python command-line tool that processes YouTube videos to generate AI-powered study notes. It was originally designed as a standalone application with worker-based parallel processing, but is now primarily used as a library invoked within AWS Lambda functions.

**Package**: `youtube-study-buddy`
**Version**: 0.1.0
**Type**: CLI Tool + Python Package
**Python Version**: >=3.13

## Purpose and Role

The CLI serves two purposes:

1. **Historical**: Standalone command-line tool for local video processing
2. **Current**: Processing engine invoked by `process_video` Lambda function

### Key Capabilities
- Extract YouTube video transcripts (multiple methods with fallbacks)
- Generate AI-powered study notes using Claude API
- Create assessment questions and answers
- Auto-categorize content and create topic links
- Generate PDF exports of notes
- Support for batch processing

## Technology Stack

### Core Dependencies
- **youtube-transcript-api**: ^0.6.2 (transcript extraction)
- **yt-dlp**: ^2025.9.26 (fallback transcript extraction)
- **anthropic**: ^0.25.0 (Claude AI API)
- **langgraph**: ^0.2.0 (workflow orchestration)
- **langchain-core**: ^0.3.0 (LLM abstractions)
- **sentence-transformers**: ^2.2.0 (semantic similarity)

### Additional Features
- **weasyprint**: ^60.0 (PDF generation)
- **markdown2**: ^2.4.0 (markdown processing)
- **streamlit**: ^1.0.0 (web UI)
- **loguru**: ^0.7.0 (structured logging)
- **fuzzywuzzy**: ^0.18.0 (fuzzy string matching)

### Networking & Proxies
- **PySocks**: ^1.7.1 (SOCKS proxy support)
- **stem**: ^1.8.0 (Tor control)

## Repository Structure

```
youtube-buddy/
├── src/
│   └── yt_study_buddy/
│       ├── cli.py                      # Main CLI entry point
│       ├── processing_pipeline.py      # Main processing orchestration
│       ├── langgraph_workflow.py       # LangGraph workflow definition
│       ├── workflow_nodes.py           # Workflow node implementations
│       ├── workflow_state.py           # Workflow state management
│       │
│       ├── tor_transcript_fetcher.py   # Transcript fetching (Tor/proxy)
│       ├── transcript_provider.py      # Transcript extraction
│       ├── ytdlp_fallback.py          # yt-dlp fallback
│       │
│       ├── study_notes_generator.py    # AI note generation
│       ├── assessment_generator.py     # Question generation
│       ├── auto_categorizer.py         # Topic categorization
│       ├── obsidian_linker.py         # Wiki-style linking
│       ├── knowledge_graph.py         # Concept relationships
│       │
│       ├── video_job.py               # Job data model (used by pipeline)
│       ├── video_processor.py         # Video processing utilities
│       │
│       ├── pdf_exporter.py            # PDF generation
│       ├── rotating_tor_client.py     # Tor rotation
│       ├── job_logger.py              # Processing logs
│       ├── error_classifier.py        # Error handling
│       ├── exit_node_tracker.py       # Tor exit tracking
│       └── daily_exit_tracker.py      # Tor analytics
│
├── tests/                              # pytest tests
├── data/                               # Output directory
│   ├── study_notes/                   # Generated notes
│   └── daily_exit_tracking.json       # Tor data
├── notes/                              # Processing logs
├── docker-compose.yml                  # Docker setup
├── streamlit_app.py                   # Web UI
├── pyproject.toml                     # Package config
└── README.md
```

## Core Processing Flow

### Current Flow (Used by Lambda)

```
┌─────────────────────────────────────────────────────────────┐
│  Lambda: process_video                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Receive video_id and URL from SQS                   │ │
│  │  2. Update DynamoDB status: "processing"                │ │
│  │  3. Invoke CLI:                                         │ │
│  │     subprocess.run(['youtube-study-buddy', 'process'])  │ │
│  └────────────────┬───────────────────────────────────────┘ │
└────────────────────┼───────────────────────────────────────┘
                     │
         ┌───────────▼────────────┐
         │  CLI Processing        │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │  1. Transcript Fetch   │────► tor_transcript_fetcher.py
         │     - Try transcript API│      transcript_provider.py
         │     - Fallback to yt-dlp│      ytdlp_fallback.py
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │  2. LangGraph Workflow │────► langgraph_workflow.py
         │     - State machine     │      workflow_state.py
         │     - Node execution    │      workflow_nodes.py
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │  3. AI Generation      │────► study_notes_generator.py
         │     - Claude API calls  │      assessment_generator.py
         │     - Study notes       │
         │     - Assessment Q&A    │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │  4. Post-Processing    │────► auto_categorizer.py
         │     - Categorization    │      obsidian_linker.py
         │     - Wiki linking      │      knowledge_graph.py
         │     - Markdown format   │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │  5. Output             │
         │     - Markdown file     │────► /tmp/note.md
         │     - Metadata JSON     │────► /tmp/meta.json
         └────────────────────────┘
                     │
         ┌───────────▼────────────┐
         │  Lambda continues:      │
         │  - Upload to S3         │
         │  - Update DynamoDB      │
         │  - Status: "completed"  │
         └─────────────────────────┘
```

### Legacy Flow (Deprecated)

The CLI originally supported parallel processing of multiple videos:

```
❌ DEPRECATED - No longer needed with SQS/Lambda

┌─────────────────────────────────────────┐
│  CLI: youtube-study-buddy batch         │
└────────────────┬────────────────────────┘
                 │
     ┌───────────▼──────────┐
     │  parallel_processor  │
     │  - Worker pool       │────► parallel_processor.py
     │  - Job queue         │      video_job.py
     │  - N concurrent jobs │      video_processor.py
     └───────────┬──────────┘
                 │
     ┌───────────▼──────────┐
     │  Worker 1 │ Worker 2 │ ... │ Worker N
     └───────────┴──────────┴─────┴──────────
                 │
     ┌───────────▼──────────┐
     │  Process each video  │
     │  (same flow as above)│
     └──────────────────────┘
```

**Why This Is Deprecated:**
- **SQS already provides queuing** - don't need in-memory job queue
- **Lambda auto-scales** - each Lambda processes one video
- **Parallel processing is handled by AWS** - not by the CLI
- **Simplified error handling** - Lambda retry policies replace worker retry logic

## Integration with Other Repositories

### 1. Infrastructure (Primary Integration)

**Repository**: `youtube-buddy-infrastructure`
**Relationship**: Invoked by `process_video` Lambda function

#### Current Usage

The CLI is packaged into the `process_video` Lambda function:

**Lambda Packaging:**
```bash
# Include CLI in Lambda function
cd lambda/process_video
pip install -t . /path/to/youtube-buddy

# OR include in Lambda Layer
cd lambda-layer/python
pip install /path/to/youtube-buddy
```

**Lambda Invocation:**
```python
# lambda/process_video/handler.py
import subprocess
import json
import os

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['body'])
        video_id = message['video_id']
        url = message['url']

        try:
            # Invoke CLI
            result = subprocess.run(
                [
                    'youtube-study-buddy',
                    'process',
                    '--url', url,
                    '--output-dir', '/tmp',
                    '--format', 'markdown'
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                env={
                    **os.environ,
                    'ANTHROPIC_API_KEY': os.environ['ANTHROPIC_API_KEY']
                }
            )

            if result.returncode == 0:
                # Success - read output
                with open(f'/tmp/{video_id}_note.md', 'r') as f:
                    note_content = f.read()

                # Upload to S3 and update DynamoDB
                # ...
            else:
                # Handle error
                # ...

        except subprocess.TimeoutExpired:
            # Handle timeout
            # ...
```

#### Integration Points

1. **Input**: URL passed as command-line argument
2. **Output**: Markdown file written to `/tmp` (Lambda writable directory)
3. **API Keys**: Environment variables (ANTHROPIC_API_KEY)
4. **Timeout**: Lambda timeout (15 minutes) vs video length
5. **Error Reporting**: Exit codes and stderr

### 2. Backend Business Logic (Parallel)

**Repository**: `youtube-buddy-backend`
**Relationship**: Sibling - separate concerns

The CLI and backend are complementary but independent:

**CLI Responsibilities:**
- Transcript extraction
- AI content generation
- Note formatting

**Backend Responsibilities:**
- API request validation
- User credit management
- DynamoDB state management
- S3 file operations

**No Direct Dependency** - They communicate only through Lambda:
```
Frontend → API Gateway → Lambda → Backend (validation/state)
                           └─→ CLI (processing)
```

### 3. Frontend (Indirect)

**Repository**: `youtube-buddy-frontend`
**Relationship**: Indirect - frontend triggers CLI via Lambda

The frontend never directly interacts with the CLI:
1. User submits URL → Frontend
2. Frontend → API Gateway → `submit_video` Lambda
3. `submit_video` → SQS queue
4. SQS → `process_video` Lambda
5. **`process_video` Lambda → CLI** (subprocess)
6. CLI → generates notes
7. Lambda → uploads to S3
8. Frontend → polls and retrieves notes

### 4. MindMesh (Output Format)

**Repository**: `mindmesh`
**Relationship**: Output format compatibility

The CLI generates notes in a format compatible with MindMesh:

**Note Format:**
```markdown
# Video Title

## Summary
Brief overview...

## Key Concepts

### [[Concept 1]]
Explanation with [[wiki-style links]]...

### [[Concept 2]]
More content with [[relationships]]...

## Assessment

### Questions
1. Question about [[Concept 1]]?

### Answers
1. Answer referencing [[Concept 2]]...

## Tags
#category #topic #subject
```

**MindMesh Integration:**
- `[[wiki-links]]` are parsed by MindMesh
- Hashtags become searchable tags
- Graph view visualizes concept connections
- Bidirectional links are auto-detected

## Current Status

### Implemented Features
- ✅ YouTube transcript extraction (multiple fallback methods)
- ✅ Claude AI integration for note generation
- ✅ Assessment question generation
- ✅ Auto-categorization of content
- ✅ Wiki-style linking (Obsidian-compatible)
- ✅ PDF export
- ✅ Tor/proxy support for reliability
- ✅ LangGraph workflow orchestration
- ✅ Streamlit web UI

### ~~Legacy Components (Removed)~~

✅ **REFACTORING COMPLETE**

The following components have been **removed** as they were designed for standalone batch processing and are no longer necessary with the Lambda + SQS architecture:

| Component | File | Status |
|-----------|------|--------|
| Worker Pool | `parallel_processor.py` | ✅ Removed - SQS + Lambda auto-scaling replaces this |
| Tor Coordinators | `tor_transcript_fetcher.py` (coordinators only) | ✅ Removed - Not needed for single-video processing |
| Batch Processing | `video_job.py` (`create_job_batch`) | ✅ Removed - SQS handles job queuing |
| Docker Compose Parallel | `docker-compose.parallel.yml` | ✅ Removed - Not used in Lambda |
| Batch CLI Flags | `--parallel`, `--workers` | ✅ Removed - Videos submitted individually via API |

### ~~Recommended Refactoring~~ → **Completed Refactoring**

**✅ Simplified CLI Structure (Current):**
```
CLI Entry Point (cli.py)
  └── Single Video Mode ONLY
      └── processing_pipeline.py
          └── langgraph_workflow.py
              ├── Fetch transcript
              ├── Generate notes (AI)
              ├── Generate assessment (AI)
              ├── Post-process (links, categories)
              └── Output markdown
```

**Benefits Achieved:**
1. ✅ **Reduced Complexity**: ~1,000 lines removed (13% reduction)
2. ✅ **Smaller Lambda Package**: 25KB reduction → faster cold starts
3. ✅ **Clearer Responsibility**: One video = one invocation
4. ✅ **Easier Testing**: No parallel test scenarios
5. ✅ **Better Error Handling**: No worker coordination issues
6. ✅ **No Threading Complexity**: Removed all locks and coordinators

### ~~Migration Path~~ → **Completed**

**✅ Phase 1: Remove Parallel Processing** (Completed)
- Removed `parallel_processor.py` (320 lines)
- Removed coordinator classes from `tor_transcript_fetcher.py` (468 lines)
- Removed `create_job_batch()` from `video_job.py` (23 lines)
- Removed `docker-compose.parallel.yml`
- Removed `--parallel` and `--workers` CLI flags
- Updated `app_interface.py` and `streamlit_app.py`

**Total Reduction:** ~1,000 lines of code (13% of codebase)

**Next Steps (Future Optimizations):**
```python
# Add Lambda-specific optimizations:
# - Further reduce package size
# - Optimize cold start time
# - Stream output instead of file writes
# - Use Lambda temp storage more efficiently
```

## Development Guidelines for Claude Code

When working in this repository:

### Current State (Lambda Integration)

1. **Focus on Single-Video Processing**
   - Only modify `processing_pipeline.py` and `langgraph_workflow.py`
   - Ignore parallel processing files

2. **Lambda Compatibility**
   - Ensure CLI works with `/tmp` directory (Lambda writable)
   - Handle timeouts gracefully (Lambda 15-minute limit)
   - Minimize package size (Lambda 250MB limit)

3. **Testing**
   - Test CLI locally: `youtube-study-buddy process --url <URL>`
   - Test in Lambda-like environment (Docker)
   - Verify output format for MindMesh

### Future Simplification

1. **Refactor for Lambda-First**
   - Remove worker pool code
   - Simplify CLI to library with minimal CLI wrapper
   - Export processing as Python function callable directly

2. **API Design**
   ```python
   # Ideal future API (no CLI needed in Lambda)
   from yt_study_buddy import process_video

   # Lambda can import and call directly
   result = process_video(
       url="https://youtube.com/watch?v=...",
       output_format="markdown"
   )
   # Returns: {"title": "...", "content": "...", "metadata": {...}}
   ```

## Dependencies on Other Repositories

**None** - The CLI is standalone and has no direct dependencies on other project repositories. It only depends on:
- External APIs (YouTube, Claude)
- Python packages (listed in pyproject.toml)

## Related Repositories

### Upstream (Invokes CLI)
- **youtube-buddy-infrastructure**: Lambda functions invoke CLI

### Downstream (Consumes Output)
- **youtube-buddy-frontend**: Displays generated notes
- **mindmesh**: Renders wiki-links and graph view

### Sibling (Parallel Concerns)
- **youtube-buddy-backend**: API/business logic (separate from processing)

## Performance Characteristics

### Typical Processing Times
- **Short video** (5-10 min): 30-60 seconds
- **Medium video** (30-60 min): 2-5 minutes
- **Long video** (2+ hours): 10-15 minutes

### Bottlenecks
1. **Transcript Extraction**: 5-30 seconds (depends on method)
2. **Claude API Calls**: 20-60 seconds per call (2-3 calls per video)
3. **Post-Processing**: 5-10 seconds

### Lambda Considerations
- **Cold Start**: ~5 seconds (with all dependencies)
- **Timeout**: 15 minutes (AWS Lambda max)
- **Memory**: 1024MB+ recommended (for ML models)
- **Concurrent Executions**: Handled by SQS + Lambda scaling

## Error Handling

### Common Errors
1. **Transcript Unavailable**: No captions on video
2. **API Rate Limits**: Claude API throttling
3. **Timeout**: Video too long for Lambda timeout
4. **Memory Error**: Large transcript + ML models

### Error Classification
```python
# error_classifier.py
class TranscriptError(Exception): pass      # Cannot fetch transcript
class APIError(Exception): pass             # Claude API failure
class TimeoutError(Exception): pass         # Processing timeout
class ContentError(Exception): pass         # Invalid content
```

### Lambda Error Handling
```python
# Lambda should catch and report errors
try:
    result = subprocess.run(['youtube-study-buddy', ...])
    if result.returncode != 0:
        # Parse stderr for error type
        update_video_status(video_id, 'failed', result.stderr)
except subprocess.TimeoutExpired:
    update_video_status(video_id, 'failed', 'Processing timeout')
```

## Future Enhancements

1. **Simplified Library API**: Direct Python import instead of subprocess
2. **Streaming Output**: Stream notes as they're generated (for long videos)
3. **Chunked Processing**: Split very long videos into chunks
4. **Multi-Language Support**: Transcripts in different languages
5. **Custom Prompts**: User-configurable AI generation prompts
6. **Caching**: Cache transcripts and intermediate results
7. **Progress Reporting**: Real-time progress updates to frontend

## Key Takeaways for Claude Code

When working in this repository, remember:

1. **This CLI is primarily a Lambda dependency** - not a standalone app
2. **Parallel processing code is legacy** - SQS handles concurrency
3. **Simplification is a priority** - remove worker/batch code when possible
4. **Output format matters** - MindMesh depends on consistent markdown format
5. **Lambda constraints apply** - 15-minute timeout, 250MB package size, /tmp storage
6. **Single responsibility** - Focus on video → notes transformation only

---

## ⚠️ CRITICAL ISSUE: Backend Integration Refactoring Required

### Problem Statement

**ARCHITECTURE MISMATCH**: The Lambda functions in the infrastructure repository are NOT using the `ytsb-backend` package as documented. This is a critical architectural issue that needs to be resolved.

**Current Reality (WRONG):**
- Lambda functions use `shared/utils.py` for business logic
- The `ytsb-backend` package exists but Lambda functions don't import it
- Code is duplicated between `shared/utils.py` and `ytsb_backend` package
- Documentation describes an architecture that doesn't match the actual implementation

**Required State (CORRECT):**
- Lambda functions must import and use the `ytsb-backend` package
- Business logic should live only in the backend package (single source of truth)
- Lambda Layer must contain the `ytsb-backend` package
- `shared/utils.py` should be eliminated or reduced to minimal Lambda-specific helpers

### Evidence of the Problem

**Current Lambda Handler (infrastructure repo):**
```python
# lambda/submit_video/handler.py (WRONG)
from shared.utils import (
    get_user_credits,
    deduct_credits,
    put_item,
    send_sqs_message
)
```

**Required Lambda Handler:**
```python
# lambda/submit_video/handler.py (CORRECT)
from ytsb_backend.services.user_service import get_user_credits, deduct_credits
from ytsb_backend.services.video_service import create_video, queue_video_for_processing
from ytsb_backend.errors import InvalidYouTubeURL, InsufficientCredits
```

### Refactoring Action Plan

#### Phase 1: Migrate Logic to Backend Package

Move all business logic from `infrastructure/lambda/shared/utils.py` to appropriate services in `backend/src/ytsb_backend/services/`:

| Current Location | Target Location | Functions |
|-----------------|-----------------|-----------|
| `shared/utils.py` | `services/user_service.py` | get_user_credits, deduct_credits, add_credits |
| `shared/utils.py` | `services/video_service.py` | create_video, update_video_status, list_videos |
| `shared/utils.py` | `services/note_service.py` | save_note, get_note |
| `shared/utils.py` | `services/workspace_service.py` | save_workspace, load_workspace, file operations |
| `shared/utils.py` | `services/queue_service.py` | send_to_processing_queue |
| `shared/utils.py` | `utils/dynamodb.py` | get_item, put_item, update_item (keep as utilities) |
| `shared/utils.py` | `utils/s3.py` | upload_to_s3, get_from_s3 (keep as utilities) |

#### Phase 2: Build Lambda Layer with Backend Package

```bash
cd youtube-buddy-infrastructure/lambda-layer

# Install backend package into layer
pip install -t python/ ../../youtube-buddy-backend-workspace/youtube-buddy-backend/

# Create layer zip
zip -r ytsb-backend-layer.zip python/

# Update Terraform to deploy layer and attach to all Lambda functions
```

#### Phase 3: Update Lambda Handlers

Refactor ALL 11 Lambda functions to import from `ytsb_backend`:

**Example Refactor (submit_video):**
```python
# BEFORE
from shared.utils import get_user_credits, deduct_credits

def lambda_handler(event, context):
    credits = get_user_credits(user_id)
    deduct_credits(user_id, 1)

# AFTER
from ytsb_backend.services.user_service import get_user_credits, deduct_credits
from ytsb_backend.errors import InsufficientCredits

def lambda_handler(event, context):
    try:
        credits = get_user_credits(user_id)
        if credits < 1:
            raise InsufficientCredits("Need 1 credit")
        deduct_credits(user_id, 1)
    except InsufficientCredits as e:
        return {'statusCode': 402, 'body': str(e)}
```

**Lambda Functions to Update:**
1. `submit_video/` - Video submission
2. `list_videos/` - List user videos
3. `get_video/` - Get video details
4. `get_note/` - Get study note
5. `process_video/` - Main processor (SQS triggered)
6. `mindmesh_workspace_load/` - Load workspace
7. `mindmesh_workspace_save/` - Save workspace
8. `mindmesh_file_create/` - Create file
9. `mindmesh_file_update/` - Update file
10. `mindmesh_file_delete/` - Delete file
11. `stripe_webhook/` - Payment webhook

#### Phase 4: Testing

```bash
# Unit tests with moto mocking
pytest lambda/*/tests/ -v

# Local Lambda testing with SAM CLI
sam local invoke --hook-name terraform submit_video -e test-events/submit.json

# Integration tests with LocalStack (optional)
docker-compose up localstack
tflocal apply
pytest tests/integration/
```

#### Phase 5: Deployment

```bash
cd youtube-buddy-infrastructure/terraform
terraform init
terraform plan  # Review changes to Lambda Layer
terraform apply  # Deploy updated layer and functions
```

### Verification Checklist

After completing refactoring:

- [ ] Backend package services contain all business logic (no duplicates in shared/)
- [ ] Lambda Layer contains `ytsb_backend` package with all dependencies
- [ ] All 11 Lambda functions import from `ytsb_backend` (not shared/utils)
- [ ] `shared/utils.py` deleted or contains only Lambda-specific response helpers
- [ ] Unit tests pass with backend package imports
- [ ] SAM CLI local testing works
- [ ] Lambda functions execute successfully in AWS
- [ ] No import errors in CloudWatch logs
- [ ] Infrastructure ARCHITECTURE.md updated to reflect reality

### Estimated Effort

- **Phase 1** (Migrate to Backend): 4-6 hours
- **Phase 2** (Build Layer): 2-3 hours
- **Phase 3** (Update Handlers): 6-10 hours
- **Phase 4** (Testing): 4-6 hours
- **Phase 5** (Deployment): 2-3 hours

**Total**: 18-28 hours (2.5-3.5 days of focused work)

### Why This Matters

1. **Eliminates Code Duplication**: Single source of truth for business logic
2. **Improves Testability**: Backend package can be tested independently
3. **Enforces Architecture**: Matches documented design patterns
4. **Enables Reusability**: Backend logic can be used in other contexts
5. **Simplifies Maintenance**: Changes in one place propagate everywhere

### Backend Package Architecture (Reference)

Since the backend repository is separate, here's a summary of its structure for context:

#### Package Structure: `ytsb-backend`
```
ytsb-backend/src/ytsb_backend/
├── config/              # Configuration management
│   ├── settings.py      # Pydantic settings (AWS region, table names, etc.)
│   └── aws_config.py    # AWS resource names/ARNs
├── models/              # Pydantic data models
│   ├── video.py         # Video(video_id, user_id, url, status, title, ...)
│   ├── user.py          # User(user_id, email, credits, ...)
│   ├── note.py          # Note(note_id, video_id, content, s3_uri, ...)
│   └── workspace.py     # Workspace(workspace_id, user_id, files, ...)
├── services/            # Business logic services
│   ├── video_service.py     # create_video, get_video, update_video_status, list_user_videos
│   ├── user_service.py      # get_user_credits, deduct_credits, add_credits
│   ├── note_service.py      # save_note, get_note, format_note_for_mindmesh
│   ├── workspace_service.py # save_workspace, load_workspace, file CRUD
│   └── auth_service.py      # verify_jwt_token, extract_user_id_from_event
├── errors/              # Custom exceptions
│   ├── base.py          # YTSBError (base class)
│   ├── validation.py    # InvalidYouTubeURL, ValidationError
│   └── aws_errors.py    # InsufficientCredits, UserNotFoundError, DynamoDBError
└── utils/               # AWS utility functions
    ├── dynamodb.py      # get_item, put_item, update_item, query_items
    ├── s3.py            # upload_to_s3, get_from_s3, generate_presigned_url
    ├── sqs.py           # send_message, receive_messages
    └── validators.py    # validate_youtube_url, validate_video_id
```

#### Example Service Implementation
```python
# ytsb_backend/services/user_service.py
from ytsb_backend.models.user import User
from ytsb_backend.utils.dynamodb import get_item, update_item
from ytsb_backend.errors import UserNotFoundError, InsufficientCredits

def get_user_credits(user_id: str) -> int:
    """Get user's available credits from DynamoDB."""
    user_data = get_item('users', {'user_id': user_id})
    if not user_data:
        raise UserNotFoundError(f"User {user_id} not found")
    user = User(**user_data)
    return user.credits

def deduct_credits(user_id: str, amount: int) -> None:
    """Deduct credits from user account."""
    credits = get_user_credits(user_id)
    if credits < amount:
        raise InsufficientCredits(f"Need {amount} credits, have {credits}")
    update_item('users', {'user_id': user_id}, {'credits': credits - amount})
```

### Infrastructure Architecture (Reference)

The infrastructure repository contains 11 Lambda functions that should use the backend package:

#### Lambda Functions (All in `youtube-buddy-infrastructure/lambda/`)
1. **submit_video/** - Submit YouTube URL, validate, check credits, queue in SQS
2. **list_videos/** - Query DynamoDB for user's videos
3. **get_video/** - Get specific video details
4. **get_note/** - Retrieve generated note from S3
5. **process_video/** - SQS-triggered processor (uses this CLI + backend)
6. **mindmesh_workspace_load/** - Load MindMesh workspace from S3
7. **mindmesh_workspace_save/** - Save MindMesh workspace to S3
8. **mindmesh_file_create/** - Create file in workspace
9. **mindmesh_file_update/** - Update file in workspace
10. **mindmesh_file_delete/** - Delete file from workspace
11. **stripe_webhook/** - Handle payment events, add credits

#### Current Problem: Lambda Functions Use shared/utils.py Instead
```python
# CURRENT (WRONG): lambda/submit_video/handler.py
from shared.utils import (
    get_user_credits,      # ❌ Duplicated code
    deduct_credits,        # ❌ Duplicated code
    put_item,              # ❌ Should be in backend utils
    send_sqs_message       # ❌ Should be in backend utils
)
```

#### Required Pattern: Lambda Functions Should Import Backend
```python
# CORRECT: lambda/submit_video/handler.py
from ytsb_backend.services.user_service import get_user_credits, deduct_credits
from ytsb_backend.services.video_service import create_video, queue_video_for_processing
from ytsb_backend.errors import InvalidYouTubeURL, InsufficientCredits

def lambda_handler(event, context):
    try:
        credits = get_user_credits(user_id)
        if credits < 1:
            raise InsufficientCredits("Need 1 credit")
        deduct_credits(user_id, 1)
        video = create_video(user_id, url)
        queue_video_for_processing(video.video_id, url, user_id)
    except InsufficientCredits as e:
        return {'statusCode': 402, 'body': str(e)}
```

#### Lambda Layer Structure (How Backend Should Be Deployed)
```
lambda-layer/
├── ytsb-backend-layer.zip
└── python/
    └── ytsb_backend/        # Backend package installed here
        ├── config/
        ├── models/
        ├── services/
        ├── errors/
        └── utils/
```

#### Terraform Configuration (How Layer Should Be Attached)
```hcl
# terraform/lambda.tf
resource "aws_lambda_layer_version" "ytsb_backend" {
  filename            = "../lambda-layer/ytsb-backend-layer.zip"
  layer_name          = "ytsb-backend-layer"
  compatible_runtimes = ["python3.12"]
}

resource "aws_lambda_function" "submit_video" {
  # ... other config ...
  layers = [aws_lambda_layer_version.ytsb_backend.arn]
}
```

### Why This Architecture Matters

**Single Source of Truth**:
- Business logic lives in ONE place: `ytsb-backend` package
- Lambda functions are thin wrappers that call backend services
- No code duplication between Lambda functions

**Testability**:
- Backend package can be tested independently with pytest
- Lambda handlers become simple and easy to test
- Mock backend services in Lambda tests

**Maintainability**:
- Change business logic once in backend package
- All Lambda functions automatically get the update (via Layer)
- Clear separation: Lambda = HTTP handling, Backend = business logic

**Reusability**:
- Backend package can be used in other contexts (CLI, scripts, other Lambdas)
- Standard Python package that follows best practices
- Pydantic models ensure data consistency

**This refactoring is critical for maintaining a clean, testable, and maintainable codebase.**

---

## ⚠️ KNOWN ISSUE: Streamlit App Broken After LangGraph Migration

### Problem Summary

The Streamlit web interface (`streamlit_app.py`) is **broken** and throws `TypeError` exceptions after the migration from the old processing pipeline to LangGraph workflow. The app tries to use API signatures that no longer exist.

### Root Cause

**Before (Old Pipeline)**:
- File: `src/yt_study_buddy/processing_pipeline.py`
- Supported parallel processing with worker pools
- Parameters: `parallel`, `max_workers`, `worker_id`

**After (LangGraph Migration)**:
- File: `src/yt_study_buddy/langgraph_workflow.py`
- Declarative state machine workflow
- **Removed** all parallel processing parameters
- Each video is processed independently (no worker coordination)

**The Problem**:
- `app_interface.py` was supposed to shield the UI from internal changes
- However, the interface itself changed when parallel parameters were removed
- Streamlit app was never updated to match the new interface

### Specific Errors

#### Error 1: `create_processor()` called with removed parameters

**Location**: `streamlit_app.py:742-743`

```python
# BROKEN CODE:
processor = create_processor(
    subject if subject else None,
    global_context,
    generate_assessments,
    auto_categorize and not subject,
    base_dir=output_base_dir,
    parallel=use_parallel,           # ❌ Parameter doesn't exist anymore
    max_workers=max_workers,         # ❌ Parameter doesn't exist anymore
    export_pdf=export_pdf,
    pdf_theme=pdf_theme
)
```

**Current Signature** (from `app_interface.py:27-35`):
```python
def create_processor(
    subject: Optional[str] = None,
    global_context: Optional[str] = None,
    generate_assessments: bool = True,
    auto_categorize: bool = True,
    base_dir: Optional[str] = None,
    export_pdf: bool = False,
    pdf_theme: str = 'default'
) -> 'YouTubeStudyNotes':
```

#### Error 2: `process_video()` called with removed parameter

**Location**: `streamlit_app.py:453`

```python
# BROKEN CODE:
result = processor.process_video(url, worker_id=worker_id)  # ❌ worker_id doesn't exist
```

**Current Signature** (from `app_interface.py:48-50`):
```python
def process_video(self, video_url: str) -> Dict[str, Any]:
    """Process a single video and return results"""
    # No worker_id parameter
```

#### Error 3: Parallel processing code still present

**Location**: `streamlit_app.py:762-780`

```python
# Code tries to process videos in parallel using ThreadPoolExecutor
if use_parallel and len(urls) > 1:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # ... parallel processing logic
```

**Problem**: After LangGraph migration, parallel processing should be handled by SQS + Lambda auto-scaling, not client-side threading.

### Files Requiring Updates

#### 1. `streamlit_app.py` (Primary fixes)

**Line 742-743**: Remove `parallel` and `max_workers` parameters
```python
# BEFORE:
processor = create_processor(
    subject if subject else None,
    global_context,
    generate_assessments,
    auto_categorize and not subject,
    base_dir=output_base_dir,
    parallel=use_parallel,           # REMOVE
    max_workers=max_workers,         # REMOVE
    export_pdf=export_pdf,
    pdf_theme=pdf_theme
)

# AFTER:
processor = create_processor(
    subject if subject else None,
    global_context,
    generate_assessments,
    auto_categorize and not subject,
    base_dir=output_base_dir,
    export_pdf=export_pdf,
    pdf_theme=pdf_theme
)
```

**Line 453**: Remove `worker_id` parameter
```python
# BEFORE:
result = processor.process_video(url, worker_id=worker_id)

# AFTER:
result = processor.process_video(url)
```

**Lines 762-780**: Simplify to sequential processing only
```python
# BEFORE: Complex parallel/sequential logic with ThreadPoolExecutor

# AFTER: Simple sequential processing
for i, url in enumerate(urls, 1):
    st.write(f"Processing video {i}/{len(urls)}: {url}")
    try:
        result = processor.process_video(url)
        results.append(result)
        st.success(f"✓ Completed: {result.get('title', 'Unknown')}")
    except Exception as e:
        st.error(f"✗ Failed: {str(e)}")
        results.append({"url": url, "error": str(e)})
```

**Lines 612-637**: Remove commented-out parallel processing UI code
- This code is already commented out but should be deleted entirely
- It references the old parallel processing system

#### 2. UI Cleanup (Optional but Recommended)

**Remove Parallel Processing Settings**:
- Lines 689-705: "Parallel Processing Settings" expander
- These UI controls are no longer functional with LangGraph
- Simplifies user experience

### Why the Interface Shield Failed

The `app_interface.py` module was designed to provide a stable API that wouldn't change when internals changed. However:

1. **Parallel processing was a core feature** of the old design
2. **Removing it changed the interface itself**, not just the implementation
3. **The shield worked correctly** - it removed the parameters from its own API
4. **But the UI wasn't updated** to match the new shield API

This is a good example of why API changes need coordinated updates across all consumers, even with abstraction layers.

### Testing After Fix

After implementing the fixes:

1. **Single Video Test**:
   ```bash
   uv run streamlit run streamlit_app.py
   # Enter a single YouTube URL
   # Verify it processes successfully
   ```

2. **Multiple Videos Test**:
   ```bash
   # Enter 3-5 YouTube URLs (one per line)
   # Verify they process sequentially
   # Check that progress updates correctly
   ```

3. **Error Handling Test**:
   ```bash
   # Try an invalid URL
   # Verify error messages are helpful
   ```

4. **Export Test**:
   ```bash
   # Enable PDF export
   # Process a video
   # Verify PDF is generated correctly
   ```

### Migration Notes for Future Reference

**What Changed in LangGraph Migration**:
- Old: Imperative pipeline with manual state management
- New: Declarative state graph with automatic state transitions
- Old: Client-side parallel processing (ThreadPoolExecutor)
- New: Sequential client processing (scaling handled by SQS + Lambda)
- Old: Worker coordination via shared Tor instance
- New: Each video is independent (no coordination needed)

**Design Decision**:
The LangGraph migration intentionally removed parallel processing from the CLI because:
1. SQS + Lambda provides better scaling
2. No need for complex worker coordination
3. Simpler error handling (one video = one state machine)
4. Easier to debug and monitor

The Streamlit app should follow the same philosophy - process videos sequentially and let the backend handle scaling.

### Estimated Fix Time

- **Code changes**: 30-45 minutes
- **Testing**: 30 minutes
- **Total**: ~1.5 hours

### Success Criteria

After the fix is complete:
- [ ] No `TypeError` exceptions when processing videos
- [ ] Single video processing works correctly
- [ ] Multiple videos process sequentially with progress updates
- [ ] Error messages are clear and helpful
- [ ] PDF export still works (if enabled)
- [ ] UI is clean (no vestigial parallel processing controls)
