"""Unit tests for Pydantic product variants and serialization."""

from __future__ import annotations

from pydantic import ValidationError
from pytest import raises

from validated_objects.models import (
    PRODUCT_ADAPTER,
    DigitalProduct,
    PhysicalProduct,
)


def base_payload() -> dict[str, object]:
    return {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "  Mechanical Keyboard  ",
        "price": "129.90",
        "active": True,
        "tags": ["hardware", "keyboard"],
        "created_at": "2026-09-03T12:00:00Z",
    }


def test_discriminated_union_round_trips_both_variants() -> None:
    physical = PRODUCT_ADAPTER.validate_python(
        {**base_payload(), "kind": "physical", "stock": 12, "weight_grams": 850}
    )
    digital = PRODUCT_ADAPTER.validate_python(
        {
            **base_payload(),
            "kind": "digital",
            "download_url": "https://example.com/guide.pdf",
            "file_size_bytes": 5_242_880,
        }
    )

    assert isinstance(physical, PhysicalProduct)
    assert isinstance(digital, DigitalProduct)
    assert physical.name == "Mechanical Keyboard"
    assert PRODUCT_ADAPTER.validate_json(PRODUCT_ADAPTER.dump_json(physical)) == physical
    assert PRODUCT_ADAPTER.validate_json(PRODUCT_ADAPTER.dump_json(digital)) == digital


def test_constraints_and_extra_fields_are_rejected() -> None:
    invalid = {
        **base_payload(),
        "kind": "physical",
        "price": "0",
        "stock": -1,
        "weight_grams": 0,
        "unexpected": True,
    }

    with raises(ValidationError) as captured:
        PRODUCT_ADAPTER.validate_python(invalid)

    locations = {error["loc"] for error in captured.value.errors()}
    assert ("physical", "price") in locations
    assert ("physical", "stock") in locations
    assert ("physical", "weight_grams") in locations
    assert ("physical", "unexpected") in locations


def test_invalid_discriminator_is_rejected() -> None:
    with raises(ValidationError, match="Input tag 'subscription'"):
        PRODUCT_ADAPTER.validate_python({**base_payload(), "kind": "subscription"})
