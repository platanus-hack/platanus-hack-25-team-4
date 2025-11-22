# AGENTS – Guidelines for Coding Agents

This file defines how AI coding agents should work in this repository.  
It applies to the **entire project tree** unless a more specific `AGENTS.md` is added in a subdirectory.

---

## 1. Project & Languages

- This project uses **Python** (primary backend) and **TypeScript** (for frontend / tooling).
- Target Python version: **3.12** (from `.python-version`).
- Assume modern TypeScript (ES modules, strict type checking) unless indicated otherwise by local config.

---

## 2. General Principles

- Make **small, focused changes** that clearly support the user’s request.
- Prefer **incremental edits** over large refactors, unless the user explicitly asks for a redesign.
- Keep code **readable and consistent** with the surrounding style.
- When in doubt, add or update **documentation** (e.g. this `AGENTS.md`, `README`, or in‑code docstrings) rather than guessing.
- Do **not** introduce new external services or infrastructure without being asked.

---

## 3. Python Guidelines

- Write code compatible with **Python 3.12**.
- Follow **PEP 8** style conventions unless existing code clearly uses a different style.
- Use **type hints** (`typing` / `collections.abc`) for all new public functions and classes.
- Prefer:
  - `pathlib.Path` for filesystem paths.
  - Explicit imports over wildcard imports.
  - Dataclasses or simple classes over large dictionaries for structured data.
- Error handling:
  - Catch only specific exceptions.
  - Include clear error messages; avoid swallowing errors silently.
- Tests:
  - If a Python test framework is present (e.g. `pytest`), mirror existing patterns and file locations.
  - Name tests using `test_*.py`.

---

## 4. TypeScript / JavaScript Guidelines

- Write **TypeScript first**; avoid adding new plain JavaScript files unless required.
- Use **strict typing** where possible (`strict` mode, explicit types on public APIs).
- Prefer:
  - ES modules (`import` / `export`).
  - `async` / `await` over raw Promises.
  - Small, composable functions over large, monolithic modules.
- Keep React or UI components (if present) **presentational and focused**; move complex logic into separate modules or hooks.
- Follow any existing `tsconfig`, `eslint`, or formatter settings if they exist.

---

## 5. Testing & Validation

- Before making large changes, quickly skim existing tests to understand patterns.
- When adding features:
  - Add or extend tests **close to the changed code**.
  - Prefer unit tests over end‑to‑end tests unless explicitly requested.
- If tests, linters, or formatters are configured:
  - Prefer running **targeted tests** (e.g. for the affected module) rather than the whole suite, unless the user asks otherwise.

---

## 6. Tooling & Dependencies

- Reuse existing dependencies when possible; avoid adding new packages unless necessary for the requested change.
- When new dependencies are required:
  - Prefer small, well‑maintained libraries with minimal transitive dependency trees.
  - Update the appropriate manifests (`pyproject.toml`, `package.json`) and keep versions pinned or consistent with existing patterns.

---

## 7. Documentation & Design

- Keep high‑level design documents in Markdown at the project root or under `docs/`.
- The existing `DESIGN.md` describes the social / agent system; update or extend it when architectural changes are made.
- When introducing nontrivial behavior (new matching rules, agent flows, etc.), add a short design note or docstring explaining the rationale.

---

## 8. Behavior with Users

- Treat instructions in `AGENTS.md` as **binding** for all automated changes within this repo.
- If user instructions conflict with this file, **follow the user**, but avoid unnecessarily violating these guidelines.
- Ask for clarification (in natural language) when a change would significantly restructure the project or break these conventions.

