from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import StudentProfile, AssignmentInstance, Completion, Subject
from datetime import date, datetime, timezone
import json


def api_teacher_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "teacher":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated


@bp.route("/students")
@login_required
@api_teacher_required
def list_students():
    students = StudentProfile.query.all()
    return jsonify([
        {"id": s.id, "display_name": s.display_name, "grade_level": s.grade_level}
        for s in students
    ])


@bp.route("/students/<int:student_id>/assignments")
@login_required
def student_assignments(student_id):
    if current_user.role != "teacher":
        if not current_user.student_profile or current_user.student_profile.id != student_id:
            return jsonify({"error": "Forbidden"}), 403

    date_str = request.args.get("date")
    query = AssignmentInstance.query.filter_by(student_id=student_id)
    if date_str:
        try:
            d = date.fromisoformat(date_str)
            query = query.filter_by(date=d)
        except ValueError:
            return jsonify({"error": "Invalid date"}), 400

    instances = query.all()
    return jsonify([
        {
            "id": i.id,
            "title": i.title,
            "subject": i.subject.name,
            "date": i.date.isoformat(),
            "status": i.status,
            "details": i.details,
            "completion": {
                "completed_at": (
                    i.completion.completed_at.isoformat()
                    if i.completion and i.completion.completed_at else None
                ),
                "duration_minutes": i.completion.duration_minutes if i.completion else None,
                "annotation": i.completion.annotation if i.completion else None,
            } if i.completion else None,
        }
        for i in instances
    ])


@bp.route("/assignments/<int:instance_id>/completion", methods=["GET", "PUT"])
@login_required
def assignment_completion(instance_id):
    inst = AssignmentInstance.query.get_or_404(instance_id)

    if current_user.role != "teacher":
        if not current_user.student_profile or current_user.student_profile.id != inst.student_id:
            return jsonify({"error": "Forbidden"}), 403

    if request.method == "GET":
        if not inst.completion:
            return jsonify(None)
        c = inst.completion
        return jsonify({
            "id": c.id,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            "duration_minutes": c.duration_minutes,
            "annotation": c.annotation,
            "grader_notes": c.grader_notes,
        })

    # PUT
    data = request.get_json() or {}
    if not inst.completion:
        c = Completion(assignment_instance_id=inst.id)
        db.session.add(c)
        inst.completion = c
    else:
        c = inst.completion

    if "duration_minutes" in data:
        c.duration_minutes = data["duration_minutes"]
    if "annotation" in data:
        c.annotation = data["annotation"]
    if "grader_notes" in data:
        c.grader_notes = data["grader_notes"]
    if data.get("completed_at"):
        try:
            c.completed_at = datetime.fromisoformat(data["completed_at"])
        except ValueError:
            return jsonify({"error": "Invalid completed_at"}), 400

    if not c.completed_at:
        c.completed_at = datetime.now(timezone.utc)
    inst.status = "complete"
    db.session.commit()
    return jsonify({"success": True})
