import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import (
    verify_password,
    create_access_token,
    verify_token,
    login_rate_limiter,
    COOKIE_NAME,
    JWT_ISSUER,
    JWT_AUDIENCE,
)
from app.skills import catalog
from app.gemini import validate_gemini_key
from app.config import INTERVIEW_PASSWORD, INTERVIEW_ALT_PASSWORD

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_rate_limits():
    """Ensure rate limiter is reset before each test."""
    login_rate_limiter.reset()
    yield
    login_rate_limiter.reset()


def test_password_verification():
    assert verify_password(INTERVIEW_PASSWORD) is True
    if INTERVIEW_ALT_PASSWORD:
        assert verify_password(INTERVIEW_ALT_PASSWORD) is True
    assert verify_password("WrongPassword123") is False
    assert verify_password("") is False
    assert verify_password(None) is False
    assert verify_password("   ") is False


def test_token_creation_and_validation():
    token = create_access_token({"sub": "ashish", "role": "owner"})
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "ashish"
    assert payload["role"] == "owner"
    assert payload["iss"] == JWT_ISSUER
    assert payload["aud"] == JWT_AUDIENCE
    assert "jti" in payload
    assert len(payload["jti"]) >= 16


def test_unauthenticated_api_access_rejected():
    endpoints = [
        "/interview/api/skills",
        "/interview/api/categories",
        "/interview/api/resumes",
        "/interview/api/sessions",
        "/interview/api/system/status",
        "/interview/api/system/models",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401, f"Endpoint {ep} did not reject unauthenticated access"
        assert res.json()["authenticated"] is False


def test_unauthenticated_static_and_root_redirect():
    # Root index request without token should redirect to login
    res_root = client.get("/interview/", follow_redirects=False)
    assert res_root.status_code == 302
    assert "/interview/login" in res_root.headers.get("location", "")

    # Static assets direct request without token should redirect to login
    res_static = client.get("/interview/static/index.html", follow_redirects=False)
    assert res_static.status_code == 302
    assert "/interview/login" in res_static.headers.get("location", "")

    res_js = client.get("/interview/static/js/app.js", follow_redirects=False)
    assert res_js.status_code == 302
    assert "/interview/login" in res_js.headers.get("location", "")


def test_security_headers_present():
    res = client.get("/interview/login")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("permissions-policy", "")
    assert "max-age=31536000" in headers.get("strict-transport-security", "")
    assert "default-src" in headers.get("content-security-policy", "")


def test_login_success():
    res = client.post("/interview/api/auth/login", json={"password": INTERVIEW_PASSWORD})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "token" in data
    # Check that Set-Cookie is set
    assert "set-cookie" in res.headers


def test_login_invalid_password():
    res = client.post("/interview/api/auth/login", json={"password": "invalid-password"})
    assert res.status_code == 401
    assert "Incorrect password" in res.json()["detail"]


def test_login_rate_limiting_brute_force_lockout():
    attacker_ip = "198.51.100.99"
    headers = {"X-Forwarded-For": attacker_ip}

    # First 4 failed attempts should return 401
    for attempt in range(4):
        res = client.post(
            "/interview/api/auth/login",
            json={"password": f"bad_password_{attempt}"},
            headers=headers,
        )
        assert res.status_code == 401, f"Attempt {attempt+1} should fail with 401"

    # 5th failed attempt triggers lockout
    res_5th = client.post(
        "/interview/api/auth/login",
        json={"password": "bad_password_5"},
        headers=headers,
    )
    assert res_5th.status_code == 429
    assert "Retry-After" in res_5th.headers
    assert "locked" in res_5th.json()["detail"].lower()

    # Subsequent attempts (even with correct password) are locked out
    res_locked = client.post(
        "/interview/api/auth/login",
        json={"password": INTERVIEW_PASSWORD},
        headers=headers,
    )
    assert res_locked.status_code == 429


def test_skills_catalog_loading():
    assert len(catalog.skills) >= 40
    sample = catalog.get_skill("arrays-hashmaps-interviewer")
    assert sample is not None
    assert "Arrays" in sample["title"]
    assert sample["category"] == "swe-i"


def test_authenticated_endpoints():
    login_res = client.post("/interview/api/auth/login", json={"password": INTERVIEW_PASSWORD})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test skills endpoint
    res = client.get("/interview/api/skills", headers=headers)
    assert res.status_code == 200
    skills = res.json()
    assert len(skills) >= 40

    # Test categories endpoint
    cat_res = client.get("/interview/api/categories", headers=headers)
    assert cat_res.status_code == 200
    cats = cat_res.json()
    assert len(cats) >= 5

    # Test system models endpoint
    model_res = client.get("/interview/api/system/models", headers=headers)
    assert model_res.status_code == 200
    assert "models" in model_res.json()

    # Test system status endpoint
    status_res = client.get("/interview/api/system/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "online"


def test_gemini_key_validation():
    assert validate_gemini_key("AIzaSyMockTestKeyFormatValidation12345") is True
    assert validate_gemini_key("sk-proj-1234567890abcdef") is False
    assert validate_gemini_key("") is False


def test_resume_tracks_api():
    login_res = client.post("/interview/api/auth/login", json={"password": INTERVIEW_PASSWORD})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/interview/api/resumes", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total_tracks"] == 10
    assert data["summary"]["java_count"] == 4
    assert data["summary"]["python_count"] == 6

    # Test single resume track
    res_j1 = client.get("/interview/api/resumes/J1", headers=headers)
    assert res_j1.status_code == 200
    track_j1 = res_j1.json()["track"]
    assert track_j1["id"] == "J1"
    assert "Fintech" in track_j1["subtitle"]
    assert len(track_j1["top_interview_questions"]) >= 3
