"""Health check endpoint for the application.

Exposes GET /health, returning HTTP 200 with a JSON body {"status": "OK"}
when the process is running. See specs/health-endpoint.md for the full
specification and acceptance criteria.
"""

from flask import Flask, Response, jsonify

app = Flask(__name__)


@app.get("/health")
def health() -> tuple[Response, int]:
    """Return service liveness status.

    Returns:
        A tuple of (JSON response, HTTP status code). jsonify() returns a
        flask.Response, not a plain dict, hence the return type below.
        Flask automatically returns HTTP 405 for any non-GET request to
        this route.
    """
    return jsonify(status="OK"), 200


if __name__ == "__main__":
    app.run()
