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
