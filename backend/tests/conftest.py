"""Shared test fixtures for the PM App backend."""
import pytest
from datetime import timedelta, datetime, timezone
from uuid import uuid4

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from jose import jwt

from main import app
from database import get_session
from config import Settings, get_settings
from models import User, UserRole, AuthProvider, Project


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(name="engine")
def engine_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",  # In-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


# =============================================================================
# Settings Fixtures
# =============================================================================

@pytest.fixture(name="test_settings")
def test_settings_fixture():
    """Create test settings with dummy values."""
    return Settings(
        database_url="sqlite://",  # Not used, we override the session
        secret_key="test-secret-key-for-jwt-signing",
        algorithm="HS256",
        access_token_expire_minutes=30,
        firebase_project_id="test-project",
        firebase_service_account_path=None,  # Don't initialize Firebase in tests
    )


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def cogniter_user(session) -> User:
    """Create a Cogniter user (internal Cognite employee)."""
    user = User(
        id=uuid4(),
        email="test.cogniter@cognite.com",
        name="Test Cogniter",
        role=UserRole.COGNITER,
        auth_provider=AuthProvider.GOOGLE,
        is_pending=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def client_user(session) -> User:
    """Create a Client user (external customer)."""
    user = User(
        id=uuid4(),
        email="client@acme.com",
        name="Client User",
        role=UserRole.CLIENT,
        auth_provider=AuthProvider.GOOGLE,
        is_pending=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def pending_user(session) -> User:
    """Create a pending (invited but not registered) user."""
    user = User(
        id=uuid4(),
        email="pending@external.com",
        name="pending",  # Placeholder name from email prefix
        role=UserRole.CLIENT,
        auth_provider=AuthProvider.EMAIL,
        is_pending=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# =============================================================================
# Project Fixtures
# =============================================================================

@pytest.fixture
def sample_project(session) -> Project:
    """Create a sample project for testing."""
    from models.project import ProjectType, HealthStatus
    
    project = Project(
        id=uuid4(),
        name="Test Project",
        type=ProjectType.FIXED_PRICE,
        precursive_url="https://precursive.example.com/projects/123",
        is_published=False,
        health_status=HealthStatus.GREEN,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


# =============================================================================
# Authentication Helpers
# =============================================================================

@pytest.fixture
def create_token(test_settings):
    """Factory fixture to create JWT tokens for testing."""
    def _create_token(user: User, expired: bool = False) -> str:
        if expired:
            expire = datetime.now(timezone.utc) - timedelta(hours=1)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": expire,
        }
        return jwt.encode(payload, test_settings.secret_key, algorithm="HS256")
    
    return _create_token


# =============================================================================
# FastAPI Test Client
# =============================================================================

@pytest.fixture(name="client")
def client_fixture(session, test_settings, engine):
    """Create a FastAPI test client with overridden dependencies."""
    def get_session_override():
        yield session
    
    def get_settings_override():
        return test_settings
    
    # Override database engine before app startup
    import database
    original_engine = database.engine
    database.engine = engine
    
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_settings] = get_settings_override
    
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Restore original engine
        database.engine = original_engine
        app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, cogniter_user, create_token):
    """Create a test client with Cogniter authentication headers."""
    token = create_token(cogniter_user)
    client.headers["Authorization"] = f"Bearer {token}"
    return client

