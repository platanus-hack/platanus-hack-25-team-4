# Profile endpoints vs Flutter frontend

## Backend (implemented)
- Paths (mounted under `/api`):
  - `GET /api/users/me/profile` → `{ profile }` (legacy envelope).
  - `PUT /api/users/me/profile` body supports `{ bio?, interests?, profileCompleted?, socialStyle?, boundaries?, availability? }` → `{ profile }`.
- Stored profile shape (`circles/src/backend/types/user.type.ts`): JSON object with optional fields:
  - `bio?: string`
  - `interests?: { title: string; description: string }[]`
  - `profileCompleted?: boolean`
  - `socialStyle?: string`
  - `boundaries?: string[]`
  - `availability?: string`

## Frontend (current)
- Endpoints used: `GET /users/me` (to get email), `GET /users/me/profile` and `PUT /users/me/profile` via `ProfileApiClient` (`circles-flutter/lib/features/profile/data/profile_api_client.dart`).
- Payloads:
  - Fetch: expects `{ profile: { interests, bio, profileCompleted } }` or unwraps `interests`/`bio` directly.
  - Update: sends `{ bio, interests: [{ title, description }], profileCompleted: true }`.
- Models: `UserProfile { email, profileCompleted, interests: UserInterest[], bio }` with minimal parsing; ignores `socialStyle`, `boundaries`, `availability`.
- UI: Profile wizard/page reads/writes `bio` and `interests` only; uses mock storage when `mockAuth` is true.

## Gaps
- Fields: backend supports extra fields (`socialStyle`, `boundaries`, `availability`) not surfaced in frontend; frontend only handles `bio` + `interests`.
- Envelope: backend wraps profile in `{ profile }`; frontend handles both but assumes `profile` key on fetch.
- Completion flag: backend uses `profileCompleted` boolean; frontend sets it true on save; alignment OK.
- Auth source: frontend derives email from session; backend returns email from `/users/me`; alignment OK.

## Wiring plan
1) Align client envelope handling: keep reading `response['profile']` but ensure fallbacks for flat shape; keep `profileCompleted` mapping.
2) Map optional backend fields to the frontend model (add to `UserProfile` if needed) or explicitly ignore with comments; minimally, tolerate their presence when parsing.
3) On update, include `profileCompleted`, `bio`, `interests`; consider passing through `socialStyle/boundaries/availability` once UI supports them.
4) Add error surfacing in Profile UI for backend failures (show snackbar/banner).
5) Add a small unit test for `ProfileApiClient` mapping to ensure envelopes and new fields don’t break parsing.
