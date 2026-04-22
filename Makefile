.PHONY: help install dev test lint build docker up down clean seed docs

help: ## Show this help message
	@echo "FleetOps Development Commands"
	@echo "============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev: ## Start development servers (backend + frontend)
	@echo "Starting FleetOps in development mode..."
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v --tb=short
	@echo "Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

test-backend: ## Run backend tests only
	cd backend && pytest tests/ -v --tb=short

test-frontend: ## Run frontend tests only
	cd frontend && npm test -- --watchAll=false

coverage: ## Run tests with coverage
	cd backend && pytest tests/ --cov=app --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

lint: ## Run all linters
	@echo "Linting backend..."
	cd backend && flake8 app/ --max-line-length=100
	cd backend && black --check app/
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: ## Format all code
	cd backend && black app/
	cd backend && isort app/
	cd frontend && npm run format

build: ## Build for production
	@echo "Building backend..."
	cd backend && docker build -t fleetops-backend .
	@echo "Building frontend..."
	cd frontend && npm run build

docker: ## Build and run with Docker Compose
	docker-compose up --build -d

docker-prod: ## Build and run production Docker Compose
	docker-compose -f docker-compose.prod.yml up --build -d

up: ## Start Docker containers
	docker-compose up -d

down: ## Stop Docker containers
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

seed: ## Seed database with demo data
	cd backend && python scripts/seed_demo.py

db-migrate: ## Run database migrations
	cd backend && alembic upgrade head

db-rollback: ## Rollback database migrations
	cd backend && alembic downgrade -1

clean: ## Clean up build artifacts and dependencies
	@echo "Cleaning..."
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +
	find . -type d -name build -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v

ssh: ## SSH into backend container
	docker-compose exec backend bash

ssh-db: ## SSH into database container
	docker-compose exec postgres psql -U fleetops -d fleetops

docs: ## Generate API documentation
	cd backend && python -c "from app.core.docs import generate_openapi_schema; generate_openapi_schema()"
	@echo "API docs generated. Visit /docs when backend is running."

status: ## Show project status
	@echo "FleetOps Status"
	@echo "==============="
	@echo "Backend commits: $$(cd backend && git log --oneline 2>/dev/null | wc -l || echo 'N/A')"
	@echo "Frontend commits: $$(cd frontend && git log --oneline 2>/dev/null | wc -l || echo 'N/A')"
	@echo "Docker status:"
	@docker-compose ps 2>/dev/null || echo "Docker not running"

# Default target
.DEFAULT_GOAL := help
