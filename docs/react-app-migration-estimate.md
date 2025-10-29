# React + Vite Migration: Effort Estimate

## Executive Summary

**Estimated Time: 6-8 weeks** (full-time development)

This document provides a detailed breakdown of migrating the Streamlit YouTube Study Buddy application to a React + Vite web application with social authentication, database storage, and an integrated Obsidian-style editor with graph visualization.

---

## Current Streamlit App Analysis

### Core Features (from streamlit_app.py)
1. **Video Processing** (~900 lines)
   - URL input/validation
   - Playlist extraction (yt-dlp)
   - Progress tracking
   - Session-based storage
   - Batch processing

2. **Configuration**
   - API key management
   - Subject categorization
   - Feature toggles (assessments, PDF export, auto-categorize)
   - Session management

3. **Monitoring/Analytics** (Currently in UI, limited)
   - Processing log display with filtering/sorting
   - Exit node usage tracking
   - Knowledge graph stats
   - Job details with timings

4. **File Management**
   - Session-based directory structure
   - ZIP download functionality
   - Markdown + PDF export

---

## React App Architecture

### Technology Stack Recommendation

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Router (type-safe routing)
- TanStack Query (server state)
- Zustand (client state)
- Tailwind CSS + shadcn/ui (components)
- Monaco Editor (code/markdown editor)
- D3.js or React Flow (graph visualization)
- Tiptap (WYSIWYG editor with Obsidian-like features)

**Backend:**
- NestJS (Node.js framework)
- PostgreSQL (primary database)
- Prisma (ORM)
- Redis (queue management, caching)
- BullMQ (job processing)
- Socket.io (real-time updates)

**Authentication:**
- NextAuth.js or Auth0
- OAuth providers (Google, GitHub, Discord)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- MinIO or S3 (file storage)

---

## Development Breakdown

### Phase 1: Backend Foundation (2-3 weeks)

#### Week 1: Core Backend Setup
**Effort: 40-50 hours**

**Tasks:**
1. **NestJS Project Setup** (4 hours)
   - Initialize NestJS project
   - Configure TypeScript, ESLint, Prettier
   - Set up environment configuration
   - Docker setup for development

2. **Database Schema Design** (8 hours)
   - User model (with OAuth providers)
   - Video model (URL, video_id, metadata)
   - Note model (markdown content, relationships)
   - Concept model (for knowledge graph)
   - Assessment model
   - ProcessingJob model (for tracking)
   - File model (attachments, PDFs)

   ```prisma
   model User {
     id            String   @id @default(cuid())
     email         String   @unique
     name          String?
     avatar        String?
     providers     AuthProvider[]
     notes         Note[]
     videos        Video[]
     settings      UserSettings?
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

     // Knowledge graph relationships
     linkedNotes   NoteLink[] @relation("sourceNote")
     linkedFrom    NoteLink[] @relation("targetNote")
     concepts      Concept[]

     assessmentId  String?
     assessment    Assessment?

     createdAt     DateTime @default(now())
     updatedAt     DateTime @updatedAt
   }

   model Video {
     id            String   @id @default(cuid())
     userId        String
     user          User     @relation(fields: [userId], references: [id])
     videoId       String   // YouTube video ID
     url           String
     title         String
     transcript    String?  @db.Text
     notes         Note[]
     processingJob ProcessingJob?
     metadata      Json?    // Duration, method, etc.
     createdAt     DateTime @default(now())
   }

   model Concept {
     id            String   @id @default(cuid())
     name          String
     notes         Note[]
     @@unique([name])
   }

   model NoteLink {
     id            String   @id @default(cuid())
     sourceId      String
     source        Note     @relation("sourceNote", fields: [sourceId], references: [id])
     targetId      String
     target        Note     @relation("targetNote", fields: [targetId], references: [id])
     linkType      String   // "related", "references", "prerequisite"
     createdAt     DateTime @default(now())
   }

   model ProcessingJob {
     id            String   @id @default(cuid())
     userId        String
     videoId       String   @unique
     video         Video    @relation(fields: [videoId], references: [id])
     status        JobStatus
     stage         ProcessingStage
     progress      Int      @default(0)
     error         String?
     timings       Json?
     createdAt     DateTime @default(now())
     updatedAt     DateTime @updatedAt
   }

   model Assessment {
     id            String   @id @default(cuid())
     noteId        String   @unique
     note          Note     @relation(fields: [noteId], references: [id])
     content       String   @db.Text
     questions     Json     // Array of questions
     createdAt     DateTime @default(now())
   }
   ```

3. **Authentication Module** (8 hours)
   - NextAuth.js or Auth0 integration
   - JWT strategy
   - OAuth providers (Google, GitHub)
   - User session management
   - Protected routes middleware

4. **Video Processing Service** (12 hours)
   - Create NestJS service wrapping Python CLI
   - Job queue with BullMQ
   - WebSocket for real-time progress updates
   - Error handling and retries
   - Python subprocess management

5. **API Endpoints - Basic CRUD** (8 hours)
   - User profile endpoints
   - Video CRUD endpoints
   - Note CRUD endpoints
   - Processing job endpoints

#### Week 2: Python Integration & Processing Pipeline
**Effort: 40-50 hours**

**Tasks:**
1. **Python CLI Integration** (12 hours)
   - Create Node.js wrapper for Python CLI
   - Handle streaming output
   - Map Python results to database models
   - File upload handling (when needed)
   - Error mapping and translation

2. **Job Queue System** (10 hours)
   - BullMQ setup with Redis
   - Video processing jobs
   - Progress tracking
   - Parallel job management
   - Job prioritization
   - Retry logic

3. **Real-time Updates** (8 hours)
   - Socket.io setup
   - Progress event emitters
   - Job status updates
   - Live log streaming

4. **File Storage** (8 hours)
   - MinIO or S3 integration
   - Markdown file storage
   - PDF storage
   - Presigned URL generation
   - File cleanup policies

5. **API Endpoints - Advanced** (10 hours)
   - Batch video processing
   - Knowledge graph queries
   - Search endpoints
   - Statistics/analytics endpoints

#### Week 3: Knowledge Graph & Search
**Effort: 40-50 hours**

**Tasks:**
1. **Knowledge Graph Service** (16 hours)
   - Graph data structure in PostgreSQL
   - Concept extraction and linking
   - Note relationship mapping
   - Graph traversal algorithms
   - Similar notes discovery

2. **Search System** (12 hours)
   - Full-text search with PostgreSQL
   - Concept search
   - Video search
   - Filter/sort capabilities

3. **Analytics Service** (8 hours)
   - User statistics
   - Processing metrics
   - Knowledge graph analytics
   - Usage tracking

4. **Testing & Documentation** (10 hours)
   - Unit tests for services
   - Integration tests
   - API documentation (Swagger)
   - Setup documentation

---

### Phase 2: Frontend Development (2-3 weeks)

#### Week 4: Core UI Components & Layout
**Effort: 40-50 hours**

**Tasks:**
1. **Project Setup** (4 hours)
   - Vite + React + TypeScript
   - Tailwind CSS + shadcn/ui
   - TanStack Router
   - TanStack Query
   - Zustand state management
   - Type generation from backend

2. **Authentication UI** (10 hours)
   - Login page with OAuth buttons
   - Registration flow
   - Profile management
   - Session handling
   - Protected route components

3. **Layout Components** (8 hours)
   - Main app shell
   - Sidebar navigation
   - Header with user menu
   - Responsive layout
   - Dark mode support

4. **Dashboard** (10 hours)
   - Recent notes overview
   - Processing queue status
   - Knowledge graph preview
   - Quick actions
   - Statistics widgets

5. **Settings Page** (8 hours)
   - User profile settings
   - API key management
   - Processing preferences
   - Theme selection
   - Export/import settings

#### Week 5: Video Processing & Note Management
**Effort: 40-50 hours**

**Tasks:**
1. **Video Input UI** (12 hours)
   - URL input form
   - Playlist extraction
   - Batch URL input
   - URL validation
   - Subject categorization
   - Processing options panel

2. **Processing Queue UI** (12 hours)
   - Job list with status
   - Real-time progress updates (Socket.io)
   - Job details modal
   - Retry/cancel controls
   - Log viewer

3. **Notes List View** (10 hours)
   - Grid/list view toggle
   - Search and filters
   - Subject grouping
   - Sorting options
   - Bulk actions

4. **Note Preview Cards** (6 hours)
   - Thumbnail/preview
   - Metadata display
   - Quick actions
   - Related notes count

#### Week 6: Obsidian-style Editor & Graph
**Effort: 45-55 hours**

**Tasks:**
1. **Markdown Editor** (16 hours)
   - Tiptap editor integration
   - Obsidian-style [[wiki links]]
   - Syntax highlighting
   - Real-time preview
   - Auto-save
   - Collaborative editing (future)
   - Keyboard shortcuts

2. **Graph Visualization** (16 hours)
   - React Flow or D3.js setup
   - Node rendering (notes as nodes)
   - Edge rendering (relationships)
   - Interactive zoom/pan
   - Node clustering
   - Highlight connected nodes
   - Filter by subject/concept
   - Graph layout algorithms

3. **Note Viewer/Editor** (12 hours)
   - Split view (editor + preview)
   - Linked notes sidebar
   - Backlinks panel
   - Assessment viewer
   - PDF export button
   - Version history (future)

4. **Concept Management** (8 hours)
   - Concept tag system
   - Auto-suggestion
   - Concept detail view
   - Related notes by concept

---

### Phase 3: Advanced Features (1-2 weeks)

#### Week 7: Polish & Advanced Features
**Effort: 40-50 hours**

**Tasks:**
1. **Advanced Search** (10 hours)
   - Global search bar
   - Search results page
   - Filters (date, subject, concepts)
   - Search highlighting
   - Recent searches

2. **Knowledge Graph Explorer** (12 hours)
   - Full-page graph view
   - Interactive exploration
   - Path finding between notes
   - Concept clustering view
   - Export graph as image

3. **Analytics Dashboard** (8 hours)
   - Processing statistics
   - Learning progress tracking
   - Concept coverage
   - Study time tracking
   - Charts and visualizations

4. **Export/Import** (10 hours)
   - Export notes as ZIP (Obsidian vault)
   - Import from Obsidian vault
   - Bulk export
   - Format conversion

5. **Mobile Responsiveness** (8 hours)
   - Mobile-optimized layouts
   - Touch gestures for graph
   - Simplified mobile editor
   - PWA setup (optional)

#### Week 8: Testing, Optimization & Deployment
**Effort: 40-50 hours**

**Tasks:**
1. **Testing** (16 hours)
   - Frontend unit tests (Vitest)
   - Component tests (React Testing Library)
   - E2E tests (Playwright)
   - Backend integration tests
   - Load testing

2. **Performance Optimization** (10 hours)
   - Code splitting
   - Lazy loading
   - Query optimization
   - Caching strategies
   - Bundle size optimization

3. **Error Handling & UX** (8 hours)
   - Error boundaries
   - Loading states
   - Empty states
   - Toast notifications
   - Form validation

4. **Documentation** (6 hours)
   - User guide
   - Developer documentation
   - API documentation
   - Deployment guide

5. **Deployment Setup** (10 hours)
   - Docker production builds
   - CI/CD pipeline
   - Environment configuration
   - Database migrations
   - Monitoring setup

---

## Detailed Effort Summary

| Phase | Component | Hours | Notes |
|-------|-----------|-------|-------|
| **Backend** | | | |
| Week 1 | Core Setup | 40-50 | NestJS, DB, Auth, Basic API |
| Week 2 | Python Integration | 40-50 | Queue, WebSocket, File Storage |
| Week 3 | Knowledge Graph | 40-50 | Graph service, Search, Analytics |
| **Frontend** | | | |
| Week 4 | Core UI | 40-50 | Auth, Layout, Dashboard, Settings |
| Week 5 | Processing UI | 40-50 | Video input, Queue, Notes list |
| Week 6 | Editor & Graph | 45-55 | Tiptap, Graph viz, Note viewer |
| **Advanced** | | | |
| Week 7 | Features | 40-50 | Search, Graph explorer, Export |
| Week 8 | Polish | 40-50 | Testing, Optimization, Deploy |
| **TOTAL** | | **325-400 hours** | **6-8 weeks full-time** |

---

## Risk Factors & Challenges

### High-Risk Items
1. **Graph Visualization Performance** (⚠️ HIGH)
   - Large graphs (>1000 nodes) may lag
   - Solution: Virtual rendering, clustering, pagination
   - Add 8-12 hours for optimization

2. **Python-Node Integration** (⚠️ MEDIUM)
   - Subprocess management complexity
   - Error handling across languages
   - Add 6-8 hours for edge cases

3. **Real-time Updates at Scale** (⚠️ MEDIUM)
   - Socket.io connection management
   - Broadcasting to many users
   - Add 4-6 hours for optimization

### Medium-Risk Items
1. **Authentication Security**
   - OAuth flow edge cases
   - Token refresh handling
   - Included in auth estimate

2. **File Storage Costs**
   - S3/MinIO costs for many users
   - Cleanup policies needed
   - Included in file storage estimate

---

## Comparison: Streamlit vs React

| Feature | Streamlit (Current) | React + NestJS |
|---------|---------------------|----------------|
| **Development Time** | 1-2 weeks | 6-8 weeks |
| **User Experience** | Basic, page reloads | Modern, real-time |
| **Authentication** | None | Full OAuth |
| **Data Persistence** | File-based, session | PostgreSQL, multi-user |
| **Scalability** | Single user | Multi-tenant |
| **Graph Visualization** | None | Interactive, zoomable |
| **Editor** | None (download files) | Built-in Obsidian-style |
| **Real-time Updates** | None | WebSocket-based |
| **Mobile Support** | Poor | Responsive + PWA |
| **Deployment** | Simple (Streamlit Cloud) | More complex (Docker, etc.) |

---

## Cost Breakdown (Infrastructure)

### Development Environment
- **Free**: PostgreSQL, Redis, MinIO (Docker)

### Production (Estimated Monthly)
- **Hosting**: $20-50/month (DigitalOcean/Hetzner VPS)
- **Database**: Included in VPS or $15/month (managed)
- **File Storage**: $5-20/month (MinIO/S3)
- **Authentication**: Free tier (Auth0) or self-hosted
- **Total**: ~$40-100/month for 100-1000 users

---

## Recommended Approach

### Option 1: Full Build (Recommended)
**Time: 6-8 weeks**
- Complete feature parity + new features
- Production-ready with auth and multi-user
- Best long-term solution

### Option 2: MVP First (Faster)
**Time: 3-4 weeks**
- Skip: Advanced graph features, analytics, export
- Basic auth (email/password only)
- Simple editor (Monaco instead of Tiptap)
- Basic graph visualization
- Then iterate based on feedback

### Option 3: Hybrid Approach
**Time: 4-5 weeks**
- Keep Streamlit for admin/processing
- Build React app as viewer/editor only
- Shared database/storage
- Less work but split architecture

---

## Next Steps

1. **Validate Requirements**
   - Review this document
   - Prioritize features
   - Identify must-haves vs nice-to-haves

2. **Choose Approach**
   - Full build vs MVP vs Hybrid
   - Timeline requirements
   - Budget constraints

3. **Set Up Development Environment**
   - Backend stack
   - Frontend stack
   - Local development flow

4. **Start with Backend Phase 1**
   - Core infrastructure first
   - Then parallel frontend development

---

## Maintenance & Ongoing Effort

Post-launch maintenance (per month):
- **Bug fixes**: 4-8 hours
- **Feature additions**: 8-16 hours
- **Infrastructure**: 2-4 hours
- **Security updates**: 2-4 hours
- **Total**: ~16-32 hours/month

---

## Conclusion

**Estimated Total Effort: 325-400 hours (6-8 weeks full-time)**

This is a significant undertaking but will result in a modern, scalable web application with:
- Multi-user support with authentication
- Database-backed storage
- Real-time processing updates
- Built-in Obsidian-style editor
- Interactive knowledge graph visualization
- Mobile-responsive design
- Production-ready infrastructure

The Streamlit app is excellent for prototyping and single-user scenarios, but migrating to React + NestJS provides the foundation for a production SaaS application.
