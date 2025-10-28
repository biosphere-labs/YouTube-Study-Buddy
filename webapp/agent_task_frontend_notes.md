# Agent Task: Frontend Notes Management & Display

## Branch: `feature/frontend-notes`

## Objective
Implement notes list, search/filter, note viewer, and provide integration points for custom editor and knowledge graph.

## Tasks

### 1. Note Types
```typescript
// types/note.ts
export interface Note {
  id: string;
  userId: string;
  videoId?: string;
  title: string;
  content: string;
  subject?: string;
  assessmentContent?: string;
  pdfUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateNoteDto {
  title?: string;
  content?: string;
  subject?: string;
}

export interface NotesQuery {
  subject?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedNotes {
  data: Note[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### 2. API Hooks
```typescript
// hooks/useNotes.ts
export function useNotes(query?: NotesQuery) {
  return useQuery({
    queryKey: ['notes', query],
    queryFn: () =>
      api.get<PaginatedNotes>('/notes', { params: query })
        .then(res => res.data),
  });
}

export function useNote(id: string) {
  return useQuery({
    queryKey: ['notes', id],
    queryFn: () => api.get<Note>(`/notes/${id}`).then(res => res.data),
    enabled: !!id,
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNoteDto }) =>
      api.put<Note>(`/notes/${id}`, data).then(res => res.data),
    onSuccess: (data) => {
      queryClient.setQueryData(['notes', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/notes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}
```

### 3. Notes List Page
```typescript
// pages/Notes.tsx
- Display grid/list of note cards
- Search bar (search by title/content)
- Filter by subject (dropdown)
- Sort options (date, title, subject)
- Pagination controls
- Empty state when no notes
- Loading skeletons
```

### 4. Note Card Component
```typescript
// components/notes/NoteCard.tsx
- Note title (truncated)
- Content preview (first 100 chars)
- Subject badge
- Created/updated date
- Assessment badge (if has assessments)
- PDF download link (if available)
- Click to open note
- Context menu (edit, delete, export)
```

### 5. Note Details Page
```typescript
// pages/NoteDetails.tsx
- Note metadata section:
  - Title (editable inline)
  - Subject badge
  - Created/updated dates
  - Link to source video (if exists)
  - PDF download button (if available)
- Content section:
  - Read-only markdown preview (initial view)
  - Edit button → switches to editor mode
- Assessment section (if exists):
  - Collapsible panel
  - Display assessment questions
- Actions:
  - Save button (when editing)
  - Delete button (with confirmation)
  - Export button (PDF/Markdown)
```

### 6. Note Editor Container (Integration Point)
```typescript
// components/notes/NoteEditorContainer.tsx
/**
 * Integration point for custom Obsidian-style editor
 * This component wraps the note content and provides
 * the interface for YOUR custom editor implementation.
 */

interface NoteEditorContainerProps {
  noteId: string;
  initialContent: string;
  onSave: (content: string) => Promise<void>;
  readOnly?: boolean;
}

export function NoteEditorContainer(props: NoteEditorContainerProps) {
  // For MVP: Simple textarea or markdown editor
  // YOU REPLACE THIS with your custom editor

  return (
    <div className="note-editor-container">
      {/* Placeholder: Simple markdown editor */}
      <textarea
        defaultValue={props.initialContent}
        className="w-full min-h-[500px] p-4 font-mono"
      />

      {/* YOUR CUSTOM EDITOR GOES HERE */}
      {/* Example:
      <ObsidianStyleEditor
        content={props.initialContent}
        onChange={handleChange}
        onSave={props.onSave}
        readOnly={props.readOnly}
      />
      */}
    </div>
  );
}
```

### 7. Knowledge Graph Container (Integration Point)
```typescript
// components/notes/GraphContainer.tsx
/**
 * Integration point for knowledge graph visualization
 * This component provides the interface for YOUR custom
 * graph implementation to display note relationships.
 */

interface GraphContainerProps {
  userId: string;
  noteIds: string[];
  onNodeClick: (noteId: string) => void;
  onLinkClick?: (sourceId: string, targetId: string) => void;
}

export function GraphContainer(props: GraphContainerProps) {
  // For MVP: Simple list view or placeholder
  // YOU REPLACE THIS with your graph visualization

  return (
    <div className="graph-container border rounded p-4">
      <p className="text-muted-foreground">
        Graph visualization integration point
      </p>

      {/* YOUR GRAPH VISUALIZATION GOES HERE */}
      {/* Example:
      <KnowledgeGraph
        nodes={notes}
        links={relationships}
        onNodeClick={props.onNodeClick}
      />
      */}
    </div>
  );
}
```

### 8. Search and Filter Component
```typescript
// components/notes/NotesFilters.tsx
- Search input (debounced)
- Subject filter dropdown
- Sort dropdown (date, title, subject)
- View mode toggle (grid/list)
- Clear filters button
```

### 9. Notes Grid/List View
```typescript
// components/notes/NotesGrid.tsx
- Responsive grid layout (1/2/3/4 columns based on screen size)
- Card hover effects
- Loading skeletons
- Empty state

// components/notes/NotesList.tsx
- Compact list layout
- More metadata visible
- Alternating row colors
```

### 10. Note Preview Component
```typescript
// components/notes/NotePreview.tsx
- Render markdown content (read-only)
- Syntax highlighting for code blocks
- Handle wiki-style links [[Note Title]]
- Handle images
- Handle tables
- Scroll to heading links
```

### 11. Subject Badge Component
```typescript
// components/notes/SubjectBadge.tsx
- Color-coded by subject
- Clickable to filter by subject
- Tooltip with subject info
```

### 12. Markdown Utilities
```typescript
// lib/markdown.ts
- Parse markdown to HTML
- Extract frontmatter
- Extract wiki-style links
- Generate table of contents
- Sanitize HTML output
```

## Dependencies to Install
```bash
npm install react-markdown remark-gfm rehype-raw rehype-sanitize
npm install react-syntax-highlighter
npm install @types/react-syntax-highlighter
npm install date-fns  # Date formatting
```

## Success Criteria
- ✅ Notes list displays all user's notes
- ✅ Search filters notes by title/content
- ✅ Filter by subject works correctly
- ✅ Pagination works correctly
- ✅ Clicking note opens detail page
- ✅ Note content renders markdown correctly
- ✅ Wiki-style links are detected
- ✅ Edit mode allows content updates
- ✅ Save updates note in database
- ✅ Delete note works (with confirmation)
- ✅ Assessment section displays when available
- ✅ Integration containers are ready for custom components

## Pages to Implement
```
/notes             - Notes list with search/filter
/notes/:id         - Note details/viewer
/notes/:id/edit    - Note editor (optional separate route)
```

## Components to Create
```
<NotesList>                - Grid/list of notes
<NoteCard>                 - Individual note preview
<NoteDetails>              - Full note view
<NoteEditorContainer>      - Integration point for editor
<GraphContainer>           - Integration point for graph
<NotesFilters>             - Search/filter controls
<NotePreview>              - Markdown renderer
<SubjectBadge>             - Subject indicator
<AssessmentPanel>          - Collapsible assessment view
```

## Markdown Features to Support
- Headers (H1-H6)
- Bold, italic, strikethrough
- Lists (ordered, unordered)
- Code blocks with syntax highlighting
- Inline code
- Links (external and wiki-style [[Note]])
- Images
- Tables
- Blockquotes
- Horizontal rules

## Wiki-Style Link Parsing
```typescript
// Regex: /\[\[([^\]]+)\]\]/g
// Example: [[Another Note]] → Link to note with title "Another Note"
// On click: Search for note by title, navigate if found
```

## Testing
- Test notes list rendering
- Test search functionality
- Test filtering by subject
- Test pagination
- Test note detail view
- Test markdown rendering
- Test wiki-link parsing
- Test note editing
- Test note deletion
- Test empty states

## Integration Points
- Depends on auth module (useAuth hook)
- Uses API client from auth module
- `<NoteEditorContainer>` ready for YOUR custom editor
- `<GraphContainer>` ready for YOUR knowledge graph
- Provides note data structure for external components

## Notes
- Use React Query for server state
- Implement optimistic updates for better UX
- Debounce search input (300ms)
- Cache rendered markdown
- Lazy load note content (load on detail page, not in list)
- Consider virtualization for long note lists
- Implement keyboard shortcuts (Ctrl+S to save, Esc to cancel)
- Add export functionality (download as .md or .pdf)
- Implement note templates (if time permits)
- Consider adding tags in addition to subjects

## Integration Examples

### Using the Editor Container
```typescript
// In your custom code:
import { NoteEditorContainer } from '@/components/notes/NoteEditorContainer';

<NoteEditorContainer
  noteId={note.id}
  initialContent={note.content}
  onSave={async (content) => {
    await updateNote({ id: note.id, data: { content } });
  }}
/>
```

### Using the Graph Container
```typescript
// In your custom code:
import { GraphContainer } from '@/components/notes/GraphContainer';

<GraphContainer
  userId={user.id}
  noteIds={notes.map(n => n.id)}
  onNodeClick={(noteId) => navigate(`/notes/${noteId}`)}
/>
```
