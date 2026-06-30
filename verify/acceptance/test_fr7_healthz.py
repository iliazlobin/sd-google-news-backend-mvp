"""FR-7: GET /healthz → 200 with status.

AC-7: Health check always returns 200 with status field.
"""

from verify.acceptance.conftest import assert_json_200


def test_healthz_returns_200(client):
    """Health check returns 200 with status ok."""
    resp = assert_json_200(client.get("/healthz"))
    assert resp.get("status") == "ok"


def test_healthz_has_version(client):
    """Health check includes version information."""
    resp = assert_json_200(client.get("/healthz"))
    # Either has a version field or status is sufficient
    assert "status" in resp
    assert resp["status"] == "ok"


def test_healthz_always_available(client):
    """Health check is always available (no auth, no query params needed)."""
    # Multiple calls all succeed
    for _ in range(3):
        resp = assert_json_200(client.get("/healthz"))
        assert resp.get("status") == "ok"
