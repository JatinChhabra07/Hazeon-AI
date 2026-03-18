"""
Pytest fixtures for Hazeon AI backend tests.

Uses an in-memory SQLite database so tests are fully isolated and fast.
The lifespan startup (init_db + seed_demo_data) is patched out so the
test DB starts clean for every test function.
"""
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import Institute, User, Question
from app.routers.auth import hash_password

# ── In-memory test database ────────────────────────────────────────────────────
# StaticPool ensures every session (the test's `db` fixture AND the client's
# override_get_db) share the exact same underlying SQLite connection, so data
# written by one session is immediately visible to the other.

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Session-scoped client (one TestClient per test session) ───────────────────

@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient with:
      - get_db overridden to use in-memory SQLite
      - lifespan startup patched out (no seed data, no real init_db)
    """
    app.dependency_overrides[get_db] = override_get_db
    with patch("app.main.init_db"), patch("app.main.seed_demo_data"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


# ── Per-test DB teardown ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for full isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Raw DB session for directly seeding test data."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Reusable data fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def test_institute(db):
    institute = Institute(
        name="Test Academy",
        code="TEST-ACE",
        city="Chandigarh",
        state="Haryana",
        plan_type="pilot",
    )
    db.add(institute)
    db.commit()
    db.refresh(institute)
    return institute


@pytest.fixture
def test_admin(db, test_institute):
    admin = User(
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        full_name="Test Admin",
        role="institute_admin",
        institute_id=test_institute.id,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_student(db, test_institute):
    student = User(
        email="student@test.com",
        password_hash=hash_password("student123"),
        full_name="Test Student",
        role="student",
        institute_id=test_institute.id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture
def test_question(db, test_institute):
    question = Question(
        text="Discuss good governance in Haryana.",
        subject="GS2 - Governance",
        topic="Good Governance",
        year=2025,
        exam_type="HCS",
        marks=15,
        word_limit=250,
        difficulty="moderate",
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@pytest.fixture
def admin_token(client, test_admin):
    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123",
    })
    return res.json()["access_token"]


@pytest.fixture
def student_token(client, test_student):
    res = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "student123",
    })
    return res.json()["access_token"]
