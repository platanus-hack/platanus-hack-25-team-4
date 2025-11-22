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

Represents a group or community.

```typescript
{
  id: string                    // UUID, primary key
  userId: string                // Creator user ID
  name: string
  description: string
  objective: string
  status: CircleStatus          // "active" | "inactive" | "archived"
  latitude: number              // Optional geolocation
  longitude: number             // Optional geolocation
  createdAt: Date
  updatedAt: Date
}
```

---

## Match

Represents a match between two users.

```typescript
{
  id: string                    // UUID, primary key
  primaryUserId: string         // User A
  secondaryUserId: string       // User B
  matchType: MatchType          // "direct" | "indirect" | "recommendation"
  matchScore: number            // 0-100
  status: MatchStatus           // "pending" | "accepted" | "rejected"
  createdAt: Date
  updatedAt: Date
}
```

---

## Chat

Represents a conversation between users.

```typescript
{
  id: string                    // UUID, primary key
  primaryUserId: string         // User A
  secondaryUserId: string       // User B
  createdAt: Date
  updatedAt: Date
}
```

---

## Message

Represents a message in a chat.

```typescript
{
  id: string                    // UUID, primary key
  chatId: string                // Chat ID
  senderId: string              // User sending message
  receiverId: string            // User receiving message
  content: string
  isModerated: boolean          // false = pending, true = approved
  createdAt: Date
}
```

---

## AgentPersona

Represents an AI agent personality/rules.

```typescript
{
  id: string                    // UUID, primary key
  userId: string                // Associated user
  name: string
  description: string
  safetyRules: string           // JSON encoded rules
  createdAt: Date
  updatedAt: Date
}
```

---

## Enums

**CircleStatus:**

- `active`
- `inactive`
- `archived`

**MatchType:**

- `direct`
- `indirect`
- `recommendation`

**MatchStatus:**

- `pending`
- `accepted`
- `rejected`
