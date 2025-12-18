# Automated Project Management Tool

A web application designed to streamline project tracking and reporting for Cognite projects, integrating with Precursive and Jira.

## Project Structure

- **backend/**: FastAPI application (Python)
- **frontend/**: Next.js application (React/TypeScript)
- **docker-compose.yml**: Container orchestration for database and full-stack deployment
- **Makefile**: Automation for development tasks

## Hybrid Development Flow (Recommended)

We use a hybrid approach for development:
1.  **Database**: Runs in Docker (stable, isolated).
2.  **Backend**: Runs locally using `uv` (fast, direct debugger access).
3.  **Frontend**: Runs locally using `npm` (fast hot-reloading).

### Prerequisites

- Docker & Docker Compose
- Python 3.13+ and [uv](https://github.com/astral-sh/uv)
- Node.js 18+ and npm

### Quick Start

1.  **Install Dependencies**
    ```bash
    make install
    ```

2.  **Start Development Environment**
    Open 3 terminal tabs:

    *Tab 1: Database*
    ```bash
    make dev-db
    ```

    *Tab 2: Backend* (http://localhost:8000)
    ```bash
    make dev-backend
    ```

    *Tab 3: Frontend* (http://localhost:3000)
    ```bash
    make dev-frontend
    ```

### Other Commands

- `make stop`: Stop all running containers.
- `make clean`: Remove Python cache files.

## Full Docker Deployment

To run the entire stack in containers (closer to production):

```bash
docker-compose up --build
```

## Demo Mode (Public Access)

For stakeholder demos, you can create a temporary public URL using Cloudflare Tunnel:

```bash
# Start all services including the tunnel
docker-compose --profile demo up
```

Look for the tunnel URL in the logs:
```
tunnel-1  | Your quick tunnel has been created!
tunnel-1  | +-------------------------------------------+
tunnel-1  | |  https://random-name.trycloudflare.com   |
tunnel-1  | +-------------------------------------------+
```

Share this URL with stakeholders for instant demo access.

**Security Notes:**
- The URL is temporary and changes on each restart
- Your local environment is exposed to the internet while running
- Only run during active demos
- Stop with `Ctrl+C` when done

## Documentation

See the `docs/` directory for detailed requirements and architecture:
- [Technical Requirements](docs/Technical_Requirements.md)
- [Backend Architecture](docs/Backend_Architecture.md)
