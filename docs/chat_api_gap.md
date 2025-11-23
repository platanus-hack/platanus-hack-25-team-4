# Chat/Message endpoints vs Flutter frontend

## Backend (implemented)
- **Chats**
  - `GET /api/chats` → `{ data: ChatWithDetails[], count }` (includes participant info; service also adds `latestMessage`).
  - `POST /api/chats` body `{ primaryUserId, secondaryUserId, matchId? }` → chat object.
  - `GET /api/chats/:chatId` → chat with participants.
  - `DELETE /api/chats/:chatId` → `204`.
- **Messages**
  - `GET /api/chats/:chatId/messages?limit&offset` → `{ data: MessageWithDetails[], total, limit, offset }`.
  - `POST /api/chats/:chatId/messages` body `{ content, receiverId }` → message (`id`, `chatId`, `senderUserId`, `receiverId`, `content`, `createdAt`, plus sender/receiver refs).
  - `GET /api/chats/:chatId/messages/:messageId` → message.
  - `DELETE /api/chats/:chatId/messages/:messageId` → `204`.

## Frontend (current)
- Models/UI: `ChatThread { id, personId, personName, circleObjective?, lastMessage?, unreadCount, messages: ChatMessage[] }`, `ChatMessage { id, senderId, text, sentAt }`.
- State: chats/messages are seeded locally in `AppState`; **no HTTP client** for chats/messages.
- UI: `ChatsPage` lists in-memory threads; send action only mutates local state (`AppState.sendMessage`); no backend integration; no chat creation when accepting a match.
- Field mismatch: backend uses `content/senderUserId/receiverId/createdAt`; frontend uses `text/senderId/sentAt` and omits receiver.
- Response shape mismatch: backend wraps lists in `{ data, total/... }`, frontend expects raw lists.

## Wiring tasks to enable real chat
1) Add a `ChatsApiClient` to call backend chat routes (`GET/POST/GET/:id/DELETE /api/chats`, `GET/POST /api/chats/:chatId/messages`, `DELETE /api/chats/:chatId/messages/:messageId`) with auth headers and response parsing.
2) Update chat/message domain models (or add DTO mappers) to map backend fields to UI: `content → text`, `senderUserId → senderId`, `createdAt → sentAt`, include participant ids/emails for receiver lookup.
3) Extend `AppState` to load chats/messages from the API, keep pagination simple (initial page), and replace local seeding; handle errors by showing empty lists + error banner.
4) Wire `ChatThreadPage` (if present) to send messages via backend `POST /messages`, append optimistic message, and refresh thread; handle failures with toasts.
5) On match accept, create or fetch a chat between participants (`POST /api/chats` or check existing via `/api/chats` filter) and surface it in Chats.
6) Update `ChatsPage` to show backend data (last message time/content, unread count if available/derived) and add pull-to-refresh.
7) Add minimal tests for the new clients/mappers (unit) and a happy-path integration for sending a message.
