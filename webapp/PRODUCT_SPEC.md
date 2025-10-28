# YouTube Study Buddy Web App - Product Specification

## Overview
Build a React + NestJS web application that wraps the existing Python CLI for YouTube Study Buddy. Users authenticate via social login, submit YouTube URLs, and access their generated notes/assessments through a database-backed system.

## Project Structure
```
webapp/
├── frontend/          # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   └── package.json
├── backend/           # NestJS + Prisma + PostgreSQL
│   ├── src/
│   │   ├── auth/
│   │   ├── videos/
│   │   ├── notes/
│   │   ├── jobs/
│   │   └── python-cli/
│   └── package.json
└── docker-compose.yml
```

## Scope - What to Build

### ✅ Backend (NestJS)
1. **Authentication Module**
   - Social OAuth integration (Google, GitHub, Discord)
   - JWT token management
   - User session handling
   - Protected routes middleware

2. **Database Schema (Prisma + PostgreSQL)**
   ```prisma
   model User {
     id            String   @id @default(cuid())
     email         String   @unique
     name          String?
     avatar        String?
     githubId      String?  @unique
     googleId      String?  @unique
     discordId     String?  @unique
     videos        Video[]
     notes         Note[]
     settings      Json?
     createdAt     DateTime @default(now())
   }

   model Video {
     id            String   @id @default(cuid())
     userId        String
     user          User     @relation(fields: [userId], references: [id])
     videoId       String   // YouTube video ID
     url           String
     title         String?
     transcript    String?  @db.Text
     processingJob ProcessingJob?
     notes         Note[]
     createdAt     DateTime @default(now())
   }

   model Note {
     id            String   @id @default(cuid())
     userId        String
     user          User     @relation(fields: [userId], references: [id])
     videoId       String?
     video         Video?   @relation(fields: [videoId], references: [id])
     title         String
     content       String   @db.Text
     subject       String?
     assessmentContent String? @db.Text
     pdfUrl        String?
     createdAt     DateTime @default(now())
     updatedAt     DateTime @updatedAt
   }

   model ProcessingJob {
     id            String   @id @default(cuid())
     videoId       String   @unique
     video         Video    @relation(fields: [videoId], references: [id])
     status        JobStatus // QUEUED, PROCESSING, COMPLETED, FAILED
     progress      Int      @default(0)
     error         String?
     result        Json?
     createdAt     DateTime @default(now())
     updatedAt     DateTime @updatedAt
   }
   ```

3. **Python CLI Integration Service**
   - Spawn Python subprocess
   - Parse CLI output
   - Map results to database models
   - Handle errors and retries

4. **Job Queue (BullMQ + Redis)**
   - Video processing queue
   - Job status tracking
   - Progress updates
   - Retry logic

5. **REST API Endpoints**
   ```
   POST   /auth/google
   POST   /auth/github
   POST   /auth/discord
   GET    /auth/me
   POST   /auth/logout

   POST   /videos              # Submit YouTube URL
   GET    /videos              # List user's videos
   GET    /videos/:id          # Get video details
   DELETE /videos/:id

   GET    /notes               # List user's notes
   GET    /notes/:id           # Get note details
   PUT    /notes/:id           # Update note content
   DELETE /notes/:id

   GET    /jobs                # List processing jobs
   GET    /jobs/:id            # Get job status
   POST   /jobs/:id/retry      # Retry failed job
   DELETE /jobs/:id            # Cancel job
   ```

6. **WebSocket Events** (Socket.io)
   - `job:progress` - Processing progress updates
   - `job:completed` - Job completion notification
   - `job:failed` - Job failure notification

### ✅ Frontend (React + Vite)
1. **Tech Stack**
   - React 18 + TypeScript
   - Vite (build tool)
   - TanStack Router (routing)
   - TanStack Query (data fetching)
   - Zustand (state management)
   - Tailwind CSS (styling)
   - shadcn/ui (component library)
   - **OverInnovate** (UI components + social sign-in)

2. **Pages/Views**
   - `/login` - Social login page (OverInnovate auth components)
   - `/dashboard` - Overview of videos/notes/jobs
   - `/videos` - Video submission and list
   - `/videos/:id` - Video details and processing status
   - `/notes` - Notes list (cards/grid view)
   - `/notes/:id` - Note viewer (integration point for YOUR editor)
   - `/settings` - User settings and API key config

3. **Key Components**
   - `<AuthProvider>` - Auth context and social login
   - `<VideoSubmitForm>` - URL input with options (subject, assessments, etc.)
   - `<JobQueue>` - Real-time job status list
   - `<JobProgressBar>` - Live progress updates via WebSocket
   - `<NoteCard>` - Note preview card
   - `<NotesList>` - Grid/list of notes with search/filter
   - `<VideoCard>` - Video preview with processing status

4. **Integration Points** (for YOUR code)
   - **Note Editor**: `<NoteEditorContainer>` - Pass note data, receives updates
   - **Knowledge Graph**: `<GraphContainer>` - Pass notes/relationships data

### ❌ Out of Scope (You Handle)
- Obsidian-style editor implementation
- Knowledge graph visualization
- Mobile responsiveness
- Production scaling/deployment
- Advanced analytics

## Technology Decisions

### Backend
- **NestJS**: Industry standard, TypeScript, good DI system
- **Prisma**: Type-safe ORM, great migrations, works well with NestJS
- **BullMQ**: Robust job queue, Redis-based, good monitoring
- **PostgreSQL**: Reliable, good for relational data
- **Socket.io**: Real-time updates, widely supported

### Frontend
- **Vite**: Fastest build tool, great DX
- **TanStack Stack**: Modern, performant, type-safe
- **shadcn/ui**: Accessible components, Tailwind-based, customizable
- **OverInnovate**: Pre-built social auth + UI components (per your request)

## Development Approach - Parallel Worktrees

### Feature Branches
```bash
# Main development
main (or develop)

# Parallel feature branches
├── feature/backend-auth          # Auth + user management
├── feature/backend-python-cli    # Python integration + job queue
├── feature/backend-api           # CRUD endpoints
├── feature/frontend-auth         # Login pages + auth context
├── feature/frontend-videos       # Video submission + list
├── feature/frontend-notes        # Notes display + list
└── feature/integration           # Connect frontend + backend
```

### Worktree Structure
```bash
# Create worktrees for parallel development
git worktree add ../ytstudybuddy-auth feature/backend-auth
git worktree add ../ytstudybuddy-python feature/backend-python-cli
git worktree add ../ytstudybuddy-api feature/backend-api
git worktree add ../ytstudybuddy-fe-auth feature/frontend-auth
git worktree add ../ytstudybuddy-fe-videos feature/frontend-videos
git worktree add ../ytstudybuddy-fe-notes feature/frontend-notes
```

## Implementation Plan

### Phase 1: Backend Foundation (1-2 days)
**Agent 1** - `feature/backend-auth`
- Set up NestJS project
- Prisma schema
- Auth module (passport strategies)
- User CRUD

**Agent 2** - `feature/backend-python-cli`
- Python CLI wrapper service
- BullMQ job queue setup
- Job processor
- Redis integration

**Agent 3** - `feature/backend-api`
- Videos controller + service
- Notes controller + service
- Jobs controller + service
- WebSocket gateway

### Phase 2: Frontend Foundation (1-2 days)
**Agent 4** - `feature/frontend-auth`
- Auth pages (login, callback)
- Auth context/hooks
- OverInnovate social login integration
- Protected route component

**Agent 5** - `feature/frontend-videos`
- Video submission form
- Video list component
- Video detail page
- Job progress tracking

**Agent 6** - `feature/frontend-notes`
- Notes list page
- Note card component
- Search/filter UI
- Note viewer skeleton (integration point)

### Phase 3: Integration (1 day)
**Agent 7** - `feature/integration`
- Connect all pieces
- E2E testing
- Docker compose setup
- Environment configuration

## API Integration with Python CLI

### How Backend Calls Python CLI
```typescript
// backend/src/python-cli/python-cli.service.ts
@Injectable()
export class PythonCliService {
  async processVideo(videoUrl: string, options: ProcessingOptions): Promise<ProcessingResult> {
    // 1. Spawn Python process
    const args = [
      'yt-study-buddy',
      videoUrl,
      ...(options.subject ? ['--subject', options.subject] : []),
      ...(options.assessments ? ['--generate-assessments'] : ['--no-assessments']),
      '--parallel',
      '--workers', '3'
    ];

    const child = spawn('uv', ['run', ...args], {
      cwd: '/path/to/python/cli',
      env: { CLAUDE_API_KEY: apiKey }
    });

    // 2. Stream output and parse progress
    child.stdout.on('data', (data) => {
      // Parse progress: "Processing 2/10 videos..."
      // Emit WebSocket event with progress
      this.wsGateway.emitProgress(jobId, progress);
    });

    // 3. Wait for completion
    await new Promise((resolve) => child.on('close', resolve));

    // 4. Read generated files from notes/ directory
    const notesPath = path.join(baseDir, 'notes', subject, `${title}.md`);
    const content = await fs.readFile(notesPath, 'utf-8');

    // 5. Store in database
    return {
      noteId,
      content,
      filepath: notesPath
    };
  }
}
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL="postgresql://user:pass@localhost:5432/ytstudy"
REDIS_URL="redis://localhost:6379"
JWT_SECRET="your-secret-key"
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."
GITHUB_CLIENT_ID="..."
GITHUB_CLIENT_SECRET="..."
DISCORD_CLIENT_ID="..."
DISCORD_CLIENT_SECRET="..."
PYTHON_CLI_PATH="/path/to/ytstudybuddy/src"
CLAUDE_API_KEY="sk-ant-..."
```

### Frontend (.env)
```env
VITE_API_URL="http://localhost:3000"
VITE_WS_URL="ws://localhost:3000"
```

## Docker Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ytstudy
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/ytstudy
      REDIS_URL: redis://redis:6379

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Success Criteria

### Minimum Viable Product (MVP)
1. ✅ User can sign in with Google/GitHub/Discord
2. ✅ User can submit YouTube URL with options
3. ✅ Job is queued and processed in background
4. ✅ Real-time progress updates shown to user
5. ✅ Generated notes stored in database
6. ✅ User can view list of their notes
7. ✅ User can open a note (shows content, ready for your editor)
8. ✅ Failed jobs can be retried

### Integration Points Ready
1. ✅ Note editor container has props: `noteId`, `initialContent`, `onSave`
2. ✅ Graph container has props: `userId`, `noteIds[]`, `onNodeClick`

## Timeline Estimate (with Parallel Development)

- **Day 1**: Backend foundation (Auth, DB, Python CLI integration)
- **Day 2**: Backend APIs (Videos, Notes, Jobs) + WebSocket
- **Day 3**: Frontend auth + video submission
- **Day 4**: Frontend notes list + job tracking
- **Day 5**: Integration, testing, Docker setup

**Total: 3-5 days with 3-7 agents working in parallel**

## Next Steps

1. Create feature branches and worktrees
2. Assign agents to specific features
3. Agents work independently, merge as they complete
4. Integration agent pulls it all together
5. You add your editor and graph components

## Notes
- Keep it simple, MVP first
- Database is source of truth for all user data
- Python CLI remains unchanged, just wrapped
- Frontend is thin client, backend does heavy lifting
- All agents have full spec context to avoid conflicts
