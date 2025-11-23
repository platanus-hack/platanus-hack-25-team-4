# team-4 Platanus Hack Project

**Current project logo:** project-logo.png

<img src="./project-logo.png" alt="Project Logo" width="200" />

Submission Deadline: 23rd Nov, 9:00 AM, Chile time.

Track: ✨ consumer AI

team-4

- Jonán Ortiz ([@jonanortizvega](https://github.com/jonanortizvega))
- Franco Giannoni ([@fagiannoni](https://github.com/fagiannoni))
- Felipe Giannoni ([@FelipeGiannoni](https://github.com/FelipeGiannoni))
- Giorgio Giannoni ([@gegianno](https://github.com/gegianno))
- Sebastián Montagna ([@montanon](https://github.com/montanon))

# Circles – Active Circles Social Network

Circles is an experimental social network built around **Active Circles**: location‑based “intent bubbles” represented by AI agent personas.  
Users create Circles with objectives (free‑text intents), radii, and durations; when Circles collide in the real world, agents simulate scenarios, assess compatibility, and decide whether it is “worth it” to connect the people involved.

- On strong alignment (match), a chat is opened directly.
- On partial alignment (soft match), the non‑objective user is asked to opt in before a chat is created.
- Users never browse nearby people; discovery is fully agent‑driven.

For the full product and system design, see `DESIGN.md`.

---

## Project Status

This repository currently contains early design notes and scaffolding for future Python and TypeScript code.  
The target backend language is **Python 3.12**, and the frontend / tooling will use **TypeScript**.

Guidelines for AI coding agents working in this repo are defined in `AGENTS.md`.

---

## Repository Layout

Current structure (subject to change as implementation evolves):

- `AGENTS.md` – Rules and conventions for AI coding agents.
- `DESIGN.md` – High‑level product and system design for Active Circles.
- `src/` – Placeholder for future application code (Python / TypeScript).
- `pyproject.toml` / `uv.lock` – Python project configuration.

---

## Getting Started (Development)

> Note: Implementation is still in progress. These steps describe the expected workflow as code is added.

### Quick Start with Docker Compose

The easiest way to run both the database and backend is using Docker Compose:

1. **Create a `.env` file in the project root**

   Copy from the example file or create manually:

   ```bash
   cp env.example .env
   ```

   Or create manually with:

   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=circles_db
   POSTGRES_PORT=5432

   NODE_ENV=development
   BACKEND_PORT=3000
   JWT_SECRET=your-super-secret-jwt-key-change-in-production
   ```

2. **Start the services**:

   ```bash
   docker-compose up -d
   ```

   This will start both the PostgreSQL database and the Node.js backend.

3. **Verify the services are running**:

   ```bash
   docker-compose ps
   ```

4. **View logs**:

   ```bash
   docker-compose logs -f backend
   docker-compose logs -f db
   ```

5. **Stop the services**:

   ```bash
   docker-compose down
   ```

The backend will be available at `http://localhost:3000` and the database at `localhost:5432`.

### Local Development Setup

1. **Python environment**

   - Ensure Python **3.12** is available (see `.python-version`).
   - Use your preferred environment manager (e.g. `uv`, `pyenv`, `venv`) to create an environment.

2. **Install Python dependencies**

   - Once dependencies are defined in `pyproject.toml`, install them with:
     - `uv sync` (recommended) or another PEP 621–compatible tool.

3. **TypeScript / Node tooling**

   - Install backend dependencies:

     ```bash
     cd circles/src/backend && npm install
     ```

   - Run in development mode:

     ```bash
     npm run dev
     ```

4. **Running tests**
   - When tests are added, follow the instructions in future docs (e.g. `pytest`, `npm test`).

---

## Contributing

- Follow the guidelines in `AGENTS.md` for coding style, testing, and dependency management.
- Keep changes small and focused, and document any nontrivial design decisions in `DESIGN.md` or a related design note.
