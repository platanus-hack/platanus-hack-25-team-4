# Data Models

## User

Represents a user account in the system.

```typescript
{
  id: string                    // UUID, primary key
  email: string                 // Unique
  firstName: string | null
  lastName: string | null
  passwordHash: string | null   // Optional (null for magic link only)
  profile: UserProfile | null   // JSON
  centerLat: number | null      // User's current latitude (center of circles)
  centerLon: number | null      // User's current longitude (center of circles)
  createdAt: Date
  updatedAt: Date
}
```

**UserProfile:**

```typescript
{
  interests?: string[]
  socialStyle?: string
  boundaries?: string[]
  availability?: string
  [key: string]: unknown        // Additional custom fields allowed
}
```

---

## MagicLinkToken

Temporary tokens for passwordless authentication.

```typescript
{
  id: string                    // UUID, primary key
  email: string                 // Unique
  token: string                 // Unique, 256-bit hex
  expiresAt: Date               // 15 minutes from creation
  createdAt: Date
}
```

**Behavior:**

- Auto-deletes after 15 minutes
- One-time use only
- Deleted after verification

---

## Circle

Represents a geographic circle centered at the user's current position with a given radius.
The center location is always the user's current position (centerLat/centerLon from User model).

```typescript
{
  id: string                    // UUID, primary key
  userId: string                // Creator user ID
  objective: string             // Goal or purpose of the circle
  radiusMeters: number          // Radius in meters from user's center position
  status: CircleStatus          // "active" | "paused" | "expired"
  startAt: Date                 // When the circle becomes active
  expiresAt: Date | null        // When the circle expires (can be null for open-ended)
  createdAt: Date
  updatedAt: Date
}
```

**Note:** Position is not stored in Circle. Instead, it uses the User's `centerLat` and `centerLon` fields.

---

## CollisionEvent

Represents a geographic proximity match between two circles. Tracks the lifecycle of a collision from initial detection through mission creation and matching.

```typescript
{
  id: string                    // UUID, primary key
  
  circle1Id: string             // First circle ID
  circle2Id: string             // Second circle ID
  user1Id: string               // Owner of circle1
  user2Id: string               // Owner of circle2
  
  distanceMeters: number        // Geographic distance between the two circles
  
  detectedAt: Date              // Timestamp of initial detection
  firstSeenAt: Date             // First time collision was observed (used for stability)
  
  status: CollisionStatus       // See CollisionStatus enum below
  
  missionId: string | null      // Associated interview mission (if created)
  matchId: string | null        // Associated match (if created)
  
  processingError: string | null // Error message if processing failed
  processedAt: Date | null      // Timestamp of final processing
  
  createdAt: Date
  updatedAt: Date
}
```

**CollisionStatus Values:**

- `detecting` - Initial detection phase, stability not yet confirmed
- `stable` - Collision observed for sufficient duration, stability confirmed
- `mission_created` - Interview mission has been created
- `matched` - Match has been confirmed
- `cooldown` - Temporarily inactive (collision may have moved out of range)
- `expired` - Collision is no longer valid/relevant

**Note:** A unique constraint on `(circle1Id, circle2Id)` ensures only one collision per circle pair.

---

## InterviewMission

Represents an AI-mediated interview between two users when their circles collide. The system conducts an interview to determine match compatibility.

```typescript
{
  id: string                    // UUID, primary key
  
  ownerUserId: string           // Owner of the first circle
  visitorUserId: string         // Owner of the second circle
  ownerCircleId: string         // The owner's circle
  visitorCircleId: string       // The visitor's circle
  collisionEventId: string      // Associated collision event (unique)
  
  status: MissionStatus         // "pending" | "in_progress" | "completed" | "failed" | "cancelled"
  
  transcript: InterviewTranscript | null  // JSON transcript of the interview
  judgeDecision: JudgeDecision | null     // AI judge's recommendation on match
  
  createdAt: Date
  completedAt: Date | null      // When the mission finished
  startedAt: Date | null        // When the interview started
  
  failureReason: string | null  // Reason if status is "failed"
  attemptNumber: number         // Retry attempt count (default 1)
}
```

**InterviewTranscript:**

```typescript
{
  turns: Array<{
    speaker: "interviewer" | "visitor"
    content: string
  }>
}
```

**JudgeDecision:**

```typescript
{
  recommendation: "match" | "soft_match" | "no_match"
  confidence: number            // 0 to 1 (confidence score)
  summary: string               // Brief explanation
}
```

**MissionStatus Values:**

- `pending` - Created but not yet started
- `in_progress` - Interview is currently running
- `completed` - Interview finished successfully
- `failed` - Interview failed to complete
- `cancelled` - Mission was cancelled

---

## Match

Represents a confirmed or pending match between two users based on circle collision and/or interview assessment.

```typescript
{
  id: string                    // UUID, primary key
  
  primaryUserId: string         // User A
  secondaryUserId: string       // User B
  
  primaryCircleId: string       // Circle from User A
  secondaryCircleId: string     // Circle from User B
  
  type: MatchType               // "match" | "soft_match"
  worthItScore: number          // 0 to 1 (match quality score)
  status: MatchStatus           // See MatchStatus enum below
  
  explanationSummary: string | null  // Human-readable explanation of why this match was made
  collisionEventId: string | null    // Associated collision event (if any)
  
  createdAt: Date
  updatedAt: Date
}
```

**MatchType Values:**

- `match` - Strong/direct match between circles
- `soft_match` - Potential match with some compatibility

**MatchStatus Values:**

- `pending_accept` - Match created, awaiting user acceptance
- `active` - Match accepted by user(s), can communicate
- `declined` - Match was explicitly declined
- `expired` - Match is no longer valid

---

## Chat

Represents a conversation between two users.

```typescript
{
  id: string                    // UUID, primary key
  
  primaryUserId: string         // User A
  secondaryUserId: string       // User B
  
  matchId: string | null        // Associated match (if from a match)
  
  createdAt: Date
}
```

---

## Message

Represents a message in a chat.

```typescript
{
  id: string                    // UUID, primary key
  
  chatId: string                // Chat ID
  senderUserId: string          // User sending message
  receiverId: string            // User receiving message
  
  content: string               // Message text
  
  moderationFlags: Json | null  // Moderation results (if flagged)
  
  createdAt: Date
}
```

---

## AgentPersona

Represents an AI agent's personality and safety rules for interviews.

```typescript
{
  userId: string                // User ID (primary key relationship)
  
  safetyRules: Json | null      // JSON-encoded safety rules for agent
  
  createdAt: Date
  updatedAt: Date
}
```

---

## Enums

### CircleStatus

- `active` - Circle is currently active and matching
- `paused` - Circle is temporarily paused
- `expired` - Circle has expired

### CollisionStatus

- `detecting` - Initial collision detection phase
- `stable` - Collision confirmed to be stable
- `mission_created` - Interview mission has been created
- `matched` - Match has been established
- `cooldown` - Temporarily inactive
- `expired` - Collision is no longer relevant

### MissionStatus

- `pending` - Not yet started
- `in_progress` - Currently executing
- `completed` - Finished successfully
- `failed` - Failed to complete
- `cancelled` - Was cancelled

### MatchType

- `match` - Strong/direct match
- `soft_match` - Potential/soft match

### MatchStatus

- `pending_accept` - Awaiting user acceptance
- `active` - User has accepted, can communicate
- `declined` - User declined
- `expired` - Match is no longer valid

---

## Database Constraints & Indexes

### Unique Constraints

- `User.email` - Unique per user
- `MagicLinkToken.email` - Unique token per email
- `MagicLinkToken.token` - Unique tokens
- `CollisionEvent.(circle1Id, circle2Id)` - Only one collision per circle pair
- `Match.collisionEventId` - One match per collision event

### Indexes

- `Circle.(status, createdAt)` - For status and timeline queries
- `CollisionEvent.(status, firstSeenAt)` - For stability detection
- `CollisionEvent.(user1Id, user2Id)` - For user-based queries
- `CollisionEvent.status` - For status filtering
- `CollisionEvent.createdAt` - For timeline queries
- `InterviewMission.(status, createdAt)` - For mission queries
- `InterviewMission.(ownerUserId, visitorUserId)` - For user-based queries
- `InterviewMission.status` - For status filtering

---

## Relationships

```
User
  ├── circles (Circle[])
  ├── matchesAsPrimary (Match[])
  ├── matchesAsSecondary (Match[])
  ├── chatsAsPrimary (Chat[])
  ├── chatsAsSecondary (Chat[])
  ├── sentMessages (Message[])
  ├── receivedMessages (Message[])
  ├── collisionsAsUser1 (CollisionEvent[])
  ├── collisionsAsUser2 (CollisionEvent[])
  ├── ownerMissions (InterviewMission[])
  ├── visitorMissions (InterviewMission[])
  └── persona (AgentPersona)

Circle
  ├── user (User)
  ├── matchesAsPrimary (Match[])
  ├── matchesAsSecondary (Match[])
  ├── collisionsAsCircle1 (CollisionEvent[])
  ├── collisionsAsCircle2 (CollisionEvent[])
  ├── missionsAsOwner (InterviewMission[])
  └── missionsAsVisitor (InterviewMission[])

CollisionEvent
  ├── circle1 (Circle)
  ├── circle2 (Circle)
  ├── user1 (User)
  ├── user2 (User)
  ├── match (Match)
  └── mission (InterviewMission)

InterviewMission
  ├── ownerUser (User)
  ├── visitorUser (User)
  ├── ownerCircle (Circle)
  ├── visitorCircle (Circle)
  └── collisionEvent (CollisionEvent)

Match
  ├── primaryUser (User)
  ├── secondaryUser (User)
  ├── primaryCircle (Circle)
  ├── secondaryCircle (Circle)
  └── collisionEvent (CollisionEvent)

Chat
  ├── primaryUser (User)
  ├── secondaryUser (User)
  └── messages (Message[])

Message
  ├── chat (Chat)
  ├── sender (User)
  └── receiver (User)
```

---

## Data Flow Summary

1. **User creates circles** → Circles stored with user's current position
2. **Location updates received** → `POST /api/locations/update`
3. **Collision detection runs** → Identifies overlapping circles → Creates `CollisionEvent` (status: `detecting`)
4. **Stability check** → After duration check → Status: `stable`
5. **Interview mission created** → Status: `mission_created`
6. **AI interviews both users** → Generates transcript and recommendation
7. **Judge decision made** → `Match` is created with recommendation
8. **User accepts match** → Match status: `active` → Can chat
9. **Communication begins** → Messages exchanged in `Chat`
