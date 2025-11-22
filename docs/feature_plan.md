# Circles app roadmap

## Functional areas
- **Home dashboard**: stats on circles, matches received, matches sent.
- **Profile**: view/update my info.
- **Circles**: create/edit/delete circles with objectives, optional expiration, and search radius.
- **Matches**: two lists — people who match my circles, and people whose circles I match; per match show circle context.
- **Interactions**: accept an outgoing match to enable chat.
- **Chats**: list conversations, open chat, send/receive messages.

## Detailed tasks
- **App shell** ✅
  - Add bottom navigation (phone) and nav rail/sidebar (wide) for Home, Circles, Matches, Chats, Profile.
  - Preserve auth session; reuse existing login/signup flow.
- **Authentication reuse**
  - Ensure auth token attached to all API calls; handle 401 by clearing session and redirecting to login. UI/labels in Spanish.
- **Home dashboard** (stub UI in place)
  - Fetch stats: total circles, matches received, matches I’m in, pending accepts.
  - Show cards with counts and quick links to Circles and Matches.
  - Handle loading/error/empty states.
- **Profile** (stub UI in place)
  - Fetch/display user info (name, email, location, avatar placeholder).
  - Edit form: name, optional bio/location, avatar upload placeholder.
  - Save to backend with optimistic UI; show errors inline.
- **Circles CRUD** (stub UI in place)
  - Circles list: objective, expiration (optional), radius (km), status.
  - Create/edit form with validation: objective (required), expiration date (optional), radius slider/input; location permissions prompt if needed.
  - Delete circle with confirm dialog.
  - Wire to backend endpoints; show errors per field/message.
- **Matching** (in-memory UI)
  - Fetch two datasets: (a) people matching my circles, (b) people whose circles I match. Each item shows circle name/objective, distance, expiration, and match strength if available.
  - Filter/sort controls (by distance/expiration).
  - Handle empty/errored states.
- **Interactions (accept)** (in-memory)
  - From “I match them” list, add “Accept” action; POST to backend to enable chat.
  - On success, move that person to chats list; update counts.
  - Handle failures with toasts/inline errors.
- **Chats** (in-memory UI)
  - Chats list: person name, circle context, last message, unread indicator.
  - Chat thread view: message list, composer with send; show sending/error states per message.
  - Receive updates via polling or web sockets (configurable); mark read on open.
- **Networking**
  - Central API client with base URL from config; attach auth token; map errors to user-friendly messages.
  - Define DTOs/models for profile, circle, match, interaction, chat.
- **Storage**
  - Cache auth token (done). Add lightweight cache for user profile and circles for fast start; invalidate on updates.
- **Navigation**
  - Define routes for /home, /circles, /matches, /chats, /profile, /chat/:id.
  - Preserve deep-link behavior on web; ensure back button works.
- **Error handling and empty states**
  - Standardize error surfaces (inline + snackbars). Provide skeletons/loading indicators. Friendly empty views with CTA.
- **Testing**
  - Unit: repositories/mappers. Widget: forms and lists render with mock data. Integration: login → create circle → see in list; match accept → chat appears.
- **Accessibility and responsiveness**
  - Follow breakpoints (phone/tablet/wide). Support text scaling, focus states, hover for web, 44x44 touch targets.

## API bodies (draft for MVP, adjustable)
- **Auth**
  - `POST /auth/login` body: `{ "email": string, "password": string }` → `{ "token": string, "user": { "id": string, "nombre": string, "email": string } }`
  - `POST /auth/signup` body: `{ "nombre": string, "email": string, "emailConfirmacion": string, "password": string, "passwordConfirmacion": string }` → same shape as login
- **Profile**
  - `GET /me` → `{ "id": string, "nombre": string, "email": string, "bio"?: string, "ubicacion"?: { "lat": number, "lng": number, "ciudad"?: string }, "avatarUrl"?: string }`
  - `PUT /me` body: `{ "nombre": string, "bio"?: string, "ubicacion"?: { "lat": number, "lng": number, "ciudad"?: string } }`
- **Circles**
  - `GET /circulos` → list of circles.
  - `POST /circulos` body: `{ "objetivo": string, "descripcion"?: string, "expiraEn"?: string (ISO), "radioKm": number, "ubicacion"?: { "lat": number, "lng": number } }`
  - `PUT /circulos/{id}` same as POST.
  - `DELETE /circulos/{id}`
- **Matches**
  - `GET /matches/mios` (personas que matchean mis círculos) → `[ { "personaId": string, "nombre": string, "circuloId": string, "circuloObjetivo": string, "distanciaKm"?: number, "expiraEn"?: string } ]`
  - `GET /matches/soy-match` (a quienes yo matcheo) → same shape.
- **Interacciones**
  - `POST /matches/{id}/aceptar` body: `{}` → `{ "chatId": string, ... }`
- **Chats**
  - `GET /chats` → `[ { "chatId": string, "personaId": string, "nombre": string, "circuloObjetivo"?: string, "ultimoMensaje"?: string, "ultimoEnvio"?: string, "noLeidos": number } ]`
  - `GET /chats/{id}/mensajes` → `[ { "id": string, "autorId": string, "texto": string, "enviadoEn": string, "estado": "enviado"|"entregado"|"leido" } ]`
  - `POST /chats/{id}/mensajes` body: `{ "texto": string }` → same message shape.
  - Optional websocket/polling endpoint for realtime: TBD (`/ws` or polling every 5–10s).

All UI copy should be in Spanish (e.g., labels, errors, buttons). We'll adjust these payloads as the backend solidifies. 
