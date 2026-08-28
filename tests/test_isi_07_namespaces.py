import uuid

import pytest

from src.platform.ai.namespaces import NamespaceError, assert_namespace_access, private_namespace, public_namespace


def test_public_and_private_namespace_contract():
    organization_id = uuid.uuid4()
    assert public_namespace("isi") == "PUBLIC/ISI"
    assert public_namespace("simpa") == "PUBLIC/SIMPA"
    namespace = private_namespace(organization_id, "SIMPA")
    assert_namespace_access(namespace, organization_id=organization_id, product_code="SIMPA")


def test_private_namespace_rejects_cross_tenant_and_product():
    organization_id = uuid.uuid4()
    namespace = private_namespace(organization_id, "SIMPA")
    with pytest.raises(NamespaceError, match="cross_tenant_namespace"):
        assert_namespace_access(namespace, organization_id=uuid.uuid4(), product_code="SIMPA")
    with pytest.raises(NamespaceError, match="cross_product_private_namespace"):
        assert_namespace_access(namespace, organization_id=organization_id, product_code="ORDO")


def test_public_product_namespace_does_not_cross_product():
    with pytest.raises(NamespaceError, match="cross_product_public_namespace"):
        assert_namespace_access("PUBLIC/SIMPA", organization_id=uuid.uuid4(), product_code="ORDO")
