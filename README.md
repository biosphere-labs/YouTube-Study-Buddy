# YouTube Study Buddy

Transform YouTube educational videos into structured study notes with AI-powered cross-referencing for **Obsidian** knowledge bases.

## 🎯 What It Does

- **AI-Generated Study Notes** – Claude AI creates comprehensive notes from YouTube video transcripts
- **Learning Assessments** – Auto-generated quiz questions to test understanding
- **Obsidian Integration** – Creates `[[wiki-style]]` links between related notes
- **Knowledge Graph** – Automatically finds connections across all your study notes
- **Auto-Categorization** – ML-based subject detection organizes notes by topic
- **PDF Export** – Export notes with Obsidian-compatible styling

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Claude API key ([get free key](https://console.anthropic.com/))
- Obsidian (optional, for viewing the linked knowledge base)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/fluidnotions/YouTube-Study-Buddy.git
cd YouTube-Study-Buddy

# 2. Create .env file with your API key
echo "CLAUDE_API_KEY=your_key_here" > .env
echo "USER_ID=$(id -u)" >> .env
echo "GROUP_ID=$(id -g)" >> .env

# 3. Start the app
docker-compose up -d

# 4. Open Streamlit UI
open http://localhost:8501
```

That's it! The Streamlit interface will guide you through processing videos.

### Managing the App

```bash
# View logs
docker logs -f youtube-study-buddy

# Stop
docker-compose down

# Restart
docker-compose restart
```

## 📚 Obsidian Integration

### Local Use (Recommended)

Mount your Obsidian vault's notes directory to enable [[wiki-links]] between notes:

```bash
# Edit docker-compose.yml
volumes:
  - /path/to/your/obsidian/vault:/app/notes  # Replace with your path
  - tracker-data:/app/tracker
```

Then process videos in the Streamlit UI with:
- **Subject**: Specify a subject (creates `/notes/Subject/` folder)
- **Global cross-referencing**: ✓ Enable to link across all subjects

The linker will create `[[links]]` to related notes in your vault.

### How Cross-Referencing Works

**Global Context** (default):
- Searches across ALL subjects for related concepts
- Creates links like: "This concept relates to [[Neural Networks]] (AI subject)"

**Subject-Only Context**:
- Only links within the specified subject
- Use `--subject-only` flag or disable "Global" in Streamlit

Example with CLI:
```bash
# Global cross-referencing (links across all subjects)
docker exec youtube-study-buddy uv run yt-study-buddy --subject "AI" https://youtube.com/watch?v=xyz

# Subject-only (links within AI subject only)
docker exec youtube-study-buddy uv run yt-study-buddy --subject "AI" --subject-only https://youtube.com/watch?v=xyz
```

### Viewing in Obsidian

1. Point Obsidian to your notes directory
2. Notes appear as markdown files with `[[wiki-links]]`
3. Use Obsidian's graph view to visualize connections
4. Click links to navigate between related concepts

## ⚙️ Configuration

### Processing Options (Streamlit UI)

- **Subject** – Organize notes by topic (creates subdirectories)
- **Global cross-referencing** – Find links across all subjects vs. subject-only
- **Generate Assessments** – Create quiz questions
- **Auto-categorize** – ML detects subject when not specified
- **Export PDF** – Generate PDFs with Obsidian styling

### File Organization

```
notes/
├── AI/
│   ├── Neural_Networks_Intro.md          # Study notes with [[links]]
│   ├── Assessment_Neural_Networks_Intro.md
│   └── pdfs/
│       └── Neural_Networks_Intro.pdf
├── Machine_Learning/
│   └── ...
└── processing_log.json                    # Job history
```

## 🎓 Learning Features

### Study Notes Include:
- **Core Concepts** – Key ideas extracted from transcript
- **Definitions** – Technical terms explained
- **Key Points** – Important takeaways
- **Cross-References** – `[[Links]]` to related notes
- **Source** – YouTube URL and video metadata

### Assessment Questions:
- **Comprehension** – Test understanding of concepts
- **Gap Analysis** – Identify what you might have missed
- **One-Up Questions** – Go beyond the video content

## 🌐 For Streamlit Cloud Deployment

The session-based deployment (from `feat/streamlit-deployment` branch) is designed for public hosting where:
- Users provide their own Claude API key
- Each session gets isolated storage
- Users download notes as ZIP when done
- No Obsidian integration (no shared vault)

For personal use with Obsidian, use the Docker setup described above.

## 🔧 Technical Details

### Architecture
- **tor-proxy** container: Bypasses YouTube rate limiting
- **app** container: Streamlit UI + Python processing
- **Tor circuit rotation**: Automatic IP rotation on retries

### Why Tor?
YouTube blocks repeated transcript requests from the same IP. Tor routing solves this for batch processing.

## 📝 License

GNU Affero General Public License v3.0 or later

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation.

---

**⭐ If you find this useful, please star the repo!** It helps others discover the project.
