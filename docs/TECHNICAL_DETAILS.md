# Technical Implementation Details

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Set your Claude API key in .env
echo "CLAUDE_API_KEY=your_key_here" > .env

# 2. Start services
docker-compose up -d

# 3. Open browser
open http://localhost:8501
```

### Streamlit Web Interface

```bash
# Simple way - use the startup script
./start_streamlit.sh

# Or manually with uv
unset VIRTUAL_ENV  # Clear any conflicting venv
uv run python -m streamlit run streamlit_app.py
```

### Using CLI (Local Development)

```bash
# Install dependencies first
uv sync

# Sequential processing
uv run yt-study-buddy https://youtu.be/VIDEO_ID

# Parallel processing (3 workers)
uv run yt-study-buddy --parallel --workers 3 \
  https://youtu.be/VIDEO1 \
  https://youtu.be/VIDEO2 \
  https://youtu.be/VIDEO3

# View processing logs
cat notes/processing_log.json | jq '.'
```

---

## LangGraph-Powered Workflow

This project uses **LangGraph** for a deterministic, stateful processing pipeline that's easy to debug and extend.

### Workflow Architecture

The workflow consists of conditional nodes that execute based on configuration:

```
START → [Auto-Categorize?] → Fetch Transcript → Generate Notes
  → [Assessment?] → Write Files → Obsidian Links
  → [PDF Export?] → Log → END
```

### Benefits

- **Visual debugging** - See exactly where processing fails
- **Automatic checkpointing** - Resume from any failed node
- **Easy to extend** - Add new features by adding nodes/edges
- **Better testing** - Test individual nodes in isolation

### Implementation Files

- `src/yt_study_buddy/workflow_state.py` - State schema (TypedDict)
- `src/yt_study_buddy/workflow_nodes.py` - Node functions (8 nodes)
- `src/yt_study_buddy/langgraph_workflow.py` - Workflow graph definition

See `docs/LANGGRAPH_MIGRATION.md` for full migration details.

### LangSmith Tracing & Debugging

LangSmith integration is built into `debug_cli.py` for workflow debugging:

```bash
# 1. Add to .env
echo "LANGSMITH_API_KEY=lsv2_pt_xxxxx" >> .env

# 2. Run debug_cli.py
uv run python debug_cli.py

# 3. View traces at https://smith.langchain.com/
```

**What you'll see:**
- Visual workflow execution timeline
- State changes at each node
- Node-level timing and performance
- Error traces with full context
- Conditional edge decisions

See `docs/LANGSMITH_QUICK_START.md` for setup and `docs/LANGSMITH_TRACING.md` for full guide.

---

## Docker Setup

### Volumes

The docker-compose configuration uses volumes for data persistence:

**`./notes`** (bind mount) - Study notes output
- Appears on host at `./notes/`
- Organized by subject
- Contains markdown files and PDFs

### Managing Data

```bash
# View processing log
cat notes/processing_log.json | jq '.'

# Backup notes
tar czf notes-backup.tar.gz notes/

# Restore notes
tar xzf notes-backup.tar.gz
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## File Organization

```
notes/
├── processing_log.json           # Complete job history
├── AI/
│   ├── video_title_1.md
│   ├── Assessment_video_title_1.md
│   └── pdfs/
│       └── video_title_1.pdf
└── Programming/
    └── ...
```

---

## Processing Log

Every job (success/failure) is logged to `notes/processing_log.json`:

```json
{
  "video_id": "abc123",
  "worker_id": 2,
  "success": true,
  "processing_duration": 58.8,
  "retry_count": 0,
  "timings": {
    "fetch_transcript": 5.2,
    "generate_notes": 20.3,
    "generate_assessment": 28.1,
    "write_files": 0.7
  },
  "error": null
}
```

### Query Examples

```bash
# Failed jobs only
cat notes/processing_log.json | jq '.[] | select(.success == false)'

# Average processing time
cat notes/processing_log.json | jq '[.[] | select(.success) | .processing_duration] | add / length'

# Jobs from specific worker
cat notes/processing_log.json | jq '.[] | select(.worker_id == 2)'

# Last 10 jobs
cat notes/processing_log.json | jq '.[-10:]'
```

---

## Performance

### Parallel Processing

- **3 Workers:** ~54% faster than sequential processing
- **Job Logging:** Complete audit trail of all processing attempts
- **Worker Coordination:** Shared resources managed via coordination layer

### Benchmarks

```bash
# Sequential (1 video)
Average: ~30-40s per video

# Parallel (3 videos, 3 workers)
Average: ~35s total (vs ~120s sequential)
Speedup: ~54%
```

---

## Development

### Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_langgraph_workflow.py -v
```

### Testing

```bash
# Quick smoke tests
uv run pytest tests/test_quick_smoke.py -v

# LangGraph workflow tests
uv run pytest tests/test_langgraph_workflow.py -v

# All tests
uv run pytest
```

### Debugging

Use `debug_cli.py` for interactive debugging:

```python
# Edit debug_cli.py
CLI_ARGS = [
    '--debug-logging',
    'https://youtu.be/VIDEO_ID',
]

# Run with debugger
uv run python debug_cli.py
```

With LangSmith enabled, view execution traces at https://smith.langchain.com/

---

## Project Structure

```
YouTube-Studdy-Buddy/
├── src/yt_study_buddy/        # Main package
│   ├── workflow_state.py      # LangGraph state schema
│   ├── workflow_nodes.py      # LangGraph nodes
│   ├── langgraph_workflow.py  # Workflow definition
│   ├── cli.py                 # CLI entry point
│   ├── video_processor.py     # Video fetching
│   ├── study_notes_generator.py
│   ├── assessment_generator.py
│   └── ...
├── tests/                     # Test suite
├── docs/                      # Documentation
│   ├── LANGGRAPH_MIGRATION.md
│   ├── LANGSMITH_TRACING.md
│   └── TECHNICAL_DETAILS.md
├── debug_cli.py               # Debug wrapper
├── streamlit_app.py           # Web interface
└── pyproject.toml            # Dependencies
```

---

## Architecture Details

### Core Components

1. **VideoProcessor** - Handles transcript fetching from YouTube
2. **StudyNotesGenerator** - Claude API integration for notes
3. **AssessmentGenerator** - Quiz generation with gap analysis
4. **AutoCategorizer** - ML-based subject detection using sentence transformers
5. **ObsidianLinker** - Knowledge graph and wiki-link generation
6. **PDFExporter** - Markdown to PDF conversion

### Data Flow

```
YouTube URL
  ↓
[Optional: Auto-Categorize]
  ↓
Fetch Transcript
  ↓
Generate Study Notes (Claude API)
  ↓
[Optional: Generate Assessment]
  ↓
Write Markdown Files
  ↓
Add Obsidian Links (Knowledge Graph)
  ↓
[Optional: Export PDFs]
  ↓
Log to processing_log.json
```

### State Management

The LangGraph workflow uses `VideoProcessingState` (TypedDict) to track all processing state:

- Input: URL, video_id, configuration
- Fetched: transcript, video_title
- Generated: study_notes, assessment
- Output: file paths
- Status: failed, completed, error
- Timing: processing_duration, per-node timings

See `src/yt_study_buddy/workflow_state.py` for full schema.

---

## API Integration

### Claude API

Used for:
- Study notes generation
- Assessment question generation
- Title extraction (when needed)

Model: `claude-sonnet-4-5-20250929`

---

## Environment Variables

```bash
# Required
CLAUDE_API_KEY=sk-ant-xxxxx

# Optional
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
GENERATE_NOTES_MODEL=claude-sonnet-4-5-20250929

# LangSmith Tracing (optional)
LANGSMITH_API_KEY=lsv2_pt_xxxxx
```

See `.env.example` for full reference.

---

## Extending the Workflow

### Adding a New Node

1. Create node function in `workflow_nodes.py`:
```python
def my_new_node(state: VideoProcessingState, my_component) -> VideoProcessingState:
    # Do work
    state['my_field'] = result
    return state
```

2. Update state schema in `workflow_state.py`:
```python
class VideoProcessingState(TypedDict, total=False):
    # ... existing fields
    my_field: Optional[str]
```

3. Add to workflow in `langgraph_workflow.py`:
```python
workflow.add_node("my_new_node", my_new_node_fn)
workflow.add_edge("previous_node", "my_new_node")
workflow.add_edge("my_new_node", "next_node")
```

### Adding Conditional Logic

```python
def should_do_something(state: VideoProcessingState) -> Literal["do_it", "skip_it"]:
    if state.get('some_condition'):
        return "do_it"
    return "skip_it"

workflow.add_conditional_edges(
    "previous_node",
    should_do_something,
    {
        "do_it": "action_node",
        "skip_it": "next_node"
    }
)
```

---

## Contributing

See main README for contribution guidelines.

## License

GNU Affero General Public License v3.0 - See LICENSE file for details.
