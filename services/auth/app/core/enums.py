"""Enumerations used across the auth service.

Provides strongly-typed string enums for domain concepts that are stored
as plain strings in the database (e.g. role names). Using enums prevents
typos and makes IDE autocompletion available.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Well-known user roles in the system.

    The database ``roles`` table may contain additional dynamically created
    roles, but all business logic and permission checks rely on these four
    values.
    """

    ADMIN = "admin"
    METHODIST = "methodist"
    SEMINARIST = "seminarist"
    CANDIDATE = "candidate"
