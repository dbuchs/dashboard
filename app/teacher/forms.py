from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, SelectMultipleField,
    DateField, BooleanField, SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length
from datetime import date


class BulkAssignForm(FlaskForm):
    student_ids = SelectMultipleField("Students", validators=[DataRequired()])
    subject_id = SelectField("Subject", validators=[DataRequired()])
    template_id = SelectField("Template (optional)", validators=[Optional()])
    title = StringField("Title", validators=[DataRequired(), Length(1, 256)])
    details = TextAreaField("Details", validators=[Optional()])
    start_date = DateField("Start Date", validators=[DataRequired()], default=date.today)
    end_date = DateField("End Date (optional)", validators=[Optional()])
    skip_weekends = BooleanField("Skip Weekends", default=True)
    submit = SubmitField("Create Assignments")


class TemplateForm(FlaskForm):
    subject_id = SelectField("Subject", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(1, 256)])
    details = TextAreaField("Details", validators=[Optional()])
    submit = SubmitField("Save Template")


class ImportForm(FlaskForm):
    csv_file = FileField("CSV File", validators=[
        FileRequired(),
        FileAllowed(["csv"], "CSV files only!")
    ])
    create_subjects = BooleanField("Create missing subjects automatically")
    on_duplicate = SelectField(
        "On duplicate (same student+date+title)",
        choices=[("skip", "Skip"), ("update", "Update")],
        default="skip",
    )
    submit = SubmitField("Upload & Preview")
