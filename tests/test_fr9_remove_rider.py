# FR 9 Remove a Rider
import pytest
from conftest import delivery_data, login
from extensions import db
from models import Delivery, User
from services.order_service import OrderService
from services.remove_rider_service import RemoveRiderService


def test_fr9_rider_with_active_delivery_cannot_be_removed(cashier, patty, rider_a):
    order = OrderService.create_order(delivery_data(patty.id), cashier)
    db.session.add(Delivery(order_id=order.id, rider_id=rider_a.id, status='Accepted'))
    db.session.commit()
    with pytest.raises(ValueError, match='active delivery'):
        RemoveRiderService.remove_rider(rider_a.id)


def test_fr9_removed_rider_is_hidden_and_cannot_log_in(client, rider_a):
    RemoveRiderService.remove_rider(rider_a.id)
    assert rider_a.removed is True
    assert User.query.filter_by(rider_id=rider_a.id).first().active is False
    response = client.post('/login', data={'username': 'andre', 'password': 'pass123'},
                           follow_redirects=True)
    assert b'Wrong username or password' in response.data


def test_fr9_rider_list_is_owner_only(client, owner, rider_a):
    login(client, 'andre')
    assert client.get('/riders').status_code == 403
    client.get('/logout')
    login(client, 'owner')
    page = client.get('/riders')
    assert page.status_code == 200 and b'Andre' in page.data
