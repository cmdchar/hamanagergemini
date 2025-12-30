.PHONY: help install dev test lint format clean build deploy

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies
	pip install -r requirements-dev.txt
	cd dashboard && npm install

dev:  ## Start development servers
	docker-compose up

dev-backend:  ## Start only backend
	cd orchestrator && uvicorn main:app --reload --port 8080

dev-frontend:  ## Start only frontend
	cd dashboard && npm run dev

test:  ## Run all tests
	pytest tests/ -v

test-unit:  ## Run unit tests
	pytest tests/unit -v

test-integration:  ## Run integration tests
	pytest tests/integration -v

test-e2e:  ## Run end-to-end tests
	pytest tests/e2e -v

coverage:  ## Run tests with coverage
	pytest --cov=orchestrator --cov=addon --cov-report=html tests/
	@echo "Coverage report: htmlcov/index.html"

lint:  ## Run linters
	flake8 orchestrator/ addon/
	mypy orchestrator/
	cd dashboard && npm run lint

format:  ## Format code
	black orchestrator/ addon/ tests/
	isort orchestrator/ addon/ tests/
	cd dashboard && npm run format

clean:  ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	cd dashboard && rm -rf dist/ node_modules/.cache/

build:  ## Build all containers
	docker-compose build

build-addon:  ## Build add-on image
	cd addon && docker build -t ha-config-sync:latest .

build-orchestrator:  ## Build orchestrator image
	cd orchestrator && docker build -t ha-config-orchestrator:latest .

build-dashboard:  ## Build dashboard
	cd dashboard && npm run build

deploy-dev:  ## Deploy to development
	docker-compose -f docker-compose.dev.yml up -d

deploy-prod:  ## Deploy to production
	docker-compose -f docker-compose.prod.yml up -d

logs:  ## Show docker logs
	docker-compose logs -f

down:  ## Stop all services
	docker-compose down

restart:  ## Restart all services
	docker-compose restart

shell-orchestrator:  ## Shell into orchestrator container
	docker-compose exec orchestrator /bin/bash

shell-addon:  ## Shell into add-on container
	docker-compose exec addon /bin/bash

db-migrate:  ## Run database migrations
	cd orchestrator && alembic upgrade head

db-reset:  ## Reset database
	cd orchestrator && alembic downgrade base && alembic upgrade head

pre-commit:  ## Run pre-commit hooks
	pre-commit run --all-files

release:  ## Create a new release
	@echo "Creating release..."
	@read -p "Enter version (e.g., 1.0.0): " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version

docs:  ## Build documentation
	cd docs && mkdocs build

docs-serve:  ## Serve documentation locally
	cd docs && mkdocs serve
