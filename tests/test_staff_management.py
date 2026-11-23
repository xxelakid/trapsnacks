# Manage Staff: the owner adds, edits and removes cashier and chef accounts
import pytest
from conftest import login
from models import Order, StatusChange, User
from extensions import db
from services.staff_service import StaffService


def test_owner_adds_a_chef_who_can_then_log_in(client, owner):
    login(client, 'owner')
    client.post('/staff/new', data={'username': 'chef9', 'role': 'chef', 'password': 'kitchen99'})
    client.get('/logout')
    response = client.post('/login', data={'username': 'chef9', 'password': 'kitchen99'})
    assert response.status_code == 302


def test_staff_form_names_every_problem(app):
    with pytest.raises(ValueError) as error:
        StaffService.add_staff({'username': '', 'role': 'pilot', 'password': '123'})
    message = str(error.value)
    assert 'username' in message and 'role' in message and 'password' in message


def test_username_must_be_unique(app, cashier):
    with pytest.raises(ValueError, match='already used'):
        StaffService.add_staff({'username': 'cashier', 'role': 'chef', 'password': 'longenough'})


def test_edit_changes_role_and_keeps_password_when_blank(client, owner, cashier):
    old_hash = cashier.password_hash
    StaffService.edit_staff(cashier.id, {'username': 'cashier', 'role': 'chef', 'password': ''})
    assert cashier.role == 'chef' and cashier.password_hash == old_hash


def test_removed_staff_keeps_history_and_cannot_log_in(client, cashier):
    order = Order(order_type='pickup', customer_name='Sam', phone='876-555-9999')
    db.session.add(order)
    db.session.flush()
    db.session.add(StatusChange(order_id=order.id, new_status='New', user_id=cashier.id))
    db.session.commit()
    StaffService.remove_staff(cashier.id)
    assert db.session.get(User, cashier.id) is not None          # still there for the history
    assert cashier not in StaffService.list_staff()
    response = client.post('/login', data={'username': 'cashier', 'password': 'pass123'},
                           follow_redirects=True)
    assert b'Wrong username or password' in response.data


def test_owner_and_riders_cannot_be_managed_here(app, owner):
    with pytest.raises(ValueError):
        StaffService.remove_staff(owner.id)


def test_only_the_owner_can_open_staff_pages(client, cashier):
    login(client, 'cashier')
    assert client.get('/staff').status_code == 403
