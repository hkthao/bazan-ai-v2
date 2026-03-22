.PHONY: dev stop logs ingest ingest-pdf ingest-md backup \
        test test-unit test-int coverage lint format typecheck \
        shell-rag pull-model logs-webui list-models \
        shell-webui status tts-voices tts-test tts-test-vi logs-tts \
        pipeline pipeline-dry pipeline-force pipeline-review pipeline-setup \
        weather-test price-test

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

qdrant-ui:
	open http://localhost:6333/dashboard || xdg-open http://localhost:6333/dashboard

qdrant-reset:
	$(COMPOSE) stop qdrant
	docker volume rm bazan-qdrant-data || true
	$(COMPOSE) up -d qdrant
	@echo "Qdrant data cleared and restarted"

# TTS
tts-voices:
	@echo "=== Kokoro TTS voices ==="
	curl -s http://localhost:$${KOKORO_PORT:-8880}/v1/voices \
	  | python3 -c "import sys,json; voices=json.load(sys.stdin).get('voices',[]); [print(f'  {v[\"voice_id\"]:20} {v.get(\"name\",\"\")}') for v in voices]"

tts-test:
	@echo "=== Generating test audio ==="
	curl -s http://localhost:$${KOKORO_PORT:-8880}/v1/audio/speech \
	  -H "Content-Type: application/json" \
	  -d '{"model":"kokoro","input":"Hello, this is Bazan AI coffee assistant. Vietnamese voice coming soon.","voice":"$${KOKORO_DEFAULT_VOICE:-af_heart}","response_format":"wav"}' \
	  --output /tmp/bazan-tts-test.wav \
	  && echo "Saved: /tmp/bazan-tts-test.wav" \
	  && { command -v afplay && afplay /tmp/bazan-tts-test.wav; } \
	  || { command -v aplay && aplay /tmp/bazan-tts-test.wav; } \
	  || echo "Play manually: open /tmp/bazan-tts-test.wav"

tts-test-vi:
	@echo "=== Vietnamese text (English voice — temp) ==="
	curl -s http://localhost:$${KOKORO_PORT:-8880}/v1/audio/speech \
	  -H "Content-Type: application/json" \
	  -d '{"model":"kokoro","input":"Gia ca ca phe hom nay tai Dak Lak la 65 nghin dong mot ky.","voice":"$${KOKORO_DEFAULT_VOICE:-af_heart}","response_format":"wav"}' \
	  --output /tmp/bazan-tts-vi-test.wav \
	  && echo "Saved: /tmp/bazan-tts-vi-test.wav"

logs-tts:
	$(COMPOSE) logs -f kokoro-tts

# Document Pipeline
pipeline:
	cd services/doc-pipeline && uv run python pipeline.py

pipeline-dry:
	cd services/doc-pipeline && uv run python pipeline.py --dry

pipeline-force:
	cd services/doc-pipeline && uv run python pipeline.py --force

pipeline-review:
	cd services/doc-pipeline && uv run python pipeline.py --review

pipeline-setup:
	cd services/doc-pipeline && uv sync
	@echo "Cần điền KB_DETAIL_ID và KB_SUMMARY_ID trong services/doc-pipeline/.env"
	@echo "Lấy ID từ: Open WebUI → Workspace → Knowledge → mở KB → xem URL"

weather-test:
	cd services/functions && \
	  OPENWEATHER_API_KEY=$$(grep OPENWEATHER_API_KEY ../../.env | cut -d= -f2) \
	  uv run python test_weather.py

price-test:

price-test:
	cd services/functions && python3 -c "import sys; sys.path.insert(0, '.'); from price_tool import Tools; t = Tools(); print(t.get_coffee_price('tất cả'))"
