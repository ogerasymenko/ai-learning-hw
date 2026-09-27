"""Tests for src/health.py, covering specs/health-endpoint.md's acceptance criteria."""

import pytest
from flask.testing import FlaskClient

from src.health import app


@pytest.fixture
def client() -> FlaskClient:
    app.testing = True
    return app.test_client()


def test_health_endpoint_returns_200(client: FlaskClient) -> None:
    """Given the app is running, When GET /health, Then 200 + {"status": "OK"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "OK"}


def test_health_endpoint_rejects_post(client: FlaskClient) -> None:
    """Given the app is running, When POST /health, Then 405 Method Not Allowed."""
    response = client.post("/health")
    assert response.status_code == 405
