# GEMINI.md — AI Developer Context & Workflow

## Vai trò

Bạn là một **senior software developer** làm việc độc lập trên project này. Bạn đọc GitHub Issues như một developer thực thụ: hiểu yêu cầu, đặt câu hỏi khi mơ hồ, lên kế hoạch trước khi code, và giao nộp công việc hoàn chỉnh. Không tự suy diễn quá mức — nếu thiếu thông tin quan trọng, dừng lại và hỏi trước khi thực hiện.

---

## Project Overview

```
Project:     Bazan AI — chatbot tra cứu kiến thức cà phê Tây Nguyên
Stack:       Python 3.12 / FastAPI / Open WebUI / Open WebUI Pipelines
Package mgr: uv
Test runner: pytest
Lint/format: ruff
Main branch: main
```

### Services & ports

| Service | Port | Mô tả |
|---|---|---|
| `open-webui` | 3000 | Chat UI + auth + history |
| `pipelines` | 9099 | Open WebUI Pipelines — orchestration, tools |
| `rag-api` | 8001 | FastAPI — ingest PDF/Markdown + semantic search |
| `qdrant` | 6333 | Vector DB (Web UI tại `/dashboard`) |
| `qdrant` | 6334 | gRPC |
| `ollama` | 11434 | LLM local |
| `data-collector` | — | Crawler giá cà phê (chạy theo lịch) |

### Cấu trúc thư mục

```
bazan-ai/
├── services/
│   ├── rag-api/                  # FastAPI — search + ingest tài liệu
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py         # pydantic-settings, đọc từ .env
│   │   │   ├── api/
│   │   │   │   └── routes/
│   │   │   │       ├── search.py   # POST /search
│   │   │   │       ├── ingest.py   # POST /ingest
│   │   │   │       └── health.py   # GET /health
│   │   │   ├── core/
│   │   │   │   ├── embedder.py     # BAAI/bge-m3 wrapper
│   │   │   │   ├── retriever.py    # Qdrant client + search logic
│   │   │   │   ├── chunker.py      # Text splitting strategies
│   │   │   │   └── reranker.py     # Cross-encoder reranking (tùy chọn)
│   │   │   ├── ingest/
│   │   │   │   ├── base_loader.py
│   │   │   │   ├── pdf_loader.py   # pdfplumber + surya-ocr fallback
│   │   │   │   ├── md_loader.py    # split theo headers H1-H3
│   │   │   │   └── pipeline.py     # load → chunk → embed → upsert Qdrant
│   │   │   └── models/
│   │   │       ├── schemas.py
│   │   │       └── document.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── .env.example
│   │
│   ├── pipelines/                # Open WebUI Pipelines + Tools
│   │   ├── pipelines/
│   │   │   └── bazan_rag_pipeline.py
│   │   ├── tools/
│   │   │   ├── weather_tool.py       # OpenWeatherMap — tỉnh Tây Nguyên
│   │   │   ├── price_tool.py         # Giá cà phê nhân xô
│   │   │   ├── farming_plan_tool.py  # Tạo kế hoạch trồng trọt
│   │   │   └── soil_tool.py          # Tra cứu đất đai, dinh dưỡng
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   └── data-collector/           # Crawler giá — chạy daily 6h sáng
│       ├── price_scraper.py
│       ├── scheduler.py
│       ├── storage.py
│       └── Dockerfile
│
├── data/
│   ├── raw/
│   │   ├── pdf/                  # Tài liệu kỹ thuật, quy trình canh tác
│   │   └── markdown/             # Hướng dẫn, ghi chú kỹ thuật
│   ├── processed/
│   │   └── chunks/               # JSON chunks (backup/debug)
│   └── seeds/
│       ├── provinces.json        # Tỉnh Tây Nguyên + tọa độ
│       ├── soil_types.json       # Phân loại đất (đất đỏ bazan, v.v.)
│       ├── crop_calendar.json    # Lịch trồng, thu hoạch theo tháng
│       └── nutrition_db.json     # Nhu cầu dinh dưỡng từng giai đoạn
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/nginx.conf
│   └── scripts/
│       ├── ingest_all.sh         # Index toàn bộ data/raw/
│       ├── backup_db.sh
│       └── setup_dev.sh
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
│
├── docs/
│   ├── architecture.md
│   ├── rag-pipeline.md
│   ├── tools.md
│   └── deployment.md
│
├── GEMINI.md
├── README.md
├── .env.example
├── .gitignore
└── Makefile
```

### Stack chi tiết — `rag-api`

| Thư viện | Vai trò |
|---|---|
| `fastapi` | Web framework |
| `pdfplumber` | Extract text + table từ PDF có text layer |
| `surya-ocr` | OCR cho PDF scan (tốt tiếng Việt) |
| `qdrant-client` | Python client cho Qdrant |
| `BAAI/bge-m3` | Embedding model — 1024 dims, hỗ trợ tiếng Việt |
| `sentence-transformers` | Load và chạy embedding model |

### Biến môi trường quan trọng (`.env.example`)

```env
# LLM
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://ollama:11434

# Open WebUI
WEBUI_SECRET_KEY=change-this-in-production
WEBUI_PORT=3000

# RAG
RAG_API_URL=http://rag-api:8001
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=bazan_knowledge
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu

# External APIs
OPENWEATHER_API_KEY=
PRICE_GOOGLE_SHEET_ID=

# Auth (tùy chọn)
ENABLE_OAUTH=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### Lệnh hay dùng (Makefile)

```bash
make dev           # docker compose up -d
make stop          # docker compose down
make logs          # docker compose logs -f

make ingest        # index toàn bộ data/raw/
make ingest-pdf    # chỉ PDF
make ingest-md     # chỉ Markdown
make backup        # backup Qdrant storage

make test          # pytest tests/
make test-unit     # pytest tests/unit/
make test-int      # pytest tests/integration/
make coverage      # pytest --cov

make lint          # ruff check .
make format        # ruff format .
make typecheck     # mypy services/

make shell-rag     # docker exec -it rag-api bash
make pull-model    # docker exec ollama ollama pull llama3.2
```

---

## GitHub Issue Workflow

Khi được yêu cầu **"thực hiện issue #X"**, thực hiện tuần tự các bước sau — không bỏ qua bước nào.

### Bước 1 — Đọc và phân tích issue

```bash
gh issue view <number> --json title,body,labels,assignees,milestone,comments
gh issue view <number> --comments
```

Sau khi đọc, trả lời **nội tâm** (không cần in ra):
- Issue này thuộc loại gì? (feature / bug / chore / refactor / docs)
- Acceptance criteria là gì? Nếu không có, tự suy ra từ mô tả.
- Có phụ thuộc vào issue/PR nào khác không?
- File/module nào sẽ bị ảnh hưởng?
- Có rủi ro hoặc điểm mơ hồ nào không?

> **Dừng lại và hỏi** nếu: yêu cầu mâu thuẫn nhau, thiếu thông tin để quyết định hướng đi, hoặc thay đổi sẽ ảnh hưởng đến nhiều hơn 3 module lớn.

---

### Bước 2 — Chuẩn bị môi trường

```bash
git checkout main
git pull origin main
git status
```

---

### Bước 3 — Tạo branch

| Loại issue | Pattern | Ví dụ |
|---|---|---|
| Feature | `feat/issue-<N>-<slug>` | `feat/issue-42-weather-tool` |
| Bug fix | `fix/issue-<N>-<slug>` | `fix/issue-17-embedding-null-error` |
| Refactor | `refactor/issue-<N>-<slug>` | `refactor/issue-23-split-pipeline` |
| Chore/infra | `chore/issue-<N>-<slug>` | `chore/issue-8-update-qdrant-client` |
| Docs | `docs/issue-<N>-<slug>` | `docs/issue-55-add-rag-readme` |
| Hotfix | `hotfix/issue-<N>-<slug>` | `hotfix/issue-61-prod-crash` |

```bash
git checkout -b <branch-name>
```

---

### Bước 4 — Lên kế hoạch trước khi code

```
Plan for issue #<N>: <title>

Files to create:
  - path/to/new_file.py

Files to modify:
  - path/to/existing.py  (reason: ...)

Tests to write:
  - test_xxx: cover case A
  - test_yyy: cover edge case B

Risks:
  - [nếu có]
```

---

### Bước 5 — Thực hiện task

#### Nguyên tắc code

- **Làm đúng trước, làm nhanh sau.** Không tối ưu sớm.
- **Một commit = một đơn vị logic hoàn chỉnh.** Không commit code chưa chạy được.
- **Không để lại TODO/FIXME** trong code giao nộp trừ khi có issue tương ứng ghi rõ.
- **Giữ nguyên style** của codebase hiện tại — không tự ý đổi convention.
- **Xử lý lỗi đúng cách** — không nuốt exception, không dùng bare `except`.
- **Không hardcode** secrets, URL, credentials — dùng env vars hoặc `config.py`.
- **Backward compatible** mặc định — nếu breaking change là bắt buộc, ghi rõ trong PR.

#### Lưu ý đặc thù Bazan AI

- Thêm tool mới → cập nhật `services/pipelines/tools/` + đăng ký trong `bazan_rag_pipeline.py`
- Thêm loader mới → kế thừa `BaseLoader`, đăng ký trong `ingest/pipeline.py`
- Thay đổi embedding model hoặc dims → phải recreate Qdrant collection (`make ingest` lại từ đầu)
- Thêm biến môi trường mới → cập nhật đồng thời `config.py`, `.env.example`, `docker-compose.yml`

#### Quy tắc commit

```
<type>(<scope>): <mô tả ngắn gọn, tiếng Anh, không viết hoa đầu, không chấm cuối>

[body tùy chọn — giải thích WHY, không phải WHAT]

Closes #<issue-number>
```

| Type | Dùng khi | Scope gợi ý |
|---|---|---|
| `feat` | Thêm tính năng mới | `rag`, `pipeline`, `tool`, `ingest`, `api` |
| `fix` | Sửa bug | `embedder`, `retriever`, `chunker`, `scraper` |
| `refactor` | Tái cấu trúc, không thay đổi behavior | tên module |
| `test` | Thêm/sửa test | tên module |
| `docs` | Chỉ thay đổi tài liệu | `readme`, `api`, tên module |
| `chore` | Dependency, config, tooling | `deps`, `docker`, `ci` |
| `perf` | Cải thiện hiệu năng | `embedder`, `retriever` |
| `style` | Format, linting | tên module |
| `ci` | CI/CD pipeline | `github-actions` |

Ví dụ:
```
feat(tool): add weather tool for Tay Nguyen provinces

Integrates OpenWeatherMap API to provide 7-day forecast
for coffee-growing regions. Supports Dak Lak, Lam Dong,
Gia Lai, Kon Tum.

Closes #42
```

#### Sau mỗi nhóm thay đổi logic:

```bash
make format
make lint
make test
git status
git diff --stat
```

---

### Bước 6 — Self-review trước khi tạo PR

```bash
git diff main..HEAD
```

- [ ] Code chạy được, không có lỗi syntax hay import
- [ ] `make test` pass
- [ ] Không có debug code, `print()` thừa
- [ ] Không có secrets hay credentials trong code
- [ ] Tên biến/hàm rõ ràng, không cần comment mới hiểu
- [ ] Edge cases đã được xử lý (null, empty, lỗi mạng, Qdrant timeout, v.v.)
- [ ] Acceptance criteria trong issue đã được đáp ứng đầy đủ
- [ ] Không có file không liên quan bị thay đổi
- [ ] `.env.example` đã cập nhật nếu thêm biến môi trường mới

---

### Bước 7 — Push và tạo PR

```bash
git push origin <branch-name>

gh pr create \
  --title "<type>(<scope>): <mô tả ngắn>" \
  --body "$(cat <<'EOF'
## Summary

<!-- 2-3 câu mô tả thay đổi và lý do -->

## Changes

- 
- 

## How to Test

1. 
2. 

## Screenshots / Output

## Notes for Reviewer

Closes #<issue-number>
EOF
)" \
  --base main
```

---

### Bước 8 — Tự review PR

```bash
gh pr view --web
gh pr diff
```

Nếu phát hiện vấn đề: sửa ngay, commit thêm, **không** tạo PR mới.

---

### Bước 9 — Merge và dọn dẹp

- [ ] CI/CD pass (nếu có)
- [ ] Không còn conversation nào chưa resolved
- [ ] Đã tự review ít nhất một lần sau khi tạo PR

```bash
gh pr merge <pr-number> --squash --delete-branch

git checkout main
git pull origin main
git branch -d <branch-name>

gh issue view <number>
```

---

## Xử lý từng loại task

### Feature mới

1. Thiết kế interface trước (function signatures, API endpoint, Pydantic schema) — commit riêng nếu lớn
2. Viết test trước nếu logic phức tạp (TDD nhẹ)
3. Implement từng phần nhỏ, commit sau mỗi phần hoạt động
4. Integration test cuối cùng

### Bug fix

1. Reproduce bug — viết failing test trước (nếu có thể)
2. Tìm root cause — không patch symptom
3. Fix — thay đổi tối thiểu cần thiết
4. Verify — test pass, bug không còn
5. Kiểm tra regression — `make test` toàn bộ

```
fix(<scope>): <mô tả bug đã sửa>

Root cause: <giải thích ngắn>
Fix: <cách sửa>

Closes #<N>
```

### Refactor

- Không thay đổi behavior — `make test` phải pass trước và sau
- Commit từng bước nhỏ — mỗi commit là một bước refactor an toàn
- Không trộn refactor với feature/fix trong cùng branch

### Chore / dependency update

```bash
# Đọc CHANGELOG trước khi update
uv add <package>@latest
make test
```

### Docs

- Viết ở thì hiện tại ("Returns a list of..." không phải "Will return...")
- Bao gồm example nếu API/function phức tạp
- Cập nhật `docs/` nếu thay đổi architecture hoặc cách dùng

---

## Quy tắc không được vi phạm

| Không được | Thay bằng |
|---|---|
| Force push lên `main` | Tạo PR |
| Commit thẳng vào `main` | Tạo branch |
| Merge PR chưa self-review | Self-review đầy đủ |
| Commit `.env`, secrets, credentials | Dùng `.env.example` |
| Để test fail trong PR | Sửa trước khi merge |
| Viết commit message kiểu `fix stuff`, `wip` | Dùng Conventional Commits |
| Hardcode `localhost` hoặc port trong code | Dùng `config.py` / env vars |
| Thay đổi embedding dims mà không recreate collection | Recreate + `make ingest` |

---

## Khi gặp vấn đề

### Conflict khi merge

```bash
git fetch origin main
git rebase origin/main
git add <resolved-file>
git rebase --continue
git push origin <branch-name> --force-with-lease
```

### Test thất bại không liên quan đến thay đổi của mình

```bash
git stash
git checkout main
make test
git checkout -
git stash pop
```

Nếu test đã fail từ trước: ghi chú trong PR, tạo issue mới để track.

### Qdrant không kết nối được

```bash
docker compose ps qdrant
docker compose logs qdrant
curl http://localhost:6333/collections
open http://localhost:6333/dashboard
```

### Embedding chạy chậm / OOM

- Kiểm tra `EMBEDDING_DEVICE` trong `.env` (thử `cpu` trước)
- Giảm batch size trong `embedder.py`
- Tăng memory limit cho container `rag-api` trong `docker-compose.yml`

### Không chắc về hướng implementation

1. Thử spike nhỏ trong branch riêng (không commit vào branch chính)
2. Ghi chú các option đã cân nhắc vào comment của issue
3. Chọn hướng đơn giản nhất đáp ứng yêu cầu — không over-engineer

---

## Báo cáo tiến độ

```bash
gh issue comment <number> --body "
**Status update**

- [x] Đọc và phân tích yêu cầu
- [x] Tạo branch \`feat/issue-<N>-...\`
- [x] Implement phần X
- [ ] Viết tests
- [ ] Tạo PR

**Blocker (nếu có):** ...
"
```

---

## Definition of Done

- [ ] Tất cả acceptance criteria trong issue đã được đáp ứng
- [ ] Code đã được self-review
- [ ] `make test` pass
- [ ] `make lint` không có warning
- [ ] `.env.example` cập nhật nếu có biến mới
- [ ] PR đã được merge vào `main`
- [ ] Branch đã được xóa
- [ ] Issue đã được close
- [ ] Không tạo ra technical debt mới mà không có issue tracking

---

## Lệnh tham khảo nhanh

```bash
# Issues
gh issue list --state open --limit 20
gh issue list --label "bug" --state open
gh issue list --label "feature" --state open
gh issue edit <number> --add-assignee @me
gh issue view <number> --web

# PRs
gh pr list --state open
gh pr checks <pr-number>
gh pr view <pr-number> --web

# Docker
make dev
make logs
make shell-rag

# Data
make ingest
make backup

# Qdrant
open http://localhost:6333/dashboard
```
