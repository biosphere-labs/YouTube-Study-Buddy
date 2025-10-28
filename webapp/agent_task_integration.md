# Agent Task: Integration & E2E Setup

## Branch: `feature/integration`

## Objective
Integrate all components, set up Docker Compose, configure environment, and perform end-to-end testing.

## Tasks

### 1. Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: ytstudy-postgres
    environment:
      POSTGRES_DB: ytstudy
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d ytstudy"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ytstudy-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ytstudy-backend
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/ytstudy
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
      DISCORD_CLIENT_ID: ${DISCORD_CLIENT_ID}
      DISCORD_CLIENT_SECRET: ${DISCORD_CLIENT_SECRET}
      PYTHON_CLI_PATH: /app/python-cli
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    volumes:
      - ./backend:/app
      - ../../src:/app/python-cli  # Mount Python CLI
      - backend_node_modules:/app/node_modules
    command: npm run start:dev

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ytstudy-frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://localhost:3000
      VITE_WS_URL: ws://localhost:3000
    volumes:
      - ./frontend:/app
      - frontend_node_modules:/app/node_modules
    command: npm run dev -- --host

volumes:
  postgres_data:
  redis_data:
  backend_node_modules:
  frontend_node_modules:
```

### 2. Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install Python and UV for CLI integration
RUN apk add --no-cache python3 py3-pip curl
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

COPY package*.json ./
RUN npm install

COPY . .

# Generate Prisma client
RUN npx prisma generate

EXPOSE 3000

CMD ["npm", "run", "start:dev"]
```

### 3. Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

### 4. Environment Configuration
Create `.env.example` files for both frontend and backend:

```bash
# backend/.env.example
DATABASE_URL="postgresql://user:pass@localhost:5432/ytstudy"
REDIS_URL="redis://localhost:6379"
JWT_SECRET="your-secret-key-change-in-production"
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GITHUB_CLIENT_ID="your-github-client-id"
GITHUB_CLIENT_SECRET="your-github-client-secret"
DISCORD_CLIENT_ID="your-discord-client-id"
DISCORD_CLIENT_SECRET="your-discord-client-secret"
PYTHON_CLI_PATH="/path/to/ytstudybuddy/src"
CLAUDE_API_KEY="sk-ant-..."
PORT=3000
NODE_ENV=development
```

```bash
# frontend/.env.example
VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000
```

### 5. Setup Scripts
```bash
# scripts/setup.sh
#!/bin/bash

echo "Setting up YouTube Study Buddy Web App..."

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

echo "Environment files created. Please update with your credentials."

# Install dependencies
echo "Installing backend dependencies..."
cd backend && npm install && cd ..

echo "Installing frontend dependencies..."
cd frontend && npm install && cd ..

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services
echo "Waiting for services to be ready..."
sleep 5

# Run Prisma migrations
echo "Running database migrations..."
cd backend && npx prisma migrate dev && cd ..

# Seed database (optional)
echo "Seeding database..."
cd backend && npm run seed && cd ..

echo "Setup complete! Run 'docker-compose up' to start all services."
```

### 6. Integration Testing Setup
```typescript
// backend/test/e2e/auth.e2e-spec.ts
describe('Authentication E2E', () => {
  it('should authenticate with Google OAuth', async () => {
    // Test OAuth flow
  });

  it('should return user info on /auth/me', async () => {
    // Test authenticated endpoint
  });

  it('should reject unauthenticated requests', async () => {
    // Test protected routes
  });
});

// backend/test/e2e/videos.e2e-spec.ts
describe('Videos E2E', () => {
  it('should submit video and create job', async () => {
    // Test video submission flow
  });

  it('should process job and create note', async () => {
    // Test full processing pipeline
  });
});
```

### 7. Integration Checklist
- [ ] Merge all feature branches into integration branch
- [ ] Resolve any merge conflicts
- [ ] Update import paths and module references
- [ ] Verify all dependencies are installed
- [ ] Run database migrations
- [ ] Start all services via Docker Compose
- [ ] Test backend health endpoint
- [ ] Test frontend loads correctly
- [ ] Test backend-frontend communication
- [ ] Test WebSocket connection

### 8. E2E Testing Scenarios

**Scenario 1: Full User Journey**
1. User visits /login
2. User signs in with Google
3. Redirected to /dashboard
4. Navigate to /videos
5. Submit YouTube URL
6. Job appears in queue
7. Progress updates appear in real-time
8. Note is created
9. Navigate to /notes
10. Click note to view content
11. Edit note content
12. Save changes
13. Logout

**Scenario 2: Job Processing**
1. Submit video URL
2. Python CLI is spawned
3. Progress updates are emitted via WebSocket
4. Markdown files are generated
5. Files are read and parsed
6. Note is created in database
7. Job status is updated to COMPLETED
8. User receives completion notification

**Scenario 3: Error Handling**
1. Submit invalid YouTube URL → Validation error
2. Submit URL with Python CLI failure → Job marked as FAILED
3. Retry failed job → Job re-queued
4. API returns 401 → User logged out
5. WebSocket disconnects → Auto-reconnect

### 9. API Integration Verification
Create integration tests that verify:
- Auth endpoints work
- Video CRUD operations work
- Note CRUD operations work
- Job queue processes videos
- WebSocket events are emitted
- Database transactions are atomic
- Error handling is consistent

### 10. Module Integration
Ensure all modules are properly connected:

```typescript
// backend/src/app.module.ts
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    AuthModule,
    UsersModule,
    VideosModule,
    NotesModule,
    JobsModule,
    PythonCliModule,
  ],
})
export class AppModule {}
```

### 11. CORS Configuration
```typescript
// backend/src/main.ts
app.enableCors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true,
});
```

### 12. Documentation
Create `webapp/README.md`:
```markdown
# YouTube Study Buddy Web App

## Prerequisites
- Docker and Docker Compose
- Node.js 20+
- Python 3.13+ with UV (for CLI integration)

## Setup
1. Clone repository
2. Run `./scripts/setup.sh`
3. Update `.env` files with your credentials
4. Run `docker-compose up`

## Development
- Backend: http://localhost:3000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Testing
- Backend: `cd backend && npm test`
- Frontend: `cd frontend && npm test`
- E2E: `cd backend && npm run test:e2e`

## Architecture
See PRODUCT_SPEC.md for detailed architecture.
```

## Success Criteria
- ✅ Docker Compose starts all services
- ✅ Database migrations run successfully
- ✅ Backend health check passes
- ✅ Frontend loads at localhost:5173
- ✅ API endpoints are accessible from frontend
- ✅ WebSocket connection established
- ✅ Full user journey works end-to-end
- ✅ Video submission creates job
- ✅ Job processing completes successfully
- ✅ Real-time updates work via WebSocket
- ✅ Notes are created and viewable
- ✅ All CRUD operations work
- ✅ Error handling works correctly

## Testing Commands
```bash
# Start all services
docker-compose up

# Run backend tests
cd backend && npm test

# Run E2E tests
cd backend && npm run test:e2e

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Reset database
cd backend && npx prisma migrate reset
```

## Integration Points Verification
1. **Auth Module** → Used by all protected endpoints
2. **Python CLI Module** → Called by Jobs module
3. **Jobs Module** → Emits WebSocket events
4. **Videos Module** → Creates jobs, uses Python CLI
5. **Notes Module** → Receives data from job processing
6. **Frontend Auth** → Calls backend auth endpoints
7. **Frontend Videos** → Subscribes to WebSocket events
8. **Frontend Notes** → Fetches and updates notes

## Deployment Considerations (Future)
- Use production-ready database (AWS RDS, etc.)
- Use managed Redis (AWS ElastiCache, etc.)
- Set up proper secrets management
- Configure CDN for static assets
- Set up SSL certificates
- Configure auto-scaling
- Set up monitoring and logging
- Configure backup and disaster recovery

## Notes
- Keep Docker volumes persistent for development
- Use health checks to ensure services are ready
- Implement graceful shutdown for all services
- Add database seeding for development
- Consider using Kubernetes for production
- Implement proper logging (Winston, Pino)
- Add APM for performance monitoring
- Set up CI/CD pipeline (GitHub Actions)
