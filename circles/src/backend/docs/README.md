# Backend Documentation

Quick reference for backend API and data models.

## Documents

1. **[ENDPOINTS.md](./ENDPOINTS.md)** - All API endpoints with request/response examples
2. **[DATA_MODELS.md](./DATA_MODELS.md)** - All database models and their fields
3. **[AUTH_PROCESS.md](./AUTH_PROCESS.md)** - Authentication flows (password and magic link)

## Quick Start

### Test Signup

```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

### Test Magic Link

```bash
# Request
curl -X POST http://localhost:3000/api/auth/magic-link/request \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","firstName":"John"}'

# Verify (use token from console in dev mode)
curl "http://localhost:3000/api/auth/verify-magic-link?token=TOKEN"
```

### Check Health

```bash
curl http://localhost:3000/api/health
```

## Environment

- **API:** <http://localhost:3000>
- **Database:** PostgreSQL at localhost:5432
- **Docs:** `circles/src/backend/docs/`
