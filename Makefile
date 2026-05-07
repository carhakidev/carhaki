.PHONY: run migrate shell superuser test lint

# Run dev server (SQLite, no Docker required)
run:
	python manage.py runserver

# Run with Docker Compose
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

# Database
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

# Create superuser
superuser:
	python manage.py createsuperuser

# Django shell
shell:
	python manage.py shell

# Tests
test:
	pytest

# Linting
lint:
	ruff check .

# Collect static (for production)
static:
	python manage.py collectstatic --noinput --settings=carhaki.settings.production

# Quick dev setup (first time)
setup:
	pip install -r requirements/development.txt
	python manage.py migrate
	python manage.py createsuperuser
