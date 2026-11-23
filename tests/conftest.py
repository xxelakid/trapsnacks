# tests/conftest.py
# Shared test set-up ("fixtures"). pytest runs this automatically.

import os
import sys

import pytest
from werkzeug.security import generate_password_hash

# Let the tests import app.py, models.py, etc. from the main folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app          # noqa: E402
from config import Config           # noqa: E402
from extensions import db           # noqa: E402
from models import MenuItem, Rider, User   # noqa: E402


class TestConfig(Config):
    TESTING = True
    # A fresh database in memory for every test (TEST_DATABASE_URL lets you test on PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite://')
    WTF_CSRF_ENABLED = False                    # makes test requests simpler


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(username, role, rider_id=None):
    user = User(username=username, role=role, rider_id=rider_id,
                password_hash=generate_password_hash('pass123'))
    db.session.add(user)
    db.session.commit()
    return user


def make_rider(name, status='available'):
    rider = Rider(name=name, phone='876-555-0000', address='1 Test Road', trn='111-222-333',
                  email=f'{name.lower()}@example.com', status=status)
    db.session.add(rider)
    db.session.commit()
    make_user(name.lower(), 'rider', rider.id)
    return rider


@pytest.fixture
def cashier(app):
    return make_user('cashier', 'cashier')


@pytest.fixture
def chef(app):
    return make_user('chef', 'chef')


@pytest.fixture
def owner(app):
    return make_user('owner', 'owner')


@pytest.fixture
def patty(app):
    item = MenuItem(name='Beef Patty', price=350, category='Patties')
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def juice(app):
    item = MenuItem(name='Fresh Fruit Juice', price=450, category='Drinks')
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def rider_a(app):
    return make_rider('Andre')


@pytest.fixture
def rider_b(app):
    return make_rider('Kemar')


def login(client, username):
    return client.post('/login', data={'username': username, 'password': 'pass123'})


def delivery_data(item_id, qty=1):
    return {'order_type': 'delivery', 'customer_name': 'Sam', 'phone': '876-555-9999',
            'address': '5 Hope Road', 'items': [{'id': item_id, 'qty': qty}]}
