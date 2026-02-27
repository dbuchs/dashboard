"""Seed database with sample data."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, StudentProfile, Subject, AssignmentTemplate, AssignmentInstance
from datetime import date, timedelta
import json


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        subjects_data = [
            ("Math", 1, json.dumps({
                "type": "object",
                "properties": {
                    "lesson_number": {"type": ["string", "number"]},
                    "correct": {"type": "number"},
                    "total": {"type": "number"},
                    "notes": {"type": "string"},
                }
            })),
            ("Reading", 2, json.dumps({
                "type": "object",
                "properties": {
                    "book_title": {"type": "string"},
                    "pages_from": {"type": "number"},
                    "pages_to": {"type": "number"},
                    "student_summary": {"type": "string"},
                    "grade": {"type": "string"},
                    "notes": {"type": "string"},
                }
            })),
            ("Latin", 3, json.dumps({
                "type": "object",
                "properties": {
                    "minutes_translating": {"type": "number"},
                    "minutes_vocab": {"type": "number"},
                    "notes": {"type": "string"},
                }
            })),
            ("Writing", 4, None),
            ("Science", 5, None),
        ]

        subjects = {}
        for name, order, schema in subjects_data:
            s = Subject.query.filter_by(name=name).first()
            if not s:
                s = Subject(name=name, sort_order=order, annotation_schema_json=schema)
                db.session.add(s)
            subjects[name] = s
        db.session.flush()

        teacher = User.query.filter_by(username="teacher").first()
        if not teacher:
            teacher = User(username="teacher", role="teacher")
            teacher.set_password("teacher123")
            db.session.add(teacher)

        student_profiles = []
        for name, grade, uname in [
            ("Alice Smith", "5th", "alice"),
            ("Bob Smith", "3rd", "bob"),
        ]:
            profile = StudentProfile.query.filter_by(display_name=name).first()
            if not profile:
                profile = StudentProfile(display_name=name, grade_level=grade)
                db.session.add(profile)
                db.session.flush()

            user = User.query.filter_by(username=uname).first()
            if not user:
                user = User(username=uname, role="student", student_profile_id=profile.id)
                user.set_password("student123")
                db.session.add(user)
            student_profiles.append(profile)

        db.session.flush()

        tmpl_data = [
            ("Math", "Singapore Math Lesson", "Complete lesson problems"),
            ("Reading", "Daily Reading", "Read assigned chapters"),
            ("Latin", "Latin Grammar", "Complete Latin exercises"),
        ]
        for subj_name, title, details in tmpl_data:
            subj = subjects.get(subj_name)
            if subj and not AssignmentTemplate.query.filter_by(title=title).first():
                t = AssignmentTemplate(subject_id=subj.id, title=title, details=details)
                db.session.add(t)

        db.session.flush()

        today = date.today()
        for offset in range(3):
            d = today + timedelta(days=offset)
            if d.weekday() >= 5:
                continue
            for profile in student_profiles:
                for subj_name, title in [
                    ("Math", "Math Lesson"),
                    ("Reading", "Reading"),
                    ("Latin", "Latin"),
                ]:
                    subj = subjects.get(subj_name)
                    if subj:
                        existing = AssignmentInstance.query.filter_by(
                            student_id=profile.id, date=d, title=title
                        ).first()
                        if not existing:
                            inst = AssignmentInstance(
                                student_id=profile.id,
                                subject_id=subj.id,
                                date=d,
                                title=title,
                                status="assigned",
                                created_by=teacher.id if teacher.id else 1,
                            )
                            db.session.add(inst)

        db.session.commit()
        print("Seeded successfully!")
        print("  Teacher: teacher / teacher123")
        print("  Students: alice / student123, bob / student123")


if __name__ == "__main__":
    seed()
