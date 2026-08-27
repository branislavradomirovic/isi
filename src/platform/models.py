"""Aggregate shared-platform model imports for SQLAlchemy/Alembic metadata registration."""

from src.platform.access.models import (  # noqa: F401
    MembershipProductAccess,
    OrganizationEntitlement,
    Permission,
    Product,
    Role,
    RoleAssignment,
    RolePermission,
)
from src.platform.identity.models import Membership, Organization, User  # noqa: F401
from src.platform.workspaces.models import Workspace  # noqa: F401
