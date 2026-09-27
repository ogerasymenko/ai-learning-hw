"""Minimal Flask application exposing a liveness health endpoint.

Implements ``specs/health-endpoint.md`` (Approved 2026-09-27).

Routes:
    ``GET /health`` returns HTTP 200 with the JSON body ``{"status": "OK"}``.
    Any other method on ``/health`` returns HTTP 405 (Flask default).

Dependencies:
    Flask -- HTTP routing and JSON responses (justified in the spec).

Configuration:
    None. No environment variables or secrets are used.

Security:
    The endpoint takes no input and returns no sensitive data, so it
    requires no authentication or input validation.

Example:
    Run locally with::

        flask --app src/health.py run

    then ``curl http://127.0.0.1:5000/health`` returns ``{"status":"OK"}``.
"""

from flask import Flask, Response, jsonify

app = Flask(__name__)


@app.get("/health")
def health() -> Response:
    """Report that the process is running.

    Returns:
        A JSON response ``{"status": "OK"}`` with HTTP status 200.
    """
    return jsonify(status="OK")
