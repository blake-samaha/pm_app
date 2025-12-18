# Backend Architecture & Design Patterns

## 1. Overview

The backend of the Automated Project Management Tool is built using **Python (FastAPI)**, designed to be robust, scalable, and maintainable. It serves as the central hub for data processing, business logic, and integration with external systems (Jira, Precursive/Salesforce).

**Key Technologies:**
*   **Framework**: FastAPI
*   **Package Management**: Astral's uv
*   **Database**: PostgreSQL
*   **ORM**: SQLModel (combines SQLAlchemy and Pydantic)
*   **Authentication**: Google OAuth2 + JWT

## 2. Architecture

The application follows a **Layered Architecture** to ensure separation of concerns, testability, and modularity.

### 2.1. High-Level Layers

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

1.  **API Layer (`routers/`)**: Handles HTTP requests, input validation, and route definitions. It delegates business logic to the Service Layer.
2.  **Service Layer (`services/`)**: Encapsulates business logic, orchestration, and transaction management. It coordinates between Repositories and Integration Clients.
3.  **Repository Layer (`repositories/`)**: Handles all database interactions (CRUD). It abstracts the underlying database implementation from the rest of the app.
4.  **Integration Layer (`integrations/`)**: Manages communication with external APIs, handling authentication, rate limiting, and data transformation.

### 2.2. Directory Structure

```
backend/
├── main.py                     # Application entry point & exception handlers
├── config.py                   # Configuration management (Pydantic Settings)
├── database.py                 # Database connection & session management
├── dependencies.py             # Shared FastAPI dependencies (Auth, Services)
├── exceptions.py               # Custom exception hierarchy
├── permissions.py              # Role-based permission helpers (pure functions)
├── logging_config.py           # Logging configuration
│
├── models/                     # Domain models (SQLModel)
│   ├── __init__.py
│   ├── user.py
│   ├── project.py
│   ├── action_item.py
│   ├── comment.py
│   └── risk.py
│
├── schemas/                    # API Contracts / DTOs (Pydantic)
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── project.py
│   └── ...
│
├── repositories/               # Data Access Layer
│   ├── __init__.py
│   ├── base.py                 # Generic repository implementation
│   ├── user_repository.py
│   └── project_repository.py
│
├── services/                   # Business Logic Layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   └── project_service.py
│
├── routers/                    # API Endpoints
│   ├── __init__.py
│   ├── auth.py
│   ├── projects.py
│   └── ...
│
├── integrations/               # External API Clients
│   ├── __init__.py
│   ├── jira_client.py
│   └── precursive_client.py
│
├── middleware/                 # Custom Middleware
│   └── ...
│
└── tests/                      # Test Suite
    ├── unit/
    └── integration/
```

## 3. Design Patterns

### 3.1. Repository Pattern
Abstracts data access logic. A generic `BaseRepository` provides common CRUD operations (`get`, `create`, `update`, `delete`), while specialized repositories extend it for domain-specific queries.

```python
# repositories/base.py
class BaseRepository[T]:
    def get_by_id(id: UUID) -> Optional[T]
    def create(obj: T) -> T
    # ...
```

### 3.2. Service Pattern
Encapsulates business rules. Services are the entry point for all logic, ensuring that routers remain thin.

```python
# services/project_service.py
class ProjectService:
    def create_project(data, user):
        # Authorization check
        # Business validation
        # Orchestrate repository calls
```

### 3.3. Dependency Injection (DI)
Leverages FastAPI's `Depends` system to inject services, repositories, and configuration into routers. This promotes loose coupling and makes testing easier (dependencies can be mocked).

```python
# dependencies.py
def get_project_service(session: SessionDep) -> ProjectService:
    return ProjectService(session)

# routers/projects.py
@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    return service.create_project(data)
```

## 4. Authorization System

The application implements **Role-Based Access Control (RBAC)** with a three-tier persona system.

### 4.1. Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `Cogniter` | Internal employees (`@cognite.com` emails) | Full access: all projects, financials, user management, project creation |
| `Client + Financials` | Senior client stakeholders | View assigned projects + financial data (budgets, burn rates) |
| `Client` | Standard client stakeholders | View assigned projects only (no financial data) |

### 4.2. Permission Helpers (`permissions.py`)

Centralized permission logic is implemented as **pure functions** for easy testing:

```python
# permissions.py
def is_internal_user(user: User) -> bool:
    """Cognite employees have full access."""
    return user.role == UserRole.COGNITER

def is_client_role(user: User) -> bool:
    """Any external client role."""
    return user.role in (UserRole.CLIENT, UserRole.CLIENT_FINANCIALS)

def can_view_financials(user: User) -> bool:
    """Roles that can see budget/financial data."""
    return user.role in (UserRole.COGNITER, UserRole.CLIENT_FINANCIALS)

def can_manage_team(user: User) -> bool:
    """Roles that can assign/remove users from projects."""
    return user.role == UserRole.COGNITER

def can_edit_project(user: User) -> bool:
    """Roles that can modify project settings."""
    return user.role == UserRole.COGNITER

def can_create_project(user: User) -> bool:
    """Roles that can create new projects."""
    return user.role == UserRole.COGNITER
```

### 4.3. Dependency Injection for Authorization

Authorization is enforced via dependencies in `dependencies.py`:

```python
# dependencies.py
CurrentUser = Annotated[User, Depends(get_current_user)]
CogniterUser = Annotated[User, Depends(require_cogniter)]

# Usage - Cogniter-only endpoint
async def create_project(current_user: CogniterUser, ...):
    # Only Cogniters can access
```

### 4.4. Project Access Control

Client roles (both `CLIENT` and `CLIENT_FINANCIALS`) can only access projects they are explicitly assigned to. This is enforced via:

```python
# services/project_service.py
def user_has_access_to_project(project_id: UUID, user: User) -> bool:
    """Check if user can access a specific project."""
    if user.role == UserRole.COGNITER:
        return True  # Cogniters can access all projects
    # Client roles require explicit assignment
    return self.repository.is_user_assigned(project_id, user.id)
```

### 4.5. Role Management

Cogniters can update user roles (except promoting to Cogniter):

```
PATCH /users/{user_id}/role
```

This allows upgrading clients to `Client + Financials` for financial data access.

## 5. Configuration Management

Configuration is managed using `pydantic-settings` in `config.py`. This provides type safety, validation, and environment variable support.

*   **Environment Variables**:
    *   `DATABASE_URL`
    *   `SECRET_KEY`
    *   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
    *   `JIRA_BASE_URL` / `JIRA_API_TOKEN`
    *   `SALESFORCE_INSTANCE_URL`

## 6. Error Handling

A custom exception hierarchy is defined in `exceptions.py` to ensure consistent error responses.

*   `PMAppException` (Base)
    *   `AuthenticationError` (401)
    *   `AuthorizationError` (403)
    *   `ResourceNotFoundError` (404)
    *   `ValidationError` (400)
    *   `ExternalServiceError` (502)

Global exception handlers in `main.py` catch these exceptions and return standardized JSON responses.

## 7. Database Best Practices

*   **Connection Pooling**: Configured in `database.py` using SQLAlchemy's `QueuePool` to handle concurrent requests efficiently.
*   **Pre-ping**: Enabled to verify connections before use, preventing stale connection errors.
*   **Transactions**: Managed within the Service layer. Operations are committed only if all steps succeed.

## 8. Testing Strategy

*   **Unit Tests** (`tests/unit/`): Test Services and Repositories in isolation using mocks.
*   **Integration Tests** (`tests/integration/`): Test API endpoints with a real (test) database to verify the full request-response cycle.

## 9. Performance Considerations

*   **Async/Await**: Used for I/O-bound operations (DB queries, external API calls).
*   **Pagination**: Required for list endpoints to prevent large payloads.
*   **Background Jobs**: (Future) For heavy synchronization tasks with Jira/Precursive.

