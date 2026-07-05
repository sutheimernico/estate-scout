"""Tests for the Listing object model, incl. the DSGVO no-contact-data guardrail."""

import pytest

from estatescout.scout.model import Listing

# Field names that must never appear on a Listing (DSGVO: no seller personal data, ADR-0001).
_FORBIDDEN = {"name", "seller", "phone", "email", "contact", "telefon", "anbieter", "makler_name"}


def test_valid_listing_normalizes_bundesland_and_derives_ppsqm():
    lst = Listing(price=300_000, living_area_sqm=100, bundesland="Niedersachsen")
    assert lst.bundesland == "NI"  # normalized to code
    assert lst.price_per_sqm == pytest.approx(3_000.0)


def test_bundesland_alias_nrw():
    assert Listing(price=200_000, living_area_sqm=80, bundesland="NRW").bundesland == "NW"


def test_invalid_values_raise():
    with pytest.raises(ValueError):
        Listing(price=0, living_area_sqm=100, bundesland="NI")
    with pytest.raises(ValueError):
        Listing(price=300_000, living_area_sqm=0, bundesland="NI")
    with pytest.raises(ValueError):
        Listing(price=300_000, living_area_sqm=100, bundesland="Atlantis")
    with pytest.raises(ValueError):
        Listing(price=300_000, living_area_sqm=100, bundesland="NI", year_built=1500)


def test_model_carries_no_seller_contact_data():
    fields = set(Listing.__dataclass_fields__)
    assert not (fields & _FORBIDDEN), "Listing must never hold seller contact data (DSGVO)"
