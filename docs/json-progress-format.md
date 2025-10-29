# JSON Progress Output Format

This document describes the JSON progress output format for API integration.

## Overview

The CLI supports a `--format json-progress` flag that outputs real-time progress events as JSON to stdout, enabling FastAPI backends to track processing status.

## Usage

```bash
youtube-study-buddy --format json-progress <url>
```

When `--format json-progress` is enabled:
- JSON progress events are written to stdout (one per line)
- Logs are redirected to stderr at WARNING level
- Each event is immediately flushed for real-time streaming

## JSON Event Format

All events have the following base structure:

```json
{
  "step": "step_identifier",
  "progress": 0.0,
  "message": "Human-readable message"
}
```

### Progress Steps

Events are emitted at the following stages:

| Step | Progress | Description |
|------|----------|-------------|
| `starting` | 10% | Processing started |
| `fetching_transcript` | 25% | Fetching YouTube transcript |
| `calling_claude` | 40% | Calling Claude API |
| `generating_notes` | 60% | Generating study notes |
| `generating_assessment` | 75% | Generating assessment questions |
| `writing_files` | 85% | Writing markdown files |
| `creating_links` | 88% | Creating cross-references |
| `exporting_pdf` | 90% | Exporting to PDF (if enabled) |
| `completed` | 100% | Processing complete |
| `error` | 0% | Error occurred |

## Event Examples

### Starting
```json
{"step": "starting", "progress": 10.0, "message": "Starting processing..."}
```

### Fetching Transcript
```json
{"step": "fetching_transcript", "progress": 25.0, "message": "Fetching transcript..."}
```

### Calling Claude API
```json
{"step": "calling_claude", "progress": 40.0, "message": "Calling Claude API..."}
```

### Generating Notes
```json
{"step": "generating_notes", "progress": 60.0, "message": "Generating study notes..."}
```

### Generating Assessment
```json
{"step": "generating_assessment", "progress": 75.0, "message": "Generating assessment..."}
```

### Writing Files
```json
{"step": "writing_files", "progress": 85.0, "message": "Writing markdown files..."}
```

### Creating Cross-References
```json
{"step": "creating_links", "progress": 88.0, "message": "Creating cross-references..."}
```

### Exporting PDF
```json
{"step": "exporting_pdf", "progress": 90.0, "message": "Exporting to PDF..."}
```

### Completion Event
```json
{
  "step": "completed",
  "progress": 100.0,
  "message": "Processing complete!",
  "output_path": "/path/to/notes/Video_Title.md",
  "duration_seconds": 45.3,
  "video_id": "abc123xyz",
  "video_title": "Video Title"
}
```

### Error Event
```json
{
  "step": "error",
  "progress": 0,
  "message": "Error: Transcript fetch failed",
  "error": "Transcript fetch failed",
  "failed_step": "fetching_transcript"
}
```

## FastAPI Integration Example

Here's a simple example of consuming the JSON progress output:

```python
import subprocess
import json
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/process/{video_id}")
async def process_video(websocket: WebSocket, video_id: str):
    await websocket.accept()

    # Start CLI process with JSON output
    process = subprocess.Popen(
        ["youtube-study-buddy", "--format", "json-progress", f"https://youtube.com/watch?v={video_id}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    # Stream progress to websocket
    for line in process.stdout:
        try:
            event = json.loads(line)
            await websocket.send_json(event)

            if event["step"] == "completed":
                break
            elif event["step"] == "error":
                await websocket.close(code=1011, reason=event["error"])
                break
        except json.JSONDecodeError:
            continue

    process.wait()
```

## Implementation Details

### ProgressReporter Class

Located in `src/yt_study_buddy/progress_reporter.py`:

```python
from yt_study_buddy.progress_reporter import (
    ProgressReporter,
    ProgressStep,
    init_progress_reporter,
    get_progress_reporter
)

# Initialize (done automatically in CLI)
init_progress_reporter(enabled=True)

# Get global instance
reporter = get_progress_reporter()

# Report progress
reporter.report_step(ProgressStep.FETCHING_TRANSCRIPT, 25.0, "Fetching...")

# Report completion
reporter.report_complete("/path/to/output.md", video_id="abc123")

# Report error
reporter.report_error("Error message", step="fetching_transcript")
```

### Backward Compatibility

The default behavior is unchanged:
- Without `--format json-progress`, normal console output is used
- Existing scripts and workflows continue to work without modification
- The progress reporter is disabled by default

## Testing

Run tests with:
```bash
pytest tests/test_json_progress.py -v
```

Tests cover:
- Enabled/disabled reporter states
- Progress step reporting
- Error handling
- Completion events
- Multiple progress events in sequence
- JSON format validation
