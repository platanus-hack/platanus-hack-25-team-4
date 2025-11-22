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
    "interests": ["tennis", "music"]
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
    "interests": ["tennis", "music"]
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
  "interests": ["tennis", "hiking"],
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

Response:

```json
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

Response: Circle object

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
