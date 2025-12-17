"""Models package - exports all models and enums."""
from enum import Enum


class UserRole(str, Enum):
    COGNITER = "Cogniter"
    CLIENT = "Client"


class AuthProvider(str, Enum):
    GOOGLE = "Google"
    EMAIL = "Email"


class ActionStatus(str, Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    NO_STATUS = "No Status"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskProbability(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskImpact(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MITIGATED = "Mitigated"


# Import all models (order matters for relationships)
from models.links import UserProjectLink
from models.user import User
from models.project import Project, ProjectType, ReportingCycle, HealthStatus
from models.action_item import ActionItem
from models.comment import Comment
from models.risk import Risk

__all__ = [
    # Enums
    "UserRole",
    "AuthProvider",
    "ProjectType",
    "ReportingCycle",
    "HealthStatus",
    "ActionStatus",
    "Priority",
    "RiskProbability",
    "RiskImpact",
    "RiskStatus",
    # Models
    "User",
    "Project",
    "UserProjectLink",
    "ActionItem",
    "Comment",
    "Risk",
]
