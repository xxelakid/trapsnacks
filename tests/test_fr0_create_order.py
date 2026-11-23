# FR 0 Create Order
import pytest
from conftest import delivery_data
from models import Order
from services.order_service import OrderService


def test_fr0_ac1_order_without_items_is_refused(cashier):
    with pytest.raises(ValueError, match='at least one item'):
        OrderService.create_order({'order_type': 'pickup', 'items': []}, cashier)


def test_fr0_ac1_order_without_type_is_refused(cashier, patty):
    with pytest.raises(ValueError, match='Pickup or Delivery'):
        OrderService.create_order({'items': [{'id': patty.id}]}, cashier)


def test_fr0_ac2_every_order_gets_a_unique_number(cashier, patty):
    first = OrderService.create_order(delivery_data(patty.id), cashier)
    second = OrderService.create_order(delivery_data(patty.id), cashier)
    assert first.id != second.id
    assert Order.query.count() == 2


def test_fr0_order_starts_as_new_with_its_items(cashier, patty):
    order = OrderService.create_order(delivery_data(patty.id, qty=3), cashier)
    assert order.status == 'New'
    assert order.items[0].quantity == 3
