# Assignments Dashboard

A Flask web app for homeschool assignments management with multi-child views, per-day checklists, and rich completion interactions.

## Features

- **Teacher Overview Dashboard**: See all students' progress at a glance
- **Student Daily View**: Satisfying completion UI with timestamps
- **Bulk Assignment Creation**: Assign to multiple students over date ranges
- **CSV Import**: Upload, preview, validate, and confirm bulk assignments
- **Flexible Annotations**: Schema-driven completion data per subject
- **API v1**: REST endpoints for external integrations
- **Sub-path Routing**: Runs under `/school/` (configurable)

## Quick Start (Local Dev)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env for your settings

# Initialize database
FLASK_APP=wsgi:application flask db init
FLASK_APP=wsgi:application flask db migrate -m "init"
FLASK_APP=wsgi:application flask db upgrade

# Seed sample data
python seed.py

# Run dev server
FLASK_APP=wsgi:application FLASK_DEBUG=1 BASE_PATH=/school flask run --port 5000
# Visit: http://localhost:5000/school/
```

### Default Credentials (after seeding)

| Role    | Username | Password    |
|---------|----------|-------------|
| Teacher | teacher  | teacher123  |
| Student | alice    | student123  |
| Student | bob      | student123  |

## Docker Compose (Production)

```bash
# Copy and edit environment
cp .env.example .env
# Edit DOMAIN, ACME_EMAIL, SECRET_KEY, DB_PASSWORD

# Start all services
make up

# Run database migrations
make migrate

# Seed sample data (optional)
make seed

# App is now at https://yourdomain.com/school/
```

## Running Tests

```bash
pytest tests/ -v
```

## CSV Import Format

Download the sample CSV template from `/school/examples/assignments_import.csv`.

Required columns: `date, student, subject, title`

Optional columns: `details, links, template, annotation_json, duration_minutes, status, completed_at`

## Architecture

- **Flask** with Blueprint-based routing
- **SQLAlchemy** + **Flask-Migrate** for database
- **Flask-Login** + **Flask-WTF** for auth + CSRF
- **Bootstrap 5** + **HTMX** for frontend interactions
- **Caddy** reverse proxy with automatic HTTPS

## Sub-path Configuration

All routes are served under `BASE_PATH` (default: `/school`). Configure via:
- `BASE_PATH` environment variable
- `APPLICATION_ROOT` in Flask config
- ProxyFix middleware for Caddy headers

## API Endpoints

- `GET /school/api/v1/students` - List all students (teacher only)
- `GET /school/api/v1/students/{id}/assignments?date=YYYY-MM-DD` - Get assignments
- `GET/PUT /school/api/v1/assignments/{id}/completion` - Get/update completion data