# Notes Module - Frontend Implementation

## Overview

The Notes Module provides a complete notes management and display system for the YouTube Study Buddy web application. It includes:

- **Notes List**: Grid/list view with search, filter, sort, and pagination
- **Note Details**: Full note viewer with markdown rendering
- **Note Editor**: Editable note content with auto-save
- **Wiki-style Links**: Support for `[[Note Title]]` links
- **Assessment Display**: Collapsible assessment questions panel
- **Integration Points**: Placeholder components for custom editor and knowledge graph

## Architecture

### Directory Structure

```
src/
├── types/
│   └── note.ts                    # TypeScript types and interfaces
├── lib/
│   ├── api.ts                     # Axios API client configuration
│   └── markdown.ts                # Markdown parsing utilities
├── hooks/
│   └── useNotes.ts                # React Query hooks for API calls
├── components/notes/
│   ├── SubjectBadge.tsx           # Color-coded subject badge
│   ├── NoteCard.tsx               # Note preview card
│   ├── NotesFilters.tsx           # Search, filter, sort controls
│   ├── NotesGrid.tsx              # Grid layout for notes
│   ├── NotesList.tsx              # List layout for notes
│   ├── NotePreview.tsx            # Markdown renderer
│   ├── AssessmentPanel.tsx        # Collapsible assessment display
│   ├── NoteEditorContainer.tsx    # INTEGRATION POINT: Custom editor
│   └── GraphContainer.tsx         # INTEGRATION POINT: Knowledge graph
└── pages/
    ├── Notes.tsx                  # Notes list page
    └── NoteDetails.tsx            # Note detail/editor page
```

## Features

### 1. Notes List Page (`/notes`)

**Components:**
- `NotesFilters`: Search, subject filter, sort, view mode toggle
- `NotesGrid`: Responsive grid layout (1/2/3 columns)
- `NotesList`: Compact list layout with metadata
- Pagination controls with page numbers

**Features:**
- Debounced search (300ms)
- Filter by subject
- Sort by date, title, or subject
- Toggle between grid/list view
- Loading skeletons
- Empty states
- Note deletion with confirmation

### 2. Note Details Page (`/notes/:id`)

**Features:**
- Inline title editing
- Toggle between view and edit modes
- Markdown preview with syntax highlighting
- Wiki-style link detection and handling
- Knowledge graph toggle
- Assessment panel (collapsible)
- Export to markdown
- PDF download (if available)
- Source video link
- Delete with confirmation

### 3. Markdown Rendering

**Supported Features:**
- Headers (H1-H6)
- Bold, italic, strikethrough
- Code blocks with syntax highlighting (via Prism)
- Inline code
- Links (external open in new tab)
- Wiki-style links: `[[Note Title]]`
- Lists (ordered and unordered)
- Tables
- Blockquotes
- Images

**Libraries Used:**
- `react-markdown` - Core markdown parsing
- `remark-gfm` - GitHub Flavored Markdown
- `rehype-raw` - Allow raw HTML
- `rehype-sanitize` - Sanitize HTML for security
- `react-syntax-highlighter` - Code syntax highlighting

### 4. API Integration

**Endpoints:**
- `GET /notes` - List notes (with query params)
- `GET /notes/:id` - Get single note
- `PUT /notes/:id` - Update note
- `DELETE /notes/:id` - Delete note

**React Query Hooks:**
```typescript
useNotes(query?: NotesQuery)      // List notes
useNote(id: string)                // Get single note
useUpdateNote()                    // Update mutation
useDeleteNote()                    // Delete mutation
```

**Query Features:**
- Automatic caching
- Optimistic updates
- Query invalidation on mutations
- Loading/error states

## Integration Points

### NoteEditorContainer

**Purpose:** Placeholder for a custom Obsidian-style editor.

**Props:**
```typescript
interface NoteEditorContainerProps {
  noteId: string;
  initialContent: string;
  onSave: (content: string) => Promise<void>;
  readOnly?: boolean;
}
```

**Current Implementation:**
- Simple textarea with save button
- Keyboard shortcut: Ctrl/Cmd+S to save
- Unsaved changes indicator
- Markdown syntax help

**To Replace:**
1. Import your custom editor component
2. Pass through the same props interface
3. Wire up the `onSave` callback
4. Maintain read-only mode support

**Example Usage:**
```typescript
<NoteEditorContainer
  noteId={note.id}
  initialContent={note.content}
  onSave={async (content) => {
    await updateNote({ id: note.id, data: { content } });
  }}
  readOnly={false}
/>
```

### GraphContainer

**Purpose:** Placeholder for a knowledge graph visualization.

**Props:**
```typescript
interface GraphContainerProps {
  userId: string;
  noteIds: string[];
  onNodeClick: (noteId: string) => void;
  onLinkClick?: (sourceId: string, targetId: string) => void;
}
```

**Current Implementation:**
- Placeholder with instructions
- Blue dashed border to indicate integration point

**To Replace:**
1. Import graph library (D3, vis.js, react-force-graph, etc.)
2. Fetch note data and relationships from API
3. Transform data into nodes/edges format
4. Wire up click callbacks for navigation

**Suggested Features:**
- Display notes as nodes
- Show wiki-links as edges
- Color-code by subject
- Interactive zoom/pan
- Search and filter nodes
- Hover tooltips with metadata

**Example Usage:**
```typescript
<GraphContainer
  userId={user.id}
  noteIds={notes.map(n => n.id)}
  onNodeClick={(noteId) => navigate(`/notes/${noteId}`)}
  onLinkClick={(source, target) => {
    console.log(`Link: ${source} -> ${target}`);
  }}
/>
```

## Utilities

### Markdown Utilities (`lib/markdown.ts`)

**Functions:**
- `extractWikiLinks(content)` - Extract all wiki-style links
- `processWikiLinks(content, onLinkClick)` - Replace wiki-links with HTML
- `extractFrontmatter(content)` - Parse YAML frontmatter
- `generateTOC(content)` - Generate table of contents from headers
- `truncateMarkdown(content, maxLength)` - Truncate for previews

### Subject Badge Colors

Predefined color schemes for common subjects:
- STEM: Mathematics (blue), Physics (purple), Chemistry (green), etc.
- Humanities: History (amber), Literature (pink), Philosophy (slate)
- Languages: English (cyan), Spanish (red), French (violet)
- Arts: Music (fuchsia), Art (rose)
- Social Sciences: Economics (orange), Psychology (teal)

## Data Flow

```
1. User visits /notes
   ↓
2. Notes page calls useNotes(query)
   ↓
3. React Query fetches from GET /notes
   ↓
4. NotesFilters updates query state
   ↓
5. NotesGrid/NotesList displays results
   ↓
6. User clicks note → navigate to /notes/:id
   ↓
7. NoteDetails calls useNote(id)
   ↓
8. Displays NotePreview or NoteEditorContainer
   ↓
9. User edits → calls useUpdateNote()
   ↓
10. Optimistic update + cache invalidation
```

## Key Design Decisions

### 1. React Query for Server State
- Automatic caching and background refetching
- Optimistic updates for better UX
- Centralized error handling
- Reduces boilerplate compared to manual state management

### 2. Separate Grid/List Components
- Allows different layouts without complex conditionals
- Easier to maintain and extend
- Better performance (only render what's needed)

### 3. Wiki-Link Processing
- Regex: `/\[\[([^\]]+)\]\]/g`
- Converted to clickable links with data attributes
- Event delegation for click handling
- Prevents XSS by using data attributes instead of inline onclick

### 4. Markdown Security
- `rehype-sanitize` prevents XSS attacks
- External links open in new tab with `rel="noopener noreferrer"`
- HTML is sanitized before rendering

### 5. Integration Points as Components
- Provides clear contract via props interface
- Allows drop-in replacement without modifying parent components
- Visual indicators help identify what needs to be replaced
- Preserves functionality even with placeholder implementations

## State Management

### Local State (useState)
- UI-only state: view mode, editing mode, filters
- Ephemeral: doesn't need to persist

### Server State (React Query)
- Notes data, single note data
- Cached and synchronized with backend
- Automatic revalidation

### URL State (Router)
- Page number, note ID
- Shareable and bookmarkable

## Performance Optimizations

1. **Lazy Loading**: Note content only loaded on details page
2. **Pagination**: Limits data fetched per request
3. **Debounced Search**: Reduces API calls during typing
4. **Query Caching**: Avoids refetching unchanged data
5. **Optimistic Updates**: Immediate UI feedback before server response
6. **Loading Skeletons**: Better perceived performance

## Error Handling

- Network errors: Display error message with retry option
- 404 Not Found: Redirect to notes list with message
- 401 Unauthorized: Handled by API interceptor
- Validation errors: Display inline error messages
- Delete confirmation: Prevents accidental deletions

## Accessibility

- Semantic HTML elements
- Keyboard navigation support (Ctrl+S to save)
- Focus management for modals/dialogs
- Alt text for icons (aria-label)
- Color contrast meets WCAG AA standards
- Screen reader friendly

## Testing Recommendations

### Unit Tests
- Markdown utilities (truncate, extract links, etc.)
- Subject badge color mapping
- Date formatting functions

### Component Tests
- NoteCard renders correctly
- NotesFilters updates query state
- NotePreview renders markdown
- Wiki-link click handlers fire correctly

### Integration Tests
- Notes list fetches and displays data
- Search/filter/sort updates results
- Pagination works correctly
- Note editing saves changes
- Delete removes note and redirects

### E2E Tests
- Full user journey: list → view → edit → save
- Wiki-link navigation between notes
- Assessment panel expand/collapse
- Export to markdown downloads file

## Future Enhancements

### Short-term
1. Bulk operations (select multiple notes, delete all)
2. Note templates
3. Tags in addition to subjects
4. Duplicate note functionality
5. Note history/versioning

### Long-term
1. Real-time collaboration
2. Note sharing and permissions
3. Advanced search (full-text, filters)
4. Custom themes and font sizes
5. Offline support with PWA
6. Mobile app with React Native

## Dependencies

```json
{
  "@tanstack/react-query": "^latest",
  "axios": "^latest",
  "date-fns": "^latest",
  "react-markdown": "^latest",
  "react-router-dom": "^latest",
  "react-syntax-highlighter": "^latest",
  "remark-gfm": "^latest",
  "rehype-raw": "^latest",
  "rehype-sanitize": "^latest",
  "zustand": "^latest" // (if needed for global state)
}
```

## Environment Variables

```env
VITE_API_URL=http://localhost:3000   # Backend API URL
VITE_WS_URL=ws://localhost:3000      # WebSocket URL (for real-time updates)
```

## Migration from Old Code

If replacing existing notes code:

1. Update imports to new component paths
2. Replace old API calls with React Query hooks
3. Update routing to use new page components
4. Replace custom markdown renderer with NotePreview
5. Test thoroughly, especially wiki-link functionality

## Support

For issues or questions:
- Check the agent_task.md for task specifications
- Review PRODUCT_SPEC.md for overall architecture
- Contact integration team for editor/graph replacement

## Summary

The Notes Module provides a complete, production-ready notes management system with:
- ✅ Full CRUD operations
- ✅ Search, filter, sort, pagination
- ✅ Markdown rendering with syntax highlighting
- ✅ Wiki-style link support
- ✅ Assessment display
- ✅ Export functionality
- ✅ Clear integration points for custom components

The code is modular, well-typed, performant, and ready for the integration of custom editor and graph visualization components.
