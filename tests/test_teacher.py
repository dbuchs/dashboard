def test_dashboard_requires_login(client):
    r = client.get("/school/teacher/dashboard", follow_redirects=True)
    assert r.status_code == 200
    assert b"Sign In" in r.data


def test_dashboard_accessible_to_teacher(teacher_client):
    r = teacher_client.get("/school/teacher/dashboard")
    assert r.status_code == 200
    assert b"Overview" in r.data


def test_bulk_assign_page(teacher_client):
    r = teacher_client.get("/school/teacher/bulk-assign")
    assert r.status_code == 200


def test_import_page(teacher_client):
    r = teacher_client.get("/school/teacher/import")
    assert r.status_code == 200


def test_templates_page(teacher_client):
    r = teacher_client.get("/school/teacher/templates")
    assert r.status_code == 200
