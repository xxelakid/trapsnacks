# Pickup orders marked Collected, saved prices, and the cashier's Order List
import pytest
from conftest import delivery_data, login
from extensions import db
from services.edit_order_service import EditOrderService
from services.order_service import OrderService
from services.order_status_service import OrderStatusService


def pickup(item, cashier, name='Pat'):
    return OrderService.create_order({'order_type': 'pickup', 'customer_name': name,
                                      'phone': '876-555-1111', 'items': [{'id': item.id, 'qty': 2}]}, cashier)


def ready(order, chef):
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    OrderStatusService.change_status(order.id, 'Ready', chef)


def test_ready_pickup_can_be_collected(cashier, chef, patty):
    order = pickup(patty, cashier)
    with pytest.raises(ValueError, match='Only Ready'):
        OrderStatusService.mark_collected(order.id, cashier)
    ready(order, chef)
    OrderStatusService.mark_collected(order.id, cashier)
    assert order.status == 'Collected'
    assert order.changes[-1].new_status == 'Collected' and order.changes[-1].user_id == cashier.id
    with pytest.raises(ValueError):                         # cannot collect twice
        OrderStatusService.mark_collected(order.id, cashier)


def test_delivery_order_cannot_be_collected(cashier, chef, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    OrderStatusService.change_status(order.id, 'Ready', chef)
    with pytest.raises(ValueError, match='delivery'):
        OrderStatusService.mark_collected(order.id, cashier)


def test_collected_order_leaves_active_list(client, cashier, chef, patty):
    order = pickup(patty, cashier)
    ready(order, chef)
    login(client, 'cashier')
    assert client.post(f'/api/orders/{order.id}/collected').get_json()['ok']
    assert client.get('/api/orders/active').get_json() == []


def test_chef_cannot_mark_collected(client, cashier, chef, patty):
    order = pickup(patty, cashier)
    ready(order, chef)
    login(client, 'chef')
    assert client.post(f'/api/orders/{order.id}/collected').status_code == 403


def test_price_is_saved_when_order_is_placed(cashier, patty):
    order = pickup(patty, cashier)
    patty.price = 500                                       # menu price goes up later
    db.session.commit()
    assert order.items[0].unit_price == 350
    assert order.total == 700                               # still the original price


def test_edit_keeps_old_price_and_new_items_use_todays_price(cashier, patty, juice):
    order = pickup(patty, cashier)
    patty.price = 500
    db.session.commit()
    EditOrderService.edit_order(order.id, {'items': [{'id': patty.id, 'qty': 3}, {'id': juice.id, 'qty': 1}]}, cashier)
    prices = {i.menu_item_id: i.unit_price for i in order.items}
    assert prices == {patty.id: 350, juice.id: 450}
    assert order.total == 3 * 350 + 450


def test_order_list_shows_all_of_todays_orders_with_status(client, cashier, chef, patty, rider_a):
    collected = pickup(patty, cashier, 'Ann')
    ready(collected, chef)
    OrderStatusService.mark_collected(collected.id, cashier)
    waiting = pickup(patty, cashier, 'Bob')
    ready(waiting, chef)
    delivery = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(delivery.id, 'Preparing', chef)

    login(client, 'cashier')
    assert client.get('/order-list').status_code == 200
    rows = {o['id']: o for o in client.get('/api/orders/list').get_json()}
    assert rows[collected.id]['status'] == 'Collected'
    assert rows[waiting.id]['status'] == 'Ready'
    assert rows[delivery.id]['delivery_status'] == 'Offered'
    assert rows[delivery.id]['total'] == 350


def test_order_list_includes_ready_pickups_from_earlier_days(client, cashier, chef, patty):
    from datetime import datetime, timedelta
    old = pickup(patty, cashier, 'Old')
    ready(old, chef)
    old.created_at = datetime.now() - timedelta(days=2)
    db.session.commit()
    login(client, 'cashier')
    rows = client.get('/api/orders/list').get_json()
    assert [(o['id'], o['earlier']) for o in rows] == [(old.id, True)]
