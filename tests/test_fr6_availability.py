# FR 6 Item Availability
import pytest
from conftest import delivery_data
from services.kitchen_service import KitchenService
from services.order_service import OrderService


def test_fr6_unavailable_item_cannot_be_ordered(cashier, patty):
    KitchenService.set_availability(patty.id, False)
    with pytest.raises(ValueError, match='not available'):
        OrderService.create_order(delivery_data(patty.id), cashier)


def test_fr6_item_can_be_made_available_again(cashier, patty):
    KitchenService.set_availability(patty.id, False)
    KitchenService.set_availability(patty.id, True)
    assert OrderService.create_order(delivery_data(patty.id), cashier).id
