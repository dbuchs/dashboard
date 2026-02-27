import pytest
from sqlalchemy.pool import StaticPool
from app import create_app, db as _db
from app.models import User, StudentProfile, Subject, AssignmentInstance
from datetime import date


@pytest.fixture(scope="session")
def app():
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "BASE_PATH": "/school",
    })

    # Push context only for DB setup, then pop so each request gets a fresh g
    ctx = _app.app_context()
    ctx.push()

    _db.create_all()

    teacher = User(username="teacher", role="teacher")
    teacher.set_password("teacher123")
    _db.session.add(teacher)

    profile = StudentProfile(display_name="Alice", grade_level="5th")
    _db.session.add(profile)
    _db.session.flush()

    student = User(username="alice", role="student", student_profile_id=profile.id)
    student.set_password("student123")
    _db.session.add(student)

    subj = Subject(name="Math", sort_order=1)
    _db.session.add(subj)
    _db.session.flush()

    inst = AssignmentInstance(
        student_id=profile.id,
        subject_id=subj.id,
        date=date.today(),
        title="Test Assignment",
        status="assigned",
    )
    _db.session.add(inst)
    _db.session.commit()

    ctx.pop()  # Pop so each test request gets its own fresh app context and g

    yield _app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def teacher_client(app):
    with app.test_client() as c:
        c.post("/school/auth/login", data={"username": "teacher", "password": "teacher123"})
        yield c


@pytest.fixture
def student_client(app):
    with app.test_client() as c:
        c.post("/school/auth/login", data={"username": "alice", "password": "student123"})
        yield c
