# Order History (owner only): delivered, picked-up and cancelled orders
from conftest import delivery_data, login
from services.cancel_order_service import CancelOrderService
from services.delivery_service import DeliveryService
from services.order_history_service import OrderHistoryService
from services.order_service import OrderService
from services.order_status_service import OrderStatusService
from services.request_rider import RequestRider


def pickup_data(item_id, name='Pat'):
    return {'order_type': 'pickup', 'customer_name': name, 'phone': '876-555-1111',
            'items': [{'id': item_id, 'qty': 2}]}


def make_history(cashier, chef, item, rider):
    """One order of each outcome, plus one still in progress (must NOT appear)."""
    delivered = OrderService.create_order(delivery_data(item.id), cashier)
    OrderStatusService.change_status(delivered.id, 'Preparing', chef)
    RequestRider.accept_delivery(delivered.delivery.id, rider)
    OrderStatusService.change_status(delivered.id, 'Ready', chef)
    DeliveryService.update_delivery(delivered.delivery.id, 'Picked up', rider)
    DeliveryService.update_delivery(delivered.delivery.id, 'Delivered', rider)

    picked_up = OrderService.create_order(pickup_data(item.id), cashier)
    OrderStatusService.change_status(picked_up.id, 'Preparing', chef)
    OrderStatusService.change_status(picked_up.id, 'Ready', chef)

    cancelled = OrderService.create_order(pickup_data(item.id, 'Kim'), cashier)
    CancelOrderService.cancel_order(cancelled.id, 'Duplicate order', cashier)

    in_progress = OrderService.create_order(pickup_data(item.id, 'Lee'), cashier)
    return delivered, picked_up, cancelled, in_progress


def ids(result):
    return {order.id for order in result['orders']}


def test_history_lists_only_finished_orders(cashier, chef, patty, rider_a):
    delivered, picked_up, cancelled, in_progress = make_history(cashier, chef, patty, rider_a)
    result = OrderHistoryService.search(OrderHistoryService.read_filters({}))
    assert ids(result) == {delivered.id, picked_up.id, cancelled.id}
    assert result['summary']['delivered']['count'] == 1
    assert result['summary']['pickup']['count'] == 1
    assert result['summary']['cancelled']['count'] == 1
    assert result['summary']['pickup']['sales'] == 700        # 2 x 350


def test_history_filters_by_outcome_and_search(cashier, chef, patty, rider_a):
    delivered, picked_up, cancelled, _ = make_history(cashier, chef, patty, rider_a)
    read = OrderHistoryService.read_filters
    assert ids(OrderHistoryService.search(read({'outcome': 'cancelled'}))) == {cancelled.id}
    assert ids(OrderHistoryService.search(read({'outcome': 'delivered'}))) == {delivered.id}
    assert ids(OrderHistoryService.search(read({'q': 'kim'}))) == {cancelled.id}
    assert ids(OrderHistoryService.search(read({'q': f'#{picked_up.id}'}))) == {picked_up.id}
    assert ids(OrderHistoryService.search(read({'date_from': '2000-01-01', 'date_to': '2000-01-02'}))) == set()


def test_delivery_still_on_the_road_is_not_in_history(cashier, chef, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    OrderStatusService.change_status(order.id, 'Preparing', chef)
    RequestRider.accept_delivery(order.delivery.id, rider_a)
    OrderStatusService.change_status(order.id, 'Ready', chef)
    assert ids(OrderHistoryService.search(OrderHistoryService.read_filters({}))) == set()


def test_only_owner_can_open_history(client, owner, cashier, chef, patty, rider_a):
    make_history(cashier, chef, patty, rider_a)
    login(client, 'cashier')
    assert client.get('/history').status_code == 403
    client.get('/logout')
    login(client, 'owner')
    page = client.get('/history')
    assert page.status_code == 200
    assert b'Duplicate order' in page.data and b'Order History' in page.data
    csv = client.get('/history.csv?outcome=cancelled')
    assert csv.status_code == 200 and b'Kim' in csv.data and b',Pat,' not in csv.data
