# Agent Task: Backend REST API & Controllers

## Branch: `feature/backend-api`

## Objective
Implement REST API endpoints for Videos, Notes, and Jobs management with proper validation and error handling.

## Tasks

### 1. Videos Module
- Create VideosModule in `backend/src/videos/`
- Implement VideosController with endpoints
- Implement VideosService with business logic
- Add DTOs for request/response validation
- Integrate with PythonCliService to queue jobs

### 2. Videos API Endpoints
```typescript
POST   /videos              # Submit YouTube URL
GET    /videos              # List user's videos (paginated)
GET    /videos/:id          # Get video details
DELETE /videos/:id          # Delete video + associated notes
```

### 3. Videos DTOs
```typescript
// CreateVideoDto
class CreateVideoDto {
  @IsUrl()
  url: string;

  @IsOptional()
  @IsString()
  subject?: string;

  @IsOptional()
  @IsBoolean()
  generateAssessments?: boolean;
}

// VideoResponseDto
class VideoResponseDto {
  id: string;
  videoId: string;
  url: string;
  title?: string;
  processingJob?: JobResponseDto;
  notes: NoteResponseDto[];
  createdAt: Date;
}
```

### 4. Notes Module
- Create NotesModule in `backend/src/notes/`
- Implement NotesController with endpoints
- Implement NotesService with business logic
- Add DTOs for request/response validation
- Implement search and filtering

### 5. Notes API Endpoints
```typescript
GET    /notes               # List user's notes (paginated, filterable)
GET    /notes/:id           # Get note details
PUT    /notes/:id           # Update note content
DELETE /notes/:id           # Delete note
```

### 6. Notes DTOs
```typescript
// UpdateNoteDto
class UpdateNoteDto {
  @IsOptional()
  @IsString()
  title?: string;

  @IsOptional()
  @IsString()
  content?: string;

  @IsOptional()
  @IsString()
  subject?: string;
}

// NoteResponseDto
class NoteResponseDto {
  id: string;
  title: string;
  content: string;
  subject?: string;
  assessmentContent?: string;
  pdfUrl?: string;
  videoId?: string;
  createdAt: Date;
  updatedAt: Date;
}

// NotesQueryDto
class NotesQueryDto {
  @IsOptional()
  @IsString()
  subject?: string;

  @IsOptional()
  @IsString()
  search?: string;

  @IsOptional()
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;
}
```

### 7. Jobs Controller Enhancement
- Add JobsController in JobsModule
- Implement endpoint handlers
- Add pagination for job lists
- Implement retry logic for failed jobs

### 8. Jobs API Endpoints
```typescript
GET    /jobs                # List user's processing jobs
GET    /jobs/:id            # Get job status and details
POST   /jobs/:id/retry      # Retry a failed job
DELETE /jobs/:id            # Cancel/delete a job
```

### 9. Request Validation
- Install class-validator and class-transformer
- Add ValidationPipe globally
- Implement custom validators:
  - YouTube URL validator
  - Video ID extractor
- Add proper error messages

### 10. Error Handling
- Create custom exception filters
- Implement error response format:
```typescript
{
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
  path: string;
}
```
- Handle common errors:
  - 400 Bad Request (validation)
  - 401 Unauthorized
  - 403 Forbidden (not owner)
  - 404 Not Found
  - 409 Conflict (duplicate)
  - 500 Internal Server Error

### 11. Pagination Helper
```typescript
// PaginationDto
class PaginationDto {
  @IsOptional()
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 20;
}

// PaginatedResponseDto
class PaginatedResponseDto<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### 12. Authorization Guards
- Implement resource ownership checks
- Ensure users can only access their own:
  - Videos
  - Notes
  - Jobs
- Add UserOwnershipGuard decorator

## Dependencies to Install
```bash
npm install class-validator class-transformer
npm install @nestjs/swagger swagger-ui-express  # Optional: API docs
```

## Success Criteria
- ✅ All CRUD endpoints respond correctly
- ✅ Input validation rejects invalid data
- ✅ Users can only access their own resources
- ✅ Pagination works correctly
- ✅ Search and filtering work on notes
- ✅ Error responses are consistent and helpful
- ✅ Submitting video URL creates job and queues processing
- ✅ Deleting video also deletes associated notes and jobs

## API Endpoints Summary
```
# Videos
POST   /videos              - Submit YouTube URL, queue processing
GET    /videos              - List user's videos (paginated)
GET    /videos/:id          - Get video details with job status
DELETE /videos/:id          - Delete video + notes + job

# Notes
GET    /notes               - List user's notes (paginated, filterable)
GET    /notes/:id           - Get note details
PUT    /notes/:id           - Update note content/title
DELETE /notes/:id           - Delete note

# Jobs
GET    /jobs                - List user's processing jobs
GET    /jobs/:id            - Get job status and progress
POST   /jobs/:id/retry      - Retry failed job
DELETE /jobs/:id            - Cancel/delete job
```

## Business Logic

### Video Submission Flow
1. Validate YouTube URL
2. Extract video ID
3. Check if video already exists for user
4. Create Video record in database
5. Create ProcessingJob record (status: QUEUED)
6. Add job to BullMQ queue
7. Return video + job details

### Note Update Flow
1. Verify note exists
2. Verify user owns note
3. Update fields
4. Return updated note

### Job Retry Flow
1. Verify job exists and user owns it
2. Verify job status is FAILED
3. Reset job status to QUEUED
4. Clear error field
5. Re-add to BullMQ queue
6. Return updated job

## Testing
- Unit tests for all services
- E2E tests for all endpoints
- Test authentication on protected routes
- Test authorization (resource ownership)
- Test validation (invalid inputs)
- Test pagination
- Test error handling

## Integration Points
- Depends on AuthModule (JwtAuthGuard)
- Depends on PythonCliModule (job queuing)
- Depends on JobsModule (WebSocket events)
- Uses Prisma for database operations
- All endpoints require authentication

## Notes
- Use `@UseGuards(JwtAuthGuard)` on all controllers
- Extract user ID from JWT token via `@CurrentUser()` decorator
- Implement soft delete for videos/notes if needed
- Add rate limiting on video submission (max 10/hour per user)
- Consider caching for frequently accessed notes
- Validate YouTube video ID format
- Handle duplicate video submissions gracefully
- Return appropriate HTTP status codes
