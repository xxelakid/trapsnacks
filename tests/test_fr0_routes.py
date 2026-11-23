# FR 0 through the routes: login lands on the cashier screen, API create order
from conftest import delivery_data, login


def test_cashier_login_lands_on_cashier_screen(client, cashier):
    response = login(client, 'cashier')
    assert response.status_code == 302 and response.headers['Location'].endswith('/cashier')


def test_cashier_creates_order_through_the_api(client, cashier, patty):
    login(client, 'cashier')
    response = client.post('/api/orders', json=delivery_data(patty.id))
    assert response.status_code == 201 and response.get_json()['ok'] is True
    bad = client.post('/api/orders', json={'order_type': 'pickup', 'items': []})
    assert bad.status_code == 400 and 'at least one item' in bad.get_json()['error']


def test_cashier_page_loads(client, cashier):
    login(client, 'cashier')
    assert client.get('/cashier').status_code == 200
