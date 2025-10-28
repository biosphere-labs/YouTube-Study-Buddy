# Agent Task: Backend Authentication Module

## Branch: `feature/backend-auth`

## Objective
Set up the NestJS backend foundation with authentication, database schema, and user management.

## Tasks

### 1. NestJS Project Setup
- Initialize NestJS project in `webapp/backend/`
- Configure TypeScript, ESLint, Prettier
- Set up project structure (modules, controllers, services)
- Install core dependencies

### 2. Prisma Schema Setup
- Install Prisma and initialize
- Implement the complete database schema from PRODUCT_SPEC.md:
  - User model (with social auth fields)
  - Video model
  - Note model
  - ProcessingJob model with JobStatus enum
- Generate Prisma client
- Create initial migration

### 3. Authentication Module
- Install Passport.js and strategies:
  - `@nestjs/passport`
  - `passport-google-oauth20`
  - `passport-github2`
  - `passport-discord`
- Implement JWT strategy and guards
- Create AuthController with endpoints:
  - `POST /auth/google`
  - `POST /auth/github`
  - `POST /auth/discord`
  - `GET /auth/me`
  - `POST /auth/logout`
- Implement AuthService with:
  - Social login handlers
  - JWT token generation
  - User session management

### 4. User Module
- Create UsersModule, UsersController, UsersService
- Implement user CRUD operations
- Add user profile management
- Implement settings management (JSON field)

### 5. Guards and Middleware
- JwtAuthGuard for protected routes
- Request user decorator
- Auth middleware for request context

### 6. Environment Configuration
- Set up ConfigModule
- Create .env.example with:
  - DATABASE_URL
  - JWT_SECRET
  - GOOGLE_CLIENT_ID/SECRET
  - GITHUB_CLIENT_ID/SECRET
  - DISCORD_CLIENT_ID/SECRET

### 7. Docker Setup
- Create Dockerfile for backend
- PostgreSQL service configuration
- Health check endpoints

## Dependencies to Install
```bash
npm install @nestjs/common @nestjs/core @nestjs/platform-express
npm install @nestjs/passport passport passport-google-oauth20 passport-github2 passport-discord
npm install @nestjs/jwt passport-jwt
npm install @nestjs/config
npm install @prisma/client
npm install bcrypt
npm install class-validator class-transformer

npm install -D @nestjs/cli typescript @types/node
npm install -D @types/passport-jwt @types/passport-google-oauth20
npm install -D prisma
```

## Success Criteria
- ✅ NestJS server starts successfully
- ✅ Database migrations run without errors
- ✅ All auth endpoints respond correctly
- ✅ JWT tokens are generated and validated
- ✅ Users can be created via social login
- ✅ Protected routes reject unauthenticated requests
- ✅ `/auth/me` returns current user info

## API Endpoints to Implement
```
POST   /auth/google     - Google OAuth callback
POST   /auth/github     - GitHub OAuth callback
POST   /auth/discord    - Discord OAuth callback
GET    /auth/me         - Get current user
POST   /auth/logout     - Logout user
GET    /health          - Health check
```

## Database Schema (Prisma)
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
  videoId       String
  url           String
  title         String?
  transcript    String?  @db.Text
  processingJob ProcessingJob?
  notes         Note[]
  createdAt     DateTime @default(now())
}

model Note {
  id                String   @id @default(cuid())
  userId            String
  user              User     @relation(fields: [userId], references: [id])
  videoId           String?
  video             Video?   @relation(fields: [videoId], references: [id])
  title             String
  content           String   @db.Text
  subject           String?
  assessmentContent String?  @db.Text
  pdfUrl            String?
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt
}

model ProcessingJob {
  id            String   @id @default(cuid())
  videoId       String   @unique
  video         Video    @relation(fields: [videoId], references: [id])
  status        JobStatus
  progress      Int      @default(0)
  error         String?
  result        Json?
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
}

enum JobStatus {
  QUEUED
  PROCESSING
  COMPLETED
  FAILED
}
```

## Testing
- Write unit tests for AuthService
- Write e2e tests for auth endpoints
- Test database connection
- Test JWT token generation/validation

## Integration Points
- Exports AuthModule for use by other modules
- Provides JwtAuthGuard for protected routes
- Database schema ready for Videos, Notes, Jobs modules

## Notes
- Use bcrypt for any password hashing (if implementing email/password later)
- JWT tokens should include user ID and email
- Implement proper error handling for OAuth failures
- Add rate limiting on auth endpoints
- Keep secrets in environment variables
- Follow NestJS best practices for module organization
