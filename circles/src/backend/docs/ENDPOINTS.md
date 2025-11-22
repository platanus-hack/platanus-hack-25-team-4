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

## User Endpoints

### GET /api/users/me

**Get current authenticated user**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "profile": {
    "interests": [
      { "title": "tennis", "description": "Beginner looking for practice" },
      { "title": "music", "description": "Enjoy live concerts" }
    ]
  },
  "centerLat": 40.7128,
  "centerLon": -74.0060,
  "createdAt": "2025-11-22T...",
  "updatedAt": "2025-11-22T..."
}
```

---

### GET /api/users/:id

**Get user by ID (public information)**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "profile": {
    "interests": [
      { "title": "tennis", "description": "Beginner looking for practice" },
      { "title": "music", "description": "Enjoy live concerts" }
    ]
  },
  "centerLat": 40.7128,
  "centerLon": -74.0060,
  "createdAt": "2025-11-22T...",
  "updatedAt": "2025-11-22T..."
}
```

---

### PATCH /api/users/me

**Update current user (firstName, lastName)**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Request:

```json
{
  "firstName": "Jane",
  "lastName": "Smith"
}
```

Response: Updated user object

---

### PATCH /api/users/me/position

**Update user's current position (latitude and longitude)**

This endpoint updates the center position for all user circles.

Requires: `Authorization: Bearer <JWT_TOKEN>`

Request:

```json
{
  "centerLat": 40.7128,
  "centerLon": -74.0060
}
```

Validation:
- `centerLat`: number between -90 and 90
- `centerLon`: number between -180 and 180

Response:

```json
{
  "message": "Position updated successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "profile": {
      "interests": ["tennis"]
    },
    "centerLat": 40.7128,
    "centerLon": -74.0060,
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

### DELETE /api/users/me

**Delete current user account**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response: `204 No Content`

---

### GET /api/users/me/profile

**Get current user's profile (deprecated, use /users/me)**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "profile": {
    "interests": ["tennis", "music"],
    "socialStyle": "outgoing",
    "boundaries": ["no spam"],
    "availability": "weekends"
  }
}
```

---

### PUT /api/users/me/profile

**Update current user's profile (deprecated, use /users/me)**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Request:

```json
{
  "bio": "New to the city, looking to meet people",
  "interests": [
    { "title": "tennis", "description": "Beginner" },
    { "title": "hiking", "description": "Trails on weekends" }
  ],
  "profileCompleted": false,
  "socialStyle": "outgoing",
  "boundaries": ["no spam"],
  "availability": "weekends"
}
```

Response: Updated profile object

---

## Circle Endpoints

### POST /api/circles

**Create a new circle**

Requires: `Authorization: Bearer <JWT_TOKEN>`

The circle will be centered at the user's current position (centerLat/centerLon).
Update user position with PATCH /api/users/me/position before creating circles.

Request:

```json
{
  "objectiveText": "Play tennis",
  "radiusMeters": 500,
  "startAt": "2025-11-23T10:00:00Z",
  "expiresAt": "2025-11-24T10:00:00Z"
}
```

Response (201 Created):

```json
{
  "circle": {
    "id": "uuid",
    "userId": "uuid",
    "objective": "Play tennis",
    "radiusMeters": 500,
    "startAt": "2025-11-23T10:00:00Z",
    "expiresAt": "2025-11-24T10:00:00Z",
    "status": "active",
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

### GET /api/circles/me

**List all circles for current user**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "circles": [
    {
      "id": "uuid",
      "userId": "uuid",
      "objective": "Play tennis",
      "radiusMeters": 500,
      "startAt": "2025-11-23T10:00:00Z",
      "expiresAt": "2025-11-24T10:00:00Z",
      "status": "active",
      "createdAt": "2025-11-22T...",
      "updatedAt": "2025-11-22T..."
    }
  ]
}
```

---

### GET /api/circles/:id

**Get circle by ID**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "circle": {
    "id": "uuid",
    "userId": "uuid",
    "objective": "Play tennis",
    "radiusMeters": 500,
    "startAt": "2025-11-23T10:00:00Z",
    "expiresAt": "2025-11-24T10:00:00Z",
    "status": "active",
    "createdAt": "2025-11-22T...",
    "updatedAt": "2025-11-22T..."
  }
}
```

---

### PATCH /api/circles/:id

**Update circle**

Requires: `Authorization: Bearer <JWT_TOKEN>`
Only circle owner can update

Request:

```json
{
  "objectiveText": "Play tennis tournament",
  "radiusMeters": 1000,
  "status": "paused"
}
```

Response: Updated circle object

---

### DELETE /api/circles/:id

**Delete circle**

Requires: `Authorization: Bearer <JWT_TOKEN>`
Only circle owner can delete

Response: `204 No Content`

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

## Chat Endpoints

All chat endpoints require authentication (`Authorization: Bearer <JWT_TOKEN>`).

### GET /api/chats

List all chats for the authenticated user with participant details and latest message preview.

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "primaryUserId": "uuid",
      "secondaryUserId": "uuid",
      "matchId": null,
      "createdAt": "2025-11-22T10:00:00Z",
      "primaryUser": {
        "id": "uuid",
        "email": "a@example.com",
        "firstName": "Alice",
        "lastName": "A"
      },
      "secondaryUser": {
        "id": "uuid",
        "email": "b@example.com",
        "firstName": "Bob",
        "lastName": "B"
      },
      "latestMessage": {
        "id": "uuid",
        "chatId": "uuid",
        "senderUserId": "uuid",
        "receiverId": "uuid",
        "content": "Hey!",
        "moderationFlags": null,
        "createdAt": "2025-11-22T10:05:00Z"
      }
    }
  ],
  "count": 1
}
```

---

### POST /api/chats

Create a new chat between two users. The authenticated user must be one of the participants.

Request:

```json
{
  "primaryUserId": "uuid",
  "secondaryUserId": "uuid",
  "matchId": "uuid"
}
```

Response (201 Created):

```json
{
  "id": "uuid",
  "primaryUserId": "uuid",
  "secondaryUserId": "uuid",
  "matchId": "uuid",
  "createdAt": "2025-11-22T10:00:00Z"
}
```

---

### GET /api/chats/:chatId

Get a specific chat with participant details.

Response:

```json
{
  "id": "uuid",
  "primaryUserId": "uuid",
  "secondaryUserId": "uuid",
  "matchId": null,
  "createdAt": "2025-11-22T10:00:00Z",
  "primaryUser": {
    "id": "uuid",
    "email": "a@example.com",
    "firstName": "Alice",
    "lastName": "A"
  },
  "secondaryUser": {
    "id": "uuid",
    "email": "b@example.com",
    "firstName": "Bob",
    "lastName": "B"
  }
}
```

---

### DELETE /api/chats/:chatId

Delete a chat. Only participants can delete.

Response: `204 No Content`

---

### GET /api/chats/:chatId/messages

List messages in a chat (paginated).

Query parameters:
- `limit` (optional, default 50, max 100)
- `offset` (optional, default 0)

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "chatId": "uuid",
      "senderUserId": "uuid",
      "receiverId": "uuid",
      "content": "Hello!",
      "moderationFlags": null,
      "createdAt": "2025-11-22T10:01:00Z",
      "chat": { "id": "uuid" },
      "sender": { "id": "uuid", "email": "a@example.com", "firstName": "Alice", "lastName": "A" },
      "receiver": { "id": "uuid", "email": "b@example.com", "firstName": "Bob", "lastName": "B" }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### POST /api/chats/:chatId/messages

Create a new message in a chat. The authenticated user becomes the sender.

Request:

```json
{
  "content": "Hello!",
  "receiverId": "uuid"
}
```

Response (201 Created):

```json
{
  "id": "uuid",
  "chatId": "uuid",
  "senderUserId": "uuid",
  "receiverId": "uuid",
  "content": "Hello!",
  "moderationFlags": null,
  "createdAt": "2025-11-22T10:01:00Z"
}
```

---

### GET /api/chats/:chatId/messages/:messageId

Get a specific message with sender/receiver details.

Response:

```json
{
  "id": "uuid",
  "chatId": "uuid",
  "senderUserId": "uuid",
  "receiverId": "uuid",
  "content": "Hello!",
  "moderationFlags": null,
  "createdAt": "2025-11-22T10:01:00Z",
  "chat": { "id": "uuid" },
  "sender": { "id": "uuid", "email": "a@example.com", "firstName": "Alice", "lastName": "A" },
  "receiver": { "id": "uuid", "email": "b@example.com", "firstName": "Bob", "lastName": "B" }
}
```

---

### DELETE /api/chats/:chatId/messages/:messageId

Delete a message. Only the sender can delete.

Response: `204 No Content`

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

#### Chats
- **Implemented**:
  - `GET /api/chats` – list user chats
  - `POST /api/chats` – create chat
  - `GET /api/chats/:chatId` – get chat details
  - `DELETE /api/chats/:chatId` – delete chat
- **Messages (implemented)**:
  - `GET /api/chats/:chatId/messages`
  - `POST /api/chats/:chatId/messages`
  - `GET /api/chats/:chatId/messages/:messageId`
  - `DELETE /api/chats/:chatId/messages/:messageId`

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
- ✅ Chats: 100% complete (chat and messaging endpoints)

**Overall Progress**: ~60% of planned features implemented
