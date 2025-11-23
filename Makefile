.PHONY: help up down logs ps restart db-migrate db-deploy clean build test lint

# Default target
help:
	@echo "Circles Development Commands"
	@echo "============================="
	@echo ""
	@echo "Docker Compose:"
	@echo "  make up                 Start all services (db, redis, backend)"
	@echo "  make down               Stop all services"
	@echo "  make restart            Restart all services"
	@echo "  make ps                 Show running services"
	@echo "  make logs               Follow backend logs"
	@echo "  make logs-db            Follow database logs"
	@echo "  make logs-all           Follow all logs"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make db-status          Show migration status"
	@echo "  make db-migrate         Create a new migration (interactive)"
	@echo "  make db-baseline        Create baseline migration from current DB state"
	@echo "  make db-deploy          Apply pending migrations to DB"
	@echo "  make db-reset           Reset database (drop and recreate)"
	@echo ""
	@echo "Development:"
	@echo "  make build              Build backend Docker image"
	@echo "  make shell-backend      Open shell inside backend container"
	@echo "  make shell-db           Open psql shell in database"
	@echo "  make test               Run backend tests"
	@echo "  make lint               Run linters"
	@echo "  make clean              Remove containers and volumes"
	@echo ""

# Compose helper
COMPOSE := docker compose --env-file ./circles/src/backend/.env

# ============ Docker Compose =============

up:
	$(COMPOSE) up -d
	@echo "✓ Services started. Backend: http://localhost:3000"

down:
	$(COMPOSE) down

restart: down up

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f backend

logs-db:
	$(COMPOSE) logs -f db

logs-all:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build --no-cache

# ============ Database Migrations =============

db-status:
	$(COMPOSE) exec backend npx prisma migrate status

db-migrate:
	@echo "Creating new migration (interactive)..."
	@echo "Note: Set schema first in circles/src/backend/prisma/schema.prisma"
	$(COMPOSE) exec -it backend npx prisma migrate dev

db-baseline:
	@echo "Creating baseline migration from current database..."
	@TS=$$(date +%Y%m%d%H%M%S); \
	DIR=/app/prisma/migrations/$${TS}_baseline; \
	$(COMPOSE) exec backend mkdir -p "$${DIR}"; \
	$(COMPOSE) exec backend npx prisma migrate diff --from-empty --to-url "$$DATABASE_URL" --script > ./circles/src/backend/prisma/migrations/$${TS}_baseline/migration.sql; \
	echo "✓ Baseline migration created: circles/src/backend/prisma/migrations/$${TS}_baseline/"

db-deploy:
	$(COMPOSE) exec backend npx prisma migrate deploy
	@echo "✓ Migrations applied"

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) exec backend npx prisma migrate reset --force; \
		echo "✓ Database reset"; \
	else \
		echo "Cancelled"; \
	fi

# ============ Development =============

shell-backend:
	$(COMPOSE) exec backend sh

shell-db:
	@echo "Connecting to PostgreSQL..."
	@docker exec -it circles-db psql -U $$(grep POSTGRES_USER ./circles/src/backend/.env | cut -d= -f2) -d $$(grep POSTGRES_DB ./circles/src/backend/.env | cut -d= -f2)

test:
	$(COMPOSE) exec backend npm test

lint:
	$(COMPOSE) exec backend npm run lint

clean:
	$(COMPOSE) down -v
	@echo "✓ All containers and volumes removed"

