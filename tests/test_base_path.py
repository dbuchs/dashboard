"""Tests that the app works correctly under BASE_PATH /school."""


def test_login_under_base_path(client):
    """Login page should be accessible under /school/auth/login."""
    r = client.get("/school/auth/login")
    assert r.status_code == 200


def test_root_base_path_redirect(client):
    """Root /school/ should redirect to login."""
    r = client.get("/school/", follow_redirects=False)
    assert r.status_code in (302, 301, 200)


def test_dashboard_under_base_path(teacher_client):
    """Teacher dashboard accessible at /school/teacher/dashboard."""
    r = teacher_client.get("/school/teacher/dashboard")
    assert r.status_code == 200
    # Links should contain the base path
    assert b"/school/" in r.data


def test_no_root_routes(client):
    """Routes should NOT be accessible at root."""
    r = client.get("/auth/login")
    assert r.status_code == 404


def test_api_under_base_path(teacher_client):
    """API endpoints accessible at /school/api/v1/."""
    r = teacher_client.get("/school/api/v1/students")
    assert r.status_code == 200
