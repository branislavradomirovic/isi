"""Aggregate shared-platform model imports for SQLAlchemy/Alembic metadata registration."""

from src.public_content import models as public_content_models  # noqa: F401
from src.knowledge import models as knowledge_models  # noqa: F401
from src.public_content import sections as public_section_models  # noqa: F401
from src.platform.auth.models import AuthSession, AuthToken, Invitation  # noqa: F401
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
