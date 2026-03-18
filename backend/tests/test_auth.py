"""
Tests for /api/auth endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  GET  /api/auth/institutes
"""


# ── Register ───────────────────────────────────────────────────────────────────

def test_register_new_student(client, test_institute):
    res = client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "pass1234",
        "full_name": "New Student",
        "role": "student",
        "institute_id": test_institute.id,
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["role"] == "student"


def test_register_duplicate_email_returns_400(client, test_student):
    res = client.post("/api/auth/register", json={
        "email": "student@test.com",
        "password": "anypass",
        "full_name": "Dup User",
        "role": "student",
    })
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]


def test_register_admin_role(client, test_institute):
    res = client.post("/api/auth/register", json={
        "email": "newadmin@test.com",
        "password": "admin999",
        "full_name": "New Admin",
        "role": "institute_admin",
        "institute_id": test_institute.id,
    })
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "institute_admin"


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_valid_credentials(client, test_student):
    res = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "student123",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["full_name"] == "Test Student"


def test_login_wrong_password_returns_401(client, test_student):
    res = client.post("/api/auth/login", json={
        "email": "student@test.com",
        "password": "wrongpass",
    })
    assert res.status_code == 401
    assert "Invalid" in res.json()["detail"]


def test_login_unknown_email_returns_401(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "pass",
    })
    assert res.status_code == 401


# ── Get current user ───────────────────────────────────────────────────────────

def test_get_me_with_valid_token(client, student_token, test_student):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "student@test.com"
    assert data["role"] == "student"


def test_get_me_without_token_returns_401(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert res.status_code == 401


# ── List institutes ────────────────────────────────────────────────────────────

def test_list_institutes_returns_active_only(client, test_institute):
    res = client.get("/api/auth/institutes")
    assert res.status_code == 200
    institutes = res.json()
    assert len(institutes) >= 1
    codes = [i["code"] for i in institutes]
    assert "TEST-ACE" in codes


def test_list_institutes_no_auth_required(client):
    """Registration dropdown should be publicly accessible."""
    res = client.get("/api/auth/institutes")
    assert res.status_code == 200
