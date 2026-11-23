"""Runs on every Render deploy (see the start command in RENDER_SETUP.md).

1. Upgrades the existing database safely (adds new columns) without deleting any data.
2. Creates the first owner account if there is none.
3. Optionally adds the demo menu on an empty database.
"""
import os

from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from app import app
from extensions import db
from models import MenuItem, User


DEMO_MENU_ITEMS = [('Bacon, Egg & Cheese Sandwich', 850, 'Sandwiches'), ('Ham & Cheese Sandwich', 750, 'Sandwiches'), ('Turkey Club Sandwich', 950, 'Sandwiches'), ('Chicken Wrap', 900, 'Sandwiches'), ('Bacon, Egg & Cheese Patty', 550, 'Patties'), ('Beef Patty', 350, 'Patties'), ('Chicken Patty', 380, 'Patties'), ('Vegetable Patty', 330, 'Patties'), ('Korean Honey Butter Chips', 650, 'Imported Snacks'), ('Japanese Kit Kat (Matcha)', 600, 'Imported Snacks'), ('Takis Fuego', 550, 'Imported Snacks'), ('Cheese Board for Two', 2500, 'Deli'), ('Pastrami (per 1/4 lb)', 1100, 'Deli'), ('Fresh Fruit Juice', 450, 'Drinks'), ('Iced Coffee', 500, 'Drinks')]


def upgrade_database():
    """Adds columns that newer versions of models.py need, keeping all existing data.

    db.create_all() (in app.py) creates missing TABLES, but never changes a table that
    already exists. So when we add a column to an existing table, we add it here.
    Each step checks first, so running this again does nothing.
    """
    user_columns = [column['name'] for column in inspect(db.engine).get_columns('user')]
    if 'active' not in user_columns:
        with db.engine.begin() as connection:
            # "user" is in quotes because USER is a reserved word in PostgreSQL
            connection.execute(text('ALTER TABLE "user" ADD COLUMN active BOOLEAN NOT NULL DEFAULT TRUE'))
        print('Database upgraded: added user.active')


def initialize():
    secret_key = os.environ.get('SECRET_KEY')
    username = os.environ.get('ADMIN_USERNAME', 'owner').strip()
    password = os.environ.get('ADMIN_PASSWORD')
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError('Set a random SECRET_KEY of at least 32 characters in Render environment variables.')
    if not username or not password or len(password) < 12:
        raise RuntimeError('Set ADMIN_USERNAME and a strong ADMIN_PASSWORD (at least 12 characters) in Render.')

    with app.app_context():
        upgrade_database()

        if not User.query.filter_by(role='owner').first():
            if User.query.filter_by(username=username).first():
                raise RuntimeError('ADMIN_USERNAME is already in use by a non-owner user.')
            owner = User(username=username, role='owner', password_hash=generate_password_hash(password))
            db.session.add(owner)
            db.session.commit()
            print('Initial owner account created.')
        else:
            print('Owner account already exists.')

        if os.environ.get('DEMO_MENU') == '1' and not MenuItem.query.first():
            for name, price, category in DEMO_MENU_ITEMS:
                db.session.add(MenuItem(name=name, price=price, category=category))
            db.session.commit()
            print('Demo menu items created.')


if __name__ == '__main__':
    initialize()
