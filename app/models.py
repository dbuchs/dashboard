from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import json


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="student")  # teacher | student
    student_profile_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=True)
    student_profile = db.relationship("StudentProfile", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(128), nullable=False)
    grade_level = db.Column(db.String(32), nullable=True)
    user = db.relationship("User", back_populates="student_profile", uselist=False)
    assignment_instances = db.relationship("AssignmentInstance", back_populates="student", lazy="dynamic")


class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    annotation_schema_json = db.Column(db.Text, nullable=True)  # JSON schema string

    templates = db.relationship("AssignmentTemplate", back_populates="subject", lazy="dynamic")
    assignment_instances = db.relationship("AssignmentInstance", back_populates="subject", lazy="dynamic")

    @property
    def annotation_schema(self):
        if self.annotation_schema_json:
            return json.loads(self.annotation_schema_json)
        return None

    @annotation_schema.setter
    def annotation_schema(self, value):
        self.annotation_schema_json = json.dumps(value) if value else None


class AssignmentTemplate(db.Model):
    __tablename__ = "assignment_templates"
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    details = db.Column(db.Text, nullable=True)
    links_json = db.Column(db.Text, nullable=True)  # JSON array [{label, url}]
    default_annotation_json = db.Column(db.Text, nullable=True)
    annotation_schema_override_json = db.Column(db.Text, nullable=True)

    subject = db.relationship("Subject", back_populates="templates")
    instances = db.relationship("AssignmentInstance", back_populates="template", lazy="dynamic")

    @property
    def links(self):
        return json.loads(self.links_json) if self.links_json else []

    @links.setter
    def links(self, value):
        self.links_json = json.dumps(value) if value else None


class AssignmentInstance(db.Model):
    __tablename__ = "assignment_instances"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("assignment_templates.id"), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    title = db.Column(db.String(256), nullable=False)
    details = db.Column(db.Text, nullable=True)
    links_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default="assigned")  # assigned | complete
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("StudentProfile", back_populates="assignment_instances")
    subject = db.relationship("Subject", back_populates="assignment_instances")
    template = db.relationship("AssignmentTemplate", back_populates="instances")
    completion = db.relationship(
        "Completion", back_populates="assignment_instance",
        uselist=False, cascade="all, delete-orphan"
    )
    creator = db.relationship("User", foreign_keys=[created_by])

    @property
    def links(self):
        return json.loads(self.links_json) if self.links_json else []

    @links.setter
    def links(self, value):
        self.links_json = json.dumps(value) if value else None

    @property
    def is_complete(self):
        return self.status == "complete"


class Completion(db.Model):
    __tablename__ = "completions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_instance_id = db.Column(
        db.Integer, db.ForeignKey("assignment_instances.id"), nullable=False, unique=True
    )
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    annotation_json = db.Column(db.Text, nullable=True)
    grader_notes = db.Column(db.Text, nullable=True)

    assignment_instance = db.relationship("AssignmentInstance", back_populates="completion")

    @property
    def annotation(self):
        return json.loads(self.annotation_json) if self.annotation_json else {}

    @annotation.setter
    def annotation(self, value):
        self.annotation_json = json.dumps(value) if value else None
