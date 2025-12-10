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

