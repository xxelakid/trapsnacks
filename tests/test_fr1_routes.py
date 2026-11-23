# FR 1 through the routes: the kitchen screen and its live updates
from conftest import delivery_data, login
from extensions import socketio


def test_chef_login_lands_on_kitchen(client, chef):
    response = login(client, 'chef')
    assert response.headers['Location'].endswith('/kitchen')
    assert client.get('/kitchen').status_code == 200


def test_kitchen_receives_new_order_live(app, client, cashier, chef, patty):
    chef_client = app.test_client()
    login(chef_client, 'chef')
    chef_socket = socketio.test_client(app, flask_test_client=chef_client)
    login(client, 'cashier')
    client.post('/api/orders', json=delivery_data(patty.id))
    events = [e['name'] for e in chef_socket.get_received()]
    assert 'order_created' in events


def test_chef_changes_status_through_the_api(client, cashier, chef, patty):
    login(client, 'cashier')
    order_id = client.post('/api/orders', json=delivery_data(patty.id)).get_json()['data']['id']
    client.get('/logout')
    login(client, 'chef')
    skip = client.post(f'/api/orders/{order_id}/status', json={'status': 'Ready'})
    assert skip.status_code == 400
    ok = client.post(f'/api/orders/{order_id}/status', json={'status': 'Preparing'})
    assert ok.get_json()['data']['status'] == 'Preparing'
