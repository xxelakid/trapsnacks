# routes/auth_routes.py
# LoginScreen + AuthRoutes: login, logout, the home page for each role,
# and the role check used by every other routes file.

from functools import wraps
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from models import User

auth_routes = Blueprint('auth_routes', __name__)

# Where each role goes after logging in, in order of preference. The first page that
# exists is used, so this still works before every feature has been added.
HOME_PAGES = {
    'cashier': ['order_routes.cashier_page'],
    'chef': ['order_status_routes.kitchen_page'],
    'rider': ['rider_routes.rider_page'],
    'owner': ['delivery_display_routes.deliveries_page', 'order_routes.cashier_page',
              'staff_routes.staff_list'],
}


def home_url(role):
    for endpoint in HOME_PAGES.get(role, []):
        if endpoint in current_app.view_functions:
            return url_for(endpoint)
    return url_for('auth_routes.welcome')


def roles_required(*roles):
    """Put @roles_required('cashier') above a route so only those roles can use it (Security 2)."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def run_service(action, success_code=200):
    """Runs a service call. A ValueError (a broken rule) becomes a message for the screen."""
    try:
        result = action()
        return jsonify(ok=True, data=result), success_code
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 400


@auth_routes.get('/')
def home():
    if current_user.is_authenticated:
        return redirect(home_url(current_user.role))
    return redirect(url_for('auth_routes.login'))


@auth_routes.get('/welcome')
@login_required
def welcome():
    """Shown when a role's main screen has not been added to the project yet."""
    return render_template('welcome.html')


@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username', '').strip()).first()
        password_ok = user and check_password_hash(user.password_hash, request.form.get('password', ''))
        # A removed account (active = False) gets the same message as a wrong password,
        # so nobody can find out which usernames exist.
        if password_ok and user.active:
            login_user(user)
            return redirect(home_url(user.role))
        flash('Wrong username or password.', 'danger')
    return render_template('login.html')


@auth_routes.get('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth_routes.login'))
