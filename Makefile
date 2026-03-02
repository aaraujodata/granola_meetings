.DEFAULT_GOAL := help
COMPOSE := docker compose

# ─── Docker targets ──────────────────────────────────────────────

.PHONY: up
up: ## Start all services (redis, backend, worker, frontend)
	$(COMPOSE) up --build -d

.PHONY: down
down: ## Stop all services and remove containers
	$(COMPOSE) down

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE) restart

.PHONY: logs
logs: ## Tail logs from all services (Ctrl-C to exit)
	$(COMPOSE) logs -f

.PHONY: logs-backend
logs-backend: ## Tail backend API logs
	$(COMPOSE) logs -f backend

.PHONY: logs-worker
logs-worker: ## Tail ARQ worker logs
	$(COMPOSE) logs -f worker

.PHONY: logs-frontend
logs-frontend: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

.PHONY: build
build: ## Rebuild all Docker images without cache
	$(COMPOSE) build --no-cache

.PHONY: ps
ps: ## Show running containers and their status
	$(COMPOSE) ps

.PHONY: clean
clean: ## Stop services, remove containers, volumes, and build cache
	$(COMPOSE) down -v --rmi local
	rm -rf web/frontend/.next

# ─── Local development (no Docker) ──────────────────────────────

.PHONY: dev
dev: ## Start all services locally (requires 3 terminal tabs)
	@echo "Start these in separate terminals:"
	@echo ""
	@echo "  1. redis-server"
	@echo "  2. cd web/backend && uvicorn app.main:app --reload --port 8000"
	@echo "  3. cd web/backend && python -m arq app.worker.WorkerSettings"
	@echo "  4. cd web/frontend && npm run dev"
	@echo ""
	@echo "Or use: make dev-backend, make dev-worker, make dev-frontend"

.PHONY: dev-backend
dev-backend: ## Start FastAPI backend locally (port 8000)
	cd web/backend && uvicorn app.main:app --reload --port 8000

.PHONY: dev-worker
dev-worker: ## Start ARQ worker locally (processes queued jobs)
	cd web/backend && python -m arq app.worker.WorkerSettings

.PHONY: dev-frontend
dev-frontend: ## Start Next.js frontend locally (port 3000)
	cd web/frontend && npm run dev

.PHONY: install
install: ## Install all dependencies (Python + Node)
	pip install -r requirements.txt
	pip install -r web/backend/requirements.txt
	cd web/frontend && npm install

# ─── Pipeline shortcuts ─────────────────────────────────────────

.PHONY: export
export: ## Run meeting export pipeline
	python granola_pipeline.py export --all

.PHONY: index
index: ## Rebuild search index
	python granola_pipeline.py index --rebuild

.PHONY: sync
sync: ## Full pipeline: export + index + process
	python granola_pipeline.py sync

.PHONY: status
status: ## Show token and database stats
	python granola_pipeline.py status

# ─── Video (Remotion) ────────────────────────────────────────────

.PHONY: video-studio
video-studio: ## Open Remotion Studio for the promo video
	cd video && npx remotion studio

.PHONY: render-video
render-video: ## Render the promo video to video/out/promo.mp4
	cd video && npx remotion render PromoVideo out/promo.mp4

# ─── SSL / Corporate proxy ────────────────────────────────────────

.PHONY: setup-ssl
setup-ssl: ## Export corporate CA certs from macOS keychain for Docker (Zscaler/NortonLifeLock)
	@mkdir -p .ca-certs
	@echo "Searching macOS keychain for corporate CA certificates..."
	@security find-certificate -a -c "NortonLifeLock" -p /Library/Keychains/System.keychain > .ca-certs/corporate-ca.pem 2>/dev/null \
		&& echo "Exported $$(grep -c 'BEGIN CERTIFICATE' .ca-certs/corporate-ca.pem) certificate(s) to .ca-certs/corporate-ca.pem" \
		|| (echo "No NortonLifeLock/Zscaler CA found in system keychain." && echo "If you have a different corporate CA, copy the .pem file to .ca-certs/ manually." && rm -f .ca-certs/corporate-ca.pem)
	@echo ""
	@echo "Run 'make down && make up' to rebuild containers with the CA bundle."

# ─── Help ────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
