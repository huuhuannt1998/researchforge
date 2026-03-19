# ResearchForge

> **A local-first autonomous research agent** — give it a one-sentence idea and it searches the literature, designs experiments, writes and runs code, evaluates results, and drafts a full paper — powered entirely by a local LLM running on your own machine.

---

## What is ResearchForge?

Academic research involves juggling dozens of tools that don't talk to each other: reference managers, spreadsheets for experiment tracking, word processors, citation checkers, and email threads with co-authors. ResearchForge replaces that fragmented stack with a single, self-hosted workspace that can drive the entire research lifecycle autonomously.

Starting from a one-sentence idea, ResearchForge can:

1. **Search the internet** for relevant papers via Semantic Scholar (free, no API key)
2. **Extract and synthesise** key findings, methods, datasets, and limitations using an LLM
3. **Design experiments** — propose hypotheses, baselines, datasets, metrics, and ablations grounded in the literature
4. **Generate and execute code** — write a Python experiment script, run it locally, and auto-fix failures with the LLM
5. **Evaluate results** — parse stdout, build comparison tables, verify hypotheses
6. **Write the paper** — produce all seven sections (Abstract through Conclusion) from the accumulated artifacts

All of this runs through a five-stage agent pipeline that you can trigger with a single click or run one stage at a time. Every artifact (literature items, evidence cards, experiment plan, code output, draft sections) is stored as structured, queryable data — nothing gets lost in a chat window.

The system is **local-first**: your data never leaves your machine. The LLM runs in [LM Studio](https://lmstudio.ai) (or any OpenAI-compatible local server). There are no subscriptions, no rate limits, and no vendor lock-in.

---

## Core Design Principles

### 1. Structured over freeform
Every stage of the workflow produces structured, queryable artifacts (JSON arrays of hypotheses, evidence cards with typed fields, metric tables, draft sections per paper section) rather than unstructured prose blobs. This makes it possible to query, visualise, and export the research record programmatically.

### 2. Vertical slices, not horizontal layers
Each major feature is a self-contained vertical slice with its own data model, API endpoints, and UI components. Slices are built incrementally; each ships end-to-end before the next begins.

### 3. The LLM drives, the researcher steers
The autonomous pipeline does the heavy lifting — searching papers, writing code, drafting sections. Researchers review and edit every artifact rather than accepting LLM output blindly. All structured outputs (experiment plans, evidence cards, draft sections) are editable through the same UI used when working manually.

### 4. Every claim has a source
Evidence cards are first-class objects. A claim made in a paper draft can be traced back to a specific quote from a specific paper, with a confidence score and supporting metrics attached.

### 5. Fail-safe execution
The code agent auto-retries on execution failure: if the generated script crashes, the error is fed back to the LLM for a fix before the second attempt. Pipeline stages are tracked individually so a failure in one stage doesn't silently corrupt others.

---

## Architecture

```
researchforge/
├── backend/                FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16
│   ├── app/
│   │   ├── models/         SQLAlchemy ORM models (8 tables)
│   │   ├── schemas/        Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── agents/     5 autonomous agent modules (one per pipeline stage)
│   │   │   ├── llm_service.py        LM Studio OpenAI-compatible client
│   │   │   ├── search_service.py     Semantic Scholar paper search
│   │   │   ├── pipeline_service.py   PipelineRun CRUD
│   │   │   ├── literature_service.py
│   │   │   └── experiment_service.py
│   │   ├── routers/        FastAPI route handlers
│   │   └── main.py         App factory, CORS, lifespan, HTTP client shutdown
│   ├── alembic/            Database migrations
│   └── tests/              pytest integration tests (53 tests, TestClient + test DB)
│
├── frontend/               Next.js 16 · React 19 · TypeScript · Tailwind CSS v4
│   └── src/
│       ├── app/            App Router pages
│       ├── components/
│       │   ├── pipeline/   PipelineTab — stage cards, polling, logs viewer
│       │   ├── literature/ LiteratureTab + sub-components
│       │   ├── experiments/ExperimentPlanTab
│       │   └── ui/         Button, Card, Input, Spinner, StatusBadge…
│       └── lib/            API client, types, utilities
│
├── storage/                Local file storage (PDFs + generated code — git-ignored)
│   └── projects/{id}/
│       ├── literature/
│       └── code/           Generated experiment scripts + output files
│
└── docker-compose.yml      PostgreSQL 16 container
```

### Data model (8 tables)

```
projects
  └── research_questions      (structured RQ with hypotheses + novelty claim)
  └── literature_items        (papers from manual import or agent discovery)
       └── evidence_cards     (typed claims with source quotes + confidence)
  └── experiment_plans        (hypotheses, baselines, datasets, metrics, ablations…)
  └── draft_sections          (full paper sections — abstract through conclusion)
  └── review_reports          (simulated peer review with structured critique)
  └── pipeline_runs           (per-stage execution record with logs + result_data)
```

### Agent pipeline

Each stage is an independent async function that reads from and writes to the database. Stages can be triggered individually or run sequentially end-to-end.

```
┌───────────────────────────────────────────────────────────────┐
│                     AI Research Pipeline                      │
│                                                               │
│  📚 Literature  →  🔬 Design  →  💻 Code  →  📊 Eval  →  ✍️ Write │
│                                                               │
│  For each stage:                                              │
│  1. Create PipelineRun record (status: pending)               │
│  2. Run agent in background thread (status: running)          │
│  3. Write artifacts to DB (LiteratureItems, ExperimentPlan…)  │
│  4. Mark completed / failed with logs + result_data           │
└───────────────────────────────────────────────────────────────┘
```

| Stage | Agent | Reads | Writes |
|---|---|---|---|
| **Literature** | `literature_agent.py` | Project title + research question | `LiteratureItem` rows, `EvidenceCard` rows, synthesis in `result_summary` |
| **Design** | `design_agent.py` | Literature synthesis + paper summaries | Upserts `ExperimentPlan` |
| **Code** | `code_agent.py` | `ExperimentPlan` | Python script to `storage/projects/{id}/code/`, execution stdout/stderr in `result_data` |
| **Evaluation** | `evaluation_agent.py` | Code stdout + experiment plan | Results table, hypothesis verdicts, findings in `result_data` |
| **Writing** | `writing_agent.py` | All prior artifacts | 7 `DraftSection` rows (abstract → conclusion) |

### API surface

```
# Projects
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}
GET    /api/projects/{id}/research-question
POST   /api/projects/{id}/research-question
PATCH  /api/projects/{id}/research-question/{rq_id}

# Literature
GET    /api/projects/{id}/literature/items/
POST   /api/projects/{id}/literature/items/
GET    /api/projects/{id}/literature/items/{item_id}
PATCH  /api/projects/{id}/literature/items/{item_id}
DELETE /api/projects/{id}/literature/items/{item_id}
POST   /api/projects/{id}/literature/items/{item_id}/upload-pdf
POST   /api/projects/{id}/literature/items/{item_id}/extract
GET    /api/projects/{id}/literature/evidence/
POST   /api/projects/{id}/literature/evidence/
GET    /api/projects/{id}/literature/evidence/{card_id}
PATCH  /api/projects/{id}/literature/evidence/{card_id}
DELETE /api/projects/{id}/literature/evidence/{card_id}

# Experiments
GET    /api/projects/{id}/experiments/
POST   /api/projects/{id}/experiments/
GET    /api/projects/{id}/experiments/{plan_id}
PATCH  /api/projects/{id}/experiments/{plan_id}
DELETE /api/projects/{id}/experiments/{plan_id}

# AI Pipeline
GET    /api/projects/{id}/pipeline/                    list all runs (optional ?stage=)
GET    /api/projects/{id}/pipeline/{run_id}            get run details
POST   /api/projects/{id}/pipeline/{stage}/run         trigger one stage
POST   /api/projects/{id}/pipeline/run-all             trigger all 5 stages sequentially
```

Interactive docs: `http://localhost:8000/docs`

---

## Feature Status

| Module | Description | Status |
|---|---|---|
| **Project Dashboard** | Create and manage research projects | ✅ Complete |
| **Research Question** | Structured hypotheses, assumptions, novelty claim | ✅ Complete |
| **Literature Workspace** | Manual import, PDF upload, AI extraction, evidence cards | ✅ Complete |
| **Experiment Planner** | Hypotheses, baselines, datasets, metrics, ablations — auto-saving editor | ✅ Complete |
| **🤖 AI Pipeline** | Autonomous 5-stage agent: search → design → code → eval → write | ✅ Complete |
| **Writing Workspace** | Edit AI-generated draft sections, LaTeX export | 🔜 Slice 5 |
| **Reviewer Arena** | Simulated peer review with structured critique | 🔜 Slice 6 |

---

## Quick Start

### Prerequisites

- **Docker** — for PostgreSQL
- **Node.js 20+** — for the frontend
- **Python 3.11+** — for the backend
- **[LM Studio](https://lmstudio.ai)** *(optional, for the AI pipeline)* — load any model and start the local server on `localhost:1234`

### One-command startup (after first-time setup)

```bash
./dev.sh
```

### First-time setup

#### 1 — Start the database

```bash
docker compose up -d
```

#### 2 — Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

#### 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

| Service | URL |
|---|---|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| LM Studio (local LLM) | http://localhost:1234 |

### Configuring the LLM

The backend reads LLM settings from environment variables (or a `.env` file in `backend/`):

```env
LLM_BASE_URL=http://localhost:1234/v1   # LM Studio default
LLM_MODEL=default                       # model name shown in LM Studio
LLM_TIMEOUT=300                         # seconds — local models can be slow
```

Any OpenAI-compatible server works (Ollama, llama.cpp, vLLM, etc.) — just change `LLM_BASE_URL`.

---

## Development

### Run tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

53 tests across 4 test files. Uses a dedicated `researchforge_test` PostgreSQL database. The test suite creates and tears down the schema automatically. Agent tests mock the LLM and Semantic Scholar calls — no external services needed.

### Project conventions

- **Services are pure**: routers call service functions; service functions only take a `db: Session` + typed inputs and return ORM objects. No business logic in routers.
- **Agents are async**: each agent module exports a single `async def run(db, project_id, run_record)` coroutine. The router runs it in a background thread with its own DB session so it doesn't block the request.
- **Schemas mirror models**: every ORM model has a corresponding `*Create`, `*Update`, and `*Out` Pydantic schema. `*Out` schemas use `model_config = {"from_attributes": True}`.
- **Frontend API client**: all API calls go through `src/lib/api.ts`. No raw `fetch` in components.
- **Auto-save pattern**: editors debounce changes (1.2 s) and call PATCH automatically — no Save button required.
- **Pipeline polling**: the `PipelineTab` polls every 3 seconds while any run is in `pending` or `running` state, and stops automatically when all runs settle.

### Swapping the LLM provider

The entire pipeline talks to the LLM through two functions in `backend/app/services/llm_service.py`:

```python
await llm_service.chat(messages, temperature=0.7, max_tokens=4096)
await llm_service.chat_json(messages, temperature=0.3)   # enforces JSON output
```

To switch from LM Studio to another provider, change `LLM_BASE_URL` (and optionally `LLM_MODEL`) in your `.env`. The agent code is provider-agnostic.

### Adding a manual extraction backend

Replace the body of `backend/app/services/extraction_service.py`:

```python
def extract_from_pdf(pdf_path: str) -> ExtractionResult:
    # Swap stub for PyMuPDF + your LLM of choice
    ...

def extract_from_url(url: str) -> ExtractionResult:
    # Swap stub for a web scraper + your LLM of choice
    ...
```

The `ExtractionResult` dataclass interface is stable — all callers use it unchanged.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.135, Python 3.13 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic 1.18 |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| HTTP client | httpx (async — LLM + Semantic Scholar calls) |
| Local LLM | LM Studio (OpenAI-compatible API at `localhost:1234`) |
| Paper search | Semantic Scholar Graph API v1 (free, no API key) |
| Frontend | Next.js 16, React 19, TypeScript |
| Styling | Tailwind CSS v4 (custom components, no UI library) |
| Testing | pytest, FastAPI TestClient, unittest.mock |
