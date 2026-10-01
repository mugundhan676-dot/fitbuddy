import os
os.environ["MOCK_AI"] = "true"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_enabled"] is False

def test_generate_and_update_api():
    payload = {
        "name": "Test User",
        "user_id": "test-001",
        "age": 25,
        "weight": 70,
        "goal": "muscle gain",
        "intensity": "medium",
    }
    response = client.post("/api/generate-workout", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["workout_plan"]["days"]) == 7
    assert body["nutrition_tip"]

    feedback = {
        "user_id": "test-001",
        "feedback": "Add more cardio and include one extra rest-focused day.",
    }
    response = client.post("/api/update-plan/test-001", json=feedback)
    assert response.status_code == 200
    assert len(response.json()["updated_plan"]["days"]) == 7

def test_admin_page():
    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "Test User" in response.text
