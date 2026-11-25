# FR 4 Accept a Delivery
from datetime import timedelta

import pytest
from conftest import delivery_data, make_rider
from services.order_service import OrderService
from services.order_status_service import OrderStatusService
from services.request_rider import RequestRider


def offered_delivery(cashier, chef, item):
    order = OrderService.create_order(delivery_data(item.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    return order.delivery


def test_fr4_ac3_ts1_only_first_rider_gets_the_delivery(cashier, chef, patty, rider_a, rider_b):
    delivery = offered_delivery(cashier, chef, patty)
    RequestRider.accept_delivery(delivery.id, rider_a)
    with pytest.raises(ValueError, match='already been taken'):
        RequestRider.accept_delivery(delivery.id, rider_b)
    assert delivery.rider_id == rider_a.id
    assert rider_a.status == 'reserved' and rider_b.status == 'available'


def test_fr4_ac4_meal_countdown_is_10_minutes_from_start_of_preparing(cashier, chef, patty, rider_a):
    delivery = offered_delivery(cashier, chef, patty)
    assert delivery.pickup_deadline - delivery.offered_at == timedelta(minutes=10)
    deadline = delivery.pickup_deadline
    RequestRider.accept_delivery(delivery.id, rider_a)
    assert delivery.pickup_deadline == deadline          # accepting does NOT restart the countdown


def test_fr4_reassigning_keeps_the_countdown(cashier, chef, patty, rider_a, rider_b):
    delivery = offered_delivery(cashier, chef, patty)
    deadline = delivery.pickup_deadline
    RequestRider.accept_delivery(delivery.id, rider_a)
    RequestRider.assign_manually(delivery.id, rider_b.id)
    assert delivery.pickup_deadline == deadline


def test_fr4_kitchen_and_rider_get_the_countdown(app, client, cashier, chef, patty, rider_a):
    from conftest import login
    from extensions import socketio
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    chef_client = app.test_client()
    login(chef_client, 'chef')
    chef_socket = socketio.test_client(app, flask_test_client=chef_client)
    chef_client.post(f'/api/orders/{order.id}/status', json={'status': 'Preparing'})
    update = [e for e in chef_socket.get_received() if e['name'] == 'order_status_changed'][0]['args'][0]
    assert update['prep_deadline'] == order.delivery.pickup_deadline.isoformat(timespec='seconds')
    offer = order.delivery.offer_dict()
    assert offer['pickup_deadline'] and offer['order_status'] == 'Preparing'
    OrderStatusService.change_status(order.id, 'Ready', chef)
    assert order.delivery.offer_dict()['order_status'] == 'Ready'
    assert order.delivery.staff_dict()['ready_at'] is not None


def test_fr4_ac1_ts2_unavailable_rider_cannot_accept(app, cashier, chef, patty):
    off_shift = make_rider('Shanice', status='unavailable')
    delivery = offered_delivery(cashier, chef, patty)
    with pytest.raises(ValueError):
        RequestRider.accept_delivery(delivery.id, off_shift)


def test_fr4_ac5_ts2_owner_reassigns_delivery(cashier, chef, patty, rider_a, rider_b):
    delivery = offered_delivery(cashier, chef, patty)
    RequestRider.accept_delivery(delivery.id, rider_a)
    RequestRider.assign_manually(delivery.id, rider_b.id)
    assert delivery.rider_id == rider_b.id
    assert rider_b.status == 'reserved' and rider_a.status == 'available'


def test_fr4_rider_on_delivery_cannot_go_off_shift(cashier, chef, patty, rider_a):
    delivery = offered_delivery(cashier, chef, patty)
    RequestRider.accept_delivery(delivery.id, rider_a)
    with pytest.raises(ValueError):
        RequestRider.set_rider_status(rider_a.id, 'unavailable')


def test_fr4_preparing_delivery_order_is_offered_to_riders(cashier, chef, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    assert order.delivery is not None and order.delivery.status == 'Offered'


def test_fr4_offer_reaches_available_rider_live(app, client, cashier, chef, patty, rider_a):
    from conftest import login
    from extensions import socketio
    rider_client = app.test_client()
    login(rider_client, 'andre')
    rider_socket = socketio.test_client(app, flask_test_client=rider_client)
    login(client, 'cashier')
    order_id = client.post('/api/orders', json=delivery_data(patty.id)).get_json()['data']['id']
    chef_client = app.test_client()
    login(chef_client, 'chef')
    chef_client.post(f'/api/orders/{order_id}/status', json={'status': 'Preparing'})
    events = [e['name'] for e in rider_socket.get_received()]
    assert 'delivery_offer' in events
