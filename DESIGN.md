# Active Circles – Product & System Design

## 1. Overview

Active Circles is a location‑based social network powered by AI agent personas.  
Users create “Circles” around themselves: each Circle encodes an objective (free‑text intent), a radius, and a duration. When Circles from different users spatially collide, their agent personas simulate interactions to decide whether it’s “worth it” to connect the humans.

Users do **not** browse nearby users or Circles. All discovery is agent‑driven.  
When the system finds a promising connection, your agent:

- Evaluates compatibility via simulated scenarios.
- Decides whether it’s a strong “match” or a “soft match”.
- Presents the other person to you, explaining *why* it’s a good fit **without exposing sensitive details** about the other user.
- Either opens a chat directly (match) or asks the other user for consent (soft match).

Circles can have different purposes and are treated as independent; they do not compete with each other.

---

## 2. Goals & Non‑Goals

### 2.1 Goals

- Connect people in physical proximity around specific, real‑world intents (e.g. “play tennis this evening”).
- Use agent personas to pre‑filter and prioritize interactions so users receive fewer but higher‑quality connections.
- Allow multiple, simultaneous Circles per user (different intents, radii, durations).
- Build rich agent personas from users’ existing digital traces plus onboarding questions.
- Provide clear, privacy‑preserving explanations for every match through the user’s own agent.

### 2.2 Non‑Goals (v1)

- User‑driven browsing of nearby users or Circles (no map‑based discovery list, no swiping).
- Group coordination or events beyond 1:1 chat.
- Fully autonomous agent‑to‑agent relationships that never involve human review.
- Adjustable “aggressiveness” controls for agent behavior (fixed strategy in v1).
- Cross‑platform federation with other social networks.

---

## 3. Core Concepts

### 3.1 Entities

- **User**  
  Human using the app, with a profile and permissions.

- **Agent Persona**  
  AI representation of the user, built from:
  - Explicit onboarding answers.
  - Optional social data (social networks, messages, locations, events).
  - Interaction history within Active Circles.  
  The agent knows:
  - Interests and preferences.
  - Communication style, boundaries, and safety constraints.
  - Objectives associated with active Circles.

- **Objective**  
  Free‑text description of what the user wants within a Circle.  
  Examples:
  - “Find someone to play tennis in Palermo between 6pm–8pm.”
  - “Grab coffee with other founders near Recoleta this morning.”

- **Interests**  
  Longer‑term topics the user cares about, inferred from data and onboarding.  
  Represented as:
  - Tags (e.g. `tennis`, `AI`, `cooking`).
  - Embeddings (for similarity calculations).

- **Circle**  
  A context for a single objective:
  - `owner_user_id`
  - `objective_text`
  - `objective_embedding`
  - `center_lat`, `center_lon` (from GPS)
  - `radius_m`
  - `start_at`, `expires_at`
  - `status` (active, paused, expired)
  - `purpose` (free‑text/category, non‑competing with other Circles)

  A user can have many Circles active simultaneously, each with a different purpose.

- **Match Types**
  - **Match**  
    Both users have Circles with strongly aligned objectives. Chat opens immediately after the agents deem it “worth it”.
  - **Soft Match**  
    One user’s Circle objective aligns with the other user’s *interests* (but not with one of their active objectives).  
    The non‑objective user receives a notification and decides whether to accept. Chat opens only on acceptance.

- **Simulated Scenario**  
  A brief, backend‑only conversation between two agent personas used to:
  - Estimate whether the connection will satisfy both users’ objectives.
  - Assess conversational chemistry and safety.
  - Produce an explanation and suggested opener.

---

## 4. User Experience & Flows

### 4.1 Onboarding & Profiling

1. **Sign‑up & Auth**
   - User signs up via phone/email + code or passwordless link.
   - Accepts terms, privacy policy, data usage for AI.

2. **Permissions & Data Sources**
   - Location permission (foreground + optional background).
   - Optional connections to:
     - Social networks (public posts, likes, friendship graph).
     - Chat platforms (where allowed – subject to platform ToS).
   - User can choose which sources to share.

3. **Questionnaire**
   - Simple, generative‑style questions:
     - Interests, hobbies, skills.
     - Social comfort level (small talk, deep conversations, etc.).
     - Boundaries (topics to avoid, time‑of‑day availability).

4. **Agent Persona Construction**
   - Backend ingests raw data, extracts signals, builds:
     - Structured traits: personality, communication style, values.
     - Interests and topic embeddings.
     - Safety rules.  
   - Agent is ready to:
     - Simulate conversations.
     - Score compatibility.
     - Explain matches back to the user.

### 4.2 Creating & Managing Circles

1. **Create Circle**
   - User taps “Create Circle”.
   - Enters objective as free text.
   - Chooses:
     - Radius (e.g., 100–3000m).
     - Duration (e.g., 30 minutes to 24 hours).
     - Optional purpose/category.
     - Optional filters (e.g., age range) if included in v1.

2. **Circle Lifecycle**
   - `Active` from `start_at` to `expires_at` while location is available.
   - Can be paused or extended by the user.
   - User can maintain multiple Circles for different purposes; these do not compete for matches.

3. **Location Updates**
   - App sends periodic GPS updates (rate adjusted for battery vs. reactivity).
   - Each active Circle’s center tracks the user’s current position (if configured to move with user).

### 4.3 Matching & Presentation

Users **do not** browse. The system only surfaces curated opportunities.

1. **Collision Detection**
   - Backend receives location updates and identifies Circle pairs whose radii overlap.
   - Produces collision events for the Matching Engine.

2. **Compatibility Evaluation**
   - For each colliding pair:
     - Compare objectives via embeddings.
     - Compare objectives vs interests in both directions.
     - Apply rules to classify as:
       - candidate `match` (objective–objective alignment), or
       - candidate `soft match` (objective–interest alignment).

3. **Agent Simulation**
   - Agent personas for both users run a short simulated conversation:
     - Clarify each user’s intent.
     - Explore likely outcomes if they meet or chat.
     - Check for friction or safety concerns.
   - Produces:
     - A “worth it” score.
     - A private rationale.
     - Suggested conversation starter and topics.

4. **Outcome**
   - **Match**  
     - If score crosses `MATCH_OPEN_CHAT_THRESHOLD`:
       - Backend creates a chat.
       - Each user’s agent “presents” the other person:
         - Explains why this match is promising.
         - Highlights alignment (e.g., “They are also in Palermo and want to play tennis around the same time”).
         - **Does not expose sensitive raw data** such as exact social handles, full names, message histories, or anything not intended for sharing.
       - Shows suggested opener that the user can edit or send.

   - **Soft Match**
     - If score crosses `SOFT_MATCH_NOTIFY_THRESHOLD`:
       - The non‑objective user receives a notification:
         - e.g., “Your agent found someone nearby who wants to play tennis. You’ve mentioned tennis as an interest. Do you want to connect?”
       - Explanation is phrased in terms of:
         - Shared interests.
         - Contextual alignment.
         - Without revealing identifying or sensitive information about the other user.
       - If accepted:
         - Chat is created and both sides see an agent‑generated intro.
       - If declined:
         - Soft match is marked as declined; no further action.

   - **Rejected**
     - If alignment or safety score is low:
       - No user‑visible action is taken.
       - The event is logged for tuning.

### 4.4 Chat Experience

- 1:1 chat between matched users.
- Features:
  - Message sending, read receipts, basic media.
  - Simple agent assistance:
    - Suggested replies (“Reply with…”) that users can tap or edit.
    - Possible conversation topics based on objectives.
  - Agents do **not** send messages autonomously in v1.

---

## 5. Matching & Agent Logic

### 5.1 Geo Filtering

- For each active Circle:
  - Store `(lat, lon, radius_m)` in a geospatial index.
  - Find candidate Circle pairs with overlapping radii:
    - `distance(centerA, centerB) ≤ radiusA + radiusB`.

### 5.2 Semantic Matching

- Represent:
  - `objective_text` → embedding.
  - `interests` → aggregated embedding + tags.

- For each candidate pair (A, B):
  - Compute:
    - `objective_similarity = cos_sim(emb(A.obj), emb(B.obj))`.
    - `interest_similarity_A = cos_sim(emb(A.obj), emb(B.interests))`.
    - `interest_similarity_B = cos_sim(emb(B.obj), emb(A.interests))`.

- Classification:
  - **Match candidate**  
    - `objective_similarity ≥ HARD_MATCH_THRESHOLD`.
  - **Soft match candidate**  
    - `objective_similarity < HARD_MATCH_THRESHOLD` and  
      `max(interest_similarity_A, interest_similarity_B) ≥ SOFT_MATCH_THRESHOLD`.

### 5.3 Simulated Scenarios

- Inputs:
  - Agent personas A and B (traits, interests, boundaries).
  - Both objectives and purposes.
  - Context: time, approximate place description, recent in‑app behavior.

- Simulation:
  - 1–3 short turns:
    - Discuss objective, expectations, logistics.
    - Evaluate compatibility, comfort, and potential risk.

- Outputs:
  - `worth_it_score ∈ [0,1]`.
  - Safety flags (if any).
  - Internal reasoning summary.
  - Suggested short intro message and possible first questions.

### 5.4 Decision Rules

- **Match (auto‑chat)**
  - If type is `match` and:
    - `worth_it_score ≥ MATCH_OPEN_CHAT_THRESHOLD` and no safety flags.
- **Soft Match (opt‑in)**
  - If type is `soft match` and:
    - `worth_it_score ≥ SOFT_MATCH_NOTIFY_THRESHOLD` and no safety flags.
- **No Match**
  - Otherwise.

### 5.5 Agent “Presentation” Behavior

When a match or soft match is ready to show:

- The user sees a card created by their own agent, e.g.:

> “I found someone nearby who also wants to play tennis this evening. They’re roughly your age, live in your area, and share a few interests like outdoor sports. I think there’s a good chance you’ll get along if you play together today.”

- The explanation:
  - Focuses on *types* of alignment (interests, timing, purpose).
  - Avoids:
    - Directly exposing the other user’s external social handles.
    - Revealing raw imported messages or posts.
    - Sharing any data outside what the other user has agreed can be visible in their in‑app profile.

---

## 6. Architecture Overview

### 6.1 Client (Mobile App)

- Features:
  - Auth & onboarding.
  - Profile & settings.
  - Circle creation and management.
  - Background/foreground location updates.
  - Notifications and match presentation cards.
  - Chat UI with agent suggestions.

- Communication:
  - REST/GraphQL for standard calls.
  - WebSockets for chat & real‑time events.

### 6.2 Backend Services

Logical components:

- **API Gateway**
  - Auth, rate limiting, request routing.

- **User & Profile Service**
  - User accounts, profile data, preferences, permissions.
  - Exposes profile to agent services and to the app (with privacy filtering).

- **Data Ingestion Service**
  - Connects to social networks and external data sources (where allowed).
  - Normalizes and stores raw text, images, events.
  - Writes into raw profile storage.

- **Agent Persona Service**
  - Processes raw data into:
    - Traits, interests, and safety rules.
    - Embeddings and structured fields.
  - Exposes:
    - `simulate_interaction(agentA, agentB, context)`.
    - `suggest_opening_message(match_context)`.

- **Circle Service**
  - Circle CRUD and lifecycle management.
  - Stores semantic data (objective, purpose) and metadata.
  - For location, writes to the Geo service / index.

- **Location & Geo Service**
  - Receives GPS updates from devices.
  - Maintains geospatial index of Circles.
  - Emits collision events to the Matching Engine.

- **Matching Engine**
  - Listens for collision events.
  - Performs semantic matching using embeddings.
  - Calls Agent Persona Service for simulations.
  - Writes Match objects and triggers notifications / chat creation.

- **Chat Service**
  - Chat rooms, messages, attachments.
  - WebSocket layer for real‑time delivery.
  - Hooks for content moderation.

- **Notification Service**
  - Push notifications via APNS/FCM.
  - In‑app notification storage and delivery.

### 6.3 Data Stores

- `user_db` – Users, preferences, auth data.
- `profile_db` – Processed profiles, traits, interests.
- `circle_db` – Circles, purposes, states.
- `geo_index` – Geospatial storage (PostGIS, Redis GEO, etc.).
- `vector_store` – Embeddings for objectives, interests, and selected content.
- `match_db` – Matches, soft match states, scores, audit logs.
- `chat_db` – Chats and messages.

---

## 7. Data Model (Simplified)

```text
User
- id
- display_name
- age (optional, with verification status)
- avatar_url
- locale
- preferences (JSON)
- permissions (JSON)  // location, social integrations, etc.

AgentPersona
- user_id (PK/FK)
- traits (JSON)
- interests_tags (string[])
- interests_embedding (vector)
- safety_rules (JSON)
- communication_style (JSON)

Circle
- id
- user_id
- objective_text
- objective_embedding (vector)
- purpose (string)
- center_lat, center_lon
- radius_m
- start_at, expires_at
- status (enum: active, paused, expired)

Match
- id
- user_a_id, user_b_id
- circle_a_id, circle_b_id
- type (enum: match, soft_match)
- worth_it_score (float)
- status (enum: pending_accept, active, declined, expired)
- explanation_summary (string)  // high-level reason, not raw data
- created_at, updated_at

Chat
- id
- user_a_id, user_b_id
- match_id
- created_at

Message
- id
- chat_id
- sender_user_id
- content (text/json for rich types)
- created_at
- moderation_flags (JSON)
```

---

## 8. Privacy, Safety & Compliance

- **Explicit Consent**
  - Users choose which external data sources are connected.
  - Clear language about how data is used to build the agent.

- **Data Minimization**
  - Store only what is necessary for:
    - Profiling, matching, safety, and explanation.
  - Allow account deletion and data export.

- **Controlled Agent Explanations**
  - Agent “presentations” must not:
    - Reveal personal identifiers beyond what the other user’s profile already exposes.
    - Leak imported content verbatim (e.g., “They posted X on Instagram yesterday”).
  - Explanations describe *patterns and alignment*, not raw underlying data.

- **Safety**
  - Age‑appropriate controls (e.g., 18+ only initially, or strict minor rules).
  - Content moderation on user messages and agent suggestions.
- Rate limiting for matches and conversations to avoid harassment or spam.

---

## 9. Open Questions & Roadmap

### 9.1 Open Questions

- How much profile information is visible in a match card (e.g., approximate age range, high‑level bio) while still respecting privacy constraints?
- Should agents eventually be allowed to propose follow‑up actions (e.g., schedule time, suggest location) directly inside chat?
- How will we evaluate the quality of simulations and “worth it” scores (feedback loop, user ratings, etc.)?

### 9.2 Suggested MVP Scope

- Single region / city rollout with:
  - Basic onboarding + interest questionnaire.
  - One agent persona per user.
  - Multiple Circles per user (objective, radius, duration, purpose).
  - Geospatial matching + semantic matching.
  - Agent‑based simulation for collisions.
  - Match and soft‑match flows with agent presentations.
  - Simple 1:1 chat with agent suggestions.

From this document, the next concrete step is to derive:

- Detailed API contracts for:
  - Circle Service (`createCircle`, `updateCircle`, `listMyCircles`).
  - Matching Engine (`onCollision`, `createMatch`).
  - Agent Persona Service (`simulateInteraction`, `explainMatch`, `suggestOpener`).
- A technical architecture diagram mapping these services and data flows.

---

## Appendix: Original Ideation Notes

The following section captures earlier ideation from `docs/idea.md`. It is preserved here for historical context and inspiration; the main specification for implementation remains the structured design above.

### 1. Core Idea

*Active Circle: tu red social del mundo real a partir de tus RRSS actuales.*

**Concept**

- Users have agent personas informed by their existing digital traces (social media, chats, events).
- Users define Circles: objectives + radius + time window.
- When Circles intersect in the real world, agents simulate multiple scenarios to decide if it is worth prompting the humans to connect.

**What “worth it” means**

- The simulated scenario is successful according to the objective.
- Examples:
  - For a tennis objective: both are available, levels align, they are close enough to meet.
  - For a founder meetup: there is sufficient overlap in domain, stage, and availability.

### 2. Agents & Roles (Ideation View)

**Profile Agent**

- Builds a rich representation of the user from:
  - Images, chats, posts, events.
  - Onboarding questions and explicit goals.
- Learns:
  - Interests and hobbies.
  - Social style and boundaries.
  - Typical schedule and availability windows.

**Interaction Agents**

- Each user has one or more “interaction agents” that:
  - Negotiate with other agents when Circles collide.
  - Ask clarifying questions about goals and constraints.
  - Simulate brief conversations and potential outcomes.
- They operate in the backend; humans do not see these conversations directly.

**Judge Agent**

- Evaluates whether a potential interaction is:
  - Not worth it.
  - Promising, but better later.
  - Strong match, suggest contact now/soon.
- Considers:
  - Goal alignment.
  - Context fit (time, distance, schedule).
  - Social fit (preferences, prior feedback).
  - Novelty (avoid repeating very similar matches).

### 3. User Flow (Narrative)

**Onboarding**

1. Install the app and connect one or more social accounts.
2. The app builds an initial profile from public data and a short quiz.
3. User defines initial Circles:
   - Objective.
   - Radius.
   - Time window.
   - Constraints (if any).

**Background Matching**

1. Phone shares approximate GPS coordinates at a low frequency.
2. When two users come within intersecting Circles:
   - Agents exchange high‑level, anonymized representations of profiles and objectives.
   - Run a short “interview” to refine understanding.
   - Submit notes to the Judge agent.
3. Judge decides whether humans should be prompted.

**Push Notification Examples**

- “Are you interested in playing tennis today or this weekend with an intermediate, friendly player who lives within 300m?”
- “There’s another AI founder nearby looking to meet co‑founders this week. Interested in connecting?”

User options:

- Accept.
- Snooze (not now, ask later).
- Decline (not interested in this type of match).

**Chat & In‑Person**

- If accepted:
  - A private chat opens in the app.
  - Agents may propose:
    - Time suggestions and locations.
    - Conversation starters or a small agenda.
  - When nearby, the app can propose meeting spots:
    - “You’re 200m apart; want directions to meet at the public courts?”

### 4. MVP Architecture Sketch (GPS‑Only)

- **Client**
  - Auth & onboarding.
  - Profile and Circle configuration UI.
  - Background GPS updates (coarse, battery‑friendly).
  - Push notifications and in‑app chat.

- **Backend**
  - Stores user profiles and Circles.
  - Location index for “who is in whose Circle?” queries.
  - Agent runtime to:
    - Represent profiles as embeddings.
    - Run short agent‑to‑agent interviews.
    - Run Judge agent for match quality.
  - Match state machine:
    - Candidate detection → interview → judge → notify → accept/decline → chat.

- **Data & Privacy**
  - Store location at low precision (e.g., geohash) with short retention.
  - Prefer operating on abstracted profile features over raw social content.
  - Allow users to pause all Circles or individual Circles.

### 5. Example Circles (From Early Notes)

**Tennis Circle**

- Objective: “Play tennis with intermediate players.”
- Radius: ~400m, evenings.
- Flow:
  - Another user with matching skill and availability enters the Circle.
  - Agents confirm level, schedule, and intent.
  - Judge: strong match this week.
  - Notification to the challenged user; if accepted, chat opens and agents suggest nearby courts.

**Founder Circle**

- Objective: “Meet AI founders building early‑stage products.”
- Radius: ~2km over the next 7 days.
- Flow:
  - Another founder’s Circle overlaps.
  - Agents discover strong overlap in domain and stage.
  - Judge triggers a contact suggestion.

These ideation notes helped shape the more formal requirements and architecture described in Sections 1–9.
