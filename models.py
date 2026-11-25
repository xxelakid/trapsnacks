# models.py
# DATA LAYER. One Python class per database table (see the SDS class diagram).

from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import true
from extensions import db


def iso(value):
    """Turns a date/time into text the browser understands, or None."""
    return value.isoformat(timespec='seconds') if value else None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)               # cashier, chef, rider, owner
    rider_id = db.Column(db.Integer, db.ForeignKey('rider.id'))   # only for riders
    # False = the account was removed. Staff are switched off instead of deleted, because
    # StatusChange rows still point to them (the database would refuse a delete).
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())

    @property
    def is_active(self):
        """Flask-Login reads this: a removed account cannot log in."""
        return self.active


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(40), default='Other')
    available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'price': self.price,
                'category': self.category, 'available': self.available}


class Order(db.Model):
    __tablename__ = 'orders'          # "order" is a reserved word in SQL, so we use "orders"
    id = db.Column(db.Integer, primary_key=True)          # this is the unique order number
    order_type = db.Column(db.String(10), nullable=False)  # pickup or delivery
    customer_name = db.Column(db.String(80), default='')
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.String(200), default='')
    special_instructions = db.Column(db.Text, default='')
    status = db.Column(db.String(12), default='New')      # New, Preparing, Ready, Collected, Cancelled
    # (Collected = a pickup order the customer has taken away; set by the cashier)
    edited = db.Column(db.Boolean, default=False)
    cancel_reason = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    changes = db.relationship('StatusChange', backref='order')
    delivery = db.relationship('Delivery', backref='order', uselist=False)

    @property
    def total(self):
        """What the customer paid: the saved price of each item times its quantity."""
        return sum(item.line_total for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'order_type': self.order_type,
            'customer_name': self.customer_name,
            'phone': self.phone,
            'address': self.address,
            'special_instructions': self.special_instructions,
            'status': self.status,
            'edited': self.edited,
            'created_at': iso(self.created_at),
            'delivery_status': self.delivery.status if self.delivery else None,
            # Delivery orders: when the meal must be ready (starts when the chef begins preparing)
            'prep_deadline': iso(self.delivery.pickup_deadline) if self.delivery else None,
            'rider': self.delivery.rider.name if self.delivery and self.delivery.rider else None,
            'cancel_reason': self.cancel_reason,
            'total': self.total,
            'items': [{'menu_item_id': i.menu_item_id, 'name': i.menu_item.name,
                       'qty': i.quantity, 'addons': i.addons, 'price': i.price} for i in self.items],
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    addons = db.Column(db.String(200), default='')
    # The menu price when the order was placed, so changing the menu later
    # does not change what past orders cost.
    unit_price = db.Column(db.Float)
    menu_item = db.relationship('MenuItem')

    @property
    def price(self):
        """The saved price (very old rows without one fall back to today's menu price)."""
        return self.unit_price if self.unit_price is not None else self.menu_item.price

    @property
    def line_total(self):
        return self.price * self.quantity


class StatusChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    old_status = db.Column(db.String(12))
    new_status = db.Column(db.String(12), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    changed_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship('User')          # who made the change (shown in Order History)


class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    trn = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(12), default='unavailable')  # available, reserved, unavailable
    removed = db.Column(db.Boolean, default=False)
    deliveries = db.relationship('Delivery', backref='rider')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'phone': self.phone, 'status': self.status}


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('rider.id'))   # empty until a rider accepts
    status = db.Column(db.String(12), default='Offered')  # Offered, Accepted, Picked up, Delivered, Cancelled
    offered_at = db.Column(db.DateTime, default=datetime.now)
    accepted_at = db.Column(db.DateTime)
    pickup_deadline = db.Column(db.DateTime)
    picked_up_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    def offer_dict(self):
        """What every available rider sees in an offer: no customer name or phone (Security 3)."""
        return {'id': self.id, 'order_id': self.order_id, 'address': self.order.address,
                'offered_at': iso(self.offered_at), 'pickup_deadline': iso(self.pickup_deadline),
                'order_status': self.order.status}

    @property
    def ready_at(self):
        """When the kitchen marked the meal Ready (None if not yet)."""
        times = [c.changed_at for c in self.order.changes if c.new_status == 'Ready']
        return max(times) if times else None

    def full_dict(self):
        """What only the rider who accepted the delivery sees."""
        data = self.offer_dict()
        data.update({
            'status': self.status,
            'customer_name': self.order.customer_name,
            'phone': self.order.phone,
            'special_instructions': self.order.special_instructions,
            'order_status': self.order.status,
            'pickup_deadline': iso(self.pickup_deadline),
            'items': [{'name': i.menu_item.name, 'qty': i.quantity} for i in self.order.items],
        })
        return data

    def staff_dict(self):
        """One row on the staff delivery screen (FR 5)."""
        return {'id': self.id, 'order_id': self.order_id, 'status': self.status,
                'rider': self.rider.name if self.rider else 'Waiting for rider',
                'order_status': self.order.status,
                'offered_at': iso(self.offered_at), 'pickup_deadline': iso(self.pickup_deadline),
                'picked_up_at': iso(self.picked_up_at), 'delivered_at': iso(self.delivered_at),
                'ready_at': iso(self.ready_at)}
