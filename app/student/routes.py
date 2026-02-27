from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.student import bp
from app.models import AssignmentInstance, Completion, Subject
from datetime import date, datetime, timezone
import json


@bp.route("/")
@bp.route("/daily")
@login_required
def daily():
    if current_user.role == "teacher":
        return redirect(url_for("teacher.dashboard"))

    student = current_user.student_profile
    if not student:
        flash("No student profile linked to your account.", "warning")
        return redirect(url_for("auth.login"))

    selected_date_str = request.args.get("date", date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()

    instances = (
        AssignmentInstance.query
        .filter_by(student_id=student.id, date=selected_date)
        .join(Subject)
        .order_by(Subject.sort_order, AssignmentInstance.id)
        .all()
    )
    grouped = {}
    for inst in instances:
        subj = inst.subject.name
        grouped.setdefault(subj, []).append(inst)

    return render_template(
        "student/daily.html",
        student=student,
        grouped=grouped,
        selected_date=selected_date,
        today=date.today(),
    )


@bp.route("/assignment/<int:instance_id>/toggle", methods=["POST"])
@login_required
def toggle_assignment(instance_id):
    inst = AssignmentInstance.query.get_or_404(instance_id)
    if current_user.role != "teacher" and (
        not current_user.student_profile
        or current_user.student_profile.id != inst.student_id
    ):
        from flask import abort
        abort(403)

    if inst.is_complete:
        inst.status = "assigned"
        if inst.completion:
            db.session.delete(inst.completion)
    else:
        inst.status = "complete"
        if not inst.completion:
            c = Completion(
                assignment_instance_id=inst.id,
                completed_at=datetime.now(timezone.utc),
            )
            db.session.add(c)
        else:
            inst.completion.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    return render_template("partials/assignment_card.html", inst=inst)


@bp.route("/assignment/<int:instance_id>/annotate", methods=["POST"])
@login_required
def annotate_assignment(instance_id):
    inst = AssignmentInstance.query.get_or_404(instance_id)
    if current_user.role != "teacher" and (
        not current_user.student_profile
        or current_user.student_profile.id != inst.student_id
    ):
        from flask import abort
        abort(403)

    annotation_data = request.form.get("annotation_json", "{}")
    try:
        annotation = json.loads(annotation_data)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    from app.services.annotation_validation import validate_annotation
    subject = inst.subject
    schema = None
    if inst.template and inst.template.annotation_schema_override_json:
        schema = json.loads(inst.template.annotation_schema_override_json)
    elif subject.annotation_schema:
        schema = subject.annotation_schema

    if schema:
        errors = validate_annotation(annotation, schema)
        if errors:
            return jsonify({"error": errors}), 400

    if not inst.completion:
        c = Completion(
            assignment_instance_id=inst.id,
            annotation_json=json.dumps(annotation),
        )
        db.session.add(c)
    else:
        inst.completion.annotation_json = json.dumps(annotation)
    db.session.commit()
    return jsonify({"success": True})
