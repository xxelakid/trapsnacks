# Foundation: login, logout, removed accounts, automatic routes, database upgrade
from sqlalchemy import inspect, text
from conftest import login, make_user
from extensions import db
from routes.auth_routes import home_url


def test_login_with_wrong_password_is_refused(client, cashier):
    response = client.post('/login', data={'username': 'cashier', 'password': 'wrong'},
                           follow_redirects=True)
    assert b'Wrong username or password' in response.data


def test_login_then_logout(client, cashier):
    assert login(client, 'cashier').status_code == 302
    client.get('/logout')
    assert client.get('/').headers['Location'].endswith('/login')


def test_removed_account_cannot_log_in(client, app):
    user = make_user('oldchef', 'chef')
    user.active = False
    db.session.commit()
    response = client.post('/login', data={'username': 'oldchef', 'password': 'pass123'},
                           follow_redirects=True)
    assert b'Wrong username or password' in response.data


def test_routes_files_are_plugged_in_automatically(app):
    assert 'auth_routes.login' in app.view_functions


def test_role_without_a_main_screen_goes_to_welcome_page(app):
    with app.test_request_context():
        assert home_url('nobody') == '/welcome'


def test_init_db_adds_missing_active_column_without_losing_users(app):
    from init_db import upgrade_database
    make_user('keepme', 'cashier')
    with db.engine.begin() as connection:
        connection.execute(text('ALTER TABLE "user" DROP COLUMN active'))   # an old database
    upgrade_database()
    columns = [c['name'] for c in inspect(db.engine).get_columns('user')]
    assert 'active' in columns
    with db.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM "user"')).scalar() == 1
