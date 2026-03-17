"""
Integration tests for the pipeline / agent endpoints.

These tests mock the LLM and Semantic Scholar services so they can run
without external dependencies.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup (same pattern as other test files)
# ---------------------------------------------------------------------------

TEST_DB_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/researchforge_test"

test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    with test_engine.connect() as conn:
        for table in ["pipeline_runs", "evidence_cards", "literature_items",
                      "experiment_plans", "draft_sections", "review_reports",
                      "research_questions", "projects"]:
            conn.execute(text(f"TRUNCATE {table} CASCADE"))
        conn.commit()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_project(client, **kwargs):
    data = {"title": "Test AI Project", "short_idea": "Testing agents", **kwargs}
    resp = client.post("/api/projects/", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_rq(client, project_id):
    resp = client.post(
        f"/api/projects/{project_id}/research-question",
        json={"main_question": "Does attention improve NLP models?"},
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Pipeline CRUD tests
# ---------------------------------------------------------------------------


class TestPipelineEndpoints:
    """Test pipeline list/get/trigger endpoints."""

    def test_list_runs_empty(self, client):
        project = _create_project(client)
        resp = client.get(f"/api/projects/{project['id']}/pipeline/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_trigger_invalid_stage(self, client):
        project = _create_project(client)
        resp = client.post(f"/api/projects/{project['id']}/pipeline/invalid/run")
        assert resp.status_code == 400

    def test_trigger_stage_creates_run(self, client):
        """Triggering a stage creates a pending run record.
        The background task runs silently; we only verify the sync record creation."""
        project = _create_project(client)
        with patch("app.routers.pipeline._run_stage_in_thread"):
            resp = client.post(f"/api/projects/{project['id']}/pipeline/literature/run")
        assert resp.status_code == 200
        run = resp.json()
        assert run["stage"] == "literature"
        assert run["status"] == "pending"
        assert run["project_id"] == project["id"]

    def test_get_run(self, client):
        project = _create_project(client)
        with patch("app.routers.pipeline._run_stage_in_thread"):
            resp = client.post(f"/api/projects/{project['id']}/pipeline/literature/run")
        run = resp.json()

        resp2 = client.get(f"/api/projects/{project['id']}/pipeline/{run['id']}")
        assert resp2.status_code == 200
        assert resp2.json()["id"] == run["id"]

    def test_get_run_not_found(self, client):
        project = _create_project(client)
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = client.get(f"/api/projects/{project['id']}/pipeline/{fake_id}")
        assert resp.status_code == 404

    def test_list_runs_filter_by_stage(self, client):
        project = _create_project(client)
        # Create two runs for different stages (suppress background tasks)
        with patch("app.routers.pipeline._run_stage_in_thread"):
            client.post(f"/api/projects/{project['id']}/pipeline/literature/run")
            client.post(f"/api/projects/{project['id']}/pipeline/design/run")

        resp = client.get(f"/api/projects/{project['id']}/pipeline/?stage=literature")
        assert resp.status_code == 200
        runs = resp.json()
        assert len(runs) == 1
        assert runs[0]["stage"] == "literature"

    def test_trigger_run_all(self, client):
        """Triggering run-all creates 5 pending run records."""
        project = _create_project(client)
        with patch("app.routers.pipeline._run_full_pipeline_in_thread"):
            resp = client.post(f"/api/projects/{project['id']}/pipeline/run-all")
        assert resp.status_code == 200
        runs = resp.json()
        assert len(runs) == 5
        stages = [r["stage"] for r in runs]
        assert stages == ["literature", "design", "code", "evaluation", "writing"]
        for r in runs:
            assert r["status"] == "pending"

    def test_project_not_found(self, client):
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = client.get(f"/api/projects/{fake_id}/pipeline/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Pipeline service unit tests
# ---------------------------------------------------------------------------


class TestPipelineService:
    """Test the pipeline service CRUD functions directly."""

    def test_create_and_list(self, client):
        project = _create_project(client)
        db = TestingSessionLocal()
        try:
            from app.services import pipeline_service
            from uuid import UUID

            pid = UUID(project["id"])
            run = pipeline_service.create_run(db, pid, "literature")
            assert run.status == "pending"
            assert run.stage == "literature"

            runs = pipeline_service.list_runs(db, pid)
            assert len(runs) == 1
        finally:
            db.close()

    def test_start_complete_fail(self, client):
        project = _create_project(client)
        db = TestingSessionLocal()
        try:
            from app.services import pipeline_service
            from uuid import UUID

            pid = UUID(project["id"])

            # Start
            run = pipeline_service.create_run(db, pid, "design")
            run = pipeline_service.start_run(db, run)
            assert run.status == "running"
            assert run.started_at is not None

            # Complete
            run = pipeline_service.complete_run(
                db, run, result_summary="Done!", result_data={"key": "val"}
            )
            assert run.status == "completed"
            assert run.result_summary == "Done!"
            assert run.result_data == {"key": "val"}

            # Create another and fail it
            run2 = pipeline_service.create_run(db, pid, "code")
            run2 = pipeline_service.start_run(db, run2)
            run2 = pipeline_service.fail_run(db, run2, "Something broke")
            assert run2.status == "failed"
            assert run2.error_message == "Something broke"
        finally:
            db.close()

    def test_append_log(self, client):
        project = _create_project(client)
        db = TestingSessionLocal()
        try:
            from app.services import pipeline_service
            from uuid import UUID

            pid = UUID(project["id"])
            run = pipeline_service.create_run(db, pid, "literature")

            pipeline_service.append_log(db, run, "Line 1")
            assert run.logs == "Line 1"

            pipeline_service.append_log(db, run, "Line 2")
            assert run.logs == "Line 1\nLine 2"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Agent integration tests (with mocked LLM + search)
# ---------------------------------------------------------------------------


class TestLiteratureAgent:
    """Test the literature agent with mocked external services."""

    @pytest.mark.asyncio
    async def test_literature_agent_flow(self, client):
        """Full literature agent flow with mocked services."""
        project = _create_project(client)
        _create_rq(client, project["id"])

        db = TestingSessionLocal()
        try:
            from uuid import UUID
            from app.services import pipeline_service
            from app.services.agents import literature_agent

            pid = UUID(project["id"])
            run = pipeline_service.create_run(db, pid, "literature")

            mock_papers = [
                {
                    "paper_id": "abc123",
                    "title": "Attention Is All You Need",
                    "authors": ["Vaswani et al."],
                    "year": 2017,
                    "venue": "NeurIPS",
                    "abstract": "We propose a new architecture based on attention.",
                    "url": "https://arxiv.org/abs/1706.03762",
                    "citation_count": 50000,
                    "pdf_url": None,
                    "doi": "10.5555/3295222.3295349",
                },
            ]

            mock_analysis = {
                "summary": "Proposes the Transformer architecture.",
                "methods": ["self-attention", "multi-head attention"],
                "datasets": ["WMT 2014"],
                "metrics": ["BLEU"],
                "limitations": ["Quadratic complexity"],
                "key_claims": [
                    {"claim": "Transformers outperform RNNs", "evidence_type": "empirical", "confidence": 0.9}
                ],
            }

            with patch("app.services.agents.literature_agent.search_service") as mock_search, \
                 patch("app.services.agents.literature_agent.llm_service") as mock_llm:

                mock_search.search_papers = AsyncMock(return_value=mock_papers)
                mock_llm.chat_json = AsyncMock(side_effect=[
                    {"queries": ["attention mechanisms NLP", "transformer architecture"]},
                    mock_analysis,
                ])
                mock_llm.chat = AsyncMock(return_value="This is a comprehensive literature synthesis.")

                await literature_agent.run(db, pid, run)

            # Verify run completed
            db.refresh(run)
            assert run.status == "completed"
            assert "literature synthesis" in (run.result_summary or "").lower() or run.result_summary is not None

            # Verify literature items were created
            from app.models.literature import LiteratureItem
            items = db.query(LiteratureItem).filter(LiteratureItem.project_id == pid).all()
            assert len(items) >= 1
            assert items[0].title == "Attention Is All You Need"
            assert items[0].extracted_summary == "Proposes the Transformer architecture."

            # Verify evidence cards were created
            from app.models.literature import EvidenceCard
            cards = db.query(EvidenceCard).filter(EvidenceCard.project_id == pid).all()
            assert len(cards) >= 1
            assert cards[0].claim == "Transformers outperform RNNs"
        finally:
            db.close()


class TestDesignAgent:
    """Test the design agent with mocked LLM."""

    @pytest.mark.asyncio
    async def test_design_agent_flow(self, client):
        project = _create_project(client)
        _create_rq(client, project["id"])

        db = TestingSessionLocal()
        try:
            from uuid import UUID
            from app.services import pipeline_service
            from app.services.agents import design_agent

            pid = UUID(project["id"])
            run = pipeline_service.create_run(db, pid, "design")

            mock_design = {
                "objective": "Test attention mechanisms",
                "hypotheses": ["H1: Attention improves accuracy"],
                "baselines": ["LSTM", "GRU"],
                "datasets": ["GLUE"],
                "metrics": ["Accuracy", "F1"],
                "ablations": ["Without attention"],
                "expected_claims": ["Better than baselines"],
                "risks": ["Limited compute"],
                "compute_notes": "1 GPU, 2 hours",
                "reproducibility_requirements": "Random seed 42",
            }

            with patch("app.services.agents.design_agent.llm_service") as mock_llm:
                mock_llm.chat_json = AsyncMock(return_value=mock_design)

                await design_agent.run(db, pid, run)

            db.refresh(run)
            assert run.status == "completed"

            from app.models.experiment import ExperimentPlan
            plan = db.query(ExperimentPlan).filter(ExperimentPlan.project_id == pid).first()
            assert plan is not None
            assert plan.objective == "Test attention mechanisms"
            assert "H1: Attention improves accuracy" in plan.hypotheses
        finally:
            db.close()


class TestWritingAgent:
    """Test the writing agent with mocked LLM."""

    @pytest.mark.asyncio
    async def test_writing_agent_flow(self, client):
        project = _create_project(client)

        db = TestingSessionLocal()
        try:
            from uuid import UUID
            from app.services import pipeline_service
            from app.services.agents import writing_agent

            pid = UUID(project["id"])
            run = pipeline_service.create_run(db, pid, "writing")

            with patch("app.services.agents.writing_agent.llm_service") as mock_llm:
                mock_llm.chat = AsyncMock(return_value="This is a generated section.")

                await writing_agent.run(db, pid, run)

            db.refresh(run)
            assert run.status == "completed"

            from app.models.writing import DraftSection
            sections = db.query(DraftSection).filter(DraftSection.project_id == pid).all()
            assert len(sections) == 7  # abstract through conclusion
            keys = {s.section_key for s in sections}
            assert "abstract" in keys
            assert "conclusion" in keys
        finally:
            db.close()
