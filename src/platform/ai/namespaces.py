from __future__ import annotations

import re
import uuid


PUBLIC_NAMESPACES = {"PUBLIC/ISI", "PUBLIC/SIMPA", "PUBLIC/ORDO"}
PRIVATE_RE = re.compile(r"^ORG-([0-9a-fA-F-]{36})/(SIMPA|ORDO)$")


class NamespaceError(ValueError):
    pass


def public_namespace(scope: str) -> str:
    normalized = str(scope).upper()
    value = f"PUBLIC/{normalized}"
    if value not in PUBLIC_NAMESPACES:
        raise NamespaceError("unsupported_public_namespace")
    return value


def private_namespace(organization_id: uuid.UUID | str, product_code: str) -> str:
    product = str(product_code).upper()
    if product not in {"SIMPA", "ORDO"}:
        raise NamespaceError("unsupported_product")
    return f"ORG-{uuid.UUID(str(organization_id))}/{product}"


def assert_namespace_access(
    namespace: str,
    *,
    organization_id: uuid.UUID | str,
    product_code: str,
) -> None:
    product = str(product_code).upper()
    if product not in {"SIMPA", "ORDO"}:
        raise NamespaceError("unsupported_product")
    if namespace == "PUBLIC/ISI":
        return
    if namespace == f"PUBLIC/{product}":
        return
    if namespace in PUBLIC_NAMESPACES:
        raise NamespaceError("cross_product_public_namespace")
    match = PRIVATE_RE.fullmatch(namespace)
    if match is None:
        raise NamespaceError("invalid_namespace")
    namespace_org, namespace_product = match.groups()
    if uuid.UUID(namespace_org) != uuid.UUID(str(organization_id)):
        raise NamespaceError("cross_tenant_namespace")
    if namespace_product != product:
        raise NamespaceError("cross_product_private_namespace")
