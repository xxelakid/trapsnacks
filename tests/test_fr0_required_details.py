# FR 0: customer name and contact phone are required for every order
import pytest
from conftest import delivery_data, login
from services.order_service import OrderService


def test_pickup_order_without_name_is_refused(cashier, patty):
    data = dict(delivery_data(patty.id), order_type='pickup', customer_name='')
    with pytest.raises(ValueError, match='customer name'):
        OrderService.create_order(data, cashier)


def test_order_without_phone_is_refused(cashier, patty):
    data = dict(delivery_data(patty.id), phone='')
    with pytest.raises(ValueError, match='phone'):
        OrderService.create_order(data, cashier)


def test_all_missing_details_are_listed_together(client, cashier, patty):
    login(client, 'cashier')
    response = client.post('/api/orders', json={'order_type': 'delivery', 'items': [{'id': patty.id}]})
    error = response.get_json()['error']
    assert 'customer name' in error and 'phone' in error and 'address' in error
