"""Tests for the health endpoint defined in specs/health-endpoint.md."""

import sys
from pathlib import Path

import pytest
from flask.testing import FlaskClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from health import app


@pytest.fixture
def client() -> FlaskClient:
    """Return a Flask test client for the health app."""
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_endpoint_returns_200(client: FlaskClient) -> None:
    """GET /health with no credentials or parameters returns 200."""
    # Arrange: client fixture

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200


def test_health_endpoint_returns_json_status_ok(client: FlaskClient) -> None:
    """GET /health returns the JSON body {"status": "OK"}."""
    # Arrange: client fixture

    # Act
    response = client.get("/health")

    # Assert
    assert response.content_type == "application/json"
    assert response.get_json() == {"status": "OK"}


def test_health_endpoint_rejects_post(client: FlaskClient) -> None:
    """POST /health returns 405 Method Not Allowed."""
    # Arrange: client fixture

    # Act
    response = client.post("/health")

    # Assert
    assert response.status_code == 405
