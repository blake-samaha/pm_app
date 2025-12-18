"""Link tables for many-to-many relationships."""

import uuid

from sqlmodel import Field, SQLModel


class UserProjectLink(SQLModel, table=True):
    """Link table for many-to-many relationship between Users and Projects."""

    user_id: uuid.UUID = Field(default=None, foreign_key="user.id", primary_key=True)
    project_id: uuid.UUID = Field(
        default=None, foreign_key="project.id", primary_key=True
    )
