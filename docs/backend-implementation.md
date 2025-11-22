# Active Circles – Backend Implementation Plan (MVP)

This plan covers only the backend for the MVP described in `DESIGN.md`.  
Backend code lives under `circles/src/backend`.  
Assumes the stack from section 6.4: Express.js + TypeScript, PostgreSQL (+ PostGIS), Prisma, Passport.js, Zod, Swagger/OpenAPI.

TypeScript requirements:

- Use **strict** mode and fail on any type errors.
- Do **not** use `any` or type assertions / casting (`as`, `<Type>`).
- Avoid `// @ts-ignore` and similar escapes except for rare, well‑documented interop.
- Keep code readable and maintainable: encapsulate domain logic into services and utilities; keep route handlers and controllers thin.

Current local scripts (from `circles/src/backend`, after `npm install`):

- `npm run dev` – start the API in watch mode.
- `npm run typecheck` – run `tsc --noEmit` (via `tsconfig.test.json`) to ensure zero TS errors.
- `npm run build` – emit compiled output to `dist`.
- `npm test` – Vitest suite for services.

---

## 0. Foundations & Project Setup

- [ ] Initialize backend project (Node.js + TypeScript, Express)
- [ ] Configure `tsconfig`, ESLint/Prettier, scripts (`dev`, `build`, `start`)
- [ ] Set up environment config (`NODE_ENV`, DB URLs, JWT secrets, thresholds, etc.)
- [ ] Add core deps: `express`, `zod`, `passport`, `passport-jwt`, `jsonwebtoken`, `bcrypt`, `prisma`, `@prisma/client`, `swagger-ui-express` (or equivalent)
- [ ] Implement centralized error handling middleware (HTTP errors, validation errors)
- [ ] Implement request logging (basic logger + request IDs)
- [ ] Set up OpenAPI/Swagger docs route and basic API skeleton

---

## 1. Database & Persistence Layer

- [ ] Provision PostgreSQL instance and enable PostGIS extension
- [ ] Initialize Prisma and connect to Postgres  
  - Current schema at `circles/src/backend/prisma/schema.prisma` defines `User`, `AgentPersona`, `Circle` (no embeddings stored), `Match`, `Chat`, `Message`, enums for statuses/types.
- [ ] Add indexes & constraints:
  - [ ] FKs between all related tables
  - [ ] Unique constraints (e.g., user email, one `AgentPersona` per user)
  - [ ] Geo index for circle locations (PostGIS)
  - [ ] Indexes for match lookups (by user, by status, by created_at)
- [ ] Implement Prisma migrations and migration workflow
- [ ] Create seed script for dev data (users, circles, test matches)

---

## 2. Auth & User / Profile Service

### 2.1 Authentication & Authorization

- [ ] Define `User` model fields from design (`first_name`, `last_name`, `age`, `avatar_url`, `locale`, `preferences`, etc.)
- [ ] Implement sign-up endpoint (email + code/passwordless or simple password for MVP)
- [ ] Implement login endpoint (if using passwords) or magic-link/OTP flow
- [ ] Set up Passport.js JWT strategy:
  - [ ] Sign JWT on login/sign-up
  - [ ] Middleware to protect authenticated routes
- [ ] Implement token refresh / logout strategy (if needed for MVP)
- [ ] Add basic rate-limiting on auth endpoints

### 2.2 User Profile & Preferences

- [ ] Implement endpoints to fetch/update profile: `GET /me`, `PATCH /me`
- [ ] Implement endpoints for preferences:
  - [ ] Social comfort level, boundaries, availability windows
  - [ ] Toggle permissions (e.g., background location, notifications)
- [ ] Ensure profile exposure API returns only fields safe for front-end and agent services

---

## 3. Onboarding & Agent Persona Service (Later Phase)

> Note: This section is planned but **not** part of the initial implementation pass. It can be tackled after core auth, circles, matching, chat, and notifications are working.

### 3.1 Onboarding Questionnaire

- [ ] Design onboarding payload and Zod schemas
- [ ] Implement RESTful onboarding/profile endpoints (e.g. `POST /users/me/profile`) to accept interests, hobbies, social style, boundaries
- [ ] Store onboarding data in appropriate tables (`User.preferences`, `Profile`, or separate table)

### 3.2 Agent Persona Modeling

- [ ] Define `AgentPersona` storage structure (traits, interests, safety rules, embeddings)
- [ ] Add pipeline to:
  - [ ] Ingest onboarding data (and later external data)
  - [ ] Produce structured traits and interests
  - [ ] Compute embeddings for interests / topics
- [ ] Implement API/internal service:
  - [ ] `AgentPersonaService.buildOrUpdate(userId)` – rebuild persona after onboarding/profile changes
  - [ ] Persist `safety_rules` and relevant metadata

### 3.3 Simulation & Explanation APIs

- [ ] Implement internal service methods (can be HTTP or in-process):
  - [ ] `simulateInteraction(agentA, agentB, context)` → `worth_it_score`, safety flags, reasoning summary
  - [ ] `suggestOpeningMessage(matchContext)` → intro and topics
  - [ ] `explainMatch(matchContext)` → user-facing explanation obeying privacy rules
- [ ] For MVP, plug in a simple implementation:
  - [ ] Either call an LLM API or stub with deterministic rules + templates
  - [ ] Enforce redaction of sensitive data in explanations

---

## 4. Circle Service

### 4.1 CRUD & Lifecycle

- [ ] Implement `POST /circles` with Zod validation:
  - [ ] `objective_text`, `radius_m`, `start_at`, `expires_at`, optional “move with user” flag
- [ ] On create:
  - [ ] Store circle record in `circle_db` and geo index (no embeddings stored currently)
- [ ] Implement:
  - [ ] `GET /circles/me` – list user’s circles
  - [ ] `GET /circles/:id` – fetch one circle
  - [ ] `PATCH /circles/:id` – update objective/radius/duration/status (pause/resume)
  - [ ] `DELETE /circles/:id` – soft delete or mark expired
- [ ] Implement lifecycle job:
  - [ ] Periodic task/cron to mark circles expired when `expires_at` passes
  - [ ] Ensure paused circles don’t participate in matching

### 4.2 Validation & Limits

- [ ] Enforce per-user limits (max active circles)
- [ ] Validate radii and durations against allowed ranges

---

## 5. Location & Geo Service

- [ ] Define API for location updates: `POST /location` or `POST /circles/:id/location`
- [ ] Authenticate user and associate update with correct circle(s)
- [ ] Write locations into:
  - [ ] `geo_index` (PostGIS) for circle centers
  - [ ] Optional `LocationUpdate` table for history/debugging
- [ ] Implement function to update all active circles for user to latest location (for “moving” circles)
- [ ] Implement geo query:
  - [ ] Find overlapping circle pairs using `ST_DWithin` or equivalent:
    - `distance(centerA, centerB) ≤ radiusA + radiusB`
- [ ] Emit “collision events” (in process or via queue) to Matching Engine when overlaps are detected

---

## 6. Matching Engine

### 6.1 Candidate Retrieval

- [ ] Implement collision listener that receives candidate circle pairs
- [ ] Fetch circles + associated users and personas
- [ ] Filter by:
  - [ ] Both circles active
  - [ ] Users not blocked or already matched/declined recently

### 6.2 Semantic Matching

- [ ] (Future) implement embedding retrieval when semantic matching is introduced
- [ ] Implement classification logic once similarity signals are available:
  - [ ] **Match candidate**: `objective_similarity ≥ HARD_MATCH_THRESHOLD`
  - [ ] **Soft match candidate**: `objective_similarity < HARD_MATCH_THRESHOLD` and `max(interest_similarity_A, interest_similarity_B) ≥ SOFT_MATCH_THRESHOLD`
  - [ ] Configurable thresholds via env/Config

### 6.3 Simulation & Decision

- [ ] For each candidate pair:
  - [ ] Call `simulateInteraction` with personas and context
  - [ ] Receive `worth_it_score`, safety flags, reasoning summary
- [ ] Implement decision rules:
  - [ ] **Match (auto chat)** if candidate type `match` and `worth_it_score ≥ MATCH_OPEN_CHAT_THRESHOLD` and no safety flags
  - [ ] **Soft match (opt-in)** if candidate type `soft match` and `worth_it_score ≥ SOFT_MATCH_NOTIFY_THRESHOLD` and no safety flags
  - [ ] Otherwise: no match (log for tuning)
- [ ] Persist `Match` record:
  - [ ] `type`, `worth_it_score`, `status` (`pending_accept`, `active`, `declined`, `expired`), `explanation_summary`
  - [ ] Link circles and users

### 6.4 Side Effects

- [ ] For `match`:
  - [ ] Create `Chat` record and initial system/agent messages if desired
  - [ ] Generate agent explanation via `explainMatch`
  - [ ] Trigger notification(s) and in-app event
- [ ] For `soft match`:
  - [ ] Create match in `pending_accept` for non-objective user
  - [ ] Generate explanation card content
  - [ ] Trigger notification for opt-in
- [ ] Implement API endpoints:
  - [ ] `GET /matches` – list matches for user
  - [ ] `POST /matches/:id/accept` – accept soft match (creates chat)
  - [ ] `POST /matches/:id/decline` – decline match/soft match

---

## 7. Chat Service (REST + WebSockets)

- [ ] Define `Chat` and `Message` schema fields (including `moderation_flags`)
- [ ] Implement REST endpoints:
  - [ ] `GET /chats` – list user’s chats
  - [ ] `GET /chats/:id/messages` – paginated messages
- [ ] Set up WebSocket layer (e.g., Socket.IO):
  - [ ] Authenticated connection using JWT
  - [ ] Join rooms per `chat_id`
  - [ ] Event for sending messages, receiving new messages
- [ ] Message creation flow:
  - [ ] Validate payload (Zod)
  - [ ] Persist message to DB
  - [ ] Run basic moderation hook (placeholder for now)
  - [ ] Broadcast to recipients via WebSocket
- [ ] Implement read receipts / message status (optional MVP)
- [ ] Implement simple agent suggestions:
  - [ ] Endpoint or WS event to get suggested replies/topics for given chat context

---

## 8. Notification Service

- [ ] Design `Notification` model (type, payload, read status, user_id)
- [ ] Implement internal service to:
  - [ ] Create notification records when matches/soft matches are created, chat messages arrive, etc.
  - [ ] Mark notifications as read
- [ ] Integrate push provider (APNS/FCM) or stub:
  - [ ] Abstract interface for sending push
  - [ ] For hackathon MVP, at least log “would send push” + rely on in-app notifications
- [ ] Expose minimal API:
  - [ ] `GET /notifications` – list for user
  - [ ] `POST /notifications/:id/read` – mark as read

---

## 9. Data Ingestion (Stretch / Post-MVP)

- [ ] Define connectors for external social networks / chat platforms
- [ ] Implement OAuth flows (if needed) and store access tokens securely
- [ ] Normalize and store imported content in a `raw_profile` area
- [ ] Extend Agent Persona builder to:
  - [ ] Extract interests/topics from imported data
  - [ ] Update embeddings and traits
- [ ] Ensure strict adherence to privacy rules (only aggregate/derived data used for explanations)

---

## 10. Privacy, Safety & Compliance

- [ ] Implement consent flags for each data source and use of data
- [ ] Implement account deletion endpoint (delete or anonymize data)
- [ ] Implement data export endpoint (basic JSON dump for MVP)
- [ ] Enforce explanation rules:
  - [ ] No raw imported content or external handles
  - [ ] Only high-level patterns in match explanations
- [ ] Age gating:
  - [ ] Store age + verification status
  - [ ] Enforce 18+ or other rules as decided
- [ ] Add basic moderation:
  - [ ] Flag messages containing disallowed content (simple keyword/regex or external API)
  - [ ] Block matching between users with repeated flags (MVP heuristic)
- [ ] Implement rate limiting:
  - [ ] Limit match creation per user/day
  - [ ] Limit messages per minute to avoid spam

---

## 11. Observability, Testing & Ops

- [ ] Add structured logging (including IDs for users, circles, matches)
- [ ] Expose basic health checks: `/health`, `/ready`
- [ ] Add metrics hooks (if using Prometheus/Grafana or similar)
- [ ] Testing:
  - [ ] Unit tests for services (matching logic, similarity thresholds, persona builder)
  - [ ] Integration tests for key flows:
    - [ ] Onboarding → Persona → Circle creation
    - [ ] Location update → Collision → Match creation
    - [ ] Soft match accept → Chat creation → Messaging
- [ ] Create local dev environment:
  - [ ] Docker compose for Postgres (+ PostGIS) and backend
  - [ ] Seed data scripts
- [ ] Prepare deployment configuration (env vars, build pipeline, run command)
