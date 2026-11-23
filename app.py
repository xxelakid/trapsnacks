# app.py
# Builds the application, connects all the parts, and starts the server.
# Run it locally with:  python app.py      (Render runs it with gunicorn: app:app)

import importlib
import pkgutil

from flask import Flask, render_template
from flask_login import current_user
from flask_socketio import join_room

import routes
from config import Config
from extensions import csrf, db, login_manager, socketio
from models import User


def register_all_routes(app):
    """ROUTES LAYER: plugs in every file in the routes/ folder automatically.

    Rule: each routes file contains a Blueprint with the SAME name as the file,
    for example routes/order_routes.py contains order_routes = Blueprint(...).
    Adding a feature therefore never requires editing this file, so team members
    can add their routes files without clashing with each other.
    """
    for module_info in pkgutil.iter_modules(routes.__path__):
        module = importlib.import_module(f'routes.{module_info.name}')
        blueprint = getattr(module, module_info.name, None)
        if blueprint is not None:
            app.register_blueprint(blueprint)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Connect the helper objects from extensions.py to this app
    db.init_app(app)
    socketio.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'
    login_manager.login_message = 'Please log in first.'

    register_all_routes(app)

    @app.context_processor
    def page_helpers():
        """Lets templates ask has_page('order_routes.cashier_page'), so a menu link or
        button only appears once the feature that provides that page has been added."""
        return {'has_page': lambda endpoint: endpoint in app.view_functions}

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

    with app.app_context():
        db.create_all()          # creates any missing tables (never changes existing ones)
    return app


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    return user if user and user.active else None     # a removed account is logged out


@socketio.on('connect')
def on_connect(auth=None):
    """Each screen joins 'rooms' so the server can send it only the updates it needs."""
    if not current_user.is_authenticated:
        return False                                   # refuse the live connection
    join_room(current_user.role)                       # 'cashier', 'chef', 'owner' or 'rider'
    if current_user.role in ('cashier', 'owner'):
        join_room('staff')                             # both use the delivery screen (FR 5)
    if current_user.role == 'rider':
        join_room(f'rider_{current_user.rider_id}')    # a private room for one rider


# Expose the Flask application to Gunicorn on Render.
app = create_app()


if __name__ == '__main__':
    print('TrapSnacks is running. On this computer open http://127.0.0.1:5000')
    print('On other devices on the same Wi-Fi open http://<this-computer-IP>:5000')
    # host='0.0.0.0' lets tablets and phones on the same Wi-Fi connect.
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
