import pytest
from fastapi.testclient import TestClient
from api.app import app
from core.settings import settings


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200, response.json()
    assert response.json() == {
        "status": "OK",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "model_loaded": hasattr(app.state, "model"),
    }
