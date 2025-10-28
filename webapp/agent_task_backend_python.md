# Agent Task: Python CLI Integration & Job Queue

## Branch: `feature/backend-python-cli`

## Objective
Create the Python CLI wrapper service and job queue system for processing YouTube videos in the background.

## Tasks

### 1. Python CLI Service Module
- Create PythonCliModule in `backend/src/python-cli/`
- Implement PythonCliService with methods:
  - `processVideo(videoUrl, options)` - Main processing function
  - `parseProgress(stdout)` - Parse CLI output for progress
  - `parseOutput(stdout)` - Parse CLI output for results
  - `readGeneratedNotes(filepath)` - Read markdown files
- Handle subprocess spawning with `child_process.spawn`
- Stream stdout/stderr for real-time updates
- Parse CLI output to extract:
  - Progress percentage
  - Generated file paths
  - Error messages

### 2. BullMQ Job Queue Setup
- Install BullMQ and Redis client
- Create JobsModule in `backend/src/jobs/`
- Configure Redis connection
- Create job queues:
  - `video-processing` queue
- Implement job processors
- Add job event listeners

### 3. Video Processing Queue
- Create VideoProcessingQueue class
- Implement job processor:
  - Call PythonCliService
  - Update job status in database
  - Parse and store results
  - Handle errors and retries
- Configure retry logic (3 attempts)
- Set job timeout (30 minutes)

### 4. Job Status Tracking
- Create JobsService for job management
- Implement job status updates:
  - QUEUED → PROCESSING → COMPLETED/FAILED
  - Progress percentage updates
- Store job results in database
- Store error messages on failure

### 5. WebSocket Gateway
- Install Socket.io for NestJS
- Create JobsGateway in `backend/src/jobs/`
- Implement WebSocket events:
  - `job:progress` - Send progress updates
  - `job:completed` - Notify completion
  - `job:failed` - Notify failure
- Authenticate WebSocket connections
- Room-based updates (user-specific)

### 6. Redis Integration
- Configure Redis connection
- Set up Redis for BullMQ
- Optional: Add Redis caching for video metadata
- Health check for Redis connection

### 7. Python CLI Integration Details
```typescript
// Example: Spawning Python CLI
const args = [
  'yt-study-buddy',
  videoUrl,
  ...(options.subject ? ['--subject', options.subject] : []),
  ...(options.assessments ? ['--generate-assessments'] : ['--no-assessments']),
  '--parallel',
  '--workers', '3'
];

const child = spawn('uv', ['run', ...args], {
  cwd: process.env.PYTHON_CLI_PATH,
  env: {
    ...process.env,
    CLAUDE_API_KEY: apiKey
  }
});
```

### 8. File System Integration
- Read generated markdown files from `notes/` directory
- Parse markdown content
- Extract metadata from frontmatter
- Store in database
- Handle file not found errors

## Dependencies to Install
```bash
npm install bullmq ioredis
npm install @nestjs/websockets @nestjs/platform-socket.io socket.io
npm install @nestjs/bull @nestjs/bullmq
```

## Success Criteria
- ✅ Redis connection established
- ✅ BullMQ queue processes jobs
- ✅ Python CLI can be spawned successfully
- ✅ Progress updates are parsed and emitted via WebSocket
- ✅ Generated notes are read and stored in database
- ✅ Failed jobs are retried automatically
- ✅ Job status is updated in real-time
- ✅ WebSocket events reach authenticated clients

## API Endpoints to Implement
```
GET    /jobs                # List user's jobs
GET    /jobs/:id            # Get job details
POST   /jobs/:id/retry      # Retry failed job
DELETE /jobs/:id            # Cancel/delete job
```

## WebSocket Events
```typescript
// Server → Client
socket.emit('job:progress', { jobId, progress, message });
socket.emit('job:completed', { jobId, noteId, result });
socket.emit('job:failed', { jobId, error });

// Client → Server
socket.on('subscribe:jobs', () => { ... });
socket.on('unsubscribe:jobs', () => { ... });
```

## Processing Flow
1. Video URL submitted via API
2. Job added to BullMQ queue (status: QUEUED)
3. Job processor picks up job (status: PROCESSING)
4. Python CLI spawned with video URL
5. Progress updates parsed and emitted via WebSocket
6. CLI generates markdown files
7. Service reads and parses markdown files
8. Content stored in database (Note model)
9. Job marked as COMPLETED
10. Completion event emitted via WebSocket

## Error Handling
- Python CLI fails → Retry job (up to 3 times)
- File not found → Mark job as failed with error
- Redis connection lost → Queue jobs in-memory temporarily
- WebSocket disconnection → Buffer updates, send on reconnect

## Environment Variables
```env
REDIS_URL="redis://localhost:6379"
PYTHON_CLI_PATH="/path/to/ytstudybuddy/src"
CLAUDE_API_KEY="sk-ant-..."
JOB_TIMEOUT_MS=1800000  # 30 minutes
JOB_RETRY_ATTEMPTS=3
```

## Testing
- Unit tests for PythonCliService
- Integration tests for job queue
- Mock Python CLI output for testing
- Test WebSocket event emission
- Test retry logic
- Test error handling

## Integration Points
- Exports PythonCliService for use by Videos module
- Exports JobsService for job management
- Exports JobsGateway for WebSocket connections
- Depends on Prisma for database access
- Depends on AuthModule for WebSocket authentication

## Notes
- Python CLI path should be configurable via env var
- CLAUDE_API_KEY should be securely stored
- Progress parsing regex: `/Processing (\d+)\/(\d+)/`
- Generated files are in: `notes/{subject}/{title}.md`
- Handle concurrent job processing (max 3 workers)
- Implement job cancellation if user requests
- Clean up old completed jobs (30 days retention)
