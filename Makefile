.PHONY: dev stop logs ingest ingest-pdf ingest-md backup \
        test test-unit test-int coverage lint format typecheck \
        shell-rag pull-model

# Docker
dev:
	docker compose -f infra/docker-compose.yml up -d

stop:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

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
	docker compose -f infra/docker-compose.yml exec rag-api bash

pull-model:
	docker compose -f infra/docker-compose.yml exec ollama ollama pull llama3.2
