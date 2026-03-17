"""
Basic integration tests for the projects API.

Run with:  pytest tests/ -v
Requires a running PostgreSQL instance (use docker compose up -d).
A separate test database is created/dropped per session.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database setup
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
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after session
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate tables between tests to keep isolation."""
    yield
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE projects CASCADE"))
        conn.commit()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_projects_empty(client):
    res = client.get("/api/projects/")
    assert res.status_code == 200
    assert res.json() == []


def test_create_project(client):
    payload = {
        "title": "Adversarial Robustness in LLMs",
        "short_idea": "Investigate prompt injection in production LLM APIs",
        "domain": "AI Security",
        "target_venue": "IEEE S&P 2027",
        "tags": ["llm", "security", "adversarial"],
    }
    res = client.post("/api/projects/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "draft"
    assert data["tags"] == payload["tags"]
    assert "id" in data
    assert "created_at" in data


def test_get_project(client):
    create_res = client.post("/api/projects/", json={"title": "Test Project"})
    project_id = create_res.json()["id"]

    res = client.get(f"/api/projects/{project_id}")
    assert res.status_code == 200
    assert res.json()["id"] == project_id


def test_get_project_not_found(client):
    res = client.get("/api/projects/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_update_project(client):
    create_res = client.post("/api/projects/", json={"title": "Original Title"})
    project_id = create_res.json()["id"]

    res = client.patch(
        f"/api/projects/{project_id}",
        json={"title": "Updated Title", "status": "active"},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"
    assert res.json()["status"] == "active"


def test_delete_project(client):
    create_res = client.post("/api/projects/", json={"title": "To Delete"})
    project_id = create_res.json()["id"]

    del_res = client.delete(f"/api/projects/{project_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 404


def test_create_and_update_research_question(client):
    create_res = client.post("/api/projects/", json={"title": "RQ Test Project"})
    project_id = create_res.json()["id"]

    rq_payload = {
        "main_question": "Does prompt injection degrade LLM safety guardrails?",
        "hypotheses": ["Safety fine-tuning is bypassed by adversarial prompts"],
        "assumptions": ["Model is deployed without additional guardrails"],
        "novelty_claim": "First systematic study of injection attacks in RAG pipelines",
    }
    rq_res = client.post(f"/api/projects/{project_id}/research-question", json=rq_payload)
    assert rq_res.status_code == 201
    rq_id = rq_res.json()["id"]

    update_res = client.patch(
        f"/api/projects/{project_id}/research-question/{rq_id}",
        json={"scope_notes": "Focus on GPT-4 and Claude-3 Sonnet"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["scope_notes"] == "Focus on GPT-4 and Claude-3 Sonnet"
