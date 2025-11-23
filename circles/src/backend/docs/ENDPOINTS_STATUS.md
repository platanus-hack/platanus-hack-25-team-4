# API Endpoint Coverage Status

This document summarizes the current state of API endpoints across the backend and the frontends (Flutter app and mockup React app).

- Backend source of truth: `circles/src/backend/routes/*.ts` and `circles/src/backend/docs/ENDPOINTS.md`
- Flutter frontend: `circles-flutter/lib/**`
- Mockup React app: `mockup/src/**` (no live API usage)

## Legend

- Missing in Backend: Used or planned by frontend, not implemented in backend
- Missing in Frontend: Implemented in backend, not used by frontend
- Mismatch: Exists on both sides but path, parameters, or response shape differ
- Correct: Implemented and aligned in both

Config notes: Flutter `assets/config/app_config.json` now points to `http://localhost:3000/api` with `mockAuth: false`, so frontend requests are prefixed with `/api` automatically via the baseUrl.

---

## Backend – Missing

These endpoints are not currently implemented in the backend:

- Matches and interactions (from feature plan, not implemented):
  - GET /matches/mios
  - GET /matches/soy-match
  - POST /matches/{id}/aceptar

- Location ingestion used by Flutter background worker:
  - POST /ubicaciones
    - Flutter worker currently posts location here. Backend does not expose this route. The closest backend action is PATCH `/api/users/me/position`.

---

## Frontend – Missing

These backend-implemented endpoints are not used by the current frontends:

- Auth (Magic Link)
  - POST /api/auth/magic-link/request
  - GET /api/auth/verify-magic-link?token=...

- Users
  - GET /api/users/me
  - GET /api/users/:id
  - PATCH /api/users/me (firstName, lastName)
  - DELETE /api/users/me
  - PATCH /api/users/me/position (centerLat, centerLon) — Flutter posts to `/ubicaciones` instead

- Circles
  - POST /api/circles
  - GET /api/circles/me
  - GET /api/circles/:id
  - PATCH /api/circles/:id
  - DELETE /api/circles/:id

- Chats and Messages
  - GET /api/chats
  - POST /api/chats
  - GET /api/chats/:chatId
  - DELETE /api/chats/:chatId
  - GET /api/chats/:chatId/messages
  - POST /api/chats/:chatId/messages
  - GET /api/chats/:chatId/messages/:messageId
  - DELETE /api/chats/:chatId/messages/:messageId

- Health
  - GET /api/health

- Profile (used, but see mismatch below)
  - GET /api/users/me/profile
  - PUT /api/users/me/profile

---

## Correctly Implemented (Aligned)

- Auth – login/signup
  - Flutter now posts to `/api/auth/login` and `/api/auth/signup` with `{ email, password, firstName?, lastName? }`, matching backend expectations.
- Profile legacy endpoints (`/api/users/me/profile` GET/PUT): Paths match and the Flutter client unwraps the `profile` envelope before parsing.
- Users – GET `/api/users/me`: Flutter uses this to load the authenticated profile and email from the backend.
- Location background reporting
  - Flutter background worker now patches `/api/users/me/position` with `{ centerLat, centerLon }` using the stored auth token.

---

## Recommendations

1. Standardize base paths in frontends to include the `/api` prefix.
2. Update Flutter Auth signup payload to `{ email, password, firstName?, lastName? }`.
3. Adjust Flutter Profile mapping to read `response["profile"]` before parsing.
4. Implement or de-scope Matches/Interactions per the feature plan.
5. Add frontend clients for Circles and Chats/Message endpoints to leverage implemented backend features.
6. Handle Web font loading offline by bundling fonts locally (Flutter web warning observed when fetching Roboto).

---

## Reference: Implemented Backend Endpoints

- Health
  - GET /api/health

- Auth
  - POST /api/auth/signup
  - POST /api/auth/login
  - POST /api/auth/magic-link/request
  - GET /api/auth/verify-magic-link?token

- Users
  - GET /api/users/me
  - GET /api/users/:id
  - PATCH /api/users/me
  - DELETE /api/users/me
  - PATCH /api/users/me/position
  - GET /api/users/me/profile (legacy)
  - PUT /api/users/me/profile (legacy)

- Circles
  - POST /api/circles
  - GET /api/circles/me
  - GET /api/circles/:id
  - PATCH /api/circles/:id
  - DELETE /api/circles/:id

- Chats
  - GET /api/chats
  - POST /api/chats
  - GET /api/chats/:chatId
  - DELETE /api/chats/:chatId

- Messages
  - GET /api/chats/:chatId/messages
  - POST /api/chats/:chatId/messages
  - GET /api/chats/:chatId/messages/:messageId
  - DELETE /api/chats/:chatId/messages/:messageId
