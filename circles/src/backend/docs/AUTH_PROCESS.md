# Authentication Process

## Overview

Two authentication methods available:

1. **Password-based** - Traditional signup/login
2. **Magic Link** - Passwordless login

Both return JWT tokens valid for 12 hours.

---

## Password-Based Auth

### Signup

1. User calls `POST /api/auth/signup` with email and password
2. System checks email doesn't exist
3. Password hashed with bcrypt
4. User created in database
5. JWT token generated and returned

Request:

```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

Response:

```json
{
  "token": "JWT_TOKEN",
  "user": { "id": "...", "email": "user@example.com", ... }
}
```

### Login

1. User calls `POST /api/auth/login` with email and password
2. System finds user by email
3. Password compared with stored hash
4. JWT token generated and returned

Request:

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

Response:

```json
{
  "token": "JWT_TOKEN",
  "user": { ... }
}
```

---

## Magic Link Auth

### Step 1: Request Magic Link

1. User calls `POST /api/auth/magic-link/request` with email
2. System generates secure 256-bit token
3. Token saved in database with 15-minute expiry
4. (Production) Email sent with magic link
5. (Development) Link logged to console

Request:

```bash
curl -X POST http://localhost:3000/api/auth/magic-link/request \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","firstName":"John"}'
```

Response:

```json
{
  "success": true,
  "message": "Magic link sent to user@example.com"
}
```

Dev mode: Console shows:

```
🔗 MAGIC LINK:
Link: http://localhost:3000/api/auth/verify-magic-link?token=abc123def456...
```

### Step 2: Verify Magic Link

1. User clicks link or calls verify endpoint with token
2. System finds token in database
3. Checks token hasn't expired (15 minutes)
4. Finds or creates user with that email
5. Deletes token (one-time use)
6. JWT token generated and returned

Request:

```bash
curl "http://localhost:3000/api/auth/verify-magic-link?token=abc123def456"
```

Response:

```json
{
  "token": "JWT_TOKEN",
  "user": { "id": "...", "email": "user@example.com", ... }
}
```

---

## Using JWT Token

Once authenticated, include token in all requests:

```bash
curl -H "Authorization: Bearer JWT_TOKEN" \
  http://localhost:3000/api/protected-endpoint
```

Token expires in 12 hours. After expiry, user must authenticate again.

---

## Error Handling

### Email Already Exists (Signup)

```json
{
  "error": "Email already registered"
}
```

Status: 409

### Invalid Credentials (Login)

```json
{
  "error": "Invalid email or password"
}
```

Status: 401

### Invalid Magic Link Token

```json
{
  "error": "Invalid or expired magic link"
}
```

Status: 401

### Magic Link Expired

```json
{
  "error": "Magic link has expired"
}
```

Status: 401

---

## Development vs Production

**Development Mode** (default):

- Magic links logged to console
- No email sent
- Use for local testing

**Production Mode** (when AWS_ACCESS_KEY_ID set):

- Magic links sent via AWS SES
- Real email delivery
- Configure in `.env.local`

Set `NODE_ENV=production` and add AWS credentials to switch modes.
