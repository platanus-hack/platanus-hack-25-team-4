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

## Frontend ↔ Backend – Mismatches

- Auth – login
  - Frontend (Flutter): POST `/auth/login` (no `/api` prefix)
  - Backend: POST `/api/auth/login`
  - Status: Mismatch (path)
  - Fix: Prefix with `/api`.

- Auth – signup
  - Frontend (Flutter): POST `/auth/signup` with body `{ name, email, emailConfirmation, password, passwordConfirmation }`
  - Backend: POST `/api/auth/signup` with body `{ email, password, firstName?, lastName? }`
  - Status: Mismatch (path and body schema)
  - Fix: Use `/api/auth/signup` and send `{ email, password, firstName?, lastName? }`.

- Profile – GET/PUT `/api/users/me/profile`
  - Backend responses are wrapped: `{ "profile": { ... } }`
  - Flutter `ProfileApiClient` currently maps the entire response (or `response["user"]`) directly to `UserProfile`, which expects fields like `interests`, `bio`, etc. (flat). It does not extract the `profile` wrapper.
  - Status: Mismatch (response shape)
  - Fix: After HTTP call, use `final body = responseBody["profile"] as Map<String, dynamic>;` before calling `UserProfile.fromJson(body)`.

- Location background reporting
  - Frontend (Flutter): POST `/ubicaciones` body `{ lat, lng, email, recordedAt }`
  - Backend: No `/ubicaciones`. Closest API is PATCH `/api/users/me/position` with `{ centerLat, centerLon }` and auth required.
  - Status: Mismatch + Missing in backend (for `/ubicaciones`)
  - Fix: Either (1) change frontend to call PATCH `/api/users/me/position` with `{ centerLat, centerLon }`, or (2) add a new backend endpoint `/api/ubicaciones` that internally updates the user’s position.

---

## Correctly Implemented (Aligned)

At this time, no frontend endpoints fully align end-to-end (path + body + response) with the backend implementation without adjustments. The closest are:

- Profile legacy endpoints (`/api/users/me/profile` GET/PUT): Paths match, but the frontend must unwrap `profile` in the response as noted above to be fully aligned.

---

## Recommendations

1. Standardize base paths in frontends to include the `/api` prefix.
2. Update Flutter Auth signup payload to `{ email, password, firstName?, lastName? }`.
3. Adjust Flutter Profile mapping to read `response["profile"]` before parsing.
4. Update background location to use PATCH `/api/users/me/position` with `{ centerLat, centerLon }` (or implement `/api/ubicaciones` on the backend).
5. Implement or de-scope Matches/Interactions per the feature plan.
6. Add frontend clients for Circles and Chats/Message endpoints to leverage implemented backend features.

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


