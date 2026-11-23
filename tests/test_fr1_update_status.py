# FR 1 Update Order Status
import pytest
from conftest import delivery_data
from models import StatusChange
from services.order_service import OrderService
from services.order_status_service import OrderStatusService


def test_fr1_ac1_status_cannot_skip_preparing(cashier, chef, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    with pytest.raises(ValueError):
        OrderStatusService.change_status(order.id, 'Ready', chef)


def test_fr1_status_moves_in_order_and_is_recorded(cashier, chef, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    OrderStatusService.change_status(order.id, 'Ready', chef)
    assert order.status == 'Ready'
    # one record for "New" plus one for each change (FR 1 SR-3)
    assert StatusChange.query.filter_by(order_id=order.id).count() == 3


def test_fr1_pickup_order_is_not_offered(cashier, chef, patty):
    data = delivery_data(patty.id)
    data['order_type'] = 'pickup'
    order = OrderService.create_order(data, cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    assert order.delivery is None
