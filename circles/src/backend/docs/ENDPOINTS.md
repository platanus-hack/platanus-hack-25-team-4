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
  "objective": "Play tennis",
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
  "objective": "Play tennis tournament",
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

## Collision Detection Endpoints

Collision events represent geographic proximity matches between circles. When two circles overlap, a collision event is created and tracked through various states.

### GET /api/collisions

**List collision events for the authenticated user**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Query Parameters:

- `status` (optional): `detecting` | `stable` | `mission_created` | `matched` | `cooldown` | `expired`
- `limit` (optional, default 20, max 100)
- `offset` (optional, default 0)
- `startDate` (optional): ISO datetime to filter from
- `endDate` (optional): ISO datetime to filter until

Response:

```json
{
  "collisions": [
    {
      "id": "uuid",
      "circle1Id": "uuid",
      "circle2Id": "uuid",
      "user1Id": "uuid",
      "user2Id": "uuid",
      "distanceMeters": 250.5,
      "detectedAt": "2025-11-22T10:00:00Z",
      "firstSeenAt": "2025-11-22T10:00:00Z",
      "status": "stable",
      "missionId": "uuid",
      "matchId": "uuid",
      "processedAt": "2025-11-22T10:01:00Z",
      "createdAt": "2025-11-22T10:00:00Z",
      "updatedAt": "2025-11-22T10:01:00Z",
      "circle1": {
        "id": "uuid",
        "objective": "Play tennis",
        "radiusMeters": 500,
        "userId": "uuid"
      },
      "circle2": {
        "id": "uuid",
        "objective": "Play tennis",
        "radiusMeters": 500,
        "userId": "uuid"
      },
      "user1": {
        "id": "uuid",
        "email": "alice@example.com",
        "firstName": "Alice",
        "lastName": "A"
      },
      "user2": {
        "id": "uuid",
        "email": "bob@example.com",
        "firstName": "Bob",
        "lastName": "B"
      },
      "mission": {
        "id": "uuid",
        "status": "pending",
        "createdAt": "2025-11-22T10:00:00Z"
      }
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 20,
    "offset": 0,
    "hasMore": false
  }
}
```

---

### GET /api/collisions/:id

**Get a single collision event by ID**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "collision": {
    "id": "uuid",
    "circle1Id": "uuid",
    "circle2Id": "uuid",
    "user1Id": "uuid",
    "user2Id": "uuid",
    "distanceMeters": 250.5,
    "detectedAt": "2025-11-22T10:00:00Z",
    "firstSeenAt": "2025-11-22T10:00:00Z",
    "status": "stable",
    "missionId": "uuid",
    "matchId": "uuid",
    "processedAt": "2025-11-22T10:01:00Z",
    "createdAt": "2025-11-22T10:00:00Z",
    "updatedAt": "2025-11-22T10:01:00Z",
    "circle1": {
      "id": "uuid",
      "objective": "Play tennis",
      "radiusMeters": 500,
      "userId": "uuid"
    },
    "circle2": {
      "id": "uuid",
      "objective": "Play tennis",
      "radiusMeters": 500,
      "userId": "uuid"
    },
    "user1": {
      "id": "uuid",
      "email": "alice@example.com",
      "firstName": "Alice",
      "lastName": "A"
    },
    "user2": {
      "id": "uuid",
      "email": "bob@example.com",
      "firstName": "Bob",
      "lastName": "B"
    },
    "mission": {
      "id": "uuid",
      "status": "pending",
      "createdAt": "2025-11-22T10:00:00Z",
      "completedAt": null
    },
    "match": {
      "id": "uuid",
      "status": "pending_accept",
      "createdAt": "2025-11-22T10:00:00Z"
    }
  }
}
```

---

## Interview Mission Endpoints

Interview missions represent AI-mediated conversations between users when circles collide. The system conducts an interview to determine if the match should be promoted.

### GET /api/missions

**List interview missions for the authenticated user**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Query Parameters:

- `status` (optional): `pending` | `in_progress` | `completed` | `failed` | `cancelled`
- `limit` (optional, default 20, max 100)
- `offset` (optional, default 0)
- `startDate` (optional): ISO datetime to filter from
- `endDate` (optional): ISO datetime to filter until

Response:

```json
{
  "missions": [
    {
      "id": "uuid",
      "ownerUserId": "uuid",
      "visitorUserId": "uuid",
      "ownerCircleId": "uuid",
      "visitorCircleId": "uuid",
      "collisionEventId": "uuid",
      "status": "in_progress",
      "transcript": {
        "turns": []
      },
      "judgeDecision": null,
      "attemptNumber": 1,
      "createdAt": "2025-11-22T10:00:00Z",
      "startedAt": "2025-11-22T10:01:00Z",
      "completedAt": null,
      "failureReason": null,
      "ownerUser": {
        "id": "uuid",
        "email": "alice@example.com",
        "firstName": "Alice",
        "lastName": "A"
      },
      "visitorUser": {
        "id": "uuid",
        "email": "bob@example.com",
        "firstName": "Bob",
        "lastName": "B"
      },
      "collisionEvent": {
        "id": "uuid",
        "distanceMeters": 250.5,
        "firstSeenAt": "2025-11-22T10:00:00Z",
        "status": "mission_created",
        "circle1": {
          "id": "uuid",
          "objective": "Play tennis",
          "radiusMeters": 500
        },
        "circle2": {
          "id": "uuid",
          "objective": "Play tennis",
          "radiusMeters": 500
        }
      }
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 20,
    "offset": 0,
    "hasMore": false
  }
}
```

---

### GET /api/missions/:id

**Get a single mission by ID with full interview state**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "mission": {
    "id": "uuid",
    "ownerUserId": "uuid",
    "visitorUserId": "uuid",
    "ownerCircleId": "uuid",
    "visitorCircleId": "uuid",
    "collisionEventId": "uuid",
    "status": "completed",
    "transcript": {
      "turns": [
        {
          "speaker": "interviewer",
          "content": "Welcome to the circle interview..."
        },
        {
          "speaker": "visitor",
          "content": "Thank you for having me..."
        }
      ]
    },
    "judgeDecision": {
      "recommendation": "match",
      "confidence": 0.85,
      "summary": "Both users share similar interests in tennis and are geographically compatible."
    },
    "attemptNumber": 1,
    "createdAt": "2025-11-22T10:00:00Z",
    "startedAt": "2025-11-22T10:01:00Z",
    "completedAt": "2025-11-22T10:15:00Z",
    "failureReason": null,
    "ownerUser": {
      "id": "uuid",
      "email": "alice@example.com",
      "firstName": "Alice",
      "lastName": "A",
      "profile": {
        "interests": ["tennis"]
      }
    },
    "visitorUser": {
      "id": "uuid",
      "email": "bob@example.com",
      "firstName": "Bob",
      "lastName": "B",
      "profile": {
        "interests": ["tennis"]
      }
    },
    "collisionEvent": {
      "id": "uuid",
      "distanceMeters": 250.5,
      "firstSeenAt": "2025-11-22T10:00:00Z",
      "detectedAt": "2025-11-22T10:00:00Z",
      "status": "mission_created",
      "circle1": {
        "id": "uuid",
        "objective": "Play tennis",
        "radiusMeters": 500
      },
      "circle2": {
        "id": "uuid",
        "objective": "Play tennis",
        "radiusMeters": 500
      }
    }
  }
}
```

---

## Match Endpoints

Matches represent two users who have been identified as compatible based on collision detection and/or interview missions.

### GET /api/matches

**List matches for the authenticated user**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Query Parameters:

- `status` (optional): `pending_accept` | `active` | `declined` | `expired`
- `limit` (optional, default 20, max 100)
- `offset` (optional, default 0)

Response:

```json
{
  "matches": [
    {
      "id": "uuid",
      "primaryUserId": "uuid",
      "secondaryUserId": "uuid",
      "primaryCircleId": "uuid",
      "secondaryCircleId": "uuid",
      "type": "match",
      "worthItScore": 0.85,
      "status": "pending_accept",
      "explanationSummary": "Both users share similar interests in tennis and are geographically compatible.",
      "collisionEventId": "uuid",
      "createdAt": "2025-11-22T10:00:00Z",
      "updatedAt": "2025-11-22T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 3,
    "limit": 20,
    "offset": 0,
    "hasMore": false
  }
}
```

---

### GET /api/matches/:id

**Get a single match by ID**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "match": {
    "id": "uuid",
    "primaryUserId": "uuid",
    "secondaryUserId": "uuid",
    "primaryCircleId": "uuid",
    "secondaryCircleId": "uuid",
    "type": "match",
    "worthItScore": 0.85,
    "status": "pending_accept",
    "explanationSummary": "Both users share similar interests in tennis and are geographically compatible.",
    "collisionEventId": "uuid",
    "createdAt": "2025-11-22T10:00:00Z",
    "updatedAt": "2025-11-22T10:00:00Z"
  }
}
```

---

### POST /api/matches/:id/accept

**Accept a match and transition to active state**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "message": "Match accepted successfully",
  "match": {
    "id": "uuid",
    "primaryUserId": "uuid",
    "secondaryUserId": "uuid",
    "primaryCircleId": "uuid",
    "secondaryCircleId": "uuid",
    "type": "match",
    "worthItScore": 0.85,
    "status": "active",
    "explanationSummary": "Both users share similar interests in tennis and are geographically compatible.",
    "createdAt": "2025-11-22T10:00:00Z",
    "updatedAt": "2025-11-22T10:05:00Z"
  }
}
```

---

### POST /api/matches/:id/decline

**Decline a match and mark as declined**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Response:

```json
{
  "message": "Match declined successfully",
  "match": {
    "id": "uuid",
    "primaryUserId": "uuid",
    "secondaryUserId": "uuid",
    "primaryCircleId": "uuid",
    "secondaryCircleId": "uuid",
    "type": "match",
    "worthItScore": 0.85,
    "status": "declined",
    "explanationSummary": "Both users share similar interests in tennis and are geographically compatible.",
    "createdAt": "2025-11-22T10:00:00Z",
    "updatedAt": "2025-11-22T10:05:00Z"
  }
}
```

---

## Location Endpoints

The location endpoints are used for ingesting real-time user location updates to enable collision detection.

### POST /api/locations/update

**Update user location and trigger collision detection**

Requires: `Authorization: Bearer <JWT_TOKEN>`

Request:

```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "accuracy": 10.5,
  "timestamp": "2025-11-22T10:00:00Z"
}
```

Validation:

- `latitude`: number between -90 and 90
- `longitude`: number between -180 and 180
- `accuracy`: positive number (meters, optional)
- `timestamp`: ISO datetime (optional)

Response (202 Accepted - async processing):

```json
{
  "message": "Location update accepted and being processed",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy": 10.5
  }
}
```

Rate Limiting:

- Maximum 1 location update per 10 seconds per user
- Exceeding rate limit returns `429 Too Many Requests`

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
- `202` - Accepted (async processing)
- `204` - No Content
- `400` - Bad request
- `401` - Unauthorized/Invalid credentials
- `403` - Forbidden (not authorized for this resource)
- `404` - Not found
- `409` - Conflict (email already exists)
- `429` - Too many requests (rate limit exceeded)
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

## API Version

All endpoints are currently on version `v1` (included in internal routing but not explicitly versioned in URLs as of this release).

---

## Key Concepts

### Circles

Circles represent a user's geographic area of interest. They are centered at the user's current position (`centerLat`/`centerLon`) with a specified radius. Multiple circles can be active simultaneously for different objectives.

### Collisions

When two circles from different users overlap geographically, a collision event is created. The system tracks collision stability over time (detecting → stable → mission_created).

### Interview Missions

When a collision reaches stable status, an interview mission is created where an AI agent interviews both participants to assess compatibility. The mission results inform the final match decision.

### Matches

A match represents confirmed compatibility between two users. Matches can be initiated after interview missions or directly through collision analysis. Users must accept matches to enable direct communication.

### Location Ingestion

Real-time location updates (via `POST /api/locations/update`) trigger background collision detection. The system maintains a 10-second rate limit per user to optimize resource usage.

---

## Implementation Notes

- All timestamps are in ISO 8601 format (UTC)
- All IDs are UUIDs
- Pagination uses `limit` and `offset` parameters
- The `/api` prefix is applied to all routes
- Rate limiting is applied per-user for location endpoints
- Async operations return `202 Accepted` immediately
