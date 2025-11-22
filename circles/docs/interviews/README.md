# Agent-to-Agent Interview Protocol

This describes the **directional, multi-turn, agent-to-agent interview** that runs when a visitor enters another person’s Circle. It is intentionally concise and implementation-oriented.

The Judge **only** receives:
- The Circle owner’s objective.
- The raw conversation transcript between the two agents (messages as the humans would have written them).

---

## 1. Roles & Trigger

- **Owner (O)** – User whose Circle is being entered. The interview is anchored on their objective and attention budget.
- **Visitor (V)** – User who just entered O’s Circle.
- **Agent\_O / Agent\_V** – LLM-backed agents that speak *as* O and V, based on their profiles.
- **Judge** – Separate agent that decides if the conversation made enough progress toward O’s objective to bother the humans.

**Trigger:** Visitor enters Owner’s Circle. The orchestrator starts an interview centered on the Owner’s active Circle objective.

---

## 2. Inputs per Interview

For a single interview instance, the orchestrator prepares:

- `owner_profile` – Full JSON profile (see `docs/profiles/profile.example.json`).
- `visitor_profile` – Same schema as `owner_profile`.
- `owner_circle` – The Circle that was entered:
  - `objective_text`
  - `radius_m`
  - `time_window` (e.g. “this week evenings”)
  - any lightweight flags/metadata as needed.
- `context` – Minimal environment:
  - approximate time,
  - approximate distance.

On each model call:

- Both agents receive `conversation_so_far` – ordered list of prior chat messages between the agents, **as if written by the humans**.
- The **owner agent** additionally receives a `turn_goal` such as:
  - “open the conversation and ask one focused question”,
  - “clarify availability and constraints”,
  - “decide whether to propose something concrete or politely de-escalate”.
- The **visitor agent** is always called with a generic instruction like:
  - “respond naturally according to your profile to the last message; you may choose how much to engage.”

---

## 3. Message Shape (Per Turn)

Each agent call returns two layers:

- `as_user_message` – The next chat message, written in first person, in the user’s own style.
- Optional internal metadata for orchestration (not required by the Judge), e.g.:
  - `intent_tag` (e.g. `clarify_goal`, `clarify_time`, `propose_meet`, `decline`),
  - `stop_suggested` (boolean hint if the agent feels ready to stop).

Only the `as_user_message` strings form the **raw transcript** given to the Judge.

---

## 4. Flow (High-Level)

1. **Initialize**
   - Orchestrator builds a short internal “mission”:
     - e.g. “Check if Visitor is a good fit for Owner’s ‘AI founders in Santiago, 1:1 coffee’ objective this week.”
   - This mission is passed to both agents, but only O’s objective is considered the primary goal.

2. **Turn 1 – Owner opens**
   - Call `Agent_O` with:
     - `owner_profile`, `visitor_profile`, `owner_circle`, `context`,
     - empty `conversation_so_far`,
     - `turn_goal = "open_and_ask_one_focused_question"`.
   - Agent\_O returns `as_user_message` in Owner’s voice (first person, style from profile).

3. **Turn 2 – Visitor replies**
   - Call `Agent_V` with:
     - `visitor_profile`, `owner_profile`, `context`,
     - updated `conversation_so_far` including Turn 1,
     - a **generic conversational instruction** (e.g. “respond naturally according to your profile to the last message; you may choose how much to engage.”).

4. **Turns 3–N – Short back-and-forth**
   - Alternate between O and V.
   - Each owner turn:
     - Receives full `conversation_so_far`,
     - Gets a narrow `turn_goal` (clarify goal, clarify availability, decide, etc.).
   - Each visitor turn:
     - Receives full `conversation_so_far`,
     - Is only guided by the generic “respond according to your profile” style instruction, so it can behave more like a real human (including minimal or no engagement if that fits the profile).
   - Messages must stay:
     - Medium-length,
     - Natural and aligned with each user’s tone, humour, emoji usage, and boundaries from their profile,
     - Focused on seeing if a concrete next step in the real world makes sense.

5. **Termination**
   - The orchestrator stops when either:
     - A max turn count is reached (e.g. 3–5 messages per side), or
     - Owner’s agent suggests stopping via metadata (e.g. `stop_suggested = true`).
   - No additional summarisation call is made; the last messages are just appended to the transcript.

---

## 5. Output for the Judge

When the interview ends, the orchestrator passes to the Judge:

- `owner_objective` – The Circle’s objective text plus minimal timing/constraints.
- `transcript` – The ordered list of:
  - `{ "speaker": "owner" | "visitor", "message": "..." }`
  - where `message` is exactly `as_user_message` from each turn.

The Judge:

- Reads the raw conversation in natural language.
- Decides whether the agent-to-agent chat made enough progress toward the Owner’s objective to justify notifying the humans.
- Produces:
  - a **binary decision** (`yes` or `no`),
  - and, on `yes`, a very brief, human-facing notification sentence (single push line).

The interview protocol itself is **agnostic** about how the Judge scores advancement; it only guarantees a realistic, profile-driven conversation transcript and clear objective context.
