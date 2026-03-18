"""
Tests for /api/mcq endpoints:
  POST   /api/mcq/upload
  GET    /api/mcq/documents
  GET    /api/mcq/documents/{id}
  DELETE /api/mcq/documents/{id}
  POST   /api/mcq/regenerate/{id}
"""
import io
from unittest.mock import patch

from app.models.models import MCQDocument, MCQQuestion


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth(token):
    return {"Authorization": f"Bearer {token}"}


MOCK_MCQS = [
    {
        "question_type": "direct",
        "question_text": "Which article abolishes untouchability?",
        "statements": None,
        "pairs": None,
        "options": [
            {"label": "a", "text": "Article 14"},
            {"label": "b", "text": "Article 17"},
            {"label": "c", "text": "Article 19"},
            {"label": "d", "text": "Article 21"},
        ],
        "correct_option": "b",
        "explanation": "Article 17 abolishes untouchability.",
        "topic": "Fundamental Rights",
        "difficulty": "easy",
    },
    {
        "question_type": "negative",
        "question_text": "Which of the following is NOT a Fundamental Right?",
        "statements": None,
        "pairs": None,
        "options": [
            {"label": "a", "text": "Right to equality"},
            {"label": "b", "text": "Right to property"},
            {"label": "c", "text": "Right to freedom"},
            {"label": "d", "text": "Right against exploitation"},
        ],
        "correct_option": "b",
        "explanation": "Right to property was removed from Fundamental Rights by the 44th Amendment.",
        "topic": "Fundamental Rights",
        "difficulty": "easy",
    },
]


def _txt_file(content="Sample document text about Indian Constitution."):
    return ("test.txt", io.BytesIO(content.encode()), "text/plain")


# ── Upload ─────────────────────────────────────────────────────────────────────

def test_upload_creates_document_and_queues_mcqs(client, admin_token, db):
    """Uploading a TXT file should create an MCQDocument and start background generation."""
    fname, fbytes, ftype = _txt_file()
    with patch("app.routers.mcq._process_document"):  # skip actual generation
        res = client.post(
            "/api/mcq/upload",
            headers=_auth(admin_token),
            files={"file": (fname, fbytes, ftype)},
            data={"title": "Test Doc", "subject_area": "Indian Polity", "num_questions": "5"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Doc"
    assert data["status"] == "uploaded"

    doc = db.query(MCQDocument).first()
    assert doc is not None
    assert doc.subject_area == "Indian Polity"


def test_upload_requires_authentication(client):
    fname, fbytes, ftype = _txt_file()
    res = client.post(
        "/api/mcq/upload",
        files={"file": (fname, fbytes, ftype)},
        data={"title": "No Auth"},
    )
    assert res.status_code == 401


def test_upload_rejects_unsupported_file_type(client, admin_token):
    res = client.post(
        "/api/mcq/upload",
        headers=_auth(admin_token),
        files={"file": ("image.jpg", io.BytesIO(b"fake"), "image/jpeg")},
        data={"title": "Bad Type"},
    )
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"]


def test_upload_rejects_too_few_questions(client, admin_token):
    fname, fbytes, ftype = _txt_file()
    res = client.post(
        "/api/mcq/upload",
        headers=_auth(admin_token),
        files={"file": (fname, io.BytesIO(b"text"), ftype)},
        data={"num_questions": "2"},  # < 5
    )
    assert res.status_code == 400


# ── List documents ─────────────────────────────────────────────────────────────

def test_list_documents_empty_for_new_institute(client, admin_token):
    res = client.get("/api/mcq/documents", headers=_auth(admin_token))
    assert res.status_code == 200
    assert res.json() == []


def test_list_documents_shows_own_institute_only(client, admin_token, db, test_institute):
    doc = MCQDocument(
        institute_id=test_institute.id,
        uploaded_by=1,
        filename="doc.txt",
        file_path="/tmp/doc.txt",
        file_type="txt",
        title="My Doc",
        status="generated",
    )
    db.add(doc)
    db.commit()

    res = client.get("/api/mcq/documents", headers=_auth(admin_token))
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "My Doc"


def test_list_documents_requires_auth(client):
    res = client.get("/api/mcq/documents")
    assert res.status_code == 401


# ── Get document ───────────────────────────────────────────────────────────────

def test_get_document_with_questions(client, admin_token, db, test_institute):
    doc = MCQDocument(
        institute_id=test_institute.id,
        uploaded_by=1,
        filename="polity.txt",
        file_path="/tmp/polity.txt",
        file_type="txt",
        title="Polity Notes",
        status="generated",
        num_questions=2,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    for mcq in MOCK_MCQS:
        db.add(MCQQuestion(
            document_id=doc.id,
            question_type=mcq["question_type"],
            question_text=mcq["question_text"],
            options=mcq["options"],
            correct_option=mcq["correct_option"],
            explanation=mcq["explanation"],
            topic=mcq["topic"],
            difficulty=mcq["difficulty"],
        ))
    db.commit()

    res = client.get(f"/api/mcq/documents/{doc.id}", headers=_auth(admin_token))
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Polity Notes"
    assert len(data["questions"]) == 2
    assert data["questions"][0]["correct_option"] in ("a", "b", "c", "d")


def test_get_document_not_found_returns_404(client, admin_token):
    res = client.get("/api/mcq/documents/9999", headers=_auth(admin_token))
    assert res.status_code == 404


# ── Delete document ────────────────────────────────────────────────────────────

def test_delete_document_removes_from_db(client, admin_token, db, test_institute):
    doc = MCQDocument(
        institute_id=test_institute.id,
        uploaded_by=1,
        filename="del.txt",
        file_path="/tmp/nonexistent.txt",  # file won't exist, should handle gracefully
        file_type="txt",
        title="To Delete",
        status="generated",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = doc.id

    res = client.delete(f"/api/mcq/documents/{doc_id}", headers=_auth(admin_token))
    assert res.status_code == 200
    assert db.query(MCQDocument).filter(MCQDocument.id == doc_id).first() is None


def test_delete_nonexistent_document_returns_404(client, admin_token):
    res = client.delete("/api/mcq/documents/9999", headers=_auth(admin_token))
    assert res.status_code == 404


# ── Regenerate ─────────────────────────────────────────────────────────────────

def test_regenerate_clears_old_questions_and_requeues(client, admin_token, db, test_institute):
    doc = MCQDocument(
        institute_id=test_institute.id,
        uploaded_by=1,
        filename="regen.txt",
        file_path="/tmp/regen.txt",
        file_type="txt",
        title="Regen Doc",
        extracted_text="Some polity text",
        status="generated",
        num_questions=1,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Seed an old question
    db.add(MCQQuestion(
        document_id=doc.id,
        question_type="direct",
        question_text="Old question?",
        options=[{"label": "a", "text": "Yes"}, {"label": "b", "text": "No"},
                 {"label": "c", "text": "Maybe"}, {"label": "d", "text": "Always"}],
        correct_option="a",
        difficulty="easy",
    ))
    db.commit()

    with patch("app.routers.mcq._process_document"):
        res = client.post(
            f"/api/mcq/regenerate/{doc.id}?num_questions=5",
            headers=_auth(admin_token),
        )
    assert res.status_code == 200

    # Old questions should be wiped
    remaining = db.query(MCQQuestion).filter(MCQQuestion.document_id == doc.id).count()
    assert remaining == 0

    # Doc status reset to "uploaded" (processing queued)
    db.refresh(doc)
    assert doc.status == "uploaded"
    assert doc.num_questions == 0


def test_regenerate_already_processing_returns_409(client, admin_token, db, test_institute):
    doc = MCQDocument(
        institute_id=test_institute.id,
        uploaded_by=1,
        filename="busy.txt",
        file_path="/tmp/busy.txt",
        file_type="txt",
        title="Busy Doc",
        status="processing",  # already in progress
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    res = client.post(f"/api/mcq/regenerate/{doc.id}", headers=_auth(admin_token))
    assert res.status_code == 409
