# FastAPI Wrapper Architecture for YouTube Study Buddy

## Overview

This document outlines the architecture for wrapping the existing Python CLI with a FastAPI REST API backend, enabling a React web application with authentication, payment processing, and usage credits.

## Current State

**Existing System:**
- Python CLI (`yt-study-buddy`) with Streamlit UI
- YouTube transcript extraction with Tor proxy for rate limiting
- Claude API integration for note generation
- Obsidian integration with wiki-links
- Multi-Tor parallel processing (5 Tor instances)
- Docker Compose orchestration

## New Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                  React Frontend (Vite)                       │
│                  http://localhost:5173                       │
│                                                               │
│  Features:                                                   │
│  - Dashboard (usage stats, credits, recent videos)          │
│  - Video submission with real-time progress                 │
│  - Note viewing and editing                                 │
│  - Social sign-in (Google, GitHub, Discord)                 │
│  - Credit purchase (Stripe integration)                     │
│  - User settings                                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP/REST + WebSocket (Socket.IO)
                  │
┌─────────────────▼───────────────────────────────────────────┐
│               FastAPI Backend                                │
│               http://localhost:8000                          │
│                                                               │
│  Routes:                                                     │
│  - /auth/* - Social OAuth + JWT                             │
│  - /videos/* - Submit, list, status                         │
│  - /notes/* - CRUD operations                               │
│  - /credits/* - Purchase, check balance                     │
│  - /jobs/* - Job status, progress                           │
│  - /ws - WebSocket for real-time updates                    │
│                                                               │
│  Services:                                                   │
│  - AuthService - JWT, OAuth providers                       │
│  - VideoService - Wraps Python CLI                          │
│  - NoteService - Note management                            │
│  - CreditService - Usage tracking, payments                 │
│  - JobService - Background job queue                        │
└─┬───────────┬───────────────┬──────────────────────────────┘
  │           │               │
  │           │               │ Spawns subprocess
  │           │               │
┌─▼──────────┐│           ┌───▼──────────────────────────────┐
│ PostgreSQL ││           │ Python CLI (uv run yt-study-buddy)│
│   :5432    ││           │                                   │
│            ││           │ - Multi-Tor parallel processing   │
│ - users    ││           │ - YouTube transcript extraction   │
│ - videos   ││           │ - Claude API processing           │
│ - notes    ││           │ - Note generation                 │
│ - jobs     ││           │ - Assessment creation             │
│ - credits  ││           │                                   │
│ - payments ││           │ Output: JSON progress + final MD  │
└────────────┘│           └───────────────────────────────────┘
              │
          ┌───▼─────────┐
          │    Redis    │
          │    :6379    │
          │             │
          │ - Job Queue │
          │ - Sessions  │
          │ - Progress  │
          └─────────────┘
```

## Backend Components

### 1. FastAPI Application Structure

```
api/
├── main.py                 # FastAPI app entry point
├── config.py               # Configuration (env vars, settings)
├── dependencies.py         # Dependency injection
│
├── auth/
│   ├── router.py           # Auth endpoints
│   ├── service.py          # OAuth, JWT logic
│   ├── models.py           # User, Session models
│   └── providers.py        # Google, GitHub, Discord OAuth
│
├── videos/
│   ├── router.py           # Video endpoints
│   ├── service.py          # CLI wrapper
│   ├── models.py           # Video, VideoJob models
│   └── schemas.py          # Pydantic schemas
│
├── notes/
│   ├── router.py           # Note endpoints
│   ├── service.py          # CRUD operations
│   ├── models.py           # Note model
│   └── schemas.py          # Pydantic schemas
│
├── credits/
│   ├── router.py           # Credit endpoints
│   ├── service.py          # Usage tracking
│   ├── models.py           # Credit, Transaction models
│   └── stripe_client.py    # Stripe integration
│
├── jobs/
│   ├── router.py           # Job status endpoints
│   ├── service.py          # Job management
│   ├── worker.py           # Background worker
│   └── models.py           # Job model
│
├── websocket/
│   ├── connection.py       # WebSocket manager
│   └── events.py           # Event types
│
└── core/
    ├── database.py         # SQLAlchemy setup
    ├── redis_client.py     # Redis connection
    ├── cli_wrapper.py      # Python CLI subprocess wrapper
    └── middleware.py       # Auth, CORS, rate limiting
```

### 2. Database Schema (PostgreSQL + SQLAlchemy)

```python
# users table
User:
  - id: UUID (PK)
  - email: String (unique)
  - name: String
  - avatar_url: String
  - provider: Enum (google, github, discord)
  - provider_id: String
  - credits: Integer (default: 10)  # Free tier
  - subscription_tier: Enum (free, pro, enterprise)
  - created_at: DateTime
  - updated_at: DateTime

# videos table
Video:
  - id: UUID (PK)
  - user_id: UUID (FK -> users)
  - youtube_url: String
  - youtube_id: String
  - title: String
  - channel: String
  - duration: Integer (seconds)
  - subject: String (nullable)
  - status: Enum (pending, processing, completed, failed)
  - credits_used: Integer
  - created_at: DateTime
  - updated_at: DateTime

# notes table
Note:
  - id: UUID (PK)
  - video_id: UUID (FK -> videos)
  - user_id: UUID (FK -> users)
  - title: String
  - content: Text (markdown)
  - summary: Text
  - assessment: JSON (nullable)
  - cross_references: JSON (list of note IDs)
  - created_at: DateTime
  - updated_at: DateTime

# jobs table
Job:
  - id: UUID (PK)
  - video_id: UUID (FK -> videos)
  - user_id: UUID (FK -> users)
  - status: Enum (queued, running, completed, failed)
  - progress: Float (0-100)
  - current_step: String
  - error_message: Text (nullable)
  - started_at: DateTime (nullable)
  - completed_at: DateTime (nullable)
  - created_at: DateTime

# credit_transactions table
CreditTransaction:
  - id: UUID (PK)
  - user_id: UUID (FK -> users)
  - amount: Integer (+ for purchase, - for usage)
  - type: Enum (purchase, usage, refund, bonus)
  - video_id: UUID (FK -> videos, nullable)
  - stripe_payment_id: String (nullable)
  - description: String
  - created_at: DateTime
```

### 3. API Endpoints

#### Authentication (`/auth`)

```
POST   /auth/login/{provider}        # Initiate OAuth flow
GET    /auth/callback/{provider}     # OAuth callback
POST   /auth/logout                  # Logout user
GET    /auth/me                      # Get current user
```

#### Videos (`/videos`)

```
POST   /videos                       # Submit video URL
GET    /videos                       # List user's videos
GET    /videos/{id}                  # Get video details
DELETE /videos/{id}                  # Delete video
GET    /videos/{id}/progress         # Get processing progress
```

#### Notes (`/notes`)

```
GET    /notes                        # List user's notes
GET    /notes/{id}                   # Get note details
PUT    /notes/{id}                   # Update note
DELETE /notes/{id}                   # Delete note
GET    /notes/{id}/export            # Export note as PDF/MD
```

#### Credits (`/credits`)

```
GET    /credits                      # Get credit balance
POST   /credits/purchase             # Purchase credits (Stripe)
GET    /credits/transactions         # Transaction history
POST   /credits/webhooks/stripe      # Stripe webhook handler
```

#### Jobs (`/jobs`)

```
GET    /jobs                         # List user's jobs
GET    /jobs/{id}                    # Get job status
POST   /jobs/{id}/cancel             # Cancel job
```

#### WebSocket (`/ws`)

```
WS     /ws                           # WebSocket connection
       Events:
       - job_progress (server -> client)
       - job_completed (server -> client)
       - job_failed (server -> client)
```

### 4. Python CLI Integration

The FastAPI backend wraps the existing Python CLI as a subprocess:

```python
# api/core/cli_wrapper.py

import asyncio
import json
from typing import AsyncGenerator

class CLIWrapper:
    """Wraps the Python CLI for video processing."""

    async def process_video(
        self,
        youtube_url: str,
        user_id: str,
        video_id: str,
        subject: str = None,
        worker_id: int = 0
    ) -> AsyncGenerator[dict, None]:
        """
        Spawn CLI subprocess and stream progress events.

        Yields:
            dict: Progress updates with structure:
                {
                    "step": "fetching_transcript",
                    "progress": 25.0,
                    "message": "Extracting transcript..."
                }
        """
        cmd = [
            "uv", "run", "yt-study-buddy",
            "--url", youtube_url,
            "--output", f"/app/data/users/{user_id}/videos/{video_id}",
            "--format", "json-progress",  # New flag for JSON output
            "--worker-id", str(worker_id)
        ]

        if subject:
            cmd.extend(["--subject", subject])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Stream progress from CLI stdout
        async for line in process.stdout:
            try:
                event = json.loads(line.decode())
                yield event
            except json.JSONDecodeError:
                continue

        await process.wait()

        if process.returncode != 0:
            stderr = await process.stderr.read()
            raise CLIError(stderr.decode())
```

### 5. Background Job Processing

Using `asyncio` + Redis for job queue:

```python
# api/jobs/worker.py

import asyncio
from redis import asyncio as aioredis
from api.core.cli_wrapper import CLIWrapper
from api.websocket.connection import ws_manager

async def process_video_job(job_id: str, video_id: str):
    """Background worker for video processing."""

    # Update job status
    await update_job_status(job_id, "running")

    # Get video details from database
    video = await get_video(video_id)

    # Process with CLI wrapper
    cli = CLIWrapper()

    try:
        async for progress in cli.process_video(
            youtube_url=video.youtube_url,
            user_id=str(video.user_id),
            video_id=str(video.id),
            subject=video.subject,
            worker_id=0  # Assign based on load balancing
        ):
            # Update job progress in database
            await update_job_progress(job_id, progress["progress"])

            # Emit WebSocket event
            await ws_manager.send_to_user(
                video.user_id,
                {
                    "type": "job_progress",
                    "job_id": job_id,
                    "video_id": video_id,
                    "progress": progress["progress"],
                    "step": progress["step"]
                }
            )

        # Mark complete
        await update_job_status(job_id, "completed")
        await ws_manager.send_to_user(
            video.user_id,
            {"type": "job_completed", "job_id": job_id, "video_id": video_id}
        )

    except Exception as e:
        await update_job_status(job_id, "failed", error=str(e))
        await ws_manager.send_to_user(
            video.user_id,
            {"type": "job_failed", "job_id": job_id, "error": str(e)}
        )
```

### 6. Credit System

**Pricing Model:**
- Free tier: 10 credits (sign up)
- 1 credit = 1 video processing
- Credit packs: 10 credits ($5), 50 credits ($20), 100 credits ($35)

**Implementation:**

```python
# api/credits/service.py

class CreditService:

    async def check_and_deduct(self, user_id: UUID, video_id: UUID) -> bool:
        """
        Check if user has credits and deduct one.

        Returns:
            bool: True if deducted, False if insufficient
        """
        user = await get_user(user_id)

        if user.credits < 1:
            return False

        # Deduct credit
        user.credits -= 1

        # Record transaction
        await create_transaction(
            user_id=user_id,
            amount=-1,
            type="usage",
            video_id=video_id,
            description=f"Video processing: {video_id}"
        )

        await db.commit()
        return True

    async def purchase_credits(
        self,
        user_id: UUID,
        amount: int,
        stripe_payment_id: str
    ):
        """Add credits after successful payment."""
        user = await get_user(user_id)
        user.credits += amount

        await create_transaction(
            user_id=user_id,
            amount=amount,
            type="purchase",
            stripe_payment_id=stripe_payment_id,
            description=f"Purchased {amount} credits"
        )

        await db.commit()
```

### 7. Authentication & Authorization

**OAuth Providers:**
- Google OAuth 2.0
- GitHub OAuth
- Discord OAuth

**JWT Token Flow:**

```python
# api/auth/service.py

from jose import jwt
from datetime import datetime, timedelta

class AuthService:

    async def create_access_token(self, user_id: UUID) -> str:
        """Generate JWT access token."""
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    async def verify_token(self, token: str) -> UUID:
        """Verify JWT and return user_id."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            return UUID(payload["sub"])
        except:
            raise AuthenticationError("Invalid token")

    async def oauth_callback(self, provider: str, code: str) -> User:
        """Handle OAuth callback and get/create user."""
        # Exchange code for access token
        user_info = await self._exchange_code(provider, code)

        # Get or create user
        user = await get_user_by_provider(provider, user_info["id"])

        if not user:
            user = await create_user(
                email=user_info["email"],
                name=user_info["name"],
                avatar_url=user_info["avatar"],
                provider=provider,
                provider_id=user_info["id"],
                credits=10  # Free tier credits
            )

        return user
```

**Middleware:**

```python
# api/core/middleware.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    """Dependency to get current authenticated user."""
    auth_service = AuthService()
    user_id = await auth_service.verify_token(token.credentials)
    user = await get_user(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

## Frontend (React)

### Tech Stack

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Routing:** TanStack Router
- **State Management:** Zustand + TanStack Query
- **UI Components:** shadcn/ui + Tailwind CSS
- **WebSocket:** Socket.IO client
- **HTTP Client:** Axios

### Key Features

1. **Dashboard**
   - Credit balance display
   - Usage statistics
   - Recent videos
   - Quick submit form

2. **Video Submission**
   - URL input with validation
   - Optional subject selection
   - Real-time progress bar (WebSocket)
   - Processing status updates

3. **Note Viewer**
   - Markdown rendering
   - Cross-reference navigation
   - Edit mode with preview
   - Export to PDF/MD

4. **Authentication**
   - Social sign-in buttons (Google, GitHub, Discord)
   - JWT token storage (localStorage)
   - Auto-refresh on token expiry
   - Protected routes

5. **Credit Management**
   - Balance display
   - Purchase modal with Stripe Elements
   - Transaction history
   - Low credit warnings

## Deployment

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ytstudy
      POSTGRES_USER: ytstudy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ytstudy"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  backend:
    build:
      context: .
      dockerfile: api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://ytstudy:${POSTGRES_PASSWORD}@postgres:5432/ytstudy
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./data:/app/data  # For user notes
      - ./src:/app/src    # For Python CLI access

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000
    depends_on:
      - backend

  # Multi-Tor instances for parallel processing
  tor-proxy-1:
    image: dperson/torproxy:latest
    ports:
      - "9050:9050"
      - "9051:9051"

  tor-proxy-2:
    image: dperson/torproxy:latest
    ports:
      - "9052:9052"
      - "9053:9053"

  tor-proxy-3:
    image: dperson/torproxy:latest
    ports:
      - "9054:9054"
      - "9055:9055"

  tor-proxy-4:
    image: dperson/torproxy:latest
    ports:
      - "9056:9056"
      - "9057:9057"

  tor-proxy-5:
    image: dperson/torproxy:latest
    ports:
      - "9058:9058"
      - "9059:9059"

volumes:
  postgres-data:
  redis-data:
```

## Migration Strategy

### Phase 1: API Development (2-3 weeks)
1. Set up FastAPI project structure
2. Implement database models (SQLAlchemy)
3. Create authentication endpoints (OAuth + JWT)
4. Wrap Python CLI as subprocess
5. Implement video submission endpoints
6. Add WebSocket for real-time progress
7. Integrate Stripe for payments

### Phase 2: Frontend Development (2-3 weeks)
1. Set up React + Vite project
2. Create authentication flow (social sign-in)
3. Build dashboard with stats
4. Implement video submission UI
5. Add WebSocket progress tracking
6. Create note viewer/editor
7. Build credit purchase flow

### Phase 3: Integration & Testing (1 week)
1. End-to-end testing
2. Load testing with multiple Tor instances
3. Security audit (auth, payments)
4. Docker Compose testing
5. Documentation

### Phase 4: Deployment (1 week)
1. Set up production environment
2. Configure domain and SSL
3. Set up monitoring (logging, metrics)
4. Deploy to cloud (AWS/DigitalOcean)
5. Marketing and launch

## Requirements

### CLI Modifications

The existing CLI needs to support JSON progress output:

```bash
# New flag: --format json-progress
uv run yt-study-buddy --url <url> --format json-progress

# Output format (streaming to stdout):
{"step": "fetching_transcript", "progress": 25.0, "message": "Extracting transcript..."}
{"step": "calling_claude", "progress": 50.0, "message": "Generating notes..."}
{"step": "creating_links", "progress": 75.0, "message": "Cross-referencing..."}
{"step": "completed", "progress": 100.0, "message": "Done!", "output_path": "/path/to/note.md"}
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ytstudy
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7

# OAuth Providers
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback/google

GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GITHUB_REDIRECT_URI=http://localhost:8000/auth/callback/github

DISCORD_CLIENT_ID=xxx
DISCORD_CLIENT_SECRET=xxx
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback/discord

# Payments
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Claude API
CLAUDE_API_KEY=your-claude-key

# CORS
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_STRIPE_PUBLIC_KEY=pk_test_xxx
```

## Security Considerations

1. **Authentication:**
   - JWT tokens with expiry
   - HttpOnly cookies for refresh tokens
   - OAuth state parameter validation
   - CSRF protection

2. **Authorization:**
   - User can only access their own videos/notes
   - Credit checks before processing
   - Rate limiting on API endpoints

3. **Payments:**
   - Stripe webhook signature verification
   - Idempotency keys for transactions
   - Credit balance consistency checks

4. **Data Privacy:**
   - User data isolation
   - Encrypted connections (HTTPS/WSS)
   - No logging of video content
   - GDPR compliance (data export/deletion)

5. **CLI Execution:**
   - Sandboxed subprocess execution
   - Resource limits (CPU, memory)
   - Timeout protection
   - Safe output path handling

## Cost Estimation

**Infrastructure (per month):**
- VPS (4GB RAM, 2 CPU): $20-40
- PostgreSQL managed DB: $15-30
- Redis managed cache: $10-20
- Domain + SSL: $1-5
- Total: $46-95/month

**API Costs:**
- Claude API: Variable (user pays via credits)
- Stripe fees: 2.9% + $0.30 per transaction

**Break-even:**
- If 1 credit = $0.50
- 100 users × 10 credits/month = 1000 credits
- Revenue: $500/month
- Profit: $400-450/month

## Next Steps

1. Create new git branch: `feature/fastapi-wrapper`
2. Set up FastAPI project structure
3. Implement database models and migrations
4. Build authentication endpoints
5. Create CLI wrapper with progress streaming
6. Add video submission endpoints
7. Implement WebSocket events
8. Integrate Stripe payments
9. Build React frontend
10. End-to-end testing
11. Deploy to production

---

**Status:** Architecture documented, ready for implementation
**Estimated Timeline:** 6-8 weeks for MVP
**Target Launch:** Q1 2026
