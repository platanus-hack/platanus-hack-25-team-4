# API Endpoints

## Auth Endpoints

### POST /api/auth/signup

**Signup with password**

Request:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe"
}
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "profile": null,
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

### POST /api/auth/login

**Login with password**

Request:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": null,
    "profile": null,
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

### POST /api/auth/magic-link/request

**Request magic link for login/signup**

Request:

```json
{
  "email": "user@example.com",
  "firstName": "John"
}
```

Response:

```json
{
  "success": true,
  "message": "Magic link sent to user@example.com"
}
```

Dev mode: Link logged to console as `token=...`

---

### GET /api/auth/verify-magic-link?token=TOKEN

**Verify magic link token and authenticate**

Request:

```
GET /api/auth/verify-magic-link?token=abc123def456
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": null,
    "lastName": null,
    "profile": {
      "interests": []
    },
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

## Health Endpoint

### GET /api/health

**Check API health**

Response:

```json
{
  "status": "ok"
}
```

---

## Circles Endpoints

All circles endpoints require authentication (`Authorization: Bearer <token>`).

### POST /api/circles

**Create a new circle**

Request:

```json
{
  "objectiveText": "Looking for tennis partners",
  "centerLat": 40.7128,
  "centerLon": -74.0060,
  "radiusMeters": 5000,
  "startAt": "2025-11-22T10:00:00Z",
  "expiresAt": "2025-11-22T18:00:00Z"
}
```

Response (201 Created):

```json
{
  "circle": {
    "id": "uuid",
    "userId": "uuid",
    "objective": "Looking for tennis partners",
    "centerLat": 40.7128,
    "centerLon": -74.0060,
    "radiusMeters": 5000,
    "startAt": "2025-11-22T10:00:00Z",
    "expiresAt": "2025-11-22T18:00:00Z",
    "status": "active",
    "createdAt": "2025-11-22T09:00:00Z",
    "updatedAt": "2025-11-22T09:00:00Z"
  }
}
```

---

### GET /api/circles/me

**List all circles for the authenticated user**

Response:

```json
{
  "circles": [
    {
      "id": "uuid",
      "userId": "uuid",
      "objective": "Looking for tennis partners",
      "centerLat": 40.7128,
      "centerLon": -74.0060,
      "radiusMeters": 5000,
      "startAt": "2025-11-22T10:00:00Z",
      "expiresAt": "2025-11-22T18:00:00Z",
      "status": "active",
      "createdAt": "2025-11-22T09:00:00Z",
      "updatedAt": "2025-11-22T09:00:00Z"
    }
  ]
}
```

---

### GET /api/circles/:id

**Get a specific circle by ID**

URL Parameters:
- `id` - Circle UUID

Response:

```json
{
  "circle": {
    "id": "uuid",
    "userId": "uuid",
    "objective": "Looking for tennis partners",
    "centerLat": 40.7128,
    "centerLon": -74.0060,
    "radiusMeters": 5000,
    "startAt": "2025-11-22T10:00:00Z",
    "expiresAt": "2025-11-22T18:00:00Z",
    "status": "active",
    "createdAt": "2025-11-22T09:00:00Z",
    "updatedAt": "2025-11-22T09:00:00Z"
  }
}
```

---

### PATCH /api/circles/:id

**Update a circle (partial update)**

URL Parameters:
- `id` - Circle UUID

Request (all fields optional):

```json
{
  "objectiveText": "Updated: Looking for basketball players",
  "centerLat": 40.7580,
  "centerLon": -73.9855,
  "radiusMeters": 3000,
  "startAt": "2025-11-23T10:00:00Z",
  "expiresAt": "2025-11-23T18:00:00Z",
  "status": "paused"
}
```

Response:

```json
{
  "circle": {
    "id": "uuid",
    "userId": "uuid",
    "objective": "Updated: Looking for basketball players",
    "centerLat": 40.7580,
    "centerLon": -73.9855,
    "radiusMeters": 3000,
    "startAt": "2025-11-23T10:00:00Z",
    "expiresAt": "2025-11-23T18:00:00Z",
    "status": "paused",
    "createdAt": "2025-11-22T09:00:00Z",
    "updatedAt": "2025-11-22T12:00:00Z"
  }
}
```

Valid status values: `"active"`, `"paused"`, `"expired"`

---

### DELETE /api/circles/:id

**Delete a circle**

URL Parameters:
- `id` - Circle UUID

Response: 204 No Content

---

## Users & Profile Endpoints

All user/profile endpoints require authentication (`Authorization: Bearer <token>`).

### GET /api/users/me/profile

**Get the authenticated user's profile**

Response:

```json
{
  "profile": {
    "interests": ["tennis", "hiking", "photography"],
    "socialStyle": "extroverted and friendly",
    "boundaries": ["no late night meetups", "public places only"],
    "availability": "weekends and evenings"
  }
}
```

---

### PUT /api/users/me/profile

**Update the authenticated user's profile**

Request:

```json
{
  "interests": ["tennis", "hiking", "photography"],
  "socialStyle": "extroverted and friendly",
  "boundaries": ["no late night meetups", "public places only"],
  "availability": "weekends and evenings"
}
```

All fields are optional except `interests` (defaults to empty array).

Response:

```json
{
  "profile": {
    "interests": ["tennis", "hiking", "photography"],
    "socialStyle": "extroverted and friendly",
    "boundaries": ["no late night meetups", "public places only"],
    "availability": "weekends and evenings"
  }
}
```

---

## Error Responses

All endpoints return errors as:

```json
{
  "error": "Error message"
}
```

HTTP Status Codes:

- `200` - Success
- `201` - Created
- `400` - Bad request
- `401` - Unauthorized/Invalid credentials
- `409` - Conflict (email already exists)
- `500` - Internal server error

---

## Authentication

All endpoints (except `/health` and auth endpoints) require:

```
Authorization: Bearer <JWT_TOKEN>
```

Token obtained from signup/login/verify-magic-link endpoints.
Token expires in 12 hours.

---

## Comparison with Feature Plan

This section compares the implemented API with the original plan from `docs/feature_plan.md`.

### ✅ Implemented & Aligned

#### Authentication
- **Planned**: `POST /auth/login`, `POST /auth/signup`
- **Implemented**: `POST /api/auth/login`, `POST /api/auth/signup`
- **Similarities**: Both endpoints exist with email/password authentication
- **Differences**:
  - ✨ **Added**: Magic link authentication (`POST /api/auth/magic-link/request`, `GET /api/auth/verify-magic-link`) - not in original plan
  - Planned signup included `emailConfirmacion` and `passwordConfirmacion` fields - not implemented in actual API
  - All endpoints use `/api` prefix in implementation
  - Response includes full user object with profile in implementation

#### Circles
- **Planned**: `GET /circulos`, `POST /circulos`, `PUT /circulos/{id}`, `DELETE /circulos/{id}`
- **Implemented**: `GET /api/circles/me`, `POST /api/circles`, `PATCH /api/circles/:id`, `DELETE /api/circles/:id`
- **Similarities**: Full CRUD operations supported
- **Differences**:
  - Field names: `objetivo` (planned) → `objectiveText` (implemented)
  - Field names: `radioKm` (planned) → `radiusMeters` (implemented)
  - Field names: `expiraEn` (planned) → `expiresAt` (implemented)
  - ✨ **Added**: `GET /api/circles/:id` - get single circle by ID
  - ✨ **Added**: `startAt` field - not in original plan
  - ✨ **Added**: `status` field with enum values (active/paused/expired)
  - Update uses `PATCH` (partial) instead of `PUT` (full replace)
  - Planned `descripcion` field not implemented
  - Planned `ubicacion` object not implemented (uses flat `centerLat`/`centerLon` instead)
  - Language: Spanish route names (planned) → English route names (implemented)

#### Profile
- **Planned**: `GET /me`, `PUT /me`
- **Implemented**: `GET /api/users/me/profile`, `PUT /api/users/me/profile`
- **Similarities**: Both GET and PUT operations for user profile
- **Differences**:
  - Route path: `/me` (planned) → `/api/users/me/profile` (implemented)
  - Planned fields: `nombre`, `bio`, `ubicacion` (lat/lng/ciudad), `avatarUrl`
  - Implemented fields: `interests` (array), `socialStyle`, `boundaries` (array), `availability`
  - **Completely different data model**: Planned was personal info focused, implemented is social matching focused

### ⏳ Planned but Not Yet Implemented

#### Matches Endpoints
- `GET /matches/mios` - Get people who match my circles
- `GET /matches/soy-match` - Get circles I match with
- **Status**: Not implemented in backend yet

#### Interactions Endpoints
- `POST /matches/{id}/aceptar` - Accept a match to enable chat
- **Status**: Not implemented in backend yet

#### Chats Endpoints
- `GET /chats` - List all chat conversations
- `GET /chats/{id}/mensajes` - Get messages for a specific chat
- `POST /chats/{id}/mensajes` - Send a message in a chat
- WebSocket/polling for real-time updates
- **Status**: Not implemented in backend yet

### ✨ Implemented but Not in Original Plan

- **Health endpoint**: `GET /api/health` - API health check
- **Magic link authentication**: Complete passwordless flow with token generation and verification
- **Individual circle retrieval**: `GET /api/circles/:id`
- **Circle status management**: Status field with active/paused/expired states

### 🔑 Key Architectural Differences

1. **Language**: Original plan used Spanish naming (`circulos`, `matches`, `objetivo`), implementation uses English
2. **Prefix**: All implemented routes use `/api` prefix
3. **Authentication**: Implementation added magic link as alternative to password auth
4. **Profile model**: Completely redesigned to focus on social matching attributes instead of basic user info
5. **Location handling**: Planned nested object (`ubicacion: { lat, lng, ciudad }`), implemented uses flat fields (`centerLat`, `centerLon`)
6. **Update operations**: Implementation uses `PATCH` for partial updates instead of `PUT`

### 📋 Summary

**Completion Status**:
- ✅ Auth: 100% complete (+ bonus magic link feature)
- ✅ Circles: 100% complete (enhanced with status management)
- ✅ Profile: 100% complete (but with different data model)
- ⏳ Matches: 0% (not started)
- ⏳ Interactions: 0% (not started)
- ⏳ Chats: 0% (not started)

**Overall Progress**: ~40% of planned features implemented
