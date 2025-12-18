"""Custom exceptions for the application."""


class PMAppException(Exception):
    """Base exception for the application."""

    pass


class AuthenticationError(PMAppException):
    """Authentication failures."""

    pass


class AuthorizationError(PMAppException):
    """Authorization/permission failures."""

    pass


class ResourceNotFoundError(PMAppException):
    """Resource not found."""

    pass


class ValidationError(PMAppException):
    """Business validation failures."""

    pass


class ExternalServiceError(PMAppException):
    """External API failures (Jira, Precursive)."""

    pass


class IntegrationError(ExternalServiceError):
    """Integration-specific errors with external services."""

    pass


class ConfigurationError(PMAppException):
    """Configuration or environment variable errors."""

    pass


class DuplicateResourceError(PMAppException):
    """Attempting to create a resource that already exists."""

    pass
