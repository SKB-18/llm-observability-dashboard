.PHONY: help install test lint format clean build up down logs seed

help:
	@echo "LLM Observability Dashboard - Available commands:"
	@echo ""
	@echo "  make install       - Install all dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make test-backend  - Run backend tests only"
	@echo "  make test-frontend - Run frontend tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code (black, isort, prettier)"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start services with Docker Compose"
	@echo "  make down          - Stop services"
	@echo "  make logs          - View service logs"
	@echo "  make seed          - Seed database with sample data"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

test:
	pytest backend/tests/ -v
	cd frontend && npm run test

test-backend:
	pytest backend/tests/ -v

test-frontend:
	cd frontend && npm run test

test-coverage:
	pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term-missing

lint:
	flake8 backend/
	cd frontend && npm run lint

format:
	black backend/
	isort backend/
	cd frontend && npm run format

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
	cd frontend && rm -rf node_modules dist

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

seed:
	python -m backend.seed_data
