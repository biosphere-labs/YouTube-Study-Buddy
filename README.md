# YouTube Study Buddy

Learning from educational YouTube videos and want to maximize retention? **YT Study Buddy** transforms passive video watching into active learning by generating structured study notes with intelligent cross-referencing and targeted assessment questions. The system builds your personal knowledge graph over time, connecting concepts across videos, while quiz-style assessments test understanding beyond surface-level recall—turning scattered video content into an interconnected learning system that actually improves retention.

This repository contains the **open-source CLI package** for self-hosted use. A managed web application will be available as a subscription service (launching mid-December 2025).

## 🧠 The Science: Active Learning vs Passive Watching

**Traditional passive note-taking** often leads to the "illusion of competence" – where learners feel they understand content simply because they've transcribed it. YT Study Buddy implements research-backed learning principles:

- **Dual Coding Theory** – Combines text with visual spatial organization for stronger memory formation
- **Generation Effect** – Assessment questions force active answer generation, improving retention
- **Desirable Difficulties** – "One-up" challenges introduce productive struggle beyond the presented material
- **Elaborative Interrogation** – Gap analysis questions reveal what your brain filtered out
- **Spaced Retrieval Practice** – Separation of note generation from video watching enables spaced review

**Result:** Instead of passive consumption, you get an active learning system with notes AND assessment questions that test understanding beyond surface-level recall.

## 📦 Available Options

### Open Source CLI (This Repository)
- **Free and open source** - Self-hosted on your own infrastructure
- Outputs Markdown files compatible with Obsidian for personal knowledge management
- Includes Streamlit web interface (via Docker) for local browser-based processing
- Full AI-powered note generation and assessments
- Requires technical setup (Python, Claude API key)
- Complete control over your data and processing
- Ideal for developers, researchers, and self-hosters

### Managed Web Application (Coming Mid-December 2025)
- **Subscription-based service** - No setup required
- Interactive assessments directly in the browser
- MindMesh integration - browser-based knowledge graph visualization and navigation
- Automatic updates and maintenance
- Ideal for students and educators who want a ready-to-use solution

## Features

### Core Capabilities
- 🤖 **AI-Powered Notes** - Claude Sonnet 4.5 generates comprehensive study materials
- 📝 **Learning Assessments** - Automatic quiz generation with gap analysis
- 🏷️ **Auto-Categorization** - ML-based subject detection
- 📊 **Knowledge Graph** - Cross-reference related concepts
- 📄 **PDF Export** - Multiple themes (Obsidian, Academic, Minimal)

**[Technical Details](docs/TECHNICAL_DETAILS.md)** - LangGraph workflow, Docker setup, development guide

## 🏗️ Architecture Overview

The complete YouTube Study Buddy system is organized into **4 separate repositories** for modularity, scalability, and separation of concerns:

1. **Core CLI Package** (This Repository - Open Source)
   - Standalone command-line tool for local use
   - Python package installable via pip/uv
   - Can run in Docker or as a systemd service
   - LangGraph-powered workflow with automatic checkpointing

2. **Backend Package**
   - Service classes for video processing, notes generation, and user management
   - Shared utilities for DynamoDB, S3, and authentication
   - Monthly subscription management
   - Python 3.12+ compatible for AWS Lambda deployment

3. **Infrastructure**
   - Terraform infrastructure as code (IaC)
   - AWS Lambda function deployment
   - DynamoDB, S3, API Gateway, CloudFront, Cognito configuration
   - Serverless architecture for scalability

4. **Web Application** (In Development)
   - React application
   - Cognito authentication with Google sign-in
   - Browser-based interface for subscription users
   - Interactive assessments that adapt based on your responses to facilitate deeper learning

> **Note:** Only the CLI package (this repository) is open source. The managed web application, backend services, and infrastructure will be part of the subscription service launching mid-December 2025.

### Processing Workflow

The CLI uses a LangGraph-powered workflow for deterministic, resumable processing:

![Workflow Diagram](docs/workflow_diagram.png)

Each video processes through conditional nodes based on your configuration (auto-categorization, assessments, PDF export).

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
