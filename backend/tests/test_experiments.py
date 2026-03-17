"""
Tests for the Experiment Planner: plan CRUD, structured fields, project linkage.

Run with:  pytest tests/test_experiments.py -v
Requires the test DB (researchforge_test) and Docker-based Postgres to be running.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

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
        conn.execute(text("TRUNCATE projects CASCADE"))
        conn.commit()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def project(client):
    res = client.post("/api/projects/", json={"title": "Experiment Test Project"})
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_list_plans_empty(client, project):
    res = client.get(f"/api/projects/{project['id']}/experiments/")
    assert res.status_code == 200
    assert res.json() == []


def test_list_plans_project_not_found(client):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/projects/{fake_id}/experiments/")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_plan_minimal(client, project):
    res = client.post(f"/api/projects/{project['id']}/experiments/", json={})
    assert res.status_code == 201
    data = res.json()
    assert data["project_id"] == project["id"]
    assert data["objective"] is None
    assert data["hypotheses"] == []
    assert data["baselines"] == []
    assert data["datasets"] == []
    assert data["metrics"] == []
    assert data["ablations"] == []
    assert data["expected_claims"] == []
    assert data["risks"] == []
    assert data["compute_notes"] is None
    assert data["reproducibility_requirements"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_plan_full(client, project):
    payload = {
        "objective": "Demonstrate that our model outperforms baselines on GLUE",
        "hypotheses": [
            "H1: Our model achieves >90% on SST-2",
            "H2: Attention heads specialize by layer",
        ],
        "baselines": ["BERT-base", "RoBERTa-base", "DeBERTa-v3"],
        "datasets": ["GLUE", "SuperGLUE", "SQuAD 2.0"],
        "metrics": ["Accuracy", "F1", "MCC"],
        "ablations": ["Without pre-training", "Without layer-norm", "Reduced heads"],
        "expected_claims": ["State-of-the-art on GLUE benchmark"],
        "risks": ["Compute budget may be insufficient", "Dataset shift"],
        "compute_notes": "4x A100 80GB, ~72h training",
        "reproducibility_requirements": "Fixed seed 42, deterministic CUDA ops",
    }
    res = client.post(f"/api/projects/{project['id']}/experiments/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["objective"] == payload["objective"]
    assert data["hypotheses"] == payload["hypotheses"]
    assert data["baselines"] == payload["baselines"]
    assert data["datasets"] == payload["datasets"]
    assert data["metrics"] == payload["metrics"]
    assert data["ablations"] == payload["ablations"]
    assert data["expected_claims"] == payload["expected_claims"]
    assert data["risks"] == payload["risks"]
    assert data["compute_notes"] == payload["compute_notes"]
    assert data["reproducibility_requirements"] == payload["reproducibility_requirements"]


def test_create_plan_project_not_found(client):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.post(f"/api/projects/{fake_id}/experiments/", json={})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------

def test_get_plan(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/experiments/",
        json={"objective": "Beat SOTA"},
    )
    plan_id = create_res.json()["id"]

    res = client.get(f"/api/projects/{project['id']}/experiments/{plan_id}")
    assert res.status_code == 200
    assert res.json()["objective"] == "Beat SOTA"


def test_get_plan_not_found(client, project):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/projects/{project['id']}/experiments/{fake_id}")
    assert res.status_code == 404


def test_get_plan_wrong_project(client):
    """A plan from project A must not be accessible via project B's URL."""
    proj_a = client.post("/api/projects/", json={"title": "Project A"}).json()
    proj_b = client.post("/api/projects/", json={"title": "Project B"}).json()

    plan = client.post(
        f"/api/projects/{proj_a['id']}/experiments/", json={"objective": "Plan A"}
    ).json()

    res = client.get(f"/api/projects/{proj_b['id']}/experiments/{plan['id']}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Update (PATCH)
# ---------------------------------------------------------------------------

def test_update_plan_objective(client, project):
    plan = client.post(
        f"/api/projects/{project['id']}/experiments/",
        json={"objective": "Initial"},
    ).json()

    res = client.patch(
        f"/api/projects/{project['id']}/experiments/{plan['id']}",
        json={"objective": "Updated objective"},
    )
    assert res.status_code == 200
    assert res.json()["objective"] == "Updated objective"


def test_update_plan_list_fields(client, project):
    plan = client.post(
        f"/api/projects/{project['id']}/experiments/", json={}
    ).json()

    res = client.patch(
        f"/api/projects/{project['id']}/experiments/{plan['id']}",
        json={
            "hypotheses": ["H1", "H2"],
            "baselines": ["BERT", "GPT"],
            "metrics": ["Accuracy"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["hypotheses"] == ["H1", "H2"]
    assert data["baselines"] == ["BERT", "GPT"]
    assert data["metrics"] == ["Accuracy"]
    # Unset fields unchanged
    assert data["datasets"] == []


def test_update_plan_partial_leaves_other_fields_intact(client, project):
    plan = client.post(
        f"/api/projects/{project['id']}/experiments/",
        json={
            "objective": "Original",
            "hypotheses": ["H1"],
            "compute_notes": "2x V100",
        },
    ).json()

    client.patch(
        f"/api/projects/{project['id']}/experiments/{plan['id']}",
        json={"objective": "Changed"},
    )

    res = client.get(f"/api/projects/{project['id']}/experiments/{plan['id']}")
    data = res.json()
    assert data["objective"] == "Changed"
    assert data["hypotheses"] == ["H1"]  # unchanged
    assert data["compute_notes"] == "2x V100"  # unchanged


def test_update_plan_not_found(client, project):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.patch(
        f"/api/projects/{project['id']}/experiments/{fake_id}",
        json={"objective": "X"},
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_plan(client, project):
    plan = client.post(
        f"/api/projects/{project['id']}/experiments/", json={}
    ).json()

    res = client.delete(f"/api/projects/{project['id']}/experiments/{plan['id']}")
    assert res.status_code == 204

    # Gone from list
    plans = client.get(f"/api/projects/{project['id']}/experiments/").json()
    assert all(p["id"] != plan["id"] for p in plans)


def test_delete_plan_not_found(client, project):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.delete(f"/api/projects/{project['id']}/experiments/{fake_id}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Multiple plans per project
# ---------------------------------------------------------------------------

def test_multiple_plans_per_project(client, project):
    for objective in ["Plan A", "Plan B", "Plan C"]:
        client.post(
            f"/api/projects/{project['id']}/experiments/",
            json={"objective": objective},
        )

    plans = client.get(f"/api/projects/{project['id']}/experiments/").json()
    assert len(plans) == 3
    objectives = {p["objective"] for p in plans}
    assert objectives == {"Plan A", "Plan B", "Plan C"}


# ---------------------------------------------------------------------------
# Project cascade delete
# ---------------------------------------------------------------------------

def test_project_delete_cascades_to_plans(client):
    proj = client.post("/api/projects/", json={"title": "Cascade Test"}).json()
    plan = client.post(
        f"/api/projects/{proj['id']}/experiments/",
        json={"objective": "Will be deleted"},
    ).json()

    client.delete(f"/api/projects/{proj['id']}")

    # Verify project gone
    assert client.get(f"/api/projects/{proj['id']}").status_code == 404
