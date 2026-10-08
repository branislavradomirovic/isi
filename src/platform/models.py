"""Aggregate shared-platform model imports for SQLAlchemy/Alembic metadata registration."""

from src.public_content import models as public_content_models  # noqa: F401
from src.knowledge import models as knowledge_models  # noqa: F401
from src.public_content import sections as public_section_models  # noqa: F401
from src.platform.auth.models import AuthSession, AuthToken, Invitation, MfaChallenge, MfaFactor  # noqa: F401
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

from src.platform.data.models import (  # noqa: F401
    DataAuditEvent,
    DataQualityResult,
    DataSource,
    DataSourceVersion,
    IngestionJob,
)

from src.platform.ai.models import (  # noqa: F401
    AIAuditEvent,
    AIEmbedding,
    AIJob,
    AIJobAttempt,
    AIModel,
    AIPolicyProfile,
    AIPrompt,
    AIPromptVersion,
)

from src.domains.simpa.models import (  # noqa: F401
    SimpaDataMapping,
    SimpaDimension,
    SimpaIndicatorDefinition,
    SimpaIndicatorObservation,
    SimpaLocalActor,
    SimpaLocalSystemProfile,
    SimpaMonitoringCycle,
    SimpaSourceType,
)

from src.domains.simpa.analytics_models import (  # noqa: F401
    SimpaAISynthesis,
    SimpaAnalyticsRun,
    SimpaIndicatorMethodology,
    SimpaIndicatorResult,
)

from src.domains.ordo.models import (  # noqa: F401
    OrdoAsset,
    OrdoDataMapping,
    OrdoDestinationProfile,
    OrdoDimension,
    OrdoIndicatorDefinition,
    OrdoIndicatorObservation,
    OrdoMonitoringCycle,
    OrdoPillar,
    OrdoSourceType,
    OrdoStakeholder,
)

from src.domains.ordo.analytics_models import (  # noqa: F401
    OrdoAISynthesis,
    OrdoAnalyticsRun,
    OrdoDevelopmentGoal,
    OrdoIndicatorMethodology,
    OrdoIndicatorResult,
    OrdoScenario,
    OrdoScenarioAssessment,
)

from src.platform.reporting.models import (  # noqa: F401
    Report,
    ReportExport,
    ReportReview,
    ReportVersion,
)

from src.platform.administration.models import (  # noqa: F401
    AdminAuditEvent,
    InvitationProductGrant,
    InvitationRoleGrant,
)

from src.platform.security.models import SecurityEvent, SecurityRateLimit  # noqa: F401

from src.platform.spatial.models import SpatialGeometryVersion  # noqa: F401

from src.platform.extraction.models import ExtractionRequest, ExtractionArtifact, ExtractionReview  # noqa: F401
