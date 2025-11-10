# YouTube Study Buddy

Learning from educational YouTube videos and want to maximize retention and build meaningful connections? **YT Study Buddy** transforms any YouTube video into structured study notes with intelligent cross-referencing that builds your personal knowledge graph over time, turning scattered video content into an interconnected learning system.

## 🏗️ Architecture Overview

This project is organized into **5 separate repositories** for modularity, scalability, and ease of deployment:

1. **[YouTube-Studdy-Buddy](https://github.com/yourusername/YouTube-Studdy-Buddy)** (This Repository) - Core CLI Package
   - Standalone command-line tool for local use
   - Python package installable via pip/uv
   - Can run in Docker or as a systemd service

2. **[ytsb-Backend](https://github.com/yourusername/ytsb-Backend)** - Business Logic Package
   - Service classes for video processing, notes, credits, MindMesh
   - Shared utilities for DynamoDB, S3, and authentication
   - Python 3.12+ compatible for Lambda deployment

3. **[YouTube-Study-Buddy-Infrastructure](https://github.com/yourusername/YouTube-Study-Buddy-Infrastructure)** - AWS Deployment
   - Terraform infrastructure as code (IaC)
   - Lambda function deployment scripts
   - DynamoDB, S3, API Gateway, CloudFront, Cognito configuration

4. **[YouTube-Study-Buddy-Frontend](https://github.com/yourusername/YouTube-Study-Buddy-Frontend)** - Web Application
   - Next.js React application
   - Cognito authentication integration
   - Deployed to S3 + CloudFront

5. **[YouTube-Study-Buddy-Docs](https://github.com/yourusername/YouTube-Study-Buddy-Docs)** - Documentation
   - API documentation
   - Deployment guides
   - Architecture decision records

### Deployment Options

- **Local/Docker**: Use this repository directly (see Quick Start below)
- **AWS Serverless**: Deploy via Infrastructure repository for scalable cloud hosting
- **Self-Hosted**: Run as systemd service or in your own infrastructure

## 🧠 The Science: Active Learning vs Passive Watching

**Traditional passive note-taking** often leads to the "illusion of competence" – where learners feel they understand content simply because they've transcribed it. YT Study Buddy implements research-backed learning principles:

- **Dual Coding Theory** – Combines text with visual spatial organization for stronger memory formation
- **Generation Effect** – Assessment questions force active answer generation, improving retention
- **Desirable Difficulties** – "One-up" challenges introduce productive struggle beyond the presented material
- **Elaborative Interrogation** – Gap analysis questions reveal what your brain filtered out
- **Spaced Retrieval Practice** – Separation of note generation from video watching enables spaced review

**Result:** Instead of passive consumption, you get an active learning system with notes AND assessment questions that test understanding beyond surface-level recall.

## 💰 Free vs Paid Alternatives

**Paid ($10-50+/month):** NoteGPT, Notta, Eightify, Maestra – all require subscriptions for full features

**Free (Limited):** Basic transcripts, no AI analysis, no cross-referencing, no assessments

**YT Study Buddy:** Completely free with AI-powered notes, learning assessments, auto-categorization, and knowledge graph building. No subscriptions, no limits.

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

### Quick Start - Streamlit Web Interface

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

## Features

### Core Capabilities
- 🤖 **AI-Powered Notes** - Claude Sonnet 4.5 generates comprehensive study materials
- 📝 **Learning Assessments** - Automatic quiz generation with gap analysis
- 🏷️ **Auto-Categorization** - ML-based subject detection
- 📊 **Knowledge Graph** - Cross-reference related concepts
- 📄 **PDF Export** - Multiple themes (Obsidian, Academic, Minimal)

## Docker Setup

### Volumes

The docker-compose configuration uses volumes for data persistence:

1. **`./notes`** (bind mount) - Study notes output
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

## Processing Log

Every job (success/failure) logged to `notes/processing_log.json`:

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
```

## Web Interface

The Streamlit UI shows:

- **Process Videos** - Batch processing with playlist extraction
- **Results** - Knowledge graph and cross-references
- **Logs** - Processing history with failure details
  - Human-readable timestamps ("2 hours ago")
  - Failure reasons
  - Retry count

## Performance

### Parallel Processing
- **3 Workers:** ~54% faster than sequential
- **Job Logging:** Complete audit trail

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
