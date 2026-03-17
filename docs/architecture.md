# ResearchForge Architecture

## Data Flow

```
User → Frontend (Next.js) → FastAPI Backend → PostgreSQL
                                           → Filesystem (PDFs, exports)
```

## Core Entities & Relationships

```
Project (top-level container)
├── ResearchQuestion (1 per project, the research brief)
├── LiteratureItem[] (imported papers)
│   └── EvidenceCard[] (structured claims from papers)
├── ExperimentPlan (experiment design)
├── DraftSection[] (paper sections, keyed by section_key)
└── ReviewReport[] (simulated reviewer feedback)
```

## Module / AI Role Map

| Module | AI Role (future) | Status |
|---|---|---|
| Project Intake | Research Planner | Stub |
| Literature Review | Literature Analyst | Stub |
| Experiment Planner | Research Planner | Stub |
| Writing Workspace | Writing Assistant | Stub |
| Reviewer Arena | Reviewer Personas (5 types) | Stub |

## Reviewer Persona Types

- `novelty_critic` — Challenges novelty and contribution claims
- `evaluation_critic` — Challenges experimental validity
- `systems_critic` — Challenges implementation and reproducibility
- `writing_critic` — Reviews clarity, structure, presentation
- `meta_reviewer` — Produces consensus summary and AC-style decision

## Key Design Decisions

1. **UUID primary keys** — avoids sequential ID guessing, future multi-tenant ready
2. **JSONB for arrays/objects** — flexible schema evolution without migrations for list fields
3. **Project-scoped cascade deletes** — deleting a project cleans up all artifacts
4. **Section keys** — draft sections identified by `section_key` (e.g., "abstract", "introduction")
   so the system knows which section is which for LaTeX export
5. **AI outputs are first-class stored artifacts** — every AI response is persisted before display
6. **Client-side data fetching in MVP** — simple `fetch` + `useState`; upgrade to SWR/React Query later

## Assumptions & Follow-ups

- Storage paths are relative to project root; absolute path stored in DB
- For now, PDF extraction is stubbed; actual pipeline to use PyMuPDF or Marker
- Tags are stored as JSONB arrays; no tag normalization table for MVP
- `ALLOWED_ORIGINS` must be updated for production deployment
- Auth is out of scope for MVP (single-user, local-first)
