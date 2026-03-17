# ResearchForge

> **A local-first research operating system** — turn a raw idea into a submission-ready paper through structured workflows, AI-assisted analysis, experiment management, and reviewer simulation.

---

## What is ResearchForge?

Academic research involves juggling dozens of tools that don't talk to each other: reference managers, spreadsheets for experiment tracking, word processors, citation checkers, and email threads with co-authors. ResearchForge replaces that fragmented stack with a single, self-hosted workspace purpose-built for the full research lifecycle.

Starting from a one-sentence idea, ResearchForge guides a researcher through every stage — literature review, experiment design, writing, and peer-review simulation — keeping all artifacts (PDFs, evidence cards, hypothesis logs, draft sections) version-tracked in one place and linked back to the originating research questions.

The system is **local-first**: your data never leaves your machine unless you choose to deploy it. There are no subscriptions, no rate limits, and no vendor lock-in.

---

## Core Design Principles

### 1. Structured over freeform
Every stage of the workflow produces structured, queryable artifacts (JSON arrays of hypotheses, evidence cards with typed fields, metric tables) rather than unstructured prose blobs. This makes it possible to later query, visualise, and export the research record programmatically.

### 2. Vertical slices, not horizontal layers
Each major feature (Literature, Experiments, Writing, Review) is a self-contained vertical slice with its own data model, API endpoints, and UI components. Slices are built incrementally; each one ships end-to-end before the next begins.

### 3. AI as an accelerator, not a crutch
AI extraction (paper summarisation, method/dataset/metric identification) runs as a pipeline that populates structured fields — researchers review and edit the output rather than accepting it blindly. The extraction interface is a clean stub today; swapping in a real LLM requires changing one function body.

### 4. Every claim has a source
Evidence cards are first-class objects. A claim made in a paper draft can be traced back to a specific quote from a specific paper, with a confidence score and supporting metrics attached.

---

## Architecture

```
researchforge/
├── backend/                FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16
│   ├── app/
│   │   ├── models/         SQLAlchemy ORM models (7 tables)
│   │   ├── schemas/        Pydantic v2 request/response schemas
│   │   ├── services/       Business logic (pure functions over DB session)
│   │   ├── routers/        FastAPI route handlers
│   │   └── main.py         App factory, CORS, lifespan
│   ├── alembic/            Database migrations
│   └── tests/              pytest integration tests (TestClient + test DB)
│
├── frontend/               Next.js 16 · React 19 · TypeScript · Tailwind CSS v4
│   └── src/
│       ├── app/            App Router pages
│       ├── components/     UI primitives + domain components
│       └── lib/            API client, types, utilities
│
├── storage/                Local file storage (PDFs — git-ignored)
│   └── projects/{id}/
│       └── literature/
│
└── docker-compose.yml      PostgreSQL 16 container
```

### Data model (7 tables)

```
projects
  └── research_questions      (structured RQ with hypotheses + novelty claim)
  └── literature_items        (imported papers with extracted metadata)
       └── evidence_cards     (typed claims with source quotes + confidence)
  └── experiment_plans        (hypotheses, baselines, datasets, metrics, ablations…)
  └── draft_sections          (writing workspace — Slice 4)
  └── review_reports          (reviewer simulation — Slice 5)
```

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
```

Interactive docs: `http://localhost:8000/docs`

---

## Feature Status

| Module | Description | Status |
|---|---|---|
| **Project Dashboard** | Create and manage research projects | ✅ Complete |
| **Research Question** | Structured hypotheses, assumptions, novelty claim | ✅ Complete |
| **Literature Workspace** | Import papers, PDF upload, AI extraction stub, evidence cards | ✅ Complete |
| **Experiment Planner** | Hypotheses, baselines, datasets, metrics, ablations, risks — auto-saving editor | ✅ Complete |
| **Writing Workspace** | Structured draft sections linked to evidence | 🔜 Slice 4 |
| **Reviewer Arena** | Simulated peer review with structured critique | 🔜 Slice 5 |

---

## Quick Start

### Prerequisites

- Docker (for PostgreSQL)
- Node.js 20+
- Python 3.11+

### 1 — Start the database

```bash
docker compose up -d
```

### 2 — Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # edit DATABASE_URL if needed
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3 — Frontend

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

---

## Development

### Run tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Tests use a dedicated `researchforge_test` PostgreSQL database. The test suite creates and tears down the schema automatically.

### Project conventions

- **Services are pure**: routers call service functions; service functions only take a `db: Session` + typed inputs and return ORM objects. No business logic in routers.
- **Schemas mirror models**: every ORM model has a corresponding `*Create`, `*Update`, and `*Out` Pydantic schema. `*Out` schemas use `model_config = {"from_attributes": True}`.
- **Frontend API client**: all API calls go through `src/lib/api.ts`. No raw `fetch` in components.
- **Auto-save pattern**: editors debounce changes (1.2 s) and call PATCH automatically — no Save button required.

### Adding a real extraction backend

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
| Frontend | Next.js 16, React 19, TypeScript |
| Styling | Tailwind CSS v4 (custom components, no UI library) |
| Testing | pytest, FastAPI TestClient |
