# db_upgrade.py
# Upgrades an existing database safely (adds new columns) without deleting any data.
# Runs automatically when the app starts (app.py) and on every Render deploy (init_db.py).

from datetime import datetime

from sqlalchemy import inspect, text

from extensions import db


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

    item_columns = [column['name'] for column in inspect(db.engine).get_columns('order_item')]
    if 'unit_price' not in item_columns:
        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE order_item ADD COLUMN unit_price FLOAT'))
            # Existing orders get the menu price as it is today (the best we know).
            connection.execute(text('UPDATE order_item SET unit_price = '
                                    '(SELECT price FROM menu_item WHERE menu_item.id = order_item.menu_item_id)'))
        print('Database upgraded: added order_item.unit_price')
        close_old_pickup_orders()


def close_old_pickup_orders():
    """Runs once, together with the unit_price upgrade. Before the "Collected" step existed,
    a pickup order was finished once it was Ready. Pickup orders from earlier days that are
    still Ready were collected long ago, so they are marked Collected (at the time they
    became Ready) and appear in the owner's Order History. Today's are left for the cashier."""
    from models import Order, StatusChange
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    old = Order.query.filter(Order.order_type == 'pickup', Order.status == 'Ready',
                             Order.created_at < today).all()
    for order in old:
        ready = [c.changed_at for c in order.changes if c.new_status == 'Ready']
        db.session.add(StatusChange(order_id=order.id, old_status='Ready', new_status='Collected',
                                    changed_at=max(ready) if ready else order.created_at))
        order.status = 'Collected'
    db.session.commit()
    if old:
        print(f'Marked {len(old)} older pickup orders as Collected.')
