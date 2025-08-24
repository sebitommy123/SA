"""System tests for overlapping provider data generation."""

import pytest

pytest.importorskip("flask", reason="Flask not installed; skipping system provider tests")

from flask_providers.mock_provider import create_overlapping_objects, get_provider_data


def test_create_overlapping_objects_counts():
    data = create_overlapping_objects()
    assert "overlapping_employees" in data
    assert "overlapping_products" in data
    assert "overlapping_customers" in data
    assert "overlapping_documents" in data
    # Basic sanity: non-empty lists
    assert len(data["overlapping_employees"]) > 0
    assert len(data["overlapping_products"]) > 0
    assert len(data["overlapping_customers"]) > 0
    assert len(data["overlapping_documents"]) > 0
    # Each object should have overlap in id and have required keys
    for key in [
        "overlapping_employees",
        "overlapping_products",
        "overlapping_customers",
        "overlapping_documents",
    ]:
        for obj in data[key]:
            assert "__id__" in obj and "overlap" in obj["__id__"]
            assert "__source__" in obj
            assert "__types__" in obj and isinstance(obj["__types__"], list)


def test_get_provider_data_unique_ids_per_provider():
    provider_data = get_provider_data()
    assert set(provider_data.keys()) == {
        "hr_database",
        "crm_system",
        "inventory_system",
        "analytics_engine",
        "document_store",
    }
    # Ensure each provider has unique IDs within itself
    for objects in provider_data.values():
        ids = [obj["__id__"] for obj in objects]
        assert len(ids) == len(set(ids))
    # Ensure at least one overlap exists across providers by id
    all_ids_by_source = {}
    for source, objects in provider_data.items():
        for obj in objects:
            all_ids_by_source.setdefault(obj["__id__"], set()).add(source)
    assert any(len(sources) > 1 for sources in all_ids_by_source.values()) 