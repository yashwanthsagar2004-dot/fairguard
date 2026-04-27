# backend/tests/test_main.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
