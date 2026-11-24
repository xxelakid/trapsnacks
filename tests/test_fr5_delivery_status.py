# FR 5 View Delivery Status
import pytest
from conftest import delivery_data
from services.delivery_service import DeliveryService
from services.order_service import OrderService
from services.order_status_service import OrderStatusService
from services.request_rider import RequestRider


def accepted(cashier, chef, item, rider):
    order = OrderService.create_order(delivery_data(item.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    RequestRider.accept_delivery(order.delivery.id, rider)
    return order


def test_fr5_cannot_pick_up_before_food_is_ready(cashier, chef, patty, rider_a):
    order = accepted(cashier, chef, patty, rider_a)
    with pytest.raises(ValueError, match='not ready'):
        DeliveryService.update_delivery(order.delivery.id, 'Picked up', rider_a)


def test_fr5_full_delivery_ends_in_history_and_frees_rider(cashier, chef, patty, rider_a):
    order = accepted(cashier, chef, patty, rider_a)
    OrderStatusService.change_status(order.id, 'Ready', chef)
    DeliveryService.update_delivery(order.delivery.id, 'Picked up', rider_a)
    assert len(DeliveryService.active_deliveries()) == 1
    DeliveryService.update_delivery(order.delivery.id, 'Delivered', rider_a)
    assert DeliveryService.active_deliveries() == []          # FR 5 SR-3
    assert len(DeliveryService.delivery_history()) == 1       # FR 5 SR-4
    assert rider_a.status == 'available'


def test_fr5_rider_cannot_update_someone_elses_delivery(cashier, chef, patty, rider_a, rider_b):
    order = accepted(cashier, chef, patty, rider_a)
    with pytest.raises(ValueError):
        DeliveryService.update_delivery(order.delivery.id, 'Picked up', rider_b)


def test_fr5_owner_lands_on_deliveries_page(client, owner):
    from conftest import login
    response = login(client, 'owner')
    assert response.headers['Location'].endswith('/deliveries')
    assert client.get('/deliveries').status_code == 200
