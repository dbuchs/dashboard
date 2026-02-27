.PHONY: up down logs migrate seed create-admin test build dev init-db

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec app flask db upgrade

seed:
	docker compose exec app python seed.py

create-admin:
	@read -p "Username: " user; \
	read -s -p "Password: " pass; echo; \
	docker compose exec app python -c "\
	from app import create_app, db; \
	from app.models import User; \
	app = create_app(); \
	app.app_context().push(); \
	u = User(username='$$user', role='teacher'); \
	u.set_password('$$pass'); \
	db.session.add(u); \
	db.session.commit(); \
	print('Created teacher:', '$$user')"

test:
	pytest tests/ -v

dev:
	FLASK_APP=wsgi:application FLASK_DEBUG=1 flask run --port 5000

init-db:
	flask --app wsgi:application db init
	flask --app wsgi:application db migrate -m "Initial migration"
	flask --app wsgi:application db upgrade
