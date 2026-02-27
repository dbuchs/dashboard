def test_login_page(client):
    r = client.get("/school/auth/login")
    assert r.status_code == 200
    assert b"Sign In" in r.data


def test_login_success(client):
    r = client.post("/school/auth/login", data={
        "username": "teacher", "password": "teacher123"
    }, follow_redirects=True)
    assert r.status_code == 200


def test_login_failure(client):
    r = client.post("/school/auth/login", data={
        "username": "teacher", "password": "wrong"
    }, follow_redirects=True)
    assert b"Invalid username or password" in r.data


def test_logout(teacher_client):
    r = teacher_client.get("/school/auth/logout", follow_redirects=True)
    assert r.status_code == 200
