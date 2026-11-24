# FR 3 Cancel Order
import pytest
from conftest import delivery_data
from services.cancel_order_service import CancelOrderService
from services.order_service import OrderService
from services.order_status_service import OrderStatusService
from services.request_rider import RequestRider


def test_fr3_cancel_needs_a_reason(cashier, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    with pytest.raises(ValueError):
        CancelOrderService.cancel_order(order.id, '', cashier)


def test_fr3_cancel_stores_reason(cashier, patty):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    CancelOrderService.cancel_order(order.id, 'Duplicate order', cashier)
    assert order.status == 'Cancelled' and order.cancel_reason == 'Duplicate order'


def test_fr3_ac3_cancelling_accepted_delivery_frees_the_rider(cashier, chef, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    RequestRider.accept_delivery(order.delivery.id, rider_a)
    CancelOrderService.cancel_order(order.id, 'Customer changed their mind', cashier)
    assert order.delivery.status == 'Cancelled'
    assert rider_a.status == 'available'


def test_fr3_ac3_cancelling_withdraws_open_offer(cashier, chef, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    CancelOrderService.cancel_order(order.id, 'Duplicate order', cashier)
    assert order.delivery.status == 'Cancelled'
