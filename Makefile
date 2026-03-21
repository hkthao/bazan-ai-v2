.PHONY: dev stop logs ingest ingest-pdf ingest-md backup 
        test test-unit test-int coverage lint format typecheck 
        shell-rag pull-model logs-webui list-models 
        shell-webui status

COMPOSE=docker compose -f infra/docker-compose.yml

# Docker
dev:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

logs-webui:
	$(COMPOSE) logs -f open-webui

status:
	$(COMPOSE) ps

# Data
ingest:
	bash infra/scripts/ingest_all.sh

ingest-pdf:
	bash infra/scripts/ingest_all.sh --type pdf

ingest-md:
	bash infra/scripts/ingest_all.sh --type markdown

backup:
	bash infra/scripts/backup_db.sh

# Testing
test:
	pytest tests/

test-unit:
	pytest tests/unit/

test-int:
	pytest tests/integration/

coverage:
	pytest --cov=services --cov-report=html tests/

# Code quality
lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy services/

# Utils
shell-rag:
	$(COMPOSE) exec rag-api bash

shell-webui:
	$(COMPOSE) exec open-webui bash

pull-model:
	ollama pull $(OLLAMA_MODEL)

list-models:
	ollama list