"""
Tests for the literature workspace: items, PDF upload, extraction, evidence cards.

Run with:  pytest tests/test_literature.py -v
Requires the test DB (researchforge_test) and Docker-based Postgres to be running.
"""
import io
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
    res = client.post("/api/projects/", json={"title": "Literature Test Project"})
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# Literature items
# ---------------------------------------------------------------------------

def test_list_literature_items_empty(client, project):
    res = client.get(f"/api/projects/{project['id']}/literature/items/")
    assert res.status_code == 200
    assert res.json() == []


def test_create_literature_item_manual(client, project):
    payload = {
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "year": 2017,
        "venue": "NeurIPS",
        "abstract": "The dominant sequence transduction models are based on complex RNNs...",
        "tags": ["transformers", "attention"],
    }
    res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["authors"] == payload["authors"]
    assert data["year"] == 2017
    assert data["venue"] == "NeurIPS"
    assert "id" in data
    # No URL provided → extraction should NOT have been triggered
    assert data["extracted_summary"] is None


def test_create_literature_item_with_url_triggers_extraction(client, project):
    payload = {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": ["Devlin et al."],
        "year": 2019,
        "doi_or_url": "https://arxiv.org/abs/1810.04805",
    }
    res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    # Extraction stub should have run and set extracted_summary
    assert data["extracted_summary"] is not None
    assert "[Stub extraction" in data["extracted_summary"]
    assert data["extracted_methods"] is not None
    assert len(data["extracted_methods"]) > 0


def test_get_literature_item(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "Test Paper"},
    )
    item_id = create_res.json()["id"]

    res = client.get(f"/api/projects/{project['id']}/literature/items/{item_id}")
    assert res.status_code == 200
    assert res.json()["id"] == item_id


def test_update_literature_item(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "Original Title", "year": 2020},
    )
    item_id = create_res.json()["id"]

    res = client.patch(
        f"/api/projects/{project['id']}/literature/items/{item_id}",
        json={"title": "Updated Title", "relevance_score": 0.9},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Updated Title"
    assert data["relevance_score"] == pytest.approx(0.9)


def test_delete_literature_item(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "To Delete"},
    )
    item_id = create_res.json()["id"]

    del_res = client.delete(
        f"/api/projects/{project['id']}/literature/items/{item_id}"
    )
    assert del_res.status_code == 204

    get_res = client.get(
        f"/api/projects/{project['id']}/literature/items/{item_id}"
    )
    assert get_res.status_code == 404


def test_pdf_upload_triggers_extraction(client, project, tmp_path):
    # Create item first
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "PDF Upload Test Paper"},
    )
    item_id = create_res.json()["id"]

    # Create a minimal fake PDF bytes
    fake_pdf = b"%PDF-1.4 fake pdf content for testing"
    res = client.post(
        f"/api/projects/{project['id']}/literature/items/{item_id}/upload-pdf",
        files={"file": ("test_paper.pdf", io.BytesIO(fake_pdf), "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["pdf_path"] is not None
    assert "test_paper.pdf" in data["pdf_path"]
    # Extraction stub should have run
    assert data["extracted_summary"] is not None


def test_pdf_upload_rejects_non_pdf(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "Bad Upload Test"},
    )
    item_id = create_res.json()["id"]

    res = client.post(
        f"/api/projects/{project['id']}/literature/items/{item_id}/upload-pdf",
        files={"file": ("notes.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert res.status_code == 422


def test_manual_extraction_trigger(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={
            "title": "Manual Extraction Test",
            "doi_or_url": "https://arxiv.org/abs/2005.14165",
        },
    )
    item_id = create_res.json()["id"]

    # Re-trigger extraction explicitly
    res = client.post(
        f"/api/projects/{project['id']}/literature/items/{item_id}/extract"
    )
    assert res.status_code == 200
    assert res.json()["extracted_summary"] is not None


def test_extract_item_without_source_fails(client, project):
    create_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "No source"},
    )
    item_id = create_res.json()["id"]

    res = client.post(
        f"/api/projects/{project['id']}/literature/items/{item_id}/extract"
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Evidence cards
# ---------------------------------------------------------------------------

def test_create_evidence_card(client, project):
    lit_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "Source Paper"},
    )
    item_id = lit_res.json()["id"]

    payload = {
        "claim": "Transformers outperform RNNs on translation tasks",
        "evidence_type": "empirical",
        "quote_or_paraphrase": "We achieve 28.4 BLEU on the WMT 2014 English-to-German task.",
        "method": "Encoder-decoder with multi-head self-attention",
        "metrics": {"BLEU": 28.4, "dataset": "WMT 2014"},
        "limitations": "High compute cost for long sequences",
        "confidence": 0.95,
        "literature_item_id": item_id,
    }
    res = client.post(
        f"/api/projects/{project['id']}/literature/evidence/",
        json=payload,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["claim"] == payload["claim"]
    assert data["confidence"] == pytest.approx(0.95)
    assert data["literature_item_id"] == item_id


def test_list_evidence_cards(client, project):
    lit_res = client.post(
        f"/api/projects/{project['id']}/literature/items/",
        json={"title": "Evidence Source"},
    )
    item_id = lit_res.json()["id"]

    for i in range(3):
        client.post(
            f"/api/projects/{project['id']}/literature/evidence/",
            json={"claim": f"Claim {i}", "literature_item_id": item_id},
        )

    # List all
    all_res = client.get(f"/api/projects/{project['id']}/literature/evidence/")
    assert len(all_res.json()) == 3

    # Filter by literature_item_id
    filtered_res = client.get(
        f"/api/projects/{project['id']}/literature/evidence/",
        params={"literature_item_id": item_id},
    )
    assert len(filtered_res.json()) == 3


def test_evidence_card_invalid_literature_item(client, project):
    """Creating a card referencing a non-existent literature item should 404."""
    res = client.post(
        f"/api/projects/{project['id']}/literature/evidence/",
        json={
            "claim": "Some claim",
            "literature_item_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert res.status_code == 404


def test_update_evidence_card(client, project):
    card_res = client.post(
        f"/api/projects/{project['id']}/literature/evidence/",
        json={"claim": "Original claim"},
    )
    card_id = card_res.json()["id"]

    res = client.patch(
        f"/api/projects/{project['id']}/literature/evidence/{card_id}",
        json={"claim": "Revised claim", "confidence": 0.7},
    )
    assert res.status_code == 200
    assert res.json()["claim"] == "Revised claim"


def test_delete_evidence_card(client, project):
    card_res = client.post(
        f"/api/projects/{project['id']}/literature/evidence/",
        json={"claim": "To delete"},
    )
    card_id = card_res.json()["id"]

    del_res = client.delete(
        f"/api/projects/{project['id']}/literature/evidence/{card_id}"
    )
    assert del_res.status_code == 204

    get_res = client.get(
        f"/api/projects/{project['id']}/literature/evidence/{card_id}"
    )
    assert get_res.status_code == 404
