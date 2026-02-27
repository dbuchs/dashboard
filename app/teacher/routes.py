from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.teacher import bp
from app.models import (
    User, StudentProfile, Subject, AssignmentTemplate,
    AssignmentInstance, Completion,
)
from datetime import date, timedelta, datetime, timezone
import json


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "teacher":
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated


@bp.route("/")
@bp.route("/dashboard")
@login_required
@teacher_required
def dashboard():
    selected_date_str = request.args.get("date", date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()

    students = StudentProfile.query.all()
    student_data = []
    for student in students:
        instances = AssignmentInstance.query.filter_by(
            student_id=student.id, date=selected_date
        ).all()
        total = len(instances)
        completed = sum(1 for i in instances if i.is_complete)
        student_data.append({
            "student": student,
            "total": total,
            "completed": completed,
            "instances": instances,
        })

    return render_template(
        "teacher/dashboard.html",
        student_data=student_data,
        selected_date=selected_date,
        today=date.today(),
    )


@bp.route("/student/<int:student_id>/daily")
@login_required
@teacher_required
def student_daily(student_id):
    selected_date_str = request.args.get("date", date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()
    student = StudentProfile.query.get_or_404(student_id)
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
        "teacher/student_daily.html",
        student=student,
        grouped=grouped,
        selected_date=selected_date,
        today=date.today(),
    )


@bp.route("/bulk-assign", methods=["GET", "POST"])
@login_required
@teacher_required
def bulk_assign():
    from app.teacher.forms import BulkAssignForm
    form = BulkAssignForm()
    students = StudentProfile.query.all()
    subjects = Subject.query.order_by(Subject.sort_order).all()
    templates = AssignmentTemplate.query.all()

    form.student_ids.choices = [(str(s.id), s.display_name) for s in students]
    form.subject_id.choices = [(str(s.id), s.name) for s in subjects]
    form.template_id.choices = [("", "-- Ad-hoc (no template) --")] + [
        (str(t.id), f"{t.subject.name}: {t.title}") for t in templates
    ]

    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data or start
        student_ids = [int(x) for x in form.student_ids.data]
        subject_id = int(form.subject_id.data)
        template_id = int(form.template_id.data) if form.template_id.data else None

        created = 0
        current_date = start
        while current_date <= end:
            if form.skip_weekends.data and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            for sid in student_ids:
                inst = AssignmentInstance(
                    student_id=sid,
                    subject_id=subject_id,
                    template_id=template_id,
                    date=current_date,
                    title=form.title.data,
                    details=form.details.data,
                    status="assigned",
                    created_by=current_user.id,
                )
                db.session.add(inst)
                created += 1
            current_date += timedelta(days=1)

        db.session.commit()
        flash(f"Created {created} assignment(s).", "success")
        return redirect(url_for("teacher.dashboard"))

    return render_template(
        "teacher/bulk_assign.html",
        form=form,
        students=students,
        subjects=subjects,
        templates=templates,
    )


@bp.route("/import", methods=["GET", "POST"])
@login_required
@teacher_required
def import_csv():
    from app.teacher.forms import ImportForm
    from app.services.csv_import import parse_csv_preview
    form = ImportForm()
    if form.validate_on_submit():
        f = form.csv_file.data
        import io
        content = f.read().decode("utf-8-sig")
        create_subjects = form.create_subjects.data
        on_duplicate = form.on_duplicate.data
        rows, errors = parse_csv_preview(content, create_subjects=create_subjects)
        import flask
        flask.session["csv_import_data"] = content
        flask.session["csv_create_subjects"] = create_subjects
        flask.session["csv_on_duplicate"] = on_duplicate
        return render_template(
            "teacher/import_preview.html",
            rows=rows,
            errors=errors,
            create_subjects=create_subjects,
            on_duplicate=on_duplicate,
        )
    return render_template("teacher/import.html", form=form)


@bp.route("/import/confirm", methods=["POST"])
@login_required
@teacher_required
def import_confirm():
    from app.services.csv_import import parse_csv_preview, commit_import
    import flask
    content = flask.session.get("csv_import_data")
    create_subjects = flask.session.get("csv_create_subjects", False)
    on_duplicate = flask.session.get("csv_on_duplicate", "skip")
    if not content:
        flash("No import data found. Please re-upload.", "warning")
        return redirect(url_for("teacher.import_csv"))
    rows, errors = parse_csv_preview(content, create_subjects=create_subjects)
    valid_rows = [r for r in rows if not r.get("errors")]
    created, skipped, error_count = commit_import(
        valid_rows, on_duplicate=on_duplicate, created_by=current_user.id
    )
    flask.session.pop("csv_import_data", None)
    flash(
        f"Import complete: {created} created, {skipped} skipped, {error_count} errors.",
        "success",
    )
    return redirect(url_for("teacher.dashboard"))


@bp.route("/templates")
@login_required
@teacher_required
def templates_list():
    templates = (
        AssignmentTemplate.query
        .join(Subject)
        .order_by(Subject.sort_order, AssignmentTemplate.title)
        .all()
    )
    return render_template("teacher/templates_list.html", templates=templates)


@bp.route("/templates/new", methods=["GET", "POST"])
@login_required
@teacher_required
def template_new():
    from app.teacher.forms import TemplateForm
    form = TemplateForm()
    subjects = Subject.query.order_by(Subject.sort_order).all()
    form.subject_id.choices = [(str(s.id), s.name) for s in subjects]
    if form.validate_on_submit():
        t = AssignmentTemplate(
            subject_id=int(form.subject_id.data),
            title=form.title.data,
            details=form.details.data,
        )
        db.session.add(t)
        db.session.commit()
        flash("Template created.", "success")
        return redirect(url_for("teacher.templates_list"))
    return render_template("teacher/template_form.html", form=form, template=None)


@bp.route("/templates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required
@teacher_required
def template_edit(template_id):
    from app.teacher.forms import TemplateForm
    t = AssignmentTemplate.query.get_or_404(template_id)
    form = TemplateForm(obj=t)
    subjects = Subject.query.order_by(Subject.sort_order).all()
    form.subject_id.choices = [(str(s.id), s.name) for s in subjects]
    if form.validate_on_submit():
        t.subject_id = int(form.subject_id.data)
        t.title = form.title.data
        t.details = form.details.data
        db.session.commit()
        flash("Template updated.", "success")
        return redirect(url_for("teacher.templates_list"))
    form.subject_id.data = str(t.subject_id)
    return render_template("teacher/template_form.html", form=form, template=t)


@bp.route("/templates/<int:template_id>/delete", methods=["POST"])
@login_required
@teacher_required
def template_delete(template_id):
    t = AssignmentTemplate.query.get_or_404(template_id)
    db.session.delete(t)
    db.session.commit()
    flash("Template deleted.", "success")
    return redirect(url_for("teacher.templates_list"))


@bp.route("/assignment/<int:instance_id>/toggle", methods=["POST"])
@login_required
@teacher_required
def toggle_assignment(instance_id):
    inst = AssignmentInstance.query.get_or_404(instance_id)
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
    return render_template("partials/assignment_row.html", inst=inst)
