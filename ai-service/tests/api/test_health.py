"""
Tests for health endpoints: GET /health and GET /ready
"""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_returns_status(client):
    # Without live Qdrant, we expect 503 degraded
    response = client.get("/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert "status" in body
    assert "checks" in body
    assert "gemini" in body["checks"]
    assert "qdrant" in body["checks"]
