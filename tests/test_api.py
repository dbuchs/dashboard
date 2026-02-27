def test_api_students_requires_auth(client):
    r = client.get("/school/api/v1/students")
    assert r.status_code == 401 or r.status_code == 302


def test_api_students(teacher_client):
    r = teacher_client.get("/school/api/v1/students")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_api_assignments(teacher_client, app):
    with app.app_context():
        from app.models import StudentProfile
        student = StudentProfile.query.first()
        student_id = student.id
    r = teacher_client.get(f"/school/api/v1/students/{student_id}/assignments")
    assert r.status_code == 200


def test_api_student_forbidden_other(student_client, app):
    with app.app_context():
        from app.models import StudentProfile
        students = StudentProfile.query.all()
        other = next((s for s in students if s.display_name != "Alice"), None)
        other_id = other.id if other else None
    if other_id:
        r = student_client.get(f"/school/api/v1/students/{other_id}/assignments")
        assert r.status_code == 403
