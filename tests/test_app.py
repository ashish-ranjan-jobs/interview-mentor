import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import verify_password, create_access_token, verify_token
from app.skills import catalog
from app.gemini import validate_gemini_key
from app.config import INTERVIEW_PASSWORD, INTERVIEW_ALT_PASSWORD

client = TestClient(app)


def test_password_verification():
    assert verify_password(INTERVIEW_PASSWORD) is True
    if INTERVIEW_ALT_PASSWORD:
        assert verify_password(INTERVIEW_ALT_PASSWORD) is True
    assert verify_password("WrongPassword123") is False
    assert verify_password("") is False


def test_token_creation_and_validation():
    token = create_access_token({"sub": "ashish", "role": "owner"})
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "ashish"
    assert payload["role"] == "owner"


def test_unauthenticated_access_rejected():
    res = client.get("/interview/api/skills")
    assert res.status_code == 401


def test_login_success():
    res = client.post("/interview/api/auth/login", json={"password": INTERVIEW_PASSWORD})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "token" in data


def test_login_invalid_password():
    res = client.post("/interview/api/auth/login", json={"password": "invalid-password"})
    assert res.status_code == 401


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
