# Obsidian Clone Integration Guide

## Overview

This guide explains how to integrate your custom Obsidian clone into the YouTube Study Buddy React frontend, replacing or complementing the existing note viewer/editor components.

## Architecture Options

### Option 1: Embedded Component (Recommended for MVP)

Integrate your Obsidian clone as a React component within the existing frontend.

```
┌─────────────────────────────────────────────────────────┐
│         YouTube Study Buddy React Frontend              │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Dashboard   │  │ Video List   │  │  Credits     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Obsidian Clone Component                │   │
│  │                                                  │   │
│  │  - Markdown rendering with wiki-links          │   │
│  │  - Graph view of cross-references              │   │
│  │  - File explorer                                │   │
│  │  - Search                                       │   │
│  │  - Editor with preview                          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Option 2: Standalone Application

Run your Obsidian clone as a separate application that communicates with the backend.

```
┌──────────────────────┐         ┌──────────────────────┐
│  YT Study Buddy      │         │  Obsidian Clone      │
│  React Frontend      │         │  Application         │
│                      │         │                      │
│  - Video submission  │         │  - Note editing      │
│  - Dashboard         │         │  - Graph view        │
│  - Credits           │◄───────►│  - File explorer     │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                 │
           │                                 │
           ▼                                 ▼
      ┌─────────────────────────────────────────┐
      │         API Gateway / Backend           │
      │         - DynamoDB for metadata         │
      │         - S3 for note storage           │
      └─────────────────────────────────────────┘
```

### Option 3: Iframe Embed

Embed your Obsidian clone via iframe if it's a web application.

---

## Integration Steps

### Step 1: Assess Your Obsidian Clone

First, let's understand what you have:

**Questions to Answer:**
1. **Technology Stack**:
   - Is it built with React, Vue, vanilla JS, or another framework?
   - Does it run in a browser or as a desktop app (Electron)?

2. **Current State**:
   - Is it a complete application or a set of components?
   - Does it have its own backend/storage or is it frontend-only?

3. **Key Features**:
   - Markdown editor with preview?
   - Wiki-link syntax support (`[[Note Name]]`)?
   - Graph view of connections?
   - File explorer/tree view?
   - Search functionality?
   - Tag support?

4. **Storage**:
   - How does it currently store notes? (LocalStorage, IndexedDB, filesystem?)
   - Can it work with remote storage (S3, API)?

5. **Dependencies**:
   - What libraries does it use?
   - Are there any conflicts with the existing React frontend?

### Step 2: Choose Integration Approach

Based on your clone's characteristics:

#### If Your Clone is React-Based:
→ **Choose Option 1** (Embedded Component)
- Easiest integration
- Shared state management
- Consistent UI/UX

#### If Your Clone is a Web App (any framework):
→ **Choose Option 3** (Iframe) or **Option 2** (Standalone)
- Iframe for quick integration
- Standalone for better separation of concerns

#### If Your Clone is Desktop-Only (Electron):
→ **Need to Extract Web Components** or **Run Separately**

---

## Detailed Integration: Option 1 (React Component)

### Directory Structure

```
react-frontend/frontend/src/
├── components/
│   ├── ObsidianClone/           # Your Obsidian clone
│   │   ├── index.tsx            # Main export
│   │   ├── Editor/
│   │   │   ├── MarkdownEditor.tsx
│   │   │   ├── MarkdownPreview.tsx
│   │   │   └── WikiLinkParser.tsx
│   │   ├── Graph/
│   │   │   ├── GraphView.tsx
│   │   │   └── GraphRenderer.tsx
│   │   ├── FileExplorer/
│   │   │   ├── FileTree.tsx
│   │   │   └── FileItem.tsx
│   │   ├── Search/
│   │   │   ├── SearchBar.tsx
│   │   │   └── SearchResults.tsx
│   │   └── Layout/
│   │       ├── ObsidianLayout.tsx
│   │       └── Sidebar.tsx
│   │
│   └── Notes/                    # Existing note components
│       ├── NoteList.tsx
│       └── NoteViewer.tsx        # Will use ObsidianClone
│
├── hooks/
│   └── useObsidianClone.ts      # Hook for Obsidian features
│
├── lib/
│   └── obsidian-adapter.ts      # Adapter for backend integration
│
└── types/
    └── obsidian.ts              # Type definitions
```

### Implementation Steps

#### 1. Copy Your Obsidian Clone Code

```bash
# From your Obsidian clone project
cp -r src/components/obsidian-editor ./react-frontend/frontend/src/components/ObsidianClone

# Or if it's a separate npm package
cd react-frontend/frontend
npm install your-obsidian-clone-package
```

#### 2. Create Storage Adapter

Your Obsidian clone likely expects filesystem-like operations. Create an adapter that maps to our backend:

```typescript
// src/lib/obsidian-adapter.ts

import { apiClient } from '../api/client';

export class ObsidianStorageAdapter {
  /**
   * Get note content by ID
   */
  async readFile(noteId: string): Promise<string> {
    const response = await apiClient.get(`/notes/${noteId}?include_content=true`);
    return response.data.content;
  }

  /**
   * Save note content
   */
  async writeFile(noteId: string, content: string): Promise<void> {
    await apiClient.put(`/notes/${noteId}`, {
      content,
      updated_at: new Date().toISOString()
    });
  }

  /**
   * List all notes for current user
   */
  async listFiles(): Promise<Array<{ id: string; title: string; path: string }>> {
    const response = await apiClient.get('/notes?limit=1000');
    return response.data.notes.map((note: any) => ({
      id: note.note_id,
      title: note.title,
      path: `/${note.subject || 'Unsorted'}/${note.title}`,
      created_at: note.created_at,
      updated_at: note.updated_at
    }));
  }

  /**
   * Search notes
   */
  async searchFiles(query: string): Promise<Array<any>> {
    const response = await apiClient.get(`/notes?search=${encodeURIComponent(query)}`);
    return response.data.notes;
  }

  /**
   * Get note links (cross-references)
   */
  async getLinks(noteId: string): Promise<Array<{ source: string; target: string }>> {
    const response = await apiClient.get(`/notes/${noteId}`);
    const note = response.data;

    // Parse cross_references from note metadata
    if (note.cross_references) {
      return note.cross_references.map((ref: any) => ({
        source: noteId,
        target: ref.note_id,
        type: 'wiki-link'
      }));
    }

    return [];
  }

  /**
   * Create new note
   */
  async createFile(title: string, content: string, subject?: string): Promise<string> {
    // Notes are created via video processing, but you could add an endpoint
    throw new Error('Note creation happens via video processing');
  }

  /**
   * Delete note
   */
  async deleteFile(noteId: string): Promise<void> {
    await apiClient.delete(`/notes/${noteId}`);
  }

  /**
   * Get note metadata
   */
  async getMetadata(noteId: string): Promise<any> {
    const response = await apiClient.get(`/notes/${noteId}`);
    return {
      title: response.data.title,
      created: response.data.created_at,
      modified: response.data.updated_at,
      tags: response.data.tags || [],
      subject: response.data.subject
    };
  }
}

export const obsidianAdapter = new ObsidianStorageAdapter();
```

#### 3. Create Integration Hook

```typescript
// src/hooks/useObsidianClone.ts

import { useState, useEffect } from 'react';
import { obsidianAdapter } from '../lib/obsidian-adapter';

interface Note {
  id: string;
  title: string;
  content: string;
  path: string;
  links: Array<{ source: string; target: string }>;
}

export function useObsidianClone() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [currentNote, setCurrentNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load all notes
  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const noteList = await obsidianAdapter.listFiles();
      setNotes(noteList as any);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const openNote = async (noteId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [content, metadata, links] = await Promise.all([
        obsidianAdapter.readFile(noteId),
        obsidianAdapter.getMetadata(noteId),
        obsidianAdapter.getLinks(noteId)
      ]);

      setCurrentNote({
        id: noteId,
        title: metadata.title,
        content,
        path: `/${metadata.subject || 'Unsorted'}/${metadata.title}`,
        links
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open note');
    } finally {
      setLoading(false);
    }
  };

  const saveNote = async (noteId: string, content: string) => {
    setLoading(true);
    setError(null);
    try {
      await obsidianAdapter.writeFile(noteId, content);

      // Update current note if it's the one being saved
      if (currentNote?.id === noteId) {
        setCurrentNote({ ...currentNote, content });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  const searchNotes = async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const results = await obsidianAdapter.searchFiles(query);
      return results;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      return [];
    } finally {
      setLoading(false);
    }
  };

  return {
    notes,
    currentNote,
    loading,
    error,
    openNote,
    saveNote,
    searchNotes,
    refreshNotes: loadNotes
  };
}
```

#### 4. Wrap Your Obsidian Component

```typescript
// src/components/ObsidianClone/ObsidianWrapper.tsx

import React from 'react';
import { useObsidianClone } from '../../hooks/useObsidianClone';
// Import your Obsidian clone main component
import { ObsidianEditor } from 'your-obsidian-clone'; // Adjust import

interface ObsidianWrapperProps {
  noteId?: string;
  onNavigate?: (noteId: string) => void;
}

export function ObsidianWrapper({ noteId, onNavigate }: ObsidianWrapperProps) {
  const {
    notes,
    currentNote,
    loading,
    error,
    openNote,
    saveNote,
    searchNotes
  } = useObsidianClone();

  React.useEffect(() => {
    if (noteId) {
      openNote(noteId);
    }
  }, [noteId]);

  if (loading && !currentNote) {
    return <div className="flex items-center justify-center h-screen">
      <div className="text-lg">Loading notes...</div>
    </div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-screen text-red-500">
      <div>Error: {error}</div>
    </div>;
  }

  return (
    <ObsidianEditor
      // Map your props to what your Obsidian clone expects
      notes={notes}
      currentNote={currentNote}
      onSave={(content) => currentNote && saveNote(currentNote.id, content)}
      onOpenNote={(id) => {
        openNote(id);
        onNavigate?.(id);
      }}
      onSearch={searchNotes}

      // Pass any configuration your clone needs
      config={{
        theme: 'dark', // or use user preference
        vimMode: false,
        spellCheck: true
      }}
    />
  );
}
```

#### 5. Update Note Viewer Route

```typescript
// src/routes/notes/$noteId.tsx (or wherever your note route is)

import { useParams } from 'react-router-dom';
import { ObsidianWrapper } from '../../components/ObsidianClone/ObsidianWrapper';

export function NoteViewerPage() {
  const { noteId } = useParams();

  return (
    <div className="h-screen">
      <ObsidianWrapper
        noteId={noteId}
        onNavigate={(newNoteId) => {
          // Navigate to new note when user clicks wiki-links
          window.history.pushState({}, '', `/notes/${newNoteId}`);
        }}
      />
    </div>
  );
}
```

#### 6. Add Route for Full Obsidian View

```typescript
// src/App.tsx or router config

<Route path="/vault" element={<ObsidianFullView />} />
<Route path="/vault/:noteId" element={<ObsidianFullView />} />
```

```typescript
// src/pages/ObsidianFullView.tsx

import { ObsidianWrapper } from '../components/ObsidianClone/ObsidianWrapper';
import { useParams, useNavigate } from 'react-router-dom';

export function ObsidianFullView() {
  const { noteId } = useParams();
  const navigate = useNavigate();

  return (
    <div className="h-screen flex flex-col">
      {/* Header with back button */}
      <header className="border-b p-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          ← Back to Dashboard
        </button>
      </header>

      {/* Full Obsidian interface */}
      <main className="flex-1 overflow-hidden">
        <ObsidianWrapper
          noteId={noteId}
          onNavigate={(newNoteId) => navigate(`/vault/${newNoteId}`)}
        />
      </main>
    </div>
  );
}
```

---

## Integration: Option 2 (Standalone Application)

If your Obsidian clone is a separate application:

### Setup

1. **Run Obsidian Clone on Different Port**
   ```bash
   # Your Obsidian clone runs on http://localhost:3001
   # React frontend runs on http://localhost:5173
   ```

2. **Configure CORS**
   Both applications need to allow cross-origin requests:

   ```typescript
   // In your Obsidian clone
   const corsOptions = {
     origin: 'http://localhost:5173',
     credentials: true
   };
   ```

3. **Share Authentication**
   Both apps should use the same Cognito user pool:

   ```typescript
   // In your Obsidian clone
   import { Amplify } from 'aws-amplify';

   Amplify.configure({
     Auth: {
       region: 'us-east-1',
       userPoolId: 'same-as-main-app',
       userPoolWebClientId: 'same-as-main-app'
     }
   });
   ```

4. **Link from Main App**
   ```typescript
   // In React frontend dashboard
   <a
     href="http://localhost:3001"
     target="_blank"
     className="btn"
   >
     Open Vault in Obsidian
   </a>
   ```

---

## Integration: Option 3 (Iframe Embed)

### Implementation

```typescript
// src/components/ObsidianClone/ObsidianIframe.tsx

import React, { useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';

interface ObsidianIframeProps {
  noteId?: string;
  src: string; // URL of your Obsidian clone
}

export function ObsidianIframe({ noteId, src }: ObsidianIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { user } = useAuth();

  useEffect(() => {
    // Send auth token to iframe
    if (iframeRef.current && user) {
      const iframe = iframeRef.current;

      iframe.addEventListener('load', () => {
        iframe.contentWindow?.postMessage({
          type: 'AUTH_TOKEN',
          token: user.signInUserSession.idToken.jwtToken
        }, src);
      });
    }
  }, [user, src]);

  useEffect(() => {
    // Navigate to specific note
    if (iframeRef.current && noteId) {
      iframeRef.current.contentWindow?.postMessage({
        type: 'OPEN_NOTE',
        noteId
      }, src);
    }
  }, [noteId, src]);

  return (
    <iframe
      ref={iframeRef}
      src={src}
      className="w-full h-full border-0"
      allow="clipboard-read; clipboard-write"
      sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
    />
  );
}
```

### In Your Obsidian Clone (iframe content)

```typescript
// Listen for messages from parent
window.addEventListener('message', (event) => {
  // Verify origin
  if (event.origin !== 'http://localhost:5173') return;

  switch (event.data.type) {
    case 'AUTH_TOKEN':
      // Store token and authenticate
      localStorage.setItem('token', event.data.token);
      break;

    case 'OPEN_NOTE':
      // Navigate to specific note
      navigateToNote(event.data.noteId);
      break;
  }
});

// Send messages to parent
function notifyParent(type: string, data: any) {
  window.parent.postMessage({ type, ...data }, 'http://localhost:5173');
}

// Example: Notify when note changes
function onNoteChange(noteId: string) {
  notifyParent('NOTE_CHANGED', { noteId });
}
```

---

## Graph View Integration

If your Obsidian clone has a graph view, you can create a dedicated route:

```typescript
// src/pages/GraphView.tsx

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { GraphVisualization } from '../components/ObsidianClone/GraphVisualization';

export function GraphView() {
  // Fetch all notes and their cross-references
  const { data: graphData } = useQuery({
    queryKey: ['graph'],
    queryFn: async () => {
      const response = await apiClient.get('/notes?limit=1000');
      const notes = response.data.notes;

      // Build nodes and edges
      const nodes = notes.map((note: any) => ({
        id: note.note_id,
        label: note.title,
        subject: note.subject
      }));

      const edges: any[] = [];
      notes.forEach((note: any) => {
        if (note.cross_references) {
          note.cross_references.forEach((ref: any) => {
            edges.push({
              source: note.note_id,
              target: ref.note_id
            });
          });
        }
      });

      return { nodes, edges };
    }
  });

  if (!graphData) return <div>Loading graph...</div>;

  return (
    <div className="h-screen">
      <GraphVisualization
        nodes={graphData.nodes}
        edges={graphData.edges}
        onNodeClick={(nodeId) => {
          // Navigate to note
          window.location.href = `/vault/${nodeId}`;
        }}
      />
    </div>
  );
}
```

---

## Common Integration Challenges

### 1. Wiki-Link Resolution

Your Obsidian clone likely expects `[[Note Title]]` syntax. You need to resolve titles to IDs:

```typescript
// src/lib/wiki-link-resolver.ts

import { apiClient } from '../api/client';

class WikiLinkResolver {
  private titleToIdMap: Map<string, string> = new Map();

  async initialize() {
    const response = await apiClient.get('/notes?limit=1000');
    response.data.notes.forEach((note: any) => {
      this.titleToIdMap.set(note.title.toLowerCase(), note.note_id);
    });
  }

  resolveLink(wikiLink: string): string | null {
    // Extract title from [[Title]]
    const title = wikiLink.replace(/\[\[|\]\]/g, '').trim().toLowerCase();
    return this.titleToIdMap.get(title) || null;
  }

  // Convert [[Title]] to markdown link with ID
  convertToMarkdown(content: string): string {
    return content.replace(/\[\[([^\]]+)\]\]/g, (match, title) => {
      const noteId = this.resolveLink(`[[${title}]]`);
      if (noteId) {
        return `[${title}](/vault/${noteId})`;
      }
      return match; // Keep original if not found
    });
  }
}

export const wikiLinkResolver = new WikiLinkResolver();
```

### 2. Real-time Sync

If multiple users or devices are editing:

```typescript
// Use polling or WebSocket for real-time updates
import { usePolling } from '../hooks/usePolling';

function NoteEditor({ noteId }: { noteId: string }) {
  const [remoteVersion, setRemoteVersion] = useState(0);
  const [localVersion, setLocalVersion] = useState(0);

  // Poll for changes every 5 seconds
  usePolling(
    async () => {
      const metadata = await obsidianAdapter.getMetadata(noteId);
      const remoteUpdated = new Date(metadata.modified).getTime();

      if (remoteUpdated > remoteVersion && remoteVersion > 0) {
        // Note was updated remotely
        if (localVersion < remoteUpdated) {
          // Ask user if they want to reload
          if (confirm('Note was updated. Reload?')) {
            window.location.reload();
          }
        }
      }

      setRemoteVersion(remoteUpdated);
    },
    5000, // 5 seconds
    noteId !== undefined
  );

  // ... rest of editor
}
```

### 3. Offline Support

If your Obsidian clone supports offline mode:

```typescript
// Use IndexedDB or LocalStorage for offline cache
import { openDB } from 'idb';

const db = await openDB('obsidian-cache', 1, {
  upgrade(db) {
    db.createObjectStore('notes', { keyPath: 'id' });
  }
});

// Cache notes locally
async function cacheNote(note: Note) {
  await db.put('notes', note);
}

// Get note from cache
async function getCachedNote(id: string): Promise<Note | undefined> {
  return await db.get('notes', id);
}

// Try cache first, then API
async function getNote(id: string): Promise<Note> {
  try {
    const cached = await getCachedNote(id);
    if (cached && !navigator.onLine) {
      return cached;
    }

    const note = await obsidianAdapter.readFile(id);
    await cacheNote({ id, content: note } as Note);
    return { id, content: note } as Note;
  } catch (err) {
    // Fallback to cache if API fails
    const cached = await getCachedNote(id);
    if (cached) return cached;
    throw err;
  }
}
```

---

## Testing Integration

### 1. Create Test Page

```typescript
// src/pages/ObsidianTest.tsx

export function ObsidianTest() {
  const [noteId, setNoteId] = useState('');

  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">Obsidian Integration Test</h1>

      <div className="mb-4">
        <input
          type="text"
          value={noteId}
          onChange={(e) => setNoteId(e.target.value)}
          placeholder="Enter note ID"
          className="border px-4 py-2 w-full"
        />
      </div>

      <ObsidianWrapper
        noteId={noteId}
        onNavigate={(id) => {
          console.log('Navigate to:', id);
          setNoteId(id);
        }}
      />
    </div>
  );
}
```

### 2. Add Test Route

```typescript
// In development only
{process.env.NODE_ENV === 'development' && (
  <Route path="/test/obsidian" element={<ObsidianTest />} />
)}
```

### 3. Test Checklist

- [ ] Load note by ID
- [ ] Edit and save note
- [ ] Wiki-link navigation works
- [ ] Search returns correct results
- [ ] Graph view shows connections
- [ ] File explorer shows all notes
- [ ] Authentication works (user can only see their notes)
- [ ] Responsive design works on mobile
- [ ] Keyboard shortcuts work
- [ ] Performance is acceptable (loads in <2s)

---

## Deployment Considerations

### 1. Bundle Size

Your Obsidian clone may increase bundle size significantly. Use code splitting:

```typescript
// Lazy load Obsidian component
const ObsidianWrapper = React.lazy(() =>
  import('../components/ObsidianClone/ObsidianWrapper')
);

function NotePage() {
  return (
    <React.Suspense fallback={<div>Loading editor...</div>}>
      <ObsidianWrapper />
    </React.Suspense>
  );
}
```

### 2. CDN for Assets

If your Obsidian clone has large assets (fonts, icons):

```typescript
// Load from CDN instead of bundling
<link
  href="https://cdn.example.com/obsidian-assets/styles.css"
  rel="stylesheet"
/>
```

### 3. Performance Optimization

```typescript
// Virtualize long lists
import { FixedSizeList } from 'react-window';

function FileExplorer({ notes }: { notes: Note[] }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={notes.length}
      itemSize={35}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          {notes[index].title}
        </div>
      )}
    </FixedSizeList>
  );
}
```

---

## Next Steps

To proceed with integration, please provide:

1. **Repository/Code Location**: Where is your Obsidian clone code?
2. **Technology Stack**: What framework/libraries does it use?
3. **Current Features**: What features are implemented?
4. **Storage Mechanism**: How does it currently store notes?
5. **Deployment Status**: Is it deployed somewhere we can test?

Once I know these details, I can provide specific integration code for your exact setup.

---

## Example: Complete Integration Flow

Here's a complete user flow after integration:

1. **User submits YouTube URL** → Video is processed → Note is created in DynamoDB/S3
2. **User clicks "View Note"** → React Router navigates to `/vault/{noteId}`
3. **ObsidianWrapper loads** → Fetches note from API via adapter
4. **User edits note** → Changes saved to DynamoDB via API
5. **User clicks wiki-link** → Resolves link, navigates to linked note
6. **User opens Graph View** → Shows visual connections between all notes
7. **User searches** → Full-text search via API returns results
8. **User navigates back** → Returns to dashboard

---

**Ready to help you integrate! Please share details about your Obsidian clone and I'll provide specific implementation code.** 🚀
