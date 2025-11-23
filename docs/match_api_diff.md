# Match endpoints vs Flutter requests (pre-implementation)

This note captures the gap between the backend match endpoints and what the Flutter app plans/uses today before wiring things up.

## Backend (implemented)
- Paths (mounted under `/api`, source `circles/src/backend/routes/matches.ts` + docs `circles/src/backend/docs/ENDPOINTS.md`):
  - `GET /api/matches` with optional `status`, `limit`, `offset`; responds with `{ matches: MatchWithDetails[], pagination: {...} }`.
  - `GET /api/matches/:id` returns `{ match: MatchWithDetails }` after participant check.
  - `POST /api/matches/:id/accept` → `{ message, match }` sets status to `active`.
  - `POST /api/matches/:id/decline` → `{ message, match }` sets status to `declined`.
- Match payload fields: `id`, `primaryUserId`, `secondaryUserId`, `primaryCircleId`, `secondaryCircleId`, `type` (`match|soft_match`), `status` (`pending_accept|active|declined|expired`), `worthItScore`, `explanationSummary`, timestamps.

## Flutter frontend (current state)
- No HTTP calls for matches yet. UI seeds in-memory data (`_seedMatchesAndChats` in `circles-flutter/lib/features/app/app_state.dart`) and renders `MatchCandidate` (`id`, `personId`, `nombre`, `circuloId`, `circuloObjetivo`, `distanciaKm?`, `expiraEn?`).
- Feature plan (see `docs/feature_plan.md`) expects:
  - `GET /matches/mios` → array of the `MatchCandidate` shape (people matching my circles).
  - `GET /matches/soy-match` → same shape (circles I match).
  - `POST /matches/{id}/aceptar` → `{ chatId, ... }` to enable chat.
- Config currently points to `https://backend2.circles.lat/api` (`circles-flutter/assets/config/app_config.json`), but no match client exists (only `CirclesApiClient` etc.).

## Key differences to resolve
- Path + prefix: backend uses `/api/matches`, `/api/matches/:id/{accept|decline}`; Flutter plan has `/matches/mios`, `/matches/soy-match`, `/matches/{id}/aceptar` (Spanish, no `/api` prefix).
- Response shape: backend wraps data (`{ matches: [...], pagination }`), while Flutter plan expects bare arrays and no pagination metadata.
- Fields: backend exposes user/circle IDs, type/status, scores, explanations; Flutter models expect `personId`, `nombre`, circle objective text, `distanciaKm`, `expiraEn` and no status/type fields.
- Actions: backend has both accept and decline and returns the updated `match`; Flutter only models “accept” and expects chat creation info (chat data not returned by backend accept).
- List semantics: backend returns a single list filtered by `status`; Flutter wants two separate lists (received vs sent) and does not yet model status to split them.

These gaps should be closed before implementing the Flutter match client (decide on paths, mapping from backend match objects to `MatchCandidate`, pagination handling, and how chat creation is triggered after acceptance).

## Planned frontend tasks to align with backend
- Add a `MatchesApiClient` that calls the backend contracts (`GET /api/matches`, `GET /api/matches/:id`, `POST /api/matches/:id/accept`, `POST /api/matches/:id/decline`) using the same baseUrl pattern as `CirclesApiClient`.
- Define DTO → domain mapper from backend `MatchWithDetails` to a richer frontend model (include `status`, `type`, `primary/secondary` user + circle ids, optional `worthItScore`, `explanationSummary`); update or replace `MatchCandidate` accordingly.
- Split matches into “for me” vs “I am in” by comparing `primaryUserId`/`secondaryUserId` to the authenticated user id (needs user id from auth profile) instead of relying on two separate endpoints.
- Wire `AppState` to fetch matches from the API (respect pagination with `limit/offset`, or page-all for now) and remove the in-memory `_seedMatchesAndChats` placeholders once network-backed.
- Implement accept/decline flows in `AppState` and UI by calling `/api/matches/:id/accept|decline`; after accept, either:
  - fetch the updated match list and, if `status === active`, open/create chat via existing chats endpoints, or
  - add a follow-up call to create/open chat if product requires (decision needed—backend accept does not return chat data).
- Update UI (`matches_page.dart`, dashboard counts) to show real statuses, disabled states, and error handling/snackbars for network failures; ensure Spanish copy still applies.
- Ensure config uses `/api` prefix (`assets/config/app_config.json` already does) and apply common auth headers via shared HTTP client.
- Add minimal tests/mocks for the new client and mapping logic (unit tests for mapper; widget/state test for accept flow if feasible).
