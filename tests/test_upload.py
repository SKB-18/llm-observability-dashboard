"""
Tests for the CSV upload endpoint.
"""
import io
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Completion, EvalResult, Upload

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv(rows: str, header: str = "prompt,response") -> bytes:
    return f"{header}\n{rows}".encode()


@pytest.fixture(autouse=True)
def clean(reset_db):
    pass


# ---------------------------------------------------------------------------
# _parse_csv / validation
# ---------------------------------------------------------------------------

def test_upload_rejects_non_csv():
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("data.txt", b"prompt,response\nhello,world", "text/plain")},
    )
    assert resp.status_code == 400
    assert "csv" in resp.json()["detail"].lower()


def test_upload_missing_required_column():
    csv = b"prompt,model\nHello,gpt-4\n"
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("data.csv", csv, "text/csv")},
    )
    assert resp.status_code == 422
    assert "response" in resp.json()["detail"]


def test_upload_empty_csv():
    csv = b"prompt,response\n"
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("empty.csv", csv, "text/csv")},
    )
    assert resp.status_code == 422
    assert "no data" in resp.json()["detail"].lower() or "valid rows" in resp.json()["detail"].lower()


def test_upload_all_blank_rows():
    csv = b"prompt,response\n , \n , \n"
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("blank.csv", csv, "text/csv")},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Minimal successful upload
# ---------------------------------------------------------------------------

def test_upload_minimal_two_columns():
    csv = _csv("What is Python?,Python is a programming language.")
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["row_count"] == 1
    assert data["source_id"].startswith("upload_")
    assert "prompt" in data["columns_detected"]
    assert "response" in data["columns_detected"]
    assert "bleu" in data["scores"]
    assert "rouge" in data["scores"]
    assert data["models"][0]["model"] == "uploaded"


def test_upload_multiple_rows():
    rows = "\n".join([
        "What is ML?,ML is machine learning.",
        "What is AI?,AI is artificial intelligence.",
        "What is DL?,DL is deep learning.",
    ])
    csv = _csv(rows)
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("ml.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["row_count"] == 3
    assert data["models"][0]["count"] == 3


# ---------------------------------------------------------------------------
# Optional columns
# ---------------------------------------------------------------------------

def test_upload_with_quality_rating():
    csv = _csv(
        "Explain loops,Loops repeat code,8",
        header="prompt,response,quality_rating",
    )
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("q.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "human" in data["scores"]
    # 8/10 = 0.8
    assert abs(data["scores"]["human"] - 0.8) < 0.01


def test_upload_quality_rating_over_1_normalised():
    """Ratings 0-10 are normalised to 0-1."""
    csv = _csv(
        "Hello,World,10",
        header="prompt,response,quality_rating",
    )
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("q.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    assert resp.json()["scores"]["human"] == 1.0


def test_upload_with_model_column():
    rows = "Ask GPT,GPT response,gpt-4\nAsk Claude,Claude response,claude-3-opus"
    csv = _csv(rows, header="prompt,response,model")
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("models.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    model_names = {m["model"] for m in data["models"]}
    assert "gpt-4" in model_names
    assert "claude-3-opus" in model_names


def test_upload_with_all_optional_columns():
    header = "prompt,response,model,tokens_in,tokens_out,latency_ms,cost_usd,quality_rating,criteria"
    row = "Tell me about Python,Python is great,gpt-4,50,30,120.5,0.002,9,Is it accurate?"
    csv = _csv(row, header=header)
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("full.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["row_count"] == 1
    assert "bleu" in data["scores"]
    assert "rouge" in data["scores"]
    assert "human" in data["scores"]


def test_upload_invalid_quality_rating_skipped():
    """Non-numeric quality_rating is silently skipped (no human eval stored)."""
    csv = _csv("Hello,World,not_a_number", header="prompt,response,quality_rating")
    resp = client.post(
        "/api/v1/upload/csv",
        files={"file": ("bad_q.csv", csv, "text/csv")},
    )
    assert resp.status_code == 201
    # human key absent since rating was invalid
    assert "human" not in resp.json()["scores"]


# ---------------------------------------------------------------------------
# Dataset listing
# ---------------------------------------------------------------------------

def test_list_uploads_empty():
    resp = client.get("/api/v1/upload/datasets")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_uploads_after_upload():
    csv = _csv("Q,A")
    client.post("/api/v1/upload/csv", files={"file": ("f.csv", csv, "text/csv")})
    resp = client.get("/api/v1/upload/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) == 1
    assert datasets[0]["filename"] == "f.csv"
    assert datasets[0]["row_count"] == 1
    assert "scores" in datasets[0]
    assert "source_id" in datasets[0]
    assert "metrics_url" in datasets[0]


def test_list_uploads_multiple():
    for i in range(3):
        csv = _csv(f"Q{i},A{i}")
        client.post("/api/v1/upload/csv", files={"file": (f"f{i}.csv", csv, "text/csv")})
    resp = client.get("/api/v1/upload/datasets")
    assert len(resp.json()) == 3


# ---------------------------------------------------------------------------
# Delete upload
# ---------------------------------------------------------------------------

def test_delete_upload():
    csv = _csv("Q,A")
    up = client.post("/api/v1/upload/csv", files={"file": ("d.csv", csv, "text/csv")}).json()
    upload_id = client.get("/api/v1/upload/datasets").json()[0]["id"]

    del_resp = client.delete(f"/api/v1/upload/{upload_id}")
    assert del_resp.status_code == 204

    assert client.get("/api/v1/upload/datasets").json() == []


def test_delete_upload_removes_completions_and_evals(reset_db):
    from tests.conftest import _Session
    csv = _csv("Q,A,8", header="prompt,response,quality_rating")
    client.post("/api/v1/upload/csv", files={"file": ("e.csv", csv, "text/csv")})
    upload_id = client.get("/api/v1/upload/datasets").json()[0]["id"]
    source_id = client.get("/api/v1/upload/datasets").json()[0]["source_id"]

    db = _Session()
    assert db.query(Completion).filter(Completion.source == source_id).count() == 1
    db.close()

    client.delete(f"/api/v1/upload/{upload_id}")

    db = _Session()
    assert db.query(Completion).filter(Completion.source == source_id).count() == 0
    assert db.query(EvalResult).join(
        Completion, EvalResult.completion_id == Completion.id
    ).filter(Completion.source == source_id).count() == 0
    db.close()


def test_delete_nonexistent_upload():
    resp = client.delete("/api/v1/upload/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Source metrics integration
# ---------------------------------------------------------------------------

def test_uploaded_data_queryable_via_source_metrics():
    csv = _csv("What is Python?,Python is a language.\nWhat is JS?,JS is web scripting.")
    up = client.post("/api/v1/upload/csv", files={"file": ("s.csv", csv, "text/csv")}).json()
    source_id = up["source_id"]

    resp = client.get(f"/api/v1/metrics/source/{source_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 2
    assert data["source"] == source_id
