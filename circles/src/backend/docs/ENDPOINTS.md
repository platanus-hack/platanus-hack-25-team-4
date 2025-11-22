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
