from types import SimpleNamespace

import pytest

from apps.catalog.services import Availability, product_availability, variant_availability


def variant(stock: int, made_to_order: bool = False):
    # The functions only read two attributes, so no database row is needed
    return SimpleNamespace(stock=stock, made_to_order=made_to_order)


@pytest.mark.parametrize("made_to_order", [False, True])
def test_in_stock_is_available(made_to_order):
    assert variant_availability(3, made_to_order) is Availability.AVAILABLE


def test_zero_stock_made_to_order():
    assert variant_availability(0, True) is Availability.MADE_TO_ORDER


def test_zero_stock_plain_is_out_of_stock():
    assert variant_availability(0, False) is Availability.OUT_OF_STOCK


def test_product_picks_best_status():
    out = variant(0)
    made = variant(0, True)
    available = variant(2)

    assert product_availability([out, out]) is Availability.OUT_OF_STOCK
    assert product_availability([out, made]) is Availability.MADE_TO_ORDER
    assert product_availability([out, made, available]) is Availability.AVAILABLE
    assert product_availability(iter([made, out])) is Availability.MADE_TO_ORDER  # any iterable


def test_product_without_variants_is_out_of_stock():
    assert product_availability([]) is Availability.OUT_OF_STOCK


def test_availability_codes_are_the_api_strings():
    assert [a.value for a in Availability] == ["AVAILABLE", "MADE_TO_ORDER", "OUT_OF_STOCK"]
    assert Availability.AVAILABLE == "AVAILABLE"  # a StrEnum serializes to plain JSON strings
