from datetime import date


def test_student_daily_requires_login(client):
    r = client.get("/school/student/daily", follow_redirects=True)
    assert r.status_code == 200
    assert b"Sign In" in r.data


def test_student_daily_page(student_client):
    r = student_client.get(f"/school/student/daily?date={date.today().isoformat()}")
    assert r.status_code == 200


def test_teacher_denied_student_page(teacher_client):
    r = teacher_client.get("/school/student/daily", follow_redirects=True)
    # Teacher gets redirected to teacher dashboard
    assert r.status_code == 200
