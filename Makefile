.PHONY: install dev-db dev-backend dev-frontend stop clean

# Install dependencies for both ends
install:
	cd frontend && npm install
	cd backend && uv sync

# Start the database only
dev-db:
	docker-compose up -d db

# Run backend locally (requires dev-db)
dev-backend:
	cd backend && uv run uvicorn main:app --reload --port 8000

# Run frontend locally
dev-frontend:
	cd frontend && npm run dev

# Stop all docker containers
stop:
	docker-compose down

# Clean up artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Run backend tests
test-backend:
	cd backend && uv run pytest tests/ -v

# Run with coverage report
test-backend-cov:
	cd backend && uv run pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run only unit tests
test-unit:
	cd backend && uv run pytest tests/unit/ -v

# Run only integration tests
test-integration:
	cd backend && uv run pytest tests/integration/ -v

# Run a specific test file
test-file:
	cd backend && uv run pytest $(FILE) -v

# Code Quality
.PHONY: format lint setup-hooks

format:
	cd backend && uv run ruff format .
	cd frontend && npm run format

lint:
	cd backend && uv run ruff check . --fix
	cd backend && uv run ty check

setup-hooks:
	cd backend && uv run bash -c 'cd .. && pre-commit install'

