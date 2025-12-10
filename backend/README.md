# PM App Backend

Automated Project Management Tool - Backend API

## Architecture

This backend follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         API Layer (Routers)             │  ← HTTP Endpoints, Request/Response
├─────────────────────────────────────────┤
│      Service Layer (Services)           │  ← Business Logic, Orchestration
├─────────────────────────────────────────┤
│   Data Access Layer (Repositories)      │  ← Database Operations
├─────────────────────────────────────────┤
│     Integration Layer (Clients)         │  ← External APIs (Jira, Precursive)
├─────────────────────────────────────────┤
│   Infrastructure (Database, Config)     │  ← Core Infrastructure
└─────────────────────────────────────────┘
```

## Project Structure

```
backend/
├── main.py                     # FastAPI app initialization
├── config.py                   # Configuration management
├── database.py                 # Database connection setup
├── dependencies.py             # Shared FastAPI dependencies
├── exceptions.py               # Custom exception classes
│
├── models/                     # SQLModel database models
│   ├── __init__.py            # Exports all models and enums
│   ├── user.py
│   ├── project.py
│   ├── action_item.py
│   ├── comment.py
│   └── risk.py
│
├── schemas/                    # Pydantic schemas (DTOs)
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   └── project.py
│
├── repositories/               # Data access layer
│   ├── __init__.py
│   ├── base.py                # Generic repository pattern
│   ├── user_repository.py
│   └── project_repository.py
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   └── project_service.py
│
├── routers/                    # API endpoints
│   ├── __init__.py
│   ├── auth.py
│   └── projects.py
│
├── integrations/               # External API clients
│   └── __init__.py
│
├── middleware/                 # Custom middleware
│   └── __init__.py
│
└── tests/                      # Test suite
    ├── __init__.py
    ├── unit/
    └── integration/
```

## Design Patterns

### 1. Repository Pattern
- **Purpose**: Abstract data access logic from business logic
- **Location**: `repositories/`
- **Example**: `UserRepository`, `ProjectRepository`

### 2. Service Pattern
- **Purpose**: Encapsulate business logic and orchestration
- **Location**: `services/`
- **Example**: `AuthService`, `ProjectService`

### 3. Dependency Injection
- **Purpose**: Loose coupling and testability
- **Location**: `dependencies.py`
- **Usage**: FastAPI's `Depends()` system

### 4. Layered Architecture
- **Purpose**: Separation of concerns
- **Benefit**: Each layer has a single responsibility

## Setup

### Prerequisites
- Python 3.13+
- PostgreSQL database
- uv package manager

### Installation

1. Install dependencies:
```bash
uv pip install -r pyproject.toml
```

2. Set up environment variables (create `.env` file):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/pm_app
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
```

3. Run migrations (create tables):
```bash
# Tables are auto-created on first run via lifespan
```

4. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Features

### Authentication
- Google OAuth2 SSO
- JWT token-based authentication
- Role-based access control (Cogniter/Client)

### Authorization
- `@cognite.com` emails automatically get Cogniter role
- Other domains get Client role
- Cogniters: full access to all projects
- Clients: access only to assigned projects

### API Endpoints

#### Authentication
- `POST /auth/login` - Login with Google OAuth
- `GET /auth/me` - Get current user info

#### Projects
- `GET /projects/` - List accessible projects
- `POST /projects/` - Create project (Cogniters only)
- `GET /projects/{id}` - Get project details
- `PATCH /projects/{id}` - Update project (Cogniters only)
- `DELETE /projects/{id}` - Delete project (Cogniters only)
- `POST /projects/{id}/publish` - Publish project
- `POST /projects/{id}/unpublish` - Unpublish project
- `POST /projects/{id}/users/{user_id}` - Assign user to project
- `DELETE /projects/{id}/users/{user_id}` - Remove user from project

## Environment Variables

See `.env.example` for all required environment variables.

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID

### Optional (for future features)
- `JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL`
- `SALESFORCE_INSTANCE_URL`, `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`

## Testing

```bash
# Run tests (future)
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## Code Quality

The codebase follows these principles:
- **Type Safety**: Python type hints throughout
- **Separation of Concerns**: Clear layering
- **Single Responsibility**: Each module has one purpose
- **DRY**: Reusable components via base classes
- **Testability**: Dependency injection for easy mocking

## Future Enhancements

- [ ] Jira integration client
- [ ] Precursive/Salesforce integration client
- [ ] Background jobs for data sync
- [ ] Caching layer (Redis)
- [ ] Rate limiting
- [ ] API versioning
- [ ] Comprehensive test suite
- [ ] Logging middleware
- [ ] Request tracking middleware

