import csv
import io
import json
from datetime import date, datetime, timezone
from app.models import StudentProfile, Subject, AssignmentTemplate, AssignmentInstance, Completion
from app import db

REQUIRED_COLUMNS = {"date", "student", "subject", "title"}


def parse_links(raw):
    """Parse links from JSON array or 'label|url;label|url' format."""
    if not raw or not raw.strip():
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    links = []
    for part in raw.split(";"):
        part = part.strip()
        if "|" in part:
            label, url = part.split("|", 1)
            links.append({"label": label.strip(), "url": url.strip()})
        elif part:
            links.append({"label": part, "url": part})
    return links


def parse_csv_preview(content, create_subjects=False):
    """Parse CSV content and return (rows, global_errors)."""
    reader = csv.DictReader(io.StringIO(content))

    fieldnames = reader.fieldnames or []
    missing = REQUIRED_COLUMNS - set(f.strip().lower() for f in fieldnames)
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}"]

    rows = []
    for i, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items()}
        row_errors = []

        # Validate date
        date_str = row.get("date", "")
        try:
            row["_date"] = date.fromisoformat(date_str)
        except ValueError:
            row_errors.append(f"Invalid date: {date_str!r}")
            row["_date"] = None

        # Find student
        student_val = row.get("student", "")
        student = (
            StudentProfile.query.join(StudentProfile.user).filter_by(username=student_val).first()
            or StudentProfile.query.filter_by(display_name=student_val).first()
        )
        if not student:
            row_errors.append(f"Student not found: {student_val!r}")
        row["_student"] = student

        # Find/create subject
        subject_val = row.get("subject", "")
        subject = Subject.query.filter(Subject.name.ilike(subject_val)).first()
        if not subject:
            if create_subjects and subject_val:
                subject = Subject(name=subject_val, sort_order=99)
                db.session.add(subject)
                db.session.flush()
            else:
                row_errors.append(f"Subject not found: {subject_val!r}")
        row["_subject"] = subject

        # Optional template
        template_val = row.get("template", "")
        template = None
        if template_val:
            template = AssignmentTemplate.query.filter_by(title=template_val).first()
            if not template and template_val.isdigit():
                template = AssignmentTemplate.query.get(int(template_val))
        row["_template"] = template

        # Parse links
        row["_links"] = parse_links(row.get("links", ""))

        # Validate annotation JSON
        annotation = {}
        annotation_raw = row.get("annotation_json", "")
        if annotation_raw:
            try:
                annotation = json.loads(annotation_raw)
            except json.JSONDecodeError:
                row_errors.append("Invalid annotation_json")
        row["_annotation"] = annotation

        # Duration
        duration = None
        if row.get("duration_minutes"):
            try:
                duration = int(row["duration_minutes"])
            except ValueError:
                row_errors.append("Invalid duration_minutes")
        row["_duration"] = duration

        # Status
        status = row.get("status", "assigned")
        if status not in ("assigned", "complete"):
            status = "assigned"
        row["_status"] = status

        # completed_at
        completed_at = None
        if row.get("completed_at"):
            try:
                completed_at = datetime.fromisoformat(row["completed_at"])
            except ValueError:
                row_errors.append(f"Invalid completed_at: {row['completed_at']!r}")
        elif status == "complete":
            completed_at = datetime.now(timezone.utc)
        row["_completed_at"] = completed_at

        row["errors"] = row_errors
        row["row_num"] = i
        rows.append(row)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return rows, []


def commit_import(valid_rows, on_duplicate="skip", created_by=None):
    created = skipped = errors = 0
    for row in valid_rows:
        if row.get("errors"):
            errors += 1
            continue
        student = row["_student"]
        subject = row["_subject"]
        d = row["_date"]
        title = row.get("title", "")

        if not student or not subject or not d or not title:
            errors += 1
            continue

        existing = AssignmentInstance.query.filter_by(
            student_id=student.id,
            date=d,
            title=title,
        ).first()

        if existing:
            if on_duplicate == "skip":
                skipped += 1
                continue
            elif on_duplicate == "update":
                existing.details = row.get("details")
                existing.subject_id = subject.id
                db.session.add(existing)
                inst = existing
                created += 1
            else:
                skipped += 1
                continue
        else:
            inst = AssignmentInstance(
                student_id=student.id,
                subject_id=subject.id,
                template_id=row["_template"].id if row.get("_template") else None,
                date=d,
                title=title,
                details=row.get("details"),
                links_json=json.dumps(row["_links"]) if row["_links"] else None,
                status=row["_status"],
                created_by=created_by,
            )
            db.session.add(inst)
            created += 1

        # Completion record
        if row["_status"] == "complete" or row.get("_annotation") or row.get("_duration"):
            db.session.flush()
            if not inst.completion:
                c = Completion(
                    assignment_instance_id=inst.id,
                    completed_at=row["_completed_at"],
                    duration_minutes=row["_duration"],
                )
                if row.get("_annotation"):
                    c.annotation = row["_annotation"]
                db.session.add(c)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        errors += 1

    return created, skipped, errors
