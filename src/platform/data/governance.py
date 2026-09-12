from __future__ import annotations

from enum import StrEnum


class DataClassification(StrEnum):
    UNCLASSIFIED = "UNCLASSIFIED"
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class PrivacyCategory(StrEnum):
    NONE_DECLARED = "NONE_DECLARED"
    AGGREGATE_NON_PERSONAL = "AGGREGATE_NON_PERSONAL"
    PSEUDONYMOUS_OR_LINKABLE = "PSEUDONYMOUS_OR_LINKABLE"
    PERSONAL_DATA = "PERSONAL_DATA"
    SENSITIVE_PERSONAL_DATA = "SENSITIVE_PERSONAL_DATA"
    UNKNOWN = "UNKNOWN"


class GovernanceState(StrEnum):
    DRAFT = "DRAFT"
    GOVERNED = "GOVERNED"
    FROZEN = "FROZEN"
    RETIRED = "RETIRED"


class AIUsePolicy(StrEnum):
    PROHIBITED = "PROHIBITED"
    LOCAL_ANALYSIS_ONLY = "LOCAL_ANALYSIS_ONLY"
    RAG_RETRIEVAL_ALLOWED = "RAG_RETRIEVAL_ALLOWED"
    MODEL_EVALUATION_ALLOWED = "MODEL_EVALUATION_ALLOWED"
    MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL = "MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL"


class ExportPolicy(StrEnum):
    PROHIBITED = "PROHIBITED"
    GOVERNED_EXPORT_ALLOWED = "GOVERNED_EXPORT_ALLOWED"


class ContentState(StrEnum):
    AVAILABLE = "AVAILABLE"
    PURGED = "PURGED"


class PurgeStatus(StrEnum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class AnonymizationStatus(StrEnum):
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

DEFAULT_CLASSIFICATION = DataClassification.UNCLASSIFIED
DEFAULT_PRIVACY_CATEGORY = PrivacyCategory.UNKNOWN
DEFAULT_GOVERNANCE_STATE = GovernanceState.DRAFT
DEFAULT_AI_USE_POLICY = AIUsePolicy.PROHIBITED
DEFAULT_EXPORT_POLICY = ExportPolicy.PROHIBITED
DEFAULT_CONTENT_STATE = ContentState.AVAILABLE
DEFAULT_PURGE_STATUS = PurgeStatus.NONE


_CLASSIFICATION_SENSITIVITY = {
    DataClassification.PUBLIC: 0,
    DataClassification.INTERNAL: 1,
    DataClassification.CONFIDENTIAL: 2,
    DataClassification.RESTRICTED: 3,
}
_PRIVACY_SENSITIVITY = {
    PrivacyCategory.NONE_DECLARED: 0,
    PrivacyCategory.AGGREGATE_NON_PERSONAL: 1,
    PrivacyCategory.PSEUDONYMOUS_OR_LINKABLE: 2,
    PrivacyCategory.PERSONAL_DATA: 3,
    PrivacyCategory.SENSITIVE_PERSONAL_DATA: 4,
}


def classification_is_downgrade(before: DataClassification | str, after: DataClassification | str) -> bool:
    old, new = DataClassification(before), DataClassification(after)
    if old is DataClassification.UNCLASSIFIED or new is DataClassification.UNCLASSIFIED:
        return False
    return _CLASSIFICATION_SENSITIVITY[new] < _CLASSIFICATION_SENSITIVITY[old]


def privacy_is_downgrade(before: PrivacyCategory | str, after: PrivacyCategory | str) -> bool:
    old, new = PrivacyCategory(before), PrivacyCategory(after)
    if old is PrivacyCategory.UNKNOWN or new is PrivacyCategory.UNKNOWN:
        return False
    return _PRIVACY_SENSITIVITY[new] < _PRIVACY_SENSITIVITY[old]


def catalog_values(catalog: type[StrEnum]) -> tuple[str, ...]:
    return tuple(item.value for item in catalog)
