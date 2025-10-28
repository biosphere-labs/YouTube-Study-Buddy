# Agent Task: Frontend Video Submission & Job Tracking

## Branch: `feature/frontend-videos`

## Objective
Implement video submission form, video list, job queue visualization, and real-time progress tracking with WebSocket.

## Tasks

### 1. Video Types
```typescript
// types/video.ts
export interface Video {
  id: string;
  videoId: string;
  url: string;
  title?: string;
  transcript?: string;
  processingJob?: ProcessingJob;
  notes: Note[];
  createdAt: string;
}

export interface ProcessingJob {
  id: string;
  videoId: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number;
  error?: string;
  result?: any;
  createdAt: string;
  updatedAt: string;
}

export interface CreateVideoDto {
  url: string;
  subject?: string;
  generateAssessments?: boolean;
}
```

### 2. API Hooks
```typescript
// hooks/useVideos.ts
export function useVideos() {
  return useQuery({
    queryKey: ['videos'],
    queryFn: () => api.get<Video[]>('/videos').then(res => res.data),
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: ['videos', id],
    queryFn: () => api.get<Video>(`/videos/${id}`).then(res => res.data),
    enabled: !!id,
  });
}

export function useCreateVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateVideoDto) =>
      api.post<Video>('/videos', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

export function useDeleteVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/videos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}
```

### 3. WebSocket Hook for Job Updates
```typescript
// hooks/useJobSocket.ts
export function useJobSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = authStore.getState().token;
    const ws = io(import.meta.env.VITE_WS_URL, {
      auth: { token },
    });

    ws.on('job:progress', (data) => {
      // Update job in cache
      queryClient.setQueryData(['jobs', data.jobId], (old: any) => ({
        ...old,
        progress: data.progress,
      }));
    });

    ws.on('job:completed', (data) => {
      // Refetch videos and notes
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    });

    ws.on('job:failed', (data) => {
      // Update job with error
      queryClient.setQueryData(['jobs', data.jobId], (old: any) => ({
        ...old,
        status: 'FAILED',
        error: data.error,
      }));
    });

    setSocket(ws);
    return () => { ws.disconnect(); };
  }, []);

  return socket;
}
```

### 4. Video Submit Form Component
```typescript
// components/videos/VideoSubmitForm.tsx
- YouTube URL input (with validation)
- Optional subject input
- Generate assessments checkbox
- Submit button with loading state
- Display submission errors
- Auto-focus URL input
- Clear form on success
```

### 5. Video List Page
```typescript
// pages/Videos.tsx
- Display list of user's videos
- Each video card shows:
  - Thumbnail (YouTube thumbnail)
  - Title (if available)
  - URL
  - Processing status badge
  - Progress bar (if processing)
  - Created date
- Click video to view details
- Delete button (with confirmation)
- Empty state when no videos
```

### 6. Video Card Component
```typescript
// components/videos/VideoCard.tsx
- Thumbnail image
- Video title/URL
- Status badge (QUEUED, PROCESSING, COMPLETED, FAILED)
- Progress bar (if PROCESSING)
- Notes count badge
- Delete button
- Click to navigate to video details
```

### 7. Video Details Page
```typescript
// pages/VideoDetails.tsx
- Video information:
  - Title
  - YouTube embed (optional)
  - URL
  - Created date
- Processing job details:
  - Status
  - Progress (with real-time updates)
  - Error message (if failed)
  - Retry button (if failed)
- List of generated notes:
  - Note cards
  - Click to open note
- Delete video button
```

### 8. Job Queue Component
```typescript
// components/jobs/JobQueue.tsx
- Display all user's jobs
- Real-time status updates via WebSocket
- Each job shows:
  - Video title/URL
  - Status badge
  - Progress bar
  - Time elapsed
  - Retry button (if failed)
  - Cancel button (if queued/processing)
- Auto-refresh job list
```

### 9. Job Progress Bar Component
```typescript
// components/jobs/JobProgressBar.tsx
- Animated progress bar
- Percentage display
- Status text ("Extracting transcript...", "Generating notes...")
- Error state styling
- Success state styling
- Indeterminate state (when queued)
```

### 10. Job Status Badge Component
```typescript
// components/jobs/JobStatusBadge.tsx
- Color-coded badges:
  - QUEUED: gray/blue
  - PROCESSING: blue/animated
  - COMPLETED: green
  - FAILED: red
- Icon for each status
- Tooltip with additional info
```

### 11. Videos Page Layout
- Video submit form at top
- Job queue section (collapsible)
- Videos grid/list (with filtering)
- Pagination (if many videos)

### 12. WebSocket Connection Management
- Auto-reconnect on disconnect
- Display connection status
- Buffer updates during disconnection
- Toast notifications for important events:
  - "Video processing started"
  - "Notes ready!"
  - "Processing failed"

## Dependencies to Install
```bash
npm install socket.io-client
npm install react-hook-form @hookform/resolvers zod
npm install sonner  # Toast notifications
```

## Success Criteria
- ✅ Video submission form validates YouTube URLs
- ✅ Submitting video creates job and shows in queue
- ✅ Job progress updates in real-time via WebSocket
- ✅ Video list displays all user's videos
- ✅ Video cards show current processing status
- ✅ Clicking video navigates to details page
- ✅ Failed jobs can be retried
- ✅ Completed jobs show generated notes
- ✅ WebSocket reconnects automatically
- ✅ Toast notifications appear for job events

## Pages to Implement
```
/videos            - Video submission + list
/videos/:id        - Video details + job status
```

## Components to Create
```
<VideoSubmitForm>      - URL input form
<VideosList>           - Grid of video cards
<VideoCard>            - Individual video preview
<JobQueue>             - List of processing jobs
<JobProgressBar>       - Animated progress bar
<JobStatusBadge>       - Status indicator
<VideoDetails>         - Full video information
```

## WebSocket Events (Client Side)
```typescript
// Listen for
socket.on('job:progress', (data) => { ... });
socket.on('job:completed', (data) => { ... });
socket.on('job:failed', (data) => { ... });

// Emit
socket.emit('subscribe:jobs');
socket.emit('unsubscribe:jobs');
```

## Form Validation
```typescript
const videoSchema = z.object({
  url: z.string()
    .url('Invalid URL')
    .regex(/(?:youtube\.com\/watch\?v=|youtu\.be\/)/, 'Must be a YouTube URL'),
  subject: z.string().optional(),
  generateAssessments: z.boolean().optional(),
});
```

## Testing
- Test video submission with valid/invalid URLs
- Test real-time progress updates
- Test WebSocket reconnection
- Test job retry functionality
- Test video deletion
- Test empty states
- Test error handling

## Integration Points
- Depends on auth module (useAuth hook)
- Uses API client from auth module
- Integrates with WebSocket for real-time updates
- Navigates to Notes module when clicking note cards
- Ready for backend API integration

## Notes
- Use React Query for server state
- Cache video and job data aggressively
- Implement optimistic updates for better UX
- Show skeleton loaders while data is fetching
- YouTube URL regex: `/(youtube\.com\/watch\?v=|youtu\.be\/)/`
- Extract video ID for thumbnail: `https://img.youtube.com/vi/{videoId}/hqdefault.jpg`
- Implement infinite scroll if user has many videos
- Add filters: status, date range, subject
- Consider adding bulk operations (delete multiple)
